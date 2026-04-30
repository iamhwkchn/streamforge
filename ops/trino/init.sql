CREATE SCHEMA IF NOT EXISTS minio.retail
WITH (location = 's3a://raw/retail/');

CREATE TABLE IF NOT EXISTS minio.retail.retail_events (
    invoice       VARCHAR,
    stock_code    VARCHAR,
    description   VARCHAR,
    quantity      BIGINT,
    invoice_date  TIMESTAMP(3),
    price         DOUBLE,
    customer_id   VARCHAR,
    country       VARCHAR,
    year          INTEGER,
    month         INTEGER
)
WITH (
    external_location = 's3a://raw/retail/',
    format = 'PARQUET',
    partitioned_by = ARRAY['year', 'month']
);

CALL minio.system.sync_partition_metadata(
    schema_name => 'retail',
    table_name  => 'retail_events',
    mode        => 'FULL'
);
