"""
Auto Extraction Service - RabbitMQ Consumer

Description:
    This script sets up a RabbitMQ consumer that listens to the extraction queue
    and processes messages using worker threads, handling timeouts and publishing responses.

Dependencies:
    - pika: RabbitMQ client
    - threading: Concurrent message processing
    - handler: Task handlers (extraction_task_handler)

Main Features:
    - Establish connection to RabbitMQ with automatic reconnection
    - Process incoming messages concurrently using threading
    - Handle timeouts for long-running tasks
    - Publish error or success responses back to pipeline queue
"""

import os
import json
import time
import sys
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

from handler import extraction_task_handler
from producer import publish

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import Config

credentials = pika.PlainCredentials(Config.RABBITMQ_USERNAME, Config.RABBITMQ_PASSWORD)


def ack_message(ch, delivery_tag):
    """Acknowledge message to confirm successful processing"""
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        print("Channel is already closed, so we can't ACK this message")


def do_work(ch, method, properties, body):
    message_type = properties.content_type

    try:
        data = json.loads(body)

        if message_type == "extraction":
            extraction_task_handler(body)
        else:
            print(f"Unknown message type: {message_type}")
        
    except json.JSONDecodeError:
        print(f"Invalid JSON in message: {body}")
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
        publish('extraction_response', 'to_pipeline', result)

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

    params = pika.ConnectionParameters(
        host=Config.RABBITMQ_HOST,
        port=Config.RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue="to_extraction", durable=True)
    channel.queue_declare(queue="to_pipeline", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_extraction", on_message_callback=callback)

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
    """Wait for RabbitMQ to be available"""
    sleep_time = 5

    rabbit_up = False
    while rabbit_up is False:
        try:
            params = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
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
