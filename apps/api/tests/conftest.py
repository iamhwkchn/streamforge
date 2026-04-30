"""
Function-scoped fixtures for integration tests.

Each test gets its own asyncpg pool and httpx client so that the
asyncpg connections and pytest-asyncio's per-test event loop are always
on the same loop. No mocks — everything hits real Postgres in Docker.
"""
import asyncpg
import httpx
import pytest
from main import app
from core.config import settings
from db.connection import db


@pytest.fixture
async def db_pool():
    """Real asyncpg pool for the duration of a single test."""
    pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    yield pool
    await pool.close()


@pytest.fixture
async def client(db_pool):
    """
    httpx AsyncClient backed by the real FastAPI app.

    Injects the test pool directly into db.pool so service calls hit
    real Postgres without going through the app's lifespan startup.
    """
    db.pool = db_pool
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
    db.pool = None


@pytest.fixture
async def retail_events_id(db_pool) -> str:
    """UUID of the seeded retail_events dataset, as a plain string."""
    row = await db_pool.fetchrow(
        "SELECT id FROM datasets WHERE name = 'retail_events'"
    )
    assert row is not None, (
        "retail_events dataset not found — is Postgres seeded? "
        "Run: docker compose -f ops/docker/docker-compose.yml up -d postgres"
    )
    return str(row["id"])
