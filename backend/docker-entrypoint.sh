#!/bin/sh
set -e

HOST="${DB_WAIT_HOST:-db}"
PORT="${DB_WAIT_PORT:-5432}"

if [ -n "$DATABASE_URL" ]; then
  echo "Waiting for database at ${HOST}:${PORT}..."
  ATTEMPTS=0
  MAX_ATTEMPTS=60
  until python -c "import socket; s = socket.create_connection(('${HOST}', ${PORT}), timeout=2); s.close()" 2>/dev/null; do
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
      echo "Database did not become available in time, aborting."
      exit 1
    fi
    sleep 1
  done
  echo "Database is up."

  echo "Running alembic upgrade head..."
  alembic upgrade head
fi

exec "$@"
