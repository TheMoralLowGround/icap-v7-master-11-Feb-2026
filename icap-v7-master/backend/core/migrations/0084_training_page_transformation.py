# Generated manually on 27-07-24

from django.db import migrations
from django.db import transaction
from django.db import connection
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


def training_page_transformation(apps, schema_editor):
    TrainBatch = apps.get_model("core", "TrainBatch")
    TrainToBatchLink = apps.get_model("core", "TrainToBatchLink")
    Batch = apps.get_model("core", "Batch")

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


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0083_trainbatch_traintobatchlink_trainparseddocument"),
    ]

    operations = [
        # Handle DB record changes
        migrations.RunPython(
            training_page_transformation,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
