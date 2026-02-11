#!/bin/bash
set -e

python3 manage.py wait_for_db

python3 manage.py migrate

python3 manage.py collectstatic --no-input --clear

GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-300}"

# gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300
gunicorn app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$GUNICORN_WORKERS" \
  --threads "$GUNICORN_THREADS" \
  --worker-class sync \
  --timeout "$GUNICORN_TIMEOUT" \