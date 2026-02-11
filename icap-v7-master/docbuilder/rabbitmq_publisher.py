"""
Organization: AIDocbuilder Inc.
File: rabbitmq_publisher.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2023-11-08
 
Description:
    This script facilitate publishing messages to Rabbitmq queues.

 
Dependencies:
    - os, json, pika
 
Main Features:
    - Establish a connection to Rabbitmq.
    - Publish messages to specified queues with JSON.
"""
import json
import os

import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)

props = {"connection_name": "docbuilder_publisher"}
params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,
    port=RABBITMQ_PORT,
    client_properties=props,
    credentials=credentials,
)


def publish(method, queue_name, body):
    """Publishe a JSON serialized message to a specified Rabbitmq queue"""
    print("Message received to publish")
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(body),
        properties=pika.BasicProperties(
            method, delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )

    connection.close()
