import logging
import os
import json
import signal
import time
import sys
from pathlib import Path

import polars as pl
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("streamforge.producer")

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

_shutdown_requested = False


def _request_shutdown(signum, _frame):
    global _shutdown_requested
    logger.info("Received signal %s — finishing current row and shutting down ...", signal.Signals(signum).name)
    _shutdown_requested = True


def load_dataset(path: str) -> list[dict]:
    logger.info("Loading dataset from %s ...", path)
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
    logger.info("Loaded %s rows, sorted by invoice_date ascending.", f"{len(full):,}")
    return full.to_dicts()


def main():
    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    if not Path(DATASET_PATH).exists():
        logger.error("Dataset not found at %s", DATASET_PATH)
        sys.exit(1)

    rows = load_dataset(DATASET_PATH)

    logger.info("Connecting to Redpanda at %s ...", REDPANDA_BROKERS)
    try:
        producer = KafkaProducer(
            bootstrap_servers=REDPANDA_BROKERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            retries=3,
        )
    except NoBrokersAvailable:
        logger.error("Could not connect to Redpanda at %s. Is it running?", REDPANDA_BROKERS)
        sys.exit(1)

    logger.info("Publishing %s events to '%s' at %s events/sec ...", f"{len(rows):,}", TOPIC, EVENTS_PER_SECOND)
    delay = 1.0 / EVENTS_PER_SECOND

    published = 0
    for i, row in enumerate(rows, start=1):
        if _shutdown_requested:
            logger.warning("Shutdown requested — stopping after %s / %s events.", f"{published:,}", f"{len(rows):,}")
            break

        try:
            producer.send(TOPIC, value=row)
            published = i
        except Exception as e:
            logger.error("[row %s] Send error: %s", i, e)
            continue

        if i % 1000 == 0:
            producer.flush()
            logger.info("Published %s / %s events", f"{i:,}", f"{len(rows):,}")

        time.sleep(delay)

    producer.flush()
    producer.close()
    logger.info("Done. Published %s events to '%s'.", f"{published:,}", TOPIC)


if __name__ == "__main__":
    main()
