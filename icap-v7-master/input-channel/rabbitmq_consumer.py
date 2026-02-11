import json
import os
import time
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()


from core.utils.process_oauth import process_outlook
from core.utils.process_basic_auth import process_basic_auth
from core.utils.process_sharepoint import process_sharepoint
from core.utils.process_onedrive import process_onedrive
from core.utils.utils import update_status


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)


def ack_message(ch, delivery_tag):
    """Acknowledge message to confirm successful processing"""
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        print("Channel is already closed, so we can't ACK this message")


def do_work(ch, method, properties, body):
    """"Process the job based on message type"""
    message_type = properties.content_type
    data = json.loads(body)

    if message_type == "process_outlook":
        process_outlook(data)
    elif message_type == "process_basic_auth":
        process_basic_auth(data)
    elif message_type == "process_sharepoint":
        process_sharepoint(data)
    elif message_type == "process_onedrive":
        process_onedrive(data)
    elif message_type == "input_process_started":
        update_status(data)

    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def callback(ch, method, properties, body):
    """Handle incoming messages"""
    t = Thread(target=do_work, args=(ch, method, properties, body))
    t.start()


def main():
    """Setup Rabbitmq connection and start consuming"""

    props = {"connection_name": "input_channel_consumer"}
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        client_properties=props,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='to_pipeline', durable=True)
    channel.queue_declare(queue="to_input_channel", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_input_channel", on_message_callback=callback)

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
