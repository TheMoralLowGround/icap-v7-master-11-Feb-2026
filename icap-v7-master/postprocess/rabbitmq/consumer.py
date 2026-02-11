"""
Organization: AIDocbuilder Inc.
File: rabbitmq_consumer.py
Version: 6.0

Description:
    This script sets up Rabbitmq consumer that listen to specific queue and processe messages
    using worker threads, handling timeouts and publishing responses.

Dependencies:
    - os, time, josn, pika, django
    - AMQPConnectionError, ConnectionClosedByBroker from pika.exceptions
    - partial from functools
    - Thread from threading
    - process_email_batch, process_train_batch, pre_classification_process, process_classify_batch_p1,
      process_classify_batch_p2, test_batch_p1, test_batch_p2, test_batch_p3, test_batch_p3b, test_batch_p3c,
      test_batch_p4, test_batch_p5, test_batch_p6b, test_batch_p7, test_batch_p8, test_batch_p9,
      test_batch_p10, atm_process_p1, atm_process_p2 from pipeline.views

Main Features:
    - Establish a connection to Rabbitmq.
    - Processe incoming messages concurrently using threading.
    - Handle timeouts for long-running tasks.
    - Publish error or success response back to specified Rabbitmq queue.
"""

import os
import sys
import json
import time
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()

from rabbitmq.handler import handle_transform_message
from rabbitmq.producer import publish

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
    message_type = properties.content_type or "postprocess_output_json"
    try:
        data = json.loads(body)
        if message_type == "postprocess_output_json":
            handle_transform_message(body)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in message: {body}. Error: {e}")
        # Still acknowledge to prevent message requeue
        delivery_tag = method.delivery_tag
        cb = partial(ack_message, ch, delivery_tag)
        ch.connection.add_callback_threadsafe(cb)
        return
    except Exception as error:
        result = {
            "batch_id": data.get('batch_id', 'unknown') if 'data' in locals() else 'unknown',
            "error": f"Process failed: {str(error)}",
            "status_code": 400,
        }
        publish(f'{message_type}_response', 'to_pipeline', result)

    # Always acknowledge the message
    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def callback(ch, method, properties, body):
    """Handle incoming messages"""
    t = Thread(target=do_work, args=(ch, method, properties, body))
    t.start()


def main():
    """Main consumer function"""
    wait_for_connection()

    credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue="to_postprocess", durable=True)
    channel.queue_declare(queue="to_pipeline", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_postprocess", on_message_callback=callback)

    print("Waiting for messages...")
    try:
        channel.start_consuming()
    except pika.exceptions.ConnectionClosedByBroker:
        print("Connection closed by Broker")
        raise  # Re-raise to be caught by outer handler
    except pika.exceptions.AMQPConnectionError:
        print("AMQP Connection Error")
        raise  # Re-raise to be caught by outer handler
    except pika.exceptions.AMQPChannelError:
        print("AMQP Channel Error")
        raise  # Re-raise to be caught by outer handler
    except KeyboardInterrupt:
        print("Consumer stopped by user")
        try:
            connection.close()
        except:
            pass
    finally:
        try:
            connection.close()
        except:
            pass


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
        except pika.exceptions.ConnectionClosedByBroker:
            print("Connection closed by Broker, reconnecting...")
            wait_for_connection()
        except pika.exceptions.AMQPConnectionError:
            print("AMQP Connection Error, reconnecting...")
            wait_for_connection()
        except pika.exceptions.AMQPChannelError:
            print("AMQP Channel Error, reconnecting...")
            wait_for_connection()
        except KeyboardInterrupt:
            print("Consumer stopped by user")
            break
        except Exception as e:
            print(f"Unexpected error: {e}, reconnecting...")
            wait_for_connection()
