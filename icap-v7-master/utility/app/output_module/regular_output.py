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


def split_key(address_block_partial, output_json):
    # initializing two lists for storage
    to_be_removed = list()
    to_be_added = list()

    # Looping through the partial keyNames
    for key_name, value in address_block_partial.items():
        # regex to find out the first Uppercase index and splitting at it
        i = re.search("[A-Z]", key_name).start()
        associated_parent_key_name, child_key_name = key_name[:i], key_name[i:]
        child_key_name = child_key_name[0].lower() + child_key_name[1:]

        if "pickUp" in key_name:
            associated_parent_key_name = "pickUp"
            child_key_name = key_name.replace("pickUp", "")

        # checking if the parent key exists in output
        if associated_parent_key_name in output_json.keys() and type(output_json[associated_parent_key_name]) == dict:
            copied_dict = output_json[associated_parent_key_name].copy()

            # for multiple children for one parent we take data from the previous dict
            for label_data in to_be_added:
                if label_data["parent"] == associated_parent_key_name:
                    copied_dict = label_data["childKeyValue"]
            block_storage = copied_dict["block"]
            # We pop[ the block and add it later on
            copied_dict.pop("block", None)

            # Storage for previous children of the addressBlock. This is done to maintain order
            new_dict = dict()
            for pre_key, pre_value in copied_dict.items():
                new_dict[pre_key] = pre_value
            new_dict[child_key_name] = value
            new_dict["block"] = block_storage
            data = {
                "parent": associated_parent_key_name,
                "childKeyName": child_key_name,
                "childKeyValue": new_dict,
                "type": "modification",
            }

            # Appending to the storage
            to_be_added.append(data)
            to_be_removed.append(associated_parent_key_name)
        else:
            """if the parent address key does not exist in output json"""
            data = {
                "parent": associated_parent_key_name,
                "childKeyName": child_key_name,
                "childKeyValue": value,
                "type": "addition",
            }
            to_be_added.append(data)
            to_be_removed.append(associated_parent_key_name)

    if to_be_removed:
        for elem in to_be_removed:
            output_json.pop(elem, None)

    if to_be_added:
        for elem in to_be_added:
            if elem["type"] == "addition":
                if elem["parent"] in output_json.keys():
                    output_json[elem["parent"]].update(
                        {elem["childKeyName"]: elem["childKeyValue"]}
                    )
                else:
                    output_json[elem["parent"]] = {
                        elem["childKeyName"]: elem["childKeyValue"]
                    }
            else:
                output_json[elem["parent"]] = elem["childKeyValue"]

    return output_json


def regular_output_main(request_data):
    try:
        # @Emon edited output to only work for only the first document on 23/08/2022
        # @Emon edited output to also take in test document
        # @Emon edited output to take care of notInUse functionality in keys
        # @Emon edited output to take care of parsing generated cells to deal with multiple dimension extraction in tables using keys tool
        # @Emon-30.09.2022 edited output to get rid of total keys in frontend and add them on this script in the background
        # @Emon on 10/10/2022 edited output to not add total prefix to dimensions if extracted in key section
        # @Emon on 16/10/2022 Edited output to take in Time fields
        # @Emon on 20/10/2022 Filler not to go in output
        # @Emon on 26/10/2022 Multiple References output will be joined and sent in order of extraction
        # @Emon on 18/11/2022 Merge enabled
        # @Emon on 02/02/2022 References
        # @Emon on 13/03/2023 Company Stop Words Added
        output_json_version = "v5.2.13032023"
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
            # Added by emon on 13/03/2023
            definitions = request_data.get("definitions")
        except:
            pass

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

        # Dealing with keyQualifiers
        qualifiers_data = dict()
        all_qualifiers_data = list()
        address_block_partial = dict()
        time_holder = list()

        def lookup_function(key_value_item):
            try:
                input_label = key_value_item["label"]
            except:
                input_label = "undefined"
            value = key_value_item["v"]
            for setting in key_qualifiers:
                options = setting["options"]
                for option in options:
                    # checking if the key exists in the option value
                    # print(label, '----', option["value"])
                    if input_label == option["value"]:
                        # print(label, '----', option["value"])
                        target_key_node_name = setting["name"]
                        # appending to the qualifers data dict

                        if target_key_node_name.lower() == "time":
                            time_holder.append(key_value_item)
                            return True

                        if type(value) == list:
                            value = "\n".join(value)

                        value = value.strip()
                        value_type = "text"

                        value_type_dict = {
                            "references": "number",
                            "notes": "text",
                            "customsentries": "number",
                            "parties": "accountNumber",
                            "service": "text",
                            "milestone": "text",
                        }
                        try:
                            if target_key_node_name.lower() in value_type_dict.keys():
                                value_type = value_type_dict[target_key_node_name]
                        except:
                            pass

                        if value:
                            associated_data = dict()
                            associated_data["parent"] = target_key_node_name.lower()
                            associated_data["valueType"] = value_type
                            associated_data["label"] = label
                            associated_data["value"] = value
                            all_qualifiers_data.append(associated_data)
                            # if target_key_node_name in qualifiers_data.keys():
                            #     qualifiers_data[target_key_node_name.lower()].append(
                            #         {"type": label, valueType: value})
                            # else:
                            #     qualifiers_data[target_key_node_name.lower()] = [
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
            if not merge_output_trigger:
                if not (document_triggered == 0 and document_idx == 0):
                    if document_triggered != document["id"]:
                        continue
            children = document["children"]
            for item in children:
                if item["type"] == "table":
                    rows = item["children"]
                    for row in rows:
                        goods_line = {}
                        for cell in row["children"]:
                            if "is_profile_key_found" in cell.keys() and not cell.get("is_profile_key_found"):
                                continue
                            try:
                                label = cell["label"]
                            except:
                                label = "undefined"
                            type_mismatch = False
                            if lookup_function(cell):
                                type_mismatch = True
                                continue
                            # checking label data from definitions
                            for item_settings_from_def in key_options_items:
                                if label == item_settings_from_def["keyValue"]:
                                    # print(label, "---", item_settings_from_def["keyValue"])
                                    # matching the type between the data and in definition settings type
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
                                try:
                                    if (label in ["None", "notInUse", "", "filler"]) or (
                                        (label[-1].isnumeric())
                                        and not ("Address" in label)
                                        and not (
                                            key_value_item.get("qualifier_parent")
                                            == "milestone"
                                        )
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
                                except:
                                    pass
                        if goods_line:
                            goods_lines.append(goods_line)

                if item["type"] == "key":
                    key_value_items = item["children"]
                    for key_value_item in key_value_items:
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

                        if key_value_item.get("type") == "mandatoryWarning":
                            continue

                        label = key_value_item["label"]
                        type_mismatch = False
                        # deleting None Labels
                        if (label in ["None", "notInUse", "", "filler"]) or (
                            (label[-1].isnumeric()) and not ("Address" in label)
                        ):
                            pass
                        else:
                            if lookup_function(key_value_item):
                                type_mismatch = True
                                continue
                            # checking label data form definitions
                            for item_settings_from_def in key_options_items:
                                # print(label, "---", item_settings_from_def["keyValue"])
                                # matching the type between the data and in definition settings type
                                if label == item_settings_from_def["keyValue"]:
                                    stop_trigger = False
                                    if label.lower() == "pickupdropmode":
                                        continue

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
                    if not "productcode" in label.lower():
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
                expanded_dict = dict()
                if children:
                    for dict_item in children:
                        key_name = dict_item["label"]
                        key_value = dict_item["v"]
                        if dict_item.get("notInUse"):
                            continue
                        expanded_dict[key_name] = key_value
                    if expanded_dict:
                        address_data.append({label: expanded_dict})

            elif elem["target_type"] == "addressBlockPartial":
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

        # print(address_data)
        # adding the reformulated keyDatas
        output_qualifiers_data = dict()

        for x in all_qualifiers_data:
            type_label = "type"
            if x["parent"] == "parties":
                type_label = "partyType"

            if not x["parent"] in output_qualifiers_data.keys():
                output_qualifiers_data[x["parent"]] = [
                    {type_label: x["label"], x["valueType"]: x["value"]}
                ]
            else:
                prev_data = output_qualifiers_data[x["parent"]]
                type_was_there_before = False
                for loop_dict in prev_data:
                    if loop_dict[type_label] == x["label"]:
                        type_was_there_before = True

                        if x.get("parent") == "references":
                            if x["value"] in loop_dict[x["valueType"]]:
                                continue

                        loop_dict[x["valueType"]] = (
                            loop_dict[x["valueType"]] + ";" + x["value"]
                        )
                if not type_was_there_before:
                    output_qualifiers_data[x["parent"]].append(
                        {type_label: x["label"], x["valueType"]: x["value"]}
                    )

        final_qualifier_data = dict()

        # converting strings into array
        for item, value in output_qualifiers_data.items():
            new_value = list()
            for x_idx, x in enumerate(value):
                if "text" in x.keys():
                    arr = [x["text"]]
                    x["text"] = arr
                elif "number" in x.keys():
                    arr = [x["number"]]
                    x["number"] = arr
                else:
                    pass
                new_value.append(x)

            final_qualifier_data[item] = new_value

        # Added time subtype to parent time key at the end.
        for time_type in time_holder:
            related_label = time_type["label"].replace("Time", "")
            if related_label in key_values.keys():
                newvalue = key_values[related_label] + " " + time_type["v"]
                key_values[related_label] = newvalue
            else:  # Or leaving it in keys
                key_values.append(time_type)

        if merge_output_trigger:
            for qualifier_type, qualifier_data in final_qualifier_data.items():
                if qualifier_type == "references":
                    for subtype in qualifier_data:
                        subtype["number"] = [
                            apply_remove_duplicates_from_string(
                                None, subtype["number"][0]
                            )
                        ]

        key_values.update(final_qualifier_data)

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

        if goods_lines:
            output_json["goodsLines"] = goods_lines

        output_json.update(key_values)
        # Doing global parsing operations
        # output_json = process(output_json)
        output_json = split_key(address_block_partial, output_json)

        try:
            # ProfileID, vendorWise changes
            output_json = output_alternator.process(profile_id, doc_type, output_json)
        except:
            # print(output_json)
            print("output alternator wasn't executed due to an error")
            print(traceback.print_exc())
            pass

        output_json.update({"batchid": batch_id})

        response = {
            "outputJsonVersion": output_json_version,
            "output_json": output_json,
        }
        return response

    except Exception as error:
        print(traceback.print_exc())
        return {"error": error, "messages": []}
