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

"""

This code is designed to help identify and extract relevant information from documents, such as addresses, company names, and other details. It works by analyzing the text in the document and comparing it to a database of known information.

Here's a step-by-step explanation of what the code does:

1. The code first imports various libraries and modules that it will use to perform its tasks.

2. It then defines several functions and variables that will be used throughout the code.

3. The main function is `lookup_central_main`. This function takes in several pieces of information, including the document itself, settings and definitions for how to interpret the document, and any additional data that might be needed.

4. The function first checks if there are any pre-defined lookups that should be performed. These are essentially queries that have been set up in advance to look for specific types of information.

5. If there are no pre-defined lookups, or if a setting is enabled, the code will attempt to automatically identify and extract information from the document. This is done by breaking the document down into smaller pieces (such as individual addresses or company names) and comparing those pieces to the database of known information.

6. The code uses various techniques to match the information in the document to the information in the database, including fuzzy string matching (which allows for small differences in spelling or formatting) and checking for patterns (such as the first few digits of an account number matching the country code).

7. If a match is found, the code will extract the relevant information from the database and add it to the document. If no match is found, or if there are multiple potential matches, the code will flag the information for manual review.

8. Once all lookups (both pre-defined and automatic) have been performed, the code returns the updated document, along with any messages or flags indicating areas that may need further review.

Overall, the goal of this code is to automate the process of extracting and verifying important information from documents, which can be a time-consuming and error-prone task when done manually. By leveraging databases of known information and various matching techniques, the code aims to improve the accuracy and efficiency of this process.


Here's a more technical documentation of the code:

**Objective:**
The code is designed to perform lookups on key-value pairs extracted from documents to retrieve relevant data from a database. It supports both pre-defined manual lookups and automatic lookups based on the document content.

**Key Components:**
1. **Functions**:
   - `fetch_global_lookup`: Generates SQL queries for automatic lookups based on the key node label and other parameters.
   - `fetch_single_result`: Executes the generated SQL queries, performs fuzzy string matching on company names and address lines, and returns the best matching result.
   - `update_key_node_with_lookup_result`: Updates the key node with the retrieved data from the lookup, handling different cases like addresses and non-address key nodes.
   - `run_manual_query`: Executes pre-defined manual lookup queries and processes the results.

2. **Data Structures**:
   - The code operates on a JSON representation of the document, with key nodes and associated values organized in a hierarchical structure.
   - It uses dictionaries to store directives, rules, and configurations for different scenarios.

3. **External Dependencies**:
   - `requests` library for making HTTP requests to a Rules API.
   - `fuzzywuzzy` library for fuzzy string matching.
   - Various custom modules like `address_custom`, `keychildren_appender`, and `addresss_cleaner` for handling specific tasks related to addresses and key nodes.

**Workflow:**
1. The `lookup_central_main` function is the entry point, which takes the document JSON, settings, and other metadata as input.
2. It checks for pre-defined manual lookup queries and stores them in `lookup_items`.
3. For automatic lookups:
   - It iterates over the key nodes in the document.
   - For each key node, it calls `fetch_global_lookup` to generate SQL queries based on the node label and other parameters.
   - The `fetch_single_result` function executes these queries, performs fuzzy matching on company names and address lines, and returns the best matching result.
   - The `update_key_node_with_lookup_result` function updates the key node with the retrieved data, handling different cases like addresses and non-address key nodes.
4. For manual lookups:
   - It calls `run_manual_query` to execute the pre-defined queries stored in `lookup_items`.
   - The results are processed, and the key nodes are updated accordingly.
5. The updated document JSON and any relevant messages are returned.

**Key Features:**
- Supports automatic lookups based on key node labels and document content.
- Performs fuzzy string matching on company names and address lines to find the best match.
- Handles different scenarios for address and non-address key nodes.
- Executes pre-defined manual lookup queries.
- Utilizes external APIs (Rules API) for executing lookup queries.
- Incorporates various rules and configurations for different scenarios.

"""

RULES_API_URL = os.getenv("RULES_DOCKER_URL")
MINIMUM_COMPANYNAME_MATCH_SCORE = 90
MINIMUM_BLOCK_MATCH_SCORE = 80
AUTO_QUERY_LABELS = [
    "consignee",
    "shipper",
    "notify",
    "pickup",
    "delivery",
    "importer",
    "supplier",
]

MINIMUM_ADDRESS_LINE_MATCH_SCORE = 90

BATCH_ID = None

# creating a list of addressBlock keyValues to run the parser
ADDRESS_KEYS = list()

directives = {
    "single_row_found": {"directive": True, "color": "green"},
    "Nothing found with this company initials / Additional Data do not match": {
        "directive": True,
        "color": "red",
    },
    "Address Line Mismatch": {"directive": True, "color": "yellow"},
    "Company Name did not reach minimum required match score of 90%": {
        "directive": True,
        "color": "red",
    },
    "Company Name has multiple close matches": {
        "directive": True,
        "color": "yellow",
    },
}


def get_key_node_type(label, address_keys):
    """Return the type of a kenode using the label"""
    if label in address_keys:
        return "address"
    else:
        return "others"


def camel_case(st):
    """convert a string to camel case"""
    output = "".join(x for x in st.title() if x.isalnum())
    return output[0].lower() + output[1:]


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


CDZ_FIELDS = ["supplier", "importer"]


def get_table_name(label):
    """
    NAMESPACING CONVENTION OF THE TABLE NAME FORMAT
    FOR CDZ FIELDS: CDZ_{FIELDNAME}
    FOR SHIPMENT FIELDS: FIELDNAME_{MASTER}
    """
    if label.lower() in CDZ_FIELDS:
        return "CDZ_" + label.upper()

    return label.upper() + "_MASTER"


def fetch_global_lookup(key_node, definition_version, profile_id):
    """fetching global lookups by keynode label"""

    lookup_command_set = dict()
    label = key_node["label"]
    if label.lower() in AUTO_QUERY_LABELS:
        nested_label = label + ".name"
        table_name = get_table_name(label)
        if "ebooking" in table_name.lower():
            return None
        keyId = key_node.get("unique_id")
        column_to_search = label.upper() + "NAME"

        column_to_search = "UPPER(" + column_to_search + ")"

        for x in key_node["children"]:
            if x["label"] == "name":
                try:
                    input_value = x["v"].strip().split()[0].upper() + "%"
                    if len(input_value) < 4:
                        # If the company's first word is only a single letter word two words are taken instead of only one
                        input_value = (" ").join(
                            x["v"].strip().split()[:1]
                        ).upper() + "%"
                except:
                    input_value = x["v"].strip()
                    if input_value[-1] == ",":
                        input_value = input_value[:-1]
                    pass

        input_value = f"<I>{input_value}</I>"
        operator_type = "LIKE"
        profile_name = f"<I>{profile_id}</I>"
        if keyId:
            sql = f"SELECT * FROM \"{table_name}\" WHERE {column_to_search} {operator_type} '{input_value}' AND \"PROFILE_NAME\"  = '{profile_name}' "
            lookup_command_set = {
                "keyId": keyId,
                "queries": [
                    {
                        "sql": sql,
                        "group": {
                            "items": [
                                {
                                    "data": {
                                        "value": input_value,
                                        "column": column_to_search,
                                        "operator": operator_type,
                                        "valueType": "input",
                                    },
                                    "type": "rule",
                                },
                                {
                                    "data": {
                                        "value": profile_id,
                                        "column": "PROFILE_NAME",
                                        "operator": "=",
                                        "valueType": "input",
                                    },
                                    "type": "rule",
                                },
                            ],
                            "operator": "AND",
                        },
                        "table": table_name,
                    }
                ],
                "definition_version": definition_version,
                "nestedLabel": nested_label,
                "auto_query": True,
            }

    return lookup_command_set


def fetch_global_lookup_v2(key_node):
    """fetching global lookups by keynode label"""

    lookup_command_set = dict()
    label = key_node["label"]
    if label.lower() in ADDRESS_KEYS:
        input_value = ""

        def __get_input_value__(value):
            try:
                input_value = value.strip().split()[0].upper()
                if len(input_value) < 4:
                    # If the company's first word is only a single letter word two words are taken instead of only one
                    input_value = (" ").join(value.strip().split()[:1]).upper()
            except:
                input_value = value.strip()
                pass
            return input_value

        for x in key_node["children"]:
            if x["label"] == "name":
                input_value = __get_input_value__(x["v"])
        if input_value == "":
            input_value = __get_input_value__(key_node["v"])
        keyId = key_node.get("unique_id")
        if input_value:
            lookup_command_set = {"keyId": keyId, "queries": {"org_name": input_value}}

    return lookup_command_set


def color_key_node(input_keynode, color):
    """Insert color decision key"""
    input_keynode["color_decision"] = color

    if input_keynode["children"]:
        for x in input_keynode["children"]:
            x["color_decision"] = color
    return input_keynode


def get_table_skip_label(source_table, result_dict):
    """GENERATE A LIST OF LABELS THAT NEEDS TO BE SKIPPED FOR PARTICULAR TABLES"""
    TABLE_SPECIFIC_SKIP_LABELS = list()
    try:
        if "template" in source_table.lower():
            for child_label in result_dict.keys():
                if not "template" in child_label.lower():
                    if len(child_label) != 3 and (child_label.lower() != "tid"):
                        TABLE_SPECIFIC_SKIP_LABELS.append(child_label)
    except:
        # print(traceback.print_exc())
        pass
    return TABLE_SPECIFIC_SKIP_LABELS


def convert_lookup_code(child_label, settings_name, key_qualifiers):
    """Finds proper key for the qualifier from lookup codes in definition settings"""
    for setting in key_qualifiers:
        if setting["name"].lower() == settings_name.lower():
            options = setting["options"]
            for option in options:
                if child_label.lower() == option["value"].lower():
                    return option["value"]


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


def update_key_node_with_lookup_result(
    key_node, index, lookup_result, address_keys, key_val_arr, key_qualifiers
):
    """Based on different type of key_nodes the processes are different"""

    SHIFT_DATA_HOLDER = list()
    key_node_type = get_key_node_type(key_node["label"], address_keys)
    result_dict = lookup_result.get("result_dict")
    additional_key_nodes = lookup_result.get("additional_keys")

    unique_id = key_node.get("unique_id")

    color_decision = directives[(lookup_result.get("decision_message"))]["color"]
    # print("color_decision", color_decision)

    source_table = lookup_result.get("source_table")
    # print("source_table", source_table)

    TABLE_SPECIFIC_SKIP_LABELS = get_table_skip_label(source_table, result_dict)

    if color_decision == "yellow":
        key_node["STATUS"] = -1
        # key_node["STATUS"] = -1000
        key_node["auto_lookup_unresolved"] = True
        for child_node in key_node.get("children",[]):
            child_node["STATUS"] = -1

    elif color_decision == "red":
        # key_node["STATUS"] = -2
        key_node["STATUS"] = -1000
        key_node["auto_lookup_unresolved"] = True

    else:
        # print("key_node_type", key_node_type)
        if key_node_type == "address":
            address_cleaned = result_dict.get("address_cleaned")
            if address_cleaned:
                """IF THE ADDRESS IS CLEANED WE HAVE NO WORRIES"""
                key_node = address_cleaned

            """If it is an address we have to work out the child nodes differently"""
            previous_child_items = key_node["children"]
            additional_child_items = list()
            for child_label, child_value in result_dict.items():
                if (
                    child_value and child_label
                ):  # Only if the value is present for child item
                    if type(child_value) == str:
                        if not child_value.strip():
                            continue
                    if "account" in child_label.lower():
                        # print("accountNumber", get_child_value(key_node, "accountNumber"))
                        if not get_child_value(key_node, "accountNumber"):
                            # For template Id a new key text detail child has to be added
                            sample_dict = dict()
                            sample_dict["v"] = child_value
                            sample_dict["label"] = "accountNumber"
                            sample_dict["id"] = "random1234"
                            sample_dict["type"] = "keyTextDetail"
                            sample_dict["children"] = []
                            sample_dict["origin"] = "auto_lookup"
                            sample_dict["is_profile_key_found"] = True
                            sample_dict["is_pure_autoextraction"] = True
                            sample_dict["STATUS"] = 1
                            additional_child_items.append(sample_dict)

                    elif "short_code" in child_label.lower():
                        if not get_child_value(key_node, "shortCode"):
                            # For template Id a new key text detail child has to be added
                            sample_dict = dict()
                            sample_dict["v"] = child_value
                            sample_dict["label"] = "shortCode"
                            sample_dict["id"] = "random12345"
                            sample_dict["type"] = "keyTextDetail"
                            sample_dict["children"] = []
                            sample_dict["origin"] = "auto_lookup"
                            sample_dict["STATUS"] = 1
                            sample_dict["is_profile_key_found"] = True
                            sample_dict["is_pure_autoextraction"] = True
                            additional_child_items.append(sample_dict)
                    continue
                    # if TABLE_SPECIFIC_SKIP_LABELS:
                    #     if child_label in TABLE_SPECIFIC_SKIP_LABELS:
                    #         continue

                    # Replacing Name child from cw1 name
                    if child_label.lower() == key_node["label"].lower() + "_cw1_name":
                        for previous_child in previous_child_items:
                            if previous_child["label"] == "name":
                                previous_child["v"] = child_value
                                continue

                    # References field check (Lookup codes. Different from lookups of this script)
                    lookupcode_type, child_label = lookup_code_conversion(
                        child_label, key_qualifiers
                    )
                    if additional_key_nodes:
                        for extra in additional_key_nodes:
                            if extra["target_column"].lower() == child_label.lower():
                                key_dict = {
                                    "child_label": extra["target_key"]["fieldInfo"][
                                        "keyValue"
                                    ],
                                    "v": child_value,
                                    "index": index,
                                    "motherNode_unique_id": unique_id,
                                }
                                (
                                    lookupcode,
                                    key_dict["child_label"],
                                ) = lookup_code_conversion(
                                    key_dict["child_label"], key_qualifiers
                                )
                                if lookupcode:
                                    key_dict["qualifierParent"] = lookupcode

                                SHIFT_DATA_HOLDER.append(key_dict)
                    if not lookupcode_type:
                        child_label = label_converter(
                            child_label, key_node["label"], key_val_arr, source_table
                        )
                    if not child_label:
                        continue

                    if child_label not in TO_BE_KEPT_INSIDE:
                        # print("TO_BE_KEPT_INSIDE", TO_BE_KEPT_INSIDE)
                        dict_data = {
                            "child_label": child_label,
                            "v": child_value,
                            "index": index,
                            "motherNode_unique_id": unique_id,
                        }
                        if lookupcode_type:
                            dict_data["qualifierParent"] = lookupcode_type

                        SHIFT_DATA_HOLDER.append(dict_data)

                    else:
                        # print("progressed_child_label", child_label)
                        if "name" in child_label.lower():
                            continue

                        if "account" in child_label.lower():
                            # print("accountNumber", get_child_value(key_node, "accountNumber"))
                            if not get_child_value(key_node, "accountNumber"):
                                # For template Id a new key text detail child has to be added
                                sample_dict = dict()
                                sample_dict["v"] = child_value
                                sample_dict["label"] = child_label
                                sample_dict["id"] = "random1234"
                                sample_dict["type"] = "keyTextDetail"
                                sample_dict["children"] = []
                                sample_dict["origin"] = "auto_lookup"
                                additional_child_items.append(sample_dict)

                        elif "shortcode" in child_label.lower():
                            if not get_child_value(key_node, "shortCode"):
                                # For template Id a new key text detail child has to be added
                                sample_dict = dict()
                                sample_dict["v"] = child_value
                                sample_dict["label"] = child_label
                                sample_dict["id"] = "random12345"
                                sample_dict["type"] = "keyTextDetail"
                                sample_dict["children"] = []
                                sample_dict["origin"] = "auto_lookup"
                                additional_child_items.append(sample_dict)

                        else:
                            if not address_cleaned:
                                # Matching existing children and replacing them
                                for previous_child in previous_child_items:
                                    if previous_child["label"] == child_label:
                                        previous_child["v"] = child_value
            # print("additional_child_items", additional_child_items)
            # Adding up the additional child items
            for x in additional_child_items:
                x["STATUS"] = 1

            if (
                additional_child_items
            ):  # Adding the additional non addrress child items to the keynode dictionary
                previous_child_items = additional_child_items + previous_child_items

            key_node["children"] = previous_child_items
            key_node["STATUS"] = 1

        else:
            """FOR RULES APPLIED ON OTHER KEYNODES"""
            for child_label, child_value in result_dict.items():
                if child_value:  # Only if the value is present for child item
                    if TABLE_SPECIFIC_SKIP_LABELS:
                        if child_label in TABLE_SPECIFIC_SKIP_LABELS:
                            continue

                    # References field check (Lookup codes. Different from lookups of this script)
                    lookupcode_type, child_label = lookup_code_conversion(
                        child_label, key_qualifiers
                    )
                    if additional_key_nodes:
                        for extra in additional_key_nodes:
                            if extra["0"].lower() == child_label.lower():
                                key_dict = {
                                    "child_label": label_converter(
                                        extra["1"],
                                        key_node["label"],
                                        key_val_arr,
                                        source_table,
                                    ),
                                    "v": child_value,
                                    "index": index,
                                    "motherNode_unique_id": unique_id,
                                }
                                (
                                    lookupcode,
                                    key_dict["child_label"],
                                ) = lookup_code_conversion(
                                    key_dict["child_label"], key_qualifiers
                                )
                                if lookupcode:
                                    key_dict["qualifierParent"] = lookupcode

                                SHIFT_DATA_HOLDER.append(key_dict)

                    if not lookupcode_type:
                        child_label = label_converter(
                            child_label, key_node["label"], key_val_arr, source_table
                        )

                    if child_label in SKIP_LABELS:
                        continue

                    if child_label:
                        dict_data = {
                            "child_label": child_label,
                            "v": child_value,
                            "index": index,
                            "motherNode_unique_id": unique_id,
                        }
                        if lookupcode_type:
                            dict_data["qualifierParent"] = lookupcode_type

                        SHIFT_DATA_HOLDER.append(dict_data)

    return key_node, SHIFT_DATA_HOLDER


def get_decision(single_query_data, nested_label, key_unique_id):
    decision_item = dict()

    single_query_data = single_query_data.get("result")

    decision = "fail"

    if "." in nested_label:
        key_label_split = nested_label.split(".")
        key_label = key_label_split[0]
        child_name = key_label_split[1]
    else:
        key_label = nested_label
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
                    "key_nested_label": nested_label,
                    "motherLabel": key_label,
                    "result_dict": result_dict,
                    "key_unique_id": key_unique_id,
                }
    else:
        decision = "incomplete"

    return decision, decision_item


def get_name_cell(label, row):
    """Get name cell from table row"""
    for key, value in row.items():
        if (
            ("name" in key.lower())
            and (label.lower() in key.lower())
            and not ("cw1" in key.lower())
        ):
            return value


def get_process_type(key_node, address_keys):
    """Get process type depending on the key_node Label"""
    if key_node["label"] in address_keys:
        return "set1"
    return "set2"


def get_child_value(key_node, child_node):
    """extract specific address child value from a keynode children list"""
    for child_dict in key_node["children"]:
        if child_dict["label"] == child_node:
            return child_dict["v"]
    return None


def fetch_notfound_message_for_process(process_type):
    if not process_type:
        return "Functional Error"
    if process_type == "set1":
        return "Nothing found with this company initials / Additional Data do not match"

    return ""


def execute_write(key_node, batch_id, reason):
    """Writing missing data on disk"""

    missing_data = {
        "keyNode": key_node["label"],
        "address_text": get_child_value(key_node, "block"),
        "name": get_child_value(key_node, "name"),
        "addressLine1": get_child_value(key_node, "addressLine1"),
        "addressLine2": get_child_value(key_node, "addressLine2"),
        "city": get_child_value(key_node, "city"),
        "postalCode": get_child_value(key_node, "postalCode"),
        "country": get_child_value(key_node, "country"),
        "countryCode": get_child_value(key_node, "countryCode"),
        "batch_id": batch_id,
        "reason": reason,
        "report_time": str(datetime.datetime.utcnow()),
    }

    filepath = "app/lookup_missing_data.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            x = json.load(f)
            if not missing_data in x:
                x.append(missing_data)
                with open(filepath, "w") as f:
                    json.dump(x, f)

    else:
        missing_list = [missing_data]
        with open(filepath, "w") as f:
            json.dump(missing_list, f)


def check_db_adLines(row, label):
    if row.get(label.upper() + "ADDRESSLINE1"):
        return False
    return True


def check_addresslines(key_node, row, label):
    disregard = False
    if row.get(label.upper() + "ADDRESSLINE1"):
        ad1_kn = get_child_value(key_node, "addressLine1")
        if ad1_kn:
            if (
                fuzz.ratio(row[label.upper() + "ADDRESSLINE1"].lower(), ad1_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True

    if row.get(label.upper() + "ADDRESSLINE2"):
        ad2_kn = get_child_value(key_node, label.upper() + "ADDRESSLINE2")
        if ad2_kn:
            if (
                fuzz.ratio(row[label.upper() + "ADDRESSLINE2"].lower(), ad2_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True
    return disregard


def check_addresslinesV2(key_node, row, label):
    disregard = False
    if row.get(label):
        ad1_kn = get_child_value(key_node, "addressLine1")
        # ad1_kn = "CENTER HS RDC VENRAY"
        if ad1_kn:
            if (
                fuzz.ratio(row[label].lower(), ad1_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True

    if row.get(label):
        ad2_kn = get_child_value(key_node, "addressLine2")
        if ad2_kn:
            if (
                fuzz.ratio(row[label].lower(), ad2_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True
    return disregard


def check_if_close_matches(numbers, target):
    try:
        if len(numbers) > 1:
            if numbers.count(target) > 1:
                return True

        for number in numbers:
            if abs(number - target) <= 2 and number != target:
                return True
    except:
        pass

    return False


def fetch_single_result(
    global_lookup,
    key_node,
    address_keys,
    MESSAGES,
    doc_id,
    use_cw1,
    lookup_type,
    disable_country_code_check,
    master_dictionaries,
):
    # master_dictionaries = request_data.get("master_dictionaries")
    country_Map = master_dictionaries.get("country_Map").get("data")
    """Fetch result from api and use fuzzyuzzy to return the one with the highest match"""
    decision_item = {"decision_message": fetch_notfound_message_for_process(None)}
    try:
        request_body = global_lookup
        # print("request_body :", request_body)
        response = requests.post(
            f"{RULES_API_URL}/api/run_lookup/", json=request_body
        ).json()

        # print(response)

        response_detail = response.get("detail")
        all_query_result = response["query_results"]
        auto_query_message = None

        process_type = get_process_type(key_node, address_keys)
        decision_item = {
            "decision_message": fetch_notfound_message_for_process(process_type)
        }
        label = key_node["label"]

        if (
            process_type == "set1"
        ):  # Search by first company word in company name and then filter by fuzzy
            for single_query_result in all_query_result:
                key_nested_label = key_node["label"] + ".name"
                table_name = single_query_result.get("source_table")

                scores_list = list()

                rows = single_query_result["result"]

                if not rows:
                    decision_item = {
                        "decision_message": fetch_notfound_message_for_process(
                            process_type
                        )
                    }
                    auto_query_message = {
                        "message": "No match found for {}".format(key_node["label"]),
                        "code": 400,
                        "module": "Lookups",
                    }

                    reason = "Nothing found with company initials"
                    # execute_write(key_node, batch_id, reason)
                    MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                return_dict = None
                try:
                    full_address_present = False
                    for row in rows:
                        if row.get(label.upper() + "_FULL_ADDRESS"):
                            full_address_present = True

                    if full_address_present:
                        prepared_json = {
                            "rows": rows,
                            "keyNode": key_node,
                            "use_cw1": use_cw1,
                        }
                        return_dict = clean_keyNode(prepared_json)
                except:
                    print(traceback.print_exc())
                    pass

                if return_dict:
                    cleaned_keyNode = return_dict.get("keyNode")
                    row_idx = return_dict.get("matched_index")
                    final_row = rows[row_idx]
                    max_score = 95

                    decision_item = {
                        "key_nested_label": key_nested_label,
                        "motherLabel": key_node["label"],
                        "result_dict": final_row,
                        "key_unique_id": key_node["unique_id"],
                        "decision_message": "single_row_found",
                        "address_cleaned": cleaned_keyNode,
                    }

                    auto_query_message = {
                        "message": " LOOKUPS: {} auto query matched at {} pct".format(
                            decision_item["key_nested_label"], max_score
                        ),
                        "code": 200,
                        "module": "Lookups",
                    }

                    # MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                # Fetching company name and the relevant iso2
                company_name_original_case = get_child_value(key_node, "name")
                company_name = company_name_original_case.upper()

                country_iso_check = False
                if not disable_country_code_check:
                    company_country = get_child_value(key_node, "country")
                    company_country_iso = get_child_value(key_node, "countryCode")
                    country_iso_check = True

                    # Creating a placeholder if country or country code exists

                    if not company_country_iso:
                        if company_country:
                            try:
                                company_country_iso = get_iso2(
                                    company_country, country_Map
                                )
                            except:
                                pass

                        if not company_country_iso:
                            country_iso_check = False

                    if country_iso_check:
                        if company_country == company_country_iso:
                            country_iso_check = False

                # placeholder for rows considered by company name fuzzy match
                consideration_1 = list()
                consideration_1_fuzz_score = list()

                # Step 1 - By Company Name Match
                for row_idx, row in enumerate(rows):
                    account_number_first_two_digit_mismatch = False
                    name_cell = get_name_cell(label, row)
                    if not name_cell:
                        continue
                    try:
                        # Extra Spaces Removal
                        if "  " in name_cell.lower():
                            name_cell = name_cell.lower().replace("  ", " ")
                    except:
                        pass

                    # Checking the ratio of the match
                    fuzz_score = fuzz.ratio(name_cell.lower(), company_name.lower())

                    if fuzz_score >= MINIMUM_COMPANYNAME_MATCH_SCORE:
                        scores_list.append(fuzz_score)

                        if lookup_type == "Normal":
                            consideration_1.append(row)  # Storing the rows
                            consideration_1_fuzz_score.append(
                                fuzz_score
                            )  # Storing the indexes

                            continue

                        disregard = False

                        # If address lines are present address lines are checked
                        address_line_consideration_out = False
                        address_line_consideration_out = check_db_adLines(row, label)
                        address_line_match = check_addresslines(key_node, row, label)
                        if (
                            not address_line_match
                            and not address_line_consideration_out
                        ):
                            disregard = True

                        if not disregard:
                            account_number_holder = None
                            # Extracting account number and further checks
                            try:
                                account_number_holder = row.get(
                                    key_node["label"].upper() + "ACCOUNTNUMBER"
                                )
                            except:
                                pass
                            if country_iso_check and account_number_holder:
                                if account_number_holder[:2] != company_country_iso:
                                    account_number_first_two_digit_mismatch = True

                            if not account_number_first_two_digit_mismatch:
                                consideration_1.append(row)  # Storing the rows
                                consideration_1_fuzz_score.append(
                                    fuzz_score
                                )  # Storing the indexes

                # Placeholder for the final row
                final_row = None

                if not final_row and consideration_1:
                    """If step 2 didn't work best match from consideration_1 is to be chosen"""
                    max_score = max(consideration_1_fuzz_score)
                    if not check_if_close_matches(
                        consideration_1_fuzz_score, max_score
                    ):
                        target_index = consideration_1_fuzz_score.index(max_score)
                        final_row = consideration_1[target_index]
                    else:
                        decision_item = {
                            "decision_message": "Company Name has multiple close matches"
                        }
                        auto_query_message = {
                            "message": " {} Company Name has multiple close matches - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                if final_row:
                    decision_item = {
                        "key_nested_label": key_nested_label,
                        "motherLabel": key_node["label"],
                        "result_dict": final_row,
                        "key_unique_id": key_node["unique_id"],
                        "decision_message": "single_row_found",
                        "source_table": table_name,
                    }

                    auto_query_message = {
                        "message": " LOOKUPS: {} auto query matched at {} pct".format(
                            decision_item["key_nested_label"], max_score
                        ),
                        "code": 200,
                        "module": "Lookups",
                    }
                    # MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                else:
                    if not scores_list:
                        decision_item = {
                            "decision_message": "Company Name did not reach minimum required match score of 90%"
                        }
                        auto_query_message = {
                            "message": "{} Company Name did not reach minimum required match score of 90% - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                    else:
                        message = "{} Address Line/Account Number initials Mismatch - doc {}".format(
                            label, doc_id[-2:]
                        )
                        auto_query_message = {
                            "message": message,
                            "code": 400,
                            "module": "Lookups",
                        }

                        # execute_write(key_node, batch_id, reason)
                        decision_item = {"decision_message": "Address Line Mismatch"}
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES
    except:
        print(traceback.print_exc())
        pass

    auto_query_message = {
        "message": "No match found for {}".format(key_node["label"]),
        "code": 400,
        "module": "Lookups",
    }
    MESSAGES.append(auto_query_message)
    reason = "General Error"
    # execute_write(key_node, batch_id, reason)
    return decision_item, MESSAGES


def fetch_single_result_v2(
    global_lookup,
    key_node,
    address_keys,
    MESSAGES,
    doc_id,
    use_cw1,
    lookup_type,
    disable_country_code_check,
    master_dictionaries,
    profile_customers,
):
    # master_dictionaries = request_data.get("master_dictionaries")
    country_Map = master_dictionaries.get("country_Map").get("data")
    """Fetch result from api and use fuzzyuzzy to return the one with the highest match"""
    decision_item = {"decision_message": fetch_notfound_message_for_process(None)}
    try:
        # Filter out values from existing customers with matching name.
        new_customers = []
        for pc in profile_customers:
            if (
                pc.get("name")
                .lower()
                .startswith(global_lookup.get("queries", {}).get("org_name").lower())
            ):
                new_customers.append(pc)
        all_query_result = [{"result": new_customers}]
        auto_query_message = None

        process_type = get_process_type(key_node, address_keys)
        decision_item = {
            "decision_message": fetch_notfound_message_for_process(process_type)
        }
        label = key_node["label"]

        if (
            process_type == "set1"
        ):  # Search by first company word in company name and then filter by fuzzy
            for single_query_result in all_query_result:
                key_nested_label = key_node["label"] + ".name"
                table_name = single_query_result.get("source_table")

                scores_list = list()

                rows = single_query_result.get("result")
                print(
                    "🐍 File: add_ons/lookup_central.py | Line: 1088 | undefined ~ rows",
                    rows,
                )

                if not rows:
                    decision_item = {
                        "decision_message": fetch_notfound_message_for_process(
                            process_type
                        )
                    }
                    auto_query_message = {
                        "message": "No match found for {}".format(key_node["label"]),
                        "code": 400,
                        "module": "Lookups",
                    }

                    reason = "Nothing found with company initials"
                    # execute_write(key_node, batch_id, reason)
                    MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                # Fetching company name and the relevant iso2
                company_name_original_case = get_child_value(key_node, "name")
                company_name = company_name_original_case.upper()

                country_iso_check = False
                try:
                    if not disable_country_code_check:
                        company_country = get_child_value(key_node, "country")
                        company_country_iso = get_child_value(key_node, "countryCode")
                        country_iso_check = True

                        # Creating a placeholder if country or country code exists

                        if not company_country_iso:
                            if company_country:
                                try:
                                    company_country_iso = get_iso2(
                                        company_country, country_Map
                                    )
                                except:
                                    pass

                            if not company_country_iso:
                                country_iso_check = False

                        if country_iso_check:
                            if company_country == company_country_iso:
                                country_iso_check = False
                except:
                    print("Problem checking ISO")
                    pass

                # placeholder for rows considered by company name fuzzy match
                consideration_1 = list()
                consideration_1_fuzz_score = list()

                # Step 1 - By Company Name Match
                for row_idx, row in enumerate(rows):
                    account_number_first_two_digit_mismatch = False
                    name_cell = row.get("name")
                    # Checking the ratio of the match
                    fuzz_score = fuzz.ratio(name_cell.lower(), company_name.lower())

                    if fuzz_score >= MINIMUM_COMPANYNAME_MATCH_SCORE:
                        scores_list.append(fuzz_score)

                        if lookup_type == "Normal":
                            consideration_1.append(row)  # Storing the rows
                            consideration_1_fuzz_score.append(
                                fuzz_score
                            )  # Storing the indexes

                            continue

                        disregard = False

                        # If address lines are present address lines are checked
                        address_line_consideration_out = False
                        # address_line_consideration_out = check_db_adLines(row, label)
                        address_line_consideration_out = row.get("address_line1")
                        address_line_match = check_addresslinesV2(key_node, row, label)
                        if (
                            not address_line_match
                            and not address_line_consideration_out
                        ):
                            disregard = True

                        if not disregard:
                            account_number_holder = None
                            # Extracting account number and further checks
                            try:
                                account_number_holder = row.get("cw1_code")
                            except:
                                pass
                            if country_iso_check and account_number_holder:
                                if account_number_holder[:2] != company_country_iso:
                                    account_number_first_two_digit_mismatch = True

                            if not account_number_first_two_digit_mismatch:
                                consideration_1.append(row)  # Storing the rows
                                consideration_1_fuzz_score.append(
                                    fuzz_score
                                )  # Storing the indexes

                # Placeholder for the final row
                final_row = None

                if not final_row and consideration_1:
                    """If step 2 didn't work best match from consideration_1 is to be chosen"""
                    max_score = max(consideration_1_fuzz_score)
                    if not check_if_close_matches(
                        consideration_1_fuzz_score, max_score
                    ):
                        target_index = consideration_1_fuzz_score.index(max_score)
                        final_row = consideration_1[target_index]
                    else:
                        decision_item = {
                            "decision_message": "Company Name has multiple close matches"
                        }
                        auto_query_message = {
                            "message": " {} Company Name has multiple close matches - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                if final_row:
                    decision_item = {
                        "key_nested_label": key_nested_label,
                        "motherLabel": key_node["label"],
                        "result_dict": final_row,
                        "key_unique_id": key_node["unique_id"],
                        "decision_message": "single_row_found",
                        "source_table": table_name,
                    }

                    auto_query_message = {
                        "message": " LOOKUPS: {} auto query matched at {} pct".format(
                            decision_item["key_nested_label"], max_score
                        ),
                        "code": 200,
                        "module": "Lookups",
                    }
                    # MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                else:
                    if not scores_list:
                        decision_item = {
                            "decision_message": "Company Name did not reach minimum required match score of 90%"
                        }
                        auto_query_message = {
                            "message": "{} Company Name did not reach minimum required match score of 90% - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                    else:
                        message = "{} Address Line/Account Number initials Mismatch - doc {}".format(
                            label, doc_id[-2:]
                        )
                        auto_query_message = {
                            "message": message,
                            "code": 400,
                            "module": "Lookups",
                        }

                        # execute_write(key_node, batch_id, reason)
                        decision_item = {"decision_message": "Address Line Mismatch"}
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES
    except:
        print(traceback.print_exc())
        pass

    auto_query_message = {
        "message": "No match found for {}".format(key_node["label"]),
        "code": 400,
        "module": "Lookups",
    }
    MESSAGES.append(auto_query_message)
    reason = "General Error"
    # execute_write(key_node, batch_id, reason)
    return decision_item, MESSAGES


def create_key_node(extra):
    """Create a dummy keynode with a given label and value"""
    extra_keynode = dict()
    extra_keynode["children"] = []
    extra_keynode["v"] = extra["v"].upper()
    extra_keynode["pos"] = ""
    extra_keynode["id"] = extra["child_label"] + "addressManualBorn" + "01"
    extra_keynode["label"] = extra["child_label"]
    extra_keynode["pageId"] = ""
    extra_keynode["type"] = "key_detail"
    extra_keynode["origin"] = "lookup"
    extra_keynode["unique_id"] = (
        extra["motherNode_unique_id"]
        + "-"
        + extra["child_label"]
        + "-"
        + str(extra["extra_idx"])
    )
    extra_keynode["STATUS"] = 1
    if extra.get("qualifierParent"):
        disregard = False
        if (
            extra.get("qualifierParent") == "references"
            and len(extra["child_label"]) != 3
        ):
            disregard = True
        if not disregard:
            extra_keynode["qualifierParent"] = extra.get("qualifierParent")

    return extra_keynode


def get_child_value(input_Node, child_key_name):
    children = input_Node["children"]
    for child_idx, child in enumerate(children[:]):
        if child["label"] == child_key_name:
            return child["v"]
    return ""


def transform_query(group_item_data, associated_sql_data, initial_key_name, doc):
    """replace value of group item"""

    value = ""

    key_name = initial_key_name

    mother_label = key_name

    if "." in key_name:
        mother_label = key_name.split(".")[0]
        key_name = key_name.split(".")[1]

    address_child_type = False

    if mother_label != key_name:
        address_child_type = True

    nodes = doc["children"]
    for node in nodes:
        if "key" in node["type"]:
            key_nodes = node["children"]
            label_to_look_for = mother_label
            for key_node in key_nodes:
                if key_node["label"] == label_to_look_for:
                    if not address_child_type:
                        value = key_node["v"]
                    else:
                        value = get_child_value(key_node, key_name)

    if value:
        group_item_data["value"] = value
        associated_sql_data = associated_sql_data.replace(initial_key_name, value)

    return group_item_data, associated_sql_data


def replace_placeholders_with_value(item_queries, doc):
    """This function goes inside each query and sees if there is a placeholder present and then puts in the value
    after fetching form data json"""

    updated_item_query_list = item_queries.copy()
    for query in item_queries:
        group = query.get("group")
        group_items = group.get("items")
        associated_sql_data = query.get("sql")
        for group_item in group_items:
            group_item_data = group_item.get("data")
            value_type = group_item_data.get("valueType")
            if value_type == "placeholder":
                key_name = group_item_data.get("value")
                group_item_data, associated_sql_data = transform_query(
                    group_item_data, associated_sql_data, key_name, doc
                )

        group["items"] = group_items
        query["sql"] = associated_sql_data
        updated_item_query_list.append(query)

    return updated_item_query_list


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
            if value_type == "key":
                placeholder_present = True

    return placeholder_present


def generate_label_val_pairs(doc):
    """This function generates keyvalue pairs"""
    output_list = list()
    nodes = doc["children"]
    for node in nodes:
        if "key" in node["type"]:
            key_nodes = node["children"]
            for k in key_nodes:
                label = k["label"]
                value = k["v"]
                if not k.get("children"):
                    created_dict = {"label": label, "value": value}
                    output_list.append(created_dict)
                else:
                    for c in k.get("children"):
                        key_name = c.get("label")
                        label = k["label"] + "." + key_name
                        value = c.get("v")
                        created_dict = {"label": label, "value": value}
                        output_list.append(created_dict)

    return output_list


def run_manual_query(lookup_item, doc, definition_version, messages):
    result_storage = list()
    lookup_items = [lookup_item]
    # Running manual queries
    for lookup_item in lookup_items:
        # print("lookup_item", lookup_item)
        nested_label = lookup_item.get("nestedLabel")
        key_unique_id = lookup_item.get("keyId")
        additional_keys = list()
        item_queries = lookup_item["queries"]
        for item_quiry in item_queries:
            if item_quiry.get("additionalKeys"):
                if item_quiry.get("additionalKeys").get("items"):
                    additions = item_quiry.get("additionalKeys").get("items")
                    for additional_key in additions:
                        additional_keys.append(additional_key)

        # Replacing the placeholders
        # item_queries = replace_placeholders_with_value(item_queries, doc)

        placeholder_present = check_for_placeholders(item_queries)

        request_body = {
            "queries": item_queries,
            "definition_version": definition_version,
        }

        if placeholder_present:
            keys_data = generate_label_val_pairs(doc)
            request_body["keys"] = keys_data
        # print("request_body", request_body)
        # print("placeholder_present", placeholder_present)
        response = requests.post(
            f"{RULES_API_URL}/api/run_lookup/", json=request_body
        ).json()
        # print("response", response)

        response_detail = response.get("detail")

        all_query_result = response.get("query_results")

        if all_query_result:
            for single_query_data in all_query_result:
                table_name = single_query_data.get("source_table")
                decision, decision_item = get_decision(
                    single_query_data, nested_label, key_unique_id
                )

                if decision == "pass":
                    decision_item["source_table"] = table_name
                    if additional_keys:
                        decision_item["additional_keys"] = additional_keys
                    result_storage.append(decision_item)
                else:
                    manual_query_error_message = {
                        "message": "Multiple/No rows found with manual lookup query for {}".format(
                            nested_label
                        ),
                        "code": 400,
                        "module": "Lookups",
                    }
                    messages.append(manual_query_error_message)

    lookup_result_labels = list()
    # print("result_storage", result_storage)
    for result in result_storage:
        result["decision_message"] = "single_row_found"
        lookup_result_labels.append(result["motherLabel"])
    return lookup_result_labels, result_storage


def lookup_central_main(request_data, d_json, messages, master_dictionaries):
    lookup_central_version = "v5.1.16002023"
    # @Emon on 14/10/2022 - Initiated table rules script
    # @Emon on 24/10/2022 - Added global lookup fetcher
    # @Emon on 30/10/2022 - Added messaging and accountNumber iso check
    # @Emon on 27/11/2022 - Added use oracle and definition version
    # @Emon on 08/12/2022 - Keynodes updated with statues and further childnodes handling
    # @Emon on 28/12/2022 - Auto Query to take precendence
    # @Emon on 01/01/2022 - Auto Lookup Variable is passed to lookup docker
    # @Emon on 03/01/2022 - Template Table only to fetch template id
    # @Emon on 10/01/2022 - Auto Query Updated to fetch two words if the first word only consists of one single letter
    # @Emon on 11/01/2022 - Previous keynodes will be replaced
    # @Emon on 18/01/2022 - TID and shortCode update
    # @Emon on 20/01/2022 - Label Conversion Logic updated
    # @Emon on 25/01/2022 - Lookup code detection and conversion added
    # @Emon on 16/02/2023 - Auto Queries will only query with same profile id
    # creating a list of addressBlock keyValues to run the parser
    # @emon on 25/02/2023 - Disable Country Code match on account number first two chars added
    # master_dictionaries = request_data.get("master_dictionaries")
    address_keys = list()
    profile_customers = request_data.get("profile_customers", [])
    try:
        definition_settings = request_data.get("definition_settings")
        key_options_items = (
            definition_settings.get("options", {}).get("options-keys", {}).get("items")
        )
    except:
        pass

    key_qualifiers = definition_settings.get("keyQualifiers")

    # print("===========")
    kay_val_arr = list()

    # lookupLables
    for item_settings_from_def in key_options_items:
        kay_val_arr.append(item_settings_from_def.get("keyValue"))
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
    autoquery_disabled = False

    global ADDRESS_KEYS

    try:

        definition_settings = request_data.get("definition_settings")
        key_qualifiers = definition_settings.get("keyQualifiers")
        key_options_items = (
            definition_settings.get("options", {}).get("options-keys", {}).get("items")
        )

        # lookupLables
        for item_settings_from_def in key_options_items:
            if item_settings_from_def["type"] == "addressBlock":
                ADDRESS_KEYS.append(item_settings_from_def["keyValue"].lower())
    except:
        pass

    try:
        if definitions["key"]["models"][0].get("lookupDisableAutoQuery") == "true":
            autoquery_disabled = True
    except:
        pass

    # Placeholder for manually saved saved lookups
    lookup_items = list()

    try:
        lookup_items = definitions["key"]["lookupItems"]
    except:
        pass

        # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass

    docs = d_json.get("nodes")
    batch_id = d_json.get("id")
    profile_name = definitions.get("definition_id")

    if not autoquery_disabled:
        lookup_type = "Explicit"
        try:
            if definitions["key"]["models"][0].get("lookupType") == "Normal":
                lookup_type = "Normal"
        except:
            pass

        disable_country_code_check = False
        try:
            if (
                definitions["key"]["models"][0].get("lookupDisableCountryCodeCheck")
                == "true"
            ):
                disable_country_code_check = True
        except:
            pass

        # Automatic Lookup
        for input_doc_idx, target_doc in enumerate(docs):
            # Figuring a way out here
            if test_document_trigger != None:
                if test_document_trigger != target_doc["id"]:
                    continue
            nodes = target_doc["children"]

            for node in nodes:
                if "key" in node["type"]:
                    key_nodes = node["children"]
                    extra_data_holder = list()
                    for key_node_idx, key_node in enumerate(key_nodes):
                        label = key_node["label"]

                        try:
                            """Else check for a global lookup for the keynode label"""
                            global_lookup = fetch_global_lookup_v2(key_node)
                            if global_lookup:
                                """If global lookup exists - the execute it"""

                                lookup_result, MESSAGES = fetch_single_result_v2(
                                    global_lookup,
                                    key_node,
                                    address_keys,
                                    MESSAGES,
                                    target_doc["id"],
                                    use_cw1,
                                    lookup_type,
                                    disable_country_code_check,
                                    master_dictionaries,
                                    profile_customers,
                                )
                                directive = None
                                try:
                                    directive = directives[
                                        lookup_result.get("decision_message")
                                    ].get("directive")
                                except:
                                    pass
                                if directive:
                                    """If a valid single row lookup result then update the keynode"""
                                    (
                                        key_node,
                                        extra_data,
                                    ) = update_key_node_with_lookup_result(
                                        key_node,
                                        key_node_idx,
                                        lookup_result,
                                        address_keys,
                                        kay_val_arr,
                                        key_qualifiers,
                                    )
                                    if extra_data:
                                        extra_data_holder += extra_data
                                else:
                                    if key_node.get("children", []):
                                        if (
                                            key_node.get("label")
                                            and key_node.get("label").lower()
                                            in ADDRESS_KEYS
                                        ):
                                            key_node["STATUS"] = -1000
                                    else:
                                        key_node["STATUS"] = 200
                                    key_node["auto_lookup_unresolved"] = True
                                    # key_node = color_key_node(key_node, "red")
                        except:
                            print(traceback.print_exc())

                    if extra_data_holder:
                        """If address child produces non-address child data using lookups: shift them outside the keynode children and into the main list"""

                        for extra_idx, extra in enumerate(extra_data_holder):
                            keynode_label = extra.get("child_label")
                            # Removing previous nodes with the same label
                            for x in key_nodes:
                                if x.get("label") == keynode_label:
                                    key_nodes.remove(x)

                            insert_index = extra["index"]
                            extra["extra_idx"] = extra_idx
                            key_nodes.insert(insert_index, create_key_node(extra))

                    node["children"] = key_nodes

    # Manual Lookup
    # print("---- Manual lookup start")
    # Remove for now 13/08/2025
    # for input_doc_idx, target_doc in enumerate(docs):
    #     # Figuring a way out here
    #     if test_document_trigger != None:
    #         if test_document_trigger != target_doc["id"]:
    #             continue
    #     nodes = target_doc["children"]

    #     for node in nodes:
    #         if "key" in node["type"]:
    #             key_nodes = node["children"]
    #             for lookup_item in lookup_items:
    #                 lookup_result_labels, result_storage = run_manual_query(
    #                     lookup_item, target_doc, definition_version, messages
    #                 )

    #                 extra_data_holder = list()
    #                 for key_node_idx, key_node in enumerate(key_nodes):
    #                     label = key_node["label"]
    #                     if label in lookup_result_labels:
    #                         """If a label is set as a local lookup execute a normal query"""
    #                         lookup_result = result_storage[
    #                             lookup_result_labels.index(label)
    #                         ]

    #                         try:
    #                             if (
    #                                 key_node["unique_id"]
    #                                 == lookup_result["key_unique_id"]
    #                                 and key_node["label"]
    #                                 == lookup_result["motherLabel"]
    #                             ):
    #                                 # print(key_node["label"], lookup_result["motherLabel"])
    #                                 (
    #                                     key_node,
    #                                     extra_data,
    #                                 ) = update_key_node_with_lookup_result(
    #                                     key_node,
    #                                     key_node_idx,
    #                                     lookup_result,
    #                                     address_keys,
    #                                     kay_val_arr,
    #                                     key_qualifiers,
    #                                 )

    #                                 if extra_data:
    #                                     extra_data_holder += extra_data
    #                         except:
    #                             print(traceback.print_exc())
    #                         label_count = lookup_result_labels.count(label)

    #                         if label_count > 1:
    #                             first_result = lookup_result_labels.index(label)
    #                             lookup_result = result_storage[
    #                                 lookup_result_labels.index(label, first_result + 1)
    #                             ]

    #                             # print("lookup_result2", lookup_result)
    #                             try:
    #                                 if (
    #                                     key_node["unique_id"]
    #                                     == lookup_result["key_unique_id"]
    #                                     and key_node["label"]
    #                                     == lookup_result["motherLabel"]
    #                                 ):
    #                                     (
    #                                         key_node,
    #                                         extra_data,
    #                                     ) = update_key_node_with_lookup_result(
    #                                         key_node,
    #                                         key_node_idx,
    #                                         lookup_result,
    #                                         address_keys,
    #                                         kay_val_arr,
    #                                         key_qualifiers,
    #                                     )
    #                                     if extra_data:
    #                                         extra_data_holder += extra_data
    #                             except:
    #                                 print(traceback.print_exc())
    #                 # print("extra_data_holder", extra_data_holder)
    #                 if extra_data_holder:
    #                     """If address child produces non-address child data using lookups: shift them outside the keynode children and into the main list"""

    #                     for extra_idx, extra in enumerate(extra_data_holder):
    #                         try:
    #                             keynode_label = extra.get("child_label")
    #                             # Removing previous nodes with the same label
    #                             for x in key_nodes:
    #                                 if x.get("label") == keynode_label:
    #                                     key_nodes.remove(x)
    #                                 insert_index = extra["index"]

    #                             extra["extra_idx"] = extra_idx
    #                             key_nodes.insert(insert_index, create_key_node(extra))
    #                         except:
    #                             print(traceback.print_exc())

    #             node["children"] = key_nodes
    # Change status of child for mother node status -1000
    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]

        for node in nodes:
            if "key" in node["type"]:
                key_nodes = node["children"]
                for key_node in key_nodes:
                    if key_node.get("STATUS") == -1000:
                        for child_key in key_node.get("children", []):
                            child_key["STATUS"] = -1000
    return d_json, MESSAGES
