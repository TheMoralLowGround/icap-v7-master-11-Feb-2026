import uuid
from core.models import Definition

from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings


DEFINITION_VERSIONS = settings.DEFINITION_VERSIONS


def get_default_table_data(table_id=0, table_name="Main Table"):
    default_table_data = {
        "table_id": table_id,
        "table_name": table_name,
        "table_unique_id": str(uuid.uuid4()),
        "table_definition_data": {
            "columns": [],
            "keyItems": [],
            "models": {},
            "normalizerItems": [],
            "ruleItems": [],
        },
    }

    return default_table_data


def migrate_definition_table_data(definition_table_data):
    if not isinstance(definition_table_data, list):
        updated_definition_table_data = [get_default_table_data()]

        if definition_table_data:
            updated_definition_table_data[0]["table_definition_data"] = {
                **definition_table_data
            }

            if not len(definition_table_data["models"]):
                updated_definition_table_data[0]["table_definition_data"]["models"] = {}

            else:
                updated_definition_table_data[0]["table_definition_data"][
                    "models"
                ] = definition_table_data["models"][0]

                for index, model in enumerate(definition_table_data["models"]):
                    if index == 0:
                        continue

                    new_table = get_default_table_data(index, f"Main_{index - 1}")

                    new_table["table_definition_data"]["models"] = model

                    updated_definition_table_data.append(new_table)

        return updated_definition_table_data

    return definition_table_data


class Command(BaseCommand):
    """Django command to stop excution if required env variables are not present"""

    def handle(self, *args, **options):
        self.stdout.write("Migration Initiated...")

        # If no error occurs during the transaction,
        # then only commit changes to DB.
        with transaction.atomic():
            definitions = Definition.objects.all()
            for definition in definitions:
                print(definition)
                definition_data = definition.data

                for definition_version in DEFINITION_VERSIONS:
                    print(definition_version)
                    table_data = definition_data[definition_version]["table"]
                    new_table_data = migrate_definition_table_data(table_data)
                    definition_data[definition_version]["table"] = new_table_data

                definition.data = definition_data
                definition.save()

        self.stdout.write(self.style.SUCCESS("Migration completed"))
