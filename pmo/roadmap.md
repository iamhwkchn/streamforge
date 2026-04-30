# Project Roadmap — StreamForge

## How to Read This

- **Stage** = GitHub Milestone
- **Epic** = GitHub Issue (parent, with checklist)
- **Task** = GitHub Issue (child) or checklist item inside the epic
- **Size** = weekend effort (S = half-day, M = full weekend, L = needs splitting)
- Status: `Done` | `To Do`
- Weekends start: May 3, 2026

---

## Stage 1 — Local Lakehouse
**GitHub Milestone:** `Stage 1 — Local Lakehouse`
**Target:** May 31, 2026 (5 weekends)
**Goal:** Data is seeded into MinIO as Parquet, queryable via Trino, browsable in the UI. Metadata catalog fully operational.

**Definition of Done:**
- [ ] `docker compose up` starts all services cleanly
- [x] Bootstrap script seeds Parquet partitions into MinIO
- [ ] Trino returns SQL results against lake data
- [ ] API serves dataset, partition, and feature metadata
- [ ] UI displays datasets and executes a SQL query

---

### Epic S1-E1 — Metadata Catalog API
**Size:** S
**Status:** Done

| # | Task | Size | Status |
|---|---|---|---|
| S1-E1-T1 | Postgres schema: datasets, partitions, features tables | S | Done |
| S1-E1-T2 | `POST /api/v1/partitions` — register a partition | S | Done |
| S1-E1-T3 | `GET /api/v1/datasets` — list all datasets | S | Done |
| S1-E1-T4 | `GET /api/v1/datasets/{id}/partitions` — list partitions for a dataset | S | Done |
| S1-E1-T5 | `GET /api/v1/datasets/{id}/features` — list features for a dataset | S | Done |
| S1-E1-T6 | `POST /api/v1/features` — register a feature definition | S | Done |

---

### Epic S1-E2 — Bootstrap Lake Script
**Size:** S (nearly done, one task remaining)
**Status:** Partially Done

| # | Task | Size | Status |
|---|---|---|---|
| S1-E2-T1 | Read Online Retail II XLSX using Polars | S | Done |
| S1-E2-T2 | Partition data by year/month | S | Done |
| S1-E2-T3 | Write partitioned Parquet files to MinIO | S | Done |
| S1-E2-T4 | Register dataset in Postgres catalog | S | Done (via 02_seeding.sql) |
| S1-E2-T5 | Call `POST /partitions` per partition after MinIO write | S | To Do |

---

### Epic S1-E3 — Seed Feature Definitions
**Size:** S
**Status:** Partially Done

| # | Task | Size | Status |
|---|---|---|---|
| S1-E3-T1 | Seed `revenue_by_country` feature in Postgres | S | Done (via 02_seeding.sql) |
| S1-E3-T2 | Seed `top_customers_spend` feature in Postgres | S | Done (via 02_seeding.sql) |
| S1-E3-T3 | Seed `daily_order_volume` feature in Postgres | S | Done (via 02_seeding.sql) |
| S1-E3-T4 | Validate feature SQL definitions execute correctly in Trino | S | To Do |

---

### Epic S1-E4 — Trino SQL Engine Setup
**Size:** M (1 weekend)
**Status:** To Do
**Depends on:** MinIO with Parquet data (S1-E2 done)

| # | Task | Size | Status |
|---|---|---|---|
| S1-E4-T1 | Configure Trino Hive/file connector for MinIO | M | To Do |
| S1-E4-T2 | Validate Trino can list and query Parquet partitions | S | To Do |
| S1-E4-T3 | Verify 3 seeded feature SQL queries return results | S | To Do |

---

### Epic S1-E5 — FastAPI Query Endpoint
**Size:** S (half weekend)
**Status:** To Do
**Depends on:** Trino running, S1-E1 done

| # | Task | Size | Status |
|---|---|---|---|
| S1-E5-T1 | `POST /api/v1/query` — execute SQL via Trino, return results | S | To Do |
| S1-E5-T2 | Error handling for bad SQL and Trino connection failures | S | To Do |

---

### Epic S1-E6 — SvelteKit Frontend (Phase 1)
**Size:** L → 2 weekends
**Status:** To Do
**Depends on:** S1-E1, S1-E5 done

| # | Task | Size | Status |
|---|---|---|---|
| S1-E6-T1 | Project setup: SvelteKit + Vite + TailwindCSS | S | To Do |
| S1-E6-T2 | Dataset browser page — list datasets from API | S | To Do |
| S1-E6-T3 | Dataset detail page — schema + partition list + feature list | S | To Do |
| S1-E6-T4 | SQL query editor — textarea + run button + results table | M | To Do |
| S1-E6-T5 | Feature registry page — list and preview feature definitions | S | To Do |

---

## Stage 2 — Streaming Ingestion
**GitHub Milestone:** `Stage 2 — Streaming Ingestion`
**Target:** June 28, 2026 (4 weekends)
**Goal:** Live data flows from CSV producer through Redpanda into MinIO as Parquet in real time. Partitions auto-register. UI shows ingestion metrics.

**Definition of Done:**
- [ ] Producer publishes CSV rows to Redpanda topic `retail.events`
- [ ] Consumer reads, validates, enriches, and micro-batches records
- [ ] Consumer writes Parquet to MinIO and registers partition via API
- [ ] UI shows live partition count and last ingestion timestamp

---

### Epic S2-E1 — Kafka Producer
**Size:** M (1 weekend)
**Status:** To Do (stub exists, logic not implemented)
**Depends on:** Redpanda running

| # | Task | Size | Status |
|---|---|---|---|
| S2-E1-T1 | Read Online Retail II XLSX row by row with Polars | S | To Do |
| S2-E1-T2 | Publish each row as a JSON event to `retail.events` Redpanda topic | S | To Do |
| S2-E1-T3 | Configurable publish rate to simulate hourly extract | S | To Do |
| S2-E1-T4 | Producer startup logging and error handling | S | To Do |

---

### Epic S2-E2 — Stream Consumer
**Size:** L → 2 weekends
**Status:** To Do (stub exists, logic not implemented)
**Depends on:** S2-E1 done, MinIO running, S1-E1 done

| # | Task | Size | Status |
|---|---|---|---|
| S2-E2-T1 | Connect consumer to Redpanda and poll `retail.events` | S | To Do |
| S2-E2-T2 | Validate and enrich records (type casting, null checks) | S | To Do |
| S2-E2-T3 | Micro-batch records by configurable batch size or time window | M | To Do |
| S2-E2-T4 | Write each micro-batch as a Parquet file to MinIO | S | To Do |
| S2-E2-T5 | Register partition via `POST /api/v1/partitions` after each write | S | To Do |
| S2-E2-T6 | Consumer offset commit and crash recovery | S | To Do |

---

### Epic S2-E3 — Ingestion Metrics in UI
**Size:** S (half weekend)
**Status:** To Do
**Depends on:** S2-E1, S2-E2, S1-E6 done

| # | Task | Size | Status |
|---|---|---|---|
| S2-E3-T1 | `GET /api/v1/datasets/{id}/metrics` — partition count, last ingested at, total rows | S | To Do |
| S2-E3-T2 | Metrics panel on dataset detail page in SvelteKit | S | To Do |

---

## Stage 3 — Platform Simulation (Kubernetes)
**GitHub Milestone:** `Stage 3 — Platform Simulation`
**Target:** July 26, 2026 (4 weekends)
**Goal:** Every service in the stack runs on a local Kubernetes cluster. StatefulSets with PVCs for stateful services. End-to-end flow identical to Docker Compose mode.

**Definition of Done:**
- [ ] All services deploy via `kubectl apply`
- [ ] Stateful services (Postgres, MinIO, Redpanda) use PersistentVolumeClaims
- [ ] End-to-end data flow works identically to Docker Compose mode

---

### Epic S3-E1 — Kubernetes Manifests: Stateful Services
**Size:** M (1 weekend)
**Status:** To Do

| # | Task | Size | Status |
|---|---|---|---|
| S3-E1-T1 | Postgres StatefulSet + PVC + ClusterIP Service | S | To Do |
| S3-E1-T2 | MinIO StatefulSet + PVC + ClusterIP Service | S | To Do |
| S3-E1-T3 | Redpanda StatefulSet + PVC + ClusterIP Service | S | To Do |

---

### Epic S3-E2 — Kubernetes Manifests: Stateless Services
**Size:** M (1 weekend)
**Status:** To Do

| # | Task | Size | Status |
|---|---|---|---|
| S3-E2-T1 | Trino Deployment + ClusterIP Service | S | To Do |
| S3-E2-T2 | FastAPI Deployment + ClusterIP Service | S | To Do |
| S3-E2-T3 | SvelteKit Deployment + ClusterIP Service | S | To Do |
| S3-E2-T4 | Optional Ingress for external UI access | S | To Do |

---

### Epic S3-E3 — Validation and Documentation
**Size:** S (half weekend)
**Status:** To Do

| # | Task | Size | Status |
|---|---|---|---|
| S3-E3-T1 | End-to-end smoke test on local Kubernetes cluster (kind or minikube) | S | To Do |
| S3-E3-T2 | `ops/k8s/README.md` — setup and deploy instructions | S | To Do |
| S3-E3-T3 | Final `README.md` update with full architecture diagram | S | To Do |

---

## Weekend Plan

| Weekend | Target | Epics |
|---|---|---|
| May 3 | Stage 1 | S1-E1 (remaining GET endpoints + POST /features), S1-E2-T5 |
| May 10 | Stage 1 | S1-E4 (Trino setup + validation) |
| May 17 | Stage 1 | S1-E5 (FastAPI query endpoint), S1-E6 start (setup + dataset browser) |
| May 24 | Stage 1 | S1-E6 finish (SQL editor + feature page) |
| May 31 | Stage 1 | Buffer / Stage 1 polish and end-to-end demo |
| Jun 7 | Stage 2 | S2-E1 (Producer) |
| Jun 14 | Stage 2 | S2-E2 start (Consumer connect + validate + micro-batch) |
| Jun 21 | Stage 2 | S2-E2 finish (MinIO write + partition register + crash recovery), S2-E3 |
| Jun 28 | Stage 2 | Buffer / Stage 2 polish and streaming demo |
| Jul 5 | Stage 3 | S3-E1 (Stateful K8s manifests) |
| Jul 12 | Stage 3 | S3-E2 (Stateless K8s manifests) |
| Jul 19 | Stage 3 | S3-E3 (Validation + docs) |
| Jul 26 | Stage 3 | Buffer / final demo prep |
