"""
Django command to wait for database to be available.
"""
import os
import time

from django.core.management.base import BaseCommand

import redis

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


class Command(BaseCommand):
    """Django command to wait for redis."""

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for redis...")
        redis_up = False
        while redis_up is False:
            try:
                redis_instance = redis.Redis(
                    host=REDIS_HOST, port=REDIS_PORT, db=0, client_name="input_channel_wait"
                )
                redis_instance.get("TEST")
                redis_up = True
            except:
                self.stdout.write("redis unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("redis available!"))
