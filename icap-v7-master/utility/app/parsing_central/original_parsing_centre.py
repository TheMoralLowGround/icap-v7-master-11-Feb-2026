import traceback

from app.misc_modules.unique_id import assign_unique_id_helper
from app.misc_modules.usable_function_list import generate_dim_cells
from app.parsing_central.parsers import (
    dimension_uom,
    financial_parser,
    height_uom,
    incoterms_parser,
    length_uom,
    location_name_parser_updated,
    package_count,
    temperature_parser,
    value_of_goods_parser,
    volume_uom,
    weight_uom,
    width_uom,
)
from app.table_keys import get_replacement_value

# @Emon 29/08/2022 - One key_node parsing failure impacts resulting docs-bug fixed by adding try except.
# @Emon 03/09/2022 - Similar as 29-Aug done for cell and row levels

"""
This is the central script that handles all parsing related tasks.
This is immediately after key extraction and rules.
"""


def get_parser_type(input_label, set_parsers):
    financial_value_labels = set_parsers.get("financial_value_labels")
    if not input_label:
        return None
    if input_label in financial_value_labels:
        return "financial_parser"
    if input_label.lower().endswith("weight"):
        return "weight_UOM"
    elif input_label.lower().endswith("volume"):
        return "volume_UOM"
    elif input_label.endswith("packagecount"):
        return "packageCount"
    elif input_label == "requirestemperaturecontrol":
        return "temperature_parser"
    # elif input_label.endswith("dimensions"):
    #     return "dimension_UOM"
    elif input_label.endswith("incoterms"):
        return "incoterms_parser"
    elif input_label.lower().endswith("locationname"):
        return "locationName_parser"
    elif "valueofgoods" in input_label.lower():
        return "valueOfGoods_parser"
    elif input_label == "height":
        return "height_UOM"
    elif input_label == "length":
        return "length_UOM"
    elif input_label == "width":
        return "width_UOM"
    return None


def generate_cell(value, label, input_cell):
    new_cell = input_cell.copy()
    new_cell["v"] = value.strip()
    new_cell["label"] = label
    return new_cell


def generate_keyNode(value, label, input_keyNode):
    new_key_node = input_keyNode.copy()
    new_key_node["v"] = value.strip()
    new_key_node["label"] = label
    return new_key_node


def parse_table_rows(node_children, definition_settings, master_dictionaries):
    # Added by emon on 08/10/2022 - Changing how dimensions are appended
    dimension_data_set = dict()
    start_index = None
    financial_value_labels = list()
    key_options_items = (
        definition_settings.get("options", {}).get("options-keys", {}).get("items")
    )
    for x in key_options_items:
        if x.get("modType") == "Financial Value":
            financial_value_labels.append(x["keyValue"])
    set_parsers = dict()
    set_parsers["financial_value_labels"] = financial_value_labels
    for row_idx, row in enumerate(node_children):
        try:
            dimension_uom_available = False
            dimension_uom_data = None
            currency_available = False
            currency_data = None
            cells = row["children"]
            processed_cells = list()
            for cell_idx, cell in enumerate(cells):
                try:
                    label = cell["label"]
                    parser_type = get_parser_type(label, set_parsers)
                    if parser_type == "weight_UOM":
                        parsed_value_list = weight_uom.process(cell["v"])
                        if len(parsed_value_list) == 3:
                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]
                            cell1 = generate_cell(number.strip(), label, cell)

                            # Adding Cell2
                            cell2 = generate_cell(uom.strip(), label + "Uom", cell)

                            processed_cells.append(cell1)
                            processed_cells.append(cell2)

                            # For extra element
                            if parsed_value_list[-1]:
                                cell3 = generate_cell(
                                    parsed_value_list[-1].strip(), label + "_1", cell
                                )
                                processed_cells.append(cell3)

                        else:
                            processed_cells.append(cell)

                    elif parser_type == "volume_UOM":
                        parsed_value_list = volume_uom.process(cell["v"])
                        if len(parsed_value_list) == 3:
                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2 = generate_cell(uom.strip(), label + "Uom", cell)

                            processed_cells.append(cell1)
                            processed_cells.append(cell2)
                            # For extra element
                            if parsed_value_list[-1]:
                                cell3 = generate_cell(
                                    parsed_value_list[-1].strip(), label + "_1", cell
                                )
                                processed_cells.append(cell3)
                        else:
                            processed_cells.append(cell)

                    elif parser_type == "valueOfGoods_parser":
                        parsed_value_list = value_of_goods_parser.process(cell["v"])
                        if len(parsed_value_list) == 3:
                            number = parsed_value_list[0]
                            currency_code = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2 = generate_cell(
                                currency_code.strip(), label + "Currency", cell
                            )

                            processed_cells.append(cell1)
                            processed_cells.append(cell2)
                            # For extra element
                            if parsed_value_list[-1]:
                                cell3 = generate_cell(
                                    parsed_value_list[-1].strip(), label + "_1", cell
                                )
                                processed_cells.append(cell3)
                        else:
                            processed_cells.append(cell)

                    elif parser_type == "packageCount":
                        parsed_value_list = package_count.process(cell["v"])
                        if len(parsed_value_list) == 3:
                            # Retaining the original cell
                            # processed_cells.append(cell)

                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2_label = label
                            if "inner" in label:
                                cell2_label = "innerPackageType"
                            elif "total" in label:
                                cell2_label = "totalPackageType"
                            else:
                                cell2_label = "packageType"

                            cell2 = generate_cell(uom.strip(), cell2_label, cell)

                            processed_cells.append(cell1)
                            processed_cells.append(cell2)
                            # For extra element
                            if parsed_value_list[-1]:
                                cell3 = generate_cell(
                                    parsed_value_list[-1].strip(), label + "_1", cell
                                )
                                processed_cells.append(cell3)
                        else:
                            processed_cells.append(cell)

                    elif parser_type == "temperature_parser":
                        parsed_value_list = temperature_parser.process(cell["v"])
                        if len(parsed_value_list) == 4:
                            # Retaining the original cell
                            processed_cells.append(cell)

                            requires_temperature_control = parsed_value_list[0]
                            required_maximum = parsed_value_list[1]
                            required_minimum = parsed_value_list[2]
                            temperature_uom = parsed_value_list[3]

                            # Adding Cell1
                            cell1 = generate_cell(
                                requires_temperature_control.strip(),
                                "requiresTemperatureControl",
                                cell,
                            )
                            # Adding Cell2
                            cell2 = generate_cell(
                                required_maximum.strip(), "requiredMaximum", cell
                            )
                            # Adding Cell3
                            cell3 = generate_cell(
                                required_minimum.strip(), "requiredMinimum", cell
                            )
                            # Adding Cell4
                            cell4 = generate_cell(
                                temperature_uom.strip(), "temperatureUom", cell
                            )

                            processed_cells.append(cell1)
                            processed_cells.append(cell2)
                            processed_cells.append(cell3)
                            processed_cells.append(cell4)
                        elif len(parsed_value_list) == 1:
                            # Retaining the original cell
                            processed_cells.append(cell)

                            requires_temperature_control = parsed_value_list[0]

                            # Adding Cell1
                            cell1 = generate_cell(
                                requires_temperature_control.strip(),
                                "requiresTemperatureControl",
                                cell,
                            )

                            processed_cells.append(cell1)
                        else:
                            processed_cells.append(cell)

                    elif parser_type == "dimension_UOM":
                        # Added by emon on 08/10/2022 - Changing how dimensions are appended
                        if row_idx == 0:
                            start_index = cell_idx
                        parsed_value_list = dimension_uom.process(cell["v"])
                        # print("parsed_value_list", parsed_value_list)
                        for idx, inner_list in enumerate(parsed_value_list):
                            cells_to_be_appended = generate_dim_cells(
                                cell, idx, inner_list
                            )

                            if not cells_to_be_appended:
                                processed_cells.append(cell)

                            # Added by emon on 08/10/2022 - Changing how dimensions are appended-
                            dim_target_row = row_idx
                            if len(parsed_value_list) > 1:
                                dim_target_row = idx
                            if cells_to_be_appended:
                                for x in cells_to_be_appended:
                                    if x["label"] != "dimensions":
                                        x["parentLabel"] = "dimensions"
                            dim_data = {
                                "startIndex": start_index,
                                "cells": cells_to_be_appended,
                            }
                            dimension_data_set[dim_target_row] = dim_data

                    elif parser_type == "height_UOM":
                        parsed_value_list = height_uom.process(cell["v"])
                        if len(parsed_value_list) == 2:
                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2 = generate_cell(uom.strip(), "dimensionsUom", cell)

                            processed_cells.append(cell1)
                            if not dimension_uom_available:
                                dimension_uom_available = True
                                # processed_cells.append(cell2)
                                dimension_uom_data = cell2

                        else:
                            processed_cells.append(cell)
                    elif parser_type == "financial_parser":
                        currency_dict = master_dictionaries.get(
                            "currencySymbolToCode"
                        ).get("data")
                        parsed_value_list = financial_parser.process(
                            cell["v"], currency_dict
                        )
                        if len(parsed_value_list) == 2:
                            number = parsed_value_list[0]
                            currency = parsed_value_list[1]
                            cell1 = generate_cell(number, cell["label"], cell)
                            # currency_label = cell["label"] + \
                            #     "Currency"
                            currency_label = "Currency"
                            cell2 = generate_cell(currency, currency_label, cell)

                            processed_cells.append(cell1)
                            # processed_cells.append(cell2)
                            if not currency_available:
                                currency_available = True
                                currency_data = cell2
                        else:
                            processed_cells.append(cell)

                    elif parser_type == "width_UOM":
                        parsed_value_list = width_uom.process(cell["v"])
                        if len(parsed_value_list) == 2:
                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2 = generate_cell(uom.strip(), "dimensionsUom", cell)

                            processed_cells.append(cell1)
                            if not dimension_uom_available:
                                dimension_uom_available = True
                                dimension_uom_data = cell2
                                # processed_cells.append(cell2)

                        else:
                            processed_cells.append(cell)
                    elif parser_type == "length_UOM":
                        parsed_value_list = length_uom.process(cell["v"])
                        if len(parsed_value_list) == 2:
                            number = parsed_value_list[0]
                            uom = parsed_value_list[1]

                            # Adding Cell1
                            cell1 = generate_cell(number.strip(), label, cell)
                            # Adding Cell2
                            cell2 = generate_cell(uom.strip(), "dimensionsUom", cell)

                            processed_cells.append(cell1)
                            if not dimension_uom_available:
                                dimension_uom_available = True
                                dimension_uom_data = cell2
                                # processed_cells.append(cell2)
                        else:
                            processed_cells.append(cell)

                    else:
                        processed_cells.append(cell)
                except AttributeError:
                    processed_cells.append(cell)
                except:
                    print(traceback.print_exc())
                    processed_cells.append(cell)

            try:
                if dimension_uom_data:
                    processed_cells.append(dimension_uom_data)
                if currency_data:
                    processed_cells.append(currency_data)
            except:
                pass

            # if processed_cells:
            row["children"] = processed_cells
            if row["children"]:
                node_children[row_idx] = row

        except:
            node_children[row_idx] = row
    try:

        def get_table_key_generated_cells(pre_rows):
            output_labels = list()
            for x in pre_rows:
                if x.get("table_key_generated") and (
                    x.get("parentLabel") != "dimensions"
                ):
                    output_labels.append(x["label"])
            return output_labels

        # Added by emon on 08/10/2022 - Changing how dimensions are appended
        if dimension_data_set:
            for key, dim_data in dimension_data_set.items():
                dim_cells = dim_data["cells"]
                dim_cells_labels = [x["label"] for x in dim_cells]
                start_index = dim_data["startIndex"]
                additional_cells = list()
                if key > 0:
                    """If a second row indeed is created
                    check if the first row contained any cell that is table key generated
                    """
                    first_row_cells = node_children[0]["children"]
                    for top_cell in first_row_cells:
                        # If table key generated cells exist on the first row then will also be shifted apart from the dimensions related fields and cells of multiples type cells
                        if not top_cell in dim_cells and (
                            not top_cell["label"] in dim_cells_labels
                        ):
                            if top_cell.get(
                                "table_key_generated"
                            ):  # and (not top_cell.get("parser_generated")):
                                a = top_cell.copy()
                                a["v"] = get_replacement_value(a)
                                additional_cells.append(a)

                if additional_cells:
                    # @Emon on 17/10/2022 : Added Table Key Precendence
                    table_key_generated_keys = get_table_key_generated_cells(
                        additional_cells
                    )
                    dim_cells = [
                        x
                        for x in dim_cells
                        if not x["label"] in table_key_generated_keys
                    ]
                    dim_cells = additional_cells + dim_cells
                try:
                    if dim_cells:
                        pre_rows = node_children[key]["children"]
                        # @Emon on 17/10/2022 : Added Table Key Precendence
                        table_key_generated_keys = get_table_key_generated_cells(
                            pre_rows
                        )
                        dim_cells = [
                            x
                            for x in dim_cells
                            if not x["label"] in table_key_generated_keys
                        ]

                        if start_index:
                            node_children[key]["children"] = (
                                pre_rows[:start_index]
                                + dim_cells
                                + pre_rows[start_index:]
                            )
                        else:
                            node_children[key]["children"].extend(dim_cells)
                except:
                    row_dict = dict()
                    row_dict["children"] = dim_cells
                    row_dict["type"] = "row"
                    row_dict["id"] = "row_manual" + "_" + str(key)
                    node_children.append(row_dict)

    except:
        print(traceback.print_exc())
        pass

    return node_children


def parser_main(input_json, definition_settings, request_data):
    # Parsing Centre v5.1.09042023
    # On 06-09-2022 @Emon added length, width parser and and made a offset of of dimensions UOM resulting from these
    # 07-09-2022 @Emon added unique id update for all parsed keyNodes
    # @Emon on 27/09/2022 - Added parsing generated field for dimensions
    # @Emon on 07/10/2022 - Destination printing two locationName nodes fixed
    # @Emon on 08/10/2022 - Changing how dimensions are appended
    # @Emon on 10/10/2022 - Bug Fix for multiple dimension, last dimension visible in each row
    # @Emon on 13/10/2022 - Attribute except clause added
    # @Emon on 17/10/2022 - Added Table Key Precendence
    # @Emon on 19/10/2022 - Bug fix: Dimension parsed values sometimes disappear in between cells- by Elvir
    # @Emon on 22/11/2022 - Dim block shifted to function list
    # @Emon on 08/02/2023 - Table rows parsing shifted as a seperate function for usage
    # @Emon on 23/02/2023 - Code Refactoring Done
    # @Almas on 04/09/2023 - Financial parser modType added
    global master_dictionaries
    master_dictionaries = request_data.get("master_dictionaries")
    print("Parsing Centre Triggered")
    output_json = input_json.copy()
    docs = output_json["nodes"]
    financial_value_labels = list()
    key_options_items = (
        definition_settings.get("options", {}).get("options-keys", {}).get("items")
    )
    for x in key_options_items:
        if x.get("modType") == "Financial Value":
            financial_value_labels.append(x["keyValue"])

    set_parsers = dict()
    set_parsers["financial_value_labels"] = financial_value_labels
    try:
        for input_doc_idx, target_doc in enumerate(docs):
            nodes = target_doc["children"]
            for i, node in enumerate(nodes):
                node_children = node["children"]

                if "table" in node["type"]:
                    node["children"] = parse_table_rows(
                        node_children, definition_settings, master_dictionaries
                    )
                    assign_unique_id_helper(node)

                elif "key" in node["type"]:
                    processed_key_nodes = list()

                    append_count = 0

                    for key_node in node_children:
                        label = key_node["label"]
                        parser_type = get_parser_type(label, set_parsers)
                        # print(parser_type)
                        try:
                            if parser_type == "weight_UOM":
                                parsed_value_list = weight_uom.process(key_node["v"])
                                if len(parsed_value_list) == 3:
                                    number = parsed_value_list[0]
                                    uom = parsed_value_list[1]
                                    # Adding Keynode1
                                    key_node1 = generate_keyNode(
                                        number.strip(), label, key_node
                                    )

                                    # Adding Cell2
                                    key_node2 = generate_keyNode(
                                        uom.strip(), label + "Uom", key_node
                                    )

                                    try:
                                        key_node2["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node2["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    # For extra element
                                    if parsed_value_list[-1]:
                                        key_node3 = generate_keyNode(
                                            parsed_value_list[-1].strip(),
                                            label,
                                            key_node,
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1
                                        processed_key_nodes.append(key_node3)
                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "volume_UOM":
                                parsed_value_list = volume_uom.process(key_node["v"])
                                if len(parsed_value_list) == 3:
                                    number = parsed_value_list[0]
                                    uom = parsed_value_list[1]
                                    # Adding KeyNode1
                                    key_node1 = generate_keyNode(
                                        number.strip(), label, key_node
                                    )

                                    # Adding key_node2
                                    key_node2 = generate_keyNode(
                                        uom.strip(), label + "Uom", key_node
                                    )
                                    try:
                                        key_node2["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node2["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    if parsed_value_list[-1]:
                                        key_node3 = generate_keyNode(
                                            parsed_value_list[-1].strip(),
                                            label + "_1",
                                            key_node,
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1
                                        processed_key_nodes.append(key_node3)
                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "packageCount":
                                parsed_value_list = package_count.process(key_node["v"])
                                if len(parsed_value_list) == 3:
                                    number = parsed_value_list[0]
                                    uom = parsed_value_list[1]
                                    # Adding key_node1

                                    key_node1 = generate_keyNode(
                                        number.strip(), label, key_node
                                    )
                                    # Adding key_node2

                                    key_node2_label = label
                                    if "inner" in label:
                                        key_node2_label = "innerPackageType"
                                    elif "total" in label:
                                        key_node2_label = "totalPackageType"
                                    else:
                                        key_node2_label = "packageType"

                                    key_node2 = generate_keyNode(
                                        uom.strip(), key_node2_label, key_node
                                    )
                                    try:
                                        key_node2["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node2["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    if parsed_value_list[-1]:
                                        key_node3 = generate_keyNode(
                                            parsed_value_list[-1].strip(),
                                            label + "_1",
                                            key_node,
                                        )
                                        processed_key_nodes.append(key_node3)
                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "temperature_parser":
                                parsed_value_list = temperature_parser.process(
                                    key_node["v"]
                                )
                                if len(parsed_value_list) == 4:
                                    requires_temperature_control = parsed_value_list[0]
                                    required_maximum = parsed_value_list[1]
                                    required_minimum = parsed_value_list[2]
                                    temperature_uom = parsed_value_list[3]

                                    # Adding key_node1
                                    key_node1 = generate_keyNode(
                                        requires_temperature_control.strip(),
                                        requires_temperature_control,
                                        key_node,
                                    )
                                    try:
                                        key_node1["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node1["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    # Adding key_node2

                                    key_node2 = generate_keyNode(
                                        required_maximum.strip(),
                                        "requiredMaximum",
                                        key_node,
                                    )
                                    try:
                                        key_node2["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node2["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1
                                    # Adding key_node3

                                    key_node3 = generate_keyNode(
                                        required_minimum.strip(),
                                        "requiredMinimum",
                                        key_node,
                                    )
                                    try:
                                        key_node3["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node3["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass

                                    append_count += 1

                                    # Adding Cell4
                                    key_node4 = generate_keyNode(
                                        temperature_uom.strip(),
                                        "temperatureUom",
                                        key_node,
                                    )
                                    try:
                                        key_node4["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node4["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    processed_key_nodes.append(key_node3)
                                    processed_key_nodes.append(key_node4)
                                elif len(parsed_value_list) == 1:
                                    requires_temperature_control = parsed_value_list[0]
                                    key_node1 = generate_keyNode(
                                        requires_temperature_control.strip(),
                                        "requiresTemperatureControl",
                                        key_node,
                                    )

                                    # Adding Cell1
                                    key_node1["unique_id"] = (
                                        key_node["unique_id"]
                                        + "-"
                                        + key_node1["label"]
                                        + "-"
                                        + str(append_count)
                                    )
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "incoterms_parser":
                                parsed_value_list = incoterms_parser.process(
                                    key_node["v"]
                                )
                                # print(parsed_value_list)
                                try:
                                    if len(parsed_value_list) == 2:
                                        incoterms = parsed_value_list[0]
                                        incoterms_location = parsed_value_list[1]
                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            incoterms.strip(), label, key_node
                                        )
                                        # Adding key_node2
                                        key_node2 = generate_keyNode(
                                            incoterms_location.strip(),
                                            label + "Location",
                                            key_node,
                                        )
                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        # if parsed_value_list[-1]:
                                        #     key_node3 = key_node.copy()
                                        #     key_node3["id"] = key_node["id"] + "_" + "2"
                                        #     key_node3["label"] = label + "_1"
                                        #     key_node3["v"] = parsed_value_list[-1].strip()
                                        #     processed_key_nodes.append(key_node3)

                                    elif len(parsed_value_list) == 1:
                                        incoterms = parsed_value_list[0]
                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            incoterms.strip(), label, key_node
                                        )
                                        processed_key_nodes.append(key_node1)
                                    else:
                                        processed_key_nodes.append(key_node)
                                except:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "locationName_parser":
                                parsed_value_list = (
                                    location_name_parser_updated.process(
                                        master_dictionaries, key_node["v"]
                                    )
                                )
                                # master_dictionaries = request_data.get("master_dictionaries")
                                # print(parsed_value_list)
                                # print(parsed_value_list)
                                if len(parsed_value_list) == 3:
                                    location = parsed_value_list[0]
                                    location_country = parsed_value_list[1]
                                    # Adding Cell1
                                    key_node1 = generate_keyNode(
                                        location.strip(), label, key_node
                                    )
                                    processed_key_nodes.append(key_node1)

                                    # Adding Cell2
                                    if (
                                        location_country != None
                                    ):  # checking if country is there @Fahim(17/11/2022)
                                        key_node2 = generate_keyNode(
                                            location_country.strip(), label, key_node
                                        )
                                        if len(key_node2["v"]) == 2:
                                            key_node2["label"] = (
                                                label.replace("LocationName", "")
                                                + "CountryCode"
                                            )

                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1
                                        if key_node2:
                                            processed_key_nodes.append(key_node2)

                                    if parsed_value_list[-1]:
                                        key_node3 = generate_keyNode(
                                            parsed_value_list[-1].strip(),
                                            label + "_1",
                                            key_node,
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1
                                        processed_key_nodes.append(key_node3)

                                # elif len(parsed_value_list) == 1:
                                #     location = parsed_value_list[0]
                                #     # Adding Cell1
                                #     key_node1 = key_node.copy()
                                #     key_node1["id"] = key_node["id"] + "_" + "0"
                                #     key_node1["v"] = location.strip()
                                #     processed_key_nodes.append(key_node1)

                                # working for location, location_code and location_country
                                elif len(parsed_value_list) == 4:
                                    location = parsed_value_list[0]
                                    location_code = parsed_value_list[1]
                                    location_country = parsed_value_list[2]
                                    # Adding key_node1
                                    key_node1 = generate_keyNode(
                                        location.strip(), label, key_node
                                    )
                                    # Adding key_node2
                                    key_node2_label = label.replace("Name", "") + "Code"
                                    key_node2 = generate_keyNode(
                                        location_code.strip(), key_node2_label, key_node
                                    )

                                    # Adding key_node3
                                    key_node3 = generate_keyNode(
                                        location_country.strip(), label, key_node
                                    )
                                    if len(key_node3["v"]) == 2:
                                        key_node3["label"] = (
                                            label.replace("LocationName", "")
                                            + "CountryCode"
                                        )
                                    else:
                                        key_node3["label"] = (
                                            label.replace("LocationName", "")
                                            + "Country"
                                        )
                                    try:
                                        key_node3["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node3["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass
                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    processed_key_nodes.append(key_node3)

                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "valueOfGoods_parser":
                                parsed_value_list = value_of_goods_parser.process(
                                    key_node["v"]
                                )
                                if len(parsed_value_list) == 3:
                                    number = parsed_value_list[0]
                                    currency = parsed_value_list[1]
                                    # Adding key_node1
                                    key_node1 = generate_keyNode(
                                        number.strip(), label, key_node
                                    )

                                    # Adding key_node2

                                    key_node2 = generate_keyNode(
                                        currency.strip(),
                                        label + "CurrencyCode",
                                        key_node,
                                    )
                                    try:
                                        key_node2["unique_id"] = (
                                            key_node["unique_id"]
                                            + "-"
                                            + key_node2["label"]
                                            + "-"
                                            + str(append_count)
                                        )
                                    except:
                                        pass

                                    append_count += 1

                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)
                                    if parsed_value_list[-1]:
                                        key_node3 = generate_keyNode(
                                            parsed_value_list[-1].strip(),
                                            label + "_1",
                                            key_node,
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        append_count += 1
                                        processed_key_nodes.append(key_node3)
                                else:
                                    processed_key_nodes.append(key_node)

                            elif parser_type == "dimension_UOM":
                                parsed_value_list = dimension_uom.process(key_node["v"])
                                # print("parsed_value_list", parsed_value_list)
                                for inner_list in parsed_value_list:
                                    # print(parsed_value_list)
                                    if len(inner_list) == 5:
                                        processed_key_nodes.append(key_node)
                                        l = inner_list[0]
                                        w = inner_list[1]
                                        h = inner_list[2]
                                        uom = inner_list[3]

                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            l.strip(), "length", key_node
                                        )
                                        try:
                                            key_node1["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node1["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node1["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node2

                                        key_node2 = generate_keyNode(
                                            w.strip(), "width", key_node
                                        )
                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node2["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node3

                                        key_node3 = generate_keyNode(
                                            h.strip(), "height", key_node
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node3["parentLabel"] = "dimensions"
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        processed_key_nodes.append(key_node3)

                                        if uom:
                                            # Adding Cell3
                                            key_node4 = generate_keyNode(
                                                uom.strip(), label + "Uom", key_node
                                            )
                                            try:
                                                key_node4["unique_id"] = (
                                                    key_node["unique_id"]
                                                    + "-"
                                                    + key_node4["label"]
                                                    + "-"
                                                    + str(append_count)
                                                )
                                            except:
                                                pass

                                            key_node4["parentLabel"] = "dimensions"
                                            append_count += 1
                                            processed_key_nodes.append(key_node4)

                                        # For extra element
                                        if inner_list[-1]:
                                            key_node5 = generate_keyNode(
                                                inner_list[-1].strip(),
                                                label + "_1",
                                                key_node,
                                            )
                                            try:
                                                key_node5["unique_id"] = (
                                                    key_node["unique_id"]
                                                    + "-"
                                                    + key_node5["label"]
                                                    + "-"
                                                    + str(append_count)
                                                )
                                            except:
                                                pass

                                            key_node5["parentLabel"] = "dimensions"
                                            append_count += 1
                                            processed_key_nodes.append(key_node5)

                                    # # Working for extra data (packageCount only)
                                    elif len(inner_list) == 6:
                                        processed_key_nodes.append(key_node)
                                        l = inner_list[0]
                                        w = inner_list[1]
                                        h = inner_list[2]
                                        uom = inner_list[3]
                                        package_count = inner_list[5]

                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            l.strip(), "length", key_node
                                        )
                                        try:
                                            key_node1["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node1["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node1["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node2

                                        key_node2 = generate_keyNode(
                                            w.strip(), "width", key_node
                                        )

                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node2["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node3
                                        key_node3 = generate_keyNode(
                                            h.strip(), "height", key_node
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node3["parentLabel"] = "dimensions"
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        processed_key_nodes.append(key_node3)

                                        # Adding key_node4
                                        key_node4 = generate_keyNode(
                                            uom.strip(), label + "Uom", key_node
                                        )
                                        try:
                                            key_node4["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node4["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node4["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node4)

                                        # Adding key_node5
                                        key_node5 = generate_keyNode(
                                            package_count.strip(),
                                            "packageCount",
                                            key_node,
                                        )
                                        try:
                                            key_node5["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node5["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node5["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node5)

                                    # Working for extra data
                                    elif len(inner_list) == 7:
                                        processed_key_nodes.append(key_node)
                                        l = inner_list[0]
                                        w = inner_list[1]
                                        h = inner_list[2]
                                        uom = inner_list[3]
                                        package_count = inner_list[5]
                                        package_type = inner_list[6]

                                        # Adding key_node1

                                        key_node1 = generate_keyNode(
                                            l.strip(), "length", key_node
                                        )
                                        try:
                                            key_node1["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node1["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node1["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node2
                                        key_node2 = generate_keyNode(
                                            w.strip(), "width", key_node
                                        )
                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node2["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node3

                                        key_node3 = generate_keyNode(
                                            h.strip(), "height", key_node
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node3["parentLabel"] = "dimensions"
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        processed_key_nodes.append(key_node3)

                                        # Adding Cell4
                                        key_node4 = generate_keyNode(
                                            uom.strip(), label + "Uom", key_node
                                        )
                                        try:
                                            key_node4["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node4["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node4["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node4)

                                        # Adding key_node5
                                        key_node5 = generate_keyNode(
                                            package_count.strip(),
                                            "packageCount",
                                            key_node,
                                        )
                                        try:
                                            key_node5["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node5["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node5["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node5)

                                        # Adding key_node6
                                        key_node6 = generate_keyNode(
                                            package_type.strip(),
                                            "packageType",
                                            key_node,
                                        )
                                        try:
                                            key_node6["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node6["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node6["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node6)

                                    # Working for WITHOUT extra data (inner_package_count and innerPackageType)
                                    elif len(inner_list) == 8:
                                        processed_key_nodes.append(key_node)
                                        l = inner_list[0]
                                        w = inner_list[1]
                                        h = inner_list[2]
                                        uom = inner_list[3]
                                        package_count = inner_list[4]
                                        package_type = inner_list[5]
                                        inner_package_count = inner_list[6]
                                        inner_package_type = inner_list[7]

                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            l.strip(), "length", key_node
                                        )
                                        try:
                                            key_node1["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node1["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node1["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node2
                                        key_node2 = generate_keyNode(
                                            w.strip(), "width", key_node
                                        )
                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node2["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding Cell3
                                        key_node3 = generate_keyNode(
                                            h.strip(), "height", key_node
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node3["parentLabel"] = "dimensions"
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        processed_key_nodes.append(key_node3)

                                        # Adding Cell4
                                        key_node4 = generate_keyNode(
                                            uom.strip(), label + "Uom", key_node
                                        )
                                        try:
                                            key_node4["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node4["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node4["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node4)

                                        # Adding key_node5
                                        key_node5 = generate_keyNode(
                                            package_count.strip(),
                                            "packageCount",
                                            key_node,
                                        )
                                        try:
                                            key_node5["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node5["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node5["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node5)

                                        # Adding key_node6

                                        key_node6 = generate_keyNode(
                                            package_type.strip(),
                                            "packageType",
                                            key_node,
                                        )
                                        try:
                                            key_node6["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node6["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node6["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node6)

                                        # Adding Cell7
                                        key_node7 = generate_keyNode(
                                            inner_package_count.strip(),
                                            "inner_package_count",
                                            key_node,
                                        )
                                        try:
                                            key_node7["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node7["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node7["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node7)

                                        # Adding Cell8
                                        key_node8 = generate_keyNode(
                                            inner_package_type.strip(),
                                            "innerPackageType",
                                            key_node,
                                        )
                                        try:
                                            key_node8["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node8["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node8["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node8)

                                    # Working for extra data (grossWeight and grossWeightUom)
                                    elif len(inner_list) == 9:
                                        processed_key_nodes.append(key_node)
                                        l = inner_list[0]
                                        w = inner_list[1]
                                        h = inner_list[2]
                                        uom = inner_list[3]
                                        package_count = inner_list[5]
                                        package_type = inner_list[6]
                                        gross_weight = inner_list[7]
                                        gross_weight_uom = inner_list[8]

                                        # Adding key_node1
                                        key_node1 = generate_keyNode(
                                            l.strip(), "length", key_node
                                        )
                                        try:
                                            key_node1["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node1["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node1["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node2
                                        key_node2 = generate_keyNode(
                                            w.strip(), "width", key_node
                                        )
                                        try:
                                            key_node2["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node2["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node2["parentLabel"] = "dimensions"
                                        append_count += 1

                                        # Adding key_node3
                                        key_node3 = generate_keyNode(
                                            h.strip(), "height", key_node
                                        )
                                        try:
                                            key_node3["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node3["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node3["parentLabel"] = "dimensions"
                                        append_count += 1

                                        processed_key_nodes.append(key_node1)
                                        processed_key_nodes.append(key_node2)
                                        processed_key_nodes.append(key_node3)

                                        # Adding key_node4
                                        key_node4 = generate_keyNode(
                                            uom.strip(), label + "Uom", key_node
                                        )
                                        try:
                                            key_node4["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node4["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node4["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node4)

                                        # Adding key_node5
                                        key_node5 = generate_keyNode(
                                            package_count.strip(),
                                            "packageCount",
                                            key_node,
                                        )
                                        try:
                                            key_node5["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node5["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node5["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node5)

                                        # Adding key_node6
                                        key_node6 = generate_keyNode(
                                            package_type.strip(),
                                            "packageType",
                                            key_node,
                                        )
                                        try:
                                            key_node6["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node6["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node6["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node6)

                                        # Adding Cell7
                                        key_node7 = generate_keyNode(
                                            gross_weight.strip(),
                                            "grossWeight",
                                            key_node,
                                        )
                                        try:
                                            key_node7["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node7["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass

                                        key_node7["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node7)

                                        # Adding key_node8
                                        key_node8 = generate_keyNode(
                                            gross_weight_uom.strip(),
                                            "grossWeightUom",
                                            key_node,
                                        )
                                        try:
                                            key_node8["unique_id"] = (
                                                key_node["unique_id"]
                                                + "-"
                                                + key_node8["label"]
                                                + "-"
                                                + str(append_count)
                                            )
                                        except:
                                            pass
                                        key_node8["parentLabel"] = "dimensions"
                                        append_count += 1
                                        processed_key_nodes.append(key_node8)

                                    else:
                                        processed_key_nodes.append(key_node)
                            elif parser_type == "financial_parser":
                                # Currency dict to be used
                                currency_dict = master_dictionaries.get(
                                    "currencySymbolToCode"
                                ).get("data")
                                parsed_value_list = financial_parser.process(
                                    key_node["v"], currency_dict
                                )
                                # print(key_node)
                                if len(parsed_value_list) == 2:
                                    number = parsed_value_list[0]
                                    currency = parsed_value_list[1]

                                    key_node1 = generate_keyNode(
                                        number, key_node["label"], key_node
                                    )
                                    currency_label = key_node["label"] + "Currency"
                                    key_node2 = generate_keyNode(
                                        currency, currency_label, key_node
                                    )
                                    processed_key_nodes.append(key_node1)
                                    processed_key_nodes.append(key_node2)

                                else:
                                    processed_key_nodes.append(key_node)
                            else:
                                processed_key_nodes.append(key_node)
                        except:
                            print(traceback.print_exc())
                            processed_key_nodes.append(key_node)

                    node_children = processed_key_nodes
                nodes[i]["children"] = node_children

            target_doc["children"] = nodes
            docs[input_doc_idx] = target_doc
    except:
        print(traceback.print_exc())
        pass

    output_json["nodes"] = docs
    return output_json
