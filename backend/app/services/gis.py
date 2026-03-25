import httpx

PARCEL_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Cache/LACounty_Parcel/MapServer/0/query"
BUILDINGS_URL = "https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/LARIAC_Buildings_2020/MapServer/0/query"
ZONING_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Zoning/FeatureServer/0/query"

# Overlay layer URLs from LA City GeoHub
HILLSIDE_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Hillside_Grading/FeatureServer/0/query"
HPOZ_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Historic_Preservation_Overlay_Zones_HPOZ/FeatureServer/0/query"
SPECIFIC_PLAN_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Specific_Plan_Area/FeatureServer/0/query"
FLOOD_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Flood_Hazard_Areas/FeatureServer/0/query"
FIRE_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Fire_Hazard_Severity_Zones/FeatureServer/0/query"
COASTAL_URL = "https://services5.arcgis.com/7nsPwEMP38bSkCjy/arcgis/rest/services/Coastal_Zone/FeatureServer/0/query"


async def _query_arcgis(url: str, lat: float, lng: float, out_fields: str = "*") -> dict | None:
    """Generic ArcGIS REST point-in-polygon query."""
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "true",
        "f": "geojson",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    if not features:
        return None
    return features[0]


async def fetch_parcel(lat: float, lng: float) -> dict | None:
    return await _query_arcgis(PARCEL_URL, lat, lng)


async def fetch_buildings(lat: float, lng: float) -> list[dict]:
    """Fetch all building footprints intersecting the point."""
    params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(BUILDINGS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    return data.get("features", [])


async def fetch_zoning(lat: float, lng: float) -> dict | None:
    return await _query_arcgis(ZONING_URL, lat, lng)


async def fetch_overlays(lat: float, lng: float) -> dict:
    """Check all overlay zones. Returns dict of overlay results."""
    results = {}
    overlay_queries = {
        "hillside": HILLSIDE_URL,
        "hpoz": HPOZ_URL,
        "specific_plan": SPECIFIC_PLAN_URL,
        "flood_zone": FLOOD_URL,
        "fire_hazard": FIRE_URL,
        "coastal_zone": COASTAL_URL,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        for name, url in overlay_queries.items():
            try:
                params = {
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
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
            except Exception:
                results[name] = None

    return results
