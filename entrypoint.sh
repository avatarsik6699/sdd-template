#!/bin/sh
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Uvicorn..."
# exec заменяет текущий процесс shell на uvicorn. Это важно для корректного обрабатывания сигналов:
# Без exec: sh ловит SIGTERM (команда docker stop), но uvicorn может не получить его
# С exec: uvicorn становится PID 1, получает SIGTERM напрямую → graceful shutdown
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
