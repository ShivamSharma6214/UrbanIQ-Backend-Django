#!/bin/sh
echo "Applying migrations..."
python manage.py migrate --noinput || true
echo "Collecting static..."
python manage.py collectstatic --noinput || true
exec "$@"
