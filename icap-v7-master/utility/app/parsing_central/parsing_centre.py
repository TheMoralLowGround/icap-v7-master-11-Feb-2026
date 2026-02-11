import copy
import re
import traceback
from typing import List, Dict, Optional
from app.misc_modules.unique_id import assign_unique_id_helper
from app.misc_modules.usable_function_list import generate_dim_cells
from app.parsing_central.parser_strategies.cell_strategy import (
    FinancialParserStrategy,
    HeightUOMStrategy,
    IncotermParserStrategy,
    LengthUOMStrategy,
    LocationNameCellStrategy,
    LocationNameCellStrategyVariantFour,
    PackageCountStrategy,
    TemperatureParserStrategy,
    ValueOfGoodsParserStrategy,
    VolumeUOMStrategy,
    WeightUOMStrategy,
    WidthUOMStrategy,
)
from app.parsing_central.parser_strategies.keynode_strategy import (
    DimensionUOMKeyNodeStrategy,
    FinanciaParserKeyNodeStrategy,
    IncotermParserKeyNodeStrategy,
    LocationNameKeyNodeStrategy,
    LocationNameKeyNodeStrategyVariantFour,
    PackageCountKeyNodeStrategy,
    TemperatureKeyNodeStrategy,
    ValueOfGoodsKeyNodeStrategy,
    VolumeUOMKeyNodeStrategy,
    WeightUOMKeyNodeStrategy,
)
from app.parsing_central.parsers import (
    dimension_uom,
    financial_parser,
    height_uom,
    incoterms_parser,
    length_uom,
    location_name_parser_original,
    location_name_parser_updated,
    package_count,
    temperature_parser,
    value_of_goods_parser,
    volume_uom,
    weight_uom,
    width_uom,
)
from app.table_keys import get_replacement_value
from app.table_keys_excel import initiate_blank_row
from app.rules_normalizers_module.table_rules_centre import fetch_parsed_cells

"""
This code is written in Python and is used for parsing and processing data from tables and keys found in documents or files. Here's a summary in simpler terms:

1. The code imports various functions and modules that help with parsing and processing different types of data, such as weights, volumes, package counts, temperatures, incoterms (international commercial terms), location names, and financial values.

2. It defines several dictionaries that map different types of data (e.g., weight, volume, package count) to specific functions or strategies for parsing and processing that data.

3. The main function `parser_main` takes an input JSON data, some definition settings, and additional request data.

4. It loops through the input data and checks if each node is a table or a key.

5. For table nodes:
   - It processes each row of the table, looking for specific labels (e.g., "weight", "volume", "dimensions").
   - If a label is found, it calls the corresponding parsing function to extract the relevant data from the cell value.
   - It generates new cells with the parsed data and updates the row with these new cells.

6. For key nodes:
   - It checks if the key label matches any of the known labels (e.g., "weight", "volume", "locationName").
   - If a match is found, it calls the corresponding parsing function and strategy to process the key value.
   - It generates new key nodes with the parsed data and updates the key node children with these new nodes.

7. The processed JSON data with the parsed table rows and key nodes is returned.

In summary, this code takes input data in a specific JSON format, identifies tables and keys within that data, and processes the values in those tables and keys using various parsing techniques. It then returns the processed data with the extracted and formatted information.

Here's a more technical summary of the code:

This Python script contains functions and strategies to parse and process data from table rows and key nodes in a JSON document. The primary function is `parser_main`, which takes an input JSON object `input_json`, definition settings `definition_settings`, and request data `request_data`.

The script defines several dictionaries:

1. `PARSER_METHOD_MAP`: Maps parser types (e.g., "weight_UOM", "volume_UOM") to their respective parser function.
2. `PARSER_KEY_NODE_STRATEGIES`: Maps parser types to their respective key node strategy class.
3. `PARSER_CELL_STRATEGIES`: Maps parser types to their respective cell strategy class.

The `get_parser_type` function determines the parser type based on the input label.

The script contains two main parsing functions:

1. `parse_table_rows`:
   - Iterates over each row in the table node.
   - For each cell in the row, it determines the parser type based on the cell label.
   - If a parser type is found, it applies the corresponding parser function and cell strategy to process the cell value.
   - It generates new cells with the parsed data and updates the row with these new cells.
   - Special handling is done for dimension-related parsing, where multiple parsed values can be generated from a single cell.

2. `parse_key`:
   - Iterates over each key node.
   - Determines the parser type based on the key label.
   - If a parser type is found, it applies the corresponding parser function and key node strategy to process the key value.
   - It generates new key nodes with the parsed data and updates the key node children with these new nodes.
   - If the key node is a compound key, it recursively processes each child key node.

The script imports several parser functions (e.g., `weight_uom`, `volume_uom`, `location_name_parser_updated`) and parser strategies (e.g., `WeightUOMStrategy`, `VolumeUOMStrategy`, `LocationNameKeyNodeStrategy`) from other modules.

The `parser_main` function orchestrates the parsing process:
1. It iterates over each target document in the input JSON.
2. For each node in the document:
   - If the node type is "table", it calls `parse_table_rows` to process the table rows.
   - If the node type is "key", it calls `parse_key` to process the key nodes.
3. It returns the processed JSON object.

The script also includes helper functions like `generate_cell`, `generate_keyNode`, and `fetch_sub_dict` to assist in generating new cells and key nodes, and fetching data from master dictionaries.

Overall, this script provides a framework for parsing and processing structured data from tables and keys in JSON documents, utilizing various parsing techniques and strategies based on the data type and label.

"""


# updated by: Sunny
# updated on: 03/10/2021


# value list processor map
PARSER_METHOD_MAP = {
    # "weight_UOM": weight_uom.process,  # Turned off
    # "volume_UOM": volume_uom.process,  # Turned off
    # "valueOfGoods_parser": value_of_goods_parser.process,  # Turned off
    # "packageCount": package_count.process,  # Turned off
    # "temperature_parser": temperature_parser.process,  # Turned off
    # "incoterms_parser": incoterms_parser.process,  # Turned off
    # "locationName_parser": location_name_parser_original.process,  # Turned off
    # "locationName_fuzzy_parser": location_name_parser_updated.process,  # Turned off
    # "valueOfGoods_parser": value_of_goods_parser.process,  # Turned off
    # "dimension_UOM": dimension_uom.process,  # Turned off
    # "financial_parser": financial_parser.process,  # Turned off
    # "height_UOM": height_uom.process,  # Turned off
    # "width_UOM": width_uom.process,  # Turned off
    # "length_UOM": length_uom.process,  # Turned off
}

# Strategy Map for generating key nodes
PARSER_KEY_NODE_STRATEGIES = {
    # "weight_UOM": WeightUOMKeyNodeStrategy,  # Turned off
    # "volume_UOM": VolumeUOMKeyNodeStrategy,  # Turned off
    # "packageCount": PackageCountKeyNodeStrategy,  # Turned off
    # "temperature_parser": TemperatureKeyNodeStrategy,  # Turned off
    # "incoterms_parser": IncotermParserKeyNodeStrategy,  # Turned off
    # "locationName_parser": [  # Turned off
    #     LocationNameKeyNodeStrategy,
    #     LocationNameKeyNodeStrategyVariantFour,
    # ],
    # "locationName_fuzzy_parser": [  # Turned off
    #     LocationNameKeyNodeStrategy,
    #     LocationNameKeyNodeStrategyVariantFour,
    # ],
    # "valueOfGoods_parser": ValueOfGoodsKeyNodeStrategy,  # Turned off
    # "dimension_UOM": DimensionUOMKeyNodeStrategy,  # Turned off
    # "financial_parser": FinanciaParserKeyNodeStrategy,  # Turned off
}

# strategy map for genarate cells
PARSER_CELL_STRATEGIES = {
    # "weight_UOM": WeightUOMStrategy,  # Turned off
    # "volume_UOM": VolumeUOMStrategy,  # Turned off
    # "packageCount": PackageCountStrategy,  # Turned off
    # "temperature_parser": TemperatureParserStrategy,  # Turned off
    # "valueOfGoods_parser": ValueOfGoodsParserStrategy,  # Turned off
    # "financial_parser": FinancialParserStrategy,  # Turned off
    # "height_UOM": HeightUOMStrategy,  # Turned off
    # "width_UOM": WidthUOMStrategy,  # Turned off
    # "length_UOM": LengthUOMStrategy,  # Turned off
    # "locationName_parser": [  # Turned off
    #     LocationNameCellStrategy,
    #     LocationNameCellStrategyVariantFour,
    # ],
    # "locationName_fuzzy_parser": [  # Turned off
    #     LocationNameCellStrategy,
    #     LocationNameCellStrategyVariantFour,
    # ],
    # "incoterms_parser": IncotermParserStrategy,  # Turned off
    # "innerPackageCount": fetch_parsed_cells,  # Turned off
}


location_name_fuzzy_match = True


def get_parser_type(input_label: str, set_parsers: dict, project: str):
    financial_value_labels = set_parsers.get("financial_value_labels")
    global location_name_fuzzy_match
    if not input_label:
        return None

    # Excluded fields - no parser should be applied (case-insensitive)
    parser_exclusion_list = ["totalvolumeuom", "totalweightuom"]
    if input_label.lower() in parser_exclusion_list:
        return None

    if input_label in financial_value_labels:
        return "financial_parser"

    input_label_map = {
        "requirestemperaturecontrol": "temperature_parser",
        "height": "height_UOM",
        "length": "length_UOM",
        "width": "width_UOM",
    }

    if parser_type := input_label_map.get(input_label):
        return parser_type

    if input_label.lower().endswith("weight"):
        return "weight_UOM"
    elif input_label.lower().endswith("volume") or "volume" in input_label.lower():
        return "volume_UOM"
    elif input_label.endswith("packageCount"):
        return "packageCount"
    # elif input_label.endswith("dimensions"):
    #     return "dimension_UOM"
    elif input_label.endswith("incoterms"):
        return "incoterms_parser"
    elif input_label.lower().endswith("locationname"):
        if (location_name_fuzzy_match == True) and (project != "ShipmentCreate"):
            return "locationName_fuzzy_parser"
        return "locationName_parser"
    elif "valueofgoods" in input_label.lower():
        return "valueOfGoods_parser"


def generate_cell(value, label, input_cell):
    new_cell = input_cell.copy()
    new_cell["v"] = value.strip()
    new_cell["label"] = label
    return new_cell


def generate_keyNode(value, label, input_key_node):
    new_key_node = input_key_node.copy()
    new_key_node["v"] = value.strip()
    new_key_node["label"] = label
    return new_key_node


def get_repeated_labels(node_children):
    """
    Identifies labels that appear multiple times within each row of JSON data.

    Iterates through each row in the input data and tracks the occurrence count
    of each label. Creates a dictionary mapping row indices to their repeated
    labels and the corresponding child objects.
    """
    try:
        repeated_labels_dict = {}
        for row_index, row in enumerate(node_children):
            label_count = {}
            label_objects = {}

            for child in row["children"]:
                # Skip if it has qualifier in key
                if "qualifierParent" in child.keys():
                    continue
                label = child.get("label")
                if label:
                    if label not in label_count:
                        label_count[label] = 0
                        label_objects[label] = []

                    label_count[label] += 1
                    label_objects[label].append(child)
            repeated_in_row = {}
            for label, count in label_count.items():
                if count > 1:
                    repeated_in_row[label] = label_objects[label]

            if repeated_in_row:
                repeated_labels_dict[row_index] = repeated_in_row
    except:
        pass
    return repeated_labels_dict


def filter_out_static_cell_if_matched_with_excel_value(node_children):
    """
    Filters JSON data by removing static values when duplicate labels exist in a row.

    For each row in the data, identifies labels that appear multiple times. When a label
    has both static and non-static values in the same row, removes all instances with
    static_value attribute and keeps only the non static ones.

    Skip if it has qualifier in key
    """
    try:
        repeated_labels_dict = get_repeated_labels(node_children)

        if not repeated_labels_dict:
            return node_children

        for row_index, labels_dict in repeated_labels_dict.items():
            if row_index >= len(node_children):
                continue

            for label, child_objects in labels_dict.items():
                all_values_static = all(
                    [i.get("static_value") == True for i in child_objects]
                )
                if all_values_static:
                    # If all values are static just keep the last one
                    children_to_remove = []
                    # Add all the static children to all expect last one to keep the last static value.
                    static_indices = []
                    for i, child in enumerate(node_children[row_index]["children"]):
                        if child.get("label") == label and child.get("static_value"):
                            static_indices.append(i)

                    if len(static_indices) > 1:
                        children_to_remove.extend(static_indices[:-1])

                    for i in sorted(children_to_remove, reverse=True):
                        node_children[row_index]["children"].pop(i)
                else:
                    static_children = []
                    non_static_children = []

                    for child in child_objects:
                        if child.get("static_value"):
                            static_children.append(child)
                        else:
                            non_static_children.append(child)

                    if static_children and non_static_children:
                        children_to_remove = []
                        # print(node_children[row_index]["children"])
                        for i, child in enumerate(node_children[row_index]["children"]):
                            if child.get("label") == label and child.get(
                                "static_value"
                            ):
                                children_to_remove.append(i)
                        for i in sorted(children_to_remove, reverse=True):
                            node_children[row_index]["children"].pop(i)
    except Exception:
        pass
    return node_children


def is_valid_dimension_split_pattern(text: str) -> bool:
    """
    Checks if the text matches the expected pattern like:
    '19x 116x62x72 1x 116x62x55'
    """
    pattern = r"^\d+x\s\d+(?:x\d+)+(?:\s\d+x\s\d+(?:x\d+)+)*$"
    return bool(re.match(pattern, text.strip()))


def dimension_format_with_newline(text: str) -> str:
    """
    Formats the text by inserting '\\n' between pattern segments
    if it matches the expected format.
    Example: '19x 116x62x72 1x 116x62x55' ->
             '19x 116x62x72\\n1x 116x62x55'
    """

    pattern = r"(\d+x\s\d+(?:x\d+)+)"
    parts = re.findall(pattern, text)
    return "\n".join(parts)


# TODO: Code is refactored in strategy. First test `KEY PARSER`
# TODO: Then integrate this one and remove if else logics
def parse_table_rows(
    node_children,
    set_parsers,
    master_dictionaries,
    doc_type_value,
    project,
    definition_id,
    definition_settings,
    table_key_items,
):
    # print("🐍 File: parsing_central/parsing_centre.py | Line: 343 | parse_table_rows ~ node_children",node_children)
    # Added by emon on 08/10/2022 - Changing how dimensions are appended
    extended_rows = list()
    updated_rows = list()
    dimension_data_set = dict()
    start_index = None
    exceptional_profiles = definition_settings.get("profileSettings", {}).get(
        "dimension_package_count_reverse_profiles", []
    )
    utility_mapped_code_list = master_dictionaries.get(
        "utility_mapped_code_list", {}
    ).get("data", {})
    is_exceptional_profile = True if definition_id in exceptional_profiles else False
    for row_idx, row in enumerate(node_children):
        try:
            cells = row["children"]
            processed_cells = []

            dimension_metadata = {
                "dimension_UOM_available": False,
                "dimension_UOM_data": None,
            }
            currency_metadata = {"currency_available": False, "currency_data": None}
            # print(cells)
            for cell_idx, cell in enumerate(cells):
                try:
                    label = cell["label"]
                    value = cell["v"]
                    # Remove spaces and change to \n
                    # print("Line 396 is valid",is_valid_dimension_split_pattern(value),value)
                    if is_valid_dimension_split_pattern(value):
                        value = dimension_format_with_newline(value)
                    parser_type = get_parser_type(label, set_parsers, project)
                    parsed_value_processor = PARSER_METHOD_MAP.get(parser_type)
                    cell_strategy = PARSER_CELL_STRATEGIES.get(parser_type)

                    if parsed_value_processor:
                        if parser_type == "dimension_UOM":
                            # Added by emon on 08/10/2022 - Changing how dimensions are appended
                            print("cell",cell.get("id"))
                            if row_idx == 0:
                                start_index = cell_idx
                            parsed_value_list = parsed_value_processor(
                                value, is_exceptional_profile
                            )
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
                        elif (
                            parser_type == "locationName_parser"
                            or parser_type == "locationName_fuzzy_parser"
                        ):
                            parser_processor = PARSER_METHOD_MAP.get(parser_type)
                            if parser_type == "locationName_parser":
                                parsed_value_list = parser_processor(
                                    master_dictionaries, value
                                )
                            elif parser_type == "locationName_fuzzy_parser":
                                parsed_value_list = parser_processor(
                                    master_dictionaries, value, doc_type_value
                                )
                            (
                                cell_strategy_variant_three,
                                cell_strategy_variant_four,
                            ) = cell_strategy
                            if len(parsed_value_list) == 3:
                                cell_strategy_variant_three(
                                    cell, processed_cells, parsed_value_list, label
                                ).process()
                            elif len(parsed_value_list) == 4:
                                cell_strategy_variant_four(
                                    cell, processed_cells, parsed_value_list, label
                                ).process()
                        elif parser_type in ["height_UOM", "width_UOM", "length_UOM"]:
                            parsed_value_list = parsed_value_processor(value)
                            cell_strategy(
                                cell, processed_cells, parsed_value_list, label
                            ).process(dimension_metadata)

                        # Removed by Emon on Oct 21 2025 - Financial Parser is not needed currently
                        # elif parser_type == "financial_parser":
                        #     currency_dict = master_dictionaries.get(
                        #         "currencySymbolToCode"
                        #     ).get("data")
                        #     parsed_value_list = parsed_value_processor(
                        #         value, currency_dict
                        #     )
                        #     cell_strategy(
                        #         cell, processed_cells, parsed_value_list, label
                        #     ).process(currency_metadata)
                        
                        
                        else:
                            parsed_value_list = parsed_value_processor(value)
                            if parsed_value_list:
                                cell_strategy(
                                    cell, processed_cells, parsed_value_list, label
                                ).process()

                    else:
                        processed_cells.append(cell)
                except AttributeError:
                    processed_cells.append(cell)
                except:
                    print(traceback.print_exc())
                    processed_cells.append(cell)
                if label.lower() == "innerpackagecount":
                    parsed_cell_results = fetch_parsed_cells(
                        cell,
                        cell_idx,
                        value,
                        utility_mapped_code_list=utility_mapped_code_list,
                    )
                    if parsed_cell_results:
                        # --- Merge Logic ---
                        # 1. Convert process_cells to dict by label for quick lookup
                        merged = {cell["label"]: cell for cell in processed_cells}

                        # 2. Update or add cells from parsed_cells (latest wins)
                        for cell in parsed_cell_results:
                            merged[cell["label"]] = cell

                        # 3. Convert back to list
                        processed_cells = list(merged.values())

            try:
                if dimension_metadata.get("dimension_UOM_available"):
                    processed_cells.append(dimension_metadata.get("dimension_UOM_data"))
                if currency_metadata.get("currency_available"):
                    processed_cells.append(currency_metadata.get("currency_data"))
            except Exception as ex:
                print(traceback.print_exc())

            # if processed_cells:
            row["children"] = processed_cells
            if row["children"]:
                node_children[row_idx] = row

        except:
            node_children[row_idx] = row
    filter_out_static_cell_if_matched_with_excel_value(node_children)
    try:

        def get_table_key_generated_cells(pre_rows):
            output_labels = list()
            for x in pre_rows:
                if (
                    x.get("table_key_generated")
                    and (x.get("parentLabel") != "dimensions")
                    and x.get("label") != "packageCount"
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
                        if x["label"] not in table_key_generated_keys
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
                            if x["label"] not in table_key_generated_keys
                        ]
                        if start_index:
                            node_children[key]["children"] = (
                                pre_rows[:start_index]
                                + dim_cells
                                + pre_rows[start_index:]
                            )
                        else:
                            node_children[key]["children"].extend(dim_cells)
                        prioritize_package_count_in_place(
                            node_children[key]["children"]
                        )

                except:
                    print(traceback.print_exc())
                    row_dict = {
                        "children": dim_cells,
                        "type": "row",
                        "id": f"row_manual_{key}",
                    }
                    node_children.append(row_dict)
            extended_rows, updated_rows = separate_dim_rows_to_new_rows(
                dimension_data_set,
                node_children,
                set_parsers,
                project,
                is_exceptional_profile,
            )

    except Exception as ex:
        print(f"Exception encountered : Table Parse {ex}")
        print(traceback.print_exc())
    if extended_rows:
        node_children = updated_rows
    update_package_count_value_if_dimension_does_not_exists(
        node_children, table_key_items
    )

    return node_children


def get_prioritized_non_static_key_item(
    table_key_items: List[Dict], target_label: str
) -> Optional[Dict]:
    matched_items = [
        item for item in table_key_items if item.get("keyLabel") == target_label
    ]

    if not matched_items:
        return None

    if len(matched_items) == 1:
        return matched_items[0]

    non_static_items = [item for item in matched_items if item.get("type") != "static"]

    if non_static_items:
        return non_static_items[-1]

    return matched_items[-1]


def update_package_count_value_if_dimension_does_not_exists(
    node_children, table_key_items
):
    package_count_item = get_prioritized_non_static_key_item(
        table_key_items, "packageCount"
    )
    if package_count_item:
        if (
            package_count_item["keyLabel"] == "packageCount"
            and package_count_item["type"] == "static"
        ):
            for row in node_children:
                table_id = None
                # If has only dimension then create hierarchy mechanism
                if any([i.get("label") == "dimensions" for i in row["children"]]):
                    if any([i.get("label") == "packageCount" for i in row["children"]]):
                        # If exists just update value
                        for cell in row["children"]:
                            if (
                                (cell["label"] == package_count_item["keyLabel"])
                                and cell.get("parser_generated", False) == False
                                and (cell.get("v") == "0" or cell.get("v") == "")
                            ):
                                cell["v"] = package_count_item["shape"]
                    else:
                        # Create a new cell and append because it does not exits
                        table_id = None
                        for cell in row["children"]:
                            if cell.get("table_id", None):
                                table_id = cell.get("table_id", None)
                                break
                        if package_count_item["keyLabel"] == "packageCount":
                            package_count_cell = {
                                "type": "cell",
                                "label": "packageCount",
                                "v": package_count_item["shape"],
                                "pos": "",
                                "pageId": "",
                                "table_key_generated": "True",
                                "static_value": "True",
                            }
                            if table_id:
                                package_count_cell.update({"table_id": table_id})
                            row["children"].append(package_count_cell)
    return node_children


def prioritize_package_count_in_place(cells) -> None:
    """
    Modifies the input list in place to retain only 'packageCount' entries with
    'parser_generated' == "True" if duplicates exist. Otherwise, keeps as is.
    """
    package_count_items = [
        cell for cell in cells if cell.get("label") == "packageCount"
    ]

    # Only act if there are multiple packageCount entries
    if len(package_count_items) > 1:
        parser_generated_items = [
            cell for cell in package_count_items if cell.get("parser_generated") == True
        ]

        if parser_generated_items:
            # Remove all packageCount items first
            cells[:] = [cell for cell in cells if cell.get("label") != "packageCount"]
            # Then add back only the parser_generated ones
            cells.extend(parser_generated_items)


def separate_dim_rows_to_new_rows(
    dimension_data_set, node_children, set_parsers, project, is_exceptional_profile
):
    try:
        extended_rows = list()
        updated_rows = list()
        for target_row_index, dim_data in dimension_data_set.items():
            row_data = copy.deepcopy(node_children[target_row_index])
            row_cells = node_children[target_row_index]["children"]
            copied_cells = copy.deepcopy(row_cells)
            cell_index, cell = next(
                (
                    (index, item)
                    for index, item in enumerate(copied_cells)
                    if item.get("label") == "dimensions"
                ),
                (None, None),
            )

            if cell:
                # Remove spaces and change to \n
                # print("IS VALID DIMENSION SPLIT",is_valid_dimension_split_pattern(cell["v"]),cell["v"])
                if is_valid_dimension_split_pattern(cell["v"]):
                    cell["v"] = dimension_format_with_newline(cell["v"])
                else:
                    # 
                    # For other scenarios
                    cell["v"] = cell["v"].replace(" ", "\n")
                # print("cell",cell["v"])
                parser_type = get_parser_type(cell["label"], set_parsers, project)
                parsed_value_processor = PARSER_METHOD_MAP.get(parser_type)

                splitted_dim_value = cell["v"].split("\n")
                if len(splitted_dim_value) > 1:
                    for idx, dim_value in enumerate(splitted_dim_value):
                        temp_dim_cell = copy.deepcopy(cell)
                        temp_dim_cell["v"] = dim_value

                        if idx == 0:
                            row_data["children"][cell_index]["v"] = dim_value
                            updated_rows.append(copy.deepcopy(row_data))

                        if dim_value and idx != 0:
                            parsed_value = parsed_value_processor(
                                dim_value, is_exceptional_profile
                            )
                            cells_to_be_appended = generate_dim_cells(
                                temp_dim_cell, 0, parsed_value[0]
                            )
                            # for copied_cell in copied_cells:
                            #     if copied_cell.get("label") == "goodsDescription":
                            #         cells_to_be_appended.append(copied_cell)
                            #         break

                            new_row_data = copy.deepcopy(row_data)
                            new_row_data["children"] = copy.deepcopy(
                                cells_to_be_appended
                            )

                            extended_rows.append(new_row_data)
                            updated_rows.append(new_row_data)
                else:
                    updated_rows.append(copy.deepcopy(row_data))
        return extended_rows, updated_rows
    except:
        return [], []


def parse_key(node_children, set_parsers, master_dictionaries, doc_type_value, project):
    processed_key_nodes = []
    for key_node in node_children:
        label = key_node["label"]
        value = key_node["v"]
        parser_type = get_parser_type(label, set_parsers, project)
        if parser_type:
            try:
                # get parser method based on parser type
                parser_processor = PARSER_METHOD_MAP.get(parser_type)
                key_node_strategy = PARSER_KEY_NODE_STRATEGIES.get(parser_type)

                if parser_processor and key_node_strategy:
                    # Process value list of the key_node
                    if parser_type == "locationName_parser":
                        parsed_value_list = parser_processor(master_dictionaries, value)
                    elif parser_type == "locationName_fuzzy_parser":
                        parsed_value_list = parser_processor(
                            master_dictionaries, value, doc_type_value
                        )
                    elif parser_type == "financial_parser":
                        currency_dict = master_dictionaries.get(
                            "currencySymbolToCode"
                        ).get("data")
                        parsed_value_list = parser_processor(value, currency_dict)
                    else:
                        parsed_value_list = parser_processor(value)

                    # process parsed value list with strategies
                    if parser_type == "dimension_UOM":
                        processed_key_nodes_dimension = []
                        for inner_list in parsed_value_list:
                            processed_key_nodes_dimension += key_node_strategy(
                                inner_list, parsed_value_list, label, key_node
                            ).process()
                        processed_key_nodes += [
                            i
                            for i in processed_key_nodes_dimension
                            if isinstance(i, dict)
                        ]
                    elif (
                        parser_type == "locationName_parser"
                        or parser_type == "locationName_fuzzy_parser"
                    ):
                        (
                            key_node_strategy_variant_three,
                            key_node_strategy_variant_four,
                        ) = key_node_strategy
                        if len(parsed_value_list) == 3:
                            key_node_strategy_variant_three(
                                processed_key_nodes, parsed_value_list, label, key_node
                            ).process()
                        elif len(parsed_value_list) == 4:
                            key_node_strategy_variant_four(
                                processed_key_nodes, parsed_value_list, label, key_node
                            ).process()
                    else:
                        key_node_strategy(
                            processed_key_nodes, parsed_value_list, label, key_node
                        ).process()
                else:
                    processed_key_nodes.append(key_node)
            except Exception as ex:
                print(f"Exception encountered [key strategy]: {ex}")
                print(traceback.print_exc())
                processed_key_nodes.append(key_node)
        elif key_node.get("isCompoundKey"):
            compound_keychildren = list()
            try:
                for child in key_node["children"]:
                    try:
                        child_label = child["label"]
                        child_value = child["v"]
                        child_parser_type = get_parser_type(
                            child_label, set_parsers, project
                        )
                        child_parser_processor = PARSER_METHOD_MAP.get(
                            child_parser_type
                        )
                        child_key_node_strategy = PARSER_KEY_NODE_STRATEGIES.get(
                            child_parser_type
                        )
                        if child_parser_processor and child_key_node_strategy:
                            if child_parser_type == "locationName_parser":
                                parsed_value_list = child_parser_processor(
                                    master_dictionaries, child_value
                                )
                            elif child_parser_type == "locationName_fuzzy_parser":
                                parsed_value_list = child_parser_processor(
                                    master_dictionaries, child_value, doc_type_value
                                )
                            elif child_parser_type == "financial_parser":
                                currency_dict = master_dictionaries.get(
                                    "currencySymbolToCode"
                                ).get("data")
                                parsed_value_list = child_parser_processor(
                                    child_value, currency_dict
                                )
                            else:
                                parsed_value_list = child_parser_processor(child_value)
                            if child_parser_type == "dimension_UOM":
                                processed_key_nodes_dimension = []
                                for inner_list in parsed_value_list:
                                    processed_key_nodes_dimension += (
                                        child_key_node_strategy(
                                            inner_list,
                                            parsed_value_list,
                                            child_label,
                                            child,
                                        ).process()
                                    )
                                compound_keychildren += [
                                    i
                                    for i in processed_key_nodes_dimension
                                    if isinstance(i, dict)
                                ]
                            elif (
                                child_parser_type == "locationName_parser"
                                or child_parser_type == "locationName_fuzzy_parser"
                            ):
                                (
                                    child_key_node_strategy_variant_three,
                                    child_key_node_strategy_variant_four,
                                ) = child_key_node_strategy
                                target_label = list()
                                target_label.append(
                                    child_label.replace("LocationName", "LocationCode")
                                )
                                target_label.append(
                                    child_label.replace("LocationName", "CountryCode")
                                )

                                if len(parsed_value_list) == 3:
                                    child_key_node_strategy_variant_three(
                                        compound_keychildren,
                                        parsed_value_list,
                                        child_label,
                                        child,
                                    ).process()
                                    if (
                                        parsed_value_list[-1] is None
                                        and parsed_value_list[-2] is None
                                    ):
                                        pass
                                    else:
                                        for child_key in compound_keychildren[:]:
                                            if child_key["label"] in target_label:
                                                if child_key["v"] == "ERROR":
                                                    compound_keychildren.remove(
                                                        child_key
                                                    )

                                elif len(parsed_value_list) == 4:
                                    child_key_node_strategy_variant_four(
                                        compound_keychildren,
                                        parsed_value_list,
                                        child_label,
                                        child,
                                    ).process()

                                    for child_key in compound_keychildren[:]:
                                        if child_key["label"] in target_label:
                                            if child_key["v"] == "ERROR":
                                                compound_keychildren.remove(child_key)

                                else:
                                    compound_keychildren.append(child)

                            else:
                                child_key_node_strategy(
                                    compound_keychildren,
                                    parsed_value_list,
                                    child_label,
                                    child,
                                ).process()
                        else:
                            compound_keychild_labels = [
                                x["label"] for x in compound_keychildren
                            ]
                            if not child_label in compound_keychild_labels:
                                compound_keychildren.append(child)
                            else:
                                for compound_keychild in compound_keychildren:
                                    if compound_keychild.get("label") == child.get(
                                        "label"
                                    ):
                                        if child.get("v") != "ERROR":
                                            compound_keychild["v"] = child.get("v")
                    except:
                        print(traceback.print_exc())
                        compound_keychildren.append(child)
                key_node["children"] = compound_keychildren
                processed_key_nodes.append(key_node)
            except:
                print(traceback.print_exc())
                processed_key_nodes.append(key_node)
        else:
            processed_key_nodes.append(key_node)
    return processed_key_nodes


def parser_main(input_json: dict, definition_settings, request_data: dict):
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
    """
    Code Flow:
    1. iterate over each target docs from docs
    2. get target_docs_children as nodes
    3. iterate over node from nodes
    4. get children of node as node children
    4. check node type either table or key
    5.  a. iterate over each key node from node children
        b. iterate  process cell for table nodes
    """

    global master_dictionaries
    global location_name_fuzzy_match
    master_dictionaries = request_data.get("master_dictionaries")
    print("Parsing Centre Triggered")

    definitions = request_data.get("definitions")
    project = request_data.get("project")
    # getting doc type from ra_json because sometimes we might not have definitions
    ra_json = request_data.get("ra_json")
    doc_type_value = ra_json.get("DocType")
    try:
        if definitions != []:
            definitions_data = definitions[0]
        else:
            definitions_data = {}
        table_key_items, key_models, table_data = {}, {}, {}
        # doc_type_value = definitions_data["type"]
        keys_data = definitions_data.get("key")
        if keys_data:
            key_models = keys_data.get("models")
        if key_models:
            key_model = key_models[0]
            if key_model.get("locationCodeFuzzyMatch") == "false":
                location_name_fuzzy_match = False
        table_data = definitions_data.get("table")
        if table_data:
            table_key_items = table_data[0]["table_definition_data"]["keyItems"]
    except:
        print(traceback.print_exc())

    # output
    output_json = input_json.copy()
    docs = output_json["nodes"]

    key_options_items = (
        definition_settings.get("options", {}).get("options-keys", {}).get("items")
    )
    financial_value_labels = {
        x["keyValue"]
        for x in key_options_items
        if x.get("modType") == "Financial Value"
    }
    set_parsers = {"financial_value_labels": financial_value_labels}

    try:
        for target_doc in docs:
            nodes = target_doc["children"]
            for node in nodes:
                node_children = node["children"]

                if "table" in node["type"]:
                    node["children"] = parse_table_rows(
                        node_children,
                        set_parsers,
                        master_dictionaries,
                        doc_type_value,
                        project,
                        definitions_data.get("definition_id"),
                        definition_settings,
                        table_key_items,
                    )
                    assign_unique_id_helper(node)

                if "key" in node["type"]:
                    node["children"] = parse_key(
                        node_children,
                        set_parsers,
                        master_dictionaries,
                        doc_type_value,
                        project,
                    )
    except Exception as ex:
        print(f"Exception encountered: {ex}")
        print(traceback.print_exc())

    return output_json


def transfer_singleColumn_type_to_table(d_json: dict):
    """Append key singleColumn data to table children"""
    singleColumnData = list()
    try:
        nodes = d_json["nodes"]
        for node in nodes:
            documents = node["children"]
            for doc in documents:
                if doc["type"] == "key":
                    key_childrens = doc["children"]
                    for key_item in key_childrens:
                        if (
                            key_item.get("block_type") == "singleColumn"
                            and key_item.get("qualifierParent") == "references"
                        ):
                            singleColumnData.extend(
                                [
                                    {
                                        "v": key_item["worksheet_name"],
                                        "worksheet_name": key_item["worksheet_name"],
                                        "type": "cell",
                                        "pos": "",
                                        "pageId": "",
                                        "label": "placeHolder",
                                        "table_key_generated": True,
                                        "table_id": 0,
                                    },
                                    {
                                        "v": key_item["v"],
                                        "worksheet_name": key_item["worksheet_name"],
                                        "type": "cell",
                                        "pos": "",
                                        "pageId": "",
                                        "label": key_item["label"],
                                        "table_key_generated": True,
                                        "table_id": 0,
                                        "qualifierParent": "references",
                                        "isSingleColumn": True,
                                    },
                                ]
                            )
            # Second pass to update
            for doc in documents:
                if doc["type"] == "table":
                    table_childrens = doc["children"]
                    new_row = initiate_blank_row()
                    new_row["children"] = singleColumnData
                    table_childrens.append(new_row)
    except:
        print(traceback.print_exc())
        return d_json
    return d_json
