"""
Excel Data Extraction Script
=============================

Purpose:
--------
This script processes JSON data to extract and manipulate values from Excel worksheets based on specified keys and settings. It provides functionality for extracting single cells, cell ranges, columns, and applying regex patterns to Excel data.

Functions:
----------
1. **regex_excel_extractor(key)**:
   Extracts values from an Excel sheet using regex patterns defined in the key's settings.
   - **Parameters**:
     - `key` (dict): Contains patterns and cell range data for regex extraction.
   - **Returns**:
     - A list of dictionaries containing extracted values and their metadata.

2. **get_row_range(worksheet_name)**:
   Determines the row range for a given worksheet.
   - **Parameters**:
     - `worksheet_name` (str): Name of the worksheet.
   - **Returns**:
     - A range object representing the rows in the worksheet.

3. **excel_column_range(start_col, end_col)**:
   Converts column names to numerical ranges and returns the corresponding column names between the start and end columns.
   - **Parameters**:
     - `start_col` (str): Starting column name.
     - `end_col` (str): Ending column name.
   - **Returns**:
     - A list of column names in the specified range.

4. **remove_digits(string)**:
   Removes all digits from a given string.
   - **Parameters**:
     - `string` (str): Input string.
   - **Returns**:
     - The string without digits.

5. **remove_alpha(string)**:
   Removes all alphabetic characters from a given string.
   - **Parameters**:
     - `string` (str): Input string.
   - **Returns**:
     - The string without alphabetic characters.

6. **extract_cell_value(key)**:
   Extracts a single cell value or a range of values from an Excel worksheet.
   - **Parameters**:
     - `key` (dict): Contains cell range information.
   - **Returns**:
     - A tuple of the extracted value, cell coordinates, and worksheet name.

7. **generate_cell_block(key)**:
   Creates a dictionary for a cell block based on extracted data.
   - **Parameters**:
     - `key` (dict): Contains cell range information.
   - **Returns**:
     - A dictionary with cell data.

8. **get_max_row(column_name, worksheet_name)**:
   Finds the maximum row number in a given column of a worksheet.
   - **Parameters**:
     - `column_name` (str): Column name.
     - `worksheet_name` (str): Worksheet name.
   - **Returns**:
     - The maximum row number.

9. **extract_cells_from_column(worksheet_name, column_range, start_row, end_row)**:
   Extracts cell values from a specific column range and rows.
   - **Parameters**:
     - `worksheet_name` (str): Worksheet name.
     - `column_range` (list): List of column names.
     - `start_row` (int): Starting row number.
     - `end_row` (int): Ending row number.
   - **Returns**:
     - A list of dictionaries containing extracted cell data.

10. **excel_single_column_extractor(key)**:
    Extracts data from a single column in a worksheet based on a specified range.
    - **Parameters**:
      - `key` (dict): Contains column range data.
    - **Returns**:
      - A list of dictionaries with extracted column data.

11. **single_column_excel(key)**:
    Processes single column data and formats it into a structured output.
    - **Parameters**:
      - `key` (dict): Contains settings for extracting single column data.
    - **Returns**:
      - A list of dictionaries with formatted single column data.

12. **excel_extraction_request(query_key_list, request_data, input_doc_idx, messages)**:
    The central function for handling Excel data extraction requests.
    - **Parameters**:
      - `query_key_list` (list): List of keys specifying data extraction settings.
      - `request_data` (dict): Contains the full document data.
      - `input_doc_idx` (int): Index of the document to process.
      - `messages` (list): List of messages for status updates.
    - **Returns**:
      - A list of extracted key-value dictionaries and updated messages.

Key Features:
-------------
- **Flexible Extraction**:
  Supports single cell, cell range, column, and regex-based data extraction.

- **Data Cleaning**:
  Removes duplicates and applies grouping where required.

- **Error Handling**:
  Uses `try-except` blocks to ensure robust execution and logs errors via `traceback`.

- **Customizable Settings**:
  Allows advanced settings such as merging multiple values with separators and applying regex patterns.

Usage:
------
1. Import the script and call the `excel_extraction_request()` function with appropriate inputs.
2. Ensure the input JSON contains nodes with cell data and the required keys for extraction.

Example:
--------
```python
results, messages = excel_extraction_request(query_key_list, request_data, input_doc_idx, messages)
print(results)
"""

import re
import traceback

from app.key_central.key_module_central import remove_duplicates

data_dictionary = None


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


def get_row_range(worksheet_name):
    global data_dictionary

    for elem in data_dictionary["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]
            maxLength = max(int(k) for v in cell_data.values() for k in v.keys())
            return range(1, maxLength)

    return range(1, 1)


def excel_column_range(start_col, end_col):
    start_num = 0
    end_num = 0

    # convert start column name to column number
    """
    This loop iterates over each character in the start_col string and converts it to a column number.
    The loop uses the ord() function to get the Unicode code point of the character, subtracts
    the code point of 'A' (which is 65), adds 1 to convert from 0-based indexing to 1-based indexing,
    and multiplies the result by 26 to shift the previous column to the left by one place.
    The loop updates the start_num variable with the cumulative column number."""

    for i in range(len(start_col)):
        start_num = start_num * 26 + (ord(start_col[i]) - ord("A") + 1)

    # convert end column name to column number
    for i in range(len(end_col)):
        end_num = end_num * 26 + (ord(end_col[i]) - ord("A") + 1)

    # create list of column names between start and end
    result = []

    """
    The loop iterates over a range of numbers from start_num to end_num + 1, inclusive.
    This means that if start_num is 1 and end_num is 3, the loop will iterate over the numbers 1, 2, and 3.
    For each number i in the range, an empty string col_name is created. This string will eventually be
    filled with the letters of the column name.
    A while loop is used to convert the number i to a column name.
    The while loop will continue until i is equal to 0.
    Inside the while loop, the variable index is calculated as (i - 1) % 26.
    This gives the index of the letter in the alphabet that corresponds to the current
    digit of the column name. For example, if i is 1, then index is 0, which corresponds to the letter 'A'.
    The letter corresponding to the index is then added to the beginning of col_name using
    chr(index + ord('A')) + col_name. The chr() function is used to convert the index to a character,
    and the + operator is used to concatenate the character to the beginning of col_name.
    The variable i is then updated to (i - 1) // 26. This shifts the focus to the next digit of the column name.
    For example, if i is 27, then after the first iteration of the loop i becomes 1, and the loop will
    continue until i is equal to 0.
    After the while loop completes, the resulting col_name is appended to the result
    list using result.append(col_name).
    Finally, when the loop completes, the result list is returned. It contains all the column
        
    """

    for i in range(start_num, end_num + 1):
        col_name = ""
        while i > 0:
            index = (i - 1) % 26
            col_name = chr(index + ord("A")) + col_name
            i = (i - 1) // 26
        result.append(col_name)

    return result


def remove_digits(string):
    return "".join(char for char in string if not char.isdigit())


def remove_alpha(string):
    return "".join(char for char in string if not char.isalpha())


def extract_cell_value(key):
    global data_dictionary
    value = ""
    """Extracts values on specific cell ranges of worksheets"""
    multi_range = None
    type_data = key.get("typeData")
    cell_range_data = type_data.get("cellRangeItems")
    worksheet_name = cell_range_data[0].get("sheetName")
    if not worksheet_name:
        sheet_number = cell_range_data[0].get("sheetNumber")
        if sheet_number:
            worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = data_dictionary["children"][0]["title"]
    co_ordinates = cell_range_data[0].get("cellRange")
    if ":" in co_ordinates:
        multi_range = True
    if not multi_range:
        """If only single cell reference selected"""
        column = remove_digits(co_ordinates)
        row = remove_alpha(co_ordinates)
        for elem in data_dictionary["children"]:
            if elem["title"] == worksheet_name:
                cell_data = elem["cell_data"]
                try:
                    target_cell = cell_data.get(column).get(row)
                    # print("94",target_cell, column, row)
                    if not target_cell:
                        return None, None, None
                    value = target_cell.get("value")
                    value = str(value)
                    if value[0] == "=":
                        return None
                    return value, co_ordinates, worksheet_name
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
                        if len(line_text_list) > 1:
                            if all(x == " " for x in line_text_list):
                                value = " "
                            else:
                                value = value.strip()
                        block_text_list.append(line_text.strip())

        block_text = "\n".join(block_text_list)
        return block_text, co_ordinates, worksheet_name
    return None, None, None


def generate_cell_block(key, merge=False):
    """Get cell data"""
    output = dict()
    value = ""
    title = "excel_cell"
    value, co_ordinates, worksheet_name = extract_cell_value(key)
    if merge:
        if not value:
            value = ""
        output["text"] = value.strip()
        output["co_ordinates"] = co_ordinates
        output["cellRange"] = co_ordinates
        output["worksheet_name"] = worksheet_name
        output["title"] = title
        output["pos"] = ""
        output["pageId"] = ""
    elif value:
        output["text"] = value.strip()
        output["co_ordinates"] = co_ordinates
        output["cellRange"] = co_ordinates
        output["worksheet_name"] = worksheet_name
        output["title"] = title
        output["pos"] = ""
        output["pageId"] = ""
    return output


def get_max_row(column_name, worksheet_name):
    global data_dictionary
    for elem in data_dictionary["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]
            column = cell_data.get(column_name)
            rows = [int(r) for r in column.keys()]
            return max(rows)

    return 0


def extract_cells_from_column(worksheet_name, column_range, start_row, end_row):
    global data_dictionary
    title = "excel_cell"
    output_list = list()
    value = ""

    if end_row:
        row_range = range(int(start_row), int(end_row) + 1)
    else:
        row_range = range(
            int(start_row), get_max_row(column_range[0], worksheet_name) + 1
        )

    for elem in data_dictionary["children"]:
        if elem["title"] == worksheet_name:
            cell_data = elem["cell_data"]
            for row in row_range:
                cell_text_list = list()
                for c in column_range:
                    column = cell_data.get(c)
                    value = None
                    try:
                        target_cell = column.get(str(row))
                        cell_value = target_cell.get("value")
                        cell_value = str(cell_value)
                        if cell_value:
                            if cell_value[0] == "=":
                                cell_value = " "
                            elif cell_value == "#VALUE!":
                                cell_value = " "
                        if cell_value:
                            cell_text_list.append(str(cell_value))
                    except:
                        value = " "
                if cell_text_list:
                    value = " ".join(cell_text_list)
                    try:
                        if len(cell_text_list > 1):
                            if all(x == " " for x in cell_text_list):
                                value = " "
                            else:
                                value = value.strip()
                    except:
                        pass

                if value:
                    output = dict()
                    output["text"] = value.strip()
                    output["co_ordinates"] = ""
                    output["cellRange"] = ""
                    output["worksheet_name"] = worksheet_name
                    output["title"] = title
                    output["pos"] = ""
                    output["pageId"] = ""
                    output_list.append(output)

    return output_list


def excel_single_column_extractor(key):
    output_list = list()

    """Extracts values on specific cell ranges of worksheets"""
    type_data = key.get("typeData")
    all_data = type_data.get("singleColumnExtractorExcel")
    column_start_cell_data = all_data.get("columnStartCell")
    column_end_cell_data = all_data.get("columnEndCell")
    worksheet_name = column_start_cell_data.get("sheetName")
    if not worksheet_name:
        sheet_number = column_start_cell_data.get("sheetNumber")
        if sheet_number:
            worksheet_name = data_dictionary["children"][sheet_number - 1]["title"]
        else:
            worksheet_name = data_dictionary["children"][0]["title"]

    if ":" in column_start_cell_data["cellRange"]:
        first_cell_start_column_data = column_start_cell_data["cellRange"].split(":")[0]
        start_column = remove_digits(first_cell_start_column_data)
        start_row = int(remove_alpha(first_cell_start_column_data))

        first_cell_end_column_data = column_start_cell_data["cellRange"].split(":")[1]
        end_column = remove_digits(first_cell_end_column_data)
        # print(end_column, start_column)
        end_row = None
        if column_end_cell_data.get("cellRange"):
            end_row = int(remove_alpha(column_end_cell_data["cellRange"].split(":")[0]))

        column_range = excel_column_range(start_column, end_column)
        output_list = extract_cells_from_column(
            worksheet_name, column_range, start_row, end_row
        )

    else:
        first_cell_start_column_data = column_start_cell_data["cellRange"].split(":")[0]
        start_column = remove_digits(first_cell_start_column_data)
        start_row = int(remove_alpha(first_cell_start_column_data))

        end_column = start_column

        end_row = None
        if column_end_cell_data.get("cellRange"):
            end_row = int(remove_alpha(column_end_cell_data["cellRange"].split(":")[0]))

        column_range = excel_column_range(start_column, end_column)

        output_list = extract_cells_from_column(
            worksheet_name, column_range, start_row, end_row
        )

    return output_list


def single_column_excel(key):
    output_list = list()
    output_list = excel_single_column_extractor(key)
    output_list_values = []
    for output in output_list:
        value = output.get("text")
        if value:
            output["text"] = value.strip()
            output_list_values.append(output)
    return output_list_values


def excel_extraction_request(
    query_key_list, request_data, input_doc_idx, messages, merge=False
):
    """Excel extraction Central"""
    global data_dictionary
    ra_json = request_data["ra_json"]
    nodes = ra_json["nodes"]
    data_dictionary = nodes[input_doc_idx]
    results = list()
    title = "excel_cell"

    for key in query_key_list:
        try:
            advance_settings = key.get("advanceSettings")
            field_name = key["keyLabel"]
            lookup_code = False
            remove_duplicate_trigger = False
            group_multiple_trigger = False

            if key.get("qualifierValue"):
                lookup_code = field_name
                field_name = key.get("qualifierValue")

            if key.get("removeDuplicates"):
                remove_duplicate_trigger = True

            if key["advanceSettings"].get("groupMultiple"):
                group_multiple_trigger = True

            if key.get("type") == "cellRange":
                try:
                    # print("key", key)
                    output_block = generate_cell_block(key, merge)
                    if output_block:
                        output_block["unique_id"] = key.get("id")

                        key_val_dict = dict()
                        if lookup_code:
                            output_block["qualifierParent"] = lookup_code
                        if advance_settings:
                            output_block["advanceSettings"] = advance_settings
                        key_val_dict[field_name] = output_block
                        results.append(key_val_dict)
                except:
                    print(traceback.print_exc())
                    pass

            elif key.get("type") == "singleColumnExcel":
                extracted_cell_list = single_column_excel(key)
                if remove_duplicate_trigger:
                    extracted_cell_list = remove_duplicates(extracted_cell_list)

                if not group_multiple_trigger:
                    for output_block in extracted_cell_list:
                        output_block["unique_id"] = key.get("id")
                        key_val_dict = dict()
                        if lookup_code:
                            output_block["qualifierParent"] = lookup_code
                        if advance_settings:
                            output_block["advanceSettings"] = advance_settings
                        key_val_dict[field_name] = output_block
                        results.append(key_val_dict)
                else:
                    try:
                        group_multiple_separator = key["advanceSettings"][
                            "groupMultipleSeparator"
                        ]
                    except:
                        group_multiple_separator = ", "
                    extracted_block = dict()
                    extracted_block["unique_id"] = key["id"]
                    extracted_block["pos"] = ""
                    extracted_block["pageId"] = ""
                    extracted_block["text"] = group_multiple_separator.join(
                        [x["text"] for x in extracted_cell_list]
                    )
                    extracted_block["title"] = "singleColumn"
                    extracted_block["advanceSettings"] = advance_settings
                    if lookup_code:
                        extracted_block["qualifierParent"] = lookup_code
                    extracted_block["co_ordinates"] = ""
                    extracted_block["cellRange"] = ""
                    extracted_block["worksheet_name"] = ""
                    extracted_block["title"] = title
                    extracted_block["pos"] = ""
                    extracted_block["pageId"] = ""
                    key_val_dict = dict()
                    key_val_dict[field_name] = extracted_block

                    results.append(key_val_dict)
            elif key.get("type") == "excelRegexExtractor":
                extracted_cell_list = regex_excel_extractor(key)
                if remove_duplicate_trigger:
                    extracted_cell_list = remove_duplicates(extracted_cell_list)
                if not group_multiple_trigger:
                    for output_block in extracted_cell_list:
                        output_block["unique_id"] = key.get("id")
                        key_val_dict = dict()
                        if lookup_code:
                            output_block["qualifierParent"] = lookup_code
                        if advance_settings:
                            output_block["advanceSettings"] = advance_settings
                        key_val_dict[field_name] = output_block
                        results.append(key_val_dict)
                else:
                    try:
                        group_multiple_separator = key["advanceSettings"][
                            "groupMultipleSeparator"
                        ]
                    except:
                        group_multiple_separator = ", "
                    extracted_block = dict()
                    extracted_block["unique_id"] = key["id"]
                    extracted_block["pos"] = ""
                    extracted_block["pageId"] = ""
                    extracted_block["text"] = group_multiple_separator.join(
                        [x["text"] for x in extracted_cell_list]
                    )
                    extracted_block["title"] = "excelRegexExtractor"
                    extracted_block["advanceSettings"] = advance_settings
                    if lookup_code:
                        extracted_block["qualifierParent"] = lookup_code
                    extracted_block["co_ordinates"] = ""
                    extracted_block["cellRange"] = ""
                    extracted_block["worksheet_name"] = ""
                    extracted_block["title"] = title
                    extracted_block["pos"] = ""
                    extracted_block["pageId"] = ""
                    key_val_dict = dict()
                    key_val_dict[field_name] = extracted_block

                    results.append(key_val_dict)

            if key.get("type") == "static":
                output_block = dict()
                output_block["text"] = key["shape"]
                output_block["unique_id"] = key.get("id")
                output_block["pos"] = ""
                output_block["pageId"] = ""
                output_block["title"] = "static"
                output_block["STATUS"] = 111
                key_val_dict = dict()
                if lookup_code:
                    output_block["qualifierParent"] = lookup_code
                if advance_settings:
                    output_block["advanceSettings"] = advance_settings
                # lookup_code["advanceSettings"] = advanceSettings
                key_val_dict[field_name] = output_block
                results.append(key_val_dict)
        except:
            print(traceback.print_exc())
            pass
    return results, messages
