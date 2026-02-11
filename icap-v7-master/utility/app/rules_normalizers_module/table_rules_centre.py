import copy
import traceback

from app.enums.table_enum import RowDirectionRule
from app.extraction_modules.selector import get_value_pos_from_list
from app.misc_modules.unique_id import assign_unique_id_helper
from app.misc_modules.usable_function_list import (
    generate_dim_cells,
    generate_temperature_cells,
    generate_volume_cells,
    generate_weight_cells,
    genereate_package_count_cells,
)
from app.parsing_central.parsers import (
    dimension_uom,
    height_uom,
    incoterms_parser,
    length_uom,
    package_count,
    temperature_parser,
    value_of_goods_parser,
    volume_uom,
    weight_uom,
    width_uom,
)
from app.rules_normalizers_module.sub_rules import convert_date
from app.rules_normalizers_module.sub_rules.add_prefix import apply_prefix_rule
from app.rules_normalizers_module.sub_rules.add_suffix import apply_suffix_rule
from app.rules_normalizers_module.sub_rules.calculate import apply_calculate_function
from app.rules_normalizers_module.sub_rules.calculate_fields import (
    apply_calculate_fields,
)
from app.rules_normalizers_module.sub_rules.conditioned_central import (
    apply_conditioned_rule,
)
from app.rules_normalizers_module.sub_rules.contains import (
    apply_contains_function,
    apply_contains_function_list,
)
from app.rules_normalizers_module.sub_rules.convert_decimal import (
    apply_convert_decimals_to_cw1,
)
from app.rules_normalizers_module.sub_rules.correct_data_type import (
    apply_correct_data_type,
)
from app.rules_normalizers_module.sub_rules.delete_from import apply_delete_from
from app.rules_normalizers_module.sub_rules.delete_until import apply_delete_Until
from app.rules_normalizers_module.sub_rules.dimension_seperator_ocr_fix import (
    apply_dimension_sep_fix,
)
from app.rules_normalizers_module.sub_rules.ends_with_v5 import (
    apply_endswithv5_function,
)
from app.rules_normalizers_module.sub_rules.exclude import apply_exclude_rules_on
from app.rules_normalizers_module.sub_rules.extract import (
    apply_extract_substring_function,
)
from app.rules_normalizers_module.sub_rules.extract_pattern import apply_extract_pattern
from app.rules_normalizers_module.sub_rules.numeric_value_format import (
    apply_format_currency_to_na_standard,
)
from app.rules_normalizers_module.sub_rules.parse import parse_index_finder
from app.rules_normalizers_module.sub_rules.replace_function import (
    apply_replace_function,
)
from app.rules_normalizers_module.sub_rules.round_decimal import (
    apply_round_decimal_rule,
)
from app.rules_normalizers_module.sub_rules.split_by import apply_split_by_seperator
from app.rules_normalizers_module.sub_rules.starts_with_v5 import (
    apply_startswithv5_function,
)
from app.rules_normalizers_module.sub_rules.trim_values import trim_values_rule
from app.rules_normalizers_module.sub_rules.case_rules import (
    set_uppercase_values_rule,
    set_lowercase_values_rule,
)
from app.custom_pipeline_modules.trunication import normalize_number_format

"""
This script is designed to process and manipulate tabular data, such as that found in spreadsheets or documents. It performs various operations on the rows and cells of the data, including:

1. Extracting information from cell values using specialized parsers for dimensions, weights, volumes, package counts, temperatures, and other data types.

2. Applying rules to modify cell values, such as replacing text, excluding specific patterns, adding prefixes or suffixes, converting decimal formats, rounding values, and performing calculations.

3. Copying cell values to other rows or columns based on conditions or rules.

4. Merging rows or distributing values across rows based on specific criteria, such as cell counts or conditions.

5. Generating new cells or columns based on the values of other cells and applying rules or conditions.

The script processes the data row by row, applying the appropriate rules and operations based on the labels or characteristics of each cell. It can handle various data formats and structures, and the operations are configurable through rule definitions.

The script is designed to automate and streamline the process of cleaning, formatting, and transforming tabular data, making it easier to work with and analyze for non-technical users.


For 

"""


def get_parser_type(input_label):
    # print(input_label)
    if not input_label:
        return None
    input_label = input_label.lower()
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


def valid_cell_counter(input_row):
    """Counts the number of visible cells in a row"""

    visible_cell_count = 0
    cells = input_row["children"]
    for cell_idx, cell in enumerate(cells):
        try:
            cell_is_invisible = False
            cell_label = cell["label"]
            if (cell_label in ["None", "notInUse", ""]) or (cell_label[-1].isnumeric()):
                if not (
                    "parser_generated" in cell.keys()
                    and (cell["parser_generated"] == True)
                ):
                    cell_is_invisible = True

            if isinstance(cell["v"], str) and cell["v"].strip() == "":
                cell_is_invisible = True
            if not cell_is_invisible:
                visible_cell_count += 1

        except:
            print(traceback.print_exc())
            visible_cell_count += 1
    return visible_cell_count


def fetch_parsed_cells(cell, cell_idx, input_text, is_exceptional_profile=False,utility_mapped_code_list={}):
    """Takes in a cell and input text and uses parsers to generated new parsed cells and returns them"""
    label = cell["label"]
    parser_type = get_parser_type(label)

    parsed_cell_results = None
    if parser_type == "dimension_UOM":
        parsed_value_list = dimension_uom.process(input_text, is_exceptional_profile)
        if parsed_value_list:
            # print("parsed_value_list", parsed_value_list)
            for idx, inner_list in enumerate(parsed_value_list):
                try:
                    parsed_cell_results = generate_dim_cells(cell, cell_idx, inner_list)
                except:
                    print(traceback.print_exc())
                    pass
            return parsed_cell_results

    elif parser_type == "temperature_parser":
        parsed_value_list = temperature_parser.process(input_text)
        if parsed_value_list:
            try:
                parsed_cell_results = generate_temperature_cells(
                    cell, parsed_value_list
                )
            except:
                print(traceback.print_exc())
                pass
        return parsed_cell_results

    elif parser_type == "weight_UOM":
        parsed_value_list = weight_uom.process(input_text)

        if parsed_value_list:
            try:
                parsed_cell_results = generate_weight_cells(cell, parsed_value_list)
            except:
                print(traceback.print_exc())
                pass
        return parsed_cell_results

    elif parser_type == "volume_UOM":
        parsed_value_list = volume_uom.process(input_text)
        if parsed_value_list:
            try:
                parsed_cell_results = generate_volume_cells(cell, parsed_value_list)
            except:
                print(traceback.print_exc())
                pass
        return parsed_cell_results

    elif parser_type == "packageCount":
        parsed_value_list = package_count.process(input_text)
        if parsed_value_list:
            try:
                parsed_cell_results = genereate_package_count_cells(
                    cell, parsed_value_list,utility_mapped_code_list
                )
            except:
                print(traceback.print_exc())
                pass
        return parsed_cell_results

    return None


def copy_to_all_rows_function(
    updated_rows, copy_to_all_rows, copy_to_all_row_index_storage
):
    """This function loops through each row and then check for a specific label and copies them to all rows except at index 0"""
    # Looping through each row
    for x_idx, x in enumerate(updated_rows):
        empty_row = False
        valid_cells = valid_cell_counter(x)
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            for y in copy_to_all_rows:
                present_previously = False
                present_index = None  # Index Placeholder
                for prev_idx, prev in enumerate(x["children"]):
                    if prev["label"] == y["label"]:
                        present_previously = True
                        present_index = prev_idx

                index_storage_value = copy_to_all_row_index_storage[y["label"]]

                if (
                    present_previously
                ):  # If the cell is present previously just copying the value from the first row to the said index
                    x["children"][present_index] = y
                else:
                    # If not append to the index from the first row
                    x["children"].insert(index_storage_value, y)

    return updated_rows


# WARNING: `trunicator` and `calulate_fields_trunicator` share logic/structure — changes to one may affect the other.
# Keep them in sync to avoid inconsistencies.
def calulate_fields_trunicator(cell):
    target_labels = [
        "grossWeight",
        "volume",
        "length",
        "width",
        "height",
        "goodsLinesHazardousMaterialVolume",
        "goodsLinesHazardousMaterialGrossWeight",
        "insuranceValue",
    ]

    if cell.get("label") in target_labels:
        cell_value = cell.get("v")

        if cell_value:
            processed_value = None
            try:
                processed_value = normalize_number_format(cell_value)
            except:
                processed_value = cell_value

            cell["v"] = processed_value

    return cell


def calculate_fields_function(updated_rows, rules_applied_on, rules_already_applied):
    for rule_key, rule_values in rules_applied_on.items():
        filtered_calculate_field_rules = [
            item for item in rule_values if item.get("type") == "calculateFields"
        ]

        if (
            filtered_calculate_field_rules
            and rule_key not in rules_already_applied.keys()
        ):
            for row_idx, row in enumerate(updated_rows):
                cells = row["children"]
                updated_cells = list()
                for cell_idx, cell in enumerate(cells):
                    try:
                        label = cell["label"]
                        if label == rule_key:
                            truncated_cell = calulate_fields_trunicator(cell)
                            changed_text = truncated_cell.get("v", "")

                            for rule_idx, rule in enumerate(
                                filtered_calculate_field_rules
                            ):
                                try:
                                    rule_inputs = rule["inputs"]
                                except:
                                    rule_inputs = rule["data"]["inputs"]

                                try:
                                    target_field = rule_inputs["value"]["fieldInfo"][
                                        "keyValue"
                                    ]
                                    target_condition = rule_inputs["condition"]
                                    target_value = None

                                    for target_cell in cells:
                                        if target_cell.get("label") == target_field:
                                            truncated_cell = calulate_fields_trunicator(
                                                target_cell
                                            )
                                            target_value = truncated_cell.get("v")
                                            break
                                    changed_text = apply_calculate_fields(
                                        changed_text, target_condition, target_value
                                    )

                                except:
                                    pass

                            cell["v"] = changed_text
                        updated_cells.append(cell)
                    except Exception:
                        pass

                row["children"] = updated_cells

            rules_already_applied[rule_key] = copy.deepcopy(
                filtered_calculate_field_rules
            )

    return updated_rows, rules_already_applied


def get_key_item_static_value(label, key_items):
    """Returns the 'shape' of the first key item matching 'label' in 'keyLabel', or an empty string if not found."""
    try:
        for item in key_items:
            if item.get("keyLabel") == label:
                return item.get("shape", "")  # Return shape if found, otherwise ""
        return ""  # Default value if keyLabel not found
    except:
        return ""


def get_target_value(
    cell, target_label, table_key_items, row_direction_rule, first_cell_copy_from
):
    """Returns the cell value, a static value from key items, or a fallback value based on the row direction rule."""
    if not cell["v"]:
        if row_direction_rule == RowDirectionRule.NON_EMPTY_ROWS.value:
            static_value = get_key_item_static_value(target_label, table_key_items)
            if static_value:
                return static_value
            elif first_cell_copy_from["v"]:
                return first_cell_copy_from["v"]
        return ""
    return cell["v"]


def copy_to_column_function(updated_rows, copy_to_column, first_row, table_key_items):
    """This function loops through each row and then check for a specific label and associated value and copies it to another label"""
    # Looping through each row
    for x_idx, x in enumerate(updated_rows):
        empty_row = False
        valid_cells = valid_cell_counter(x)
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            for y in copy_to_column:
                copy_done = False
                rule = y["rule"]
                target_value = None
                origin_label = y["cell_data"]["label"]
                target_pos = ""
                insert_pos = y["index"]
                target_page_id = ""
                target_table_id = None
                worksheet_name = None
                target_label = rule["inputs"]["columnName"]["fieldInfo"]["keyValue"]
                row_direction_type = rule["inputs"]["row"]
                first_cell_copy_from = y["cell_data"]
                for prev_idx, prev in enumerate(x["children"]):
                    if prev["label"] == origin_label:
                        target_value = get_target_value(
                            prev,
                            target_label,
                            table_key_items,
                            row_direction_type,
                            first_cell_copy_from,
                        )
                        target_pos = prev["pos"]
                        target_page_id = prev["pageId"]
                        target_table_id = prev.get("table_id")
                        worksheet_name = prev.get("worksheet_name")
                if target_value:
                    try:
                        target_parent = rule["inputs"]["columnName"]["parent"]
                    except:
                        target_parent = None

                    if row_direction_type == "first" and x_idx > 0:
                        continue

                    for prev_idx, prev in enumerate(x["children"]):
                        if prev["label"] == target_label:
                            prev["v"] = target_value
                            prev["pos"] = target_pos
                            copy_done = True
                    if not copy_done:
                        cell_to_insert = y.get("cell_data").copy()
                        cell_to_insert["label"] = target_label
                        if target_parent:
                            cell_to_insert["qualifierParent"] = target_parent
                        cell_to_insert["v"] = target_value
                        cell_to_insert["pos"] = target_pos
                        cell_to_insert["export"] = True
                        cell_to_insert["pageId"] = target_page_id
                        if target_table_id:
                            cell_to_insert["table_id"] = target_table_id
                        if worksheet_name:
                            cell_to_insert["worksheet_name"] = worksheet_name
                        cell_to_insert["id"] += "_" + target_label
                        x["children"].insert(insert_pos + 1, cell_to_insert)
    return updated_rows


def merge_row_function(input_rows, merge_row_input, first_row):
    """This function loops through each row and then check for a specific condition against the associated value of that
    cell and if the condition is met, adds it with the same cell in the previous row"""
    # Looping through each row
    for row_idx, row in enumerate(input_rows):
        if row_idx == first_row:  # If first row - Ignored
            continue

        empty_row = False
        valid_cells = valid_cell_counter(row)
        if valid_cells < 1:
            empty_row = True

        if not empty_row:
            for cell_idx, cell in enumerate(row["children"]):
                cell_label = cell["label"]
                associated_rule = merge_row_input.get(cell_label)
                if associated_rule:
                    rule_inputs = associated_rule["inputs"]
                    merge_type = rule_inputs["condition"]
                    target_value = rule_inputs["value"]
                    if merge_type == "cellCountLessThan":
                        if valid_cells < target_value:
                            replace_in_row_index = row_idx - 1
                            merge_done = False
                            while not merge_done:
                                try:
                                    for prev_cell in input_rows[replace_in_row_index][
                                        "children"
                                    ]:
                                        if prev_cell[
                                            "label"
                                        ] == cell_label and prev_cell.get("v"):
                                            prev_cell["v"] = (
                                                prev_cell["v"] + "\n" + cell["v"]
                                            )
                                            try:
                                                new_pos = get_value_pos_from_list(
                                                    [prev_cell["pos"], cell["pos"]]
                                                )
                                                prev_cell["pos"] = new_pos
                                            except:
                                                pass

                                            merge_done = True

                                    if not merge_done:
                                        replace_in_row_index -= 1
                                except:
                                    print(traceback.print_exc())
                                    pass
                            if merge_done:
                                cell["v"] = ""

    return input_rows


def distribute_column_throughout_rows(input_rows, distribute_row_input, first_row):
    """This function takes in a list of rows and for each specific cell label,
    fills up the rows that have empty value on the column with the preceding non empty text
    """

    # print(distribute_row_input)
    # Looping through each row
    def upward_distribution(row_idx, cell_label, input_cell):
        input_value = input_cell["v"]
        target_row_index = row_idx - 1
        if target_row_index >= 0:
            valid_cells = valid_cell_counter(input_rows[target_row_index])
            if valid_cells > 0:
                for cell in input_rows[target_row_index]["children"]:
                    if cell["label"] == cell_label:
                        if cell["v"]:
                            return input_rows
                        else:
                            cell["v"] = input_value
                            # print(target_row_index, "replaced")
                # print(target_row_index, input_cell)
                input_rows[target_row_index]["children"].append(input_cell)

            upward_distribution(target_row_index, cell_label, input_cell)

        return input_rows

    def downward_distribution(row_idx, cell_label, input_cell):
        input_value = input_cell["v"]
        target_row_index = row_idx + 1
        if target_row_index <= (len(input_rows) - 1):
            valid_cells = valid_cell_counter(input_rows[target_row_index])

            if valid_cells > 0:
                for cell in input_rows[target_row_index]["children"]:
                    if cell["label"] == cell_label:
                        if cell["v"]:
                            return input_rows
                        else:
                            cell["v"] = input_value
                            # print(target_row_index, "replaced")
                # print(target_row_index, input_cell)
                input_rows[target_row_index]["children"].append(input_cell)

            downward_distribution(target_row_index, cell_label, input_cell)

        return input_rows

    # Looping through each row
    for row_idx, row in enumerate(input_rows):
        empty_row = False
        valid_cells = valid_cell_counter(row)
        if valid_cells < 1:
            empty_row = True

        if not empty_row:
            for cell_idx, cell in enumerate(row["children"]):
                cell_label = cell["label"]
                associated_rule = distribute_row_input.get(cell_label)
                if associated_rule:
                    if cell["v"]:
                        upward_distribution(row_idx, cell_label, cell)
                        downward_distribution(row_idx, cell_label, cell)
    return input_rows


def get_first_valid_row(rows):
    try:
        for x_idx, x in enumerate(rows):
            if valid_cell_counter(x) > 0:
                return x_idx
        return 0
    except:
        return 0


def num(s):
    if "," in s:
        s = s.replace(",", ".")

    try:
        return int(s)
    except ValueError:
        return float(s)


def condition_pass(condition_type, origin_value, rule):
    try:
        if condition_type == "contains":
            if apply_contains_function(rule["inputs"], origin_value):
                return True
        elif condition_type == "greaterThan":
            value_to_compare = rule["inputs"]["valueGtLT"]
            if num(origin_value) > value_to_compare:
                return True
        elif condition_type == "lessThan":
            value_to_compare = rule["inputs"]["valueGtLT"]
            if num(origin_value) < value_to_compare:
                return True
    except:
        print(traceback.print_exc())
        pass

    return False


def set_value_function(updated_rows, set_value_storage, first_row):
    """Loops through each row and checks the value of a certain cell against a condition and generates/replaces a new column with a set value"""
    # Looping through each row
    for x_idx, x in enumerate(updated_rows):
        empty_row = False
        valid_cells = valid_cell_counter(x)
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            for y in set_value_storage:
                copy_done = False
                rule = y["rule"]
                origin_value = None
                origin_label = y["cell_data"]["label"]
                target_pos = ""
                insert_pos = y["index"]
                target_page_id = ""

                for prev_idx, prev in enumerate(x["children"]):
                    if prev["label"] == origin_label:
                        origin_value = prev["v"]
                        target_pos = prev["pos"]
                        target_page_id = prev["pageId"]

                if origin_value:
                    condition_type = rule["inputs"]["condition"]

                    if condition_pass(condition_type, origin_value, rule):
                        target_label = rule["inputs"]["columnName"]["fieldInfo"][
                            "keyValue"
                        ]
                        # target_label = rule["inputs"]["columnName"]
                        target_value = rule["inputs"]["columnValue"]

                        discontinue = False
                        for prev_idx, prev in enumerate(x["children"]):
                            if prev["label"] == target_label:
                                if not discontinue:
                                    prev["v"] = target_value
                                    prev["pos"] = target_pos
                                    copy_done = True

                        if not copy_done:
                            cell_to_insert = dict()
                            cell_to_insert["type"] = "cell"
                            cell_to_insert["label"] = target_label
                            cell_to_insert["v"] = target_value
                            cell_to_insert["pos"] = target_pos
                            cell_to_insert["pageId"] = target_page_id
                            cell_to_insert["export"] = True
                            x["children"].insert(insert_pos + 1, cell_to_insert)

    return updated_rows


def row_level_rule(
    rows,
    rules_applied_on,
    labels_to_process,
    table_key_items,
    rules_already_applied,
    definition_settings,
    definition_id,
):
    """
    This function takes in:
    1. a row
    2. a dictionary containing the cell labels
    3. a list of particular cell labels to process(this is used to not to reprocess a cell that has already gone through the process)

    After application and modification of the row, the updated rows are returned

    """

    updated_rows = list()
    copy_to_all_rows = list()
    copy_to_all_row_index_storage = dict()
    merge_column_storage = dict()
    distribute_column_storage = dict()
    first_row = get_first_valid_row(rows)
    copy_to_column_storage = list()
    set_value_storage = list()
    calculateFields = None

    exceptional_profiles = definition_settings.get("profileSettings", {}).get(
        "dimension_package_count_reverse_profiles", []
    )
    is_exceptional_profile = True if definition_id in exceptional_profiles else False

    for row_idx, row in enumerate(rows):
        cells = row["children"]
        updated_cells = list()
        end_cells = list()
        for cell_idx, cell in enumerate(cells):
            try:
                disregarded = (
                    False  # To track if this cell was disregarded for some reason
                )
                rules_data_set = list()
                already_appended = False

                if cell["label"] in rules_applied_on.keys():
                    if labels_to_process:
                        if not cell["label"] in labels_to_process:
                            updated_cells.append(cell)
                            continue
                    label = cell["label"]

                    rules_data_set = rules_applied_on[label]
                    # print(rules_data_set, "-------", cell["label"])
                    original_text = cell["v"]
                    changed_text = original_text
                    if not rules_data_set:
                        continue

                    for rule_idx, rule in enumerate(rules_data_set):
                        try:
                            rule_inputs = rule["inputs"]
                        except:
                            rule_inputs = rule["data"]["inputs"]

                        if rule["type"] == "contains":
                            if isinstance(changed_text, list):
                                changed_text = apply_contains_function_list(
                                    rule_inputs, changed_text
                                )
                            else:
                                if apply_contains_function(rule_inputs, changed_text):
                                    disregarded = False
                                else:
                                    disregarded = True
                                    cell["rule_decision"] = "disregarded"

                        elif rule["type"] == "replaceValue":
                            changed_text = apply_replace_function(
                                rule_inputs, changed_text
                            )
                        elif rule["type"] == "startsWithV5":
                            changed_text = apply_startswithv5_function(
                                rule_inputs, changed_text
                            )
                        elif rule["type"] == "endsWithV5":
                            changed_text = apply_endswithv5_function(
                                rule_inputs, changed_text
                            )
                        elif rule["type"] == "trim":
                            changed_text = trim_values_rule(rule_inputs, changed_text)
                        elif rule["type"] == "exclude":
                            changed_text = apply_exclude_rules_on(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "parseFrom":
                            # TODO: Reconfirm
                            parse_index = parse_index_finder(rule_inputs, changed_text)
                            parsed_text = None
                            if parse_index > -1:
                                parsed_text = changed_text[parse_index:]

                            if parsed_text:
                                changed_text = changed_text[:parse_index]
                                cell["v"] = changed_text
                                updated_cells.append(cell)
                                already_appended = True

                                new_parsed_cell = cell.copy()
                                new_parsed_cell["v"] = parsed_text
                                parse_label = rule["inputs"]["fieldName"]["fieldInfo"][
                                    "keyValue"
                                ]
                                # parse_label = rule["inputs"]["fieldName"]
                                new_parsed_cell["label"] = parse_label
                                updated_cells.insert(cell_idx + 1, new_parsed_cell)

                        elif rule["type"] == "copyToAllRows":
                            if row_idx == first_row:
                                if (
                                    not cell in copy_to_all_rows
                                ):  # Appending to the storage
                                    if cell["v"] and (not disregarded):
                                        copy_to_all_rows.append(cell)
                                        copy_to_all_row_index_storage[label] = cell_idx

                        elif rule["type"] == "copyToColumn":
                            if row_idx == first_row:
                                if cell["v"] and (not disregarded):
                                    data = {
                                        "cell_data": cell,
                                        "rule": rule,
                                        "index": cell_idx,
                                    }
                                    if not data in copy_to_column_storage:
                                        copy_to_column_storage.append(data)

                        elif rule["type"] == "mergeRow":
                            if not label in merge_column_storage.keys():
                                merge_column_storage[label] = rule

                        elif rule["type"] == "distributeRows":
                            if not label in distribute_column_storage.keys():
                                distribute_column_storage[label] = rule
                        elif rule["type"] == "convertDecimalsToCW1":
                            changed_text = apply_convert_decimals_to_cw1(
                                rule_inputs, changed_text
                            )
                        elif rule["type"] == "formatDate":
                            if not cell.get("formated_date"):
                                changed_text = convert_date.process(changed_text)

                        elif rule["type"] == "extractSubstring":
                            changed_text = apply_extract_substring_function(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "deleteFrom":
                            changed_text = apply_delete_from(rule_inputs, changed_text)

                        elif rule["type"] == "deleteUntil":
                            changed_text = apply_delete_Until(rule_inputs, changed_text)

                        elif rule["type"] == "extractPattern":
                            changed_text = apply_extract_pattern(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "setValue":
                            if not disregarded:
                                data = {
                                    "cell_data": {"label": cell.get("label")},
                                    "rule": rule,
                                    "index": cell_idx,
                                }
                                if not data in set_value_storage:
                                    set_value_storage.append(data)

                        elif rule["type"] == "convertToUppercase":
                            changed_text = set_uppercase_values_rule(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "addPrefix":
                            try:
                                changed_text = apply_prefix_rule(
                                    rule_inputs, changed_text
                                )
                            except:
                                pass

                        elif rule["type"] == "addSuffix":
                            try:
                                changed_text = apply_suffix_rule(
                                    rule_inputs, changed_text
                                )
                            except:
                                pass

                        elif rule["type"] == "convertToLowercase":
                            changed_text = set_lowercase_values_rule(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "calculate":
                            changed_text = apply_calculate_function(
                                rule_inputs, changed_text
                            )
                        elif rule["type"] == "calculateFields":
                            calculateFields = True

                        elif rule["type"] == "reparse":
                            if not disregarded:
                                # TODO: Reconfirm
                                parsed_cell_results = fetch_parsed_cells(
                                    cell, cell_idx, changed_text, is_exceptional_profile
                                )
                                if parsed_cell_results:
                                    for parsed_cell_idx, parsed_cell in enumerate(
                                        parsed_cell_results
                                    ):
                                        placement = cell_idx + 1 + parsed_cell_idx

                                        def search_for_cell_with_label(
                                            input_label, cells_list
                                        ):
                                            output = list()
                                            for x_idx, x in enumerate(cells_list):
                                                if x["label"] == input_label:
                                                    output.append(x_idx)
                                            return output

                                        cell_already_present = (
                                            search_for_cell_with_label(
                                                parsed_cell["label"], cells
                                            )
                                        )

                                        if not cell_already_present:
                                            updated_cells.insert(placement, parsed_cell)
                                        else:
                                            end_cells.append(parsed_cell)
                        elif rule["type"] == "roundDecimal":
                            if not disregarded:
                                changed_text = apply_round_decimal_rule(
                                    rule_inputs, changed_text
                                )

                        elif rule["type"] == "conditionedRule":
                            if not disregarded:
                                changed_text = apply_conditioned_rule(
                                    rule_inputs, changed_text
                                )
                        elif rule["type"] == "dimensionSeperatorFix":
                            if not disregarded:
                                changed_text = apply_dimension_sep_fix(changed_text)
                        elif rule["type"] == "formatCurrencyToNAStandard":
                            if not disregarded:
                                changed_text = apply_format_currency_to_na_standard(
                                    changed_text
                                )
                        elif rule["type"] == "correctDataType":
                            if not disregarded:
                                changed_text = apply_correct_data_type(
                                    rule_inputs, changed_text
                                )
                        elif rule["type"] == "DoNotTruncate":
                            cell["DoNotTruncate"] = "true"
                        elif rule["type"] == "split":
                            # Handle for list split
                            if isinstance(changed_text, list):
                                new_splited_dict = {}
                                new_changed_text = []
                                for list_idx, list_item in enumerate(changed_text):
                                    split_data = apply_split_by_seperator(
                                        rule_inputs, list_item
                                    )
                                    if not split_data:
                                        # Pass the same value if it exists
                                        continue
                                    new_changed_text.append(split_data[0])
                                    for data_idx, data in enumerate(split_data[1:]):
                                        # Add to dictionary to append new data to specific cell
                                        if data_idx not in new_splited_dict:
                                            new_splited_dict[data_idx] = []
                                        new_splited_dict[data_idx].append(data)
                                changed_text = new_changed_text
                                # Second pass to create new cell
                                for k, v in new_splited_dict.items():
                                    new_cell = cell.copy()
                                    new_cell["v"] = v
                                    new_cell["label"] = cell["label"] + "__" + str(k)
                                    updated_cells.append(new_cell)
                            else:
                                split_data = apply_split_by_seperator(
                                    rule_inputs, changed_text
                                )
                                changed_text = split_data[0]
                                for data_idx, data in enumerate(split_data[1:]):
                                    new_cell = cell.copy()
                                    new_cell["v"] = data
                                    new_cell["label"] = (
                                        cell["label"] + "__" + str(data_idx)
                                    )
                                    updated_cells.append(new_cell)
                        else:
                            pass

                    if not disregarded and not already_appended:
                        cell["v"] = changed_text
                        updated_cells.append(cell)

                else:
                    updated_cells.append(cell)

            except:
                print(traceback.print_exc())
                updated_cells.append(cell)

        if end_cells:
            updated_cells += end_cells

        row["children"] = updated_cells
        updated_rows.append(row)

    """Irregular rules such as merge, distribute, copy to all rows, copy to column. set value
    These are processed at the very end of all small rules """

    if merge_column_storage:
        updated_rows = merge_row_function(updated_rows, merge_column_storage, first_row)

    if distribute_column_storage:
        distribute_column_throughout_rows(
            updated_rows, distribute_column_storage, first_row
        )

    if copy_to_all_rows:
        """if copy to all rows, run a function that copies/replaces that value in each row"""
        updated_rows = copy_to_all_rows_function(
            updated_rows, copy_to_all_rows, copy_to_all_row_index_storage
        )

    if copy_to_column_storage:
        updated_rows = copy_to_column_function(
            updated_rows, copy_to_column_storage, first_row, table_key_items
        )

    if set_value_storage:
        updated_rows = set_value_function(updated_rows, set_value_storage, first_row)
    print("calculateFields", calculateFields)
    if calculateFields:
        updated_rows, rules_already_applied = calculate_fields_function(
            updated_rows, rules_applied_on, rules_already_applied
        )

    return updated_rows, rules_already_applied


def cell_label_extractor(rows):
    """extract cell labels from a row"""
    previous_cell_labels = list()
    for row in rows:
        for x in row["children"]:
            if x["label"] not in previous_cell_labels:
                previous_cell_labels.append(x["label"])
    return previous_cell_labels


def table_rules_process(request_data, d_json):
    tableRulesVersion = "v5.1.15092023.00"
    # @Emon on 05/10/2022 - initiated table rules script
    # @Emon on 06/10/2022 - Added ReplaceValue and Parse From
    # @Emon on 10/10/2022 - Bug Fix - CopyToAllRows - displayed in empty rows
    # @Emon on 11/10/2022 - Exclude Rule added
    # @Emon on 13/10/2022 - Merge row on cell count added
    # @Emon on 14/10/2022 First valid row finder added
    # @Emon on 15/10/2022 - Distribute Row rule added
    # @Emon on 19/10/2022 - CW1 Conversion Rule added
    # @Emon on 23/10/2022 - Extract Substring added
    # @Emon on 24/10/2022 - Second level rule application added
    # @Emon on 24/10/2022 - Delete From Delete Until Rules added
    # @Emon on 29/10/2022 - Copy to Column Rule Added
    # @Emon on 31/10/2022 - Set Value Column Rule Added
    # @Emon on 22/11/2022 - Reparse Rule Added
    # @Emon on 28/11/2022 - Reparse bug fix
    # @Emon on 03/12/2022 - UpperCase, LowerCase, Calculate Rules Added
    # @Emon on 09/01/2023 - Conditioned Rule updated
    # @Emon on 16/01/2023 - Conditioned Rules now has contains regex and delete until
    # @Emon on 07/02/2023 - Set Value rule now has greater than and lesser than added to it

    try:
        definitions_list = request_data.get("definitions", [])
        definitions = definitions_list[0] if definitions_list else {}
        definition_settings = request_data.get("definition_settings")
    except:
        definitions = {}
        definition_settings = None

    docs = d_json["nodes"]

    # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass

    for input_doc_idx, target_doc in enumerate(docs):
        try:
            # Figuring a way out here
            if test_document_trigger != None:
                if test_document_trigger != target_doc["id"]:
                    continue
            nodes = target_doc["children"]
            for i, node in enumerate(nodes):
                node_children = node["children"]
                if "table" in node["type"]:
                    # Multi_table update
                    rules_applied_on = dict()
                    try:
                        table_definitions = definitions.get("table")
                        table_unique_id = node.get("table_name")
                        table_rules = None
                        for table_definition in table_definitions:
                            if (
                                table_definition.get("table_name") == table_unique_id
                            ):
                                target_def = table_definition.get(
                                    "table_definition_data"
                                )
                                table_rules = target_def.get("ruleItems",[])
                                table_key_items = target_def.get("keyItems",[])
                        if not table_rules:
                            continue

                        for table_rule in table_rules:
                            rules_applied_on[table_rule["label"]] = table_rule["rules"]
                    except:
                        print(traceback.print_exc())
                    label_to_process = list()
                    rows = node["children"]
                    mother_cell_labels = cell_label_extractor(rows)

                    rules_already_applied = dict()
                    # Processing each row using a row level function
                    updated_rows, rules_already_applied = row_level_rule(
                        rows,
                        rules_applied_on,
                        label_to_process,
                        table_key_items,
                        rules_already_applied,
                        definition_settings,
                        definitions.get("definition_id"),
                    )

                    first_born_child_list = cell_label_extractor(updated_rows)

                    new_born_list = [
                        y for y in first_born_child_list if y not in mother_cell_labels
                    ]

                    if new_born_list:
                        print("Inside here")
                        updated_rows, rules_already_applied = row_level_rule(
                            updated_rows,
                            rules_applied_on,
                            new_born_list,
                            table_key_items,
                            rules_already_applied,
                            definition_settings,
                            definitions.get("definition_id"),
                        )
                    node["children"] = updated_rows
                    assign_unique_id_helper(node)

        except:
            print(traceback.print_exc())
            pass
    return d_json
