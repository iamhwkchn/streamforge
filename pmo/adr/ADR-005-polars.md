# ADR-005 — Data Processing Library: Polars over Pandas / PySpark

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a Python library to read the source Excel dataset, transform and partition it, and write Parquet files to MinIO. The library must be fast, memory-efficient (running on a laptop), and have native Parquet write support.

## Decision

Use **Polars** for all ETL and data transformation logic.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Pandas | Row-based execution model, high memory usage for large datasets, no native parallelism — significantly slower than Polars for partition-level operations |
| PySpark | Requires a JVM and Spark cluster setup; extreme overkill for a single-node local process; startup time alone makes it impractical |
| DuckDB (Python) | Excellent for SQL-based transforms, but less natural for the row-by-row streaming enrichment pattern in the consumer |
| PyArrow directly | Lower-level API; Polars provides a more ergonomic DataFrame API while internally using Arrow memory format |

## Consequences

**Benefits:**
- Rust-based engine — significantly faster than Pandas for groupby, partition, and write operations
- Native `write_parquet()` using Apache Arrow — no intermediate conversion step
- `read_excel()` supports multi-sheet workbooks with `sheet_id=None` (used in bootstrap script)
- `partition_by()` method directly produces the year/month partitioning needed for the lake layout
- Low memory footprint through lazy evaluation and streaming support

**Trade-offs:**
- Polars API differs from Pandas — some team members may need to learn the Polars expression syntax
- Smaller ecosystem than Pandas for some edge-case libraries, though not relevant for this project's scope
