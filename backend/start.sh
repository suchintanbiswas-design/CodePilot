#!/bin/bash
set -e

echo "Starting database migration check..."

# Create versions directory if it doesn't exist
mkdir -p /app/alembic/versions

echo "Running database migrations (upgrade head)..."
alembic upgrade head

echo "Starting application server..."
exec "$@"
