from __future__ import annotations

import logging
import math
import httpx
from app.config import get_settings
from app.models.schemas import AddressCandidate

logger = logging.getLogger(__name__)

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
LA_CENTERLINE_URL = (
    "https://maps.lacity.org/lahub/rest/services/centerlineLocator/GeocodeServer/findAddressCandidates"
)


def _web_mercator_to_latlng(x: float, y: float) -> tuple[float, float]:
    """Convert Web Mercator (EPSG:3857) to lat/lng (EPSG:4326)."""
    lng = (x / 20037508.34) * 180.0
    lat = (y / 20037508.34) * 180.0
    lat = 180.0 / math.pi * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lat, lng


async def geocode_google(address: str) -> list[AddressCandidate]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                GOOGLE_GEOCODE_URL,
                params={"address": address, "key": settings.google_maps_api_key},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "OK":
            logger.warning(f"Google geocode failed: {data.get('status')} - {data.get('error_message', '')}")
            return []

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
        logger.info(f"Google geocode returned {len(candidates)} candidates")
        return candidates
    except Exception as e:
        logger.warning(f"Google geocode exception: {e}")
        return []


async def geocode_la_centerline(address: str) -> list[AddressCandidate]:
    """Fallback geocoder using LA City Centerline Locator."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            LA_CENTERLINE_URL,
            params={
                "Street": address,
                "f": "json",
                "maxLocations": 5,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    candidates = []
    for c in data.get("candidates", []):
        loc = c.get("location", {})
        x, y = loc.get("x", 0), loc.get("y", 0)
        if x and y:
            lat, lng = _web_mercator_to_latlng(x, y)
            logger.info(f"LA Centerline: '{c.get('address')}' -> lat={lat:.6f}, lng={lng:.6f}")
            candidates.append(
                AddressCandidate(
                    formatted_address=c.get("address", ""),
                    lat=lat,
                    lng=lng,
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
