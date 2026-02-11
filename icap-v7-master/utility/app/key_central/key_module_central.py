import math
import operator
import os
import re
import string
import traceback
from datetime import date

import requests
from fuzzywuzzy import fuzz
from redis_utils import get_redis_data

from app.extraction_modules.regex_extractor import regex_extractor_function
from app.extraction_modules.selector import get_value_pos_from_list, selector_function
from app.extraction_modules.value_directed_script import valueDirected_command
from app.key_central.awb_scripts.auto_extractor import auto_extractor, chunk_process

from ..common_dictionary import unwanted_chars
from ..response_formator import populate_error_response

"""
This script is a part of a larger application that extracts data from documents. It takes in a list of keys (data fields to be extracted), a request with document details, and an index of the target document. The script then calls various extraction modules to find the values corresponding to each key in the document.

The extraction modules include:

1. Selector Tool: Allows the user to manually select an area on the document for extraction.
2. Anchor Tool: Extracts data based on predefined anchor points or patterns in the document.
3. Static Tool: Returns a static value provided by the user.
4. Today Tool: Returns the current date.
5. Auto Tool: Automatically extracts common data fields like supplier, importer, origin, destination, goods description, etc. from airway bills.
6. Regex Extractor: Extracts data using regular expressions.
7. Single Column Extractor: Extracts data from a single column in the document.
8. Barcode Extractor: Extracts barcode data from the document.
9. Keys Tool: Extracts data based on user-provided keywords or phrases.

The script processes each key, calls the appropriate extraction module based on the key type, and assembles the extracted data into a structured format. It handles various cases like multiple occurrences, grouping, and duplicate removal. Finally, it returns the extracted data and any error messages.

In summary, this script acts as a central component that coordinates the extraction of data from documents using different techniques based on user input and document characteristics.

"""


DOCBUILDER_API_URL = os.getenv("DOCBUILDER_API_URL")


def get_left_pos(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos(pos):
    return int(pos.split(",", 3)[3])


def generate_single_col_ra_json(input_ra_json, input_doc_idx):
    """Generate ra json with specific input document index"""

    ra_json_children = input_ra_json["nodes"][input_doc_idx]
    input_ra_json["nodes"] = [ra_json_children]
    return input_ra_json


def get_value_pos_from_list(input_list):
    all_left = []
    all_top = []
    all_right = []
    all_bottom = []
    for v in input_list:
        all_left.append(get_left_pos(v))
        all_top.append(get_top_pos(v))
        all_right.append(get_right_pos(v))
        all_bottom.append(get_bottom_pos(v))

    output_left = str(min(all_left))
    output_top = str(min(all_top))
    output_right = str(max(all_right))
    output_bottom = str(max(all_bottom))
    output_pos = (
        output_left + "," + output_top + "," + output_right + "," + output_bottom
    )
    return output_pos


def closest_key_val_pair_text(key_val_match_holder, key):
    if len(key_val_match_holder) == 1:
        return key_val_match_holder[0]["text"]
    key_left = int(key["startPos"])
    key_top = int(key["topPos"])
    check_distance_list = list()
    try:
        for i, key_val in enumerate(key_val_match_holder):
            chunk_pos = key_val[-1]
            chunk_left = get_left_pos(chunk_pos)
            chunk_top = get_top_pos(chunk_pos)
            x1, y1, x2, y2 = key_left, key_top, chunk_left, chunk_top
            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            check_distance_list.append([i, dist])
        check_distance_list = sorted(check_distance_list, key=operator.itemgetter(1))
        selected_dist_pair = check_distance_list[0]
        selected_block_idx = selected_dist_pair[0]
        return key_val_match_holder[selected_block_idx]["text"]
    except:
        return key_val_match_holder[0]["text"]


def check_if_inside_any_potential_block(input_block, key):
    try:
        block_pos = input_block["pos"]
        block_left = get_left_pos(block_pos)
        block_top = get_top_pos(block_pos)
        block_right = get_right_pos(block_pos)
        block_bottom = get_bottom_pos(block_pos)

        key_left = int(key["startPos"])
        key_top = int(key["topPos"])
        key_right = int(key["endPos"])
        key_bottom = int(key["bottomPos"])
        if (
            (key_left >= block_left)
            and (key_right <= block_right)
            and (key_top >= block_top)
            and (key_bottom <= block_bottom)
        ):
            return True
    except:
        pass

    return False


def get_the_closest_block(input_blocks, key):
    key_left = int(key["startPos"])
    key_top = int(key["topPos"])

    check_distance_list = list()
    try:
        for i, block in enumerate(input_blocks):
            check = block["text"].replace(key["shape"], "")
            if all(i in string.punctuation for i in check):
                continue
            block_pos = block["pos"]
            block_left = get_left_pos(block_pos)
            block_top = get_top_pos(block_pos)
            x1, y1, x2, y2 = key_left, key_top, block_left, block_top
            dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            check_distance_list.append([i, dist])
        check_distance_list = sorted(check_distance_list, key=operator.itemgetter(1))
        try:
            selected_dist_pair = check_distance_list[0]
        except:
            return input_blocks[0]
        if selected_dist_pair[1] < 600:
            selected_block_idx = selected_dist_pair[0]
            return input_blocks[selected_block_idx]
    except:
        print(traceback.print_exc())
        print("Error in keyvalue extractor")
        print("For key ", key["shape"], "multiple_blocks were detected by none close")


def get_rest_string(up_to_word, key, copied_block, single_line_mode):
    rx_to_first = r"^.*?{}".format(re.escape(up_to_word))
    text = re.sub(rx_to_first, "", copied_block["text"], flags=re.DOTALL).strip()

    if single_line_mode:
        text = text.split('\n')[0]

    # colon removal
    if text[0] == ":":
        text = text[1:].strip()
    for c in unwanted_chars:
        if c in text:
            text = text.replace(c, "")

    # added by emon on 19/05/2022
    if key["keyLabel"] == "references":
        first_line = text.splitlines()[0]
        if first_line[0] == ":":
            first_line = first_line[1:]
        text = first_line.strip()
    return text


def remove_duplicates(dictionaries):
    seen = set()
    result = []
    for d in dictionaries:
        if d["text"] not in seen:
            seen.add(d["text"])
            result.append(d)
    return result


# Extracting anchor thresholds from key
def extract_anchor_thresholds(request_data):
    """Extracts thresholds related to anchors"""
    chunking_thresholds = dict()
    try:
        definitions = request_data.get("definitions", [])
        key_model = definitions[0]["key"]["models"][0] if definitions else {}

        attributes_to_check_for = [
            "anchorChunkThreshold",
            "anchorLineThreshold",
            "anchorExtraChunkSpace",
        ]
        for a in attributes_to_check_for:
            if key_model.get(a):
                fieldName = a.replace("anchor", "")
                fieldName = fieldName[0].lower() + fieldName[1:]
                chunking_thresholds[fieldName] = key_model.get(a)
    except:
        # print(traceback.print_exc())
        pass

    return chunking_thresholds


def filter_positional_duplicates(input_list):
    """Function to remove duplicate key value pairs in a list which are the same pixel positions of the page
    This error is present due to chunking threshold problems and removing them downstream is a patch up.
    The input here is a list of dictionaries and the output is the duplicate removed list of dictionaries
    """

    filtered_extracted_block_list = list()
    existing_dicts = set()
    for d in input_list:
        if d["pos"] not in existing_dicts:
            existing_dicts.add(d["pos"])
            filtered_extracted_block_list.append(d)

    return filtered_extracted_block_list


AWB_BATCH_DATA = {}
AWB_BATCH_DATA_WORD_ONLY = {}


def extraction_tools_request(
    input_query_key_list, request_data, input_doc_idx, messages
):
    """
    Primary function that calls different extraction modules and created blocks (As in block of data containing the value,
    position, pageId, type, titile of the target text) and assembles them all inside a key node dictionary and returns it

    """

    ra_json = request_data["ra_json"]
    job_id = request_data["job_id"]
    query_shape_list = []
    d_json = request_data["data_json"]
    target_doc = d_json["nodes"][input_doc_idx]
    # Get Document Type
    document_id = target_doc["id"]
    doc_type = target_doc["DocType"]
    project_type = request_data["project"]
    AWB = False
    if doc_type == "Airway Bill":
        AWB = True
        AWB_BATCH_DATA, batch_data_word_only = chunk_process(ra_json)

    master_dictionaries = request_data.get("master_dictionaries")
    try:
        awb_key_data = master_dictionaries.get("awb_key_data").get("data")
    except:
        awb_key_data = None

    query_key_list = input_query_key_list.copy()

    nodes = target_doc["children"]
    blocks = None
    for node in nodes:
        if "blocks" in node["id"].lower():
            blocks = node["children"]

    done_labels = []
    results = list()
    extraction_fails = list()

    # For anchors
    json_chunking_thresholds = extract_anchor_thresholds(request_data)
    input_dict = get_redis_data(job_id).get("chunking_dictionary")

    single_line_mode = False
    definition_settings = request_data["definition_settings"]
    jap_eng_convert_profiles = definition_settings["profileSettings"].get(
        "jap_eng_convert_profiles", []
    )
    profile_name = d_json["DefinitionID"]
    if profile_name in jap_eng_convert_profiles:
        single_line_mode = True

    for key in query_key_list:
        lookupcode = ""
        fieldName = key["keyLabel"]
        multiple_trigger = False
        remove_duplicate_trigger = False
        group_multiple_trigger = False
        group_multiples = False
        advanceSettings = key.get("advanceSettings")
        extractMultiple = key.get("extractMultiple")
        removeDuplicates = key.get("removeDuplicates")
        if extractMultiple:
            multiple_trigger = True
        if removeDuplicates:
            remove_duplicate_trigger = True
        try:
            if advanceSettings.get("groupMultiple"):
                group_multiples = True
                group_multiple_trigger = True
                group_multiple_separator = advanceSettings.get("groupMultipleSeparator")
        except:
            pass

        if key.get("qualifierValue"):
            lookupcode = fieldName

        try:
            if key.get("qualifierValue"):
                fieldName = key["qualifierValue"]
        except:
            pass
        if "keyLabel" in key.keys():
            keylabel = key["keyLabel"]
            if "pickUp" in keylabel:
                keylabel = keylabel.replace("pickUp", "pickup")
                key["keyLabel"] = keylabel
                fieldName = keylabel

        if "selector" in key.keys() and key["selector"] == True:
            pass
            # data_found = False
            # if "" in [
            #     key.get("startPos", ""),
            #     key.get("topPos", ""),
            #     key.get("endPos", ""),
            #     key.get("bottomPos", ""),
            #     key.get("pageId", ""),
            # ]:
            #     response = populate_error_response(
            #         data={},
            #         error=f"You didn't capture proper area for your selected key.",
            #         traceback="keyval_extractor.py had an error",
            #     )
            #     return response
            # extracted_block, selector_version = selector_function(
            #     key, input_doc_idx, job_id, input_dict
            # )
            # if extracted_block:
            #     data_found = True
            #     key_val_dict = dict()
            #     try:
            #         extracted_block["unique_id"] = key["id"]
            #     except:
            #         pass

            #     if lookupcode:
            #         extracted_block["qualifierParent"] = lookupcode

            #     extracted_block["advanceSettings"] = advanceSettings
            #     if key.get("export") == False:
            #         extracted_block["export"] = False
            #     elif key.get("export") == True:
            #         extracted_block["export"] = True
            #     key_val_dict[fieldName] = extracted_block
            #     results.append(key_val_dict)
            # try:
            #     # Emon added on 15/10/2022
            #     if not data_found:
            #         notFound_text = fieldName + " extraction fail"
            #         tool_doc = "Selector Tool-Doc#{:02}".format(input_doc_idx + 1)
            #         notFound_message = {
            #             "message": notFound_text,
            #             "code": 400,
            #             "module": tool_doc,
            #         }
            #         extraction_fails.append(notFound_message)
            # except:
            #     pass

        elif "type" in key.keys() and key["type"] == "anchors":
            try:
                previous_values = list()
                data_found = False
                anchor_results = list()
                anchor_values = list()
                anchor_pos = list()

                # Added by emon on 15/10/2022 #ANCHRORTRIGGERS01
                if not multiple_trigger:
                    extracted_block_list, anchor_version = valueDirected_command(
                        key,
                        ra_json,
                        input_doc_idx,
                        None,
                        json_chunking_thresholds,
                        job_id,
                        input_dict,
                    )
                    if extracted_block_list:
                        for extracted_block in extracted_block_list:
                            # Added by emon on 15/10/2022
                            if extracted_block:
                                data_found = True
                                try:
                                    extracted_block["unique_id"] = key["id"]
                                except:
                                    pass
                                key_val_dict = dict()

                                if lookupcode:
                                    extracted_block["qualifierParent"] = lookupcode

                                extracted_block["advanceSettings"] = advanceSettings
                                if key.get("export") == False:
                                    extracted_block["export"] = False
                                elif key.get("export") == True:
                                    extracted_block["export"] = True
                                key_val_dict[fieldName] = extracted_block
                                # print("key_val_dict", key_val_dict)
                                anchor_results.append(key_val_dict)
                else:
                    # @Emon on 08/09/2022 - Multiple Trigger code added
                    # input_dict = get_redis_data(job_id)["chunking_dictionary"] # Input chunking dictionary
                    # Getting chunking data from the document in loop
                    values = input_dict[str(input_doc_idx)]
                    page_indexes = values["data"].keys()
                    block_count = 0

                    for page in page_indexes:
                        extracted_block_list, anchor_version = valueDirected_command(
                            key, ra_json, input_doc_idx, page, None, job_id, input_dict
                        )

                        extracted_block_list = filter_positional_duplicates(
                            extracted_block_list
                        )
                        block_count += 1
                        if extracted_block_list:
                            for extracted_block in extracted_block_list:
                                if extracted_block:
                                    if remove_duplicate_trigger:
                                        if extracted_block["text"] in previous_values:
                                            extracted_block = None
                                        else:
                                            previous_values.append(
                                                extracted_block["text"]
                                            )

                                if extracted_block:
                                    data_found = True
                                    try:
                                        extracted_block["unique_id"] = key["id"]
                                    except:
                                        pass

                                    key_val_dict = dict()
                                    if lookupcode:
                                        extracted_block["qualifierParent"] = lookupcode
                                    extracted_block["originates_from_multiples"] = True
                                    extracted_block["advanceSettings"] = advanceSettings
                                    if key.get("export") == False:
                                        extracted_block["export"] = False
                                    elif key.get("export") == True:
                                        extracted_block["export"] = True
                                    key_val_dict[fieldName] = extracted_block
                                    # print("key_val_dict", key_val_dict)
                                    anchor_results.append(key_val_dict)
                try:
                    if not data_found:  # Emon added on 15/10/2022
                        notFound_text = fieldName + " extraction Fail"
                        tool_doc = "Anchor Tool-Doc#{:02}".format(input_doc_idx + 1)
                        notFound_message = {
                            "message": notFound_text,
                            "code": 400,
                            "module": tool_doc,
                        }
                        extraction_fails.append(notFound_message)
                except:
                    pass
                if group_multiple_trigger or remove_duplicate_trigger:
                    try:
                        if group_multiple_trigger:
                            for anchor_result in anchor_results:
                                value = anchor_result[fieldName]["text"]
                                pos = anchor_result[fieldName]["pos"]
                                if remove_duplicate_trigger:
                                    if value not in anchor_values:
                                        anchor_pos.append(pos)
                                        anchor_values.append(value)
                                else:
                                    anchor_values.append(value)
                                    anchor_pos.append(pos)

                            anchor_value = group_multiple_separator.join(anchor_values)
                            anchor_results = anchor_results[0]
                            anchor_results[fieldName]["text"] = anchor_value
                            anchor_results[fieldName]["pos"] = get_value_pos_from_list(
                                anchor_pos
                            )
                            results.append(anchor_results)

                        elif remove_duplicate_trigger:
                            for anchor_result in anchor_results:
                                value = anchor_result[fieldName]["text"]
                                if value not in anchor_values:
                                    results.append(anchor_result)
                                anchor_values.append(value)
                    except:
                        print(traceback.print_exc())
                        pass

                else:
                    for anchor_result in anchor_results:
                        results.append(anchor_result)

            except:
                print(traceback.print_exc())
                pass

        elif "type" in key.keys() and key["type"] == "static":
            extracted_block = dict()
            if key["shape"]:
                try:
                    extracted_block["unique_id"] = key["id"]
                except:
                    pass

                extracted_block["text"] = key["shape"]
                extracted_block["pos"] = ""
                extracted_block["pageId"] = ""
                extracted_block["title"] = "static"
                extracted_block["STATUS"] = 111
                key_val_dict = dict()
                if lookupcode:
                    extracted_block["qualifierParent"] = lookupcode
                extracted_block["advanceSettings"] = advanceSettings
                if key.get("export") == False:
                    extracted_block["export"] = False
                elif key.get("export") == True:
                    extracted_block["export"] = True
                key_val_dict[fieldName] = extracted_block

                results.append(key_val_dict)
        elif key.get("type") == "today":
            extracted_block = dict()
            try:
                extracted_block["unique_id"] = key["id"]
                today = date.today()
                extracted_block["text"] = today.strftime("%m/%d/%Y")
                extracted_block["pos"] = ""
                extracted_block["pageId"] = ""
                extracted_block["title"] = "today"
                extracted_block["STATUS"] = 111
                key_val_dict = dict()
                if lookupcode:
                    extracted_block["qualifierParent"] = lookupcode
                extracted_block["advanceSettings"] = advanceSettings
                if key.get("export") == False:
                    extracted_block["export"] = False
                elif key.get("export") == True:
                    extracted_block["export"] = True
                key_val_dict[fieldName] = extracted_block
                results.append(key_val_dict)
            except:
                print(traceback.print_exc())

        elif key.get("type") == "auto":
            discontinue = False
            key_data = None
            if "supplier" in fieldName.lower():
                key_data = awb_key_data.get("supplier_key_data")

            if "importer" in fieldName.lower():
                key_data = awb_key_data.get("importer_key_data")

            if "originlocationname" in fieldName.lower():
                key_data = awb_key_data.get("origin_name_key_data")

            if "destinationlocationname" in fieldName.lower():
                key_data = awb_key_data.get("destination_name_key_data")

            if "goods" in fieldName.lower():
                key_data = awb_key_data.get("goodsDescription_key_data")

            if "airline" in fieldName.lower():
                key_data = awb_key_data.get("flight_data_key_data")

            if "housebill" in fieldName.lower():
                key_data = awb_key_data.get("housebill_key_data")

            if "masterbill" in fieldName.lower():
                key_data = awb_key_data.get("masterbill_key_data")

            if not key_data:
                discontinue = True
            if not discontinue:
                extraction_data = None
                extracted_block = dict()
                try:
                    extraction_data = auto_extractor(
                        AWB_BATCH_DATA, document_id, key_data
                    )
                except:
                    print(traceback.print_exc())

                if extraction_data:
                    extracted_block["text"] = extraction_data["text"]
                    extracted_block["pageId"] = extraction_data["pageId"]
                    extracted_block["pos"] = extraction_data["pos"]
                    extracted_block["title"] = extraction_data["title"]
                    extracted_block["title"] = "auto"
                    extracted_block["STATUS"] = 0
                    extracted_block["unique_id"] = key["id"]
                    key_val_dict = dict()
                    if lookupcode:
                        extracted_block["qualifierParent"] = lookupcode
                    extracted_block["advanceSettings"] = advanceSettings

                    if key.get("export"):
                        extracted_block["export"] = True
                    else:
                        extracted_block["export"] = False
                    key_val_dict[fieldName] = extracted_block
                    results.append(key_val_dict)

        elif key.get("type") == "regexExtractor":
            
            # # Read the three dot trigger for Grab Multi Line
            # # Pass it into the function below
            grab_extra_trigger = None
            # grab_extra_trigger = {"v": "1"}
            if key["advanceSettings"].get("grabMultiLines") == True:
                grab_extra_trigger = key["advanceSettings"]
            result, regex_failed, regex_version = regex_extractor_function(
                key, input_doc_idx, job_id, input_dict, project_type, grab_extra_trigger
            )

            if result:
                if remove_duplicate_trigger:
                    result = remove_duplicates(result)

                separator = "," + " "
                if group_multiple_trigger:
                    separator = group_multiple_separator + " "

                if separator == "\\n":
                    separator = "\n"

                if group_multiples:
                    # Added by emon on 18/04/2023 - Group Multiple Button for Regex
                    extracted_block = dict()

                    extracted_block["unique_id"] = key["id"]
                    extracted_block["pos"] = get_value_pos_from_list(
                        [x["pos"] for x in result]
                    )
                    extracted_block["pageId"] = result[0]["pageId"]
                    extracted_block["text"] = separator.join(
                        [x["text"] for x in result]
                    )
                    extracted_block["advanceSettings"] = advanceSettings
                    if key.get("export") == False:
                        extracted_block["export"] = False
                    elif key.get("export") == True:
                        extracted_block["export"] = True
                    extracted_block["title"] = "regexExtractor"
                    if lookupcode:
                        extracted_block["qualifierParent"] = lookupcode
                    key_val_dict = dict()
                    key_val_dict[fieldName] = extracted_block
                    results.append(key_val_dict)

                else:
                    multiple = False
                    if len(result) > 1:
                        multiple = True
                    for extracted_block in result:
                        if lookupcode:
                            extracted_block["qualifierParent"] = lookupcode

                        extracted_block["originates_from_multiples"] = multiple
                        extracted_block["unique_id"] = key["id"]
                        key_val_dict = dict()
                        extracted_block["advanceSettings"] = advanceSettings
                        if key.get("export") == False:
                            extracted_block["export"] = False
                        elif key.get("export") == True:
                            extracted_block["export"] = True
                        extracted_block["title"] = "regexExtractor"
                        key_val_dict[fieldName] = extracted_block
                        results.append(key_val_dict)
            if not result:
                if regex_failed == True:
                    notFound_text = fieldName + " regex Fail"
                    tool_doc = "Regex Tool-Doc#{:02}".format(input_doc_idx + 1)
                    notFound_message = {
                        "message": notFound_text,
                        "code": 400,
                        "module": tool_doc,
                    }
                    extraction_fails.append(notFound_message)
                else:
                    notFound_text = fieldName + " extraction Fail"
                    tool_doc = "Regex Tool-Doc#{:02}".format(input_doc_idx + 1)
                    notFound_message = {
                        "message": notFound_text,
                        "code": 400,
                        "module": tool_doc,
                    }
                    extraction_fails.append(notFound_message)

        elif key.get("isCompoundKey") == True:
            pass
        elif key.get("type") == "cellRange":
            pass

        elif key.get("type") == "excelRegexExtractor":
            pass

        elif key.get("type") == "singleColumn":
            try:
                discontinue = False
                try:
                    input_ra_json = ra_json.copy()
                    doc_level_ra_json = generate_single_col_ra_json(
                        input_ra_json, input_doc_idx
                    )
                except:
                    print(traceback.print_exc())
                    discontinue = True

                if not discontinue:
                    request_data_copied = dict()
                    request_data_copied["definitions"] = request_data.get("definitions")
                    request_data_copied["ra_json"] = doc_level_ra_json

                    # extracted_data = send_request()
                    url = f"{DOCBUILDER_API_URL}/single_col_extractor"
                    data = {"input_data": key, "input_ra_json": request_data_copied}

                    # print(url)
                    # print(data)

                    extracted_data = None
                    try:
                        extracted_data = (
                            requests.post(url, json=data).json().get("data")
                        )
                    except:
                        print(traceback.print_exc())
                        pass

                    # print(extracted_data)

                    # group_multiples = False
                    # if advanceSettings.get("groupMultiple"):
                    #     group_multiples = True
                    #     if advanceSettings.get("groupMultipleSeparator"):
                    #         separator = advanceSettings.get("groupMultipleSeparator") + " "
                    #     else:
                    #         separator = "," + " "

                    group_multiples = advanceSettings.get("groupMultiple", False)
                    separator = advanceSettings.get("groupMultipleSeparator")

                    if group_multiples and separator:
                        separator = separator + " "
                    else:
                        separator = ", "

                    # group_multiples = advanceSettings.get("groupMultiple", False)
                    # separator = advanceSettings.get("groupMultipleSeparator", ", ")

                    # if group_multiples and separator:
                    #     separator += " "

                    if extracted_data:
                        duplicate_check_list = list()
                        done = set()
                        result = []

                        for d in extracted_data:
                            if d["v"] not in done:
                                done.add(d["v"])
                                result.append(d)

                        cleaned_result = [x for x in result if x.get("label")]

                        if group_multiples:
                            # Added by emon on 13/03/2023 - Group Multiple Button
                            extracted_block = dict()
                            extracted_block["unique_id"] = key["id"]
                            extracted_block["pos"] = get_value_pos_from_list(
                                [x["pos"] for x in cleaned_result]
                            )
                            extracted_block["pageId"] = cleaned_result[0]["page_id"]
                            extracted_block["text"] = separator.join(
                                [x["v"] for x in cleaned_result]
                            )
                            extracted_block["title"] = "singleColumn"
                            extracted_block["advanceSettings"] = advanceSettings
                            if key.get("export") == False:
                                extracted_block["export"] = False
                            elif key.get("export") == True:
                                extracted_block["export"] = True
                            if lookupcode:
                                extracted_block["qualifierParent"] = lookupcode
                            key_val_dict = dict()
                            key_val_dict[fieldName] = extracted_block
                            results.append(key_val_dict)

                        else:
                            for x in cleaned_result:
                                extracted_block = dict()
                                extracted_block["unique_id"] = key["id"]
                                extracted_block["text"] = x["v"]
                                extracted_block["pos"] = x["pos"]
                                extracted_block["pageId"] = x["page_id"]
                                extracted_block["title"] = "singleColumn"
                                if len(cleaned_result):
                                    extracted_block["originates_from_multiples"] = True
                                extracted_block["advanceSettings"] = advanceSettings
                                if lookupcode:
                                    extracted_block["qualifierParent"] = lookupcode
                                if key.get("export") == False:
                                    extracted_block["export"] = False
                                elif key.get("export") == True:
                                    extracted_block["export"] = True
                                key_val_dict = dict()
                                key_val_dict[fieldName] = extracted_block
                                results.append(key_val_dict)
            except:
                print(traceback.print_exc())
                pass

        elif key.get("type") == "barcode":
            try:
                extracted_block = dict()
                target_doc = ra_json["nodes"][input_doc_idx]
                extracted_block["advanceSettings"] = advanceSettings
                typeData = key.get("typeData")
                barcode_index = int(typeData.get("barcodeIndex")) - 1
                barcode_identifier = "GetBarCode" + str(barcode_index)
                barcode_text = target_doc["children"][0][barcode_identifier]
                extracted_block["unique_id"] = key["id"]
                extracted_block["text"] = barcode_text
                extracted_block["pageId"] = ""
                extracted_block["pos"] = target_doc["children"][0][
                    "Position" + str(barcode_index)
                ]
                extracted_block["title"] = "barcode"
                if lookupcode:
                    extracted_block["qualifierParent"] = lookupcode
                key_val_dict = dict()
                key_val_dict[fieldName] = extracted_block
                if key.get("export") == False:
                    extracted_block["export"] = False
                elif key.get("export") == True:
                    extracted_block["export"] = True
                results.append(key_val_dict)

            except:
                print(traceback.print_exc())

                pass

        else:
            if not blocks:
                # print("Blocks not produced for document id" + " " + d_json["id"])
                continue
            data_found = False
            find_count = 0
            multiple_blocks_storage = []
            query_shape_list.append(key["shape"])
            key_val_dict = dict()
            for block in blocks:
                # checking if pipe is inside key shape
                if "|" in key["shape"]:
                    shape_list = key["shape"].split("|")
                    if find_count > 0:
                        break
                    else:
                        # print("initial count ",find_count, " ----", key["shape"])
                        # checking for each shape in pipe
                        for pipe_idx, pipe_shape in enumerate(shape_list):
                            multiple_storage_for_pipe = []
                            # checking if that shape is in any text field of a block
                            for c in unwanted_chars:
                                if c in pipe_shape:
                                    pipe_shape = pipe_shape.replace(c, "")
                            if pipe_shape.lower() in block["text"].lower():
                                multiple_storage_for_pipe.append(block)

                            # final block placeholder to check
                            final_block = None
                            # checking distance
                            if len(multiple_storage_for_pipe) == 1:
                                final_block = multiple_storage_for_pipe[0]
                            elif len(multiple_storage_for_pipe) > 1:
                                for single_block in multiple_storage_for_pipe:
                                    # replacing positions by associated pipe indexes
                                    pipe_shape["startPos"] = key["startPos"].split("|")[
                                        pipe_idx
                                    ]
                                    pipe_shape["endPos"] = key["endPos"].split("|")[
                                        pipe_idx
                                    ]
                                    pipe_shape["topPos"] = key["topPos"].split("|")[
                                        pipe_idx
                                    ]
                                    pipe_shape["bottomPos"] = key["bottomPos"].split(
                                        "|"
                                    )[pipe_idx]
                                    found_inside_the_blocks = []
                                    if check_if_inside_any_potential_block(
                                        single_block, pipe_shape
                                    ):
                                        found_inside_the_blocks.append(single_block)
                                    if len(found_inside_the_blocks) > 1:
                                        final_block = get_the_closest_block(
                                            found_inside_the_blocks, key
                                        )
                                    else:
                                        if found_inside_the_blocks:
                                            final_block = found_inside_the_blocks[0]
                                    if not final_block:
                                        final_block = get_the_closest_block(
                                            multiple_blocks_storage, key
                                        )

                            if final_block:
                                copied_block = final_block.copy()
                                # checking if key value data atrribute is there
                                if "key_val_data" in final_block.keys():
                                    for key_data in copied_block["key_val_data"]:
                                        for key_in_pair, value_in_pair in key_data[
                                            "pair"
                                        ].items():
                                            if pipe_shape[-1] == ":":
                                                pipe_shape = pipe_shape[:-1]
                                            if (
                                                pipe_shape.lower()
                                                in key_in_pair.lower()
                                                or (
                                                    fuzz.ratio(pipe_shape, key_in_pair)
                                                    > 90
                                                )
                                            ):
                                                if "M3" in key_in_pair:
                                                    text = "M3 " + text
                                                text = value_in_pair.strip()
                                                if text[0] == ":":
                                                    text = text[1:]
                                                copied_block["text"] = text
                                else:
                                    # if key value data is not there taking directly from matched text field
                                    try:
                                        copied_block["text"] = get_rest_string(
                                            pipe_shape, key, copied_block, single_line_mode
                                        )
                                    except:
                                        print(traceback.print_exc())
                                        pass

                                # checking if the queried shape contains at qualifer value
                                if copied_block["text"] and find_count == 0:
                                    copied_key = key.copy()
                                    try:
                                        copied_block["unique_id"] = key["id"]
                                    except:
                                        pass
                                    if lookupcode:
                                        copied_block["qualifierParent"] = lookupcode

                                    copied_block["advanceSettings"] = advanceSettings
                                    if key.get("export") == False:
                                        copied_block["export"] = False
                                    elif key.get("export") == True:
                                        copied_block["export"] = True
                                    key_val_dict[fieldName] = copied_block

                                    if fieldName not in done_labels:
                                        results.append(key_val_dict)
                                        find_count = find_count + 1
                                        data_found = True
                                        # print('changed count ',
                                        #       find_count)
                                        done_labels.append(fieldName)
                else:
                    try:
                        shape = key.get("shape")
                        if shape and shape[-1] == ":":
                            key["shape"] = key["shape"][:-1]

                        for c in unwanted_chars:
                            if c in key["shape"]:
                                key["shape"] = key["shape"].replace(c, "")

                        # checking if that shape is in any text field of a block
                        if key["shape"].lower() in block["text"].lower():
                            multiple_blocks_storage.append(block)
                    except:
                        response = populate_error_response(
                            data={},
                            error=f"You didn't select key.",
                            traceback=traceback.print_exc(),
                        )
                        return response

            if multiple_blocks_storage:
                final_block = None

                if len(multiple_blocks_storage) == 1:
                    final_block = multiple_blocks_storage[0]

                elif len(multiple_blocks_storage) > 1:
                    found_inside_the_blocks = []
                    for single_block in multiple_blocks_storage:
                        if check_if_inside_any_potential_block(single_block, key):
                            found_inside_the_blocks.append(single_block)
                    if len(found_inside_the_blocks) > 1:
                        final_block = get_the_closest_block(
                            found_inside_the_blocks, key
                        )
                    else:
                        if found_inside_the_blocks:
                            final_block = found_inside_the_blocks[0]
                    if not final_block:
                        final_block = get_the_closest_block(
                            multiple_blocks_storage, key
                        )

                if final_block:
                    copied_block = final_block.copy()
                    # checking if key value data atrribute is there
                    if "key_val_data" in final_block.keys():
                        key_val_match_holder = list()
                        for key_data in copied_block["key_val_data"]:
                            for key_in_pair, value_in_pair in key_data["pair"].items():
                                if key["shape"][-1] == ":":
                                    key["shape"] = key["shape"][:-1]

                                for c in unwanted_chars:
                                    if c in key["shape"]:
                                        key["shape"] = key["shape"].replace(c, "")

                                if (key["shape"].lower() in key_in_pair.lower()) or (
                                    fuzz.ratio(key["shape"], key_in_pair) > 90
                                ):
                                    text = value_in_pair.strip()

                                    if not text:
                                        continue

                                    if "M3" in key_in_pair:
                                        text = "M3 " + text

                                    if text[0] == ":":
                                        text = text[1:]
                                    for c in unwanted_chars:
                                        if c in text:
                                            text = text.replace(c, "")

                                    temp_dict = dict()
                                    temp_dict["pos"] = key_data["pos"]
                                    temp_dict["text"] = text
                                    key_val_match_holder.append(temp_dict)

                        if not key_val_match_holder:
                            try:
                                copied_block["text"] = get_rest_string(
                                    key["shape"], key, copied_block, single_line_mode
                                )
                            except:
                                print(traceback.print_exc())
                                pass
                        else:
                            # print(key_val_match_holder)
                            if (key_val_match_holder) == 1:
                                copied_block["text"] = key_val_match_holder[0]["text"]
                            else:
                                try:
                                    text = closest_key_val_pair_text(
                                        key_val_match_holder, key
                                    )
                                except:
                                    print(traceback.print_exc())
                                    pass
                                copied_block["text"] = text

                    else:
                        # if key value data is not there taking directly from matched text field
                        try:
                            copied_block["text"] = get_rest_string(
                                key["shape"], key, copied_block, single_line_mode
                            )
                        except:
                            pass

                    if copied_block["text"]:
                        try:
                            copied_block["unique_id"] = key["id"]
                        except:
                            pass
                        copied_key = key.copy()
                        if lookupcode:
                            copied_block["qualifierParent"] = lookupcode
                        copied_block["advanceSettings"] = advanceSettings
                        if key.get("export") == False:
                            copied_block["export"] = False
                        elif key.get("export") == True:
                            copied_block["export"] = True
                        key_val_dict[fieldName] = copied_block
                        results.append(key_val_dict)
                        data_found = True

            try:
                # Emon added on 15/10/2022
                if not data_found:
                    notFound_text = fieldName + " extraction fail"
                    tool_doc = "Keys Tool-Doc#{:02}".format(input_doc_idx + 1)
                    notFound_message = {
                        "message": notFound_text,
                        "code": 400,
                        "module": tool_doc,
                    }
                    extraction_fails.append(notFound_message)
            except:
                pass

    try:
        if extraction_fails:
            # Messages to be displayed on timeline
            lineSpace = {
                "message": "-----------------------------",
                "code": 400,
                "module": "Key Extraction",
            }
            try:
                if lineSpace != messages[-1]:
                    messages.append(lineSpace)
            except:
                pass

            for fail in extraction_fails:
                messages.append(fail)

            if lineSpace != messages[-1]:
                messages.append(lineSpace)
    except:
        print(traceback.print_exc())
        pass

    return results, messages


def get_new_checkbox_value_from_ra_json(ra_json):
    checkbox_values = ["FCL", "LCL", "BCN"]
    new_checkbox_value = None
    # Loop over ra_json
    nodes = ra_json["nodes"]
    for node in nodes:
        documents = node["children"]
        for document in documents:
            cell_data = document.get("cell_data", {})
            for key_cell_data, value_cell_data in cell_data.items():
                for column_key, column_value in value_cell_data.items():
                    if column_value.get("value", None) in checkbox_values:
                        new_checkbox_value = column_value.get("value", None)
                        return new_checkbox_value
    return new_checkbox_value


def update_shipment_type_key(d_json, request_data):
    ra_json = request_data["ra_json"]
    new_checkbox_value = get_new_checkbox_value_from_ra_json(ra_json)
    if not new_checkbox_value:
        return d_json
    try:
        definitions = request_data["definitions"]
    except:
        response = populate_error_response(
            data=d_json, error="definitions not found", traceback=traceback.print_exc()
        )
        return response
    try:
        definition_settings = request_data["definition_settings"]
        definition_id = definitions[0]["definition_id"]
        profile_settings = definition_settings.get("profileSettings")
        checkbox_settings = profile_settings.get("exception_excel_checkbox_profiles")
        for setting in checkbox_settings:
            # If does not exists in d_json just return it
            if setting.get("applicable_for") != "key":
                return d_json
            if setting.get("name") != definition_id:
                return d_json

    except Exception:
        print(traceback.print_exc())
        return d_json
    key_found = False
    nodes = d_json["nodes"]
    for node in nodes:
        documents = node["children"]
        for document in documents:
            if document.get("type") == "key":
                key_items = document["children"]
                for key_item in key_items:
                    if key_item.get("label") == "shipmentType":
                        key_found = True
                        key_item["v"] = new_checkbox_value
                if not key_found:
                    key_items.append(
                        {
                            "label": "shipmentType",
                            "pageId": "",
                            "pos": "",
                            "type": "key_detail_static",
                            "STATUS": 111,
                            "v": new_checkbox_value,
                            "block_type": "static",
                        }
                    )
    return d_json
