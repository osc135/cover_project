from fastapi import APIRouter, HTTPException
from app.models.schemas import AddressRequest, AddressResponse
from app.services.geocoding import geocode

router = APIRouter()

# Bounding box for LA County (generous)
LA_BOUNDS = {"lat_min": 33.7, "lat_max": 34.35, "lng_min": -118.7, "lng_max": -117.65}


@router.post("/resolve-address", response_model=AddressResponse)
async def resolve_address(req: AddressRequest):
    candidates = await geocode(req.address)
    if not candidates:
        raise HTTPException(status_code=404, detail="No address candidates found")

    # Filter to candidates within LA County bounds
    la_candidates = [
        c for c in candidates
        if LA_BOUNDS["lat_min"] <= c.lat <= LA_BOUNDS["lat_max"]
        and LA_BOUNDS["lng_min"] <= c.lng <= LA_BOUNDS["lng_max"]
    ]

    if not la_candidates:
        raise HTTPException(
            status_code=404,
            detail="Address is outside the Los Angeles County area. This tool only supports residential parcels in LA.",
        )

    return AddressResponse(
        candidates=la_candidates,
        needs_confirmation=len(la_candidates) > 1,
    )
