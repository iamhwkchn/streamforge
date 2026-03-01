import os
import io
import polars as pl
from minio import Minio
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATASET_PATH = PROJECT_ROOT / "data" / "raw_datasets" / "online_retail_ll.xlsx"
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "raw"
DATASET_PREFIX = "retail"

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
        # Requires 'fastexcel' or 'openpyxl' installed
        sheets_dict = pl.read_excel(DATASET_PATH, sheet_id=None)
    except Exception as e:
        print(f"Error reading Excel workbook: {e}")
        return

    all_data = []
    for sheet_name, df in sheets_dict.items():
        print(f"Processing sheet: {sheet_name} ({len(df)} rows)")
        
        # Standardize columns and extract time partitions
        processed_df = df.with_columns([
            pl.col("InvoiceDate").dt.year().alias("year"),
            pl.col("InvoiceDate").dt.month().alias("month")
        ])
        all_data.append(processed_df)

    # Combine and Partition
    print("Merging all years and creating lake partitions...")
    full_df = pl.concat(all_data)
    
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

    print("Multi-sheet Bootstrap Complete!")
    print(f"Total rows ingested: {len(full_df)}")

if __name__ == "__main__":
    bootstrap()