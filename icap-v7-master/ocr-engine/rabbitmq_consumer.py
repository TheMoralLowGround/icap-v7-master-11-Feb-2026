import pika
import json
import time
import os
import sys
from threading import Thread
from functools import partial
from pika.exceptions import ConnectionClosedByBroker, AMQPConnectionError
from timeout_utils import func_timeout, FunctionTimedOut

from app import ocrengine_api

from rabbitmq_publisher import publish

# Required to load robot modules from external scripts folder

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')
WORKER_TIMEOUT = float(os.getenv('WORKER_TIMEOUT')) # in Minutes
WORKER_TIMEOUT_SECONDS = WORKER_TIMEOUT * 60 # Convert minutes to seconds

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)


def ack_message(ch, delivery_tag):
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        print("Channel is already closed, so we can't ACK this message")


def do_work(ch, method, properties, body):
    """Process the job"""
    message_type = properties.content_type

    data = json.loads(body)
    try:
        if message_type == 'create_batch_ocr':
            func_timeout(WORKER_TIMEOUT_SECONDS, ocrengine_api.create_batch, args=(data,))

    except FunctionTimedOut:
        result = {
            "batch_id": data['batch_id'],
            "error": f"Process timed out after {WORKER_TIMEOUT} minutes.",
            "messages": [],
            "status_code": 400,
        }
        publish(f'{message_type}_response', 'to_pipeline', result)

    except Exception as error:
        result = {
            "batch_id": data['batch_id'],
            "error": f"Process failed: {str(error)}",
            "messages": [],
            "status_code": 400,
        }
        publish(f'{message_type}_response', 'to_pipeline', result)

    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def callback(ch, method, properties, body):
    t = Thread(target=do_work, args=(ch, method, properties, body))
    t.start()


def main():
    """Setup Rabbitmq connection and start consuming"""

    props = {'connection_name' : 'ocr_engine_consumer'}
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        client_properties=props,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue='to_pipeline', durable=True)
    channel.queue_declare(queue='to_docbuilder', durable=True)
    channel.queue_declare(queue='to_utility', durable=True)
    channel.queue_declare(queue='to_ocr_engine', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='to_ocr_engine', on_message_callback=callback)

    print("Waiting for messages...")
    channel.start_consuming()


def wait_for_connection():
    print('Waiting for rabbitmq...')
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
        except (AMQPConnectionError):
            print(f'Rabbitmq unavailable, waiting {sleep_time} second...')
            time.sleep(sleep_time)

    print('Rabbitmq available!')


if __name__ == '__main__':
    while True:
        try:
            main()
        except ConnectionClosedByBroker:
            print("Connection closed by Broker")
            wait_for_connection()
