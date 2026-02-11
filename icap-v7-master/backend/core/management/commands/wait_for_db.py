"""
Django command to wait for database to be available.
"""

import os
import time
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from django.conf import settings
from psycopg import OperationalError as psycopgError
import psycopg

PGBOUNCER_PORT = os.getenv("PGBOUNCER_PORT")
PGBOUNCER_HOST = os.getenv("PGBOUNCER_HOST")


class Command(BaseCommand):
    """Django command to wait for pgbouncer."""

    def check_pgbouncer(self):
        """Check if pgbouncer is available."""
        try:
            db_settings = settings.DATABASES["default"]
            conn = psycopg.connect(
                dbname=db_settings["NAME"],
                user=db_settings["USER"],
                password=db_settings.get("PASSWORD", ""),
                host=PGBOUNCER_HOST,
                port=PGBOUNCER_PORT,
            )
            conn.close()
            return True
        except (psycopgError, OperationalError) as e:
            self.stdout.write(f"PgBouncer connection error: {str(e)}")
            return False

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for pgbouncer...")

        while True:
            if self.check_pgbouncer():
                break
            self.stdout.write("PgBouncer unavailable, waiting...")
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS("PgBouncer is available!"))
