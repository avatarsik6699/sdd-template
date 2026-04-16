.PHONY: dev install migrate lint test

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
