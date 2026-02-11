"""
Organization: AIDocbuilder Inc.
File: rabbitmq_consumer.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2023-11-08
 
Description:
    This script sets up Rabbitmq consumer that listen to specific queue and processe messages 
    using worker threads, handling timeouts and publishing responses.

 
Dependencies:
    - os, time, josn, pika, redis, flask_app
    - AMQPConnectionError, ConnectionClosedByBroker from pika.exceptions
    - partial from functools
    - Thread from threading
    - publish from rabbitmq_publisher
    - FunctionTimedOut, func_timeout from timeout_utils
 
Main Features:
    - Establish a connection to Rabbitmq.
    - Processe incoming messages concurrently using threading.
    - Handle timeouts for long-running tasks.
    - Publish error or success response back to specified Rabbitmq queue.
"""
import json
import os
import time
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

import flask_app
from rabbitmq_publisher import publish
from timeout_utils import FunctionTimedOut, func_timeout

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
WORKER_TIMEOUT = float(os.getenv("WORKER_TIMEOUT"))  # in Minutes
WORKER_TIMEOUT_SECONDS = WORKER_TIMEOUT * 60  # Convert minutes to seconds

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)


def ack_message(ch, delivery_tag):
    """Acknowledge message to confirm successful processing"""
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        print("Channel is already closed, so we can't ACK this message")


def do_work(ch, method, properties, body):
    """Process the job based on message type"""
    message_type = properties.content_type
    data = json.loads(body)
    try:
        if message_type == "start_process":
            func_timeout(WORKER_TIMEOUT_SECONDS, flask_app.start_process, args=(data,))
        elif message_type == "atm_process":
            func_timeout(WORKER_TIMEOUT_SECONDS, flask_app.atm_process, args=(data,))

    except FunctionTimedOut:
        result = {
            "job_id": data["job_id"],
            "error": f"Process timed out after {WORKER_TIMEOUT} minutes.",
            "messages": [],
            "status_code": 400,
        }
        publish(f"{message_type}_response", "to_pipeline", result)

    except Exception as error:
        result = {
            "job_id": data["job_id"],
            "error": f"Process failed: {str(error)}",
            "messages": [],
            "status_code": 400,
        }
        publish(f"{message_type}_response", "to_pipeline", result)

    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def callback(ch, method, properties, body):
    """Handle incoming messages"""
    t = Thread(target=do_work, args=(ch, method, properties, body))
    t.start()


def main():
    """Setup Rabbitmq connection and start consuming"""
    props = {"connection_name": "docbuilder_consumer"}
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        client_properties=props,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue="to_pipeline", durable=True)
    channel.queue_declare(queue="to_docbuilder", durable=True)
    channel.queue_declare(queue="to_utility", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_docbuilder", on_message_callback=callback)

    print("Waiting for messages...")
    channel.start_consuming()


def wait_for_connection():
    """Trying to establish a connection to Rabbitmq"""
    print("Waiting for rabbitmq...")
    sleep_time = 5

    rabbit_up = False
    while rabbit_up is False:
        try:
            params = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
            )
            connection = pika.BlockingConnection(params)
            connection.close()
            rabbit_up = True
        except AMQPConnectionError:
            print(f"Rabbitmq unavailable, waiting {sleep_time} second...")
            time.sleep(sleep_time)

    print("Rabbitmq available!")


if __name__ == "__main__":
    while True:
        try:
            main()
        except ConnectionClosedByBroker:
            print("Connection closed by Broker")
            wait_for_connection()
