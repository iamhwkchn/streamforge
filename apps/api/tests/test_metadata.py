"""
Integration tests for the Metadata Catalog API.

All tests run against real Postgres in Docker — no mocks.
Write tests clean up their own inserted rows via db_pool.
"""
import pytest

BASE = "/api/v1/metadata"
UNKNOWN_UUID = "00000000-0000-0000-0000-000000000000"


# ---------------------------------------------------------------------------
# GET /datasets
# ---------------------------------------------------------------------------

class TestListDatasets:
    """GET /api/v1/metadata/datasets — returns all registered datasets."""

    async def test_status_200(self, client):
        resp = await client.get(f"{BASE}/datasets")
        assert resp.status_code == 200

    async def test_response_is_list(self, client):
        resp = await client.get(f"{BASE}/datasets")
        assert isinstance(resp.json(), list)

    async def test_contains_retail_events(self, client):
        resp = await client.get(f"{BASE}/datasets")
        names = [d["name"] for d in resp.json()]
        assert "retail_events" in names

    async def test_dataset_has_required_fields(self, client):
        resp = await client.get(f"{BASE}/datasets")
        dataset = next(d for d in resp.json() if d["name"] == "retail_events")
        assert "id" in dataset
        assert "name" in dataset
        assert "storage_location" in dataset
        assert "created_at" in dataset

    async def test_storage_location_is_minio_path(self, client):
        resp = await client.get(f"{BASE}/datasets")
        dataset = next(d for d in resp.json() if d["name"] == "retail_events")
        assert dataset["storage_location"].startswith("s3a://")


# ---------------------------------------------------------------------------
# GET /datasets/{id}/partitions
# ---------------------------------------------------------------------------

class TestListPartitions:
    """GET /api/v1/metadata/datasets/{id}/partitions — returns partitions for a dataset."""

    async def test_status_200_with_valid_id(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/partitions")
        assert resp.status_code == 200

    async def test_response_is_list(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/partitions")
        assert isinstance(resp.json(), list)

    async def test_empty_list_for_unknown_dataset(self, client):
        resp = await client.get(f"{BASE}/datasets/{UNKNOWN_UUID}/partitions")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_partition_fields_when_present(self, client, db_pool, retail_events_id):
        """Seeds one partition, checks fields, then cleans up."""
        path = "s3a://raw/retail/test/field_check.parquet"
        await db_pool.execute(
            "INSERT INTO partitions (dataset_id, partition_path, row_count) VALUES ($1, $2, $3)",
            retail_events_id, path, 10,
        )
        try:
            resp = await client.get(f"{BASE}/datasets/{retail_events_id}/partitions")
            partition = next(p for p in resp.json() if p["partition_path"] == path)
            assert "id" in partition
            assert "dataset_id" in partition
            assert "partition_path" in partition
            assert "row_count" in partition
            assert "processed_at" in partition
        finally:
            await db_pool.execute("DELETE FROM partitions WHERE partition_path = $1", path)


# ---------------------------------------------------------------------------
# GET /datasets/{id}/features
# ---------------------------------------------------------------------------

class TestListFeatures:
    """GET /api/v1/metadata/datasets/{id}/features — returns feature definitions."""

    async def test_status_200_with_valid_id(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/features")
        assert resp.status_code == 200

    async def test_returns_three_seeded_features(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/features")
        assert len(resp.json()) == 3

    async def test_seeded_feature_names_present(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/features")
        names = {f["name"] for f in resp.json()}
        assert names == {"revenue_by_country", "top_customers_spend", "daily_order_volume"}

    async def test_feature_has_required_fields(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/features")
        feature = resp.json()[0]
        assert "id" in feature
        assert "name" in feature
        assert "sql_definition" in feature
        assert "dataset_id" in feature
        assert "created_at" in feature

    async def test_sql_definition_is_non_empty(self, client, retail_events_id):
        resp = await client.get(f"{BASE}/datasets/{retail_events_id}/features")
        for feature in resp.json():
            assert len(feature["sql_definition"]) > 0

    async def test_empty_list_for_unknown_dataset(self, client):
        resp = await client.get(f"{BASE}/datasets/{UNKNOWN_UUID}/features")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /partitions
# ---------------------------------------------------------------------------

class TestRegisterPartition:
    """POST /api/v1/metadata/partitions — registers a new partition."""

    async def test_success_response(self, client, db_pool):
        path = "s3a://raw/retail/test/register_success.parquet"
        payload = {"dataset_name": "retail_events", "partition_path": path, "row_count": 42}
        try:
            resp = await client.post(f"{BASE}/partitions", json=payload)
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
        finally:
            await db_pool.execute("DELETE FROM partitions WHERE partition_path = $1", path)

    async def test_row_is_persisted_in_db(self, client, db_pool):
        path = "s3a://raw/retail/test/persist_check.parquet"
        payload = {"dataset_name": "retail_events", "partition_path": path, "row_count": 99}
        try:
            await client.post(f"{BASE}/partitions", json=payload)
            row = await db_pool.fetchrow(
                "SELECT row_count FROM partitions WHERE partition_path = $1", path
            )
            assert row is not None
            assert row["row_count"] == 99
        finally:
            await db_pool.execute("DELETE FROM partitions WHERE partition_path = $1", path)

    async def test_error_on_unknown_dataset(self, client):
        payload = {
            "dataset_name": "does_not_exist",
            "partition_path": "s3a://raw/retail/test/noop.parquet",
            "row_count": 0,
        }
        resp = await client.post(f"{BASE}/partitions", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"

    async def test_missing_required_field_returns_422(self, client):
        resp = await client.post(f"{BASE}/partitions", json={"dataset_name": "retail_events"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /features
# ---------------------------------------------------------------------------

class TestRegisterFeature:
    """POST /api/v1/metadata/features — registers a new feature definition."""

    async def test_success_response(self, client, db_pool):
        name = "test_feature_integration"
        payload = {
            "name": name,
            "sql_definition": "SELECT 1",
            "dataset_name": "retail_events",
        }
        try:
            resp = await client.post(f"{BASE}/features", json=payload)
            assert resp.status_code == 200
            assert resp.json()["status"] == "success"
        finally:
            await db_pool.execute("DELETE FROM features WHERE name = $1", name)

    async def test_row_is_persisted_in_db(self, client, db_pool):
        name = "test_feature_persist"
        sql = "SELECT country FROM retail_events GROUP BY country"
        payload = {"name": name, "sql_definition": sql, "dataset_name": "retail_events"}
        try:
            await client.post(f"{BASE}/features", json=payload)
            row = await db_pool.fetchrow(
                "SELECT sql_definition FROM features WHERE name = $1", name
            )
            assert row is not None
            assert row["sql_definition"] == sql
        finally:
            await db_pool.execute("DELETE FROM features WHERE name = $1", name)

    async def test_error_on_unknown_dataset(self, client):
        payload = {
            "name": "orphan_feature",
            "sql_definition": "SELECT 1",
            "dataset_name": "does_not_exist",
        }
        resp = await client.post(f"{BASE}/features", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "error"

    async def test_missing_required_field_returns_422(self, client):
        resp = await client.post(f"{BASE}/features", json={"name": "incomplete"})
        assert resp.status_code == 422
