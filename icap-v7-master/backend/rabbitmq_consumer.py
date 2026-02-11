"""
Organization: AIDocbuilder Inc.
File: rabbitmq_consumer.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script sets up Rabbitmq consumer that listen to specific queue and processe messages 
    using worker threads, handling timeouts and publishing responses.
 
Dependencies:
    - os, time, json, pika, django
    - AMQPConnectionError, ConnectionClosedByBroker from pika.exceptions
    - partial from functools
    - Thread from threading
    - process_email_batch_p1, process_train_batch_p1, pre_classification_process_p1, process_classify_batch_p1,
      process_classify_batch_p2, test_batch_p1, test_batch_p2, test_batch_p3, test_batch_p3b, test_batch_p3c,
      test_batch_p4, test_batch_p5, test_batch_p6b, test_batch_p7, test_batch_p8, test_batch_p9,
      test_batch_p10, atm_process_p1, atm_process_p2, ignore_dense_pages_p2, process_train_batch_p2, process_email_batch_p2 from pipeline.views
    - process_pdfs_and_docs_p2, process_electronic_pdfs_p2 from pipeline.worker_tasks
 
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

# Setup django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()

from pipeline.views import (
    process_email_batch_p1,
    process_train_batch_p1,
    pre_classification_process_p1,
    process_classify_batch_p1,
    process_classify_batch_p2,
    test_batch_p1,
    test_batch_p2,
    test_batch_p3,
    test_batch_p3b,
    test_batch_p3c,
    test_batch_p4,
    test_batch_p5,
    test_batch_p6b,
    test_batch_p7,
    test_batch_p8,
    test_batch_p8c,
    test_batch_p9,
    test_batch_p10,
    atm_process_p1,
    atm_process_p2,
    test_batch_p2_batch_type,
    test_batch_p3_merge_data_json,
    process_dataset_batches,
    start_transaction_process,
    start_training_process,
    start_label_mapping_process,
    test_batch_p2_extraction_response,
    process_ai_agent_response,
    ignore_dense_pages_p2,
    process_train_batch_p2,
    process_email_batch_p2,
)

from pipeline.worker_tasks import (
    handle_ocr_completed,
    process_pdfs_and_docs_p2,
    process_electronic_pdfs_p2,
)

from utils.classification_utils import document_matching_p2, handle_ocr_mismatch

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

    if message_type == "batch_queued":
        test_batch_p1(data)
    elif message_type == "start_process_response":
        test_batch_p2(data)
    elif message_type == "post_extraction_process":
        test_batch_p2_batch_type(data)
    elif message_type == "process_table_keys_response":
        test_batch_p3(data)
    elif message_type == "merge_data_json_from_auto_extraction":
        test_batch_p3_merge_data_json(data)
    elif message_type == "excel_table_process_response":
        test_batch_p3b(data)
    elif message_type == "excel_table_keys_process_response":
        test_batch_p3c(data)
    elif message_type == "keyval_extractor_response":
        test_batch_p4(data)
    elif message_type == "post_processing_response":
        test_batch_p5(data)
    elif message_type == "email_batch_validation_released":
        test_batch_p6b(data)
    elif message_type == "output_json_response":
        test_batch_p7(data)
    elif message_type == "assembly_queued":
        test_batch_p8(data)
    elif message_type == "postprocess_output_json_response":
        test_batch_p8c(data)
    elif message_type == "api_call_queued":
        test_batch_p9(data)
    elif message_type == "doc_upload_queued":
        test_batch_p10(data)
    elif message_type == "email_batch_queued":
        process_email_batch_p1(data)
    elif message_type == "train_batch_queued":
        process_train_batch_p1(data)
    elif message_type == "pre_classification_process_queued":
        pre_classification_process_p1(data)
    elif message_type == "title_classification_response":
        document_matching_p2(data)
    elif message_type == "ocr_mismatch_response":
        handle_ocr_mismatch(data)
    elif message_type == "classify_batch_queued":
        process_classify_batch_p1(data)
    elif message_type == "continue_classification_process_queued":
        process_classify_batch_p2(data)
    elif message_type == "atm_process_queue":
        atm_process_p1(data)
    elif message_type == "atm_process_response":
        atm_process_p2(data)
    elif message_type == "create_batch_ocr_response":
        handle_ocr_completed(data)
    elif message_type == "process_dataset_batches":
        process_dataset_batches(data)
    elif message_type == "start_transaction_process":
        start_transaction_process(data)
    elif message_type == "start_training_process":
        start_training_process(data)
    elif message_type == "label_mapping":
        start_label_mapping_process(data)
    elif message_type == "extraction_response":
        test_batch_p2_extraction_response(data)
    elif message_type == "ai_agent_response":
        process_ai_agent_response(data)
    elif message_type == "ignore_dense_pages_response":
        ignore_dense_pages_p2(data)
    elif message_type == "process_train_batch_p2_queued":
        process_train_batch_p2(data)
    elif message_type == "process_email_batch_p2_queued":
        process_email_batch_p2(data)
    elif message_type == "pdf_categorization_response":
        process_pdfs_and_docs_p2(data)
    elif message_type == "electronic_pdf_response":
        process_electronic_pdfs_p2(data)

    delivery_tag = method.delivery_tag
    cb = partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)


def callback(ch, method, properties, body):
    """Handle incoming messages"""
    t = Thread(target=do_work, args=(ch, method, properties, body))
    t.start()


def main():
    """Setup Rabbitmq connection and start consuming"""

    props = {"connection_name": "backend_consumer"}
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
    channel.queue_declare(queue="to_ocr_engine", durable=True)
    channel.queue_declare(queue="to_input_channel", durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="to_pipeline", on_message_callback=callback)

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
