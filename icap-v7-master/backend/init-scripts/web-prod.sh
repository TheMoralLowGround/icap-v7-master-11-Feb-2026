#!/bin/bash
set -e

AUTO_MIGRATE="${AUTO_MIGRATE}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-300}"

python3 manage.py check_env

python3 manage.py wait_for_db

if [ "$AUTO_MIGRATE" == "" ] || [ "$AUTO_MIGRATE" == 1 ]; then
  python3 manage.py migrate
fi

python3 manage.py collectstatic --no-input --clear

python3 manage.py wait_for_redis

python3 manage.py store_project_data

python3 manage.py wait_for_rabbitmq

gunicorn app.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$GUNICORN_WORKERS" \
  --threads "$GUNICORN_THREADS" \
  --worker-class sync \
  --timeout "$GUNICORN_TIMEOUT" \
