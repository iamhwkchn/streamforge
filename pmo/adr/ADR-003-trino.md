# ADR-003 — SQL Analytics Engine: Trino over Alternatives

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a distributed SQL engine that can query Parquet files stored in MinIO directly, without copying data into a traditional database. This is the core compute layer of the lakehouse and must support industry-standard SQL over object storage.

## Decision

Use **Trino** as the distributed SQL engine.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| DuckDB | Excellent local performance, but primarily an embedded/in-process engine — does not simulate the distributed SQL layer found in real data platforms (Athena, Starburst, BigQuery) |
| Apache Spark (PySpark) | Too heavy for a laptop; requires a cluster setup or a large JVM footprint; better suited for batch ETL than interactive SQL |
| Presto | Trino is the actively maintained fork of Presto — effectively the same architecture with a better release cadence |
| Snowflake / BigQuery | Cloud-only; defeats the purpose of a fully local architecture |

## Consequences

**Benefits:**
- Industry-standard distributed SQL engine — the same architecture used by Athena (AWS), Starburst, and many enterprise data platforms
- Native S3/MinIO connector via Hive metastore or file-based catalog
- Supports querying partitioned Parquet files with predicate pushdown
- Runs as a single Docker container for local development

**Trade-offs:**
- Trino configuration (catalog, connector, Hive metastore) has a non-trivial learning curve
- Heavier JVM startup time compared to DuckDB
- Requires a Hive metastore or `iceberg` catalog setup to manage table metadata — adds configuration overhead
