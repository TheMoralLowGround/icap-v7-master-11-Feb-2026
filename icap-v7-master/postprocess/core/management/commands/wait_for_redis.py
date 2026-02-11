from django.core.management.base import BaseCommand
import redis
import os
import time

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

class Command(BaseCommand):
    help = 'Wait for Redis to be available'

    def handle(self, *args, **options):
        """Wait for Redis to be available"""
        self.stdout.write("Waiting for redis...")
        
        redis_available = False
        while not redis_available:
            try:
                redis_instance = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=0,
                    client_name="postprocess",
                )
                redis_instance.ping()
                redis_available = True
                self.stdout.write(self.style.SUCCESS("redis available!"))
            except redis.ConnectionError:
                self.stdout.write("Redis unavailable, waiting 1 second...")
                time.sleep(1)
