import json
import pika
import os


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
props = {'connection_name' : 'ocr_engine_publisher'}
params = pika.ConnectionParameters(
    host=RABBITMQ_HOST, 
    port=RABBITMQ_PORT, 
    client_properties=props,
    credentials=credentials,
)

def publish(method, queue_name, body):

    print("Message recived to publish")
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(body),
        properties=pika.BasicProperties(
            method,
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))

    connection.close()
