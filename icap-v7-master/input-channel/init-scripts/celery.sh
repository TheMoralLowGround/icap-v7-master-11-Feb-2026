#!/bin/bash
set -e

python3 manage.py wait_for_redis

python3 manage.py wait_for_rabbitmq 

celery -A app worker -l INFO --concurrency=4 -Q input_channel_queue,outlook_queue,basic_email_queue,sharepoint_queue,onedrive_queue
