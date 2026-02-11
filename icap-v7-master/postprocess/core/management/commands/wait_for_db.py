"""
Django command to wait for database to be available.
"""

import time

import psycopg2
from psycopg2 import sql
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database."""

    def _ensure_database_exists(self) -> None:
        """Create the target database if it does not exist yet."""
        db_settings = settings.DATABASES.get("default", {})
        target_db = db_settings.get("NAME")
        if not target_db:
            return

        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=db_settings.get("USER"),
                password=db_settings.get("PASSWORD"),
                host=db_settings.get("HOST"),
                port=db_settings.get("PORT"),
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s", (target_db,)
                )
                exists = cursor.fetchone()
                if not exists:
                    cursor.execute(
                        sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db))
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Created database '{target_db}'.")
                    )
        except psycopg2.OperationalError:
            # Database server is not ready yet.
            return
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def handle(self, *args, **options):
        """Entrypoint for command"""
        self.stdout.write("Waiting for database...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=["default"])
                db_up = True
            except OperationalError:
                self.stdout.write("Database unavailable, waiting 1 second...")
                self._ensure_database_exists()
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
