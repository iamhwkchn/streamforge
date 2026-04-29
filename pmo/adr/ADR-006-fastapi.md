# ADR-006 — Backend API Framework: FastAPI over Flask / Django

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a Python backend service to expose the metadata catalog (datasets, partitions, features) and proxy SQL queries to Trino. The service must be async-capable (connecting to Postgres via asyncpg), easy to structure into versioned routes, and fast to iterate on as a solo developer.

## Decision

Use **FastAPI** as the backend API framework.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Flask | Synchronous by default — would require threading or `asyncio` workarounds to handle async Postgres connections; no built-in OpenAPI documentation |
| Django + Django REST Framework | Heavyweight ORM and admin layer that is unnecessary for a lightweight metadata API; slower to set up for a solo project |
| aiohttp | Lower-level async HTTP framework; requires more boilerplate compared to FastAPI for routing and validation |
| Express (Node.js) | Would require switching runtime from Python, which is the primary language for data processing in this project |

## Consequences

**Benefits:**
- Native async support — integrates cleanly with `asyncpg` for async Postgres queries
- Automatic OpenAPI docs at `/docs` — no extra work for API documentation
- Pydantic-based request validation out of the box (used for `PartitionPayload` schema)
- Lifespan context manager handles Postgres connection pool startup and teardown cleanly
- Versioned router structure (`api/v1/`) is easy to extend without breaking changes

**Trade-offs:**
- No built-in ORM — SQL queries are written manually via `asyncpg`, which is intentional but requires discipline to avoid ad-hoc SQL sprawl
- Lightweight by design — anything requiring background task orchestration or a job queue will need an external solution
