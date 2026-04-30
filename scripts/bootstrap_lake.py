import os
import io
import httpx
import polars as pl
from minio import Minio
from pathlib import Path
import openpyxl

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATASET_PATH = PROJECT_ROOT / "data" / "raw_datasets" / "online_retail_II.xlsx"
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "raw"
DATASET_PREFIX = "retail"
API_BASE_URL = "http://localhost:8000"


def register_partition_with_api(
    api_base_url: str,
    dataset_name: str,
    partition_path: str,
    row_count: int,
) -> dict:
    """
    POSTs a partition registration to the metadata catalog API.

    Input:
        api_base_url   (str) — base URL of the StreamForge API
        dataset_name   (str) — name of the dataset (e.g. "retail_events")
        partition_path (str) — full S3 path of the Parquet file (e.g. "s3a://raw/...")
        row_count      (int) — number of rows in the partition

    Output:
        dict — API response body, e.g. {"status": "success", ...} or {"status": "error", ...}
        Returns {"status": "error", "message": str} on network failure.
    """
    try:
        resp = httpx.post(
            f"{api_base_url}/api/v1/metadata/partitions",
            json={
                "dataset_name": dataset_name,
                "partition_path": partition_path,
                "row_count": row_count,
            },
            timeout=10,
        )
        return resp.json()
    except httpx.RequestError as e:
        return {"status": "error", "message": str(e)}


def bootstrap():
    """
    Reads all sheets from the Excel dataset and seeds MinIO with partitioned Parquet files.
    """
    print("Starting StreamForge Multi-Sheet Bootstrap...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    # Initialize MinIO Client
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")

    # Process Excel Sheets
    # pl.read_excel with sheet_id=None returns a dictionary of all sheets
    print(f"Reading all sheets from: {DATASET_PATH}")
    try:
        wb = openpyxl.load_workbook(DATASET_PATH, read_only=True)
        sheet_names = wb.sheetnames
        wb.close()
        sheets_dict = {
            name: pl.read_excel(
                DATASET_PATH,
                sheet_name=name,
                schema_overrides={"Invoice": pl.Utf8, "StockCode": pl.Utf8},
            )
            for name in sheet_names
        }
    except Exception as e:
        print(f"Error reading Excel workbook: {e}")
        return

    all_data = []
    for sheet_name, df in sheets_dict.items():
        print(f"Processing sheet: {sheet_name} ({len(df)} rows)")
        
        # Standardize columns and extract time partitions
        # xlsx2csv surfaces dates as strings; parse before extracting year/month
        processed_df = df.with_columns(
            pl.col("InvoiceDate").str.to_datetime("%d/%m/%y %H:%M", strict=False)
        ).with_columns([
            pl.col("InvoiceDate").dt.year().alias("year"),
            pl.col("InvoiceDate").dt.month().alias("month")
        ])
        all_data.append(processed_df)

    # Combine and Partition
    print("Merging all years and creating lake partitions...")
    full_df = pl.concat(all_data).drop_nulls(subset=["InvoiceDate"])
    
    # Group by year/month to create the folder structure
    partitions = full_df.partition_by(["year", "month"], include_key=True)
    
    for p_df in partitions:
        year = p_df["year"][0]
        month = p_df["month"][0]
        
        # Define the S3 path: retail/year=YYYY/month=MM/data.parquet
        s_path = f"{DATASET_PREFIX}/year={year}/month={month:02d}/data.parquet"
        
        # Convert partition to Parquet in-memory
        parquet_buffer = io.BytesIO()
        p_df.write_parquet(parquet_buffer)
        parquet_buffer.seek(0)
        
        # Upload to MinIO
        client.put_object(
            BUCKET_NAME,
            s_path,
            data=parquet_buffer,
            length=parquet_buffer.getbuffer().nbytes,
            content_type="application/octet-stream"
        )
        print(f"Uploaded: {s_path}")

        # Register partition in metadata catalog
        result = register_partition_with_api(
            api_base_url=API_BASE_URL,
            dataset_name="retail_events",
            partition_path=f"s3a://{BUCKET_NAME}/{s_path}",
            row_count=len(p_df),
        )
        if result.get("status") == "success":
            print(f"  Registered partition: s3a://{BUCKET_NAME}/{s_path} ({len(p_df)} rows)")
        else:
            print(f"  Warning: metadata registration failed — {result.get('message')}")

    print("Multi-sheet Bootstrap Complete!")
    print(f"Total rows ingested: {len(full_df)}")

if __name__ == "__main__":
    bootstrap()