import datetime
import json
import os
import re
import traceback

import requests
from fuzzywuzzy import fuzz

from app.address_modules.address_custom import get_iso2
from app.address_modules.addresss_cleaner import clean_keyNode
from app.key_central.keychildren_appender import SKIP_LABELS, TO_BE_KEPT_INSIDE

RULES_API_URL = os.getenv("RULES_DOCKER_URL")


def cells_to_keys(cells):
    keys = list()
    for cell in cells:
        cell_dict = dict()
        cell_dict["label"] = cell.get("label")
        cell_dict["value"] = list()
        cell_dict["value"].append(cell.get("v"))
        keys.append(cell_dict)
    return keys


def check_for_placeholders(item_queries):
    """This function goes inside each query and sees if there is a placeholder present and then puts in the value
    after fetching form data json"""
    placeholder_present = False

    for query in item_queries:
        group = query.get("group")
        group_items = group.get("items")
        for group_item in group_items:
            group_item_data = group_item.get("data")
            value_type = group_item_data.get("valueType")
            if (value_type == "key") or (value_type == "column"):
                placeholder_present = True

    return placeholder_present


def get_decision(single_query_data, label):
    decision_item = dict()

    single_query_data = single_query_data.get("result")

    decision = "fail"

    if "." in label:
        key_label_split = label.split(".")
        key_label = key_label_split[0]
        child_name = key_label_split[1]
    else:
        key_label = label
    if single_query_data:
        # If multi row
        if len(single_query_data) > 1:
            decision = "incomplete"

        # If single row result
        elif len(single_query_data) == 1:
            single_row = single_query_data[0]
            decision = "pass"
            result_dict = single_row

            if decision == "pass":
                decision_item = {
                    "key_nested_label": label,
                    "motherLabel": key_label,
                    "result_dict": result_dict,
                }
    else:
        decision = "incomplete"

    return decision, decision_item


def run_table_lookup(lookup_item, cells, definition_version, messages):
    result_storage = list()
    lookup_result_labels = list()
    additional_keys = list()

    label = lookup_item.get("label")
    item_queries = lookup_item["queries"]

    for item_query in item_queries:
        if item_query.get("additionalKeys"):
            if item_query.get("additionalKeys").get("items"):
                additions = item_query.get("additionalKeys").get("items")
                for additional_key in additions:
                    additional_keys.append(additional_key)

        keys_to_remove = [key for key in item_query if key != "sql"]
        for key in keys_to_remove:
            del item_query[key]

        k_placeholder = re.findall(r"<K>.*?</K>'", item_query["sql"])
        if k_placeholder:
            value = re.sub(r"(=|LIKE)\s+'<K>", r"IN <C>", item_query["sql"])
            item_query["sql"] = value.replace("</K>'", "</C>")

    columns = cells_to_keys(cells)

    request_body = {
        "queries": item_queries,
        "definition_version": definition_version,
        "columns": columns,
    }

    response = requests.post(
        f"{RULES_API_URL}/api/run_lookup/", json=request_body
    ).json()

    response_detail = response.get("detail")

    all_query_result = response.get("query_results")

    if all_query_result:
        for single_query_data in all_query_result:
            table_name = single_query_data.get("source_table")
            decision, decision_item = get_decision(single_query_data, label)

            if decision == "pass":
                decision_item["source_table"] = table_name
                if additional_keys:
                    decision_item["additional_keys"] = additional_keys
                result_storage.append(decision_item)
            else:
                manual_query_error_message = {
                    "message": "Multiple/No rows found with table manual lookup query for {}".format(
                        label
                    ),
                    "code": 400,
                    "module": "Lookups",
                }
                messages.append(manual_query_error_message)

    for result in result_storage:
        result["decision_message"] = "single_row_found"
        lookup_result_labels.append(result["motherLabel"])
    return lookup_result_labels, result_storage


def label_converter(s, label, key_val_arr, source_table):
    """convert labels to output json format"""
    # print("s", s)
    if s.lower() == "template_id":
        return "TID"

    if s.lower() == "consignee_account":
        s = "consigneeaccountnumber"

    if s.lower() == "shipper_account":
        s = "shipperaccountnumber"

    if s.lower() == "dest_code":
        s = "destinationlocationcode"

    if (s.lower() == "code") and ("ebooking_inco_terms" in source_table.lower()):
        s = "incoterms"

    if (s.lower() == "location_code") and (
        "ebooking_origin_location" in source_table.lower()
    ):
        s = "origincountrycode"

    if (s.lower() == "location_code") and (
        "ebooking_dest_location" in source_table.lower()
    ):
        s = "destinationcountrycode"

    if s.lower() == "parties_deliveryagent":
        s = "deliveryagent"

    if s.lower() == "dest_agent":
        s = "deliveryagent"

    transformed = ""

    if len(s) == 3:
        transformed = s.upper()

    # USING KEYVALUE LIST FROM DEFINITION SETTINGS
    for val in key_val_arr:
        if s.lower() == val.lower():
            transformed = val

    try:
        # Removing key_node label from the string
        if transformed.lower().startswith(label.lower()) and (
            transformed.lower() != label.lower()
        ):
            full_text = re.compile(label, re.IGNORECASE)
            full_text = full_text.sub("", transformed)
            transformed = full_text[0].lower() + full_text[1:]
    except:
        pass

    if transformed == "fullAddress":
        transformed = "block"

    if transformed.lower() == "templateid":
        transformed = "TID"

    return transformed


def lookup_code_conversion(child_label, key_qualifiers):
    """Checks if column is of a lookup code type (References type) and converts and passes a flag"""
    check_tuples = ("PARTIES_", "NOTES_", "TIME_", "CUSTOMSENTRIES_", "SERVICE_")
    lookup_code_type = None
    if len(child_label) == 3:
        lookup_code_type = "references"
        child_label = child_label.upper()

    if child_label.startswith(check_tuples):
        lookup_code_type = child_label.split("_")[0]
        for setting in key_qualifiers:
            if setting["name"].lower() == lookup_code_type.lower():
                lookup_code_type = setting["name"]

        child_label = convert_lookup_code(
            child_label.split("_")[1], lookup_code_type, key_qualifiers
        )

    return lookup_code_type, child_label


def convert_lookup_code(child_label, settings_name, key_qualifiers):
    """Finds proper key for the qualifier from lookup codes in definition settings"""
    for setting in key_qualifiers:
        if setting["name"].lower() == settings_name.lower():
            options = setting["options"]
            for option in options:
                if child_label.lower() == option["value"].lower():
                    return option["value"]


def update_cells(cells, lookup_result, key_val_arr, key_qualifiers):
    updated_cells = cells.copy()
    result_dict = lookup_result.get("result_dict")
    label = lookup_result.get("key_nested_label")
    additional_key_nodes = lookup_result.get("additional_keys")
    # print("additional_key_nodes", additional_key_nodes)

    target_cell = None
    for cell in updated_cells:
        if cell["label"].lower() == label.lower():
            target_cell = cell
            break

    for child_label, child_value in result_dict.items():
        if child_value and child_label:
            # print("child_label", child_label)
            # print("child_value", child_value)
            v6_label_found = False
            original_child_label = child_label
            # Only if the value is present for child item
            if type(child_value) == str:
                if not child_value.strip():
                    continue
            if "_cw1_name" in child_label.lower():
                child_label = child_label.lower().replace("_cw1_name", "name")

            lookupcode_type, child_label = lookup_code_conversion(
                child_label, key_qualifiers
            )
            if not lookupcode_type:
                child_label = label_converter(
                    child_label, label, key_val_arr, lookup_result["source_table"]
                )

            if not child_label:
                child_label = original_child_label
                v6_label_found = False
            else:
                v6_label_found = True
            cell_found = False
            if v6_label_found:
                cell_idx = None
                for cell_idx, cell in enumerate(updated_cells):
                    if cell["label"].lower() == child_label.lower():
                        cell_found = True
                        cell["v"] = child_value
                        cell["lookup_generated"] = True

            # print("cell_found", cell_found)

            if not cell_found:
                if v6_label_found:
                    new_cell = {
                        "label": child_label,
                        "v": child_value,
                        "lookup_generated": True,
                        "pos": "",
                        "pageId": "",
                        "STATUS": "0",
                        "type": "cell",
                        "id": target_cell["id"] + "_lookup",
                    }
                    if lookupcode_type:
                        new_cell["qualifierParent"] = lookupcode_type
                    updated_cells.append(new_cell)
            # print("additional_key", additional_key_nodes)
            if additional_key_nodes:
                for extra in additional_key_nodes:
                    # print("extra", extra)
                    # print("child_label", child_label)
                    if extra["target_column"].lower() == child_label.lower():
                        cell_found = False
                        cell_idx = None
                        for cell_idx, cell in enumerate(updated_cells):
                            # print("cell_label", cell["label"])
                            # print("extra_target_key", extra["target_key"]["fieldInfo"]["keyValue"])
                            if (
                                cell["label"].lower()
                                == extra["target_key"]["fieldInfo"]["keyValue"].lower()
                            ):
                                cell_found = True
                                cell["v"] = child_value
                                cell["lookup_generated"] = True
                                break
                        if not cell_found:
                            # print("child_label_not_cell", child_label)
                            # print("extra_target_key", extra["target_key"]["fieldInfo"]["keyValue"])
                            new_cell = {
                                "label": extra["target_key"]["fieldInfo"]["keyValue"],
                                "v": child_value,
                                "lookup_generated": True,
                                "pos": "",
                                "pageId": "",
                                "STATUS": "0",
                                "type": "cell",
                                "id": target_cell["id"] + "_lookup",
                            }

                            lookupcode_type, new_cell["label"] = lookup_code_conversion(
                                new_cell["label"], key_qualifiers
                            )
                            if lookupcode_type:
                                new_cell["qualifierParent"] = lookupcode_type
                            updated_cells.append(new_cell)

    return updated_cells


def table_lookups_main(request_data, d_json, messages, master_dictionaries):
    print("Calling Table Lookups")
    table_lookup_version = "v6.0.24042025"
    address_keys = list()
    try:
        definition_settings = request_data.get("definition_settings")
        key_options_items = (
            definition_settings.get("options", {}).get("options-keys", {}).get("items")
        )
    except:
        pass

    key_qualifiers = definition_settings.get("keyQualifiers")

    # print("===========")
    key_val_arr = list()

    # lookupLables
    for item_settings_from_def in key_options_items:
        key_val_arr.append(item_settings_from_def.get("keyValue"))
        if item_settings_from_def["type"] == "addressBlock":
            address_keys.append(item_settings_from_def["keyValue"])

    MESSAGES = messages
    try:
        definitions = request_data["definitions"]
        if definitions != []:
            definitions = definitions[0]
        else:
            definitions = {}
    except:
        pass

    # Getting necessary flags
    use_cw1 = definitions.get("cw1")
    definition_version = request_data.get("definition_version")
    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass

    docs = d_json.get("nodes")
    batch_id = d_json.get("id")
    profile_name = definitions.get("definition_id")

    lookup_items = list()
    table_definitions = definitions.get("table", [])

    for table_definition in table_definitions:
        table_definition_id = table_definition.get("table_name")
        table_definition_data = table_definition.get("table_definition_data")

        lookup_items = table_definition_data.get("lookupItems")
        for lookup_item in lookup_items:

            for input_doc_idx, target_doc in enumerate(docs):
                # Figuring a way out here
                if test_document_trigger != None:
                    if test_document_trigger != target_doc["id"]:
                        continue
                nodes = target_doc["children"]

                for node in nodes:
                    if "table" in node["type"]:
                        rows = node["children"]
                        table_id = node["table_name"]
                        if table_definition_id == table_id:
                            for row_idx, row in enumerate(rows):
                                cells = row["children"]

                                lookup_result_labels, result_storage = run_table_lookup(
                                    lookup_item, cells, definition_version, messages
                                )
                                updated_cells = None

                                for cell in cells:
                                    label = cell.get("label")
                                    if cell.get("label") in lookup_result_labels:
                                        lookup_result = result_storage[
                                            lookup_result_labels.index(label)
                                        ]
                                        result_dict = lookup_result.get("result_dict")

                                        # Profile based conditional lookups 
                                        definition_settings = request_data["definition_settings"]
                                        conditional_lookups_profiles = definition_settings["profileSettings"].get(
                                            "conditional_lookups_profiles", []
                                        )
                                        for profile in conditional_lookups_profiles:
                                            if profile_name == profile["name"]:
                                                column_mapping = profile["column_mapping"]
                                                result_dict = lookup_result.get("result_dict")
                                                updated_dict = result_dict.copy()
                                                for new_key, existing_key in column_mapping.items():
                                                    if existing_key in result_dict:
                                                        updated_dict[new_key] = result_dict[existing_key]
                                                lookup_result["result_dict"] = updated_dict

                                        updated_cells = update_cells(
                                            cells,
                                            lookup_result,
                                            key_val_arr,
                                            key_qualifiers,
                                        )

                                if updated_cells:
                                    row["children"] = updated_cells

    return d_json, messages
