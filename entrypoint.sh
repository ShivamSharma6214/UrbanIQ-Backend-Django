#!/usr/bin/env bash
set -e

# Wait for DB to be ready (simple loop)
# Note: for robust setups consider using 'wait-for' scripts

echo "Running migrations..."
python manage.py migrate --noinput || true

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Execute the container command (gunicorn or celery)
exec "$@"
