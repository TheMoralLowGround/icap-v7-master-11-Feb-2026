"""
Preprocess Service - RabbitMQ Consumer

Description:
    This script sets up a RabbitMQ consumer that listens to the preprocess queue
    and processes messages using worker threads, handling timeouts and publishing responses.

Dependencies:
    - pika: RabbitMQ client
    - threading: Concurrent message processing
    - app: Task handlers (ignore_dense_pages_task, categorize_pdfs_task, process_files_task)

Main Features:
    - Establish connection to RabbitMQ with automatic reconnection
    - Process incoming messages concurrently using threading
    - Handle timeouts for long-running tasks
    - Publish error or success responses back to pipeline queue
"""

import json
import time
import logging
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handler import ignore_dense_pages_task, categorize_pdfs_task, process_files_task
from producer import publish
from utils.timeout_utils import FunctionTimedOut
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

credentials = pika.PlainCredentials(Config.RABBITMQ_USERNAME, Config.RABBITMQ_PASSWORD)


def ack_message(ch, delivery_tag):
    """Acknowledge message to confirm successful processing"""
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        logger.warning("Channel is already closed, cannot ACK message")


def do_work(ch, method, properties, body):
    message_type = properties.content_type

    try:
        logger.info(f"Received message with type: {message_type}")
        data = json.loads(body)

        if message_type == "ignore_dense_pages":
            ignore_dense_pages_task(data)
        elif message_type == "categorize_pdfs":
            categorize_pdfs_task(data)
        elif message_type == "process_files":
            process_files_task(data)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in message: {body}")
        # Still acknowledge to prevent message requeue
        delivery_tag = method.delivery_tag
        cb = partial(ack_message, ch, delivery_tag)
        ch.connection.add_callback_threadsafe(cb)
        return
    except FunctionTimedOut:
        result = {
            "batch_id": data.get('batch_id', 'unknown'),
            "error": f"Process timed out after {Config.WORKER_TIMEOUT} minutes.",
            "status_code": 400,
        }
        logger.error(f"Task timed out: {message_type}")
        publish(f'{message_type}_response', 'to_pipeline', result)

    except Exception as error:
        result = {
            "batch_id": data.get('batch_id', 'unknown') if 'data' in locals() else 'unknown',
            "error": f"Process failed: {str(error)}",
            "status_code": 400,
        }
        logger.error(f"Task failed: {message_type} - {error}", exc_info=True)
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

    credentials = pika.PlainCredentials(Config.RABBITMQ_USERNAME, Config.RABBITMQ_PASSWORD)
    params = pika.ConnectionParameters(
        host=Config.RABBITMQ_HOST,
        port=Config.RABBITMQ_PORT,
        credentials=credentials,
    )
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=Config.QUEUE_TO_PREPROCESS, durable=True)
    channel.queue_declare(queue=Config.QUEUE_TO_PIPELINE, durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=Config.QUEUE_TO_PREPROCESS, on_message_callback=callback)

    logger.info(f"Waiting for messages...")
    try:
        channel.start_consuming()
    except pika.exceptions.ConnectionClosedByBroker:
        logger.error("Connection closed by Broker")
        raise
    except pika.exceptions.AMQPConnectionError:
        logger.error("AMQP Connection Error")
        raise
    except pika.exceptions.AMQPChannelError:
        logger.error("AMQP Channel Error")
        raise
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user")
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
    """Wait for RabbitMQ connection to be available"""
    logger.info("Waiting for RabbitMQ connection...")
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
            logger.warning(f"RabbitMQ unavailable, retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)

    logger.info("RabbitMQ connection established!")


if __name__ == "__main__":
    while True:
        try:
            main()
        except pika.exceptions.ConnectionClosedByBroker:
            logger.error("Connection closed by Broker, reconnecting...")
            wait_for_connection()
        except pika.exceptions.AMQPConnectionError:
            logger.error("AMQP Connection Error, reconnecting...")
            wait_for_connection()
        except pika.exceptions.AMQPChannelError:
            logger.error("AMQP Channel Error, reconnecting...")
            wait_for_connection()
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}, reconnecting...", exc_info=True)
            wait_for_connection()
