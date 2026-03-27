from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.db import get_db
from app.models.schemas import AssessRequest, AssessmentResponse, ConfidenceBreakdown
from app.services.rag import retrieve_chunks
from app.services.llm import run_assessment

# Indexed zone prefixes
INDEXED_ZONES = {"R1", "R2", "R3", "R4", "R5", "RD", "RE", "RS", "RU", "RW"}


def compute_confidence(parcel_data: dict, zoning_data: dict, buildings: list, chunks: list, constraints: list) -> ConfidenceBreakdown:
    """Calculate confidence from data quality and rule confidence separately."""
    factors = []

    # --- Data Quality (0.0 - 1.0) ---
    dq_score = 1.0

    # Lot size: big factor
    if not parcel_data.get("lot_size_sqft"):
        dq_score -= 0.25
        factors.append("Lot size missing (-25% data quality)")

    # Base zone indexed?
    import re
    base_zone = zoning_data.get("base_zone") or ""
    zone_clean = re.sub(r'^(\([A-Z]+\)|\[[A-Z]+\])+', '', base_zone)
    zone_prefix = zone_clean.split("-")[0]
    if zone_prefix not in INDEXED_ZONES:
        dq_score -= 0.30
        factors.append(f"Zone {base_zone} rules not fully indexed (-30% data quality)")

    # Buildings found?
    if not buildings:
        dq_score -= 0.10
        factors.append("No existing building data found (-10% data quality)")

    # Unindexed overlays
    overlay_hits = []
    if zoning_data.get("hillside"):
        overlay_hits.append("Hillside")
    if zoning_data.get("coastal_zone"):
        overlay_hits.append("Coastal Zone")
    if zoning_data.get("specific_plan"):
        overlay_hits.append(f"Specific Plan: {zoning_data['specific_plan']}")
    if zoning_data.get("hpoz"):
        overlay_hits.append("HPOZ")
    if overlay_hits:
        dq_score -= 0.05 * len(overlay_hits)
        factors.append(f"Overlay zones detected but not fully modeled: {', '.join(overlay_hits)} (-{5 * len(overlay_hits)}% data quality)")

    # RAG chunks found?
    if len(chunks) < 3:
        dq_score -= 0.15
        factors.append(f"Only {len(chunks)} regulatory chunks found (-15% data quality)")

    dq_score = max(0.0, min(1.0, dq_score))

    # --- Rule Confidence (from LLM constraint levels) ---
    if constraints:
        weights = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.2}
        total = sum(weights.get(c.get("confidence", c.confidence if hasattr(c, "confidence") else "LOW"), 0.2) for c in constraints)
        rc_score = total / len(constraints)
        high_count = sum(1 for c in constraints if (c.get("confidence") if isinstance(c, dict) else c.confidence) == "HIGH")
        med_count = sum(1 for c in constraints if (c.get("confidence") if isinstance(c, dict) else c.confidence) == "MEDIUM")
        low_count = sum(1 for c in constraints if (c.get("confidence") if isinstance(c, dict) else c.confidence) == "LOW")
        factors.append(f"Rule confidence: {high_count} HIGH, {med_count} MEDIUM, {low_count} LOW")
    else:
        rc_score = 0.3
        factors.append("No constraints generated — low rule confidence")

    # --- Overall ---
    overall = round(dq_score * rc_score, 2)

    if overall >= 0.90:
        grade = "A"
    elif overall >= 0.75:
        grade = "B"
    elif overall >= 0.60:
        grade = "C"
    else:
        grade = "D"

    return ConfidenceBreakdown(
        data_quality=round(dq_score, 2),
        rule_confidence=round(rc_score, 2),
        overall=overall,
        grade=grade,
        factors=factors,
    )

router = APIRouter()


@router.post("/assess", response_model=AssessmentResponse)
async def assess(req: AssessRequest, db: AsyncSession = Depends(get_db)):
    # Check cache
    cached = await db.execute(
        text("SELECT * FROM assessments WHERE apn = :apn AND building_type = :bt"),
        {"apn": req.apn, "bt": req.building_type},
    )
    row = cached.fetchone()
    if row:
        return AssessmentResponse(
            apn=row.apn,
            building_type=row.building_type,
            buildable=row.buildable,
            confidence_score=row.confidence_score,
            confidence_grade=row.confidence_grade,
            summary=row.summary,
            constraints=json.loads(row.constraints) if isinstance(row.constraints, str) else row.constraints,
            open_questions=json.loads(row.open_questions) if isinstance(row.open_questions, str) else row.open_questions,
        )

    # Load parcel data
    parcel_row = await db.execute(
        text("SELECT apn, address, lot_size_sqft, geometry FROM parcels WHERE apn = :apn"),
        {"apn": req.apn},
    )
    parcel = parcel_row.fetchone()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found — run confirm-address first")

    # Load zoning
    zoning_row = await db.execute(
        text("SELECT * FROM zoning_designations WHERE apn = :apn"),
        {"apn": req.apn},
    )
    zoning = zoning_row.fetchone()
    if not zoning:
        raise HTTPException(status_code=404, detail="Zoning data not found")

    # Load buildings
    buildings_row = await db.execute(
        text("SELECT building_type, sqft FROM buildings WHERE apn = :apn"),
        {"apn": req.apn},
    )
    buildings = [{"building_type": b.building_type, "sqft": b.sqft} for b in buildings_row.fetchall()]

    # RAG retrieval
    base_zone = zoning.base_zone or "R1"
    # Strip prefixes like [Q], (T)(Q) and height district suffix (e.g., "[Q]R3-1" -> "R3")
    import re
    zone_clean = re.sub(r'^(\([A-Z]+\)|\[[A-Z]+\])+', '', base_zone)
    zone_prefix = zone_clean.split("-")[0] if zone_clean else "R1"
    chunks = await retrieve_chunks(db, zone_prefix, req.building_type)

    # Calculate lot dimensions from geometry
    import math
    lot_width_ft = None
    lot_depth_ft = None
    geometry = parcel.geometry
    if isinstance(geometry, str):
        geometry = json.loads(geometry)
    if geometry and geometry.get("coordinates"):
        coords = geometry["coordinates"][0] if geometry["type"] == "Polygon" else geometry["coordinates"][0][0]
        # At LA latitude: 1 degree lat ≈ 364,000 ft, 1 degree lng ≈ 288,000 ft
        FT_PER_LAT = 364000
        FT_PER_LNG = 288000

        # Calculate all edge lengths
        edges = []
        for i in range(len(coords) - 1):
            dx = (coords[i+1][0] - coords[i][0]) * FT_PER_LNG
            dy = (coords[i+1][1] - coords[i][1]) * FT_PER_LAT
            length = math.sqrt(dx*dx + dy*dy)
            mid = [(coords[i][0] + coords[i+1][0]) / 2, (coords[i][1] + coords[i+1][1]) / 2]
            edges.append({"idx": i, "length": length, "mid": mid})

        if len(edges) >= 4:
            # Sort edges by length — typically the two longer edges are depth, two shorter are width
            # But more accurately: use edge orientations
            # For now, use a simpler heuristic: lot width ≈ shorter pair, lot depth ≈ longer pair
            sorted_edges = sorted(edges, key=lambda e: e["length"])
            lot_width_ft = round((sorted_edges[0]["length"] + sorted_edges[1]["length"]) / 2, 1)
            lot_depth_ft = round((sorted_edges[-1]["length"] + sorted_edges[-2]["length"]) / 2, 1)
            # Ensure width < depth (convention)
            if lot_width_ft > lot_depth_ft:
                lot_width_ft, lot_depth_ft = lot_depth_ft, lot_width_ft

    # Build context dicts
    parcel_data = {
        "apn": parcel.apn,
        "address": parcel.address,
        "lot_size_sqft": parcel.lot_size_sqft,
        "lot_width_ft": lot_width_ft,
        "lot_depth_ft": lot_depth_ft,
    }
    zoning_data = {
        "base_zone": zoning.base_zone,
        "height_district": zoning.height_district,
        "hillside": zoning.hillside,
        "coastal_zone": zoning.coastal_zone,
        "fire_hazard": zoning.fire_hazard,
        "hpoz": zoning.hpoz,
        "specific_plan": zoning.specific_plan,
        "flood_zone": zoning.flood_zone,
    }

    # Run LLM assessment
    result = await run_assessment(parcel_data, zoning_data, buildings, chunks, req.building_type)

    # Compute our own confidence score
    constraint_dicts = [c.model_dump() for c in result.constraints]
    breakdown = compute_confidence(parcel_data, zoning_data, buildings, chunks, constraint_dicts)
    result.confidence_score = breakdown.overall
    result.confidence_grade = breakdown.grade
    result.confidence_breakdown = breakdown

    # Cache result
    await db.execute(
        text("""
            INSERT INTO assessments (apn, building_type, buildable, confidence_score, confidence_grade, summary, constraints, open_questions, raw_response)
            VALUES (:apn, :bt, :buildable, :score, :grade, :summary, :constraints, :oq, :raw)
            ON CONFLICT (apn, building_type) DO UPDATE SET
                buildable = EXCLUDED.buildable,
                confidence_score = EXCLUDED.confidence_score,
                confidence_grade = EXCLUDED.confidence_grade,
                summary = EXCLUDED.summary,
                constraints = EXCLUDED.constraints,
                open_questions = EXCLUDED.open_questions,
                raw_response = EXCLUDED.raw_response
        """),
        {
            "apn": req.apn,
            "bt": req.building_type,
            "buildable": result.buildable,
            "score": result.confidence_score,
            "grade": result.confidence_grade,
            "summary": result.summary,
            "constraints": json.dumps([c.model_dump() for c in result.constraints]),
            "oq": json.dumps(result.open_questions),
            "raw": json.dumps(result.model_dump()),
        },
    )
    await db.commit()

    return result


@router.get("/assessment/{apn}/{building_type}", response_model=AssessmentResponse)
async def get_assessment(apn: str, building_type: str, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT * FROM assessments WHERE apn = :apn AND building_type = :bt"),
        {"apn": apn, "bt": building_type},
    )
    result = row.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return AssessmentResponse(
        apn=result.apn,
        building_type=result.building_type,
        buildable=result.buildable,
        confidence_score=result.confidence_score,
        confidence_grade=result.confidence_grade,
        summary=result.summary,
        constraints=json.loads(result.constraints) if isinstance(result.constraints, str) else result.constraints,
        open_questions=json.loads(result.open_questions) if isinstance(result.open_questions, str) else result.open_questions,
    )
