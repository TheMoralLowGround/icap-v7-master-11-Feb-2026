import threading
import traceback

from app.address_modules.address_custom import custom_address_parser
from app.address_modules.simple_detectors.company_by_email import (
    detect_company_by_email_and_rearrange,
)
from app.address_modules.simple_detectors.trim_till_country import trim_address

from ..address_modules.converters.espanol import translate_spanish_to_english

"""
Script that creates children inside each keynode for key-view.
Depening on the label being a address item or compound field or a regular field.

This code is written in Python and is used for processing and formatting address data. It takes in JSON data containing addresses and performs various operations on it. Here's a summary in simpler terms:

1. The code imports some functions from other files that help with processing addresses, such as detecting the company name from an email address and trimming the address until the country is found.

2. It defines some lists of labels that are related to address fields (e.g., "addressLine1", "city", "state") and labels that should be skipped during processing.

3. There are functions to check if certain address processing operations (like detecting the company by email or trimming the address until the country) should be performed based on some configurations.

4. The main function `key_child_appender_process` takes the input JSON data, a list of address keys, some configurations, and additional data.

5. It loops through the input data and for each address field (like "addressLine1", "city", etc.), it performs the following operations:
   - If the field is an address field, it tries to format the address text using the imported functions.
   - It splits the address text into lines and creates child nodes for each line under the address field.
   - If the address text is a dictionary, it creates additional child nodes for any extra data that is not part of the standard address fields.

6. The processed JSON data with the formatted addresses and additional child nodes is returned.

In summary, this code takes address data in a specific JSON format, processes and formats the addresses based on certain rules and configurations, and returns the processed data with additional child nodes representing the formatted address lines and any extra data.

Here's a more technical summary of the code:

This Python script contains functions to process JSON data containing address information. The primary function is `key_child_appender_process`, which takes a JSON object `d_json`, a list of address keys `address_keys`, a list of definitions `definitions`, and a request data dictionary `request_data`.

The function iterates over the nodes in the JSON object, and for each node with the type "key", it processes the children nodes. If a child node is marked as a compound key, it is skipped. Otherwise, the function checks if the child node's label is in the `address_keys` list.

If the label is an address key, the function attempts to parse and format the address text using various techniques:

1. It trims the address text until the country if the `trim_address_by_country_trigger` function returns True based on the `definitions`.
2. It attempts to detect the company name from an email address and rearrange the address text if the `detectCompanyByEmail` function returns True based on the `definitions`.
3. It calls the `custom_address_parser` function with the address text, `definitions`, and `master_dictionaries` from `request_data` to further parse and format the address.

The function then splits the formatted address text into lines and creates child nodes for each line under the address key node. If the address text is a dictionary, it creates additional child nodes for any keys not in the `TO_BE_KEPT_INSIDE` list.

The script also defines a helper function `create_key_node` to create a new key node with children for any extra address data that doesn't fit into the standard address fields.

The script imports the following functions from other modules:

- `custom_address_parser` from `app.address_modules.address_custom`
- `detect_company_by_email_and_rearrange` from `app.address_modules.simple_detectors.company_by_email`
- `trim_address` from `app.address_modules.simple_detectors.trim_till_country`

The modified JSON data with the formatted addresses and additional child nodes is returned by the `key_child_appender_process` function.

"""


def create_key_node(extra):
    extra_keynode = dict()
    extra_keynode["children"] = []
    extra_keynode["v"] = extra["v"].upper()
    extra_keynode["pos"] = extra["pos"]
    extra_keynode["unique_id"] = extra["unique_id"] + "_" + extra["label"]
    extra_keynode["id"] = extra["label"] + "addressManualBorn" + "01"
    extra_keynode["label"] = extra["label"]
    extra_keynode["pageId"] = extra["pageId"]
    extra_keynode["type"] = "key_detail"
    return extra_keynode


TO_BE_KEPT_INSIDE = [
    "name",
    "addressLine1",
    "addressLine2",
    "city",
    "state",
    "country",
    "postcode",
    "countryCode",
    "postalCode",
    "block",
    "Attn",
    "contactPhone",
    "contactEmail",
    "accountNumber",
    "stateProvince",
    "Fax",
    "postalcode",
    "shortCode",
    "postalCode",
    "addressShortCode",
    "contactName",
]

SKIP_LABELS = ["cw1Name", "id", "environment", "profileName", "masterId"]


def detectCompanyByEmail(definitions):
    try:
        key_definitions = definitions[0]["key"]
        key_model = key_definitions["models"][0]
        if key_model:
            output = key_model.get("detectCompanyByEmail")
        return bool(output)
    except:
        pass


def trim_address_by_country_trigger(definitions):
    try:
        key_definitions = definitions[0]["key"]
        key_model = key_definitions["models"][0]
        if key_model:
            output = key_model.get("trimAddressTillCountry")
        return bool(output)
    except:
        pass


def process_keyNode(
    keyNode,
    keyNode_idx,
    inner_child_idx,
    extraData,
    master_dictionaries,
    definitions,
    address_keys,
    project,
):
    try:
        address_type = False
        inner_child_list = list()
        label = keyNode["label"]
        text = keyNode["v"]
        if keyNode["type"] == "key_detail_robot":
            inner_children_type = "keyTextDetailRobot"
        elif keyNode["type"] == "key_detail_static":
            inner_children_type = "keyTextDetailStatic"
        else:
            inner_children_type = "keyTextDetail"

        if any(address_key == label for address_key in address_keys):
            address_type = True
            # print(address_keys,child_dict["label"])

            try:
                if type(text) == list:
                    text = "\n".join(text)
                try:
                    # Code added on Nov 16, 2024 by Emon
                    try:
                        if project == "Freight":
                            text = translate_spanish_to_english(
                                text, master_dictionaries
                            )
                    except:
                        pass
                    if trim_address_by_country_trigger(definitions):
                        text = trim_address(text)
                        print("Trim Address By Country triggered")
                    if detectCompanyByEmail(definitions):
                        text = detect_company_by_email_and_rearrange(text)

                    text = custom_address_parser(
                        text, definitions, master_dictionaries, project=project
                    )
                except:
                    print(traceback.print_exc())
                    name = text
                    try:
                        name = name.split()[0]
                    except:
                        print(traceback.print_exc())
                        pass

                    text = {"name": text, "block": text}
            except:
                print(traceback.print_exc())
                pass
        if address_type:
            if not text:
                line_inner_idx = "keyTextDetail_" + str(inner_child_idx)
                inner_child_list.append(
                    {
                        "type": inner_children_type,
                        "label": "",
                        "id": line_inner_idx,
                        "v": "",
                        "children": [],
                    }
                )
                inner_child_idx += 1
            else:
                if type(text) == str:
                    text_lines = text.splitlines()

                    for line in text_lines:
                        line_inner_idx = "keyTextDetail_" + str(inner_child_idx)
                        inner_child_list.append(
                            {
                                "type": inner_children_type,
                                "label": "",
                                "id": line_inner_idx,
                                "v": line,
                                "children": [],
                            }
                        )
                        inner_child_idx += 1

                elif type(text) == list:
                    for line in text:
                        line_inner_idx = "keyTextDetail_" + str(inner_child_idx)

                        inner_child_list.append(
                            {
                                "type": inner_children_type,
                                "label": "",
                                "id": line_inner_idx,
                                "v": line,
                                "children": [],
                            }
                        )
                        inner_child_idx += 1

                elif type(text) == dict:
                    for keyData, valueData in text.items():
                        if keyData not in TO_BE_KEPT_INSIDE:
                            data = {
                                "label": keyData,
                                "v": valueData,
                                "unique_id": keyNode["unique_id"],
                                "insert_position": keyNode_idx,
                                "pos": keyNode["pos"],
                                "pageId": keyNode["pageId"],
                            }
                            extraData.append(data)

                        else:
                            line_inner_idx = "keyTextDetail_" + str(inner_child_idx)

                            inner_child_list.append(
                                {
                                    "type": inner_children_type,
                                    "label": keyData,
                                    "id": line_inner_idx,
                                    "v": valueData,
                                    "children": [],
                                }
                            )
                            inner_child_idx += 1
        keyNode["children"] = inner_child_list
        # print("="*25)
        # print(keyNode)
        # print("="*25)
        return keyNode
    except:
        print(f"Error inside the process_keyNode function for keyNode -> {keyNode}")
        pass


def key_child_appender_process(
    d_json, address_keys, definitions, request_data, project
):
    # Updated on 19/10/2022 - Added children empty node
    # Updated on 24/10/2022 - Added locationcode exception
    """
    This function primarily adds address child items to the keynodes
    and leaves rest of the keynodes with an empty children array

    """

    inner_child_idx = 0
    docs = d_json["nodes"]
    master_dictionaries = request_data.get("master_dictionaries")

    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if (
                not node_children
            ):  # Bug fix by emon on 01/08/2022- @Emon Caterpillar Multiple Document Batch Test Document Button Fail Issue
                continue
            if "key" in node["type"]:
                extraData = list()
                threads = []
                has_key_node_children = False
                for keyNode_idx, keyNode in enumerate(node_children):
                    if keyNode.get("isCompoundKey") == True:
                        continue
                    # If auto extraction has children automatically created.
                    elif len(keyNode.get("children",[])) > 0:
                        has_key_node_children = True
                    else:
                        if keyNode.get("v",None):
                            thread = threading.Thread(
                                target=process_keyNode,
                                args=(
                                    keyNode,
                                    keyNode_idx,
                                    inner_child_idx,
                                    extraData,
                                    master_dictionaries,
                                    definitions,
                                    address_keys,
                                    project,
                                ),
                            )
                            threads.append(thread)

                    node_children[keyNode_idx] = keyNode
                if not has_key_node_children:
                    for thread in threads:
                        try:
                            thread.start()
                        except Exception as e:
                            print(f"Failed to start thread: {e}")

                    for thread in threads:
                        try:
                            thread.join()
                        except Exception as e:
                            print(f"Failed to join thread: {e}")
                    try:
                        if extraData:
                            for extra in extraData:
                                extra_keyNode = create_key_node(extra)
                                node_children.insert(
                                    extra["insert_position"], extra_keyNode
                                )
                    except:
                        print(traceback.print_exc())
                        pass

                    nodes[i]["children"] = node_children

        docs[input_doc_idx]["children"] = nodes
    d_json["nodes"] = docs

    return d_json
