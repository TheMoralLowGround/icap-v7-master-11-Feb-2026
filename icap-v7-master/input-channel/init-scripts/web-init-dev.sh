#!/bin/bash
set -e

AUTO_MIGRATE="${AUTO_MIGRATE}"

python3 manage.py wait_for_db

if [ "$AUTO_MIGRATE" == "" ] || [ "$AUTO_MIGRATE" == 1 ]; then
  python3 manage.py migrate
fi

python3 manage.py runserver 0.0.0.0:8000