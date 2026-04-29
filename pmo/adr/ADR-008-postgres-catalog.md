# ADR-008 — Metadata Store: PostgreSQL over Alternatives

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a metadata catalog to track registered datasets, Parquet partition locations, row counts, and feature SQL definitions. This catalog is the source of truth for the API and UI — it must support structured relational queries, be durable between restarts, and be lightweight enough to run locally.

## Decision

Use **PostgreSQL** as the metadata catalog.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| SQLite | Lacks async driver support compatible with `asyncpg`; not suitable for concurrent writes from the consumer and API simultaneously; does not simulate production catalog systems |
| MongoDB | Document-oriented model adds flexibility that is not needed here — catalog data is highly structured and relational (datasets → partitions, datasets → features) |
| MySQL | Functionally viable, but Postgres is more widely used in the data engineering ecosystem and has better support for UUID types and `gen_random_uuid()` |
| Apache Atlas / OpenMetadata | Purpose-built metadata catalogs — far too heavy for a local simulation; these are the production systems this project is conceptually emulating |
| In-memory store (Redis) | Not durable across restarts; not suitable as a primary catalog store |

## Consequences

**Benefits:**
- Relational schema with foreign keys (`partitions.dataset_id → datasets.id`) enforces catalog integrity
- `asyncpg` provides a fast, native async Postgres driver compatible with FastAPI's async lifecycle
- `gen_random_uuid()` for primary keys works out of the box in Postgres 13+
- Docker volume mount ensures catalog data persists across container restarts
- SQL seeding scripts (`01_init.sql`, `02_seeding.sql`) run automatically via `docker-entrypoint-initdb.d`

**Trade-offs:**
- Requires a running Postgres container — adds to the Docker Compose dependency chain
- Schema migrations are manual for now (no Alembic or Flyway) — acceptable for v1 but will need a migration tool if the schema evolves significantly
