.PHONY: dev install migrate lint test deploy deploy-logs deploy-ps

dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

install:
	uv sync --dev

migrate:
	uv run alembic upgrade head

lint:
	uv run ruff check . && uv run ruff format --check .

test:
	uv run pytest

# ── VPS deploy ─────────────────────────────────────────────────────────────
# Usage: make deploy VPS_USER=ubuntu VPS_HOST=1.2.3.4 PROJECT_DIR=/opt/my-project
VPS_USER    ?= deploy
VPS_HOST    ?= $(shell grep ^DOMAIN .env 2>/dev/null | cut -d= -f2)
PROJECT_DIR ?= /opt/$(shell basename $(CURDIR))

deploy:
	ssh $(VPS_USER)@$(VPS_HOST) \
	  "cd $(PROJECT_DIR) && \
	   git pull && \
	   docker compose -f docker-compose.yml -f docker-compose.prod.yml \
	     up -d --build --remove-orphans"

deploy-logs:
	ssh $(VPS_USER)@$(VPS_HOST) \
	  "cd $(PROJECT_DIR) && docker compose logs -f backend frontend nginx"

deploy-ps:
	ssh $(VPS_USER)@$(VPS_HOST) \
	  "cd $(PROJECT_DIR) && docker compose ps"
