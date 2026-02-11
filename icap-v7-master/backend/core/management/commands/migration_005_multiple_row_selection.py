from core.models import Definition

from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings


DEFINITION_VERSIONS = settings.DEFINITION_VERSIONS


def migrate_definition_table_data(definition_table_data):
    if isinstance(definition_table_data, list):
        if len(definition_table_data):
            for table in definition_table_data:
                extended_user_selected_patterns = table["table_definition_data"][
                    "models"
                ].get("extendedUserSelectedPatterns", [])

                for index, extended_user_selected_pattern in enumerate(
                    extended_user_selected_patterns
                ):
                    hash_map = {}
                    sorted_extended_user_selected_pattern = []

                    for item in extended_user_selected_pattern:
                        key = item["pos"].split(",")[3]
                        hash_map[key] = item

                    for key in sorted(hash_map.keys(), key=int):
                        sorted_extended_user_selected_pattern.append(hash_map[key])

                    extended_user_selected_patterns[
                        index
                    ] = sorted_extended_user_selected_pattern

                table["table_definition_data"]["models"][
                    "extended_user_selected_patterns"
                ] = extended_user_selected_patterns

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
