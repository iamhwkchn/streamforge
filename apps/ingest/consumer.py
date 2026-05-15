import io
import json
import os
import sys
import time

import polars as pl
import requests
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from minio import Minio

REDPANDA_BROKERS = os.getenv("REDPANDA_BROKERS", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "raw")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50000"))
BATCH_TIMEOUT_SECS = int(os.getenv("BATCH_TIMEOUT_SECS", "10"))

TOPIC = "retail.events"
DATASET_NAME = "retail_events"
DATASET_PREFIX = "retail"
GROUP_ID = "streamforge-consumer"


_BATCH_SCHEMA = {
    "invoice": pl.Utf8,
    "stock_code": pl.Utf8,
    "description": pl.Utf8,
    "quantity": pl.Utf8,
    "invoice_date": pl.Utf8,
    "price": pl.Utf8,
    "customer_id": pl.Utf8,
    "country": pl.Utf8,
}


def parse_batch(records: list[dict]) -> pl.DataFrame:
    """
    Casts raw JSON dicts to a typed Polars DataFrame.
    Drops rows where invoice_date cannot be parsed.
    Adds year and month columns derived from invoice_date.
    """
    if not records:
        return pl.DataFrame()

    # Declare everything as Utf8 first to avoid schema inference failures
    # when customer_id is null in early rows (polars 1.x infers Null type).
    df = pl.DataFrame(records, schema=_BATCH_SCHEMA, infer_schema_length=0)
    df = df.with_columns([
        pl.col("quantity").cast(pl.Int64, strict=False),
        pl.col("price").cast(pl.Float64, strict=False),
        pl.col("invoice_date").str.to_datetime(
            "%Y-%m-%dT%H:%M:%S", strict=False
        ),
    ]).drop_nulls(subset=["invoice_date"])

    return df.with_columns([
        pl.col("invoice_date").dt.year().alias("year"),
        pl.col("invoice_date").dt.month().alias("month"),
    ])


def collect_batch(consumer: KafkaConsumer, batch_size: int, timeout_secs: int) -> list[dict]:
    """Polls until batch_size records collected or timeout_secs elapsed."""
    messages = []
    deadline = time.monotonic() + timeout_secs

    while len(messages) < batch_size and time.monotonic() < deadline:
        remaining_ms = int((deadline - time.monotonic()) * 1000)
        poll_ms = min(500, max(1, remaining_ms))
        records = consumer.poll(timeout_ms=poll_ms, max_records=batch_size - len(messages))
        for tp_messages in records.values():
            for msg in tp_messages:
                try:
                    messages.append(json.loads(msg.value))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

    return messages


def read_existing_partition(minio_client: Minio, bucket: str, object_path: str) -> pl.DataFrame | None:
    """Downloads an existing Parquet partition from MinIO. Returns None if not found."""
    try:
        response = minio_client.get_object(bucket, object_path)
        data = response.read()
        response.close()
        return pl.read_parquet(io.BytesIO(data))
    except Exception as e:
        if "NoSuchKey" in str(e) or "NoSuchBucket" in str(e):
            return None
        raise


def write_partition(minio_client: Minio, df: pl.DataFrame, bucket: str, object_path: str) -> None:
    """Writes a Polars DataFrame as Parquet to MinIO, overwriting any existing object."""
    buffer = io.BytesIO()
    df.write_parquet(buffer)
    buffer.seek(0)
    minio_client.put_object(
        bucket,
        object_path,
        data=buffer,
        length=buffer.getbuffer().nbytes,
        content_type="application/octet-stream",
    )


def register_partition(api_base_url: str, dataset_name: str, partition_path: str, row_count: int) -> bool:
    """POSTs a partition registration to the catalog API. Returns True on success."""
    try:
        resp = requests.post(
            f"{api_base_url}/api/v1/metadata/partitions",
            json={"dataset_name": dataset_name, "partition_path": partition_path, "row_count": row_count},
            timeout=10,
        )
        return resp.json().get("status") == "success"
    except Exception as e:
        print(f"  Warning: partition registration failed — {e}")
        return False


def main():
    print("StreamForge Consumer starting ...")
    print(f"  Redpanda: {REDPANDA_BROKERS}  |  MinIO: {MINIO_ENDPOINT}  |  API: {API_BASE_URL}")
    print(f"  Batch: up to {BATCH_SIZE} records or {BATCH_TIMEOUT_SECS}s")

    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        print(f"  Created bucket: {MINIO_BUCKET}")

    print(f"Connecting to Redpanda at {REDPANDA_BROKERS} ...")
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=REDPANDA_BROKERS,
            group_id=GROUP_ID,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
            max_partition_fetch_bytes=10 * 1024 * 1024,
            fetch_max_bytes=100 * 1024 * 1024,
        )
    except NoBrokersAvailable:
        print(f"ERROR: Could not connect to Redpanda at {REDPANDA_BROKERS}.")
        sys.exit(1)

    print(f"Polling '{TOPIC}' (group: {GROUP_ID}) ...")
    while True:
        raw_records = collect_batch(consumer, BATCH_SIZE, BATCH_TIMEOUT_SECS)
        if not raw_records:
            continue

        print(f"Collected {len(raw_records)} records — processing ...")

        try:
            df = parse_batch(raw_records)
        except Exception as e:
            print(f"  Parse error: {e} — skipping batch")
            consumer.commit()
            continue

        if df.is_empty():
            consumer.commit()
            continue

        groups = df.partition_by(["year", "month"], include_key=True)
        all_ok = True

        for group_df in groups:
            year = int(group_df["year"][0])
            month = int(group_df["month"][0])
            batch_data = group_df.drop(["year", "month"])
            object_path = f"{DATASET_PREFIX}/year={year}/month={month:02d}/data.parquet"
            partition_path = f"s3a://{MINIO_BUCKET}/{object_path}"

            try:
                existing = read_existing_partition(minio_client, MINIO_BUCKET, object_path)
                if existing is not None:
                    merged = pl.concat([existing, batch_data]).unique()
                else:
                    merged = batch_data
                write_partition(minio_client, merged, MINIO_BUCKET, object_path)
                ok = register_partition(API_BASE_URL, DATASET_NAME, partition_path, len(merged))
                prev = len(existing) if existing is not None else 0
                if ok:
                    print(f"  year={year}/month={month:02d}: {prev} + {len(batch_data)} → {len(merged)} rows")
                else:
                    print(f"  Warning: write OK but registration failed for year={year}/month={month:02d}")
                    all_ok = False
            except Exception as e:
                print(f"  Error on year={year}/month={month:02d}: {e}")
                all_ok = False

        if all_ok:
            consumer.commit()
        else:
            print("  Errors in batch — not committing offsets (will retry)")


if __name__ == "__main__":
    main()
