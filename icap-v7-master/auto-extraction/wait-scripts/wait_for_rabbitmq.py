import time
import pika
import os
from pika.exceptions import AMQPConnectionError


RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_PORT = os.getenv('RABBITMQ_PORT')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD')

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
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
