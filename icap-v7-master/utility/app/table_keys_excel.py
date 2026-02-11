import re
import traceback

from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

from app.extraction_modules.excel_sub_module import (
    excel_column_range,
)

"""
Same as table keys for pdf but there are speicfic rules.
There are also excel specific rules that is specific to excel filetype only.
"""


data_dictionary = dict()


def get_row_range(worksheet_name):
    global data_dictionary

    for elem in data_dictionary["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]
            maxLength = max(int(k) for v in cell_data.values() for k in v.keys())
            return range(1, maxLength)

    return range(1, 1)


def remove_digits(string):
    return "".join(char for char in string if not char.isdigit())


def remove_alpha(string):
    return "".join(char for char in string if not char.isalpha())


def regex_excel_extractor(key):
    global data_dictionary
    targets = key.get("excelRegexExtractor")
    patterns = targets.get("patterns")
    cell_range_data = targets.get("cellRanges")
    top_anchor = None
    bottom_anchor = None
    try:
        worksheet_name = cell_range_data[0].get("sheetName")
        if not worksheet_name:
            worksheet_name = cell_range_data[1].get("sheetName")
    except:
        print(traceback.print_exc())

    if not worksheet_name:
        sheet_number = cell_range_data[0].get("sheetNumber")
        if not sheet_number:
            sheet_number = cell_range_data[1].get("sheetNumber")

        if sheet_number:
            worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = data_dictionary["children"][0]["title"]

    try:
        top_anchor = cell_range_data[0].get("cellRange")
        top_anchor_value = cell_range_data[0].get("cellValue")
        if top_anchor:
            top_anchor = remove_alpha(top_anchor)
        bottom_anchor = cell_range_data[1].get("cellRange")
        bottom_anchor_value = cell_range_data[1].get("cellValue")
        if bottom_anchor:
            bottom_anchor = remove_alpha(bottom_anchor)
    except:
        print(traceback.print_exc())

    if not top_anchor or not bottom_anchor:
        for elem in data_dictionary["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                for column_name, column_data in cell_data.items():
                    for row, cell in column_data.items():
                        cell_value = cell.get("value")
                        if cell_value == top_anchor_value:
                            top_anchor = row
                        if cell_value == bottom_anchor_value:
                            bottom_anchor = row

    if not top_anchor:
        top_anchor = 1
    if not bottom_anchor:
        bottom_anchor = get_row_range(worksheet_name)[-1]

    # List to store matching IDs
    matching_ids = dict()

    # Compile the patterns for efficiency
    compiled_patterns = [re.compile(pattern) for pattern in patterns]
    for elem in data_dictionary["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]

    for column, rows in cell_data.items():
        for row_key, row_data in rows.items():
            if (int(row_key) > int(top_anchor)) and (int(row_key) < int(bottom_anchor)):
                value = row_data.get("value", "")
                id = row_data.get("id", "")
                # Check if the value matches any of the patterns
                if not isinstance(value, str):
                    value = str(value)
                if any(pattern.match(value) for pattern in compiled_patterns):
                    matching_ids[id] = value

    extracted_keys = list()
    for match_id, value in matching_ids.items():
        output = dict()
        output["text"] = value
        output["co_ordinates"] = match_id.split(".")[-1]
        output["cellRange"] = match_id.split(".")[-1]
        output["worksheet_name"] = worksheet_name
        output["title"] = "excelRegexExtractor"
        output["pos"] = ""
        output["pageId"] = ""
        extracted_keys.append(output)

    return extracted_keys


def extract_cell_value(key):
    global data_dictionary

    """Extracts values on specific cell ranges of worksheets"""
    type_data = key.get("typeData")
    cell_range_data = type_data.get("cellRangeItems")
    worksheet_name = cell_range_data[0].get("sheetName")
    co_ordinates = cell_range_data[0].get("cellRange")
    multi_range = True if ":" in co_ordinates else False
    if not worksheet_name:
        sheet_number = cell_range_data[0].get("sheetNumber")
        if sheet_number:
            worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = data_dictionary["children"][0]["title"]
    if not multi_range:
        """If only single cell reference selected"""
        column = remove_digits(co_ordinates)
        row = remove_alpha(co_ordinates)
        for elem in data_dictionary["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                try:
                    target_cell = cell_data.get(column).get(row)
                    # print(target_cell, column, row)
                    if target_cell:
                        value = target_cell.get("value")
                        value = str(value)
                        if value[0] == "=":
                            return None, None, None
                        return value, co_ordinates, worksheet_name
                    else:
                        return None, None, None
                except:
                    print(traceback.print_exc())
                    return None
    else:
        """If a cell range is selected. A block is returned with spaces and newlines"""
        start_column_data = co_ordinates.split(":")[0]
        end_column_data = co_ordinates.split(":")[1]

        start_column = remove_digits(start_column_data)
        start_column_start_row = remove_alpha(start_column_data)

        end_column = remove_digits(end_column_data)
        end_column_end_row = remove_alpha(end_column_data)

        column_range = excel_column_range(start_column, end_column)

        row_range = range(int(start_column_start_row), int(end_column_end_row) + 1)

        block_text_list = list()
        for elem in data_dictionary["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                for row in row_range:
                    line_text_list = list()
                    for column in column_range:
                        try:
                            target_cell = cell_data.get(column).get(str(row))
                            cell_value = target_cell.get("value")
                            cell_value = str(cell_value)
                            if cell_value:
                                if cell_value[0] == "=":
                                    return None
                                elif cell_value == "#VALUE!":
                                    return None
                            if cell_value:
                                line_text_list.append(str(cell_value))
                        except:
                            continue
                    if line_text_list:
                        line_text = " ".join(line_text_list)
                        block_text_list.append(line_text.strip())

        block_text = "\n".join(block_text_list)
        return block_text, co_ordinates, worksheet_name
    return None, None, None


def filter_cell_column(data, start_key):
    try:
        filtered_data = {k: v for k, v in data.items() if int(k) >= int(start_key)}
        last_key = max(filtered_data.keys(), key=int) if filtered_data else None
        return last_key
    except:
        return None


def extract_single_cell_coordinates(key):
    global data_dictionary
    type_data = key.get("typeData")
    single_extractor_excel = type_data.get("singleColumnExtractorExcel", {})
    column_start_cell = single_extractor_excel.get("columnStartCell", {})
    column_end_cell = single_extractor_excel.get("columnEndCell", {})
    worksheet_name = column_start_cell.get("sheetName", None)
    start_cell_range = column_start_cell.get("cellRange", None)
    end_cell_range = column_end_cell.get("cellRange", None)
    if not worksheet_name:
        sheet_number = column_start_cell.get("sheetNumber")
        if sheet_number:
            worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = data_dictionary["children"][0]["title"]
    if start_cell_range and end_cell_range:
        co_ordinates = f"{start_cell_range}:{end_cell_range}"
        return worksheet_name, co_ordinates
    co_ordinates = start_cell_range
    nodes = data_dictionary["children"]
    for node in nodes:
        if node["title"] == worksheet_name:
            if ":" not in start_cell_range:
                str_to_list = [i for i in start_cell_range]
                column_name = str_to_list[0]
                start_row = int(str_to_list[1])
                last_key = filter_cell_column(node["cell_data"][column_name], start_row)
                if last_key:
                    co_ordinates = f"{start_cell_range}:{column_name}{last_key}"
    return worksheet_name, co_ordinates


def extract_cell_value_multisheet(key, multisheet_trigger):
    global data_dictionary

    """Extracts values on specific cell ranges of worksheets"""
    type_data = key.get("typeData")
    if key.get("type") == "singleColumnExcel":
        worksheet_name, co_ordinates = extract_single_cell_coordinates(key)
    else:
        cell_range_data = type_data.get("cellRangeItems")
        worksheet_name = cell_range_data[0].get("sheetName")
        co_ordinates = cell_range_data[0].get("cellRange")
        if not worksheet_name:
            sheet_number = cell_range_data[0].get("sheetNumber")
            if sheet_number:
                worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
            else:
                worksheet_name = data_dictionary["children"][0]["title"]
    multi_range = True if ":" in co_ordinates else False
    key_list = list()
    if not multi_range:
        """If only single cell reference selected"""
        column = remove_digits(co_ordinates)
        row = remove_alpha(co_ordinates)
        for elem in data_dictionary["children"]:
            extract_sheet = False
            if multisheet_trigger["condition"] == "contains":
                if multisheet_trigger["sheetName"].lower() in elem["title"].lower():
                    extract_sheet = True
            elif multisheet_trigger["condition"] == "equals":
                if multisheet_trigger["sheetName"].lower() == elem["title"].lower():
                    extract_sheet = True
            if extract_sheet:
                cell_data = elem["cell_data"]
                try:
                    target_cell = cell_data.get(column).get(row)
                    # print(target_cell, column, row)
                    if target_cell:
                        value = target_cell.get("value")
                        value = str(value)
                        if value[0] == "=":
                            pass
                        else:
                            key_dict = dict()
                            key_dict["value"] = value
                            key_dict["co_ordinates"] = co_ordinates
                            key_dict["worksheet_name"] = elem["title"]
                            key_list.append(key_dict)
                except:
                    print(traceback.print_exc())
                    return None
    else:
        """If a cell range is selected. A block is returned with spaces and newlines"""
        start_column_data = co_ordinates.split(":")[0]
        end_column_data = co_ordinates.split(":")[1]

        start_column = remove_digits(start_column_data)
        start_column_start_row = remove_alpha(start_column_data)

        end_column = remove_digits(end_column_data)
        end_column_end_row = remove_alpha(end_column_data)

        column_range = excel_column_range(start_column, end_column)

        row_range = range(int(start_column_start_row), int(end_column_end_row) + 1)

        for elem in data_dictionary["children"]:
            extract_sheet = False
            if multisheet_trigger["condition"] == "contains":
                if multisheet_trigger["sheetName"].lower() in elem["title"].lower():
                    extract_sheet = True
            elif multisheet_trigger["condition"] == "equals":
                if multisheet_trigger["sheetName"].lower() == elem["title"].lower():
                    extract_sheet = True
            if extract_sheet:
                cell_data = elem["cell_data"]
                block_text_list = list()
                for row in row_range:
                    line_text_list = list()

                    for column in column_range:
                        try:
                            target_cell = cell_data.get(column).get(str(row))
                            cell_value = target_cell.get("value")
                            cell_value = str(cell_value)
                            if cell_value:
                                if cell_value[0] == "=":
                                    pass
                                elif cell_value == "#VALUE!":
                                    pass
                                else:
                                    line_text_list.append(str(cell_value))
                        except:
                            continue
                    if line_text_list:
                        line_text = " ".join(line_text_list)
                        block_text_list.append(line_text.strip())
                    block_text = "\n".join(block_text_list)
                    key_dict = dict()
                    key_dict["value"] = (
                        block_text_list
                        if key.get("type") == "singleColumnExcel"
                        else block_text
                    )
                    key_dict["co_ordinates"] = co_ordinates
                    key_dict["worksheet_name"] = elem["title"]
                key_list.append(key_dict)
    return key_list


def single_cell_adder(fieldname, target_doc, value, co_ordinates, worksheet_name, key):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)
                first_row = tabledata["children"][0]

            cells = first_row["children"]
            cell = dict()
            if (key.get("qualifierValue") != "") and (
                key.get("qualifierValue") != None
            ):
                cell["qualifierParent"] = key.get("keyLabel")
            cell["type"] = "cell"
            cell["label"] = fieldname
            cell["v"] = value
            cell["co_ordinates"] = co_ordinates
            cell["cellRange"] = co_ordinates
            cell["worksheet_name"] = worksheet_name
            cell["table_key_generated"] = True
            cell["pos"] = ""
            cell["pageId"] = ""
            cells.append(cell)
            first_row["children"] = cells
            tabledata["children"][0] = first_row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())

    return target_doc


def static_cell_adder(fieldname, target_doc, key):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)
                first_row = tabledata["children"][0]

            cells = first_row["children"]
            cell = dict()
            if (key.get("qualifierValue") != "") and (
                key.get("qualifierValue") != None
            ):
                cell["qualifierParent"] = key.get("keyLabel")
            cell["type"] = "cell"
            cell["label"] = fieldname
            cell["v"] = key["shape"]
            cell["pos"] = ""
            cell["table_key_generated"] = True
            cell["pageId"] = ""
            cell["static_value"] = True
            cells.append(cell)
            first_row["children"] = cells
            tabledata["children"][0] = first_row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())

    return target_doc


def static_all_row_or_total_adder(fieldname, target_doc, key, all_row_flag=False):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)

            for row_index, row in enumerate(tabledata["children"]):
                cells = row["children"]
                cell = dict()
                if (key.get("qualifierValue") != "") and (
                    key.get("qualifierValue") != None
                ):
                    cell["qualifierParent"] = key.get("keyLabel")
                cell["type"] = "cell"
                cell["label"] = fieldname
                if all_row_flag:
                    cell["v"] = key["shape"]
                else:
                    if row_index == 0:
                        cell["v"] = key["shape"]
                    else:
                        cell["v"] = "0"
                cell["pos"] = ""
                cell["pageId"] = ""
                cell["table_key_generated"] = True
                cell["static_value"] = True
                cells.append(cell)
                row["children"] = cells
                tabledata["children"][row_index] = row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())
    return target_doc


def eachsheet_shipment_static_cell_adder(fieldname, target_doc, key):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)
            table_id = None
            prev_table_id = None
            for row_index, row in enumerate(tabledata["children"]):
                cells = row["children"]

                for cell in cells:
                    if cell.get("table_id") != prev_table_id:
                        table_id = str(cell.get("table_id"))
                        break
                cell = dict()
                if (key.get("qualifierValue") != "") and (
                    key.get("qualifierValue") != None
                ):
                    cell["qualifierParent"] = key.get("keyLabel")
                cell["type"] = "cell"
                cell["label"] = fieldname
                if not prev_table_id or table_id != prev_table_id:
                    cell["v"] = key["shape"]
                    cell["pos"] = ""
                    cell["pageId"] = ""
                    cell["table_key_generated"] = True
                    cell["static_value"] = True
                    cells.append(cell)
                row["children"] = cells
                prev_table_id = table_id
                tabledata["children"][row_index] = row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())
    return target_doc


def remove_empty_row_values_if_exists(target_doc: dict) -> dict:
    """
    Removes rows with empty 'v' lists from tables in the given document.

    This function processes the 'children' of a document to find elements of type 'table',
    and removes any row where the value of 'v' is an empty list. After removing such rows,
    it also removes any tables that have no remaining rows.
    """
    input_target_doc = target_doc.copy()
    docs = input_target_doc["children"]
    try:
        for doc in docs:
            if doc["type"] == "table":
                tables = doc["children"]
                for table in tables:
                    rows = table["children"]
                    for row in rows[:]:
                        if isinstance(row.get("v"), list) and len(row.get("v")) == 0:
                            rows.remove(row)
                # Second pass to check if table has empty rows
                new_table = [
                    item
                    for item in doc["children"]
                    if len(item.get("children", [])) > 0
                ]
                doc["children"] = new_table
    except Exception as e:
        print(traceback.format_exc())
    return input_target_doc


def multi_shipment_adder(
    fieldname, target_doc, key_list, key, all_row_copy, total_count_keys
):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)
            if (fieldname.lower() not in all_row_copy) and (
                fieldname.lower() not in total_count_keys
            ):
                for key_idx, key_dict in enumerate(key_list):
                    value = key_dict.get("value")
                    co_ordinates = key_dict["co_ordinates"]
                    worksheet_name = key_dict["worksheet_name"]

                    target_row = None

                    for row_idx, row in enumerate(tabledata["children"]):
                        cells = row["children"]

                        for cell in cells:
                            if cell.get("table_id") == key_idx:
                                target_row = row_idx
                                break
                        if target_row != None:
                            break

                    if target_row == None:
                        blank_row = initiate_blank_row()
                        tabledata["children"].append(blank_row)
                        target_row = len(tabledata["children"]) - 1
                    if value and key_idx == 0:
                        target_row = 0
                    cells = tabledata["children"][target_row]["children"]
                    cell = dict()
                    if (key.get("qualifierValue") != "") and (
                        key.get("qualifierValue") != None
                    ):
                        cell["qualifierParent"] = key.get("keyLabel")
                    cell["type"] = "cell"
                    cell["label"] = fieldname
                    cell["v"] = value
                    cell["co_ordinates"] = co_ordinates
                    cell["cellRange"] = co_ordinates
                    cell["worksheet_name"] = worksheet_name
                    cell["table_key_generated"] = True
                    cell["pos"] = ""
                    cell["pageId"] = ""
                    cell["table_id"] = key_idx
                    cells.append(cell)
                    tabledata["children"][target_row]["children"] = cells
            elif fieldname.lower() in all_row_copy:
                for key_idx, key_dict in enumerate(key_list):
                    value = key_dict.get("value")
                    co_ordinates = key_dict["co_ordinates"]
                    worksheet_name = key_dict["worksheet_name"]
                    for row_count, row in enumerate(tabledata["children"]):
                        cells = row["children"]
                        correct_row = False
                        for cell in cells:
                            if cell.get("table_id") == key_idx:
                                correct_row = True
                                break
                        if correct_row:
                            cell = dict()
                            if (key.get("qualifierValue") != "") and (
                                key.get("qualifierValue") != None
                            ):
                                cell["qualifierParent"] = key.get("keyLabel")
                            cell["type"] = "cell"
                            cell["label"] = fieldname
                            cell["v"] = value
                            cell["co_ordinates"] = co_ordinates
                            cell["cellRange"] = co_ordinates
                            cell["worksheet_name"] = worksheet_name
                            cell["table_key_generated"] = True
                            cell["pos"] = ""
                            cell["pageId"] = ""
                            cell["table_id"] = key_idx
                            cells.append(cell)
                            row["children"] = cells
                            tabledata["children"][row_count] = row
            elif fieldname.lower() in total_count_keys:
                for key_idx, key_dict in enumerate(key_list):
                    value = key_dict.get("value")
                    co_ordinates = key_dict["co_ordinates"]
                    worksheet_name = key_dict["worksheet_name"]
                    first_time_flag = True
                    for row_count, row in enumerate(tabledata["children"]):
                        cells = row["children"]
                        correct_row = False
                        for cell in cells:
                            if cell.get("table_id") == key_idx:
                                correct_row = True
                                break
                        if correct_row:
                            cell = dict()
                            if (key.get("qualifierValue") != "") and (
                                key.get("qualifierValue") != None
                            ):
                                cell["qualifierParent"] = key.get("keyLabel")
                            cell["type"] = "cell"
                            cell["label"] = fieldname
                            if first_time_flag:
                                cell["v"] = value
                                first_time_flag = False
                            else:
                                cell["v"] = "0"
                            cell["co_ordinates"] = co_ordinates
                            cell["cellRange"] = co_ordinates
                            cell["worksheet_name"] = worksheet_name
                            cell["table_key_generated"] = True
                            cell["pos"] = ""
                            cell["pageId"] = ""
                            cell["table_id"] = key_idx
                            cells.append(cell)
                            row["children"] = cells
                            tabledata["children"][row_count] = row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())

    target_doc = remove_empty_row_values_if_exists(target_doc)
    return target_doc


def all_row_copier_or_total_count_adder(
    fieldname,
    target_doc,
    value,
    co_ordinates,
    worksheet_name,
    key,
    all_row_copy_flag=False,
):
    try:
        for index, tabledata in enumerate(target_doc["children"]):
            try:
                first_row = tabledata["children"][0]
            except:
                blank_row = initiate_blank_row()
                tabledata["children"].append(blank_row)

            for row_count, row in enumerate(tabledata["children"]):
                cells = row["children"]
                cell = dict()
                if (key.get("qualifierValue") != "") and (
                    key.get("qualifierValue") != None
                ):
                    cell["qualifierParent"] = key.get("keyLabel")
                cell["type"] = "cell"
                cell["label"] = fieldname
                if all_row_copy_flag:
                    cell["v"] = value
                else:
                    if row_count == 0:
                        cell["v"] = value
                    else:
                        cell["v"] = "0"
                cell["co_ordinates"] = co_ordinates
                cell["cellRange"] = co_ordinates
                cell["worksheet_name"] = worksheet_name
                cell["table_key_generated"] = True
                cell["pos"] = ""
                cell["pageId"] = ""
                cells.append(cell)
                row["children"] = cells
                tabledata["children"][row_count] = row
            target_doc["children"][index] = tabledata
    except:
        print(traceback.print_exc())

    return target_doc


def initiate_blank_row():
    output_dict = dict()
    output_dict["pos"] = ""
    output_dict["type"] = "row"
    output_dict["pageId"] = ""
    output_dict["STATUS"] = 0
    output_dict["children"] = []
    return output_dict


def excel_table_keys(request_data):
    global data_dictionary
    all_rows_copy = [
        "goodsdescription",
        "requirestemperaturecontrol",
        "commoditycode",
        "requiredmaximum",
        "requiredminimum",
        "temperatureuom",
        "grossweightuom",
        "netweightuom",
    ]
    total_count_keys = [
        "grossweight",
        "volume",
        "packagecount",
        "netweight",
        "innerpackagecount",
    ]
    try:
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)

        d_json = request_data["data_json"]
        ra_json = request_data["ra_json"]
        nodes = ra_json["nodes"]
        messages = []

        definitions_list = request_data.get("definitions", [])
        definitions = definitions_list[0] if definitions_list else {}
        table_definitions = definitions.get("table", {})

        docs = d_json["nodes"]
        test_document_trigger = None
        test_document_trigger = request_data.get("document_id", None)

        for table_definition in table_definitions:
            query_key_list = table_definition.get("table_definition_data", {}).get(
                "keyItems", []
            )
            try:
                table_model = table_definition["table_definition_data"]["models"]
                table_model_name = table_model["type"]
                multi_shipment_type = table_model.get("multishipmentType")
                if "multishipment".lower() in table_model_name:
                    table_model_name = "multishipment"
            except:
                table_model_name = None

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
                        multisheet_trigger["sheetName"] = table_model.get("sheetName")
            except:
                print(traceback.print_exc())
                pass

            for input_doc_idx, target_doc in enumerate(docs):
                # Test document trigger handling
                if test_document_trigger and test_document_trigger != target_doc["id"]:
                    continue
                data_dictionary = nodes[input_doc_idx]
                for key in query_key_list:
                    field_name = (
                        key.get("qualifierValue")
                        if key.get("qualifierValue")
                        else key.get("keyLabel")
                    )

                    if key.get("type") == "static":
                        try:
                            if (field_name.lower() in all_rows_copy) or (
                                table_model_name == "multishipment"
                                and "Eachsheet" not in multi_shipment_type
                            ):
                                target_doc = static_all_row_or_total_adder(
                                    field_name, target_doc, key, True
                                )
                            elif field_name.lower() in total_count_keys:
                                target_doc = static_all_row_or_total_adder(
                                    field_name, target_doc, key
                                )
                            elif "Eachsheet" in multi_shipment_type:
                                eachsheet_shipment_static_cell_adder(
                                    field_name, target_doc, key
                                )
                            else:
                                target_doc = static_cell_adder(
                                    field_name, target_doc, key
                                )
                        except:
                            print(traceback.print_exc())
                    elif key.get("type") == "excelRegexExtractor":
                        try:
                            extracted_keys = regex_excel_extractor(key)
                            for extracted_key in extracted_keys:
                                value = extracted_key.get("text")
                                co_ordinates = extracted_key["co_ordinates"]
                                worksheet_name = extracted_key["worksheet_name"]
                                if field_name.lower() in all_rows_copy:
                                    target_doc = all_row_copier_or_total_count_adder(
                                        field_name,
                                        target_doc,
                                        value,
                                        co_ordinates,
                                        worksheet_name,
                                        key,
                                        True,
                                    )
                                elif field_name.lower() in total_count_keys:
                                    target_doc = all_row_copier_or_total_count_adder(
                                        field_name,
                                        target_doc,
                                        value,
                                        co_ordinates,
                                        worksheet_name,
                                        key,
                                    )
                                else:
                                    target_doc = single_cell_adder(
                                        field_name,
                                        target_doc,
                                        value,
                                        co_ordinates,
                                        worksheet_name,
                                        key,
                                    )
                        except:
                            print(traceback.print_exc())
                    else:
                        try:
                            if not multisheet_trigger:
                                (
                                    value,
                                    co_ordinates,
                                    worksheet_name,
                                ) = extract_cell_value(key)
                                if value:
                                    if (field_name.lower() in all_rows_copy) or (
                                        table_model_name == "multishipment"
                                    ):
                                        target_doc = (
                                            all_row_copier_or_total_count_adder(
                                                field_name,
                                                target_doc,
                                                value,
                                                co_ordinates,
                                                worksheet_name,
                                                key,
                                                True,
                                            )
                                        )
                                    elif field_name.lower() in total_count_keys:
                                        target_doc = (
                                            all_row_copier_or_total_count_adder(
                                                field_name,
                                                target_doc,
                                                value,
                                                co_ordinates,
                                                worksheet_name,
                                                key,
                                            )
                                        )
                                    else:
                                        target_doc = single_cell_adder(
                                            field_name,
                                            target_doc,
                                            value,
                                            co_ordinates,
                                            worksheet_name,
                                            key,
                                        )
                            else:
                                if multisheet_trigger:
                                    key_list = extract_cell_value_multisheet(
                                        key, multisheet_trigger
                                    )
                                    if key_list:
                                        target_doc = multi_shipment_adder(
                                            field_name,
                                            target_doc,
                                            key_list,
                                            key,
                                            all_rows_copy,
                                            total_count_keys,
                                        )
                        except:
                            print(traceback.print_exc())
                pass
        set_redis_data(job_id, "data_json", d_json)
        result = {"job_id": job_id, "messages": messages, "status_code": 200}
        publish("excel_table_keys_process_response", "to_pipeline", result)

    except:
        print(traceback.print_exc())

        set_redis_data(job_id, "data_json", d_json)

        result = {
            "job_id": job_id,
            "messages": messages,
            "status_code": 200,
        }
        publish("excel_table_keys_process_response", "to_pipeline", result)
