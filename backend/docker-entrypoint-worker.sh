#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! pg_isready -h postgres -p 5432 -U postgres; do
  sleep 1
done

echo "PostgreSQL started"

echo "Waiting for Redis..."
while ! redis-cli -h redis -p 6379 ping > /dev/null 2>&1; do
  sleep 1
done

echo "Redis started"

# Workers don't run migrations - only the backend service does
echo "Starting worker..."
exec "$@"
