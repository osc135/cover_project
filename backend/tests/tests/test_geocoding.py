"""Integration tests for the geocoding service."""

import pytest
from app.services.geocoding import geocode, _web_mercator_to_latlng


class TestWebMercatorConversion:
    """Unit tests for coordinate conversion — no external deps."""

    def test_known_point_la(self):
        """Known Web Mercator coords for downtown LA."""
        # Downtown LA is roughly (-118.25, 34.05) in WGS84
        # In Web Mercator: (-13164000, 4035000) approximately
        lat, lng = _web_mercator_to_latlng(-13164000, 4035000)
        assert 33.5 < lat < 34.5, f"Latitude {lat} out of LA range"
        assert -119.0 < lng < -117.5, f"Longitude {lng} out of LA range"

    def test_zero_point(self):
        lat, lng = _web_mercator_to_latlng(0, 0)
        assert abs(lat) < 0.01
        assert abs(lng) < 0.01


@pytest.mark.asyncio
class TestGeocode:
    """Integration tests — hits real geocoding APIs."""

    async def test_known_address_returns_candidates(self):
        candidates = await geocode("2335 Overland Ave, Los Angeles, CA")
        assert len(candidates) >= 1

    async def test_known_address_correct_location(self):
        candidates = await geocode("2335 Overland Ave, Los Angeles, CA")
        c = candidates[0]
        # Should be near Mar Vista
        assert 34.0 < c.lat < 34.1, f"Latitude {c.lat} unexpected"
        assert -118.5 < c.lng < -118.4, f"Longitude {c.lng} unexpected"

    async def test_known_address_has_formatted_address(self):
        candidates = await geocode("2335 Overland Ave, Los Angeles, CA")
        c = candidates[0]
        assert "overland" in c.formatted_address.lower() or "2335" in c.formatted_address

    async def test_nonsense_address(self):
        """Garbage input should return empty or still not crash."""
        candidates = await geocode("zzzzz not a real place 99999")
        # Either empty or some result — just shouldn't crash
        assert isinstance(candidates, list)
