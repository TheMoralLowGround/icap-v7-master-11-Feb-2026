#!/bin/bash
set -e

python3 wait-scripts/wait_for_redis.py

python3 wait-scripts/wait_for_rabbitmq.py

# Start AI Agent worker
echo "Starting AI Agent worker..."
exec python3 rabbitmq/consumer.py