"""
AI Agent Service - RabbitMQ Consumer

Description:
    This script sets up a RabbitMQ consumer that listens to the ai-agent queue
    and processes messages using worker threads, handling timeouts and publishing responses.

Dependencies:
    - pika: RabbitMQ client
    - threading: Concurrent message processing
    - handler: Task handlers (awb_hawb_date_validator_task, awb_or_hawb_no_and_supplier_validator_task,
      sub_doc_class_selector_task, cdz_data_modification_task)

Main Features:
    - Establish connection to RabbitMQ with automatic reconnection
    - Process incoming messages concurrently using threading
    - Handle timeouts for long-running tasks
    - Publish error or success responses back to pipeline queue
"""

import os
import json
import time
from functools import partial
from threading import Thread

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker

from handler import (
    awb_hawb_date_validator_task,
    awb_or_hawb_no_and_supplier_validator_task,
    sub_doc_class_selector_task,
    cdz_data_modification_task,
    shipment_table_agent_task,
    dynamic_content_creation_agent_task,
    run_ai_agents,
)
from producer import publish
from utils.timeout_utils import func_timeout, FunctionTimedOut

WORKER_TIMEOUT_SECONDS = 300

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
    message_type = properties.content_type

    try:
        data = json.loads(body)
        
        if message_type == "ai_agent":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, run_ai_agents, args=(data,)
            )
        elif message_type == "awb_hawb_date_validator":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, awb_hawb_date_validator_task, args=(data,)
            )
        elif message_type == "awb_or_hawb_no_and_supplier_validator":
            func_timeout(
                WORKER_TIMEOUT_SECONDS,
                awb_or_hawb_no_and_supplier_validator_task,
                args=(data,),
            )
        elif message_type == "hbl_mbl":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, sub_doc_class_selector_task, args=(data,)
            )
        elif message_type == "data_modification":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, cdz_data_modification_task, args=(data,)
            )
        elif message_type == "shipment_table":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, shipment_table_agent_task, args=(data,)
            )
        elif message_type == "dynamic_content_creation":
            func_timeout(
                WORKER_TIMEOUT_SECONDS, dynamic_content_creation_agent_task, args=(data,)
            )
    except json.JSONDecodeError:
        print(f"Invalid JSON in message: {data}")
        # Still acknowledge to prevent message requeue
        delivery_tag = method.delivery_tag
        cb = partial(ack_message, ch, delivery_tag)
        if ch.connection.is_open:
            ch.connection.add_callback_threadsafe(cb)
        else:
            print("Connection is already closed, cannot acknowledge message")
        return
    except FunctionTimedOut:
        print("Process timed out for batch_id: ", data.get("batch_id", "unknown"))
        result = {
            "batch_id": data.get("batch_id", "unknown"),
            "transaction_id": data.get("transaction_id", ""),
            "error": "Process timed out.",
            "status_code": 400,
        }
        publish("ai_agent_response", "to_pipeline", result)

    except Exception as error:
        print("Process failed for batch_id: ", data.get("batch_id", "unknown"))
        result = {
            "batch_id": (
                data.get("batch_id", "unknown") if "data" in locals() else "unknown"
            ),
            "transaction_id": data.get("transaction_id", ""),
            "error": f"Process failed: {str(error)}",
            "status_code": 400,
        }
        publish("ai_agent_response", "to_pipeline", result)

    # Always acknowledge the message
    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    if ch.connection.is_open:
        ch.connection.add_callback_threadsafe(cb)
    else:
        print("Connection is already closed, cannot acknowledge message")


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

    channel.queue_declare(queue="to_ai_agent", durable=True)
    channel.queue_declare(queue="to_pipeline", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_ai_agent", on_message_callback=callback)

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
