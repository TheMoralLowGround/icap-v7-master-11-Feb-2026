"""
Definitions Extractor API
==========================

Overview:
---------
This Flask-based API extracts structured information from a provided JSON payload. 
The information is categorized into various fields such as regular fields, goods lines, 
and address blocks based on predefined definitions and key qualifiers.

Endpoints:
----------
1. `/definitions_extractor` (POST)
   - Input: JSON payload containing batch ID, document nodes, and definition settings.
   - Output: JSON structure with categorized fields.

Key Components:
---------------
1. **Helper Functions**:
   - `key_qualifier_Check`: Matches the `keyLabel` or `colLabel` of an input item with predefined key qualifiers.
   - `get_address_detail_keys`: Extracts child labels for an address block based on a parent key's label.
   - `get_type`: Identifies the type of a given label (e.g., key, table, address block) using the key options.

2. **Definition Settings**:
   - `keyQualifiers`: Predefined rules for matching input keys to specific field categories.
   - `options-keys`: Configuration for determining the type of a key or column.

3. **Extraction Logic**:
   - Processes nodes from the input JSON.
   - Categorizes labels into:
     - `goodsLines`: Table-related fields.
     - `regularFields`: Standard key-value fields.
     - Address blocks and their details.
   - Handles partial address blocks and nested keys.

Error Handling:
---------------
- Validates the presence of required fields (`definition_settings`, `keyQualifiers`, `options-keys`).
- Returns meaningful error messages in case of missing or invalid data.

Execution Flow:
---------------
1. Parse and validate the input JSON payload.
2. Extract and process `keyQualifiers` and `options-keys` from the definition settings.
3. Traverse document nodes to identify and categorize fields:
   - Keys: Extracted from nodes of type `key`.
   - Table Columns: Extracted from nodes of type `table`.
4. Use helper functions to:
   - Map keys to their types and qualifiers.
   - Extract address details for address blocks.
   - Categorize fields based on predefined rules.
5. Construct and return the output JSON.

Input Example:
--------------
```json
{
    "id": "batch123",
    "definition_settings": {
        "keyQualifiers": [
            {
                "name": "exampleKey",
                "options": [
                    {"value": "exampleValue1"},
                    {"value": "exampleValue2"}
                ]
            }
        ],
        "options": {
            "options-keys": {
                "items": [
                    {"keyValue": "exampleKey", "type": "key"},
                    {"keyValue": "exampleTable", "type": "table"}
                ]
            }
        }
    },
    "data_json": {
        "nodes": [
            {
                "type": "document",
                "children": [
                    {
                        "type": "key",
                        "children": [
                            {"label": "exampleKeyLabel", "children": []}
                        ]
                    },
                    {
                        "type": "table",
                        "children": [
                            {
                                "type": "row",
                                "children": [{"label": "exampleTableLabel"}]
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
"""


import re
import traceback

from flask import jsonify, request

from app.response_formator import populate_error_response


def key_qualifier_Check(input_item, key_qualifiers_input):
    for setting in key_qualifiers_input:
        name = setting["name"]
        if "keyLabel" in input_item.keys():
            label = input_item["keyLabel"]
        if "colLabel" in input_item.keys():
            label = input_item["colLabel"]
        if label == name:
            options = setting["options"]
            for option in options:
                if input_item["qualifierValue"] == option["value"]:
                    return option["value"]
    if "keyLabel" in input_item.keys():
        return input_item["keyLabel"]
    elif "colLabel" in input_item.keys():
        return input_item["colLabel"]


def get_address_detail_keys(input_label, data_json):
    output = list()
    documents = data_json["nodes"]
    document = documents[0]
    children = document["children"]
    if not children:
        for x in documents:
            if x["children"]:
                children = x["children"]
    for item in children:
        if item["type"] == "key":
            key_value_items = item["children"]
            for key_value_item in key_value_items:
                label = key_value_item["label"]
                if input_label == label:
                    address_label_detail_children = key_value_item["children"]
                    for detail_label in address_label_detail_children:
                        output.append(detail_label["label"])
    return output


def get_type(input_item, key_options_items):
    if "keyLabel" in input_item.keys():
        label = input_item["keyLabel"]
    elif "colLabel" in input_item.keys():
        label = input_item["colLabel"]
    for item_settings_from_def in key_options_items:
        if label == item_settings_from_def["keyValue"]:
            return item_settings_from_def["type"]


def init(app):
    @app.route("/definitions_extractor", methods=["POST"])
    def definitions_extractor():
        try:
            """
            This function takes in data json and pakcs all the labels of the extracted fields and sends them in an
            agreed upon json structure, and returns it.
            """

            print("Running Definitions Extractor")
            # Definitions Extractor v5.023082022
            # @Emon updated bug that had duplicate address child in definitions address details on 23/08/2022
            # @Emon updated the script to only extract from the first document
            # @Emon updated the script to take in test document as well test batch
            output = dict()
            print("Processing Definitions")
            request_data = request.get_json()
            batch_id = request_data["id"]
            output["batchid"] = batch_id

            try:
                definition_settings = request_data.get("definition_settings")
            except:
                response = populate_error_response(
                    data={},
                    error="definition_settings not found",
                    traceback=traceback.print_exc(),
                )
                return jsonify(response), 400

            try:
                key_qualifiers = definition_settings.get("keyQualifiers")
            except:
                response = populate_error_response(
                    data={},
                    error="keyQualifiers not found",
                    traceback=traceback.print_exc(),
                )
                return jsonify(response), 400

            try:
                key_options_items = (
                    definition_settings.get("options", {})
                    .get("options-keys", {})
                    .get("items")
                )
            except:
                response = populate_error_response(
                    data={},
                    error="keyOptions Items not found",
                    traceback=traceback.print_exc(),
                )
                return jsonify(response), 400

            def lookup_function(input_label):
                for setting in key_qualifiers:
                    options = setting["options"]
                    for option in options:
                        # checking if the key exists in the option value
                        # print(label, '----', option["value"])
                        if input_label == option["value"]:
                            # print(label, '----', option["value"])
                            target_key_node_name = setting["name"]
                            return target_key_node_name
                return None

            d_json = request_data["data_json"]

            try:
                nodes = d_json["nodes"][0]["children"]
                if not nodes:
                    for x in d_json["nodes"]:
                        if x["children"]:
                            nodes = x["children"]

            except Exception as error:
                response = populate_error_response(
                    data=d_json, error=error, traceback=traceback.print_exc()
                )
                return jsonify(response), 400

            keys = list()
            table_data = None
            for node in nodes:
                if "table" in node["type"]:
                    table_data = node["children"]
                if "key" in node["type"]:
                    keys = node["children"]
            key_items = list()
            for key in keys:
                key_dict = dict()
                key_dict["keyLabel"] = key["label"]
                key_items.append(key_dict)

            # TABLE COLUMN NAME EXTRACTION CODE SNIPPED TO GO HERE
            table_column_list = list()
            if table_data:
                for row in table_data:
                    if row["children"] != []:
                        for cell in row["children"]:
                            cell_dict = dict()
                            cell_dict["colLabel"] = cell["label"]
                            if cell_dict not in table_column_list:
                                table_column_list.append(cell_dict)
            try:
                # processing labels of table columns
                for column in table_column_list:
                    label = column["colLabel"]
                    # checking for none labels
                    if (label in ["None", "notInUse", ""]) or (label[-1].isnumeric()):
                        continue

                    target_type = get_type(column, key_options_items)
                    # if table type it goes inside goodsLines
                    if target_type == "table":
                        if "goodsLines" in output.keys():
                            output["goodsLines"].append(label)
                        else:
                            output["goodsLines"] = [label]
                    # if keyType goes into regularFields
                    elif target_type == "key" or (not target_type):
                        if (not target_type) and lookup_function(label):
                            qualifier_name = lookup_function(label)
                            if qualifier_name in output.keys():
                                output[qualifier_name].append(label)
                            else:
                                output[qualifier_name] = [label]
                        else:
                            if "regularFields" in output.keys():
                                output["regularFields"].append(label)
                            else:
                                output["regularFields"] = [label]
            except:
                print(traceback.print_exc())
                pass
            try:
                # processing key items
                for item in key_items:
                    label = item["keyLabel"]
                    # checking for none labels
                    if (label in ["None", "notInUse", ""]) or (label[-1].isnumeric()):
                        continue
                    target_type = get_type(item, key_options_items)
                    # print(label , "------", target_type)
                    # if table type it goes inside goodsLines
                    if target_type == "table":
                        if "goodsLines" in output.keys():
                            output["goodsLines"].append(label)
                        else:
                            output["goodsLines"] = [label]

                    elif target_type == "addressBlock":
                        address_detail_keys = []
                        address_detail_keys = get_address_detail_keys(label, d_json)
                        tbr = ["block"]
                        address_detail_keys = [
                            x for x in address_detail_keys if x not in tbr
                        ]
                        if not label in output.keys():
                            output[label] = address_detail_keys
                        else:
                            output[label] = address_detail_keys + output[label]

                        # print(label,address_detail_keys)

                    elif target_type == "addressBlockPartial":
                        try:
                            i = re.search("[A-Z]", label).start()
                            associated_parent_key_name, child_key_name = (
                                label[:i],
                                label[i:],
                            )
                            child_key_name = (
                                child_key_name[0].lower() + child_key_name[1:]
                            )
                            if "pickUp" in label:
                                associated_parent_key_name = "pickUp"
                                child_key_name = label.replace("pickUp", "")

                            if associated_parent_key_name in output.keys():
                                output[associated_parent_key_name].append(
                                    child_key_name
                                )
                            else:
                                output[associated_parent_key_name] = [child_key_name]
                                # print(label,address_detail_keys)
                                # if keyType goes into regularFields
                        except:
                            pass

                    elif target_type == "key" or (not target_type):
                        try:
                            if (not target_type) and lookup_function(label):
                                qualifier_name = lookup_function(label)
                                if qualifier_name in output.keys():
                                    output[qualifier_name].append(label)
                                else:
                                    output[qualifier_name] = [label]
                            else:
                                if "regularFields" in output.keys():
                                    output["regularFields"].append(label)
                                else:
                                    output["regularFields"] = [label]
                        except:
                            pass
            except:
                print(traceback.print_exc())
                pass

            print(output)
            return jsonify(output), 200

        except Exception as error:
            response = populate_error_response(
                data={}, error=str(error), traceback=traceback.print_exc()
            )
            return jsonify(response), 400
