"""
Auto Extraction Service - RabbitMQ Producer

Description:
    This script facilitates publishing messages to RabbitMQ queues.
    Reuses a thread-local connection/channel to avoid per-message connection
    overhead (important when publishing from worker threads).

Dependencies:
    - pika: RabbitMQ client
    - json: Message serialization
    - utils.Config for centralized configuration

Main Features:
    - Reuse connection per thread to reduce latency when publishing
    - Reconnect automatically if connection is closed
    - Publish messages to specified queues with JSON format
"""

import json
import threading
import pika
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Config

credentials = pika.PlainCredentials(Config.RABBITMQ_USERNAME, Config.RABBITMQ_PASSWORD)
props = {"connection_name": "extraction_publisher"}
params = pika.ConnectionParameters(
    host=Config.RABBITMQ_HOST,
    port=Config.RABBITMQ_PORT,
    client_properties=props,
    credentials=credentials,
)

_thread_local = threading.local()


def _get_connection_and_channel():
    """Return thread-local connection and channel; create if missing or closed."""
    conn = getattr(_thread_local, "connection", None)
    ch = getattr(_thread_local, "channel", None)
    if conn is None or not getattr(conn, "is_open", False):
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        conn = pika.BlockingConnection(params)
        ch = conn.channel()
        _thread_local.connection = conn
        _thread_local.channel = ch
    elif ch is None or not getattr(ch, "is_open", False):
        ch = conn.channel()
        _thread_local.channel = ch
    return conn, ch


def publish(method, queue_name, body):
    """Publish a JSON serialized message to a Rabbitmq queue. Reuses connection per thread."""
    print("Message received to publish")
    for attempt in range(2):
        try:
            _connection, channel = _get_connection_and_channel()
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(body),
                properties=pika.BasicProperties(
                    content_type=method,
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,
                ),
            )
            return
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError,
            pika.exceptions.ConnectionClosedByBroker,
        ):
            _thread_local.connection = None
            _thread_local.channel = None
            if attempt == 1:
                raise
