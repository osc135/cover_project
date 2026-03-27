from __future__ import annotations
from typing import Optional, List
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

PARCEL_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"
BUILDINGS_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/LARIAC_Buildings_2020/MapServer/0/query"
ZONING_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Zoning/FeatureServer/15/query"

# Overlay layer URLs from LA City GeoHub (verified)
HPOZ_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Historic_Preservation_Overlay_Zones/FeatureServer/5/query"
SPECIFIC_PLAN_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Specific_Plan_Areas/FeatureServer/6/query"
FLOOD_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/LA_Flood_Hazard_Areas/FeatureServer/0/query"
FIRE_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Very_High_Fire_Hazard_Severity_Zones/FeatureServer/0/query"
# Hillside and Coastal Zone layers not available on this server — detected via zoning code suffix instead

# Reusable client — avoids TCP connection overhead per request
_client: Optional[httpx.AsyncClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_client() -> httpx.AsyncClient:
    global _client, _client_loop
    loop = asyncio.get_event_loop()
    if _client is None or _client.is_closed or _client_loop is not loop:
        _client = httpx.AsyncClient(timeout=30)
        _client_loop = loop
    return _client


async def _query_arcgis(url: str, lat: float, lng: float, out_fields: str = "*", retries: int = 2) -> Optional[dict]:
    """Generic ArcGIS REST point-in-polygon query with retry."""
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "true",
        "f": "geojson",
    }
    client = _get_client()
    last_err = None

    for attempt in range(1 + retries):
        try:
            logger.info(f"ArcGIS query: {url.split('/')[-3]} at ({lat}, {lng})" + (f" (retry {attempt})" if attempt else ""))
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            logger.info(f"  -> {len(features)} features returned")
            if not features:
                return None
            return features[0]
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.ConnectError) as e:
            last_err = e
            logger.warning(f"  ArcGIS attempt {attempt + 1} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(1)

    raise last_err


async def fetch_parcel(lat: float, lng: float) -> Optional[dict]:
    return await _query_arcgis(PARCEL_URL, lat, lng)


async def fetch_buildings(lat: float, lng: float) -> List[dict]:
    """Fetch all building footprints intersecting the point."""
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    client = _get_client()
    resp = await client.get(BUILDINGS_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("features", [])


async def fetch_zoning(lat: float, lng: float) -> Optional[dict]:
    return await _query_arcgis(ZONING_URL, lat, lng)


async def fetch_overlays(lat: float, lng: float) -> dict:
    """Check all overlay zones. Returns dict of overlay results."""
    results = {}
    overlay_queries = {
        "hpoz": HPOZ_URL,
        "specific_plan": SPECIFIC_PLAN_URL,
        "flood_zone": FLOOD_URL,
        "fire_hazard": FIRE_URL,
    }

    client = _get_client()
    for name, url in overlay_queries.items():
        try:
            params = {
                "geometry": f"{lng},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json",
            }
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            features = data.get("features", [])
            results[name] = features[0] if features else None
            logger.info(f"  Overlay {name}: {'found' if features else 'not present'}")
        except Exception as e:
            logger.warning(f"  Overlay {name} failed: {e}")
            results[name] = None

    return results
