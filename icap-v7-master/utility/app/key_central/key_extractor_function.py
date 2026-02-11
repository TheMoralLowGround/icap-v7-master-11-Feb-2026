import traceback
from collections import OrderedDict

from app.extraction_modules.excel_sub_module import excel_extraction_request

from ..response_formator import populate_error_response
from .key_module_central import extraction_tools_request

"""
This script is a Python module that performs key-value extraction from documents and incorporates data from external sources, such as robots and Excel files. Here's a technical summary:

1. **Document Preprocessing**: The script removes any existing key nodes from the input JSON data to prepare for new key extraction.

2. **Query Key List Retrieval**: It fetches the list of keys to be extracted from the provided definitions in the request data.

3. **Document Processing**:
   - It iterates through each document node in the JSON data.
   - For Excel files, it calls the `excel_extraction_request` function to extract data from the Excel document.
   - For non-Excel documents, it performs the following steps:
     - Compound Key Extraction: If a key is marked as a compound key, it extracts its child keys using the `extraction_tools_request` function.
     - Regular Key Extraction: It calls the `extraction_tools_request` function to extract regular keys from the document.

4. **Key Node Creation**:
   - It creates key node dictionaries for each extracted key-value pair, including compound keys.
   - The key nodes contain metadata such as label, position, page ID, and export status.
   - It appends the key nodes as children to the corresponding document node in the JSON data.

5. **Robot Data Extraction**:
   - It attempts to import and run external robot scripts (`robot.robot.main`) to extract data from the documents.
   - It incorporates the robot data into a separate dictionary (`robot_Data_Holder`).
   - It creates key nodes for the robot data and appends them to the corresponding document node in the JSON data.

6. **Special Extraction**:
   - It attempts to import and run a special extraction function (`special_extraction_function`) from a separate module (`app.special_robots.special_extraction`).
   - It incorporates the data extracted by this function into the `robot_Data_Holder` dictionary.

7. **Error Handling**:
   - The script uses the `traceback` module to print any exceptions that occur during the extraction process.

8. **Return Value**:
   - The script returns the updated JSON data (`d_json`) with the extracted key-value pairs and additional data from robots and special extractions.

The purpose of this script is to centralize the key-value extraction process from various document types, including regular documents, Excel files, and data from external sources like robots and special extraction functions. It prepares the extracted data in a structured JSON format for further processing or integration into other systems.


"""


def main(request_data, d_json, messages, query_key_list):
    # Key extractor version 5.24-12022.01
    # 12/08/2022 Extraction will check if rest of string apart from key shapes if they are only punctuations. if so ignored @Emon
    # 19/08/2022 Static Field Extraction Logic Added/Robot Triggered for all batch even though test document clicked bug fixed/VersionData Added for KeyValueExtractor and Rules
    # 06/09/2022 Added unique key attribute to all key nodes
    # @Emon on 08/09/2022 - Multiple Trigger code added
    # @Emon on 09/09/2022 - Average Span calculation for multiple trigger added
    # @Emon on 16/09/2022 - If value is empty then do not append logic added
    # @Emon on 16/09/2022 - If the data json document node is empty static/robot and other keys should also be present
    # @Emon on 18/09/2022 - Multiple Shape Keys were not trimming the key shape bug fix
    # @Emon on 19/09/2022 - Test Document Flag reception added
    # @Emon on 21/09/2022 - Test Document Flag reception and conditions updated
    # @Emon on 15/10/2022 #ANCHRORTRIGGERS01 in key extraction module
    # @Emon on 15/10/2022 - Extraction Modules to show extraction fails in timeline
    # @Emon on 20/10/2022 - Duplicate Removal Button not working bug fix
    # @Emon on 24/01/2023 - Added qualifierParent in the extracted keys
    # @Emon on 13/03/2023 - Group Multiples added for single column extractor
    # @Emon on 18/04/2023 - Group Multiples added for regex extractor

    initial_json = d_json.copy()

    ra_json = request_data["ra_json"]
    d_json = request_data["data_json"]

    job_id = request_data["job_id"]

    docs = d_json["nodes"]

    # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass

    # keyNode removal
    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            if "key" in node["id"].lower() or "key_0" in node["id"].lower():
                d_json["nodes"][input_doc_idx]["children"].remove(node)
                # pass

    try:
        definitions = request_data["definitions"]
    except:
        response = populate_error_response(
            data=d_json, error="definitions not found", traceback=traceback.print_exc()
        )
        return response

    # for elem in definitions:
    #     definitions_docType = elem["docType"]
    #     query_key_dict[definitions_docType] = elem["key"]["items"]

    # Here is the key list will be stored
    for input_doc_idx, target_doc in enumerate(docs):
        compound_outputs = list()
        if (test_document_trigger != None) and (
            test_document_trigger != target_doc["id"]
        ):  # Figuring a way out here
            continue

        if target_doc.get("ext") == ".xlsx":
            try:
                # If the querykeylist is present then only go
                results, messages = excel_extraction_request(
                    query_key_list, request_data, input_doc_idx, messages
                )
            except:
                print(traceback.print_exc())
                pass

        else:
            try:
                for key in query_key_list[:]:
                    compound_output = dict()
                    if key.get("isCompoundKey") == True:
                        keyLabel = key["keyLabel"]
                        compound_key_list = key["compoundItems"]
                        compound_results, messages = extraction_tools_request(
                            compound_key_list, request_data, input_doc_idx, messages
                        )
                        for index, compound_result in enumerate(compound_results[:]):
                            for child_key, value in compound_result.items():
                                if index == 0:
                                    # value_type = value["text"]
                                    compound_output = value.copy()
                                    compound_output["v"] = value["text"]
                                    compound_output["id"] = (
                                        "key_detail_compound_" + str(input_doc_idx)
                                    )
                                    compound_output["children"] = list()
                                    compound_output["label"] = keyLabel
                                    compound_output["type"] = "key_detail"
                                    compound_output["isCompoundKeyLabel"] = keyLabel
                                    compound_output["isCompoundChildLabel"] = child_key
                                    compound_output["isCompoundKey"] = True
                                    if key.get("export") == True:
                                        compound_output["export"] = True
                                    elif key.get("export") == False:
                                        compound_output["export"] = False
                                    value["label"] = child_key
                                    value["v"] = value["text"]
                                    value["children"] = list()
                                    value["id"] = "key_inner_compound_" + str(
                                        input_doc_idx
                                    )
                                    value["type"] = "keyTextDetail"
                                    value["isCompoundKeyChild"] = True
                                    compound_output["children"].append(value.copy())
                                else:
                                    value["label"] = child_key
                                    value["v"] = value["text"]
                                    value["children"] = list()
                                    value["id"] = "key_inner_compound_" + str(
                                        input_doc_idx
                                    )
                                    value["type"] = "keyTextDetail"
                                    value["isCompoundKeyChild"] = True
                                    compound_output["children"].append(value.copy())
                        if compound_output != {}:
                            compound_outputs.append(compound_output.copy())
            except:
                print(traceback.print_exc())
                pass
            results, messages = extraction_tools_request(
                query_key_list, request_data, input_doc_idx, messages
            )

        start_idx = 0
        children_list = []

        project = request_data.get("project")
        combined_extraction = {}
        combined_labels = []
        remove_duplicate_text_from_combined_labels = []
        if project == "Freight":
            combined_labels = ["pickupInstruction", "deliveryInstruction"]
            remove_duplicate_line_from_combined_labels = combined_labels[:]

        # creating each key child per each key val pair and appending to children list
        for result in results:
            # print('\n')
            for key, value in result.items():
                ignore = False
                if value:
                    if not value["text"]:
                        continue
                    try:
                        # Combined Extraction
                        if key in combined_labels:
                            for x in children_list:
                                if x["label"] == key:
                                    x["v"] += "\n" + value["text"]
                                    try:
                                        if (
                                            key
                                            in remove_duplicate_line_from_combined_labels
                                        ):
                                            x["v"] = "\n".join(
                                                list(
                                                    OrderedDict.fromkeys(
                                                        x["v"].split("\n")
                                                    )
                                                )
                                            )
                                    except:
                                        pass

                                    ignore = True
                    except:
                        pass

                    if ignore:
                        continue

                    child_dict = dict()
                    child_dict["is_profile_key_found"] = True
                    child_dict["is_pure_autoextraction"] = True
                    value_type = "key_detail"

                    # For Static Field Types
                    if value.get("title") == "static":
                        value_type = "key_detail_static"

                    child_dict["id"] = value_type + "_" + str(start_idx)
                    try:
                        child_dict["unique_id"] = value["unique_id"]
                    except:
                        pass

                    if value.get("qualifierParent"):
                        child_dict["qualifierParent"] = value.get("qualifierParent")

                    child_dict["advanceSettings"] = value.get("advanceSettings")
                    child_dict["label"] = key
                    child_dict["pageId"] = value["pageId"]
                    child_dict["pos"] = value["pos"]
                    child_dict["type"] = value_type
                    if value.get("export") == True:
                        child_dict["export"] = True
                    elif value.get("export") == False:
                        child_dict["export"] = False
                    # For Excel
                    worksheet_name = value.get("worksheet_name")
                    cellRange = value.get("cellRange")
                    if worksheet_name:
                        child_dict["worksheet_name"] = worksheet_name
                    if cellRange:
                        child_dict["cellRange"] = cellRange
                    status = value.get("STATUS")
                    if not status:
                        status = 0
                    child_dict["STATUS"] = status
                    # ommitting keyname and anything before it
                    text = value["text"]
                    child_dict["v"] = text
                    child_dict["block_type"] = value["title"]
                    start_idx += 1
                    children_list.append(child_dict)
        if compound_outputs:
            for compound_output in compound_outputs[:]:
                children_list.append(compound_output.copy())
        key_node = None
        # appending the keyval children list to key mother node
        if children_list:
            key_node = dict()
            key_node["id"] = "key_" + str(input_doc_idx)
            key_node["pos"] = ""
            key_node["type"] = "key"
            key_node["pageId"] = ""
            key_node["STATUS"] = 0
            key_node["children"] = children_list
            d_json["nodes"][input_doc_idx]["children"].append(key_node)

        robot_children_list = list()

        robot_Data_Holder = dict()
        # @Emon edited on 25/08/2022 to deal with robot version reference error:
        robot_version = dict()
        robot_version["name"] = ""
        robot_version["version"] = ""
        try:
            # load robots from external scripts folder
            from robot.robot import main as regular_robot

            msg1 = {
                "message": "Successfully imported Robots from external folder",
                "code": 200,
                "module": "robots",
            }
            # if not msg1 in messages:
            #     messages.append(msg1)

            regular_Robot_Data = regular_robot(ra_json, input_doc_idx)
            # Added by Almas 01/08/2022
            try:
                robot_version = regular_Robot_Data[1]
                regular_Robot_Data = regular_Robot_Data[0]
            except:
                pass
            for regular_Robot_Key, regular_Robot_Value in regular_Robot_Data.items():
                robot_Data_Holder[regular_Robot_Key] = regular_Robot_Value

            msg2 = {
                "message": "Robot "
                + robot_version["name"]
                + " Version: "
                + robot_version["version"],
                "code": 200,
                "module": "robots",
            }
            if not msg2 in messages:
                messages.append(msg2)

        except ImportError:
            msg3 = {
                "message": "Failed to import Robots from external folder",
                "code": 400,
                "module": "robots",
            }
            # if not msg3 in messages:
            #     messages.append(msg3)
        except:
            print(traceback.print_exc())
            pass

        # Special extraction from rajson itself - INCASE OF SICK-AG
        try:
            from app.special_robots.special_extraction import (
                special_extraction_function,
            )

            ra_json_sepcial_extraction = special_extraction_function(
                ra_json, input_doc_idx, job_id
            )
            for special_key, special_value in ra_json_sepcial_extraction.items():
                robot_Data_Holder[special_key] = special_value
        except:
            print(traceback.print_exc())
            pass

        if not robot_Data_Holder:
            continue

            # Alteration process for robot values
        robot_to_alternate = list()
        for robot_key, robot_val in robot_Data_Holder.items():
            single_key_val_data = dict()
            single_key_val_data[robot_key] = robot_val
            robot_to_alternate.append(single_key_val_data)

        robot_data = list()

        for alternated_data in robot_to_alternate:
            for alternated_robot_key, alternated_robot_val in alternated_data.items():
                robot_data.append({alternated_robot_key: alternated_robot_val})

        # Appending robot data to the keyNode
        for robot_key_val_pairs in robot_data:
            for robot_Label, robot_Value in robot_key_val_pairs.items():
                if robot_Value:
                    if "v" in robot_Value.keys() and (not robot_Value["v"]):
                        continue
                    robot_child_dict = dict()
                    robot_child_dict["id"] = "key_detail_" + str(start_idx)
                    robot_child_dict["label"] = robot_Label
                    robot_child_dict["pageId"] = robot_Value["pageId"]
                    robot_child_dict["pos"] = robot_Value["pos"]
                    robot_child_dict["type"] = "key_detail_robot"
                    if robot_Value.get("qualifierParent"):
                        robot_child_dict["qualifierParent"] = robot_Value.get(
                            "qualifierParent"
                        )
                    robot_child_dict["STATUS"] = 200
                    try:
                        robot_child_dict["unique_id"] = "robot_unique_id" + str(
                            start_idx
                        )
                    except:
                        pass
                    # ommitting keyname and anything before it
                    robot_child_dict["v"] = robot_Value["v"]
                    start_idx += 1
                    robot_children_list.append(robot_child_dict)

        if key_node and robot_children_list:
            key_node["children"] += robot_children_list
        else:
            key_node = dict()
            key_node["id"] = "key_" + str(input_doc_idx)
            key_node["pos"] = ""
            key_node["type"] = "key"
            key_node["pageId"] = ""
            key_node["STATUS"] = 200
            key_node["children"] = robot_children_list
            d_json["nodes"][input_doc_idx]["children"].append(key_node)
    return d_json


def update_data_json_based_on_definition(request_data,data_json):
    """This function is utilized for updating data_json. For example: everytime the unique_id comes from auto extraction
    it is changed and rules won't get applied as it is based on that unique id so it maps the unique_id and applies the rules.
    """
    definitions = request_data["definitions"]
    if definitions:
        try:
            definitions = definitions[0]
            for node in data_json["nodes"]:
                for document in node["children"]:
                    if document.get("type") == "key":
                        for key_node in document.get("children"):
                            try:
                                id_replaced = False
                                # Update rules Unique id if it maps from auto extraction
                                for rule_item in definitions["key"]["ruleItems"]:
                                    if rule_item.get("id").startswith(
                                        key_node.get("label")
                                    ):
                                        id_replaced = True
                                        key_node["unique_id"] = rule_item["keyId"]
                                if not id_replaced:
                                    for not_in_use_item in definitions["key"]["notInUseItems"]:
                                        if not_in_use_item.get(
                                            "nestedLabel"
                                        ).startswith(key_node.get("label")):
                                            key_node["unique_id"] = not_in_use_item[
                                                "keyId"
                                            ]
                            except:
                                print(traceback.print_exc())
        except:
            print(traceback.print_exc())
            pass

    return data_json
