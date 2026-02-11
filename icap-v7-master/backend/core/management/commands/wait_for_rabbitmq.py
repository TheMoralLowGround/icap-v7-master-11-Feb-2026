"""
Django command to wait for database to be available.
"""
import os
import time

import pika
from django.core.management.base import BaseCommand
from pika.exceptions import AMQPConnectionError

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)


class Command(BaseCommand):
    """Django command to wait for rabbitmq."""

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for rabbitmq...")
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
                self.stdout.write("Rabbitmq unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Rabbitmq available!"))
