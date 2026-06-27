COMPOSE := docker compose -f ops/docker/docker-compose.yml
DATASET := data/raw_datasets/online_retail_II.xlsx
DATASET_URL := https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip

.PHONY: check-docker data up down logs seed test ps clean

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

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

seed:
	cd scripts && poetry install && \
		poetry run python bootstrap_lake.py && \
		poetry run python init_trino.py

test:
	cd apps/api && python3 -m pytest tests/ -q
	cd apps/ingest && python3 -m pytest tests/ -q

ps:
	$(COMPOSE) ps

clean:
	$(COMPOSE) down -v
	rm -rf data/minio data/postgres data/trino-catalog
