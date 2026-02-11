import copy
import re
import traceback
from urllib.parse import unquote

from app.address_modules.address_custom import custom_address_parser
from app.common_dictionary import MERGE_OUTPUT_TRIGGER_PROFILE_IDS
from app.rules_normalizers_module.sub_rules.remove_duplicates_from_string import (
    apply_remove_duplicates_from_string,
)

from ..alternator import output_alternator
from ..response_formator import populate_error_response

"""
Project specific output json creator that follows a schema
"""

DIM_LABELS = ["length", "width", "height", "dimensionsUom"]
TEMPERATURE_LABELS = [
    "requiresTemperatureControl",
    "requiredMinimum",
    "requiredMaximum",
    "temperatureUom",
]


def transform_hz_label(old_key):
    """Transform hazardous keys"""
    new_key = old_key

    if new_key == "imoClassCode":
        return "_IMOClassCode"

    if "goodsLinesHazardousMaterial" in new_key:
        new_key = new_key.replace("goodsLinesHazardousMaterial", "")
        new_key = new_key[0].lower() + new_key[1:]

    return new_key


ADDRESS_CHILD_DISREGARD_LIST = ["block", "country", "Attn", "Fax"]
BOOL_FIELDS = [
    "_DGFDeliver",
    "requiresTemperatureControl",
    "assembly",
    "_DGFInsure",
    "_DGFPickup",
    "destinationControlled",
]


def prepare_data(elem):
    output_dict = dict()
    child_key_name = elem["childKeyName"]
    child_key_value = elem["childKeyValue"]
    parent = elem["parent"]

    if "contact" in child_key_name:
        data = {transform_label(child_key_name): child_key_value}
        output_dict["contact"] = data

    elif child_key_name == "name":
        output_dict[child_key_name] = child_key_value

    elif child_key_name == "accountNumber":
        output_dict[child_key_name] = child_key_value

    elif child_key_name == "shortCode":
        output_dict["addressShortCode"] = child_key_value

    elif child_key_name == "dropMode":
        output_dict["dropMode"] = child_key_value

    else:
        output_dict["address"] = {child_key_name: child_key_value}

    return output_dict


def transform_glKey(input_label):
    """Converts labels according to cw1 format - Nest Specific"""
    if input_label == "temperatureUom":
        return "uom"

    return input_label


def transform_label(input_label):
    if "phone" in input_label.lower():
        return "phone"
    elif "email" in input_label.lower():
        return "email"
    elif "name" in input_label.lower():
        return "name"
    return input_label


def update_parent(parent_data, child_key_name, child_key_value):
    """Update a address parent key inside output json"""

    if type(parent_data) != dict:
        return parent_data

    new_json = parent_data.copy()

    disregard = False

    if child_key_name == "name":
        new_json[child_key_name] = child_key_value
        disregard = True
    elif child_key_name == "accountNumber":
        new_json[child_key_name] = child_key_value
        disregard = True

    elif child_key_name == "shortCode":
        new_json["addressShortCode"] = child_key_value
        disregard = True

    elif child_key_name == "dropMode":
        new_json["dropMode"] = child_key_value
        disregard = True

    elif "contact" in child_key_name:
        disregard = True
        if "contact" in new_json.keys():
            new_json["contact"].update(
                {transform_label(child_key_name): child_key_value}
            )
        else:
            new_json["contact"] = {transform_label(child_key_name): child_key_value}

    if not disregard:
        if "address" in new_json.keys():
            new_json["address"].update({child_key_name: child_key_value})
        else:
            new_json["address"] = {child_key_name: child_key_value}
    return new_json


def address_partial_function(address_block_partial, output_json):
    # initializing two lists for storage

    to_be_added = list()

    # Looping through the partial keyNames
    for key_name, value in address_block_partial.items():
        # regex to find out the first Uppercase index and splitting at it
        i = re.search("[A-Z]", key_name).start()
        if "pickUp" in key_name:
            child_key_name = key_name.replace("pickUp", "pickup")

        associated_parent_key_name, child_key_name = key_name[:i], key_name[i:]
        child_key_name = child_key_name[0].lower() + child_key_name[1:]

        if child_key_name == "addressShortCode":
            child_key_name = "shortCode"

        # checking if the parent key exists in output
        if associated_parent_key_name in output_json.keys() and type(output_json[associated_parent_key_name]) == dict:
            copied_dict = output_json[associated_parent_key_name].copy()

            # for multiple children for one parent we take data from the previous dict
            for label_data in to_be_added:
                if label_data["parent"] == associated_parent_key_name:
                    copied_dict = label_data["childKeyValue"]
            block_storage = copied_dict.get("block")
            # We pop[ the block and add it later on
            copied_dict.pop("block", None)

            # Storage for previous children of the addressBlock. This is done to maintain order
            new_dict = dict()
            for pre_key, pre_value in copied_dict.items():
                new_dict[pre_key] = pre_value

            new_dict = update_parent(new_dict, child_key_name, value)
            # if "contact" in child_key_name:
            #     data = { transform_label(child_key_name) : value }
            #     if not "contact" in new_dict.keys():
            #         new_dict["contact"] = data
            #     else:
            #         new_dict["contact"].update(data)

            # else:
            #     new_dict[child_key_name] = value

            # if block_storage:
            #     new_dict["block"] = block_storage

            data = {
                "parent": associated_parent_key_name,
                "childKeyName": child_key_name,
                "childKeyValue": new_dict,
                "type": "modification",
            }

            # Appending to the storage
            to_be_added.append(data)

        else:
            """if the parent address key does not exist in output json"""
            data = {
                "parent": associated_parent_key_name,
                "childKeyName": child_key_name,
                "childKeyValue": value,
                "type": "addition",
            }
            to_be_added.append(data)

    if to_be_added:
        for elem in to_be_added:
            if elem["type"] == "addition":
                child_key_name = elem["childKeyName"]
                child_key_value = elem["childKeyValue"]
                parent = elem["parent"]

                if child_key_name == "state":
                    child_key_name = "stateProvince"

                if parent in output_json.keys():
                    output_json[parent] = update_parent(
                        output_json[parent], child_key_name, child_key_value
                    )
                else:
                    data = {elem["childKeyName"]: elem["childKeyValue"]}
                    output_json[parent] = prepare_data(elem)
            else:
                output_json[elem["parent"]] = elem["childKeyValue"]

    return output_json


def tranform_underscore_fields(output_json):
    updated_fields = {
        "dgfDeliver": "_DGFDeliver",
        "undgNumber": "_UNDGNumber",
        "imoClassCode": "_IMOClassCode",
        "dgfAssignedIdentity": "_DGFAssignedIdentity",
        "dgfInsure": "_DGFInsure",
        "awbChargesDisplay": "_AWBChargesDisplay",
        "awbDimensionsDefaultOption": "_AWBDimensionsDefaultOption",
        "hawbSuppression": "_HAWBSuppression",
        "dgfPickup": "_DGFPickup",
    }
    return {
        updated_fields.get(field, field): value for field, value in output_json.items()
    }


def convert_to_Dtype(input_dict):
    """CONVERT STRING TO DIFFERENT DATA TYPES"""

    float_list = [
        "grossWeight",
        "volume",
        "length",
        "width",
        "height",
        "requiredMinimum",
        "requiredMaximum",
        "netWeight",
        "valueOfGoods",
        "insuranceValue",
        "totalChargeable",
        "loadingMeters",
    ]
    int_list = ["packageCount", "innerPackageCount"]

    for key, value in input_dict.items():
        if key in float_list:
            try:
                value = str(value)
                if "," in str(value) and "." not in str(value):
                    value = str(value).replace(",", ".")
                
                elif value.count(",") == 1 and value.count(".") == 1:
                    if value.index(".") > value.index(","):
                        value = value.replace(",", "")
                elif "*" in str(value):
                    value = value.replace("*", "")
                
                input_dict[key] = float(value)
                if key in ["length", "width", "height", "grossWeight", "volume"]:
                    input_dict[key] = round(input_dict[key], 3)
            except:
                print(traceback.print_exc())

        if key in int_list:
            try:
                if isinstance(value, str):
                    if value.count(",") == 1:
                        value = value.replace(",", ".")
                        input_dict[key] = int(round(float(value)))
                    else:
                        input_dict[key] = int(value)
                else:
                    input_dict[key] = int(value) if isinstance(value, int) else int(round(float(value)))
            except:
                try:
                    input_dict[key] = int(float(value))
                except:
                    pass

    return input_dict


def get_actual_parent(input_label, key_qualifiers_input, qualifier_parent):
    """This function is only triggered when copy value rule was placed and we have to
    validate the original qualifier_parent for the new label"""

    if qualifier_parent:
        for setting in key_qualifiers_input:
            name = setting["name"]
            if name == qualifier_parent:
                options = setting["options"]
                for option in options:
                    if input_label == option["value"]:
                        return qualifier_parent

    for setting in key_qualifiers_input:
        name = setting["name"]
        if qualifier_parent:
            if name == qualifier_parent:
                continue

        options = setting["options"]
        for option in options:
            if input_label == option["value"]:
                return name

    return None


def convert_goodsLines_value_formats(goods_lines):
    """CONVERT GOODSLINES VALUE TYPE FORMATS"""
    for goods_line in goods_lines:
        dim_data = dict()
        tbr = list()
        for key, value in goods_line.items():
            if key == "dimensions":
                if type(value) != dict:
                    tbr.append(key)
                else:
                    dim_data[key] = convert_to_Dtype(value)
                    tbr.append(key)
            elif key == "temperatures":
                dim_data[key] = convert_to_Dtype(value)
                tbr.append(key)

        if tbr:
            for key in tbr:
                goods_line.pop(key, None)

        goods_line = convert_to_Dtype(goods_line)
        if dim_data:
            goods_line.update(dim_data)

    return goods_lines


def convert_to_bool(input_value):
    try:
        if input_value.lower() == "true":
            return True
        else:
            return False
    except:
        return input_value


def update_bools(input_dict):
    """
    This function accepts a nested dictionary and converts specific key-value pairs to boolean values.
    """

    if isinstance(input_dict, dict):
        for key, value in input_dict.items():
            try:
                lowercase_key = key.lower()
                if lowercase_key in [field.lower() for field in BOOL_FIELDS]:
                    if isinstance(value, str):
                        input_dict[key] = convert_to_bool(value)
                    elif isinstance(value, dict):
                        update_bools(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                update_bools(item)
                elif isinstance(value, dict):
                    update_bools(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            update_bools(item)
            except:
                print(traceback.print_exc())
    elif isinstance(input_dict, list):
        for item in input_dict:
            if isinstance(item, dict):
                update_bools(item)

    return input_dict


def get_hazardous_labels(key_options_items):
    output_list = ["imoClassCode"]
    for item_settings_from_def in key_options_items:
        if item_settings_from_def["modType"] == "hazardousMaterial":
            output_list.append(item_settings_from_def["keyValue"])
    return output_list


def shift_bool_fields(output_json):
    """Shift Address Related Boolean Fields"""

    if "_DGFDeliver" in output_json.keys():
        data = {"_DGFDeliver": output_json["_DGFDeliver"]}
        if "delivery" in output_json.keys():
            output_json["delivery"].update(data)
        else:
            output_json["delivery"] = data

        del output_json["_DGFDeliver"]

    if "_DGFPickup" in output_json.keys():
        data = {"_DGFPickup": output_json["_DGFPickup"]}
        if "pickup" in output_json.keys():
            output_json["pickup"].update(data)
        else:
            output_json["pickup"] = data

        del output_json["_DGFPickup"]

    return output_json


def customs_classification(goods_lines):
    """
    Modification for customsClassification in output json
    """
    for gl in goods_lines:
        if "harmonizedCode" and "customsClassificationCountryCode" in gl.keys():
            gl["customsClassification"] = [
                {
                    "code": gl["harmonizedCode"],
                    "countryCode": gl.pop("customsClassificationCountryCode"),
                }
            ]

    return goods_lines


def address_key_filter(key_value_item, address_keys):
    if key_value_item.get("qualifier_parent"):
        qualifier_parent = key_value_item.get("qualifier_parent")
        if qualifier_parent in address_keys:
            if key_value_item.get("label") in ["name", "phone", "email"]:
                key_value_item["label"] = (
                    key_value_item["qualifier_parent"]
                    + "Contact"
                    + key_value_item["label"].capitalize()
                )
            else:
                key_value_item["label"] = (
                    key_value_item["qualifier_parent"]
                    + key_value_item["label"][0].upper()
                    + key_value_item["label"][1:]
                )
            del key_value_item["qualifier_parent"]
    return key_value_item


def validate_additional_refrence_profile(data, profile_name):
    """Checks if 'additional_reference_profiles' exists, is a non-empty list, and contains 'HK_AFR_STANDARD_PROFILE_AIR_ShipmentCreate'."""
    if not data or "additional_reference_profiles" not in data:
        return False

    profiles = data["additional_reference_profiles"]
    if not isinstance(profiles, list) or len(profiles) == 0:
        return False

    return any(profile == profile_name for profile in profiles)


def transform_reference_data(data):
    """Transforms STY and BR items by replacing STY types with their number values and mapping corresponding BR numbers, ensuring only one STY and one BR exist."""

    # Extract STY, BR, and other items
    sty_items = [item for item in data if item["type"] == "STY"]
    br_items = [item for item in data if item["type"].startswith("BR")]
    other_items = [item for item in data if item["type"] not in ("STY", "BR:")]

    # If no STY and BR items exist, return the data unchanged
    if not sty_items and not br_items:
        return data

    # Ensure exactly one STY and one BR item exist
    if len(sty_items) != 1 or len(br_items) != 1:
        print(
            "Error: Invalid input: There must be exactly one STY item and one BR item."
        )
        return data

    sty_types = sty_items[0]["number"].split("\n")
    br_numbers = br_items[0]["number"].split("\n")

    # Ensure STY and BR parts are correctly mapped
    if len(sty_types) != len(br_numbers):
        print("Error: Mismatch: STY parts and BR parts must have the same length.")
        return data

    transformed_data = other_items.copy()

    # Process and map STY types to corresponding BR numbers
    for sty_type, br_number in zip(sty_types, br_numbers):
        for num in br_number.split("/"):
            transformed_data.append({"type": sty_type.strip(), "number": num.strip()})

    return transformed_data

value_type_dict = {
    "references": "number",
    "notes": "text",
    "customsEntries": "number",
    "parties": "accountNumber",
    "service": "text",
    "milestone": "text",
}


def output_cw1_main(request_data):
    try:
        # @Emon on 04/12/2022 initiated the script
        # @Emon on 23/01/2022 Block will not go to output
        # @Emon on 13/03/2023 Company Stop Words Argument Added

        output_json_version = "v5.18072023-Cw1"
        d_json = request_data["data_json"]
        master_dictionaries = request_data.get("master_dictionaries")
        # store the definitions
        try:
            definition_settings = request_data.get("definition_settings")
        except:
            response = populate_error_response(
                data={},
                error="definition_settings not found",
                traceback=traceback.print_exc(),
            )
            return response

        try:
            key_qualifiers = definition_settings.get("keyQualifiers")
        except:
            response = populate_error_response(
                data={},
                error="keyQualifiers not found",
                traceback=traceback.print_exc(),
            )
            return response

        try:
            # Added by emon on 13/03/2023 - Company Stop Words argument passed
            definitions = request_data.get("definitions")
        except:
            pass

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
            return response

        try:
            address_keys = list()

            # lookupLables
            for item_settings_from_def in key_options_items:
                if item_settings_from_def["type"] == "addressBlock":
                    address_keys.append(item_settings_from_def["keyValue"])
        except:
            response = populate_error_response(
                data={}, error="Address Keys not found", traceback=traceback.print_exc()
            )
            return response

        HZGOODSLINES_LABELS = get_hazardous_labels(key_options_items)

        # Dealing with keyQualifiers
        qualifiers_data = dict()
        all_qualifiers_data = list()
        address_block_partial = dict()
        time_holder = list()

        batch_mode = request_data.get("batch_mode")

        def lookup_function(key_value_item, qualifier_parent):
            try:
                label = key_value_item["label"]
            except:
                label = "undefined"

            # ADDED BY EMON ON 07/03/2023
            if key_value_item.get("copyValue"):
                try:
                    qualifier_parent = get_actual_parent(
                        label, key_qualifiers, qualifier_parent
                    )
                except:
                    print(traceback.print_exc())
                    pass

            if not qualifier_parent:
                return False

            value = key_value_item["v"]
            # appending to the qualifers data dict
            if qualifier_parent.lower() == "time":
                time_holder.append(key_value_item)
                return True

            if type(value) == list:
                value = "\n".join(value)

            value = value.strip()
            value_type = "text"


            try:
                if qualifier_parent in value_type_dict.keys():
                    value_type = value_type_dict[qualifier_parent]
            except:
                pass

            if value:
                associated_data = dict()
                associated_data["parent"] = qualifier_parent
                associated_data["valueType"] = value_type
                associated_data["label"] = label
                placed_value = value
                if "\\n" in placed_value:
                    placed_value = placed_value.replace("\\n", "\n")
                associated_data["value"] = placed_value

                all_qualifiers_data.append(associated_data)
                # if target_keyNode_name in qualifiers_data.keys():
                #     qualifiers_data[target_keyNode_name.lower()].append(
                #         {"type": label, valueType: value})
                # else:
                #     qualifiers_data[target_keyNode_name.lower()] = [
                #         {"type": label, valueType: value}]
            return True

        temp_json = copy.deepcopy(d_json)
        profile_id = temp_json["DefinitionID"]
        doc_type = temp_json["DocumentType"]
        batch_id = temp_json["id"]
        goods_lines = []
        address_data = []
        key_values = {}
        type_mismatch_list = []

        documents = temp_json["nodes"]

        # added by emon on 19/05/2022
        test_document_trigger = None
        try:
            test_document_trigger = request_data["document_id"]
        except:
            pass

        merge_output_trigger = False

        if profile_id in MERGE_OUTPUT_TRIGGER_PROFILE_IDS:
            merge_output_trigger = True

        if not test_document_trigger:
            document_triggered = 0
        else:
            document_triggered = test_document_trigger

        for document_idx, document in enumerate(documents):
            # if not merge_output_trigger:
            #     if not (document_triggered == 0 and document_idx == 0):
            #         if document_triggered != document["id"]:
            #             continue

            children = document["children"]
            compound_output = dict()
            for item in children:
                if item["type"] == "table":
                    rows = item["children"]
                    for row in rows:
                        goods_line = {}
                        for cell in row["children"]:
                            # If profile key not found continue
                            if "is_profile_key_found" in cell.keys() and not cell.get("is_profile_key_found"):
                                continue
                            try:
                                label = cell["label"]
                            except:
                                label = "undefined"
                            type_mismatch = False
                            if lookup_function(cell, cell.get("qualifier_parent")):
                                type_mismatch = True
                                continue
                            # checking label data from defintions
                            for item_settings_from_def in key_options_items:
                                if label == item_settings_from_def["keyValue"]:
                                    # print(label, "---", item_settings_from_def["keyValue"])
                                    # matching the type between the data and in defintion settings type
                                    if item_settings_from_def["type"] != item["type"]:
                                        found_in_type = item["type"]
                                        target_type = item_settings_from_def["type"]
                                        mismatch_data = dict()
                                        mismatch_data["data"] = cell
                                        mismatch_data["found_in_type"] = found_in_type
                                        mismatch_data["target_type"] = target_type
                                        type_mismatch_list.append(mismatch_data)
                                        type_mismatch = True
                            if not type_mismatch:
                                value = cell["v"]
                                allowed = True
                                # deleting None Labels
                                if (label in ["None", "notInUse", "", "filler"]) or (
                                    (label[-1].isnumeric())
                                    and not ("Address" in label)
                                    and not (
                                        cell.get("qualifier_parent") == "references"
                                    )
                                    and not (cell.get("qualifier_parent") == "milestone")
                                ):
                                    if not (
                                        "parser_generated" in cell.keys()
                                        and (cell["parser_generated"] == True)
                                    ):
                                        allowed = False
                                if allowed:
                                    if type(value) == float or type(value) == int:
                                        value = str(value)
                                    if value:
                                        goods_line.update({label: value.strip()})
                        if goods_line:
                            goods_lines.append(goods_line)

                if item["type"] == "key":
                    key_value_items = item["children"]
                    for key_value_item in key_value_items:
                        # print("key_value_item", key_value_item)
                        key_value_item = address_key_filter(
                            key_value_item, address_keys
                        )
                        # If profile key not found continue
                        if "is_profile_key_found" in key_value_item.keys() and not key_value_item.get("is_profile_key_found"):
                            continue
                        # Added by emon on 20/09/2022
                        if key_value_item.get("notInUse"):
                            continue

                        if merge_output_trigger:
                            if document_idx > 0:
                                if (
                                    key_value_item.get("qualifier_parent")
                                    != "references"
                                ):
                                    continue

                        if key_value_item.get("title") == "mandatoryWarning":
                            continue

                        label = key_value_item["label"]
                        type_mismatch = False
                        # deleting None Labels
                        bypass_labels = ["T1", "T2", "137"]
                        if (label in ["None", "notInUse", "", "filler"]) or (
                            (label not in bypass_labels and label[-1].isnumeric())
                            and not ("Address" in label)
                            and not (
                                key_value_item.get("qualifier_parent") == "references"
                            )
                            and not (
                                key_value_item.get("qualifier_parent") == "milestone"
                            )
                        ):
                            pass
                        elif key_value_item.get("isCompoundKey") == True:
                            if key_value_item.get("isCompoundKeyLabel") == "service":
                                if (
                                    not key_value_item["isCompoundKeyLabel"]
                                    in compound_output.keys()
                                ):
                                    compound_output[
                                        key_value_item["isCompoundKeyLabel"]
                                    ] = list()
                                compound_key_items = key_value_item["children"]
                                compound_output_list = dict()
                                compound_output_list["type"] = key_value_item["label"]

                                for compound_idx, compound_key_item in enumerate(
                                    compound_key_items
                                ):
                                    if compound_idx == 0:
                                        compound_output_list[
                                            key_value_item["isCompoundChildLabel"]
                                        ] = key_value_item["label"]
                                    compound_child_label = compound_key_item["label"]
                                    compound_child_value = compound_key_item["v"]
                                    if compound_output_list[
                                        key_value_item["isCompoundChildLabel"]
                                    ]:
                                        if (
                                            len(
                                                compound_output[
                                                    key_value_item["isCompoundKeyLabel"]
                                                ]
                                            )
                                            > 3
                                        ):
                                            response = populate_error_response(
                                                data={},
                                                error="Service type cannot be more than 3",
                                                traceback=traceback.print_exc(),
                                            )
                                            return response
                                    if compound_child_label == "duration":
                                        try:
                                            compound_output_list[
                                                compound_child_label
                                            ] = float(compound_child_value)
                                        except:
                                            response = populate_error_response(
                                                data={},
                                                error="Duration must be a number",
                                                traceback=traceback.print_exc(),
                                            )
                                            return response
                                    elif compound_child_label == "contractor":
                                        if len(compound_child_value) <= 12:
                                            compound_output_list[
                                                compound_child_label
                                            ] = compound_child_value
                                        else:
                                            response = populate_error_response(
                                                data={},
                                                error="Contractor must be less than 12 characters",
                                                traceback=traceback.print_exc(),
                                            )
                                            return response

                                    elif compound_child_label == "count":
                                        try:
                                            compound_output_list[
                                                compound_child_label
                                            ] = int(compound_child_value)
                                        except:
                                            response = populate_error_response(
                                                data={},
                                                error="Count must be a number",
                                                traceback=traceback.print_exc(),
                                            )
                                            return response
                                    else:
                                        compound_output_list[compound_child_label] = (
                                            compound_child_value
                                        )

                                compound_output[
                                    key_value_item["isCompoundKeyLabel"]
                                ].append(compound_output_list)

                            else:
                                try:
                                    if (
                                        not key_value_item["isCompoundKeyLabel"]
                                        in compound_output.keys()
                                    ):
                                        compound_output[
                                            key_value_item["isCompoundKeyLabel"]
                                        ] = dict()
                                    compound_key_items = key_value_item["children"]
                                    for compound_key_item in compound_key_items:
                                        compound_child_label = compound_key_item[
                                            "label"
                                        ]
                                        compound_child_value = compound_key_item["v"]
                                        compound_output[
                                            key_value_item["isCompoundKeyLabel"]
                                        ][compound_child_label] = compound_child_value
                                except:
                                    print(traceback.print_exc())
                                    pass
                            key_values.update(compound_output)
                        else:
                            if lookup_function(
                                key_value_item, key_value_item.get("qualifier_parent")
                            ):
                                type_mismatch = True
                                continue
                            # checking label data form defintions
                            for item_settings_from_def in key_options_items:
                                # print(label, "---", item_settings_from_def["keyValue"])
                                # matching the type between the data and in defintion settings type
                                if label == item_settings_from_def["keyValue"]:
                                    if item_settings_from_def["type"] != item["type"]:
                                        found_in_type = item["type"]
                                        target_type = item_settings_from_def["type"]
                                        mismatch_data = dict()
                                        mismatch_data["data"] = key_value_item
                                        mismatch_data["found_in_type"] = found_in_type
                                        mismatch_data["target_type"] = target_type
                                        type_mismatch_list.append(mismatch_data)
                                        type_mismatch = True
                                        # print(key_value_item, target_type)
                            if not type_mismatch:
                                value = key_value_item["v"]
                                key_values.update({label: value})

        extra_row_label_holder = list()
        # Count of dimensions
        dim_count = 0

        """Getting the number of dimensions in mismatch list.
        This essentially helps us determine how many extra rows to add to output goodsLines"""
        for elem in type_mismatch_list:
            if elem["target_type"] == "table" and elem["found_in_type"] == "key":
                data = elem["data"]
                label = data["label"]
                if label == "dimensions":
                    dim_count += 1

        # appending to correct target types using the dict
        for elem in type_mismatch_list:
            if elem["target_type"] == "table" and elem["found_in_type"] == "key":
                data = elem["data"]
                label = data["label"]
                value = data["v"]
                originates_from_dim = False
                try:
                    originates_from_dim = data.get("parentLabel")
                except:
                    pass

                if (not "dimensions" in label) and (
                    not originates_from_dim == "dimensions"
                ):
                    label = "total" + label[0].upper() + label[1:]
                    key_values.update({label: value})
                else:
                    extra_row_label_holder.append([label, value])

            elif elem["target_type"] == "key" and elem["found_in_type"] == "table":
                data = elem["data"]
                label = data["label"]
                value = data["v"]
                key_values.update({label: value})

            elif elem["target_type"] == "addressBlock":
                data = elem["data"]
                label = data["label"]
                children = list()
                try:
                    children = data["children"]
                except:
                    text = custom_address_parser(
                        data["v"], definitions, master_dictionaries
                    )
                    for key_data, value_data in text.items():
                        child_dict = dict()
                        child_dict["label"] = key_data
                        child_dict["v"] = value_data
                        children.append(child_dict)
                address_dict = dict()
                full_dict = dict()
                contact_dict = dict()

                if children:
                    for dict_item in children:
                        key_name = dict_item["label"]
                        key_value = dict_item["v"]
                        if dict_item.get("notInUse"):
                            continue

                        disregard = False

                        if key_name in ADDRESS_CHILD_DISREGARD_LIST:
                            disregard = True

                        if key_name == "name":
                            full_dict[key_name] = key_value
                            disregard = True

                        elif key_name == "accountNumber":
                            full_dict[key_name] = key_value
                            disregard = True

                        elif key_name == "dropMode":
                            full_dict[key_name] == key_value
                            disregard = True

                        elif key_name == "addressShortCode":
                            full_dict[key_name] = key_value
                            disregard = True

                        elif "contact" in key_name:
                            contact_dict[transform_label(key_name)] = key_value
                            disregard = True

                        if not disregard:
                            if key_name == "state":
                                key_name = "stateProvince"
                            address_dict[key_name] = key_value

                    if address_dict:
                        full_dict["address"] = address_dict

                    if contact_dict:
                        full_dict["contact"] = contact_dict

                    if full_dict:
                        if not label == "block":
                            address_data.append({label: full_dict})

            elif elem["target_type"] == "addressBlockPartial":
                data = elem["data"]
                disregard = False
                if data["label"] in ADDRESS_CHILD_DISREGARD_LIST:
                    disregard = True
                if not disregard:
                    address_block_partial[elem["data"]["label"]] = elem["data"]["v"]

        # Process to add table data found in keys in goodsLines:
        # Initiating the extra row list-- THIS IS TO BE ADDED TO THE FINAL OUTPUT GOODSLINES
        extra_row_list = list()
        try:
            temp_extra_rows_holder = list()  # this is a placeholder for this process
            if dim_count == 0:
                """If no dimensions at all just adding non-dimension fields to a single goodsLine and appending to goodsLines"""
                only_non_dim_dict = dict()
                for x in extra_row_label_holder:
                    only_non_dim_dict[x[0]] = x[1]
                if only_non_dim_dict:
                    extra_row_list.append(only_non_dim_dict)
            else:
                non_dimension_fields_list = list()
                targets = [
                    "dimensions",
                    "length",
                    "width",
                    "height",
                    "dimensionsUom",
                    "packageCount",
                ]

                # Seperating non dimension fields
                for x in extra_row_label_holder:
                    if not x[0] in targets:
                        non_dimension_fields_list.append(x)

                # looping through each target field and extracting data at seperate instances
                for target_field in targets:
                    target_dict = dict()
                    target_count = 0
                    for x in extra_row_label_holder:
                        if target_field == x[0]:
                            target_dict[target_count] = {x[0]: x[1]}
                            target_count += 1
                        if target_dict:
                            temp_extra_rows_holder.append(target_dict)

                """Depending on dimensions count creating extra rows and appending non dimension fields
                to each of these rows"""
                for i in range(dim_count):
                    index_in_loop_dict = dict()
                    for temp in temp_extra_rows_holder:
                        for key, value in temp[i].items():
                            index_in_loop_dict[key] = value
                    if index_in_loop_dict:
                        for field in non_dimension_fields_list:
                            index_in_loop_dict[field[0]] = field[1]
                        extra_row_list.append(index_in_loop_dict)
        except:
            pass
            print(traceback.print_exc())

        if extra_row_list:
            """Adding this extra_row data to goodsLines"""
            for extra_row in extra_row_list:
                goods_lines.append(extra_row)

        # adding the reformulated keyDatas
        output_qualifiers_data = dict()

        for x in all_qualifiers_data:
            # print("X", x)
            type_label = "type"
            value_type = x["valueType"]

            if x.get("parent").lower() == "parties":
                type_label = "partyType"

            if (x.get("parent").lower() == "service") and (len(x["label"]) > 3):
                # print("Service")
                # print(len(x["label"]))
                append_dict = {x["label"]: x["value"]}
            else:
                append_dict = {type_label: x["label"], value_type: x["value"]}

            if not x["parent"] in output_qualifiers_data.keys():
                output_qualifiers_data[x["parent"]] = [append_dict]
            else:
                # if x["parent"] == "references":
                #     if append_dict in output_qualifiers_data[x["parent"]]:
                #         continue

                output_qualifiers_data[x["parent"]].append(append_dict)

        # Added time subtype to parent time key at the end.
        for time_type in time_holder:
            related_label = time_type["label"].replace("Time", "")
            if related_label in key_values.keys():
                newvalue = key_values[related_label] + " " + time_type["v"]
                key_values[related_label] = newvalue
            else:  # Or leaving it in keys
                key_values[time_type["label"].replace("Time", "")] = time_type["v"]

        # if merge_output_trigger:
        #     for qualifer_type, qualiferData in final_qualifier_data.items():
        #         if qualifer_type == "references":
        #             for subtype in qualiferData:
        #                 subtype["number"] = [apply_remove_duplicates_from_string(
        #                     None, subtype["number"][0])]

        profile_settings = definition_settings.get("profileSettings")
        if validate_additional_refrence_profile(profile_settings, profile_id):
            if "references" in output_qualifiers_data.keys():
                output_qualifiers_data["references"] = transform_reference_data(
                    output_qualifiers_data["references"]
                )

        key_values.update(output_qualifiers_data)

        if address_data:
            for i in address_data:
                key_values.update(i)

        # Convert all values to string
        for item in goods_lines:
            for key in item.keys():
                try:
                    try:
                        converted_string = unquote(item[key].replace("=", "%"))
                        item[key] = str(converted_string)
                    except:
                        item[key] = str(item[key])
                except:
                    item[key] = ""

        output_json = dict()

        """ Restructuring dims """
        for goods_line in goods_lines:
            tbr = list()
            dim_dict = dict()
            temperature_dict = dict()
            hazardous_gl_dict = dict()

            for gl_key, gl_val in goods_line.items():
                """Looping through goodsLine and restructing after detecting type of label"""
                if gl_key in DIM_LABELS:
                    gl_key_transformed = transform_glKey(gl_key)
                    dim_dict[gl_key_transformed] = gl_val
                    tbr.append(gl_key)

                elif gl_key in TEMPERATURE_LABELS:
                    gl_key_transformed = transform_glKey(gl_key)
                    temperature_dict[gl_key_transformed] = gl_val
                    tbr.append(gl_key)

                elif gl_key in HZGOODSLINES_LABELS:
                    gl_key_transformed = transform_hz_label(gl_key)
                    # hazardous_gl_dict[gl_key_transformed] = gl_val

                    def is_number(value):
                        try:
                            float(value)
                            return True
                        except ValueError:
                            return False

                    if gl_key_transformed == "_IMOClassCode":
                        if is_number(gl_val):
                            if "." in gl_val:
                                # if it has decimal
                                hazardous_gl_dict[gl_key_transformed] = float(gl_val)
                            else:
                                hazardous_gl_dict[gl_key_transformed] = int(gl_val)
                        else:
                            hazardous_gl_dict[gl_key_transformed] = gl_val
                    else:
                        hazardous_gl_dict[gl_key_transformed] = gl_val
                    tbr.append(gl_key)

            if dim_dict:
                goods_line["dimensions"] = dim_dict

            if temperature_dict:
                goods_line["temperatures"] = temperature_dict

            if hazardous_gl_dict:
                goods_line["hazardousMaterial"] = [hazardous_gl_dict]

            for i in tbr:
                del goods_line[i]

        if goods_lines:
            goods_lines = convert_goodsLines_value_formats(goods_lines)
            goods_line = customs_classification(goods_lines)
            output_json["goodsLines"] = goods_lines

        output_json.update(key_values)

        # Doing global parsing operations
        # output_json = process(output_json)
        output_json = address_partial_function(address_block_partial, output_json)

        if output_json:  # and batch_mode != "training":
            "Converting numerical values to to float/integer type values"
            output_json = convert_to_Dtype(output_json)

            try:
                """Adding underscores infront of some fields"""
                output_json = tranform_underscore_fields(output_json)
            except:
                print(traceback.print_exc())

            try:
                """Converting bool fields to bool type fields"""
                output_json = update_bools(output_json)
            except:
                print(traceback.print_exc())
                pass

            try:
                """Shifting keys such as _DGFDeliver and _DGFPickup inside the address keys"""
                output_json = shift_bool_fields(output_json)
            except:
                pass
            try:
                if "notes" in output_json.keys():
                    notes_list = list()
                    for note in output_json["notes"]:
                        if note not in notes_list:
                            notes_list.append(note)
                    output_json["notes"] = notes_list
            except:
                print(traceback.print_exc())
                pass

            print(output_json)
        # try:
        #     # Profile_id, vendorWise changes
        #     output_json = v4_output_alternator.process(
        #             profile_id, docType, output_json)
        # except:
        #     # print(output_json)
        #     print("output alternator wasn't executed due to an error")
        #     print(traceback.print_exc())
        #     pass

        output_json.update({"batchid": batch_id})
        response = {
            "outputJsonVersion": output_json_version,
            "output_json": output_json,
        }
        return response

    except ValueError as ve:
        print(traceback.print_exc())
        message = "A numerical value has multiple decimal points in it. Please recheck"

        message_dict = {"message": message, "code": 400, "module": "OutputJson"}

        return {"error": ve, "messages": [message_dict]}

    except Exception as error:
        print(traceback.print_exc())
        return {"error": error, "messages": []}
