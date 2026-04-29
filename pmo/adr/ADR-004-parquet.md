# ADR-004 — Data Format: Apache Parquet over Row-Based Formats

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a file format for storing data in the lake (MinIO). The format must be efficient for analytical queries (column scans, aggregations), natively supported by Trino and Polars, and standard in the lakehouse ecosystem.

## Decision

Use **Apache Parquet** as the storage format for all lake data.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| CSV | Row-based, no compression, no schema enforcement, no predicate pushdown — entirely unsuitable for analytics at lake scale |
| JSON / JSONL | Row-based, schema-less, verbose — poor query performance for analytical workloads |
| ORC | Also columnar and lakehouse-compatible, but Parquet has broader ecosystem support (Polars, PyArrow, Trino, Spark all prefer Parquet) |
| Delta Lake / Iceberg | Table formats built on Parquet — valuable for ACID transactions and time travel, but adds significant configuration complexity for v1 of this project |
| Avro | Better for streaming serialization (row-based), not optimized for analytical reads |

## Consequences

**Benefits:**
- Columnar format — Trino only reads the columns referenced in a query, dramatically reducing I/O
- Native compression per column (Snappy, Zstd) reduces storage size significantly
- Supported natively by Polars (`write_parquet`), PyArrow, Trino, Spark, DuckDB, and every major analytics tool
- Schema is embedded in the file footer — self-describing without an external catalog
- Partitioned Parquet (year/month folder structure) enables partition pruning in Trino

**Trade-offs:**
- Not human-readable — requires tooling (DuckDB, Python, Parquet CLI) to inspect
- Immutable once written — no in-place updates (acceptable for append-only lake ingestion)
