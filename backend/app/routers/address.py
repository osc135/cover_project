from fastapi import APIRouter, HTTPException
from app.models.schemas import AddressRequest, AddressResponse
from app.services.geocoding import geocode

router = APIRouter()


@router.post("/resolve-address", response_model=AddressResponse)
async def resolve_address(req: AddressRequest):
    candidates = await geocode(req.address)
    if not candidates:
        raise HTTPException(status_code=404, detail="No address candidates found")

    return AddressResponse(
        candidates=candidates,
        needs_confirmation=len(candidates) > 1,
    )
