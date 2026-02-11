import copy
import json
import traceback

from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

from app.extraction_modules.excel_sub_module import (
    excel_column_range,
    remove_alpha,
    remove_digits,
)
from app.table_keys import initiate_blank_row

"""
Central API call for Excel table extraction.
Backend does not call docbuilder docker for table extraction for excel files.

"""

DATA_DICTIONARY = dict()


def get_row_range(worksheet_name):
    global DATA_DICTIONARY

    for elem in DATA_DICTIONARY["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]
            maxLength = max(int(k) for v in cell_data.values() for k in v.keys())
            return range(1, maxLength)

    return range(1, 1)


def get_selection_type(cell_range):
    """
    Gives the proper type of cell selection
    """
    range_type = None
    start_column_data = cell_range.split(":")[0]
    start_column = remove_digits(start_column_data)
    start_column_start_row = remove_alpha(start_column_data)
    end_column_data = cell_range.split(":")[1]
    end_column = remove_digits(end_column_data)
    end_column_end_row = remove_alpha(end_column_data)

    # column_range = excel_column_range(start_column, end_column)

    row_indexes_present = True
    if not start_column_start_row and not end_column_end_row:
        row_indexes_present = False

    if start_column == end_column:
        if not row_indexes_present:
            range_type = "single_column_unlimited"
        else:
            range_type = "single_column_limited"

    else:
        if not row_indexes_present:
            range_type = "merged_column_unlimited"
        else:
            range_type = "merged_column_limited"

    return range_type


def single_column_function(
    cell_range, worksheet_name, selection_type, multisheet_trigger
):
    """Eg. Cell range (A2:A10)"""

    global DATA_DICTIONARY

    # print("single_column_function")
    # print("multisheet_trigger", multisheet_trigger)
    cell_list = list()

    split_data = cell_range.split(":")
    column_name = remove_digits(split_data[0])
    if "unlimited" in selection_type:
        row_range = get_row_range(worksheet_name)
    else:
        row_range = range(
            int(remove_alpha(split_data[0])), int(remove_alpha(split_data[1])) + 1
        )
    if not multisheet_trigger:
        for elem in DATA_DICTIONARY["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                column_data = cell_data.get(column_name)
                for r in row_range:
                    cell_value = " "
                    cell_reference = " "
                    try:
                        cell_element = column_data.get(str(r))
                        cell_value = cell_element.get("value")
                        cell_reference = cell_element.get("id")
                    except:
                        pass

                    cell_value = str(cell_value)
                    if cell_value:
                        if cell_value[0] == "=":
                            cell_value = " "
                        elif cell_value == "#VALUE!":
                            cell_value = " "

                    cell_dict = dict()
                    cell_dict["v"] = cell_value
                    cell_dict["co_ordinates"] = cell_reference
                    cell_dict["worksheet_name"] = worksheet_name
                    cell_dict["type"] = "cell"
                    cell_dict["pos"] = ""
                    cell_dict["pageId"] = ""
                    cell_dict["cellRange"] = column_name + str(r)
                    cell_list.append(cell_dict)
    else:
        table_id = 0
        for elem in DATA_DICTIONARY["children"]:
            extarct_sheet = False
            if multisheet_trigger["condition"] == "contains":
                if multisheet_trigger["sheetName"].lower() in elem["title"].lower():
                    extarct_sheet = True
            elif multisheet_trigger["condition"] == "equals":
                if multisheet_trigger["sheetName"].lower() == elem["title"].lower():
                    extarct_sheet = True
            if extarct_sheet:
                cell_data = elem["cell_data"]
                column_data = cell_data.get(column_name)
                for r in row_range:
                    cell_value = " "
                    cell_reference = " "
                    try:
                        cell_element = column_data.get(str(r))
                        cell_value = cell_element.get("value")
                        cell_reference = cell_element.get("id")
                    except:
                        pass

                    cell_value = str(cell_value)
                    if cell_value:
                        if cell_value[0] == "=":
                            cell_value = " "
                        elif cell_value == "#VALUE!":
                            cell_value = " "

                    cell_dict = dict()
                    cell_dict["v"] = cell_value
                    cell_dict["co_ordinates"] = cell_reference
                    cell_dict["worksheet_name"] = elem["title"]
                    cell_dict["type"] = "cell"
                    cell_dict["pos"] = ""
                    cell_dict["pageId"] = ""
                    cell_dict["cellRange"] = column_name + str(r)
                    cell_dict["table_id"] = table_id
                    cell_list.append(cell_dict)
                table_id += 1
    # print("single_cell_list", cell_list)
    return cell_list


def merged_column_function(
    cell_range, worksheet_name, selection_type, multisheet_trigger
):
    """Eg. Cell range (A2:B10)"""

    global DATA_DICTIONARY
    # print("merged_column_function")
    # print("multisheet_trigger", multisheet_trigger)
    cell_list = list()

    start_column_data = cell_range.split(":")[0]
    end_column_data = cell_range.split(":")[1]

    try:
        start_column = remove_digits(start_column_data)
        start_column_start_row = remove_alpha(start_column_data)
    except:
        pass
    try:
        end_column = remove_digits(end_column_data)
        end_column_end_row = remove_alpha(end_column_data)
    except:
        pass

    if "unlimited" in selection_type:
        row_range = get_row_range(worksheet_name)
    else:
        row_range = range(int(start_column_start_row), int(end_column_end_row) + 1)
    column_range = excel_column_range(start_column, end_column)

    if not multisheet_trigger:
        for elem in DATA_DICTIONARY["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                for r in row_range:
                    cell_value_list = list()
                    for column in column_range:
                        cell_value = " "
                        cell_reference = " "
                        try:
                            column_data = cell_data.get(column)
                            cell_element = column_data.get(str(r))
                            cell_value = cell_element.get("value")
                            cell_reference = cell_element.get("id")
                            cell_value = str(cell_value)
                            # print("cell_value",cell_value)
                            if cell_value:
                                if cell_value[0] == "=":
                                    cell_value = " "
                                elif cell_value == "#VALUE!":
                                    cell_value = " "
                            cell_value_list.append(cell_value)
                        except:
                            # print(traceback.print_exc())
                            continue
                        cell_value_list.append(" ")

                    if cell_value_list:
                        cell_value_concatenated = " ".join(cell_value_list)
                        try:
                            if len(cell_value_list) > 1:
                                if all(x == " " for x in cell_value_list):
                                    cell_value_list = " "
                                else:
                                    cell_value_concatenated = (
                                        cell_value_concatenated.strip()
                                    )
                        except:
                            pass
                    else:
                        cell_value_concatenated = " "

                    cell_dict = dict()
                    cell_dict["v"] = cell_value_concatenated
                    cell_dict["co_ordinates"] = (
                        cell_reference  # Has to be the specific cell
                    )
                    cell_dict["worksheet_name"] = worksheet_name
                    cell_dict["type"] = "cell"
                    cell_dict["pos"] = ""
                    cell_dict["pageId"] = ""
                    cell_dict["cellRange"] = f"{start_column_data}:{end_column_data}"
                    cell_list.append(cell_dict)

    else:
        table_id = 0
        for elem in DATA_DICTIONARY["children"]:
            extarct_sheet = False
            if multisheet_trigger["condition"] == "contains":
                if multisheet_trigger["sheetName"].lower() in elem["title"].lower():
                    extarct_sheet = True
            elif multisheet_trigger["condition"] == "equals":
                if multisheet_trigger["sheetName"].lower() == elem["title"].lower():
                    extarct_sheet = True
            if extarct_sheet:
                cell_data = elem["cell_data"]
                for r in row_range:
                    cell_value_list = list()
                    for column in column_range:
                        cell_value = " "
                        cell_reference = " "
                        try:
                            column_data = cell_data.get(column)
                            cell_element = column_data.get(str(r))
                            cell_value = cell_element.get("value")
                            cell_reference = cell_element.get("id")
                            cell_value = str(cell_value)
                            # print("cell_value",cell_value)
                            if cell_value:
                                if cell_value[0] == "=":
                                    cell_value = " "
                                elif cell_value == "#VALUE!":
                                    cell_value = " "
                            cell_value_list.append(cell_value)
                        except:
                            # print(traceback.print_exc())
                            continue
                        cell_value_list.append(" ")

                    if cell_value_list:
                        cell_value_concatenated = " ".join(cell_value_list)
                        try:
                            if len(cell_value_list) > 1:
                                if all(x == " " for x in cell_value_list):
                                    cell_value_list = " "
                                else:
                                    cell_value_concatenated = (
                                        cell_value_concatenated.strip()
                                    )
                        except:
                            pass
                    else:
                        cell_value_concatenated = " "

                    cell_dict = dict()
                    cell_dict["v"] = cell_value_concatenated
                    cell_dict["co_ordinates"] = (
                        cell_reference  # Has to be the specific cell
                    )
                    cell_dict["worksheet_name"] = elem["title"]
                    cell_dict["type"] = "cell"
                    cell_dict["pos"] = ""
                    cell_dict["pageId"] = ""
                    cell_dict["cellRange"] = f"{start_column_data}:{end_column_data}"
                    cell_dict["table_id"] = table_id
                    cell_list.append(cell_dict)
                table_id += 1
    return cell_list


def extract_cells_on_selection_type(
    selection_type, cell_range, worksheet_name, multisheet_trigger
):
    cell_list = list()

    if "single_column" in selection_type:
        cell_list = single_column_function(
            cell_range, worksheet_name, selection_type, multisheet_trigger
        )

    elif "merged_column" in selection_type:
        cell_list = merged_column_function(
            cell_range, worksheet_name, selection_type, multisheet_trigger
        )

    return cell_list


def extract_cells(column, table_range, multisheet_trigger):
    """This returns a list of cell dictionaries for a particular column definition"""

    global DATA_DICTIONARY
    cell_range_all_data = column.get("cellRanges")

    cell_range_data = cell_range_all_data[0]
    worksheet_name = cell_range_data.get("sheetName")
    if not worksheet_name:
        sheet_number = cell_range_data.get("sheetNumber")
        if sheet_number:
            worksheet_name = DATA_DICTIONARY["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = DATA_DICTIONARY["children"][0]["title"]
    cell_range = cell_range_data.get("cellRange")
    try:
        if table_range["tableEnd"] == None:
            try:
                table_range["tableEnd"] = get_row_range(worksheet_name)[-1] + 1
                if multisheet_trigger:
                    worksheet_ranges = list()
                    for worksheet in DATA_DICTIONARY["children"]:
                        extract_sheet = False
                        if multisheet_trigger["condition"] == "contains":
                            if (
                                multisheet_trigger["sheetName"].lower()
                                in worksheet["title"].lower()
                            ):
                                extract_sheet = True
                        elif multisheet_trigger["condition"] == "equals":
                            if (
                                multisheet_trigger["sheetName"].lower()
                                == worksheet["title"].lower()
                            ):
                                extract_sheet = True
                        if extract_sheet:
                            worksheet_ranges.append(
                                get_row_range(worksheet["title"])[-1] + 1
                            )
                    table_range["tableEnd"] = max(worksheet_ranges)
            except IndexError:
                print(traceback.print_exc())
                table_range["tableEnd"] = (
                    int(remove_alpha(table_range["tableStart"])) + 1
                )

            table_range["tableEnd"] = cell_range[0] + str(table_range["tableEnd"])
    except:
        print(traceback.print_exc())
    try:
        if (
            len(cell_range) == 3
            and cell_range[0].isalpha()
            and cell_range[1] == ":"
            and cell_range[2].isalpha()
        ):
            first_column = cell_range.split(":")[0]
            second_column = cell_range.split(":")[1]
            startcolumn = remove_digits(first_column)
            startcolumn_startrow = remove_alpha(table_range["tableStart"])
            end_column = remove_digits(second_column)
            endcolumn_endrow = remove_alpha(table_range["tableEnd"])
            cell_range = (
                startcolumn + startcolumn_startrow + ":" + end_column + endcolumn_endrow
            )

        if not ":" in cell_range:
            end_column = remove_digits(cell_range)
            endcolumn_endrow = remove_alpha(table_range["tableEnd"])
            cell_range = cell_range + ":" + end_column + endcolumn_endrow
        else:
            first_range = cell_range.split(":")[0]
            second_range = cell_range.split(":")[1]
            startcolumn_startrow = remove_alpha(first_range)
            endcolumn_endrow = remove_alpha(second_range)
            if startcolumn_startrow == endcolumn_endrow:
                end_column = remove_digits(second_range)
                endcolumn_endrow = remove_alpha(table_range["tableEnd"])
                cell_range = first_range + ":" + end_column + endcolumn_endrow
    except:
        print(traceback.print_exc())

    """There could be multiple types of vertical column range selections
    1. Single Column Limited (A2:A10)
    2. Merged Column Limited (A2:B10)
    3. Single Column Unlimited (A:A)
    4. Merged Column Unlimited (A:B)
    """
    selection_type = get_selection_type(cell_range)

    # print(selection_type)
    # print("cell_range", cell_range)
    cell_list = extract_cells_on_selection_type(
        selection_type, cell_range, worksheet_name, multisheet_trigger
    )

    # print("cell_list",cell_list)
    return cell_list


def max_list_length(d):
    """
    Returns the maximum length of any list value in the input dictionary d.
    """
    max_len = 0
    for val in d.values():
        if isinstance(val, list):
            max_len = max(max_len, len(val))
    return max_len


def valid_cell_value_excel(input_string):
    for s in input_string:
        if not s.isspace():
            return True

    return False


def empty_row_remover(table_dict):
    rows = table_dict["children"]
    for row in rows[:]:
        remove_row = False

        if not any(valid_cell_value_excel(c["v"]) == True for c in row["children"]):
            remove_row = True

        if remove_row:
            rows.remove(row)

    table_dict["children"] = rows
    return table_dict


def is_empty_row(cells):
    is_empty = True
    for cell in cells:
        if valid_cell_value_excel(cell["v"]):
            is_empty = False
            break
    return is_empty


def generate_rows_list(maximum_cell_count):
    row_list = list()
    for y in range(maximum_cell_count):
        blank_row = initiate_blank_row()
        row_list.append(blank_row)

    return row_list


def merge_advanced_column_data(
    temp_merge_value_column, previous_cell_list, cell_list, merge_value_separator
):
    if not previous_cell_list:
        return cell_list

    for l, new_item in enumerate(cell_list):

        if is_empty_row(cell_list):
            cell_list = copy.deepcopy(previous_cell_list)
        else:
            if not is_empty_row(previous_cell_list):
                if l < len(previous_cell_list) and valid_cell_value_excel(
                    new_item["v"]
                ):
                    prev_v = previous_cell_list[l].get("v", "")
                    existing_v = new_item.get("v", "")
                    cell_list[l]["v"] = f"{prev_v}{merge_value_separator} {existing_v}"

    return cell_list


def generate_table_node(columns, table_range, table_name, multisheet_trigger):
    table_type = "vertical"
    if not table_type == "vertical":
        return {}

    table_dict = dict()

    # Storage for all the columns and its subsequent row list as a list of key val pairs
    column_data_storage = dict()

    temp_previous_column = None
    temp_merge_value_column = None
    # Looping through each column to extract cells
    for i, column in enumerate(columns):
        column["colIndex"] = i
        lookup_code = ""
        field_name = column["colLabel"]
        advance_settings = column.get("advanceSettings")
        if (
            advance_settings
            and advance_settings.get("mergeValue")
            and advance_settings.get("mergeValueSeparator")
        ):
            temp_merge_value_column = column

        if column.get("qualifierValue"):
            lookup_code = field_name
            field_name = column.get("qualifierValue")

        cell_list = extract_cells(column, table_range, multisheet_trigger)

        if (
            temp_merge_value_column
            and temp_previous_column
            and temp_merge_value_column["colIndex"] < column["colIndex"]
        ):
            if temp_merge_value_column.get("qualifierValue") == column.get(
                "qualifierValue"
            ):
                previous_cell_list = column_data_storage.get(field_name, [])
                cell_list = merge_advanced_column_data(
                    temp_merge_value_column,
                    previous_cell_list,
                    cell_list,
                    temp_merge_value_column.get("advanceSettings").get(
                        "mergeValueSeparator"
                    ),
                )

        if cell_list:
            if lookup_code:
                for c in cell_list:
                    c["qualifierParent"] = lookup_code

            column_data_storage[field_name] = cell_list
        temp_previous_column = column

    # print(column_data_storage)

    # Gettting the maximum cell count
    maximum_cell_count = 0
    try:
        maximum_cell_count = max_list_length(column_data_storage)
    except:
        print(traceback.print_exc(0))

    # Creating a list of rows depending on the maximum cell count
    row_list = generate_rows_list(maximum_cell_count)

    for column_name, cell_list in column_data_storage.items():
        """For each cell  index, appending that cell to same index of the row list.
        So, the first cell of a column is appended to the first row
        """

        for c_idx, c in enumerate(cell_list):
            if c.get("v"):
                c["label"] = column_name
                row_list[c_idx]["children"].append(c)

    # Removing empty rows
    row_list = [r for r in row_list if r["children"]]

    # print("Final Row list")
    # print(row_list)

    table_dict["type"] = "table"
    table_dict["children"] = row_list
    table_dict["pos"] = ""
    table_dict["pageId"] = ""

    return table_dict


def convert_to_zero(table_dict):
    rows = table_dict["children"]
    target_labels = [
        "weight",
        "volume",
        "dimension",
        "length",
        "width",
        "height",
        "packagecount",
    ]
    for row_idx, row in enumerate(rows):
        cells = row["children"]
        for cell_idx, cell in enumerate(cells):
            if any(
                target_label in cell["label"].lower() for target_label in target_labels
            ):
                if "uom" not in cell["label"].lower():
                    if cell["v"] == " ":
                        cell["v"] = "0"
                        cells[cell_idx] = cell
        for cell in cells[:]:
            if cell["v"].strip() == "":
                cells.remove(cell)
    return table_dict


def process_excel_table(request_data):
    try:
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)

        # Version = 1.01.07042023
        # @Emon on 07/04/2023 - Initiated the API
        # @Emon on 22/05/2023 - Merge column function fixed - If the cell is null, space is to be cell value

        global DATA_DICTIONARY

        ra_json = request_data["ra_json"]
        d_json = request_data["data_json"]
        messages = list()

        try:
            definitions_list = request_data.get("definitions", [])
            definitions = definitions_list[0] if definitions_list else {}
        except:
            definitions = {}
        try:
            table_definitions = definitions.get("table", [])
            for table_definition_idx, table_definition in enumerate(table_definitions):
                table_uid = table_definition.get("table_unique_id")
                table_name = table_definition.get("table_name")
                target_column = None
                try:
                    table_range = dict()

                    table_model = table_definition["table_definition_data"]["models"]
                    try:
                        table_range["tableEnd"] = table_model["tableEnd"]["cellRange"]
                    except:
                        table_range["tableEnd"] = None
                    table_range["tableStart"] = table_model["tableStart"]["cellRange"]
                    try:
                        if ":" in table_range["tableEnd"]:
                            table_range["tableEnd"] = table_range["tableEnd"].split(
                                ":"
                            )[1]
                    except:
                        pass
                    if (
                        table_range["tableStart"] is not None
                        and ":" in table_range["tableStart"]
                    ):
                        table_range["tableStart"] = table_range["tableStart"].split(
                            ":"
                        )[0]
                except:
                    print(traceback.print_exc())
                    pass
                empty_columns_trigger = False
                try:
                    columns = table_definition["table_definition_data"]["columns"]
                    if not columns:
                        empty_columns_trigger = True
                except:
                    pass

                docs = d_json["nodes"]
                # added by emon on 19/05/2022
                test_document_trigger = None
                try:
                    test_document_trigger = request_data["document_id"]
                except:
                    pass
                try:
                    table_model_name = table_model["type"]
                    if "multishipment" in table_model_name:
                        table_model_name = table_model_name + table_model.get(
                            "multishipmentType"
                        )
                except:
                    print(traceback.print_exc())

                try:
                    multisheet_trigger = False
                    if table_model["type"] == "multishipment":
                        if (
                            table_model.get("multishipmentType")
                            == "Multisheet Multishipment"
                        ) or (
                            table_model.get("multishipmentType")
                            == "Eachsheet Single Shipment"
                        ):
                            multisheet_trigger = dict()
                            multisheet_condition = table_model.get(
                                "sheetNameIdentifierCondition"
                            )
                            if "contain" in multisheet_condition.lower():
                                multisheet_trigger["condition"] = "contains"
                            elif "equal" in multisheet_condition.lower():
                                multisheet_trigger["condition"] = "equals"
                            multisheet_trigger["sheetName"] = table_model.get(
                                "sheetName"
                            )
                except:
                    print(traceback.print_exc())
                    pass

                # Primary loop
                for input_doc_idx, target_doc in enumerate(docs):
                    # Test document trigger handling
                    if (test_document_trigger != None) and (
                        test_document_trigger != target_doc["id"]
                    ):
                        continue

                    nodes = ra_json["nodes"]
                    DATA_DICTIONARY = nodes[input_doc_idx]
                    try:
                        if table_model.get("identifier"):
                            identifier = table_model["identifier"]
                            identifier_value = identifier["cellValue"]
                            if identifier_value:
                                for elem in DATA_DICTIONARY["children"]:
                                    cell_data = elem["cell_data"]

                                    for column, column_cell in cell_data.items():
                                        for row, cell in column_cell.items():
                                            if (
                                                table_model.get("multishipmentType")
                                                != "Singlesheet Multishipment"
                                            ):
                                                if cell["value"] == identifier_value:
                                                    target_column = column
                                                    target_row = row
                                                    break

                                identifier_column = dict()
                                identifier_column["colLabel"] = "identifier"
                                identifier_column["cellRanges"] = list()
                                cell_range = dict()
                                cell_range["sheetName"] = None
                                target_row = remove_alpha(table_range["tableStart"])
                                cell_range["cellRange"] = target_row
                                if target_column:
                                    cell_range["cellRange"] = target_column + target_row
                                identifier_column["cellRanges"].append(cell_range)
                            else:
                                identifier_column = dict()
                                identifier_column["colLabel"] = "identifier"
                                identifier_column["cellRanges"] = list()
                                cell_range = dict()
                                cell_range["sheetName"] = None
                                target_row = remove_alpha(table_range["tableStart"])
                                if (
                                    identifier.get("cellRange")
                                    and ":" in identifier["cellRange"]
                                ):
                                    target_column = identifier["cellRange"].split(":")[
                                        0
                                    ]
                                else:
                                    target_column = remove_digits(
                                        identifier["cellRange"]
                                    )
                                cell_range["cellRange"] = target_column + target_row
                                identifier_column["cellRanges"].append(cell_range)

                            if empty_columns_trigger:
                                columns = list()
                                columns.append(identifier_column)
                            else:
                                columns.insert(0, identifier_column)

                    except:
                        print(traceback.print_exc())
                        pass
                    # This function generates table using table columns
                    try:
                        table_dict = generate_table_node(
                            columns, table_range, table_name, multisheet_trigger
                        )
                        # print("table_dict", table_dict)
                    except:
                        print(traceback.print_exc())
                        pass
                    table_dict = empty_row_remover(table_dict)
                    table_dict = convert_to_zero(table_dict)
                    id_value = ".00" + str(table_definition_idx + 1)
                    table_dict["id"] = target_doc["id"] + id_value
                    table_dict["table_unique_id"] = table_uid
                    table_dict["table_name"] = table_name
                    target_doc["children"].append(table_dict)
        except:
            print(traceback.print_exc())
            pass

        set_redis_data(job_id, "data_json", d_json)
        result = {"job_id": job_id, "messages": messages, "status_code": 200}
        publish("excel_table_process_response", "to_pipeline", result)

    except:
        print(traceback.print_exc())

        set_redis_data(job_id, "data_json", d_json)

        result = {
            "job_id": job_id,
            "status_code": 200,
        }
        publish("excel_table_process_response", "to_pipeline", result)
