from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from core.models import TrainBatch, Batch, TrainToBatchLink
from django.db import transaction
from django.utils import timezone


def get_next_sequence_value(sequence_name):
    """
    This is postgres specific function to create a sequence in DB if not exist,
    and fetch the next sequence value
    """
    with connection.cursor() as cursor:
        query = f"""CREATE SEQUENCE IF NOT EXISTS {sequence_name}"""
        cursor.execute(query)
        query = f"""SELECT nextval('{sequence_name}')"""
        cursor.execute(query)
        result = cursor.fetchone()
        return result[0]


def get_new_batch_id():
    date_part = timezone.now().date().strftime("%Y%m%d")
    sequence_name = f"trainbatch{date_part}"
    sequence_value = get_next_sequence_value(sequence_name)
    sequence_value = str(sequence_value).zfill(5)
    batch_id = f"{date_part}.E{sequence_value}"
    return batch_id


class Command(BaseCommand):
    """Converts old training batches to new a new TrainBatch"""

    def handle(self, *args, **kwargs):
        self.stdout.write("Migration Initiated...")
        # If no error occurs during the transaction,
        # then only commit changes to DB.
        with transaction.atomic():
            TrainBatch.objects.filter(id__icontains="E").delete()

            # need to create a TrainBatch and then link to batch
            batches = (
                Batch.objects.filter(mode="training")
                .order_by("created_at")
                .values_list("id", "definition_id")
            )

            for batch_id, definition_id in batches:
                train_batch_qs = TrainBatch.objects.filter(
                    matched_profile_name=f"{definition_id}__OLD"
                )

                if train_batch_qs.exists():
                    train_batch = train_batch_qs.first()
                else:
                    train_batch = TrainBatch.objects.create(
                        id=get_new_batch_id(),
                        matched_profile_name=f"{definition_id}__OLD",
                    )

                TrainToBatchLink.objects.create(
                    train_batch=train_batch, batch_id=batch_id, mode="training"
                )
        self.stdout.write(self.style.SUCCESS("Migration completed"))
