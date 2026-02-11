#!/bin/bash
set -e

python wait_for_rabbitmq.py

python rabbitmq_consumer.py
