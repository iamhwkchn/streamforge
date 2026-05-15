"""
Unit tests for the metrics endpoint — no Postgres, no Docker.

Two layers tested independently:
  - Service layer: get_dataset_metrics() with a mocked asyncpg pool
  - Route layer:   GET /datasets/{id}/metrics with a mocked service function
"""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import httpx
import pytest
from main import app

DATASET_ID = UUID("12345678-1234-5678-1234-567812345678")
DATASET_ID_STR = str(DATASET_ID)
BASE = "/api/v1/metadata"


def _make_pool(fetchrow_result: dict) -> MagicMock:
    """Return a mock asyncpg pool whose acquire() yields a conn with the given fetchrow result."""
    mock_conn = AsyncMock()
    mock_conn.fetchrow.return_value = fetchrow_result

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = mock_conn
    mock_cm.__aexit__.return_value = False

    mock_pool = MagicMock()
    mock_pool.acquire.return_value = mock_cm
    return mock_pool, mock_conn


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Service layer
# ---------------------------------------------------------------------------

class TestGetDatasetMetricsService:

    async def test_returns_metrics_when_partitions_exist(self):
        from api.v1.metadata.services import get_dataset_metrics

        pool, _ = _make_pool({"partition_count": 5, "total_rows": 2500, "last_ingested_at": "2025-06-01T12:00:00"})
        with patch("api.v1.metadata.services.get_db_pool", AsyncMock(return_value=pool)):
            result = await get_dataset_metrics(DATASET_ID)

        assert result["partition_count"] == 5
        assert result["total_rows"] == 2500
        assert result["last_ingested_at"] == "2025-06-01T12:00:00"

    async def test_returns_zeros_and_null_when_no_partitions(self):
        from api.v1.metadata.services import get_dataset_metrics

        pool, _ = _make_pool({"partition_count": 0, "total_rows": 0, "last_ingested_at": None})
        with patch("api.v1.metadata.services.get_db_pool", AsyncMock(return_value=pool)):
            result = await get_dataset_metrics(DATASET_ID)

        assert result["partition_count"] == 0
        assert result["total_rows"] == 0
        assert result["last_ingested_at"] is None

    async def test_returns_error_dict_when_pool_unavailable(self):
        from api.v1.metadata.services import get_dataset_metrics

        with patch("api.v1.metadata.services.get_db_pool", AsyncMock(return_value=None)):
            result = await get_dataset_metrics(DATASET_ID)

        assert result["status"] == "error"
        assert "Database" in result["message"]

    async def test_passes_dataset_id_to_query(self):
        from api.v1.metadata.services import get_dataset_metrics

        pool, mock_conn = _make_pool({"partition_count": 1, "total_rows": 10, "last_ingested_at": None})
        with patch("api.v1.metadata.services.get_db_pool", AsyncMock(return_value=pool)):
            await get_dataset_metrics(DATASET_ID)

        _, call_kwargs = mock_conn.fetchrow.call_args
        positional = mock_conn.fetchrow.call_args.args
        assert DATASET_ID in positional

    async def test_queries_partitions_table(self):
        from api.v1.metadata.services import get_dataset_metrics

        pool, mock_conn = _make_pool({"partition_count": 2, "total_rows": 200, "last_ingested_at": None})
        with patch("api.v1.metadata.services.get_db_pool", AsyncMock(return_value=pool)):
            await get_dataset_metrics(DATASET_ID)

        sql = mock_conn.fetchrow.call_args.args[0].lower()
        assert "partitions" in sql
        assert "count" in sql
        assert "sum" in sql
        assert "max" in sql


# ---------------------------------------------------------------------------
# Route layer
# ---------------------------------------------------------------------------

class TestMetricsRoute:

    async def test_status_200(self, client):
        mock_svc = AsyncMock(return_value={"partition_count": 3, "total_rows": 300, "last_ingested_at": None})
        with patch("api.v1.metadata.router.get_dataset_metrics", mock_svc):
            resp = await client.get(f"{BASE}/datasets/{DATASET_ID_STR}/metrics")
        assert resp.status_code == 200

    async def test_response_values_pass_through(self, client):
        mock_svc = AsyncMock(return_value={"partition_count": 7, "total_rows": 1400, "last_ingested_at": "2025-06-15T08:30:00"})
        with patch("api.v1.metadata.router.get_dataset_metrics", mock_svc):
            body = (await client.get(f"{BASE}/datasets/{DATASET_ID_STR}/metrics")).json()
        assert body["partition_count"] == 7
        assert body["total_rows"] == 1400
        assert body["last_ingested_at"] == "2025-06-15T08:30:00"

    async def test_null_last_ingested_passes_through(self, client):
        mock_svc = AsyncMock(return_value={"partition_count": 0, "total_rows": 0, "last_ingested_at": None})
        with patch("api.v1.metadata.router.get_dataset_metrics", mock_svc):
            body = (await client.get(f"{BASE}/datasets/{DATASET_ID_STR}/metrics")).json()
        assert body["last_ingested_at"] is None

    async def test_service_called_with_correct_uuid(self, client):
        mock_svc = AsyncMock(return_value={"partition_count": 0, "total_rows": 0, "last_ingested_at": None})
        with patch("api.v1.metadata.router.get_dataset_metrics", mock_svc):
            await client.get(f"{BASE}/datasets/{DATASET_ID_STR}/metrics")
        mock_svc.assert_awaited_once_with(DATASET_ID)

    async def test_invalid_uuid_returns_422(self, client):
        resp = await client.get(f"{BASE}/datasets/not-a-uuid/metrics")
        assert resp.status_code == 422

    async def test_service_called_exactly_once_per_request(self, client):
        mock_svc = AsyncMock(return_value={"partition_count": 0, "total_rows": 0, "last_ingested_at": None})
        with patch("api.v1.metadata.router.get_dataset_metrics", mock_svc):
            await client.get(f"{BASE}/datasets/{DATASET_ID_STR}/metrics")
        assert mock_svc.await_count == 1
