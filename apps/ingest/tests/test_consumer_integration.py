"""
Integration tests for consumer.py — requires MinIO and the API running.

Run after:
    docker compose down -v
    docker compose up -d minio postgres api

These tests truncate the partitions table and clear MinIO's retail/ prefix
before each test to ensure a clean slate.
"""
import io
import sys
from pathlib import Path

import polars as pl
import psycopg2
import pytest
import requests as req
from minio import Minio

sys.path.insert(0, str(Path(__file__).parent.parent))
from consumer import parse_batch, register_partition, write_partition

API_BASE_URL = "http://localhost:8000"
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "raw"
DATASET_NAME = "retail_events"
PG_DSN = "host=localhost port=5432 dbname=streamforge user=admin password=password"


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def services_available() -> bool:
    try:
        req.get(f"{API_BASE_URL}/api/v1/metadata/datasets", timeout=2)
        mc = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
        mc.list_buckets()
        psycopg2.connect(PG_DSN).close()
        return True
    except Exception:
        return False


skip_if_no_services = pytest.mark.skipif(
    not services_available(),
    reason="Services not reachable — start with: docker compose up -d minio postgres api",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_minio_client() -> Minio:
    return Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)


def get_partitions_from_api() -> list[dict]:
    datasets = req.get(f"{API_BASE_URL}/api/v1/metadata/datasets", timeout=10).json()
    dataset = next((d for d in datasets if d["name"] == DATASET_NAME), None)
    if not dataset:
        return []
    return req.get(
        f"{API_BASE_URL}/api/v1/metadata/datasets/{dataset['id']}/partitions", timeout=10
    ).json()


def make_retail_df(rows: list[dict]) -> pl.DataFrame:
    return pl.DataFrame({
        "invoice": [r["invoice"] for r in rows],
        "stock_code": [r["stock_code"] for r in rows],
        "description": [r["description"] for r in rows],
        "quantity": pl.Series([r["quantity"] for r in rows], dtype=pl.Int64),
        "invoice_date": [r["invoice_date"] for r in rows],
        "price": pl.Series([r["price"] for r in rows], dtype=pl.Float64),
        "customer_id": [r["customer_id"] for r in rows],
        "country": [r["country"] for r in rows],
    })


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_if_no_services
class TestConsumerIntegration:

    @pytest.fixture(autouse=True)
    def clean_state(self):
        """Truncates partitions table and clears MinIO retail/ prefix before each test.
        Lives inside the class so it only runs when the class is not skipped."""
        conn = psycopg2.connect(PG_DSN)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE partitions")
        conn.close()

        mc = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
        if mc.bucket_exists(MINIO_BUCKET):
            objects = list(mc.list_objects(MINIO_BUCKET, prefix="retail/", recursive=True))
            for obj in objects:
                mc.remove_object(MINIO_BUCKET, obj.object_name)
        else:
            mc.make_bucket(MINIO_BUCKET)

    def test_write_partition_creates_parquet_in_minio(self):
        mc = make_minio_client()
        df = make_retail_df([
            {"invoice": "A1", "stock_code": "X", "description": "d", "quantity": 1,
             "invoice_date": "2010-12-01T08:26:00", "price": 2.55, "customer_id": "1", "country": "UK"},
        ] * 5)
        object_path = "retail/year=2010/month=12/data.parquet"

        write_partition(mc, df, MINIO_BUCKET, object_path)

        response = mc.get_object(MINIO_BUCKET, object_path)
        result = pl.read_parquet(io.BytesIO(response.read()))
        response.close()
        assert len(result) == 5

    def test_register_partition_creates_catalog_entry(self):
        path = "s3a://raw/retail/year=2010/month=12/data.parquet"
        ok = register_partition(API_BASE_URL, DATASET_NAME, path, 5)

        assert ok is True
        partitions = get_partitions_from_api()
        assert len(partitions) == 1
        assert partitions[0]["partition_path"] == path
        assert partitions[0]["row_count"] == 5

    def test_register_partition_upsert_updates_row_count(self):
        path = "s3a://raw/retail/year=2010/month=12/data.parquet"
        register_partition(API_BASE_URL, DATASET_NAME, path, 5)
        register_partition(API_BASE_URL, DATASET_NAME, path, 10)

        partitions = get_partitions_from_api()
        assert len(partitions) == 1
        assert partitions[0]["row_count"] == 10

    def test_parse_batch_cleans_and_types_records(self):
        records = [
            {
                "invoice": "536365", "stock_code": "85123A", "description": "Item A",
                "quantity": 6, "invoice_date": "2010-12-01T08:26:00",
                "price": 2.55, "customer_id": "17850", "country": "United Kingdom",
            },
            {
                "invoice": "536366", "stock_code": "22752", "description": "Item B",
                "quantity": 2, "invoice_date": None,
                "price": 1.45, "customer_id": None, "country": "Germany",
            },
        ]
        df = parse_batch(records)

        assert len(df) == 1
        assert df["quantity"].dtype == pl.Int64
        assert df["price"].dtype == pl.Float64
        assert "year" in df.columns and "month" in df.columns
        assert df["year"][0] == 2010
        assert df["month"][0] == 12

    def test_full_pipeline_write_and_register(self):
        mc = make_minio_client()
        records = [
            {"invoice": "A", "stock_code": "X", "description": "d", "quantity": 1,
             "invoice_date": "2010-11-01T10:00:00", "price": 1.0, "customer_id": "1", "country": "UK"},
            {"invoice": "B", "stock_code": "Y", "description": "d", "quantity": 2,
             "invoice_date": "2010-12-01T10:00:00", "price": 2.0, "customer_id": "2", "country": "UK"},
            {"invoice": "C", "stock_code": "Z", "description": "d", "quantity": 3,
             "invoice_date": "2010-12-05T10:00:00", "price": 3.0, "customer_id": "3", "country": "UK"},
        ]
        df = parse_batch(records)
        groups = df.partition_by(["year", "month"], include_key=True)

        for group_df in groups:
            year = int(group_df["year"][0])
            month = int(group_df["month"][0])
            batch_data = group_df.drop(["year", "month"])
            object_path = f"retail/year={year}/month={month:02d}/data.parquet"
            write_partition(mc, batch_data, MINIO_BUCKET, object_path)
            register_partition(API_BASE_URL, DATASET_NAME, f"s3a://{MINIO_BUCKET}/{object_path}", len(batch_data))

        nov = mc.get_object(MINIO_BUCKET, "retail/year=2010/month=11/data.parquet")
        dec = mc.get_object(MINIO_BUCKET, "retail/year=2010/month=12/data.parquet")
        assert len(pl.read_parquet(io.BytesIO(nov.read()))) == 1
        assert len(pl.read_parquet(io.BytesIO(dec.read()))) == 2
        nov.close()
        dec.close()

        partitions = get_partitions_from_api()
        assert len(partitions) == 2
        paths = {p["partition_path"] for p in partitions}
        assert "s3a://raw/retail/year=2010/month=11/data.parquet" in paths
        assert "s3a://raw/retail/year=2010/month=12/data.parquet" in paths
