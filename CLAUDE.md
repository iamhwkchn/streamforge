# StreamForge

A fully local streaming lakehouse: Kafka-style ingestion (Redpanda) → Parquet data lake (MinIO) → distributed SQL (Trino) → metadata catalog (Postgres) → FastAPI → SvelteKit UI. See [README.md](README.md) for the architecture diagram and [idea.md](idea.md) / [pmo/adr/](pmo/adr/) for the "why" behind each technology choice.

## Layout

- `apps/api` — FastAPI backend. Metadata catalog endpoints (`api/v1/metadata`) and the Trino query endpoint (`api/v1/query`).
- `apps/ingest` — Kafka producer (`producer.py`) and consumer (`consumer.py`) for streaming ingestion.
- `apps/web` — SvelteKit frontend (Datasets, Query, Features pages).
- `ops/docker` — `docker-compose.yml`, the only orchestration file in active use (Kubernetes manifests for Stage 3 are still in progress, see `pmo/roadmap.md`).
- `ops/postgres` — schema + seed SQL, auto-run by Postgres on first boot via `docker-entrypoint-initdb.d`.
- `scripts/` — one-off Poetry-managed scripts for the static Stage-1 lake bootstrap and Trino validation (distinct from the always-on streaming producer/consumer).

## Running it

```bash
make up      # downloads the dataset (if missing) and starts the full stack
make test    # runs apps/api and apps/ingest pytest suites
make logs    # tail all service logs
make down    # stop everything
make clean   # stop and wipe persisted Postgres/MinIO/Trino state
```

See the `Makefile` for the exact commands each target runs — don't duplicate them here, they'll drift.

## Conventions worth knowing before editing

- **No ORM.** `apps/api` talks to Postgres directly via `asyncpg` (see `db/connection.py`). Service functions in `api/v1/metadata/services.py` return `{"status": "error", "message": ...}` dicts for handled cases (unknown dataset, duplicate name, missing pool) rather than raising — that's the established pattern for that module. The query layer (`api/v1/query/services.py`) instead raises `HTTPException` for bad SQL / unreachable Trino. Match whichever pattern the module you're touching already uses.
- **Read-only SQL guard.** Any path that executes user-supplied SQL against Trino must go through `_assert_read_only` in `apps/api/api/v1/query/services.py` — it only allows `SELECT`/`WITH`. Feature "run" and the Query page both route through the same `/api/v1/query` endpoint for this reason; don't add a second SQL-execution path that bypasses it.
- **Ingestion crash-safety.** `apps/ingest/consumer.py` disables Kafka auto-commit and only commits offsets after a batch's Parquet write *and* partition registration both succeed (`enable_auto_commit=False`, manual `consumer.commit()`). Partitions are read-merge-deduped (`.unique()`) on every write, which is what makes re-processing after a crash safe. Don't "simplify" this into an unconditional commit.
- **Structured logging in ingest.** `producer.py` and `consumer.py` use the stdlib `logging` module, not `print`. Keep new ingest code consistent with that.
- **Tests run against a real Postgres**, not mocks — `apps/api/tests` and `apps/ingest/tests` expect the Docker stack (or at least Postgres) to be up. See the docstring at the top of `apps/api/tests/test_metadata.py`.
- **Env vars are read once, at import, into module-level constants** in both `apps/ingest/producer.py` and `apps/api/core/config.py` — they are not re-read inside functions. A test that does `patch.dict("os.environ", {...})` after import has no effect on code that references the already-bound constant; patch the constant itself (`patch.object(module, "CONST", value)`). `test_exits_when_file_not_found` in `apps/ingest/tests/test_producer.py` got this wrong and silently fell through to publishing the full real dataset to a live Redpanda broker — fixed, but a reminder this pattern bites easily.

## Further reading

- [docs/metadata_catalog.md](docs/metadata_catalog.md) — Postgres catalog schema and registration flow
- [docs/streaming_ingestion.md](docs/streaming_ingestion.md) — producer/consumer design, crash recovery, idempotency
- [docs/query_engine.md](docs/query_engine.md) — Trino execution path, the read-only SQL guard, pagination
- [docs/frontend.md](docs/frontend.md) — SvelteKit routes, API client, UI workflows
- [docs/feature_registry.md](docs/feature_registry.md) — save/list/run/delete lifecycle for named SQL features

## Project status

Stages 1 (Local Lakehouse) and 2 (Streaming Ingestion) are complete. Stage 3 (Kubernetes) is in progress — current task breakdown is in `pmo/roadmap.md`.
