# Project Charter — StreamForge

## 1. Project Overview

| Field | Detail |
|---|---|
| Project Name | StreamForge |
| Owner | Sriram Sivaraman |
| Start Date | April 2026 |
| Target Completion | July 2026 |
| Work Cadence | Weekends only (~8–10 hours per weekend) |
| Repository | github.com/iamhwkchn/streamforge |

---

## 2. Problem Statement

Modern data platforms combine streaming ingestion, object storage, distributed SQL engines, metadata catalogs, and analytics UIs. These systems are cloud-based, expensive, and difficult to study end-to-end without production access.

There is no simple, fully local, open-source project that demonstrates how data flows from an upstream source through streaming ingestion into a Parquet-based data lake, becomes queryable via a distributed SQL engine, and is exposed through a feature and analytics UI.

---

## 3. Goal

Build StreamForge — a fully local simulation of a modern streaming lakehouse — using open-source technologies, runnable on a single laptop, to demonstrate end-to-end data engineering depth.

---

## 4. Success Criteria

- [ ] Sales data flows from CSV through Redpanda into MinIO as partitioned Parquet
- [ ] Trino can query Parquet data in MinIO via SQL
- [ ] Postgres metadata catalog tracks all datasets, partitions, and features
- [ ] FastAPI exposes catalog and query endpoints
- [ ] SvelteKit UI supports dataset browsing, SQL querying, and feature definition
- [ ] Full stack starts with a single `docker compose up`
- [ ] Optional Kubernetes manifests exist for each service

---

## 5. Scope

### In Scope
- Streaming ingestion via Redpanda (Kafka API)
- Parquet-based data lake on MinIO
- Postgres metadata catalog (datasets, partitions, features)
- Trino as the distributed SQL engine
- FastAPI backend serving catalog and query APIs
- SvelteKit frontend for analytics and feature exploration
- Docker Compose as the primary local orchestration
- Kubernetes manifests as a secondary deployment mode

### Out of Scope
- Production-grade scalability or multi-node deployment
- Authentication or multi-tenancy
- Real-time alerting or monitoring dashboards
- Support for datasets other than Online Retail II (for v1)

---

## 6. Dataset

**Online Retail II (UCI)** — real transactional sales data (2009–2011) stored in `data/raw_datasets/online_retail_II.xlsx`.

Used to simulate event-based transactional data flowing through the platform.

---

## 7. Delivery Stages

| Stage | Name | Target Weekend |
|---|---|---|
| 1 | Local Lakehouse | May 31, 2026 |
| 2 | Streaming Ingestion | June 28, 2026 |
| 3 | Platform Simulation (Kubernetes) | July 26, 2026 |

---

## 8. Stakeholders

| Role | Name |
|---|---|
| Developer | Sriram Sivaraman |
| Reviewer / Audience | Hiring managers, engineering interviewers |

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Trino + MinIO connector configuration complexity | High | High | Spike on Trino config in Stage 1 Weekend 1 |
| Weekend availability disrupted | Medium | Medium | Buffer of 1 extra weekend per stage |
| Redpanda local resource usage too high | Medium | Medium | Use `--smp 1 --memory 1G` (already configured) |
| Scope creep on UI features | Medium | Low | Strict scope: browser + SQL editor + feature form only |

---

## 10. Definition of Done (Project Level)

The project is complete when:
1. A fresh `docker compose up` brings the full stack online
2. The bootstrap script seeds data end-to-end into the lake
3. A Trino SQL query returns results in the UI
4. At least one feature definition is stored and previewable
5. Kubernetes manifests deploy all services successfully in a local cluster
