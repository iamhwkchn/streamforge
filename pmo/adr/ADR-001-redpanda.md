# ADR-001 — Event Streaming: Redpanda over Apache Kafka

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs an event streaming backbone to simulate real-world data ingestion. An upstream system publishes sales records as events, and the consumer reads those events to process and write to the lake. The streaming layer needs to be Kafka API-compatible so the code represents industry-standard patterns, but must run easily on a single laptop.

## Decision

Use **Redpanda** as the event broker.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| Apache Kafka + Zookeeper | Requires Zookeeper (extra service), heavier memory footprint, slower startup — too heavy for local dev |
| Apache Kafka (KRaft mode) | Better than Zookeeper mode but still significantly heavier than Redpanda for a single-node local setup |
| RabbitMQ | Not Kafka API-compatible; would require a different client library and doesn't simulate real data platform patterns |

## Consequences

**Benefits:**
- Kafka API-compatible — producer and consumer code uses the standard `kafka-python` or `confluent-kafka` client, exactly as in production
- Single binary, no Zookeeper dependency
- Runs on `--smp 1 --memory 1G`, fits comfortably on a laptop
- Ships with Redpanda Console UI on port 9644 for debugging

**Trade-offs:**
- Redpanda is not identical to Kafka internals — any Kafka-specific features (e.g., Kafka Streams) are not available
- Not suitable if the project later needs to demonstrate Kafka-specific ecosystem tooling (Kafka Connect, KSQL)
