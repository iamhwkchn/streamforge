# StreamForge

StreamForge is a local streaming lakehouse with a feature registry, mimicking a real-world data platform.

## Architecture

- **Ingestion**: Redpanda (Kafka) -> Ingestion Worker (Polars) -> MinIO (Parquet)
- **Catalog**: Postgres (Datasets, Partitions, Features)
- **Compute**: Trino (Distributed SQL Engine)
- **Backend**: FastAPI
- **Frontend**: Svelte (Vite)

## Repository Structure

- `apps/api`: FastAPI Backend
- `apps/web`: Svelte Frontend
- `apps/ingest`: Python Ingestion Worker
- `ops/`: Infrastructure configuration (Docker, Trino, Postgres)

## Getting Started

See `ops/docker/README.md` for infrastructure setup.
