# ADR-002 — Object Storage: MinIO over Cloud Storage

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs an object storage layer to serve as the data lake, storing partitioned Parquet files. The storage layer must be S3-compatible so Trino can query it using the standard S3 connector, and so the code mirrors real-world lakehouse architecture (S3, ADLS, GCS).

## Decision

Use **MinIO** as the local object storage layer.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Local filesystem | Not S3-compatible; Trino's S3 connector would not work; does not simulate real lakehouse storage |
| AWS S3 (real) | Requires AWS account, IAM setup, costs money, cannot run fully locally |
| Azure ADLS / GCS | Same issues as real S3 — cloud dependency, not local |
| SeaweedFS | Less mature S3 compatibility layer; fewer community resources |

## Consequences

**Benefits:**
- Fully S3-compatible API — Trino, Polars, and boto3 all connect to MinIO identically to how they would connect to AWS S3
- Ships with a web console on port 9001 for browsing buckets and objects visually
- Runs as a single Docker container with a persistent volume
- Free, open-source, widely used in local lakehouse setups

**Trade-offs:**
- MinIO in single-node mode does not provide erasure coding or distributed durability — but this is a local simulation, not a production system
- Bucket and access key configuration must be manually set up on first run (handled by Docker Compose environment variables)
