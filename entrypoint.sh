#!/bin/sh
set -e

# Run Alembic migrations if config is present
if [ -f /app/alembic.ini ] && [ -d /app/migrations ]; then
  echo "[entrypoint] Running database migrations..."
  alembic upgrade head
  echo "[entrypoint] Database migrations complete."
else
  echo "[entrypoint] Alembic files not found; skipping migrations."
fi

# Execute the given command (e.g., uvicorn)
exec "$@"
