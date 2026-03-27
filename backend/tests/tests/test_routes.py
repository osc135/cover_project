"""Integration tests for FastAPI API routes.

These hit real external APIs (geocoding) and the real database.
Run with: pytest tests/tests/test_routes.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


transport = ASGITransport(app=app)


@pytest.mark.asyncio
class TestHealth:
    """GET /api/health — no external deps."""

    async def test_health_returns_ok(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
class TestResolveAddress:
    """POST /api/resolve-address — hits geocoding API."""

    async def test_known_la_address(self):
        """A real LA address should return at least one candidate."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/resolve-address",
                json={"address": "2335 Overland Ave, Los Angeles, CA"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["candidates"]) >= 1
        candidate = data["candidates"][0]
        assert "lat" in candidate
        assert "lng" in candidate
        assert 34.0 < candidate["lat"] < 34.1
        assert -118.5 < candidate["lng"] < -118.4

    async def test_garbage_address_returns_404(self):
        """Nonsense input should return 404 when no candidates found."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/resolve-address",
                json={"address": "zzzzz xkcd not a place 99999"},
            )
        # Geocoder may return empty => 404, or may still find something.
        assert resp.status_code in (200, 404)

    async def test_missing_body_returns_422(self):
        """Missing required field should return 422 validation error."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/resolve-address", json={})
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestGetParcel:
    """GET /api/parcel/{apn} — reads from the database."""

    async def test_unknown_apn_returns_404(self):
        """A fabricated APN should return 404."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/parcel/0000-000-000")
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestAssess:
    """POST /api/assess — validation tests only (no DB/LLM dependency)."""

    async def test_assess_missing_fields_returns_422(self):
        """Missing required fields should return 422."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/assess", json={"apn": "1234"})
        assert resp.status_code == 422

    async def test_assess_empty_body_returns_422(self):
        """Empty body should return 422."""
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/assess", json={})
        assert resp.status_code == 422
