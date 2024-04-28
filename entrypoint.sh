#!/bin/sh
# entrypoint.sh

# Exit script in case of error
set -e

echo "Running Django migrations..."
poetry run python manage.py migrate

echo "Starting Gunicorn..."
exec poetry run gunicorn app.wsgi:application --bind 0.0.0.0:8000
