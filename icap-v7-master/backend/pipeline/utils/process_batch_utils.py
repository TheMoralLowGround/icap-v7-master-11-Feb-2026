import sys
import os
import json
import traceback
import copy
import re
import random
import string

from django.conf import settings
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from utils.classification_utils import get_instance_classes
from utils.email_utils import send_failure_notification
from utils.utils import to_camel_case

from core.models import Batch, BatchStatus, EmailBatch, TrainBatch, Definition
from dashboard.models import Profile, Project
from core.serializers import DefinitionSerializer

channel_layer = get_channel_layer()

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
BATCH_ID_PREFIX = os.getenv("BATCH_ID_PREFIX", "")


def send_to_group(group, event_type, data):
    """
    Define a function to send a message to a specified group
    """
    async_to_sync(channel_layer.group_send)(group, {"type": event_type, "data": data})


def get_next_sequce_value(sequence_name):
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


def gerenate_job_id_for_batch(batch_id):
    # Generate unique job_id
    random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    job_id = f"aidb:job:{random_string}:{batch_id}"
    return job_id


def get_new_email_batch_id(training=False, manual=False):
    """Return new email batch ID"""
    date_part = timezone.now().date().strftime("%Y%m%d")
    sequence_name = f"emailbatch{date_part}"
    sequence_value = get_next_sequce_value(sequence_name)
    sequence_value = str(sequence_value).zfill(5)
    if training:
        if manual:
            batch_id = f"multi_{BATCH_ID_PREFIX}{date_part}.{sequence_value}"
        else:
            batch_id = f"{BATCH_ID_PREFIX}TN{date_part}.{sequence_value}"
    else:
        batch_id = f"{BATCH_ID_PREFIX}{date_part}.{sequence_value}"

    return batch_id


def get_new_batch_id(infix="B"):
    """Return new batch ID"""
    date_part = timezone.now().date().strftime("%Y%m%d")
    sequence_name = f"batch{date_part}"
    sequence_value = get_next_sequce_value(sequence_name)
    sequence_value = str(sequence_value).zfill(5)
    batch_id = f"{BATCH_ID_PREFIX}{infix}{date_part}.{sequence_value}"

    return batch_id


def write_batch_status(**kwargs):
    """
    Save status using BatchStatus model
    """
    BatchStatus.objects.create(**kwargs)


def write_batch_log(**kwargs):
    """
    Save Status for batch
    """
    write_batch_status(**kwargs)
    status = kwargs["status"]
    batch_id = kwargs["batch_id"]

    # Save latest status in memory and only process new status if its diffrent
    if cache.get(batch_id, "") != status:
        cache.set(batch_id, status, 60 * 5)

        # Save Status in DB
        Batch.objects.filter(id=batch_id).update(status=status)

        # Publish status to websocket channel
        data = {"batch_id": batch_id, "status": status}
        send_to_group(f"batch_status_tag_{batch_id}", "batch_status_tag", data)


def write_parent_batch_log(**kwargs):
    """
    Save Status for email and train batch
    """

    status = kwargs["status"]
    batch_id = kwargs["batch_id"]
    train_batch_log = kwargs.pop("train_batch_log", None)
    if train_batch_log is None:
        if TrainBatch.objects.filter(id=batch_id).exists():
            print("trainToBatchLink found")
            train_batch_log = True
        else:
            train_batch_log = False
    write_batch_status(**kwargs)

    # Save latest status in memory and only process new status if its diffrent
    if cache.get(batch_id, "") != status:
        cache.set(batch_id, status, 60 * 5)

        # Save Status in DB
        if train_batch_log:
            TrainBatch.objects.filter(id=batch_id).update(status=status)
            batch_status_tag = "train_batch_status_tag"
        else:
            EmailBatch.objects.filter(id=batch_id).update(status=status)
            batch_status_tag = "email_batch_status_tag"
        # Publish status to websocket channel
        data = {"batch_id": batch_id, "status": status}
        send_to_group(f"{batch_status_tag}_{batch_id}", batch_status_tag, data)


def write_failed_log(**kwargs):
    """Write failed log"""
    try:
        write_batch_log(**kwargs)
        _, _, parent_batch, _, *tail = get_instance_classes(kwargs["batch_id"])
        if not parent_batch:
            return
        if parent_batch.status == "failed":
            return
        # Send failure notification due to batch execution failed
        train_batch_log = kwargs.pop("train_batch_log", None)
        if train_batch_log is None:
            if EmailBatch.objects.filter(id=parent_batch.id).exists():
                send_failure_notification(parent_batch.id, kwargs["sub_message"])

        kwargs["batch_id"] = parent_batch.id
        if "sub_message" in kwargs:
            kwargs["sub_message"] = f"AIDB-107: {kwargs['sub_message']}"
        write_parent_batch_log(**kwargs)
        return
    except Exception:
        print(traceback.format_exc())


def prepare_parent_batch_path(parent_batch_id, sub_path="email-batches"):
    """prepare parent batch path when 'email-batches' as sub_path"""
    batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, parent_batch_id)
    if os.path.exists(batch_path):
        shutil.rmtree(batch_path)
    os.makedirs(batch_path)
    return batch_path


def get_ocr_engine_type(email_batch):
    ocr_engine_type = "internal"

    try:
        # Try to get OCR engine type from project settings
        profile = Profile.objects.get(name=email_batch.matched_profile_name)
        project = Project.objects.get(name=profile.project)
        other_settings = project.settings.get("otherSettings")
        ocr_engine_type = other_settings.get("ocr_settings", {}).get(
            "engine_type", "internal"
        )
    except Profile.DoesNotExist:
        pass

    return ocr_engine_type


def get_classifier_settings(email_batch):
    classifier_settings = {}

    try:
        # Try to get OCR engine type from project settings
        profile = Profile.objects.get(name=email_batch.matched_profile_name)
        project = Project.objects.get(name=profile.project)
        other_settings = project.settings.get("otherSettings")
        classifier_settings = other_settings.get("classifier_settings", {})
    except Profile.DoesNotExist:
        pass

    return classifier_settings


def get_extraction_payload(batch: Batch):
    try:
        profile = Profile.objects.get(name=batch.definition_id)
        project = Project.objects.get(name=profile.project)
    except (Profile.DoesNotExist, Project.DoesNotExist):
        return [], []

    project_settings = project.settings

    # Get project key labels
    project_keys = project_settings.get("options", {}).get("options-keys", {})
    project_key_items = project_keys.get("items", [])
    # project_key_labels = [i['keyLabel'] for i in project_key_items]

    # Get profile key labels
    profile_key_items = (
        profile.keys if profile.keys and isinstance(profile.keys, list) else []
    )
    profile_key_labels = {
        i["keyValue"]: {
            "process_prompt": i.get("process_prompt", {}),
            "precedence": i.get("precedence", []),
        }
        for i in profile_key_items
    }

    # Final profile kesy labels (which exist in project key labels)
    KEYS = [
        {
            **i,
            "prompt": i.get("project_prompt", {}),  # Project-level prompt
            "process_prompt": profile_key_labels[i["keyValue"]]["process_prompt"],  # Process-level prompt
            "precedence": profile_key_labels[i["keyValue"]]["precedence"],
        }
        for i in project_key_items
        if i["keyValue"] in profile_key_labels
    ]

    # Get mapped keys from project
    mapped_keys = project_settings.get("options", {}).get("options-mapped-keys", {})
    mapped_keys_items = mapped_keys.get("items", [])

    # Filter mapped keys
    MAPPED_KEYS = get_mapped_keys(KEYS, mapped_keys_items)

    return KEYS, MAPPED_KEYS


def get_mapped_keys(keys, mapped_keys_items):
    result = []

    for item in mapped_keys_items:
        # Look for a matching key
        matching_key = None
        for key in keys:
            if key["keyValue"] == item["keyValue"]:
                matching_key = key
                break

        # If we found a matching key, add the item with the type
        if matching_key:
            result.append({**item, "type": matching_key["type"]})

    return result


def trigger_manual_extraction(definition_data):
    """
    Determines if manual extraction is needed based on key or table definitions.
    Returns True if any key or table item has a type other than 'auto'.
    """
    if not len(definition_data):
        return False

    definition = definition_data[0]
    key_items = definition.get("key", {}).get("items", [])
    table_definition = definition.get("table", [])
    table_data, key_data = [], []
    has_any_manual_table_key = False
    is_table_model_manual = False
    if table_definition:
        for td in table_definition:
            is_table_model_manual = (
                td.get("table_definition_data", {}).get("models", {}).get("type", None)
                != "auto"
            )
            table_items = td.get("table_definition_data", {}).get("keyItems", [])
            table_data = [i.get("type") for i in table_items]
            has_any_manual_table_key = any([i != "auto" for i in table_data])
            if has_any_manual_table_key or is_table_model_manual:
                break
    key_data = [i.get("type") for i in key_items]
    return (
        any([i != "auto" for i in key_data])
        or has_any_manual_table_key
        or is_table_model_manual
    )


def extract_document_id(input_string):
    """
    Extracts the base format (M########.S######.##) from input string.
    Returns the first 3 dot-separated segments.

    Examples:
    "M20250807.S500005.02" -> "M20250807.S500005.02"
    "M20250807.S500005.02.001" -> "M20250807.S500005.02"
    "M20250807.S500005.02.002.001" -> "M20250807.S500005.02"
    """
    if not input_string:
        return ""

    parts = input_string.split(".")
    return ".".join(parts[:3])


def merge_data_json(auto_json, manual_json, definitions):
    """
    Merge auto-generated cells and keys into manual JSON structure.
    Preserves manual layout while appending new cells and key details from auto JSON.
    """
    auto_tables = []
    auto_keys = []

    def collect_auto_table_names(nodes):
        if definitions:
            definition_tables = definitions[0].get("table", [])
            for node in nodes:
                for doc in node.get("children", []):
                    if doc.get("type") == "table":
                        table_name = doc.get("table_name", None)
                        if table_name:
                            # If table name exists in definition table check if it has auto
                            if table_name in [
                                table.get("table_name") for table in definition_tables
                            ]:
                                for table in definition_tables:
                                    table_type = (
                                        table.get("table_definition_data", {})
                                        .get("models", {})
                                        .get("type", None)
                                    )
                                    if (
                                        doc.get("table_name") == table.get("table_name")
                                    ) and table_type == "auto":
                                        auto_tables.append(doc)
                                    else:
                                        # If table not auto drop all the rows
                                        auto_tables.append({**doc, "children": []})
                            else:
                                # Else add all auto tables
                                auto_tables.append(doc)
        else:
            for node in nodes:
                for doc in node.get("children", []):
                    if doc.get("type") == "table":
                        auto_tables.append(doc)

    def collect_auto_keys(node):
        if definitions:
            definition_key_items = definitions[0].get("key", {}).get("items", [])
            excluded_labels = {
                to_camel_case(item.get("keyLabel"))
                for item in definition_key_items
                if item.get("type")
                and item.get("type").lower() != "auto"
                and item.get("type").lower() != "prompt"
            }
            for doc in node:
                for key in doc.get("children", []):
                    if key.get("type") == "key":
                        key["children"] = [
                            item
                            for item in key["children"]
                            if item.get("label") not in excluded_labels
                        ]
                        auto_keys.append(key)
        else:
            for doc in node:
                for key in doc.get("children", []):
                    if key.get("type") == "key":
                        auto_keys.append(key)

    merged = copy.deepcopy(manual_json)

    collect_auto_table_names(auto_json["nodes"])
    collect_auto_keys(auto_json["nodes"])

    # Merge Tables
    for auto_table_detail in auto_tables:
        auto_table_doc_id = extract_document_id(auto_table_detail.get("id", ""))
        table_found = False
        for node in merged.get("nodes", []):
            node_doc_id = extract_document_id(node.get("id", ""))

            # If the document ID doesn’t match, skip and continue
            if auto_table_doc_id != node_doc_id:
                continue

            # Find existing table in the manual data
            for doc in node.get("children", []):
                if doc.get("type", None) == "table":
                    if auto_table_detail.get("table_name", None) == doc.get(
                        "table_name", None
                    ):
                        table_found = True
                        doc["children"].extend(auto_table_detail["children"])
            if not table_found:
                node["children"].append(auto_table_detail)

        # Update table index
        for node in merged.get("nodes", []):
            for doc_index, doc in enumerate(node.get("children", [])):
                if doc.get("type", None) == "table":
                    doc["table_id"] = doc_index

    # Merge Keys
    for auto_key in auto_keys:
        auto_key_doc_id = extract_document_id(auto_key.get("id", ""))

        for node in merged.get("nodes", []):
            node_doc_id = extract_document_id(node.get("id", ""))
            if auto_key_doc_id == node_doc_id:
                node["children"].append(auto_key)
    return merged


def update_ra_json_from_auto_extraction(data_json, ra_json):
    """
    Updates RA JSON with 'Vendor' and 'DocumentType' fields from auto-extracted data.
    Applies updates at both the root and node levels if available.
    """
    try:
        vendor = data_json.get("Vendor", None)
        doc_type = data_json.get("DocumentType", None)
        for node in ra_json.get("nodes"):
            if vendor:
                node["Vendor"] = vendor
            if doc_type:
                node["DocType"] = doc_type
        if vendor:
            ra_json["Vendor"] = vendor
        if doc_type:
            ra_json["DocType"] = doc_type
        return ra_json
    except:
        return ra_json


def fix_string_format(input_string):
    """
    Converts strings with spaces and numeric suffixes to properly formatted versions.

    Examples:
    - "B20250522.00047. 1" -> "B20250522.00047.01"
    - "B20250522.00047. 1. 01" -> "B20250522.00047.01.001"
    - "B20250522.00047. 1. 01. 01.001" -> "B20250522.00047.01.001.001.001"
    - "B20250522.00047. 01" -> "B20250522.00047.01"
    - "B20250522.00047. 01. 001" -> "B20250522.00047.01.001"
    - "B20250522.00047. 01. 001. 001.001" -> "B20250522.00047.01.001.001.001"
    - "B20250522.00047. 01. 1. 1.1" -> "B20250522.00047.01.001.001.001"
    - "B20250522.00047. 122. 1. 1.1" -> "B20250522.00047.122.001.001.001"

    Args:
        input_string (str): The input string to format

    Returns:
        str: The formatted string
    """
    try:
        parts = input_string.split(".")

        # Handle simple cases early
        if len(parts) <= 2:
            return input_string.replace(" ", "")

        # Process first two parts (just remove spaces)
        result = [parts[0].replace(" ", ""), parts[1].replace(" ", "")]

        # Process remaining parts with appropriate padding
        for i, part in enumerate(parts[2:], start=2):
            # Clean the part (remove spaces)
            clean_part = part.replace(" ", "")

            # Determine required padding based on position
            required_digits = 2 if i == 2 else 3

            # Apply padding if needed
            if len(clean_part) < required_digits:
                clean_part = clean_part.zfill(required_digits)

            result.append(clean_part)

        return ".".join(result)
    except Exception as e:
        print(f"Error in fix_string_format: {e}")
        return input_string


def fix_corrupted_unicode(text):
    """Fix text where null characters have corrupted Unicode sequences"""
    import re

    # Replace null character followed by 2 hex digits with proper Unicode
    # This handles the case where \u00XX became \u0000XX
    result = ""
    i = 0
    while i < len(text):
        if (
            i < len(text) - 2
            and text[i] == "\u0000"
            and re.match(r"[0-9a-fA-F]{2}", text[i + 1 : i + 3])
        ):
            # Convert to proper Unicode character
            hex_part = text[i + 1 : i + 3]
            unicode_char = chr(int(hex_part, 16))
            result += unicode_char
            i += 3
        else:
            result += text[i]
            i += 1

    return result


def parse_unicode_escapes(text):
    """Convert Unicode escape sequences to actual characters"""
    try:
        decoded = text.encode().decode("unicode_escape")
        decoded.replace("—", "–")
        decoded = fix_corrupted_unicode(text)
        return decoded
    except Exception as e:
        print(f"Error in parse_unicode_escapes: {e}")
        return text


def fix_id_auto_extraction(data_json):
    """
    Normalizes all table and key IDs in the auto-extracted JSON using fix_string_format.
    Applies formatting recursively to document, table, row, and key levels.
    """
    for node in data_json["nodes"]:
        for document in node["children"]:
            if document["type"] == "table":
                try:
                    document["id"] = fix_string_format(document["id"])
                    document["is_auto_extracted"] = True
                    for table in document["children"]:
                        table["id"] = fix_string_format(table["id"])
                        for row in table["children"]:
                            row["id"] = fix_string_format(row["id"])
                            row["label"] = to_camel_case(
                                row["label"], row.get("key_value")
                            )
                            row["v"] = parse_unicode_escapes(row["v"])

                            # if row.get("original_key_label"):
                            #     row["original_key_label"] = to_camel_case(row["original_key_label"])
                except:
                    pass
            if document["type"] == "key":
                try:
                    document["id"] = fix_string_format(document["id"])
                    for key in document["children"]:
                        key["id"] = fix_string_format(key["id"])
                        key["type"] = "key_detail"
                        key["is_auto_extracted"] = True
                        # Convert labels to camel case
                        key["label"] = to_camel_case(key["label"], key.get("key_value"))

                        # if key.get("original_key_label"):
                        #     key["original_key_label"] = to_camel_case(key["original_key_label"])

                        key["v"] = parse_unicode_escapes(key["v"])
                        for kc in key.get("children", []):
                            kc["type"] = "keyTextDetail"
                            kc["label"] = to_camel_case(
                                kc["label"], kc.get("key_value")
                            )
                            kc["v"] = parse_unicode_escapes(kc["v"])

                            # if kc.get("original_key_label"):
                            #     kc["original_key_label"] = to_camel_case(kc["original_key_label"])
                except:
                    pass
    return data_json


def normalize_merged_data(data_json, definitions):
    """Remove any key from auto extracted if the manual extraction key exists."""
    try:
        query_key_lists = definitions[0].get("key", {}).get("items", [])
        for key_item in query_key_lists:
            if (
                key_item.get("type", None) != "auto"
                and key_item.get("type", None) != "prompt"
            ):
                for doc in data_json.get("nodes", []):
                    for key in doc.get("children", []):
                        if key.get("type") == "key":
                            key_childrens = key.get("children", [])
                            key["children"] = [
                                key
                                for key in key_childrens
                                if key.get("label", None)
                                != key_item.get("keyLabel", None)
                            ]
        # table_key_items = (
        #     definitions[0]
        #     .get("table", [])[0]
        #     .get("table_definition_data", {})
        #     .get("keyItems", [])
        # )
        # for table_key_item in table_key_items:
        #     if table_key_item.get("type", None) != "auto":
        #         for doc in data_json.get("nodes", []):
        #             for table in doc.get("children", []):
        #                 if table.get("type") == "table":
        #                     for row in table.get("children", []):
        #                         row_childrens = row.get("children", [])
        #                         row["children"] = [
        #                             cell
        #                             for cell in row_childrens
        #                             if cell.get("label", None)
        #                             != table_key_item.get("keyLabel", None)
        #                         ]
    except:
        pass
    return data_json


def update_data_json_based_on_definition(
    batch_instance: Batch, definition_version: str, data_json: dict
):
    """This function is utilized for updating definition. For example: everytime the unique_id comes from auto extraction
    it is changed and rules won't get applied as it is based on that unique id so it maps the unique_id and applies the rules.
    """
    qs = Definition.objects.filter(
        definition_id__iexact=batch_instance.definition_id, vendor=batch_instance.vendor
    )
    definition_data = None
    try:
        if qs.exists():
            definition = qs.first()
            definition_data = definition.data
            for node in data_json["nodes"]:
                for document in node["children"]:
                    if document.get("type") == "key":
                        for key_node in document.get("children"):
                            try:
                                if key_node.get("is_auto_extracted"):
                                    key_items = definition_data[definition_version][
                                        "key"
                                    ]["items"]
                                    is_auto_key = key_node.get("label") not in [
                                        item.get("keyLabel")
                                        for item in key_items
                                        if item.get("type") == "auto"
                                    ]
                                    # If non auto from key then only proceed
                                    if is_auto_key:
                                        # Update rules Unique id if it maps from auto extraction
                                        for rule_item in definition_data[
                                            definition_version
                                        ]["key"]["ruleItems"]:
                                            if rule_item.get("id").startswith(
                                                key_node.get("label")
                                            ):
                                                key_node["unique_id"] = rule_item[
                                                    "keyId"
                                                ]
                                        for not_in_use_item in definition_data[
                                            definition_version
                                        ]["key"]["notInUseItems"]:
                                            if not_in_use_item.get(
                                                "nestedLabel"
                                            ).startswith(key_node.get("label")):
                                                key_node["unique_id"] = not_in_use_item[
                                                    "keyId"
                                                ]
                            except:
                                print(traceback.print_exc())
                                pass
        # for rule_item in definition_data[definition_version]["key"]["ruleItems"]:
        #     # Override the auto extraction unique_id set in rules for auto extracted value.
        #     try:
        #         label = rule_item.get("id")
        #         manual_key_items = [
        #             i
        #             for i in definition_data[definition_version]["key"]["items"]
        #             if label.startswith(i.get("keyLabel")) and i.get("type") != "auto"
        #         ]
        #         if manual_key_items:
        #             rule_item["keyId"] = manual_key_items[0].get("id")
        #     except:
        #         print(traceback.print_exc())
        # for not_in_use_item in definition_data[definition_version]["key"][
        #     "notInUseItems"
        # ]:
        #     # Override the auto extraction unique_id set in Not in use for auto extracted value.
        #     try:
        #         label = not_in_use_item.get("nestedLabel")
        #         manual_key_items = [
        #             i
        #             for i in definition_data[definition_version]["key"]["items"]
        #             if label.startswith(i.get("keyLabel")) and i.get("type") != "auto"
        #         ]
        #         if manual_key_items:
        #             not_in_use_item["keyId"] = manual_key_items[0].get("id")
        #     except:
        #         print(traceback.print_exc())
        # definition.data = definition_data
        # definition.save()
    except:
        print("Failed to update Definition from auto extraction data json")
    return data_json


def get_exception_data(
    batch_instance, document_id, definition_version=settings.DEFAULT_DEFINITION_VERSION
):
    exception_data = []

    for item in batch_instance.layout_ids:
        if document_id and item["document_id"] != document_id:
            continue

        qs = Definition.objects.filter(
            definition_id__iexact=batch_instance.definition_id,
            layout_id=item["layout_id"],
        )

        if not qs.exists():
            continue

        def_data = DefinitionSerializer(qs.first()).data

        if not (definition_version in def_data["data"].keys()):
            raise ValueError(f"Definition not found for version {definition_version}")

        # Filter definition version
        filtered_data = def_data["data"][definition_version]

        key_data = filtered_data.get("key", {})
        key_items = key_data.get("items", [])
        exception_list = []

        for key_item in key_items:
            type = key_item.get("type")
            if not type or not type == "prompt":
                continue

            exception_list.append(
                {
                    "type": "key",
                    "process_key": key_item.get("keyLabel", ""),
                    "definition_prompt": key_item.get("definition_prompt", ""),
                }
            )

        table_data = filtered_data.get("table", [])
        for table in table_data:
            definition_data = table["table_definition_data"]
            column_prompts = definition_data.get("columnPrompts", [])

            for column_prompt in column_prompts:
                type = column_prompt.get("type")
                if not type or not type == "prompt":
                    continue

                exception_list.append(
                    {
                        "type": "table",
                        "process_key": column_prompt.get("keyLabel", ""),
                        "definition_prompt": column_prompt.get("definition_prompt", {}),
                    }
                )

        exception_data.append(
            {
                "document_id": item["document_id"],
                "exception_list": exception_list,
            }
        )

    return exception_data
