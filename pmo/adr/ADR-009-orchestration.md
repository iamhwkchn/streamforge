# ADR-009 — Orchestration: Docker Compose (primary) + Kubernetes (secondary)

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge runs six services (Redpanda, MinIO, Postgres, Trino, FastAPI, SvelteKit). These services need to start reliably, share a network, and have persistent storage for stateful components. The project must also demonstrate platform engineering knowledge beyond simple local development.

## Decision

Use **Docker Compose** as the primary local orchestration method, with **Kubernetes manifests** as a secondary deployment mode (Stage 3).

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Docker Compose only | Simple and sufficient for development, but does not demonstrate container orchestration knowledge expected of a senior data engineer |
| Kubernetes only | Too complex for daily development iteration — slow feedback loop, harder to debug locally |
| Helm Charts | Adds abstraction on top of Kubernetes; appropriate for packaging, but adds complexity without benefit for a demo project |
| Nomad | Less industry-standard than Kubernetes for data platform deployments |
| Bare Docker (no Compose) | Requires manually managing networks, volumes, and startup order — high friction for daily dev |

## Consequences

**Docker Compose (Primary):**
- Single `docker compose up` starts the full stack
- Named volumes provide persistence for Postgres, MinIO, and Redpanda across restarts
- `docker-entrypoint-initdb.d` auto-runs Postgres seed scripts on first boot
- Port mappings expose services to localhost for local development and debugging

**Kubernetes (Secondary — Stage 3):**
- StatefulSets + PVCs for Postgres, MinIO, Redpanda — mirrors production deployment patterns
- Deployments for Trino, FastAPI, SvelteKit — stateless, horizontally scalable
- ClusterIP Services for internal communication between pods
- Demonstrates understanding of stateful vs stateless workload distinctions, PVC lifecycle, and service abstraction

**Trade-offs:**
- Maintaining two deployment modes adds documentation and testing overhead
- Kubernetes manifests will need to be kept in sync with Docker Compose service definitions as the stack evolves
- Local Kubernetes (kind or minikube) requires additional tooling installation compared to Docker Compose
