from django.conf import settings
from django.db import migrations

# Populate Data for Defualt definition version & draft version
DEFAULT_DEFINITION_VERSION = settings.DEFAULT_DEFINITION_VERSION


def restructure_definition(apps, schema_editor):
    Definition = apps.get_model("core", "Definition")

    definitions = Definition.objects.all().iterator()
    for definition in definitions:
        data = definition.data
        data[DEFAULT_DEFINITION_VERSION]["table"] = definition.table
        data[DEFAULT_DEFINITION_VERSION]["key"] = definition.key

        data["draft"]["table"] = definition.draft_table
        data["draft"]["key"] = definition.draft_key

        definition.data = data
        definition.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0039_definition_data"),
    ]

    operations = [
        # Handle DB record changes
        migrations.RunPython(restructure_definition),
    ]
