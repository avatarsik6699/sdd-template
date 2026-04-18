#!/bin/sh
set -e

echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting Uvicorn..."
# exec replaces the shell process with uvicorn so it becomes PID 1 and receives SIGTERM directly → graceful shutdown
if [ "${APP_ENV}" = "development" ]; then
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
