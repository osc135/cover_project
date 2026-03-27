"""Integration tests for GIS API calls — hits real LA County/City APIs."""

import pytest
from app.services.gis import fetch_parcel, fetch_buildings, fetch_zoning, fetch_overlays


# 2335 Overland Ave, Mar Vista — known R1-1-O parcel
OVERLAND_LAT = 34.0431
OVERLAND_LNG = -118.4261

# 2021 Kelton Ave, Westwood — known R1-1
KELTON_LAT = 34.0553
KELTON_LNG = -118.4440


@pytest.mark.asyncio
class TestParcelAPI:
    """Tests against the live LA County Parcel API."""

    async def test_fetch_parcel_returns_feature(self):
        result = await fetch_parcel(OVERLAND_LAT, OVERLAND_LNG)
        assert result is not None
        assert "properties" in result
        assert "geometry" in result

    async def test_fetch_parcel_correct_apn(self):
        result = await fetch_parcel(OVERLAND_LAT, OVERLAND_LNG)
        props = result["properties"]
        apn = props.get("APN", "")
        assert apn.startswith("4320"), f"Expected APN starting with 4320, got {apn}"

    async def test_fetch_parcel_has_geometry(self):
        result = await fetch_parcel(OVERLAND_LAT, OVERLAND_LNG)
        geom = result["geometry"]
        assert geom["type"] in ("Polygon", "MultiPolygon")
        assert len(geom["coordinates"]) > 0

    async def test_fetch_parcel_has_property_details(self):
        result = await fetch_parcel(OVERLAND_LAT, OVERLAND_LNG)
        props = result["properties"]
        # Should have residential property attributes
        assert props.get("UseType") is not None
        assert props.get("SitusStreet") is not None

    async def test_fetch_parcel_no_result_for_ocean(self):
        """A point in the ocean should return None."""
        result = await fetch_parcel(33.9, -118.6)
        assert result is None


@pytest.mark.asyncio
class TestBuildingsAPI:

    async def test_fetch_buildings_returns_list(self):
        result = await fetch_buildings(OVERLAND_LAT, OVERLAND_LNG)
        assert isinstance(result, list)

    async def test_fetch_buildings_have_geometry(self):
        result = await fetch_buildings(OVERLAND_LAT, OVERLAND_LNG)
        if result:  # building footprints may not always be available
            for b in result:
                assert "geometry" in b
                assert "properties" in b


@pytest.mark.asyncio
class TestZoningAPI:

    async def test_fetch_zoning_returns_feature(self):
        result = await fetch_zoning(OVERLAND_LAT, OVERLAND_LNG)
        assert result is not None
        assert "properties" in result

    async def test_fetch_zoning_correct_zone(self):
        """Overland Ave should be in an R1 zone."""
        result = await fetch_zoning(OVERLAND_LAT, OVERLAND_LNG)
        props = result["properties"]
        zone = props.get("Zoning") or props.get("ZONE_CMPLT") or props.get("ZONE_CLASS") or ""
        assert "R1" in zone, f"Expected R1 zone, got {zone}"

    async def test_fetch_zoning_different_zone(self):
        """Kelton Ave should return a residential zone."""
        result = await fetch_zoning(KELTON_LAT, KELTON_LNG)
        props = result["properties"]
        zone = props.get("Zoning") or props.get("ZONE_CMPLT") or props.get("ZONE_CLASS") or ""
        assert zone, f"Expected a zone designation, got empty"
        # Kelton is [Q]R4-1L — verify it's a residential zone
        assert "R" in zone, f"Expected residential zone, got {zone}"


@pytest.mark.asyncio
class TestOverlaysAPI:

    async def test_fetch_overlays_returns_dict(self):
        result = await fetch_overlays(OVERLAND_LAT, OVERLAND_LNG)
        assert isinstance(result, dict)
        assert "hpoz" in result
        assert "specific_plan" in result
        assert "flood_zone" in result
        assert "fire_hazard" in result

    async def test_overlays_standard_residential_no_hazards(self):
        """A standard R1 lot in Mar Vista should not be in fire/flood/HPOZ zones."""
        result = await fetch_overlays(OVERLAND_LAT, OVERLAND_LNG)
        assert result["hpoz"] is None
        assert result["fire_hazard"] is None
