from django.core.management.base import BaseCommand
import pika
import os
import time
from pika.exceptions import AMQPConnectionError

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)

class Command(BaseCommand):
    help = 'Wait for RabbitMQ to be available'

    def handle(self, *args, **options):
        """Wait for RabbitMQ to be available"""
        self.stdout.write("Waiting for rabbitmq...")
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
                self.stdout.write(self.style.SUCCESS("Rabbitmq available!"))
            except AMQPConnectionError:
                self.stdout.write(f"Rabbitmq unavailable, waiting {sleep_time} second...")
                time.sleep(sleep_time)
