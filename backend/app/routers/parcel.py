from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.db import get_db
from app.models.schemas import (
    ConfirmAddressRequest,
    ParcelResponse,
    ParcelSummary,
    BuildingFootprint,
    ZoningInfo,
)
from app.services import gis

router = APIRouter()


async def _stream_pipeline(req: ConfirmAddressRequest, db: AsyncSession):
    """Run the data collection pipeline, yielding SSE progress events."""

    def event(step: str, status: str, detail: str = ""):
        payload = json.dumps({"step": step, "status": status, "detail": detail})
        return f"data: {payload}\n\n"

    lat, lng = req.lat, req.lng

    # 1 - Fetch parcel
    yield event("parcel", "in_progress", "Fetching parcel data from LA County...")
    parcel_feature = await gis.fetch_parcel(lat, lng)
    if not parcel_feature:
        yield event("parcel", "error", "No parcel found at this location")
        return
    props = parcel_feature.get("properties", {})
    apn = props.get("APN", props.get("AIN", ""))
    lot_size = props.get("ShapeArea") or props.get("Shape__Area")
    yield event("parcel", "complete")

    # 2 - Fetch zoning
    yield event("zoning", "in_progress", "Loading zoning designations...")
    zoning_feature = await gis.fetch_zoning(lat, lng)
    base_zone = None
    if zoning_feature:
        zprops = zoning_feature.get("properties", {})
        base_zone = zprops.get("Zoning") or zprops.get("ZONE_CMPLT") or zprops.get("ZONE_CLASS")
    yield event("zoning", "complete")

    # 3 - Fetch overlays
    yield event("overlays", "in_progress", "Checking overlay zones...")
    overlays = await gis.fetch_overlays(lat, lng)
    yield event("overlays", "complete")

    # 4 - Fetch buildings
    yield event("buildings", "in_progress", "Fetching existing building footprints...")
    building_features = await gis.fetch_buildings(lat, lng)
    yield event("buildings", "complete")

    # 5 - Store in DB
    yield event("storing", "in_progress", "Saving parcel data...")
    try:
        geom_json = json.dumps(parcel_feature.get("geometry"))
        await db.execute(
            text("""
                INSERT INTO parcels (apn, address, lot_size_sqft, geometry)
                VALUES (:apn, :address, :lot_size, cast(:geom as jsonb))
                ON CONFLICT (apn) DO UPDATE SET
                    address = EXCLUDED.address,
                    lot_size_sqft = EXCLUDED.lot_size_sqft,
                    geometry = EXCLUDED.geometry
            """),
            {"apn": apn, "address": req.formatted_address, "lot_size": lot_size, "geom": geom_json},
        )

        # Store zoning
        await db.execute(
            text("""
                INSERT INTO zoning_designations (apn, base_zone, hillside, coastal_zone, fire_hazard, hpoz, specific_plan, flood_zone)
                VALUES (:apn, :base_zone, :hillside, :coastal, :fire, :hpoz, :sp, :flood)
                ON CONFLICT (apn) DO UPDATE SET
                    base_zone = EXCLUDED.base_zone,
                    hillside = EXCLUDED.hillside,
                    coastal_zone = EXCLUDED.coastal_zone,
                    fire_hazard = EXCLUDED.fire_hazard,
                    hpoz = EXCLUDED.hpoz,
                    specific_plan = EXCLUDED.specific_plan,
                    flood_zone = EXCLUDED.flood_zone
            """),
            {
                "apn": apn,
                "base_zone": base_zone,
                "hillside": overlays.get("hillside") is not None,
                "coastal": overlays.get("coastal_zone") is not None,
                "fire": (overlays.get("fire_hazard") or {}).get("attributes", {}).get("HAZ_CODE") if overlays.get("fire_hazard") else None,
                "hpoz": overlays.get("hpoz") is not None,
                "sp": (overlays.get("specific_plan") or {}).get("attributes", {}).get("SPECIFIC_PLAN") if overlays.get("specific_plan") else None,
                "flood": (overlays.get("flood_zone") or {}).get("attributes", {}).get("FLD_ZONE") if overlays.get("flood_zone") else None,
            },
        )

        # Store buildings
        for bf in building_features:
            bprops = bf.get("properties", {})
            bf_geom = json.dumps(bf.get("geometry"))
            await db.execute(
                text("""
                    INSERT INTO buildings (apn, building_type, sqft, geometry)
                    VALUES (:apn, :btype, :sqft, cast(:geom as jsonb))
                """),
                {
                    "apn": apn,
                    "btype": bprops.get("UseType"),
                    "sqft": bprops.get("Shape__Area"),
                    "geom": bf_geom,
                },
            )

        await db.commit()
    except Exception as e:
        await db.rollback()
        yield event("storing", "error", str(e))
        return

    yield event("storing", "complete")

    # Final response with full parcel data
    result = ParcelResponse(
        parcel=ParcelSummary(
            apn=apn,
            address=req.formatted_address,
            lot_size_sqft=lot_size,
            geometry=parcel_feature.get("geometry"),
        ),
        buildings=[
            BuildingFootprint(
                building_type=bf.get("properties", {}).get("UseType"),
                sqft=bf.get("properties", {}).get("Shape__Area"),
                geometry=bf.get("geometry"),
            )
            for bf in building_features
        ],
        zoning=ZoningInfo(
            base_zone=base_zone,
            hillside=overlays.get("hillside") is not None,
            coastal_zone=overlays.get("coastal_zone") is not None,
            fire_hazard=(overlays.get("fire_hazard") or {}).get("attributes", {}).get("HAZ_CODE") if overlays.get("fire_hazard") else None,
            hpoz=overlays.get("hpoz") is not None,
            specific_plan=(overlays.get("specific_plan") or {}).get("attributes", {}).get("SPECIFIC_PLAN") if overlays.get("specific_plan") else None,
            flood_zone=(overlays.get("flood_zone") or {}).get("attributes", {}).get("FLD_ZONE") if overlays.get("flood_zone") else None,
        ),
    )

    yield event("complete", "complete", result.model_dump_json())


@router.post("/confirm-address")
async def confirm_address(req: ConfirmAddressRequest, db: AsyncSession = Depends(get_db)):
    return StreamingResponse(
        _stream_pipeline(req, db),
        media_type="text/event-stream",
    )


@router.get("/parcel/{apn}", response_model=ParcelResponse)
async def get_parcel(apn: str, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("SELECT apn, address, lot_size_sqft, geometry FROM parcels WHERE apn = :apn"),
        {"apn": apn},
    )
    parcel = row.fetchone()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    buildings_row = await db.execute(
        text("SELECT building_type, sqft, geometry FROM buildings WHERE apn = :apn"),
        {"apn": apn},
    )
    buildings = buildings_row.fetchall()

    zoning_row = await db.execute(
        text("SELECT * FROM zoning_designations WHERE apn = :apn"),
        {"apn": apn},
    )
    zoning = zoning_row.fetchone()

    return ParcelResponse(
        parcel=ParcelSummary(
            apn=parcel.apn,
            address=parcel.address,
            lot_size_sqft=parcel.lot_size_sqft,
            geometry=parcel.geometry,
        ),
        buildings=[
            BuildingFootprint(
                building_type=b.building_type,
                sqft=b.sqft,
                geometry=b.geometry,
            )
            for b in buildings
        ],
        zoning=ZoningInfo(
            base_zone=zoning.base_zone if zoning else None,
            hillside=zoning.hillside if zoning else False,
            coastal_zone=zoning.coastal_zone if zoning else False,
            fire_hazard=zoning.fire_hazard if zoning else None,
            hpoz=zoning.hpoz if zoning else False,
            specific_plan=zoning.specific_plan if zoning else None,
            flood_zone=zoning.flood_zone if zoning else None,
        ),
    )
