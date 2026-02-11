"""
Document Processing Script
===========================

Purpose:
--------
This script processes JSON representations of documents, applying transformations, filtering, and restructuring based on specific rules defined for various profiles and document types. The primary goal is to clean, reformat, and enhance the structured data for downstream applications.

Functions:
----------
1. **row_ordering(row_children)**:
   Assigns sequential IDs to the children of a row.
   - **Parameters**:
     - `row_children` (list): A list of child dictionaries for a row.
   - **Returns**:
     - A list of child dictionaries with updated IDs.

2. **generate_empty_row(count)**:
   Creates an empty row dictionary with a unique ID.
   - **Parameters**:
     - `count` (int): The unique index for the row ID.
   - **Returns**:
     - A dictionary representing an empty row.

3. **generate_cell(value, label)**:
   Creates a new cell dictionary with a value and label.
   - **Parameters**:
     - `value` (str): The value of the cell.
     - `label` (str): The label of the cell.
   - **Returns**:
     - A dictionary representing a cell.

4. **sorter(input_list)**:
   Sorts a list of items based on their top position on a page.
   - **Parameters**:
     - `input_list` (list): A list of dictionaries containing positional data.
   - **Returns**:
     - A sorted list of dictionaries.

5. **process(d_json)**:
   The main function to process the input JSON, transforming document nodes based on specific profiles and rules.
   - **Parameters**:
     - `d_json` (dict): The input JSON containing document data.
   - **Returns**:
     - A processed JSON with updated nodes.
   - **Features**:
     - Handles specific profiles (e.g., `"CM_CAMEROON"`, `"LEMOAG_AIR"`, `"US_OFR_DSM"`, etc.).
     - Applies transformations to tables, keys, and nodes:
       - Cleans up redundant rows.
       - Restructures data into new fields.
       - Formats and adjusts specific values (e.g., dimensions, package counts).
     - Supports complex cases such as merging placeholders, updating labels, and managing positional data.
   - **Error Handling**:
     - Uses `try-except` blocks to ensure robust execution and logs errors using `traceback`.

Profiles and Rules:
-------------------
1. **CM_CAMEROON and Bill Of Entry**:
   - Filters `chargesTable` and `entrylinesTable`, removing irrelevant rows and fixing `customsValue` issues.

2. **LEMOAG_AIR and Shippers Letter of Instruction**:
   - Merges sequential `placeHolder` fields where applicable.

3. **US_OFR_DSM and Booking Request**:
   - Processes `CUSTOMTEMPFIELD` and other fields, restructuring data into `CRF`, `SRN`, and `placeHolder`.

4. **CH_LEM_AIR and Shippers Letter of Instruction**:
   - Combines `incoterms` and `placeHolder` into a new `marksAndNumbers` field.

5. **CH_RIETER_AIR_CHMAR001 and Shippers Letter of Instruction**:
   - Formats `MKS` data into `marksAndNumbers` with rules based on `incoterms`.

6. **PL_AFR_TRUMPF and Booking Request**:
   - Converts dimensions from millimeters (MM) to centimeters (CM).

7. **MULTI-MLT and Booking Request**:
   - Extracts package counts from `placeHolder` and creates a new field `packageCount`.

Error Handling:
---------------
- Uses `try-except` blocks to capture and log exceptions for debugging without interrupting the overall processing.

Usage:
------
1. Import the script and call the `process()` function with a valid document JSON.
2. Extend or modify the rules within `process()` for additional profiles or document types.

Example:
--------
```python
processed_json = process(input_json)
print(processed_json)
"""

import re
import traceback

from app.key_central.key_module_central import (
    get_bottom_pos,
    get_left_pos,
    get_right_pos,
    get_top_pos,
)


def row_ordering(row_children):
    count = 0
    for value in row_children:
        value["id"] = "cell_" + str(count)
        count += 1
    return row_children


def generate_empty_row(count):
    row = dict()
    row["id"] = "row_" + str(count)
    row["children"] = list()
    row["type"] = "row"
    row["pos"] = ""
    row["pageId"] = ""
    return row


def generate_cell(value, label):
    new_cell = dict()
    new_cell["children"] = []
    new_cell["unique_id"] = "alternator_v4" + label
    new_cell["type"] = "cell"
    new_cell["v"] = value
    new_cell["label"] = label
    new_cell["id"] = ""
    new_cell["pageId"] = ""
    return new_cell


def sorter(input_list):
    output_list = sorted(input_list, key=lambda k: get_top_pos(k["pos"]))

    return output_list


def process(d_json):
    input_json = d_json.copy()
    profile_id = input_json["DefinitionID"]
    doc_type = input_json["DocumentType"]
    vendor_name = input_json["Vendor"]
    documents = input_json["nodes"]
    # print(profile_id)

    try:
        if (
            "CM_CAMEROON".lower() in profile_id.lower()
            and "Bill Of Entry".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    charges_table = False
                    entrylines_table = False
                    if node.get("type") == "table":
                        first_row = node["children"][0]
                        first_cells = first_row["children"]
                        for first_cell in first_cells:
                            if first_cell.get("label") == "baseAmount":
                                charges_table = True
                                first_pageId = first_cell.get("pageId")
                                break
                            elif first_cell.get("label") == "harmonizedCode":
                                entrylines_table = True
                                first_pageId = first_cell.get("pageId")
                                break
                    if charges_table:
                        rows = node["children"]
                        final_rows = list()
                        for row_idx, row in enumerate(rows):
                            skip_row = False
                            cells = row["children"]
                            for cell_idx, cell in enumerate(cells):
                                if cell.get("pageId") == first_pageId:
                                    skip_row = True
                                    break
                            if skip_row:
                                pass
                            else:
                                final_rows.append(row)
                        node["children"] = final_rows
                    elif entrylines_table:
                        rows = node["children"]
                        final_rows = list()
                        customsvalue_issue = False
                        prev_customsvalue = None
                        for row_idx, row in enumerate(rows):
                            skip_row = False
                            cells = row["children"]

                            cell_labels = [cell.get("label") for cell in cells]
                            if customsvalue_issue:
                                if "customsValue" in cell_labels:
                                    for cell_idx, cell in enumerate(cells):
                                        if cell.get("label") == "customsValue":
                                            temp_customsvalue = cell.copy()
                                            cell = prev_customsvalue.copy()
                                            prev_customsvalue = temp_customsvalue.copy()
                                            cells[cell_idx] = cell
                                else:
                                    cells.append(prev_customsvalue)

                            for cell_idx, cell in enumerate(cells):
                                if row_idx == 0:
                                    if cell.get("label") == "customsValue":
                                        if cell.get("pageId") == first_pageId:
                                            pass
                                        else:
                                            customsvalue_issue = True
                                            prev_customsvalue = cell.copy()
                                    if cell.get("pageId") == first_pageId:
                                        skip_row = True
                            row["children"] = cells
                            if skip_row:
                                pass
                            else:
                                final_rows.append(row)
                        node["children"] = final_rows

    except:
        pass

    try:
        if (
            "LEMOAG_AIR".lower() in profile_id.lower()
            and "Shippers Letter of Instruction".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        rows = node["children"]
                        previous_value = None
                        for row_index, row in enumerate(rows):
                            new_list = list()
                            table_items = row["children"]
                            for index, table_item in enumerate(table_items):
                                label = table_item["label"]
                                if label == "placeHolder":
                                    value = table_item["v"]
                                    if (
                                        "x" not in value.lower()
                                        or value.count("x") == 1
                                    ):
                                        if previous_value != None:
                                            previous_value["v"] = (
                                                previous_value["v"] + " " + value
                                            )
                                        else:
                                            new_list.append(table_item)
                                    else:
                                        new_list.append(table_item)
                                        previous_value = table_item
                                else:
                                    new_list.append(table_item)

                            row["children"] = new_list
                        node["children"] = rows
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        print(traceback.print_exc())
        pass

    try:
        if (
            "US_OFR_DSM".lower() in profile_id.lower()
            and "Booking Request".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        rows = node["children"]
                        value_dict = dict()
                        label_list = list()
                        commodity_code = None
                        pack_type = None
                        marks_and_numbers = list()
                        target_value = dict()
                        value_to_transfer = None
                        new_rows = list()
                        new_rows.append(rows[0])
                        row_count = 1
                        try:
                            for row_index, row in enumerate(rows):
                                new_list = list()
                                table_items = row["children"]
                                for index, table_item in enumerate(table_items):
                                    label = table_item["label"]
                                    if label == "commodityCode":
                                        commodity_code = table_item.copy()
                                    if label == "packageType":
                                        if pack_type == None:
                                            pack_type = table_item.copy()
                                    if label == "marksAndNumbers":
                                        # print("marks", table_item)
                                        if table_item["v"] != "":
                                            marks_and_numbers.append(table_item.copy())
                                    if label not in label_list:
                                        label_list.append(label)
                                        value_dict[label] = list()
                                        value_dict[label].append(table_item)
                                    else:
                                        value_dict[label].append(table_item)

                                row["children"] = table_items
                        except:
                            print(traceback.print_exc())
                            pass
                        if "CUSTOMTEMPFIELD" in label_list:
                            target_value["CRF"] = list()
                            target_value["SRN"] = list()
                            for commodity_value in value_dict["CUSTOMTEMPFIELD"]:
                                left_pos = get_left_pos(commodity_value["pos"])
                                if left_pos < 200:
                                    new_row = generate_empty_row(row_count)
                                    new_rows.append(new_row)
                                    row_count = row_count + 1
                                if len(commodity_value["v"]) < 8:
                                    value_to_transfer = commodity_value.copy()
                                    print("value", value_to_transfer)
                                    print(label_list)
                                    value_to_transfer["label"] = "placeHolder"
                                    if "placeHolder" in label_list:
                                        value_dict["placeHolder"].append(
                                            value_to_transfer
                                        )
                                    else:
                                        value_dict["placeHolder"] = list()
                                        label_list.append("placeHolder")
                                        value_dict["placeHolder"].append(
                                            value_to_transfer
                                        )
                                    # print("value", value_dict["placeHolder"])
                                elif len(commodity_value["v"]) < 15:
                                    if left_pos > 250 and left_pos < 650:
                                        commodity_value["label"] = "CRF"
                                        commodity_value[
                                            "qualifierParent"
                                        ] = "references"
                                        target_value["CRF"].append(commodity_value)
                                    elif left_pos > 700:
                                        commodity_value["label"] = "SRN"
                                        commodity_value[
                                            "qualifierParent"
                                        ] = "references"
                                        target_value["SRN"].append(commodity_value)
                                elif len(commodity_value["v"]) < 25:
                                    commodity_value["v"] = commodity_value["v"].strip()
                                    if left_pos < 225:
                                        commodity_value["v"] = commodity_value[
                                            "v"
                                        ].split(" ")[1]
                                        commodity_value["label"] = "CRF"
                                        commodity_value[
                                            "qualifierParent"
                                        ] = "references"
                                        target_value["CRF"].append(commodity_value)
                                    elif left_pos > 300:
                                        commodity_value["v"] = commodity_value[
                                            "v"
                                        ].strip()
                                        crf = commodity_value.copy()
                                        crf["v"] = commodity_value["v"].split(" ")[0]
                                        crf["label"] = "CRF"
                                        crf["qualifierParent"] = "references"
                                        target_value["CRF"].append(crf)
                                        commodity_value["v"] = commodity_value[
                                            "v"
                                        ].split(" ")[1]
                                        commodity_value["label"] = "SRN"
                                        commodity_value[
                                            "qualifierParent"
                                        ] = "references"
                                        target_value["SRN"].append(commodity_value)
                                elif len(commodity_value["v"]) < 37:
                                    crf = commodity_value.copy()
                                    crf["v"] = commodity_value["v"].split(" ")[1]
                                    crf["label"] = "CRF"
                                    crf["qualifierParent"] = "references"
                                    target_value["CRF"].append(crf)
                                    commodity_value["v"] = commodity_value["v"].split(
                                        " "
                                    )[2]
                                    commodity_value["label"] = "SRN"
                                    commodity_value["qualifierParent"] = "references"
                                    target_value["SRN"].append(commodity_value)
                        if "placeHolder" in label_list:
                            target_value["placeHolder"] = list()
                            goods_anchor = 1600
                            if "goodsDescription" in label_list:
                                goods_anchor = get_left_pos(
                                    value_dict["goodsDescription"][0]["pos"]
                                )
                            value_dict["placeHolder"] = sorter(
                                value_dict["placeHolder"]
                            )
                            for place_holder_value in value_dict["placeHolder"]:
                                right_pos = get_right_pos(place_holder_value["pos"])
                                if right_pos < goods_anchor:
                                    target_value["placeHolder"].append(
                                        place_holder_value
                                    )
                                else:
                                    split_value = place_holder_value["v"].split(" ", 1)
                                    place_holder_value["v"] = split_value[0]
                                    value_to_transfer = place_holder_value.copy()
                                    value_to_transfer["label"] = "goodsDescription"
                                    value_to_transfer["v"] = split_value[1]
                                    if "goodsDescription" in label_list:
                                        value_dict["goodsDescription"].append(
                                            value_to_transfer
                                        )
                                    else:
                                        value_dict["goodsDescription"] = list()
                                        label_list.append("goodsDescription")
                                        value_dict["goodsDescription"].append(
                                            value_to_transfer
                                        )
                                    target_value["placeHolder"].append(
                                        place_holder_value
                                    )
                        if "goodsDescription" in label_list:
                            target_value["goodsDescription"] = list()
                            value_dict["goodsDescription"] = sorter(
                                value_dict["goodsDescription"]
                            )
                            for goods_description_value in value_dict[
                                "goodsDescription"
                            ]:
                                target_value["goodsDescription"].append(
                                    goods_description_value
                                )
                        if "harmonizedCode" in label_list:
                            target_value["harmonizedCode"] = list()
                            for hsindex, hsvalue in enumerate(
                                value_dict["harmonizedCode"]
                            ):
                                hsvalue_left_pos = get_left_pos(hsvalue["pos"])
                                hsvalue_right_pos = get_right_pos(hsvalue["pos"])
                                try:
                                    if hsindex == 0:
                                        if len(hsvalue["v"]) < 4:
                                            pass
                                        else:
                                            if hsvalue["v"][0] == ".":
                                                hsvalue["v"] = hsvalue["v"][1:]
                                            hsvalue["v"] = hsvalue["v"].strip()
                                            target_value["harmonizedCode"].append(
                                                hsvalue
                                            )
                                    elif (
                                        hsindex < len(value_dict["harmonizedCode"]) - 1
                                    ):
                                        try:
                                            if hsvalue_right_pos < get_left_pos(
                                                value_dict["harmonizedCode"][
                                                    hsindex + 1
                                                ]["pos"]
                                            ) or hsvalue_right_pos < get_left_pos(
                                                value_dict["harmonizedCode"][
                                                    hsindex - 1
                                                ]["pos"]
                                            ):
                                                pass
                                            else:
                                                if hsvalue["v"][0] == ".":
                                                    hsvalue["v"] = hsvalue["v"][1:]
                                                hsvalue["v"] = hsvalue["v"].strip()
                                                target_value["harmonizedCode"].append(
                                                    hsvalue
                                                )
                                        except:
                                            print(traceback.print_exc())
                                            pass
                                    else:
                                        if hsvalue["v"][0] == ".":
                                            hsvalue["v"] = hsvalue["v"][1:]
                                        hsvalue["v"] = hsvalue["v"].strip()
                                        target_value["harmonizedCode"].append(hsvalue)
                                except:
                                    print(traceback.print_exc())
                                    target_value["harmonizedCode"].append(hsvalue)

                        # print("target_value", target_value)
                        target_keys = list(target_value.keys())
                        final_target_dict = dict()
                        if "CRF" in target_keys:
                            final_target_dict["CRF"] = list()
                            for crf in target_value["CRF"]:
                                final_target_dict["CRF"].append(crf)
                        if "SRN" in target_keys:
                            final_target_dict["SRN"] = list()
                            for srn in target_value["SRN"]:
                                final_target_dict["SRN"].append(srn)
                        if "placeHolder" in target_keys:
                            final_target_dict["placeHolder"] = list()
                            if len(target_value["placeHolder"]) == len(
                                target_value["CRF"]
                            ):
                                for place_holder in target_value["placeHolder"]:
                                    final_target_dict["placeHolder"].append(
                                        place_holder
                                    )
                            else:
                                target_placeholder = None
                                target_position = None
                                for place_index, place_holder in enumerate(
                                    target_value["placeHolder"]
                                ):
                                    if place_index == 0:
                                        target_placeholder = place_holder.copy()
                                        target_position = get_top_pos(
                                            place_holder["pos"]
                                        )
                                    else:
                                        if (
                                            get_top_pos(place_holder["pos"])
                                            - target_position
                                        ) < 100:
                                            target_placeholder["v"] = (
                                                target_placeholder["v"]
                                                + " "
                                                + place_holder["v"]
                                            )
                                            target_position = get_top_pos(
                                                place_holder["pos"]
                                            )
                                        else:
                                            final_target_dict["placeHolder"].append(
                                                target_placeholder
                                            )
                                            target_placeholder = place_holder.copy()
                                            target_position = get_top_pos(
                                                place_holder["pos"]
                                            )
                                final_target_dict["placeHolder"].append(
                                    target_placeholder
                                )
                        if "goodsDescription" in target_keys:
                            final_target_dict["goodsDescription"] = list()
                            target_goods = None
                            for goods_index, goods_description in enumerate(
                                target_value["goodsDescription"]
                            ):
                                if target_goods == None:
                                    target_goods = goods_description.copy()
                                else:
                                    if (
                                        len(goods_description["v"]) == 10
                                        and goods_description["v"].isdigit() == True
                                    ):
                                        target_goods["v"] = (
                                            target_goods["v"]
                                            + " "
                                            + goods_description["v"]
                                        )
                                        final_target_dict["goodsDescription"].append(
                                            target_goods
                                        )
                                        target_goods = None
                                    else:
                                        target_goods["v"] = (
                                            target_goods["v"]
                                            + " "
                                            + goods_description["v"]
                                        )
                        if "harmonizedCode" in target_keys:
                            final_target_dict["harmonizedCode"] = list()
                            target_hs_pos = None
                            target_hs = None
                            for hs_index, harmonized_code in enumerate(
                                target_value["harmonizedCode"]
                            ):
                                if target_hs_pos == None:
                                    target_hs_pos = get_bottom_pos(
                                        harmonized_code["pos"]
                                    )
                                    target_hs = harmonized_code.copy()
                                else:
                                    if (
                                        get_top_pos(harmonized_code["pos"])
                                        - target_hs_pos
                                        < 100
                                    ):
                                        target_hs["v"] = (
                                            target_hs["v"] + harmonized_code["v"]
                                        )
                            final_target_dict["harmonizedCode"].append(target_hs)

                        # print("final_target_dict", final_target_dict)
                        srn_count = 0
                        place_holder_count = 0
                        marks_count = 0
                        for row_index, new_row in enumerate(new_rows):
                            if row_index == 0:
                                pass
                            else:
                                try:
                                    if "CRF" in final_target_dict.keys():
                                        new_row["children"].append(
                                            final_target_dict["CRF"][row_index - 1]
                                        )
                                        anchor_pos = get_top_pos(
                                            final_target_dict["CRF"][row_index - 1][
                                                "pos"
                                            ]
                                        )
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "SRN" in final_target_dict.keys():
                                        if len(final_target_dict["SRN"]) == len(
                                            final_target_dict["CRF"]
                                        ):
                                            new_row["children"].append(
                                                final_target_dict["SRN"][row_index - 1]
                                            )
                                        else:
                                            if (
                                                abs(
                                                    get_top_pos(
                                                        final_target_dict["SRN"][
                                                            srn_count
                                                        ]["pos"]
                                                    )
                                                    - anchor_pos
                                                )
                                                < 80
                                            ):
                                                new_row["children"].append(
                                                    final_target_dict["SRN"][srn_count]
                                                )
                                                srn_count = srn_count + 1
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "placeHolder" in final_target_dict.keys():
                                        if len(final_target_dict["placeHolder"]) == len(
                                            final_target_dict["CRF"]
                                        ):
                                            new_row["children"].append(
                                                final_target_dict["placeHolder"][
                                                    row_index - 1
                                                ]
                                            )
                                        else:
                                            if (
                                                abs(
                                                    get_top_pos(
                                                        final_target_dict[
                                                            "placeHolder"
                                                        ][place_holder_count]["pos"]
                                                    )
                                                    - anchor_pos
                                                )
                                                < 80
                                            ):
                                                new_row["children"].append(
                                                    final_target_dict["placeHolder"][
                                                        place_holder_count
                                                    ]
                                                )
                                                place_holder_count = (
                                                    place_holder_count + 1
                                                )
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "goodsDescription" in final_target_dict.keys():
                                        new_row["children"].append(
                                            final_target_dict["goodsDescription"][
                                                row_index - 1
                                            ]
                                        )
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "harmonizedCode" in final_target_dict.keys():
                                        if row_index == 1:
                                            new_row["children"].append(
                                                final_target_dict["harmonizedCode"][0]
                                            )
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "commodityCode" in label_list:
                                        new_row["children"].append(commodity_code)
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "packageType" in label_list:
                                        new_row["children"].append(pack_type)
                                except:
                                    print(traceback.print_exc())
                                    pass
                                try:
                                    if "marksAndNumbers" in label_list:
                                        new_row["children"].append(
                                            marks_and_numbers[marks_count]
                                        )
                                        marks_count = marks_count + 1
                                except:
                                    print(traceback.print_exc())
                                    pass
                            new_row["children"] = row_ordering(new_row["children"])
                        node["children"] = new_rows
                    nodes[node_idx] = node
    except:
        pass
    try:
        if (
            "CH_LEM_AIR".lower() in profile_id.lower()
            and "Shippers Letter of Instruction".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        new_list = list()
                        key_value_items = node["children"]
                        inco_terms = None
                        place_holder = None
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "incoterms":
                                inco_terms = key_value_item["v"]
                                inco_terms = inco_terms.split(" ")[0]
                            if label == "placeHolder":
                                place_holder = key_value_item["v"]
                            if inco_terms and place_holder:
                                place_holder = inco_terms + " " + place_holder
                                key_value_item["v"] = place_holder
                                key_value_item["label"] = "marksAndNumbers"
                            new_list.append(key_value_item)
                        node["children"] = new_list
                        nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        print(traceback.print_exc())
        pass
    try:
        if (
            "CH_RIETER_AIR_CHMAR001".lower() in profile_id.lower()
            and "Shippers Letter of Instruction".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        new_list = list()
                        key_value_items = node["children"]
                        inco_terms = ""
                        inco1 = ["CPT", "DAP", "CIP", "DDP", "CIF"]
                        inco2 = ["EXW", "FCA"]
                        marks_and_number = " "
                        m_k_s = ""
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "incoterms":
                                inco_terms = key_value_item["v"]
                                inco_terms = inco_terms.split(" ")[0]
                            if label == "MKS":
                                # if "MKS" in label and "marksAndNumbers" in label["MKS"]:
                                #     # if marks.get("qualifierValue"):
                                #         marks_and_number = label["MKS"]["marksAndNumbers"]
                                #         print(marks_and_number)
                                marks_and_number = key_value_item["v"]
                                try:
                                    if inco_terms in inco1:
                                        m_k_s = (
                                            "FREIGHT PREPAID / "
                                            + inco_terms
                                            + "\n"
                                            + "MARKS: "
                                            + marks_and_number
                                        )
                                    elif inco_terms in inco2:
                                        m_k_s = (
                                            "FREIGHT COLLECT / "
                                            + inco_terms
                                            + "\n"
                                            + "MARKS: "
                                            + marks_and_number
                                        )

                                except:
                                    print(traceback.print_exc())
                                    pass
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "MKS":
                                key_value_item["v"] = m_k_s
                    nodes[node_idx] = node
            document["children"] = nodes
            documents[document_idx] = document

    except:
        print(traceback.print_exc())
        pass

    try:
        if (
            "PL_AFR_TRUMPF".lower() in profile_id.lower()
            and "Booking Request".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        rows = node["children"]
                        for row_index, row in enumerate(rows):
                            new_list = list()
                            table_items = row["children"]
                            for index, table_item in enumerate(table_items):
                                label = table_item["label"]
                                if label == "dimensions":
                                    value = table_item["v"]
                                    if "MM" in value:
                                        dimension = ""
                                        value = value.replace("MM", "")
                                        value = value.replace("Dim.", "")
                                        value = value.replace("Dim", "")
                                        uom = "CM"
                                        value = value.split("/")
                                        for val in value:
                                            val = val.strip()
                                            val = int(val)
                                            val = int(val / 10)
                                            val = str(val)
                                            dimension += val + "/ "
                                        dimension = dimension[:-2]
                                        dimension = dimension + " " + uom
                                        print(dimension)
                                        table_item["v"] = dimension
                                new_list.append(table_item)
                            row["children"] = new_list
                        node["children"] = rows
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document

    except:
        print(traceback.print_exc())
        pass

    # try:
    #     if "IT_HENKEL_SEA".lower() in profile_id.lower() and "Shippers Letter of Instruction".lower() in doc_type.lower():
    #         for document_idx, document in enumerate(documents):
    #             nodes = document['children']
    #             for node_idx, node in enumerate(nodes):
    #                 if node['type'] == 'table':

    #                     rows = node['children']
    #                     for row_index, row in enumerate(rows):
    #                         new_list = list()
    #                         goods_description = ""
    #                         gross_weight = ""
    #                         package_id = ""
    #                         not_in_use = ""
    #                         not_in_use10 = ""
    #                         goods_undg = ""
    #                         table_items = row["children"]
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'goodsDescription':
    #                                 goods_description = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'grossWeight':
    #                                 gross_weight = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'packageID':
    #                                 package_id = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'notInUse':
    #                                 not_in_use = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'filler':
    #                                 not_in_use10 = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == '_UNDGNumber':
    #                                 if value.strip()!= "":
    #                                     undg_number = value
    #                         for index, table_item in enumerate(table_items):
    #                             label = table_item["label"]
    #                             value = table_item["v"]
    #                             if label == 'commodityCode' and value == "DGD":
    #                                 goods_undg = undg_number
    #                         print("goods", goods_description)
    #                         print("gross", gross_weight)
    #                         print("package", package_id)
    #                         print("not", not_in_use)
    #                         print("not10", not_in_use10)
    #                         print("undg", goods_undg)
    #                         goods_description = goods_description + gross_weight + package_id + not_in_use +not_in_use10 + goods_undg
    #                         print("goods", goods_description)
    #                         new_list.append(table_item)
    #                         row["children"] = new_list
    #                     print("rows", rows)
    #                     node["children"] = rows
    #                 print("node", node)
    #                 nodes[node_idx] = node
    #             document["children"] = nodes
    #             documents[document_idx] = document
    # except:
    #     print(traceback.print_exc())
    #     pass
    try:
        if (
            "MULTI-MLT".lower() in profile_id.lower()
            and "Booking Request".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        rows = node["children"]
                        for row_index, row in enumerate(rows):
                            package_count = "1"
                            new_list = list()
                            table_items = row["children"]
                            for table_index, table_item in enumerate(table_items):
                                label = table_item["label"]
                                if label == "placeHolder":
                                    pos = table_item["pos"]
                                    value = table_item["v"]
                                    pageId = table_item["pageId"]
                                    try:
                                        match = re.findall(r"\.\.\.(\d+) nos\.", value)
                                        if match:
                                            package_count = str(match[0])
                                        new_list.append(table_item)
                                        cell2 = generate_cell(
                                            package_count, "packageCount"
                                        )
                                        new_list.append(cell2)
                                        # print(new_list)
                                    except:
                                        pass
                                else:
                                    new_list.append(table_item)
                            row["children"] = new_list
                        node["children"] = rows
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document

        return input_json
    except:
        print(traceback.print_exc())
        pass

    return d_json
