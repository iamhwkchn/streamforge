import os
import json
import time
import sys
from pathlib import Path

import polars as pl
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

REDPANDA_BROKERS = os.getenv("REDPANDA_BROKERS", "localhost:9092")
DATASET_PATH = os.getenv(
    "DATASET_PATH",
    str(Path(__file__).parent.parent.parent / "data" / "raw_datasets" / "online_retail_II.xlsx"),
)
TOPIC = "retail.events"
EVENTS_PER_SECOND = int(os.getenv("EVENTS_PER_SECOND", "100"))

COLUMN_RENAME = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}


def load_dataset(path: str) -> list[dict]:
    print(f"Loading dataset from {path} ...")
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True)
    sheet_names = wb.sheetnames
    wb.close()

    frames = []
    for name in sheet_names:
        df = pl.read_excel(
            path,
            sheet_name=name,
            schema_overrides={"Invoice": pl.Utf8, "StockCode": pl.Utf8},
        )
        # fastexcel already parses InvoiceDate as Datetime — no string parsing needed
        df = (
            df.drop_nulls(subset=["InvoiceDate"])
            .with_columns(pl.col("Customer ID").cast(pl.Utf8))
            .rename(COLUMN_RENAME)
            .with_columns(
                pl.col("invoice_date").dt.strftime("%Y-%m-%dT%H:%M:%S")
            )
        )
        frames.append(df)

    full = pl.concat(frames).sort("invoice_date")
    print(f"Loaded {len(full):,} rows, sorted by invoice_date ascending.")
    return full.to_dicts()


def main():
    if not Path(DATASET_PATH).exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        sys.exit(1)

    rows = load_dataset(DATASET_PATH)

    print(f"Connecting to Redpanda at {REDPANDA_BROKERS} ...")
    try:
        producer = KafkaProducer(
            bootstrap_servers=REDPANDA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3,
        )
    except NoBrokersAvailable:
        print(f"ERROR: Could not connect to Redpanda at {REDPANDA_BROKERS}. Is it running?")
        sys.exit(1)

    print(f"Publishing {len(rows):,} events to '{TOPIC}' at {EVENTS_PER_SECOND} events/sec ...")
    delay = 1.0 / EVENTS_PER_SECOND

    for i, row in enumerate(rows, start=1):
        try:
            producer.send(TOPIC, value=row)
        except Exception as e:
            print(f"  [row {i}] Send error: {e}")
            continue

        if i % 1000 == 0:
            producer.flush()
            print(f"  Published {i:,} / {len(rows):,} events")

        time.sleep(delay)

    producer.flush()
    print(f"Done. Published {len(rows):,} events to '{TOPIC}'.")


if __name__ == "__main__":
    main()
