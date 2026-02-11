#!/bin/bash
set -e

python3 wait-scripts/wait_for_redis.py

python3 wait-scripts/wait_for_rabbitmq.py

python3 rabbitmq/consumer.py