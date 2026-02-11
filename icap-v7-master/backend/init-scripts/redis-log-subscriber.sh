#!/bin/bash
set -e

python3 manage.py wait_for_redis

python3 redis_log_subscriber.py
