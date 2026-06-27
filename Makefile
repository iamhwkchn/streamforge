COMPOSE := docker compose -f ops/docker/docker-compose.yml
COMPOSE_ALL := $(COMPOSE) --profile ingest
DATASET := data/raw_datasets/online_retail_II.xlsx
DATASET_URL := https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip

.PHONY: check-docker data up ingest logs-ingest down logs seed test ps clean

check-docker:
	@docker info > /dev/null 2>&1 || { \
		echo "Docker daemon is not running. Start Docker Desktop and try again."; \
		exit 1; \
	}

data:
	@if [ -f "$(DATASET)" ]; then \
		echo "Dataset already present at $(DATASET)"; \
	else \
		echo "Downloading Online Retail II dataset from UCI..."; \
		mkdir -p data/raw_datasets; \
		curl -sSL "$(DATASET_URL)" -o /tmp/online_retail_ii.zip; \
		unzip -o /tmp/online_retail_ii.zip -d data/raw_datasets/; \
		rm -f /tmp/online_retail_ii.zip; \
		echo "Dataset ready at $(DATASET)"; \
	fi

up: check-docker data
	$(COMPOSE) up -d --build

ingest: check-docker data
	$(COMPOSE_ALL) up -d --build producer consumer
	@echo "Ingestion started. Track it with:"
	@echo "  make logs-ingest          # producer/consumer logs"
	@echo "  http://localhost:3000     # Datasets -> retail_events (refresh to see counts climb)"
	@echo "  http://localhost:8082     # Redpanda Console -> Topics -> retail.events"

logs-ingest:
	$(COMPOSE_ALL) logs -f producer consumer

down:
	$(COMPOSE_ALL) down

logs:
	$(COMPOSE_ALL) logs -f

seed:
	cd scripts && poetry install && \
		poetry run python bootstrap_lake.py && \
		poetry run python init_trino.py

test:
	cd apps/api && python3 -m pytest tests/ -q
	cd apps/ingest && python3 -m pytest tests/ -q

ps:
	$(COMPOSE_ALL) ps

clean:
	$(COMPOSE_ALL) down -v
	rm -rf data/minio data/postgres data/trino-catalog
