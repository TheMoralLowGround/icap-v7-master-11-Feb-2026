#!/bin/bash
set -e

python3 manage.py wait_for_redis

python3 manage.py wait_for_rabbitmq

python3 rabbitmq_consumer.py
