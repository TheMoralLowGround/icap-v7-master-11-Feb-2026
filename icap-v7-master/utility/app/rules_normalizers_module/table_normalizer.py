import copy
import traceback

from app.misc_modules.unique_id import assign_unique_id_helper

from .table_rules_centre import fetch_parsed_cells

"""
This Python script is designed to normalize and clean up data in tables within JSON documents. Here's a summary in simple terms:

1. The script imports various functions and modules to assist in the normalization process.

2. It defines several helper functions to perform specific tasks, such as checking if a cell is visible, counting the number of valid cells in a row, and converting pipe-separated inputs into lists.

3. The main function `normalize_table` takes two inputs: request data and a JSON document.

4. It iterates through each table node in the JSON document and applies various normalization rules based on the provided definitions and settings.

5. Some of the normalization rules include:
   - Removing rows based on the number of valid cells or specific column values
   - Removing duplicate rows or duplicate values within a column
   - Combining rows based on trigger columns and combining values from specified columns
   - Shifting values from multiple columns into new rows
   - Reparsing specific columns to extract additional data
   - Shifting cell values upwards based on the values in other columns

6. After applying the normalization rules, the script updates the table rows with the processed data and assigns unique IDs to the nodes.

7. The modified JSON document with the normalized tables is returned.

In summary, this script takes a JSON document containing tables and applies various rules and transformations to clean up and normalize the data within those tables. It removes unnecessary rows, combines or splits rows based on specific conditions, and extracts or rearranges data from the table cells to create a more structured and organized representation of the data.

Here's a more technical summary of the script:

This Python script, `normalize_table`, is part of a larger application and is responsible for normalizing and transforming tabular data in JSON documents based on predefined rules and configurations. The primary function is `normalize_table`, which takes two arguments: `request_data` (containing definitions and other metadata) and `d_json` (the JSON document to be normalized).

The script defines several helper functions:

1. `invisibility_checker`: Determines if a cell should be considered invisible based on its label and value.
2. `valid_cell_counter`: Counts the number of visible cells in a row.
3. `add_totals_field`: Adds total fields to the first valid row of a table.
4. `fetch_totals`: Retrieves total cells from a row.
5. `get_first_valid_index`: Finds the index of the first valid row in a table.
6. `removeRow_function`: Removes rows based on conditions like cell count or column values.
7. `shiftMultiplesOfColumnToRows_function`: Shifts values from multiple columns into new rows.
8. `remove_duplicate_row_function`: Removes duplicate rows based on visible cell values.
9. `empty_out_column_cells`: Removes duplicate values from a specified column.
10. `pipeSeparated_input_to_list`: Converts a pipe-separated string into a list.
11. `generate_trigger_dict`: Generates a dictionary of label-value pairs for trigger columns.
12. `generate_combination_dict`: Generates a dictionary of label-value pairs for columns to be combined.
13. `update_row_with_combined_data`: Updates a row with combined data from other rows.
14. `is_valid_string`: Checks if a string is non-empty and non-whitespace.
15. `shiftCellUpBasedOnColumn_function`: Shifts cell values upwards based on values in other columns.
16. `combineGoodsLine_function`: Combines rows based on trigger columns and combines values from specified columns.
17. `reparse_function`: Reparses cells in specified columns to extract additional data.

The `normalize_table` function iterates through each target document and table node in the JSON document. For each table node, it fetches the normalization rules and configurations from the `request_data`. It then applies the normalization rules by invoking the corresponding helper functions based on the rule type.

The supported normalization rules include:

1. `removeRow`: Removes rows based on conditions like cell count or column values.
2. `removeDuplicateRow`: Removes duplicate rows based on visible cell values.
3. `removeDuplicatesFromColumn`: Removes duplicate values from a specified column.
4. `combineGoodsLines`: Combines rows based on trigger columns and combines values from specified columns.
5. `shiftMultiplesOfColumnToRows`: Shifts values from multiple columns into new rows.
6. `reparse`: Reparses cells in specified columns to extract additional data.
7. `shiftCellUpBasedOnColumns`: Shifts cell values upwards based on values in other columns.

After applying the normalization rules, the script updates the table rows with the processed data and assigns unique IDs to the nodes using the `assign_unique_id_helper` function.

The script imports various functions and modules from other parts of the application, such as `fetch_parsed_cells` (for reparsing cells) and `assign_unique_id_helper` (for assigning unique IDs).

Overall, this script provides a flexible framework for normalizing and transforming tabular data in JSON documents by applying a set of predefined rules and configurations. It uses helper functions to perform specific tasks and updates the JSON document with the normalized data.


"""


def invisibility_checker(cell):
    cell_is_invisible = False
    cell_label = cell["label"]
    if (cell_label in ["None", "notInUse", ""]) or (cell_label[-1].isnumeric()):
        if not (
            "parser_generated" in cell.keys() and (cell["parser_generated"] == True)
        ):
            cell_is_invisible = True

    if cell["v"].strip() == "":
        cell_is_invisible = True
    return cell_is_invisible


def valid_cell_counter(input_row):
    """Counts the number of visible cells in a row"""

    visible_cell_count = 0
    cells = input_row["children"]
    for cell_idx, cell in enumerate(cells):
        try:
            cell_is_invisible = invisibility_checker(cell)
            if not cell_is_invisible:
                visible_cell_count += 1
        except:
            print(traceback.print_exc())
            visible_cell_count += 1
    return visible_cell_count


def add_totals_field(totals_storage, row_data):
    first_row = row_data.copy()
    cells = first_row.get("children")
    for c_idx, c in reversed(list(enumerate(cells))):
        label = c.get("label")
        if label in totals_storage.keys():
            cells[c_idx] = totals_storage[label]
            del totals_storage[label]
    return cells


def fetch_totals(cells):
    output_dict = dict()
    tuple_set_1 = ("weight", "volume", "count")
    for cell in cells:
        label = cell.get("label")
        if (
            label.lower().endswith(tuple_set_1)
            and cell.get("table_key_generated")
            and not cell.get("originates_from_multiples")
        ):
            output_dict[label] = cell

    return output_dict


def get_first_valid_index(input_rows):
    """Returns the row index of the first valid row"""
    for idx, input_row in enumerate(input_rows):
        if valid_cell_counter(input_row) > 0:
            return idx

    return None


def removeRow_function(rows, item_inputs):
    # print("Table Normalizer - Remove Row Function Triggered")
    final_rows = list()
    removal_type = item_inputs["condition"]
    target_value = item_inputs["value"]
    totals_storage = dict()
    try:
        if (removal_type == "cellCountLessThan") or (
            removal_type == "cellCountLessThanShiftTotals"
        ):
            target_value = int(target_value)
            if not target_value > 0:
                return False, rows
    except:
        pass

    if removal_type == "cellCountLessThan":
        for row_idx, row in enumerate(rows):
            visible_cell_count = 0
            cells = row["children"]
            for cell_idx, cell in enumerate(cells):
                cell_is_invisible = False
                cell_label = cell["label"]
                if (cell_label in ["None", "notInUse", ""]) or (
                    cell_label[-1].isnumeric()
                ):
                    if not (
                        "parser_generated" in cell.keys()
                        and (cell["parser_generated"] == True)
                    ):
                        cell_is_invisible = True

                if isinstance(cell["v"], str) and cell["v"].strip() == "":
                    cell_is_invisible = True

                if not cell_is_invisible:
                    visible_cell_count += 1
            if visible_cell_count >= target_value:
                final_rows.append(row)

    elif removal_type == "columnValue":
        """Remove rows based on columnValue"""
        value_storage = list()
        for row_idx, row in enumerate(rows):
            valid_cells = valid_cell_counter(row)
            empty_row = False
            value = ""
            if valid_cells < 1:
                empty_row = True
            if not empty_row:
                cells = row["children"]
                for cell_idx, cell in enumerate(cells):
                    cell_label = cell.get("label")
                    if cell_label == target_value and cell.get("v"):
                        if cell.get("v").strip() != "":
                            value = cell.get("v")
                if value and (not value in value_storage):
                    value_storage.append(value)
                    final_rows.append(row)

    elif removal_type == "cellCountLessThanShiftTotals":
        first_valid_row = get_first_valid_index(rows)

        for row_idx, row in enumerate(rows):
            visible_cell_count = 0
            cells = row["children"]
            if row_idx == first_valid_row:
                totals_storage = fetch_totals(cells)

            for cell_idx, cell in enumerate(cells):
                cell_is_invisible = False
                cell_label = cell["label"]
                if (cell_label in ["None", "notInUse", ""]) or (
                    cell_label[-1].isnumeric()
                ):
                    if not (
                        "parser_generated" in cell.keys()
                        and (cell["parser_generated"] == True)
                    ):
                        cell_is_invisible = True

                if cell["v"].strip() == "":
                    cell_is_invisible = True

                if not cell_is_invisible:
                    visible_cell_count += 1
            if visible_cell_count >= target_value:
                final_rows.append(row)

    else:
        return False, rows

    try:
        if final_rows and totals_storage:
            first_valid_index = get_first_valid_index(final_rows)
            if first_valid_index != None:
                final_rows[first_valid_index]["children"] = add_totals_field(
                    totals_storage, final_rows[first_valid_index]
                )
    except:
        print(traceback.print_exc())
        pass

    return True, final_rows


def shiftMultiplesOfColumnToRows_function(rows, item_inputs):
    """This rule shifts value of multiple columns to next rows / initiates new row.
    Use case: In one table there is two dimensions. dimension and dimension_1. This will generate
    a copy the first row and then create another same row but the new row will have the value of dimension_1 as the dimension
    """

    target_columns = item_inputs.get("columns")
    target_columns_list = pipeSeparated_input_to_list(target_columns)

    final_rows = list()

    target_column_data_storage_by_row_idx = dict()

    for row_idx, row in enumerate(rows):
        target_cells_data = dict()
        valid_cells = valid_cell_counter(row)
        empty_row = False
        tbr = list()
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            cells = row["children"]
            target_cell = None
            for cell_idx, cell in enumerate(cells):
                cell_label = cell.get("label")
                if cell_label[-1].isnumeric():
                    parent = cell_label[:-2]
                    if parent in target_columns_list:
                        if cell.get("v"):
                            if cell.get("v").strip():
                                if parent in target_cells_data.keys():
                                    target_cells_data[parent].append(cell)
                                else:
                                    target_cells_data[parent] = [cell]
                                tbr.append(cell)
            if tbr:
                row["children"] = [c for c in cells if c not in tbr]
            if target_cells_data:
                target_column_data_storage_by_row_idx[row_idx] = target_cells_data

        final_rows.append(row)

    for r_idx, storage_data in target_column_data_storage_by_row_idx.items():
        # Getting the maximum number of cells in the whole dataset disregarding label type
        get_max_val_size = 0
        for _, associated_cells in storage_data.items():
            if len(associated_cells) > get_max_val_size:
                get_max_val_size = len(associated_cells)

        # Inserting number of rows according to get_max_val_size after the row in index
        for i in range(get_max_val_size):
            try:
                row_dict = copy.deepcopy(final_rows[r_idx])
                # Copying the previous row
                row_dict["children"] = [
                    x
                    for x in row_dict["children"]
                    if x["label"] not in storage_data.keys()
                ]

                # If totals set to 0
                tuple_set_1 = ("weight", "volume", "count")
                for c in row_dict["children"]:
                    try:
                        if c["v"].strip():
                            label = c.get("label")
                            if (
                                label.lower().endswith(tuple_set_1)
                                and c.get("table_key_generated")
                                and not c.get("originates_from_multiples")
                            ):
                                c["v"] = "0"
                    except:
                        pass

            except:
                row_dict = dict()
                row_dict["type"] = "row"
                row_dict["pos"] = ""
                row_dict["pageId"] = ""
                row_dict["children"] = []

            for key, associated_cells in storage_data.items():
                for associated_cell in associated_cells:
                    if associated_cell["label"][-1] == str(i + 1):
                        associated_cell["label"] = key
                        row_dict["children"].append(associated_cell)

            if row_dict["children"]:
                try:
                    target_index = r_idx + i + 1
                    # integrating in final rows
                    final_rows.insert(target_index, row_dict)
                except:
                    final_rows.append(row_dict)

    return final_rows


def remove_duplicate_row_function(input_rows, item_inputs):
    row_holder_valid_cell_only = list()
    output_rows = list()
    for row_idx, row in enumerate(input_rows):
        disregard_row = False
        valid_cell_data = dict()
        empty_row = False
        valid_cells = valid_cell_counter(row)
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            cells = row["children"]
            for cell_idx, cell in enumerate(cells):
                if not invisibility_checker(cell):
                    valid_cell_data[cell["label"]] = cell["v"]

        if valid_cell_data:
            if not (valid_cell_data in row_holder_valid_cell_only):
                row_holder_valid_cell_only.append(valid_cell_data)
            else:
                disregard_row = True

        if not disregard_row:
            output_rows.append(row)

    return output_rows


def empty_out_column_cells(rows, item_inputs):
    """Empty out cell based on duplicate columnValue"""
    target_column = item_inputs.get("value")
    value_storage = list()
    final_rows = list()

    for row_idx, row in enumerate(rows):
        valid_cells = valid_cell_counter(row)
        empty_row = False
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            cells = row["children"]
            for cell_idx, cell in enumerate(cells):
                cell_label = cell.get("label")
                if cell_label == target_column and cell.get("v"):
                    if cell.get("v").strip() != "":
                        value = cell.get("v")
                        if value in value_storage:
                            cell["v"] = ""
                        else:
                            value_storage.append(value)
        final_rows.append(row)

    return final_rows


def pipeSeparated_input_to_list(input_text):
    if ("|") in input_text:
        return input_text.split("|")
    else:
        return [input_text]


def generate_trigger_dict(cells, trigger_columns_list):
    """Generates a dict with label value pairs"""
    output_dict = dict()
    label_list = trigger_columns_list.copy()

    for cell in reversed(cells):
        label = cell.get("label").strip()
        if label in label_list:
            output_dict[label] = cell["v"]
            label_list.remove(label)

    return output_dict


def generate_combination_dict(cells, combine_on_columns_list):
    """Generates a dict with label value pairs (Values are in floats)"""
    output_dict = dict()
    label_list = combine_on_columns_list.copy()

    for cell in reversed(cells):
        label = cell.get("label").strip()
        if label in label_list:
            output_dict[label] = cell["v"].replace(",", ".")
            label_list.remove(label)

    return output_dict


def update_row_with_combined_data(row, combination_data):
    """Updates a list of cells with new values"""
    cells = row.get("children")

    for key, value in combination_data.items():
        cell_dict = dict()
        if key == "packageCount":
            value = int(round(float(value)))
        cell_dict["v"] = value
        cell_dict["id"] = ""
        cell_dict["type"] = "cell"
        cell_dict["pageId"] = ""
        cell_dict["pos"] = ""
        cell_dict["label"] = key
        cells.append(cell_dict)

    # Debugging this error
    # for cell in reversed(cells):
    #     label = cell.get("label")
    #     if label in combination_data.keys():
    #         value_to_replace = combination_data[label]
    #         cell["v"] = str(value_to_replace)

    #         del combination_data[label]

    new_row = row.copy()
    new_row["children"] = cells

    return new_row


def is_valid_string(input_text):
    if input_text:
        if input_text.strip():
            return True
    return False


def shiftCellUpBasedOnColumn_function(rows, item_inputs):
    columns_to_shift = pipeSeparated_input_to_list(item_inputs.get("targetColumns"))
    trigger_column_names = pipeSeparated_input_to_list(
        item_inputs.get("basedOnColumns")
    )
    removal_indexes = list()

    for r_idx, row in reversed(list(enumerate(rows))):
        check_done = list()
        valid_cells = valid_cell_counter(row)
        empty_row = False
        data_to_shift = dict()
        # Checking if target columns do have a valid value
        target_columns_valid = True

        # Checking if trigger columns are empty/does not exist
        trigger_columns_empty = True

        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            cells = row["children"]
            for c_idx, c in reversed(list(enumerate(cells))):
                label = c["label"]
                value = c["v"]

                if label in columns_to_shift and not label in check_done:
                    check_done.append(label)
                    if not is_valid_string(value):
                        target_columns_valid = False
                    else:
                        data_to_shift[label] = c

                elif label in trigger_column_names and not label in check_done:
                    check_done.append(label)
                    if is_valid_string(value):
                        trigger_columns_empty = False

            if target_columns_valid and trigger_columns_empty and data_to_shift:
                up_column_index = r_idx - 1
                try:
                    target_row = rows[up_column_index]
                    target_row_has_triggers_populated = True
                    target_row_has_empty_target_columns = True
                    check_done = list()
                    for c_idx, c in reversed(list(enumerate(target_row["children"]))):
                        label = c["label"]
                        if label in trigger_column_names and label not in check_done:
                            check_done.append(label)
                            if not is_valid_string(c["v"]):
                                target_row_has_triggers_populated = False
                        elif label in columns_to_shift and label not in check_done:
                            check_done.append(label)
                            if is_valid_string(c["v"]):
                                target_row_has_empty_target_columns = False

                    if (
                        target_row_has_triggers_populated
                        and target_row_has_empty_target_columns
                    ):
                        for key, cell_data in data_to_shift.items():
                            appending_done = False
                            for c in target_row["children"]:
                                if c["label"] == key:
                                    c = cell_data
                                    appending_done = True
                            if not appending_done:
                                target_row["children"].append(cell_data)

                        removal_indexes.append(r_idx)

                except:
                    print(traceback.print_exc())
                    pass

    if removal_indexes:
        for r_idx in removal_indexes:
            rows[r_idx]["children"] = [
                x for x in rows[r_idx]["children"] if not x["label"] in columns_to_shift
            ]

    return rows


def combineGoodsLine_function(rows, item_inputs):
    """Combines goodsLines based on given inputs such as trigger column and combine on column
    The trigger column value matches are taken into consideration while values are combined on the specified combine on columns
    """

    input_rows = rows.copy()

    #
    trigger_columns_inputs = item_inputs.get("basedOnColumns")
    combine_on_trigger_inputs = item_inputs.get("combineOnColumns")
    trigger_columns_input = ""
    combine_on_trigger_input = ""

    for idx in range(len(trigger_columns_inputs)):
        if idx == 0:
            trigger_columns_input = trigger_columns_inputs[idx]["fieldInfo"]["keyValue"]
        else:
            trigger_columns_input += "|"
            trigger_columns_input += trigger_columns_inputs[idx]["fieldInfo"][
                "keyValue"
            ]

    for idx in range(len(combine_on_trigger_inputs)):
        if idx == 0:
            combine_on_trigger_input = combine_on_trigger_inputs[idx]["fieldInfo"][
                "keyValue"
            ]
        else:
            combine_on_trigger_input += "|"
            combine_on_trigger_input += combine_on_trigger_inputs[idx]["fieldInfo"][
                "keyValue"
            ]
    #

    # trigger_columns_input = item_inputs.get("basedOnColumns")
    # combine_on_trigger_input = item_inputs.get("combineOnColumns")
    trigger_columns_list = pipeSeparated_input_to_list(trigger_columns_input)
    combine_on_columns_list = pipeSeparated_input_to_list(combine_on_trigger_input)

    trigger_dict = dict()
    trigger_index = None
    remove_indexes = list()
    combination_dict = dict()

    trigger_row_dict = dict()

    for row_idx, row in enumerate(input_rows):
        valid_cells = valid_cell_counter(row)
        empty_row = False
        if valid_cells < 1:
            empty_row = True
        if not empty_row:
            cells = row["children"]
            if trigger_dict:
                current_trigger_dict = generate_trigger_dict(
                    cells, trigger_columns_list
                )
                if current_trigger_dict == trigger_dict:
                    remove_indexes.append(row_idx)
                    current_combination_dict = generate_combination_dict(
                        cells, combine_on_columns_list
                    )

                    # Update Combination Dict
                    for key, value in current_combination_dict.items():
                        if key in combination_dict[trigger_index].keys():
                            val_prev = float(combination_dict[trigger_index][key])
                            val_up = val_prev + float(value)
                            combination_dict[trigger_index][key] = str(val_up)
                            # combination_dict[trigger_index][key] += value
                        else:
                            combination_dict[trigger_index][key] = str(value)

                else:
                    if current_trigger_dict in trigger_row_dict.values():
                        remove_indexes.append(row_idx)
                        trigger_dict = current_trigger_dict
                        trigger_index = list(trigger_row_dict.keys())[
                            list(trigger_row_dict.values()).index(trigger_dict)
                        ]
                        current_combination_dict = generate_combination_dict(
                            cells, combine_on_columns_list
                        )

                        # Update Combination Dict
                        for key, value in current_combination_dict.items():
                            if key in combination_dict[trigger_index].keys():
                                val_prev = float(combination_dict[trigger_index][key])
                                val_up = val_prev + float(value)
                                combination_dict[trigger_index][key] = str(val_up)
                                # combination_dict[trigger_index][key] += value
                            else:
                                combination_dict[trigger_index][key] = str(value)

                    else:
                        trigger_dict = generate_trigger_dict(
                            cells, trigger_columns_list
                        )
                        trigger_index = row_idx
                        combination_dict[trigger_index] = generate_combination_dict(
                            cells, combine_on_columns_list
                        )
                        trigger_row_dict[trigger_index] = trigger_dict

            else:
                trigger_dict = generate_trigger_dict(cells, trigger_columns_list)
                trigger_index = row_idx
                trigger_row_dict[trigger_index] = trigger_dict
                combination_dict[trigger_index] = generate_combination_dict(
                    cells, combine_on_columns_list
                )

    # Update rows based on combined data
    for row_idx, row in enumerate(input_rows):
        if row_idx in combination_dict.keys():
            row = update_row_with_combined_data(row, combination_dict[row_idx])

    # Remove matched rows
    input_rows = [row for i, row in enumerate(input_rows) if not i in remove_indexes]
    return input_rows


def reparse_function(input_rows, item_inputs, is_exceptional_profile=False):
    columns_to_parse = item_inputs.get("columns")
    columns_to_parse_list = pipeSeparated_input_to_list(columns_to_parse)

    for r in input_rows:
        cells = r.get("children")
        end_cells = list()
        for cell_idx, cell in enumerate(cells):
            if cell["label"] in columns_to_parse_list:
                parsed_cell_results = fetch_parsed_cells(
                    cell, cell_idx, cell["v"], is_exceptional_profile
                )
                if parsed_cell_results:
                    for parsed_cell_idx, parsed_cell in enumerate(parsed_cell_results):
                        placement = cell_idx + 1 + parsed_cell_idx

                        def search_for_cell_with_label(input_label, cells_list):
                            output = list()
                            for x_idx, x in enumerate(cells_list):
                                if x["label"] == input_label:
                                    output.append(x_idx)
                            return output

                        cell_already_present = search_for_cell_with_label(
                            parsed_cell["label"], cells
                        )

                        if not cell_already_present:
                            cells.insert(placement, parsed_cell)
                        else:
                            end_cells.append(parsed_cell)

        if end_cells:
            cells += end_cells

        r["children"] = cells

    return input_rows


def notEmptyColumn_function(rows, item_inputs):
    final_rows = list()
    removal_values = list()
    if "|" in item_inputs["removeIfValue"]:
        removal_values = item_inputs["removeIfValue"].split("|")
    else:
        removal_values.append(item_inputs["removeIfValue"])
    target_columns = list()
    for column in item_inputs["notEmptyColumn"]:
        target_columns.append(column["fieldInfo"]["keyValue"])

    targets_found = False
    for row_idx, row in enumerate(rows):
        valid_row = True
        cells = row["children"]
        for cell in cells:
            if cell["label"] in target_columns:
                targets_found = True
                if (cell["v"] in removal_values) or (cell["v"].strip() == ""):
                    valid_row = False
                    break
        if valid_row and targets_found:
            final_rows.append(row)
    if targets_found:
        return final_rows
    return rows


def normalize_table(request_data, d_json):
    normalizeTable_version = "v5.0.16022023"
    # @Emon on 07/10/2022 - initiated table rules script
    # @Emon on 14/10/2022 - Remove Row on valid cells rule applied
    # @Emon on 09/01/2022 - Remove rows based on column duplicate cell value added, Empty out column cells rule added
    # @Emon on 21/01/2022 - Remove row shift totals added
    # @Emon on 08/02/2023 - Shift Multiples Of Column Rows function added
    # @Emon on 16/02/2023 - Shift Cell Up Rule added

    try:
        definitions = request_data["definitions"]
        if definitions == []:
            definitions = {}
        else:
            definitions = definitions[0]
        definition_settings = request_data.get("definition_settings")
    except:
        pass

    exceptional_profiles = definition_settings.get("profileSettings", {}).get(
        "dimension_package_count_reverse_profiles", []
    )
    is_exceptional_profile = (
        True if definitions.get("definition_id") in exceptional_profiles else False
    )

    docs = d_json["nodes"]

    # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = int(request_data["document_id"].split(".")[-1]) - 1
    except:
        pass

    for input_doc_idx, target_doc in enumerate(docs):
        try:
            # Figuring a way out here
            if test_document_trigger != None:
                if test_document_trigger != input_doc_idx:
                    continue
            nodes = target_doc["children"]
            for i, node in enumerate(nodes):
                node_children = node["children"]
                if "table" in node["type"]:
                    try:
                        # Multi_table update
                        try:
                            table_definitions = definitions.get("table")
                            table_unique_id = node.get("table_name")
                            normalizer_items = None
                            for table_definition in table_definitions:
                                if (
                                    table_definition.get("table_name")
                                    == table_unique_id
                                ):
                                    target_def = table_definition.get(
                                        "table_definition_data"
                                    )
                                    normalizer_items = target_def.get("normalizerItems")

                            if not normalizer_items:
                                continue
                        except:
                            print(traceback.print_exc())
                        rows = node["children"]

                        for item in normalizer_items:
                            item_type = item["type"]
                            item_inputs = item["inputs"]

                            if item["type"] == "removeRow":
                                modification, rows = removeRow_function(
                                    rows, item_inputs
                                )
                                if modification:
                                    assign_unique_id_helper(node)

                            elif item["type"] == "removeDuplicateRow":
                                try:
                                    rows = remove_duplicate_row_function(
                                        rows, item_inputs
                                    )
                                except:
                                    print(traceback.print_exc())
                                    pass
                            elif item["type"] == "removeDuplicatesFromColumn":
                                try:
                                    rows = empty_out_column_cells(rows, item_inputs)
                                except:
                                    print(traceback.print_exc())
                                    pass

                            elif item["type"] == "combineGoodsLines":
                                try:
                                    rows = combineGoodsLine_function(rows, item_inputs)

                                except:
                                    print(traceback.print_exc())
                                    pass

                            elif item["type"] == "shiftMultiplesOfColumnToRows":
                                try:
                                    rows = shiftMultiplesOfColumnToRows_function(
                                        rows, item_inputs
                                    )
                                except:
                                    print(traceback.print_exc())
                                    pass

                            elif item["type"] == "reparse":
                                try:
                                    rows = reparse_function(
                                        rows, item_inputs, is_exceptional_profile
                                    )

                                except:
                                    print(traceback.print_exc())
                                    pass

                            elif item["type"] == "shiftCellUpBasedOnColumns":
                                try:
                                    rows = shiftCellUpBasedOnColumn_function(
                                        rows, item_inputs
                                    )
                                except:
                                    print(traceback.print_exc)
                                    pass
                            elif item["type"] == "notEmptyColumnRemoveRow":
                                try:
                                    rows = notEmptyColumn_function(rows, item_inputs)
                                except:
                                    print(traceback.print_exc())
                                    pass

                            node["children"] = rows

                    except:
                        print(traceback.print_exc())
        except:
            print(traceback.print_exc())
            pass
    return d_json
