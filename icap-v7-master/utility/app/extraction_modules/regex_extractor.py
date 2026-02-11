"""
Regex Extraction Script
========================

Purpose:
--------
This script processes structured data to extract text based on specified regex patterns within defined boundaries, such as top and bottom anchors. It supports multiple regex patterns, thresholds, and unique extraction for pages of a document.

Functions:
----------
1. **get_value_pos_from_list(input_list)**:
   Calculates and returns a bounding box (`left,top,right,bottom`) from a list of positions.
   - **Parameters**:
     - `input_list` (list): List of position strings in the format `left,top,right,bottom`.
   - **Returns**:
     - A string representing the combined bounding box.

2. **find_line_top_pos(data_detail, find_key)**:
   Finds the top position of a line matching the specified text using fuzzy string matching.
   - **Parameters**:
     - `data_detail` (dict): Chunked data containing text and positions.
     - `find_key` (str): Text to find.
   - **Returns**:
     - The top position (`key1`) of the matching line.

3. **get_left_pos(pos)**, **get_top_pos(pos)**, **get_right_pos(pos)**, **get_bottom_pos(pos)**:
   Extracts the respective position values (left, top, right, bottom) from a position string.
   - **Parameters**:
     - `pos` (str): A position string in the format `left,top,right,bottom`.
   - **Returns**:
     - The integer value for the respective position.

4. **regex_extractor_function(key, doc_idx_in_loop, job_id, input_dict, project)**:
   Main function for regex-based text extraction.
   - **Parameters**:
     - `key` (dict): Contains extraction settings including regex patterns, anchors, and thresholds.
     - `doc_idx_in_loop` (int): Index of the document being processed.
     - `job_id` (str): ID of the current job.
     - `input_dict` (dict): Input chunked data.
     - `project` (str): Project name to determine special conditions for extraction.
   - **Returns**:
     - A tuple:
       - `output_list` (list): List of extracted matches with metadata (text, position, page ID, etc.).
       - `regex_failed` (bool): Whether regex failed to match any pattern.
       - `regex_version` (str): Version of the regex extraction process.

Workflow:
---------
1. Extracts data and regex patterns from the `key` parameter.
2. Determines the boundaries using top and bottom anchors, applying thresholds where applicable.
3. Iterates through the document's chunked data, applying regex patterns to each line of text:
   - Matches are extracted, and their metadata (text, position, page ID) is stored in the `output_list`.
   - Supports multiple regex matches per line or stops at the first match based on settings.
4. Ensures uniqueness of matches to avoid duplicate entries.
5. Returns the list of extracted matches, regex status, and version.

Key Features:
-------------
- **Anchored Extraction**:
  Uses top and bottom anchors to limit the search space within the document.

- **Regex Matching**:
  Supports multiple regex patterns with options for single or multiple matches.

- **Unique Extraction**:
  Ensures no duplicate matches are returned for the same page and position.

- **Threshold Adjustments**:
  Allows flexibility in defining the anchor thresholds to expand or contract the extraction range.

- **Error Handling**:
  Employs `try-except` blocks to log and handle exceptions, ensuring robust execution.

Usage:
------
1. Import the script and call `regex_extractor_function()` with appropriate inputs.
2. Define the `key` with the necessary anchors, thresholds, and regex patterns.

Example:
--------
```python
output_list, regex_failed, regex_version = regex_extractor_function(
    key, doc_idx_in_loop, job_id, input_dict, project
)
print(output_list)
"""

import re
import traceback

from fuzzywuzzy import fuzz

from ..json_chunking import json_chunking_main
from .value_directed_script import replace_page_id_string


def get_value_pos_from_list(input_list):
    all_left = []
    all_top = []
    all_right = []
    all_bottom = []
    for v in input_list:
        all_left.append(get_left_pos(v))
        all_top.append(get_top_pos(v))
        all_right.append(get_right_pos(v))
        all_bottom.append(get_bottom_pos(v))

    output_left = str(min(all_left))
    output_top = str(min(all_top))
    output_right = str(max(all_right))
    output_bottom = str(max(all_bottom))

    output_pos = (
        output_left + "," + output_top + "," + output_right + "," + output_bottom
    )
    return output_pos


def find_line_top_pos(data_detail, find_key):
    for key1, value1 in data_detail.items():
        for elem in value1:
            text = elem[0]
            if (fuzz.WRatio(text, find_key)) > 90:
                return key1


def get_left_pos(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos(pos):
    return int(pos.split(",", 3)[3])


def grab_subseq_lines(line, line_key, count_of_lines):
    """return the combined str use the line_key currently in loop from the dictionary and use that to grab
    the subseq lines"""
    subseq_lines = []
    keys = list(line.keys())
    if int(count_of_lines) > len(keys):
        count_of_lines = len(keys)
    for i in range(int(count_of_lines)):
        if line_key not in keys:
            break  # Exit early if line_key is not in keys

        current_index = keys.index(line_key)
        next_index = current_index + 1 + i

        if next_index < len(keys):  # Avoid index errors
            next_key = keys[next_index]
            next_line = " ".join(c[0] for c in line[next_key])
            subseq_lines.append(next_line) if next_line not in subseq_lines else None

    return " ".join(subseq_lines)


def regex_extractor_function(
    key, doc_idx_in_loop, job_id, input_dict, project, grab_extra_trigger=None
):
    try:
        # Initiated on 13/02/2023 - By Emon
        # @Emon on 16-03-2023 Added Thresholds
        # @Emon on 31-03-2023 Threshold changing per line fix
        # @Sunny on 19-03-2025 added grab_extra_trigger
        regex_version = "1.190325"
        regex_failed = False
        regex_found = False
        # Primary loop to get chunks within defined range
        values = input_dict[str(doc_idx_in_loop)]
        data = values["data"]

        output_list = list()
        uniq_list = list()
        uniq = False

        extractor_inputs = key.get("regexExtractor")
        anchors = extractor_inputs.get("anchors")
        regex_list = extractor_inputs.get("patterns")

        if key.get("extractMultiple"):
            multiple_regex_status = True
        else:
            if key.get("keyLabel") == "sysField":
                multiple_regex_status = False
            else:
                multiple_regex_status = True

        first_page_id = None
        for page, line in data.items():
            while not first_page_id:
                for top_pos, chunks in line.items():
                    first_page_id = chunks[0][2]

        # Declaring Placeholders
        top_anchor = None
        bottom_anchor = None
        top_th = None
        bottom_th = None

        # Fetching the anchor texts/shape
        try:
            top_anchor = anchors.get("top").get("text")
            bottom_anchor = anchors.get("bottom").get("text")
        except:
            return output_list

        # Fetching the thresholds
        try:
            top_th = int(anchors.get("top").get("threshold"))
        except:
            pass

        try:
            bottom_th = int(anchors.get("bottom").get("threshold"))
        except:
            pass

        """
        Primary loop
        """
        for page, line in data.items():
            paragraph_top = None
            paragraph_bottom = None

            try:
                if top_anchor:
                    paragraph_top = find_line_top_pos(data[page], top_anchor)
                if bottom_anchor:
                    paragraph_bottom = find_line_top_pos(data[page], bottom_anchor)
            except:
                pass

            # If top anchor present but not found the page is skipped
            if top_anchor and not paragraph_top:
                continue

            # If bottom anchor is present but was not found the page is skipped
            if bottom_anchor and not paragraph_bottom:
                continue

            # Adjusting the thresholds
            if paragraph_top:
                # Current Page Top
                paragraph_top_curr = paragraph_top[:]

                if top_th:
                    paragraph_top_curr = int(paragraph_top_curr) + top_th

            if paragraph_bottom:
                # Current Page Bottom
                paragraph_bottom_curr = paragraph_bottom[:]
                if bottom_th:
                    paragraph_bottom_curr = int(paragraph_bottom_curr) + bottom_th

            """PRIMARY LOOP"""
            # Looping through lines
            for line_key, chunks in line.items():
                """Disregarding lines by top and bottom anchor"""
                if top_anchor:
                    if int(line_key) < int(paragraph_top_curr):
                        continue

                if bottom_anchor:
                    if int(line_key) > int(paragraph_bottom_curr):
                        continue

                """Full line text. This is where the regex is applied on"""
                line_text = " ".join([c[0] for c in chunks])
                """Creates the line boundary"""
                try:
                    line_boundary = get_value_pos_from_list([c[1] for c in chunks])
                except:
                    print(traceback.print_exc())
                    line_boundary = ""

                for regex in regex_list:
                    try:
                        """
                        Finds and extracts all regex matches form chunking dictionary and appends to the output list
                        """
                        if (project == "ShipmentCreate") or (
                            project == "ShipmentUpdate"
                        ):

                            additional_lines = None
                            matched_list = list(re.finditer(regex, line_text))

                            if (
                                grab_extra_trigger
                                and grab_extra_trigger["grabMultiLines"]
                                and matched_list
                            ):
                                additional_lines = grab_subseq_lines(
                                    line,
                                    line_key,
                                    grab_extra_trigger["grabMultiLinesNumber"],
                                )
                                if additional_lines:
                                    line_text = f"{line_text} {additional_lines}"

                            matched_list = re.findall(regex, line_text)

                            if matched_list:
                                regex_found = True
                                page_no_format = "TM000000"
                                page_id = replace_page_id_string(
                                    page_no_format, page, first_page_id
                                )
                                for matched_text in matched_list:
                                    matched_text = matched_text.strip()
                                    if (
                                        matched_text
                                        and line_boundary
                                        and page_id not in uniq_list
                                    ):
                                        uniq_list.extend(
                                            [matched_text, line_boundary, page_id]
                                        )
                                        uniq = True
                                    if uniq:
                                        output = dict()
                                        output["text"] = matched_text.strip()
                                        output["pos"] = line_boundary
                                        output["pageId"] = page_id
                                        output["title"] = "regexExtraction"
                                        output_list.append(output)
                            else:
                                regex_failed = True
                        else:

                            additional_lines = None
                            matched_list = list(re.finditer(regex, line_text))

                            if (
                                grab_extra_trigger
                                and grab_extra_trigger["grabMultiLines"]
                                and matched_list
                            ):
                                additional_lines = grab_subseq_lines(
                                    line,
                                    line_key,
                                    grab_extra_trigger["grabMultiLinesNumber"],
                                )
                                if additional_lines:
                                    line_text = f"{line_text} {additional_lines}"
                            matched_list = list(re.finditer(regex, line_text))
                            if matched_list:
                                regex_found = True
                                page_no_format = "TM000000"
                                page_id = replace_page_id_string(
                                    page_no_format, page, first_page_id
                                )

                                for match_num, match in enumerate(
                                    matched_list, start=1
                                ):
                                    matched_text = match.group()
                                    matched_text = matched_text.strip()
                                    if (
                                        matched_text
                                        and line_boundary
                                        and page_id not in uniq_list
                                    ):
                                        uniq_list.extend(
                                            [matched_text, line_boundary, page_id]
                                        )
                                        uniq = True
                                    if uniq:
                                        output = dict()
                                        output["text"] = matched_text.strip()
                                        output["pos"] = line_boundary
                                        output["pageId"] = page_id
                                        output["title"] = "regexExtraction"
                                        output_list.append(output)
                            else:
                                regex_failed = True
                    except:
                        print(traceback.print_exc())
                        pass

                if not multiple_regex_status:
                    break
        if regex_found:
            regex_failed = False

        return output_list, regex_failed, regex_version

    except:
        print(traceback.print_exc())
