#!/bin/bash
set -e

AUTO_MIGRATE="${AUTO_MIGRATE}"

python3 manage.py check_env

python3 manage.py wait_for_db

if [ "$AUTO_MIGRATE" == 1 ]; then
  python3 manage.py migrate
fi

python3 manage.py wait_for_redis

python3 manage.py store_project_data

python3 manage.py wait_for_rabbitmq

# Start Django server
echo "Starting Django server..."
exec python3 manage.py runserver 0.0.0.0:8000 --noreload
