from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.db import get_db
from app.models.schemas import AssessRequest, AssessmentResponse
from app.services.rag import retrieve_chunks
from app.services.llm import run_assessment

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
        text("SELECT apn, address, lot_size_sqft FROM parcels WHERE apn = :apn"),
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
    # Strip height district suffix for chunk lookup (e.g., "R1-1" -> "R1")
    zone_prefix = base_zone.split("-")[0] if base_zone else "R1"
    chunks = await retrieve_chunks(db, zone_prefix, req.building_type)

    # Build context dicts
    parcel_data = {
        "apn": parcel.apn,
        "address": parcel.address,
        "lot_size_sqft": parcel.lot_size_sqft,
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
