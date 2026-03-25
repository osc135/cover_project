import httpx
from app.config import get_settings
from app.models.schemas import AddressCandidate

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
LA_CENTERLINE_URL = (
    "https://maps.lacity.org/lahub/rest/services/centerlineLocator/GeocodeServer/findAddressCandidates"
)


async def geocode_google(address: str) -> list[AddressCandidate]:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            GOOGLE_GEOCODE_URL,
            params={"address": address, "key": settings.google_maps_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    candidates = []
    for result in data.get("results", []):
        loc = result["geometry"]["location"]
        candidates.append(
            AddressCandidate(
                formatted_address=result["formatted_address"],
                lat=loc["lat"],
                lng=loc["lng"],
                place_id=result.get("place_id"),
            )
        )
    return candidates


async def geocode_la_centerline(address: str) -> list[AddressCandidate]:
    """Fallback geocoder using LA City Centerline Locator."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            LA_CENTERLINE_URL,
            params={
                "SingleLine": address,
                "f": "json",
                "outFields": "*",
                "maxLocations": 5,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    candidates = []
    for c in data.get("candidates", []):
        loc = c.get("location", {})
        candidates.append(
            AddressCandidate(
                formatted_address=c.get("address", ""),
                lat=loc.get("y", 0),
                lng=loc.get("x", 0),
            )
        )
    return candidates


async def geocode(address: str) -> list[AddressCandidate]:
    """Try Google first, fall back to LA Centerline."""
    settings = get_settings()
    if settings.google_maps_api_key:
        candidates = await geocode_google(address)
        if candidates:
            return candidates

    return await geocode_la_centerline(address)
