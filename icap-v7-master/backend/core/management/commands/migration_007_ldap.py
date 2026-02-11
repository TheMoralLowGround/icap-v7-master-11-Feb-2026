from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    """Drops the django_admin_log and knox_authtoken tables and their migration records from the database."""

    def handle(self, *args, **kwargs):
        # Drop tables
        tables_to_delete = ["django_admin_log", "knox_authtoken"]

        with connection.cursor() as cursor:
            for table in tables_to_delete:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully dropped the {table} table.")
                )

        # Delete migration records
        MigrationRecorder.Migration.objects.filter(app="knox").delete()
        MigrationRecorder.Migration.objects.filter(app="admin").delete()

        self.stdout.write(
            self.style.SUCCESS("Successfully deleted admin and knox migration records.")
        )
