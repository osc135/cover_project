"""Shared fixtures for tests and evals."""

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create a real database session for integration tests."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


# Also expose conftest values for test_rag.py import
__all__ = ["db_session", "TEST_PARCELS"]


# Known test parcels with expected data
TEST_PARCELS = [
    {
        "address": "2021 Kelton Ave, Los Angeles, CA",
        "label": "Westwood R1-1",
        "expected_zone_prefix": "R1",
        "expected_apn_prefix": "4263",
        "lat": 34.0553,
        "lng": -118.4440,
    },
    {
        "address": "2335 Overland Ave, Los Angeles, CA",
        "label": "Mar Vista R1-1-O",
        "expected_zone_prefix": "R1",
        "expected_apn_prefix": "4320",
        "lat": 34.0431,
        "lng": -118.4261,
    },
    {
        "address": "1525 S Saltair Ave, Los Angeles, CA",
        "label": "Mid-City R3-1",
        "expected_zone_prefix": "R3",
        "expected_apn_prefix": "4262",
        "lat": 34.0487,
        "lng": -118.4627,
    },
    {
        "address": "11941 Brentwood Grove Dr, Los Angeles, CA",
        "label": "Brentwood RE15",
        "expected_zone_prefix": "RE",
        "expected_apn_prefix": "4401",
        "lat": 34.0748,
        "lng": -118.4756,
    },
    {
        "address": "1535 Ocean Ave, Santa Monica, CA",
        "label": "Santa Monica (out of jurisdiction)",
        "expected_zone_prefix": None,  # Outside LA City — may not have zoning
        "expected_apn_prefix": "4292",
        "lat": 34.0102,
        "lng": -118.4963,
    },
]
