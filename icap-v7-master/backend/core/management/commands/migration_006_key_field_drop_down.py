import copy

from core.models import Definition
from dashboard.models import Project
from dashboard.serializers import ProjectSerializer

from django.db import transaction
from django.core.management.base import BaseCommand
from django.conf import settings


DEFINITION_VERSIONS = settings.DEFINITION_VERSIONS


def get_Key_options_for_rules(project_name):
    hash_map = {}

    qs = Project.objects.filter(name=project_name)

    if qs.exists():
        project = qs.first()
        serialize_data = ProjectSerializer(project).data

        definition_settings = serialize_data["definition_settings"]
    else:
        return hash_map

    options_key_items = definition_settings["options"]["options-keys"]["items"]
    key_qualifiers = definition_settings["keyQualifiers"]
    compound_keys = definition_settings["compoundKeys"]

    for options_key_item in options_key_items:
        if (
            options_key_item["qualifier"] != ""
            or options_key_item["compoundKeys"] != ""
        ):
            continue

        hash_map[options_key_item["keyValue"]] = {
            "fieldInfo": options_key_item,
            "parent": None,
        }

    for item in key_qualifiers:
        for option in item["options"]:
            hash_map[option["value"]] = {
                "fieldInfo": {
                    "keyValue": option["value"],
                    "keyLabel": option["label"],
                },
                "parent": item["name"],
            }

    for item in compound_keys:
        for keyItem in item["keyItems"]:
            hash_map[keyItem["keyValue"]] = {
                "fieldInfo": keyItem,
                "parent": item["name"],
            }

    return hash_map


def get_normalizer_item_field_value(old_field_value, key_options_for_rules):
    new_field_value = []

    for item in old_field_value.split("|"):
        field_value = key_options_for_rules.get(item, None)

        if field_value:
            new_field_value.append(key_options_for_rules[item])

    return new_field_value


def migrate_normalizer_items(definition_normalizer_items, key_options_for_rules):
    normalizer_items = []

    for normalizer_item in definition_normalizer_items:
        if (
            normalizer_item["type"] == "combineGoodsLines"
            and normalizer_item["inputs"]
            and isinstance(normalizer_item["inputs"]["basedOnColumns"], str)
            and isinstance(normalizer_item["inputs"]["combineOnColumns"], str)
        ):
            based_on_columns = get_normalizer_item_field_value(
                normalizer_item["inputs"]["basedOnColumns"], key_options_for_rules
            )

            combine_on_columns = get_normalizer_item_field_value(
                normalizer_item["inputs"]["combineOnColumns"], key_options_for_rules
            )

            if len(based_on_columns) and len(combine_on_columns):
                normalizer_item["inputs"]["basedOnColumns"] = based_on_columns
                normalizer_item["inputs"]["combineOnColumns"] = combine_on_columns

                normalizer_items.append(normalizer_item)
            continue

        normalizer_items.append(normalizer_item)

    return normalizer_items


def migrate_rule_items(definition_rule_items, key_options_for_rules):
    rule_items = []

    for rule_item in definition_rule_items:
        rules = []

        for rule in rule_item["rules"]:
            if rule["type"] not in [
                "copyValue",
                "parseFrom",
                "copyToColumn",
                "setValue",
            ]:
                rules.append(rule)

                continue

            field_name = "fieldName" if rule["type"] == "parseFrom" else "columnName"

            if rule["type"] == "copyValue":
                field_name = "value"
                old_field_value = rule["inputs"][field_name]

                if old_field_value.get(field_name, None):
                    old_field_value = old_field_value[field_name]
            else:
                old_field_value = rule["inputs"][field_name]

            if not isinstance(old_field_value, str):
                if isinstance(old_field_value, dict):
                    rules.append(rule)
                continue

            new_field_value = key_options_for_rules.get(old_field_value, None)

            if new_field_value:
                rule["inputs"][field_name] = new_field_value
                rules.append(rule)

        rule_item["rules"] = rules
        rule_items.append(rule_item)

    return rule_items


def migrate_definition_key_data(definition_key_data, key_options_for_rules):
    key_data = copy.deepcopy(definition_key_data)

    if len(key_data.keys()) == 0:
        return key_data

    if key_data.get("ruleItems"):
        key_data["ruleItems"] = migrate_rule_items(
            key_data["ruleItems"], key_options_for_rules
        )

    return key_data


def migrate_definition_table_data(definition_table_data, key_options_for_rules):
    table_data = copy.deepcopy(definition_table_data)

    if isinstance(table_data, list):
        if len(table_data):
            for table in table_data:
                if table["table_definition_data"].get("ruleItems"):
                    table["table_definition_data"]["ruleItems"] = migrate_rule_items(
                        table["table_definition_data"]["ruleItems"],
                        key_options_for_rules,
                    )

                if table["table_definition_data"].get("normalizerItems"):
                    table["table_definition_data"]["normalizerItems"] = (
                        migrate_normalizer_items(
                            table["table_definition_data"]["normalizerItems"],
                            key_options_for_rules,
                        )
                    )

    return table_data


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
                project_name = definition.definition_id.split("_")[-1]

                key_options_for_rules = get_Key_options_for_rules(project_name)

                if not key_options_for_rules:
                    self.stdout.write(
                        self.style.ERROR(f"Project not found: {project_name}")
                    )
                    continue

                definition_data = definition.data

                for definition_version in DEFINITION_VERSIONS:
                    print(definition_version)

                    table_data = definition_data[definition_version]["table"]
                    new_table_data = migrate_definition_table_data(
                        table_data, key_options_for_rules
                    )
                    definition_data[definition_version]["table"] = new_table_data

                    key_data = definition_data[definition_version]["key"]
                    new_key_data = migrate_definition_key_data(
                        key_data, key_options_for_rules
                    )
                    definition_data[definition_version]["key"] = new_key_data

                definition.data = definition_data
                definition.save()

        self.stdout.write(self.style.SUCCESS("Migration completed"))
