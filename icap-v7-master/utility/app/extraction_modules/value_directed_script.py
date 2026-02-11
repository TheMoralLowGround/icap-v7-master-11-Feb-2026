"""
Selector Function Script
========================

Purpose:
--------
This script extracts text from specified positional boundaries on a document page based on key settings and chunked data.

Functions:
----------
1. **get_left_pos(pos)**:
   Extracts the left position value from a positional string.
   - **Parameters**:
     - `pos` (str): A string in the format `left,top,right,bottom`.
   - **Returns**:
     - `int`: The left position.

2. **get_top_pos(pos)**:
   Extracts the top position value from a positional string.
   - **Parameters**:
     - `pos` (str): A string in the format `left,top,right,bottom`.
   - **Returns**:
     - `int`: The top position.

3. **get_right_pos(pos)**:
   Extracts the right position value from a positional string.
   - **Parameters**:
     - `pos` (str): A string in the format `left,top,right,bottom`.
   - **Returns**:
     - `int`: The right position.

4. **get_bottom_pos(pos)**:
   Extracts the bottom position value from a positional string.
   - **Parameters**:
     - `pos` (str): A string in the format `left,top,right,bottom`.
   - **Returns**:
     - `int`: The bottom position.

5. **replace_page_id_string(s, key, first_page_id)**:
   Converts and replaces page IDs to a consistent format.
   - **Parameters**:
     - `s` (str): Format string, e.g., `TM000000`.
     - `key` (int): Current page number.
     - `first_page_id` (str): First page ID in the dataset.
   - **Returns**:
     - `str`: Updated page ID string.

6. **get_value_pos_from_list(input_list)**:
   Computes a bounding box (`left,top,right,bottom`) covering all positions in the input list.
   - **Parameters**:
     - `input_list` (list): List of positional strings in the format `left,top,right,bottom`.
   - **Returns**:
     - `str`: The combined bounding box.

7. **get_bottom_pos_of_a_line(input_chunks)**:
   Retrieves the minimum bottom position from a list of chunks.
   - **Parameters**:
     - `input_chunks` (list): List of chunk tuples where the second element is the positional string.
   - **Returns**:
     - `int`: The minimum bottom position.

8. **selector_function(key, doc_idx_in_loop, job_id, input_dict)**:
   Extracts text from specified positional areas on the document.
   - **Parameters**:
     - `key` (dict): Defines extraction criteria such as boundaries and page ID.
     - `doc_idx_in_loop` (int): Index of the document in the loop.
     - `job_id` (str): Current job ID.
     - `input_dict` (dict): Input data containing chunked text and positions.
   - **Returns**:
     - `tuple`: A dictionary with extracted text and metadata, and the selector version.
     - `None` if no text is extracted.

Workflow:
---------
1. Reads the chunked data and positional settings from `key`.
2. Supports multi-page or single-page extraction based on pipe-separated settings in `key`.
3. Iterates through lines of text, filtering chunks within the specified boundaries.
4. Checks if text chunks align with the left and right positional constraints.
5. Concatenates text from valid chunks, computes the bounding box, and assigns page IDs.
6. Returns the extracted text block with metadata or `None` if no data is found.

Key Features:
-------------
- **Boundary-based Extraction**:
  Extracts text within a rectangle defined by top, bottom, left, and right positions.

- **Multi-page Support**:
  Handles pipe-separated boundaries for extraction across multiple pages.

- **Duplicate Prevention**:
  Avoids adding repeated chunks to the output list.

- **Robust Page ID Handling**:
  Replaces page IDs consistently to match data formats.

- **Error Handling**:
  Ensures resilience to malformed input or unexpected data formats using `try-except` blocks.

Usage:
------
1. Define the `key` with positional settings and call `selector_function`.
2. Input chunked data through `input_dict`.

Example:
--------
```python
output, version = selector_function(key, doc_idx_in_loop, job_id, input_dict)
if output:
    print("Extracted Text:", output["text"])
else:
    print("No text found.")
"""


import operator
import re
import traceback

from rapidfuzz import fuzz, process

from app.json_chunking import json_chunking_main


def adjust_th(
    top_anchor_bottom_pos,
    bottom_anchor_top_pos,
    right_anchor_left_pos,
    left_anchor_right_pos,
    th_set,
):
    """
    This function takes in integers and a set of thresholds and adjusts the integers based on related thresholds
    """
    top_th = th_set[0]
    bottom_th = th_set[1]
    right_th = th_set[2]
    left_th = th_set[3]

    # Adjusting the thresholds
    if top_anchor_bottom_pos and top_th:
        top_anchor_bottom_pos += top_th
    if bottom_anchor_top_pos and bottom_th:
        bottom_anchor_top_pos += bottom_th
    if right_anchor_left_pos and right_th:
        right_anchor_left_pos += right_th
    if left_anchor_right_pos and left_th:
        left_anchor_right_pos += left_th
    return (
        top_anchor_bottom_pos,
        bottom_anchor_top_pos,
        right_anchor_left_pos,
        left_anchor_right_pos,
    )


# Top parse positions (Left, Top, Right, Bottom)
def get_left_pos(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos(pos):
    return int(pos.split(",", 3)[3])


def str_to_shape(string):
    """
    Converts string into Shape
    """
    convert_string = []
    for i in string:
        if re.findall("[A-Z]", i):
            convert_string.append("X")
        elif re.findall("[a-z]", i):
            convert_string.append("x")
        elif re.findall("[0-9]", i):
            convert_string.append("D")
        elif i == ".":
            convert_string.append("b")
        elif i == ",":
            convert_string.append("c")
        elif i == ":":
            convert_string.append("y")
        else:
            convert_string.append(i)

    return "".join(convert_string)


def find_line_multi(data_detail, find_key):
    """
    This function takes in a text and then loops around chunking dictionary to find the text inside a chunk text or
    a fuzzymatch of more than 90%
    """
    output_multi_list = []
    for key, value in data_detail.items():
        for key1, value1 in value.items():
            for elem in value1:
                text = elem[0]
                if (find_key in text) or (fuzz.WRatio(text, find_key)) > 90:
                    output_multi_list.append([key, elem[1]])
    return output_multi_list


def get_value_pos_from_list(input_list, th_set):
    """
    This function takes in a list of co-ordinates and returns the vector summation of them
    """
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


def replace_page_id_string(s, key, first_page_id):
    """
    This function takes in a page index and then converts it to Page ID format which is TM00000X
    """

    def end_nonzero_int_count(s):  # function added here by emon 04/04/22
        s = s.replace("tm", "").replace("TM","")
        count = len(s)
        return count

    key = int(key)

    last_int_count = end_nonzero_int_count(first_page_id)
    last_int = first_page_id[-last_int_count:]
    new_key = str(key + int(last_int))
    new_key_len = len(new_key)

    "this function replaces key to key format of datacap"
    output = s[:-new_key_len] + new_key

    return output


def get_the_closest_chunk(input_lines, anchor_pos):
    """
    This function finds the closest chunk that in regards to original defined anchor text and position.
    As there could be multiple instances of matches inside one single page.
    """

    if len(input_lines) == 1:
        return input_lines[0]
    anchor_left = get_left_pos(anchor_pos)
    anchor_top = get_top_pos(anchor_pos)

    check_distance_list = list()
    try:
        for i, line in enumerate(input_lines):
            chunk_pos = line[-1]
            chunk_left = get_left_pos(chunk_pos)
            chunk_top = get_top_pos(chunk_pos)
            x1, y1, x2, y2 = anchor_left, anchor_top, chunk_left, chunk_top
            dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** (1 / 2)
            check_distance_list.append([i, dist])
        check_distance_list = sorted(check_distance_list, key=operator.itemgetter(1))
        selected_dist_pair = check_distance_list[0]
        selected_block_idx = selected_dist_pair[0]
        return input_lines[selected_block_idx]
    except:
        return input_lines[0]


def get_anchor_data(anchor):
    shape = anchor["text"]
    pos = anchor["pos"]
    return shape, pos


def grab_anchor_all(input_key, anchor_type):
    """Grabs anchor data from definition"""
    try:
        th_val = None
        anchor_data = input_key["anchorShapes"][anchor_type]
        anchor_shape, defined_anchor_pos = get_anchor_data(anchor_data)
        if anchor_type == "left":
            defined_anchor_target_pos = get_right_pos(defined_anchor_pos)
        elif anchor_type == "top":
            defined_anchor_target_pos = get_bottom_pos(defined_anchor_pos)
        elif anchor_type == "right":
            defined_anchor_target_pos = get_left_pos(defined_anchor_pos)
        else:
            defined_anchor_target_pos = get_top_pos(defined_anchor_pos)
        try:
            if "threshold" in anchor_data.keys():
                if anchor_data["threshold"]:
                    th_val = int(anchor_data["threshold"])
        except:
            pass
        return anchor_shape, defined_anchor_pos, defined_anchor_target_pos, th_val
    except:
        return None, None, None, None


def delete_from(input_string, manipulative_value):
    """This function deletes up until a specific substring of a string"""
    try:
        output_text = input_string
        find_idx = output_text.lower().find(manipulative_value.lower())
        if find_idx > -1:
            output_text = output_text[:find_idx]
        return output_text.strip()
    except:
        return input_string


def find_sub_box(parent_box_str, text, sub_chunk):
    """
    Find the sub-box coordinates for a given sub-chunk within a parent box.

    Args:
        parent_box_str (str): Coordinates of the parent box in the format "x_min,y_min,x_max,y_max".
        text (str): The full text in the parent box.
        sub_chunk (str): The sub-chunk of text for which the sub-box is to be found.

    Returns:
        str: Sub-box coordinates as a formatted string "x_min,y_min,x_max,y_max".
    """

    try:
        # Parse the parent box string into coordinates
        parent_box = tuple(map(int, parent_box_str.split(",")))

        # Find the best match for the sub-chunk in the text using fuzz.WRatio
        best_match = process.extractOne(sub_chunk, [text], scorer=fuzz.WRatio)
        if not best_match or best_match[1] < 70:  # Match threshold
            raise ValueError("Sub-chunk not found or confidence too low.")

        # Get the start and end positions of the best match in the text
        match_text = best_match[0]
        start_idx = text.find(match_text)
        end_idx = start_idx + len(match_text)

        # Calculate the parent box width
        parent_width = parent_box[2] - parent_box[0]

        # Calculate the proportional start and end positions in the text
        total_chars = len(text)
        start_ratio = start_idx / total_chars
        end_ratio = end_idx / total_chars

        # Calculate the sub-box coordinates
        sub_x_min = parent_box[0] + int(parent_width * start_ratio)
        sub_x_max = parent_box[0] + int(parent_width * end_ratio)

        # Keep the y-coordinates the same as the parent box
        sub_y_min = parent_box[1]
        sub_y_max = parent_box[3]

        # Format the output as "x_min,y_min,x_max,y_max"
        return f"{sub_x_min},{sub_y_min},{sub_x_max},{sub_y_max}"
    except Exception as e:
        print(f"Error: {e}")
        return parent_box_str


def extractor(data, inputs, first_page_id):
    """Primary function that loops through the chunking dictionary to extract the text inside the defined area"""
    # print(inputs)
    count = 0
    output_page_index = inputs.get("output_page_index")
    top_anchor_bottom_pos = inputs.get("topAnchorBottomPos")
    bottom_anchor_top_pos = inputs.get("bottomAnchorTopPos")
    left_anchor_right_pos = inputs.get("leftAnchorRightPos")
    right_anchor_left_pos = inputs.get("rightAnchorLeftPos")
    right_anchor_shape = inputs.get("rightAnchorShape")
    right_anchor_line_data = inputs.get("rightAnchorLineData")
    th_set = inputs.get("th_set")

    left_anchor_shape = inputs.get("leftAnchorShape")
    left_anchor_line_data = inputs.get("leftAnchorLineData")

    # print("page_indexes")
    # print(data.keys())

    chunk_pos_list = list()
    output_text_list = list()
    chunk_page_list = list()

    # Primary loop to get chunks within defined range
    for page, line in data.items():
        count += 1
        if page == output_page_index:
            for line_top_key, chunk_data in line.items():
                line_text_list = list()
                line_top = int(line_top_key)
                line_is_allowed = True
                # Conditions for selecting the line
                if top_anchor_bottom_pos and bottom_anchor_top_pos:
                    if not (
                        (line_top > top_anchor_bottom_pos)
                        and (line_top < bottom_anchor_top_pos)
                    ):
                        line_is_allowed = False
                elif top_anchor_bottom_pos and (not bottom_anchor_top_pos):
                    if not (line_top > top_anchor_bottom_pos):
                        line_is_allowed = False
                elif (not top_anchor_bottom_pos) and (bottom_anchor_top_pos):
                    if not (line_top < bottom_anchor_top_pos):
                        line_is_allowed = False

                left_anchor_present_indicator = list()
                right_anchor_present_indicator = list()
                if line_is_allowed:
                    chunk_disregard_decision = dict()
                    for chunk_idx, chunk in enumerate(chunk_data):
                        chunk_text = chunk[0]
                        chunk_pos = chunk[-2]
                        chunk_left = get_left_pos(chunk_pos)
                        chunk_right = get_right_pos(chunk_pos)
                        chunk_bottom = get_bottom_pos(chunk_pos)
                        allowed = True
                        # Conditions for selecting the line
                        if left_anchor_right_pos and right_anchor_left_pos:
                            if int(chunk_left) < left_anchor_right_pos:
                                chunk_disregard_decision[chunk_idx] = "Out-of-Left"

                                if int(chunk_right) > right_anchor_left_pos:
                                    chunk_disregard_decision[
                                        chunk_idx
                                    ] = "Out-of-RightLeft"

                                allowed = False

                            else:
                                if int(chunk_right) > right_anchor_left_pos:
                                    chunk_disregard_decision[chunk_idx] = "Out-of-Right"
                                    allowed = False

                        elif left_anchor_right_pos and (not right_anchor_left_pos):
                            if not (int(chunk_left) > left_anchor_right_pos):
                                allowed = False
                                chunk_disregard_decision[chunk_idx] = "Out-of-Left"

                        elif (not left_anchor_right_pos) and right_anchor_left_pos:
                            if not (int(chunk_right) < right_anchor_left_pos):
                                chunk_disregard_decision[chunk_idx] = "Out-of-Right"
                                allowed = False

                        if bottom_anchor_top_pos:
                            if chunk_bottom > bottom_anchor_top_pos:
                                allowed = False

                        if left_anchor_right_pos:
                            if left_anchor_shape in chunk_text:
                                left_anchor_present_indicator.append(
                                    [chunk_idx, chunk_pos]
                                )

                        if right_anchor_left_pos:
                            if right_anchor_shape in chunk_text:
                                right_anchor_present_indicator.append(
                                    [chunk_idx, chunk_pos]
                                )

                        if chunk_pos in chunk_pos_list:
                            """Added by @Emon on 29/08/2022 - Sometimes due to problem in line chunking same chunk comes in two consecutive
                            sentences hence gets extracted twice. This is to prevent that
                            """
                            allowed = False

                        if allowed:
                            line_text_list.append(chunk_text)
                            chunk_actual_pos = find_sub_box(
                                chunk_pos, chunk_text, chunk_text
                            )
                            chunk_pos_list.append(chunk_actual_pos)

                    extraction_done = False
                    if line_text_list:
                        line_text = " ".join(line_text_list)
                        if re.search("[a-zA-Z|0-9]", line_text):
                            extraction_done = True
                            output_text_list.append(line_text)

                            chunk_page_list.append(page)
                    if not extraction_done:
                        try:
                            disregard_operation = False
                            if (
                                left_anchor_present_indicator
                                and right_anchor_present_indicator
                            ):
                                disregard_both_side_trim = False
                                if left_anchor_line_data and right_anchor_line_data:
                                    if not (
                                        abs(
                                            line_top
                                            - get_top_pos(left_anchor_line_data[1])
                                        )
                                        < 10
                                    ) and not (
                                        (
                                            abs(
                                                line_top
                                                - get_top_pos(right_anchor_line_data[1])
                                            )
                                            < 10
                                        )
                                    ):
                                        disregard_both_side_trim = True

                                if not disregard_both_side_trim:
                                    target_chunk_left = left_anchor_present_indicator[
                                        0
                                    ][0]
                                    chunk_pos_left = left_anchor_present_indicator[0][1]
                                    target_chunk_right = right_anchor_present_indicator[
                                        0
                                    ][0]
                                    chunk_pos_right = right_anchor_present_indicator[0][
                                        1
                                    ]
                                    if (
                                        chunk_disregard_decision[target_chunk_left]
                                        == "Out-of-RightLeft"
                                        and chunk_disregard_decision[target_chunk_right]
                                        == "Out-of-RightLeft"
                                    ):
                                        # afterIndicator = chunk_data[target_chunk:]
                                        if target_chunk_left == target_chunk_right:
                                            target_chunk = target_chunk_right

                                            indicator = chunk_data[target_chunk]

                                            line_text_list_1 = [
                                                indicator[0].split(left_anchor_shape)[1]
                                            ]

                                            line_text = " ".join(line_text_list_1)
                                            line_text = delete_from(
                                                line_text, right_anchor_shape
                                            )

                                            if re.search("[a-zA-Z|0-9]", line_text):
                                                output_text_list.append(line_text)

                                                chunk_actual_pos = find_sub_box(
                                                    chunk_pos, chunk_text, line_text
                                                )
                                                chunk_pos_list.append(chunk_actual_pos)

                                                chunk_page_list.append(page)
                                                disregard_operation = True

                            if disregard_operation:
                                continue

                            if left_anchor_present_indicator:
                                disregard_out_of_left_operation = False
                                if left_anchor_line_data:
                                    if not (
                                        abs(
                                            line_top
                                            - get_top_pos(left_anchor_line_data[1])
                                        )
                                        < 10
                                    ):
                                        disregard_out_of_left_operation = True

                                if not disregard_out_of_left_operation:
                                    target_chunk = left_anchor_present_indicator[0][0]
                                    chunk_pos = left_anchor_present_indicator[0][1]
                                    if (
                                        chunk_disregard_decision[target_chunk]
                                        == "Out-of-Left"
                                    ):
                                        # afterIndicator = chunk_data[target_chunk:]
                                        indicator = chunk_data[target_chunk]
                                        line_text_list = [
                                            indicator[0].split(left_anchor_shape, 1)[1]
                                        ]
                                        line_text = " ".join(line_text_list)
                                        if re.search("[a-zA-Z|0-9]", line_text):
                                            output_text_list.append(line_text)

                                            chunk_actual_pos = find_sub_box(
                                                chunk_pos, chunk_text, line_text
                                            )
                                            chunk_pos_list.append(chunk_actual_pos)

                                            chunk_page_list.append(page)

                            if right_anchor_present_indicator:
                                disregard_out_of_right_operation = False
                                if right_anchor_line_data:
                                    if not (
                                        abs(
                                            line_top
                                            - get_top_pos(right_anchor_line_data[1])
                                        )
                                        < 10
                                    ):
                                        disregard_out_of_right_operation = True

                                if not disregard_out_of_right_operation:
                                    target_chunk = right_anchor_present_indicator[0][0]
                                    chunk_pos = right_anchor_present_indicator[0][1]
                                    if (
                                        chunk_disregard_decision[target_chunk]
                                        == "Out-of-Right"
                                    ):
                                        # afterIndicator = chunk_data[target_chunk:]
                                        indicator = chunk_data[target_chunk]
                                        line_text_list = [
                                            indicator[0].split(right_anchor_shape, 1)[0]
                                        ]
                                        line_text = " ".join(line_text_list)
                                        if re.search("[a-zA-Z|0-9]", line_text):
                                            chunk_actual_pos = find_sub_box(
                                                chunk_pos, chunk_text, line_text
                                            )
                                            chunk_pos_list.append(chunk_actual_pos)

                                            output_text_list.append(line_text)
                                            chunk_page_list.append(page)

                        except:
                            print(traceback.print_exc())
                            pass
    try:
        output_boundary = get_value_pos_from_list(chunk_pos_list, th_set)
    except:
        # print(traceback.print_exc())
        output_boundary = ""

    if output_text_list:
        output_text = "\n".join(output_text_list).strip()
        output_dict = dict()
        if output_text[0] == ":":
            output_text = output_text[1:]
        output_dict["text"] = output_text.strip()
        output_dict["pos"] = output_boundary
        page_no_format = "TM000000"
        output_dict["pageId"] = replace_page_id_string(
            page_no_format, output_page_index, first_page_id
        )
        output_dict["title"] = "anchor"
        return output_dict


def regular_anchor_search(key, data, page_limiter):
    """
    This function searches for only one instance of a target text inside one document instead of multiple occurances of same
    text multiple times throughout one document
    """
    # Initiating actual anchors
    left_anchor_right_pos = None
    top_anchor_bottom_pos = None
    right_anchor_left_pos = None
    bottom_anchor_top_pos = None
    left_anchor_line_data = None
    output_page_index = None
    right_anchor_line_data = None

    # Placeholder in case left anchor is not found
    left_adjusted = False

    # Placeholder if top anchor is not found
    top_adjusted = False

    # Placeholder if bottom anchor is not found
    bottom_adjusted = False

    # Placeholder if right anchor is not found
    right_adjusted = False

    """Grabbing anchor data from definitions"""
    (
        left_anchor_shape,
        defined_left_anchor_pos,
        defined_left_anchor_right_pos,
        left_th,
    ) = grab_anchor_all(key, "left")
    (
        top_anchor_shape,
        defined_top_anchor_pos,
        defined_top_anchor_bottom_pos,
        top_th,
    ) = grab_anchor_all(key, "top")
    (
        right_anchor_shape,
        defined_right_anchor_pos,
        defined_right_anchor_left_pos,
        right_th,
    ) = grab_anchor_all(key, "right")
    (
        bottom_anchor_shape,
        defined_bottom_anchor_pos,
        defined_bottom_anchor_top_pos,
        bottom_th,
    ) = grab_anchor_all(key, "bottom")

    found_on_page_list = list()

    top_bottom_page_check = dict()

    if left_anchor_shape:
        """Getting the right position left boundary Shape"""
        left_anchor_line_data_multi = find_line_multi(data, left_anchor_shape)
        if left_anchor_line_data_multi:
            left_anchor_line_data = get_the_closest_chunk(
                left_anchor_line_data_multi, defined_left_anchor_pos
            )
            left_anchor_right_pos = get_right_pos(left_anchor_line_data[1])
            found_on_page_list.append(left_anchor_line_data[0])

        else:
            """If no left anchor is found we assume the defined Left Anchor Pos"""
            left_anchor_right_pos = defined_left_anchor_right_pos
            left_adjusted = True

    if top_anchor_shape:
        multi_include = False
        multi_include_trigger_text = "(multi)"
        if multi_include_trigger_text in top_anchor_shape:
            multi_include = True
            top_anchor_shape = top_anchor_shape.replace(multi_include_trigger_text, "")

        # Getting the bottom position of top boundary shape
        top_anchor_line_data_multi = find_line_multi(data, top_anchor_shape)

        if top_anchor_line_data_multi:
            if multi_include:
                top_anchor_line_data = top_anchor_line_data_multi[0]
            else:
                top_anchor_line_data = get_the_closest_chunk(
                    top_anchor_line_data_multi, defined_top_anchor_pos
                )
            top_anchor_bottom_pos = get_bottom_pos(top_anchor_line_data[1])
            found_on_page_list.append(top_anchor_line_data[0])
            top_bottom_page_check["top"] = top_anchor_line_data[0]

        else:
            top_adjusted = True
            """If no top anchor is found we just assume the defined Top Anchor Pos"""
            top_anchor_bottom_pos = defined_top_anchor_bottom_pos

    if right_anchor_shape:
        # Getting the left position of right boundary shape
        right_anchor_line_data_multi = find_line_multi(data, right_anchor_shape)

        if right_anchor_line_data_multi:
            right_anchor_line_data = get_the_closest_chunk(
                right_anchor_line_data_multi, defined_right_anchor_pos
            )
            right_anchor_left_pos = get_left_pos(right_anchor_line_data[1])
            output_page_index = right_anchor_line_data[0]
            found_on_page_list.append(output_page_index)
        else:
            right_adjusted = True
            """If no right anchor is found we just assume the defined Right Anchor Pos"""
            right_anchor_left_pos = defined_right_anchor_left_pos

    if bottom_anchor_shape:
        # Getting the top position of bottom boundary shape
        bottom_anchor_line_data_multi = find_line_multi(data, bottom_anchor_shape)
        # print(bottomShapeLineData)
        if bottom_anchor_line_data_multi:
            bottom_anchor_line_data = get_the_closest_chunk(
                bottom_anchor_line_data_multi, defined_bottom_anchor_pos
            )
            bottom_anchor_top_pos = get_top_pos(bottom_anchor_line_data[1])
            found_on_page_list.append(bottom_anchor_line_data[0])
            top_bottom_page_check["bottom"] = bottom_anchor_line_data[0]
        else:
            """If no bottom anchor is found we just assume the defined bottom Anchor Pos"""
            bottom_anchor_top_pos = defined_bottom_anchor_top_pos
            bottom_adjusted = True

    try:
        """if top/bottom anchor is missed and a provision that the difference between bottom and top pos never be negative"""
        if (top_anchor_bottom_pos > bottom_anchor_top_pos) and (
            defined_top_anchor_bottom_pos and defined_bottom_anchor_top_pos
        ):
            defined_height = (
                defined_bottom_anchor_top_pos - defined_top_anchor_bottom_pos
            )
            if top_adjusted:
                top_anchor_bottom_pos = bottom_anchor_top_pos - defined_height
            else:
                bottom_anchor_top_pos = top_anchor_bottom_pos + defined_height
    except:
        pass

    # Section to find the exact page
    """So, so out of all the anchors found the image, three are found on the first page and only one is found on the second
    page. Clearly this is not to be the case. So, we assume that ALL THE ANCHORS IF FOUND MUST BE IN THE SAME PAGE"""

    def most_common(lst):
        return max(set(lst), key=lst.count)

    if found_on_page_list:
        output_page_index = most_common(found_on_page_list)
    if page_limiter:
        output_page_index = page_limiter

    try:
        if top_bottom_page_check:
            """If top and bottom anchors are not found on the same page then adjustments"""
            if (
                top_bottom_page_check["top"] != top_bottom_page_check["bottom"]
            ):  # If both anchors are not found on the same page
                # If bottom is found on the common page
                if output_page_index == top_bottom_page_check["bottom"]:
                    top_anchor_bottom_pos = (
                        defined_top_anchor_bottom_pos  # Then make top Anchor reset
                    )
                else:
                    # Or else make the bottom anchor reset
                    bottom_anchor_top_pos = defined_bottom_anchor_top_pos
    except:
        pass

    # Adjusting the thresholds
    th_set = [top_th, bottom_th, right_th, left_th]
    (
        top_anchor_bottom_pos,
        bottom_anchor_top_pos,
        right_anchor_left_pos,
        left_anchor_right_pos,
    ) = adjust_th(
        top_anchor_bottom_pos,
        bottom_anchor_top_pos,
        right_anchor_left_pos,
        left_anchor_right_pos,
        th_set,
    )

    debug = False

    """ If left anchor is not found we just calculate a percentile to guess the left anchor"""
    # Adjustement calculations depending on parallel positions
    if left_adjusted:
        # if debug:
        #     print("Right Anchor Current", "--", right_anchor_left_pos, " ",
        #           "Defined Right Anchor", defined_right_anchor_left_pos)
        #     print("left anchor right pos current", "---", left_anchor_right_pos)
        if right_anchor_left_pos:
            right_anchor_diff = (
                right_anchor_left_pos - defined_right_anchor_left_pos
            ) / defined_right_anchor_left_pos
            left_anchor_right_pos = left_anchor_right_pos + (
                right_anchor_diff * left_anchor_right_pos
            )
        # if debug:
        #     print("Adjusted left anchor right position", left_anchor_right_pos)

    """ Similar process if the bottom anchor is not found a percentile using the top anchor is used to guess the bottom anchor"""
    if bottom_adjusted:
        # if debug:
        #     print("Bottom Has been adjusted")
        #     print("Top anchor Bottom", "--", top_anchor_bottom_pos, " ",
        #           "Defined Top Anchor Bottom", defined_top_anchor_bottom_pos)
        #     print("bottom anchor right pos current", "---", bottom_anchor_top_pos)
        if top_anchor_bottom_pos:
            top_anchor_diff = (
                top_anchor_bottom_pos - defined_top_anchor_bottom_pos
            ) / defined_top_anchor_bottom_pos
            bottom_anchor_top_pos = bottom_anchor_top_pos + (
                bottom_anchor_top_pos * top_anchor_diff
            )
        # if debug:
        #     print("Adjusted Top anchor bottom position", bottom_anchor_top_pos)

    anchor_find_check = [left_adjusted, top_adjusted, right_adjusted, bottom_adjusted]
    # print(anchor_find_check)

    if anchor_find_check.count(True) > 1:
        return None
    final_output = list()
    return_dict = {
        "output_page_index": output_page_index,
        "topAnchorBottomPos": top_anchor_bottom_pos,
        "bottomAnchorTopPos": bottom_anchor_top_pos,
        "leftAnchorRightPos": left_anchor_right_pos,
        "rightAnchorLeftPos": right_anchor_left_pos,
        "leftAnchorShape": left_anchor_shape,
        "leftAnchorLineData": left_anchor_line_data,
        "rightAnchorShape": right_anchor_shape,
        "rightAnchorLineData": right_anchor_line_data,
        "th_set": th_set,
    }
    final_output.append(return_dict)

    return final_output


def fetch_relative_distance(pos1, pos2):
    """Get Relative distance between two positions"""
    x1 = get_left_pos(pos1) + ((get_right_pos(pos1) - get_left_pos(pos1)) / 2)
    y1 = get_top_pos(pos1) + ((get_bottom_pos(pos1) - get_top_pos(pos1)) / 2)
    x2 = get_left_pos(pos2) + ((get_right_pos(pos2) - get_left_pos(pos2)) / 2)
    y2 = get_top_pos(pos2) + ((get_bottom_pos(pos2) - get_top_pos(pos2)) / 2)
    dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** (1 / 2)
    # dist = abs(y2-y1)
    return dist


def fetch_related_anchor(line_data, fixed_line_data, related_distance):
    """This function uses the defined distance of two anchors and then in subsequent processing: Finds the relative anchors using a fixed position"""

    # print(related_distance, fixed_line_data)
    fixed_pos = fixed_line_data[1]
    distance_list = list()
    for x in line_data:
        pos = x[1]
        # print(pos)
        distance = fetch_relative_distance(fixed_pos, pos)
        # print(distance)
        distance_list.append(distance)
    target = min(distance_list, key=lambda x: abs(x - related_distance))
    # print(target)
    target_index = distance_list.index(target)
    # print(target_index)
    output = line_data[target_index]
    return output


def multiple_anchor_search(key, data, page_limiter):
    """
    This function searches for multiple instances of target text inside one document.
    Primary difference from the regular anchor extractor is that there are multiple scenarios while finding the top anchor
    """

    final_output = list()
    # Placeholder in case left anchor is not found
    left_adjusted = False

    # Placeholder if top anchor is not found
    top_adjusted = False

    # Placeholder if bottom anchor is not found
    bottom_adjusted = False

    # Placeholder if right anchor is not found
    right_adjusted = False

    # Initiating actual anchors
    left_anchor_right_pos = None
    top_anchor_bottom_pos = None
    right_anchor_left_pos = None
    bottom_anchor_top_pos = None
    left_anchor_line_data = None
    output_page_index = None
    left_anchor_shape = None
    right_anchor_line_data = None

    """Grabbing anchor data from definitions"""
    (
        left_anchor_shape,
        defined_left_anchor_pos,
        defined_left_anchor_right_pos,
        left_th,
    ) = grab_anchor_all(key, "left")
    (
        top_anchor_shape,
        defined_top_anchor_pos,
        defined_top_anchor_bottom_pos,
        top_th,
    ) = grab_anchor_all(key, "top")
    (
        right_anchor_shape,
        defined_right_anchor_pos,
        defined_right_anchor_left_pos,
        right_th,
    ) = grab_anchor_all(key, "right")
    (
        bottom_anchor_shape,
        defined_bottom_anchor_pos,
        defined_bottom_anchor_top_pos,
        bottom_th,
    ) = grab_anchor_all(key, "bottom")

    if top_anchor_shape:
        # Getting the bottom position of top boundary shape
        top_anchor_line_data_multi = find_line_multi(data, top_anchor_shape)
        if not top_anchor_line_data_multi:
            top_adjusted = True
            top_anchor_bottom_pos = defined_top_anchor_bottom_pos

    if left_anchor_shape:
        """Getting the right position left boundary Shape"""
        left_anchor_line_data_multi = find_line_multi(data, left_anchor_shape)
        if not left_anchor_line_data_multi:
            left_adjusted = True
            """If no left anchor is found we just assume the defined left Anchor Pos"""
            left_anchor_right_pos = defined_left_anchor_right_pos

    if right_anchor_shape:
        # Getting the left position of right boundary shape
        right_anchor_line_data_multi = find_line_multi(data, right_anchor_shape)
        if not right_anchor_line_data_multi:
            right_adjusted = True
            """If no right anchor is found we just assume the defined Right Anchor Pos"""
            right_anchor_left_pos = defined_right_anchor_left_pos

    if bottom_anchor_shape:
        # Getting the top position of bottom boundary shape

        bottom_anchor_line_data_multi = find_line_multi(data, bottom_anchor_shape)
        if not bottom_anchor_line_data_multi:
            bottom_adjusted = True
            bottom_anchor_top_pos = defined_bottom_anchor_top_pos

    anchor_find_check = [left_adjusted, top_adjusted, right_adjusted, bottom_adjusted]

    if anchor_find_check.count(True) > 1:
        return None

    # SCENARIO 1 - TOP ANCHORS ONLY COME ONCE
    scenario = None
    if len(top_anchor_line_data_multi) == 1:
        scenario = 1

    elif len(top_anchor_line_data_multi) > 1:
        scenario = 2

    if scenario == 1:
        """
        WHEN THE TOP ANCHOR COMES ONLY ONCE, THE APPEARANCE OF OTHER ANCHORS MULTIPLE TIMES DOES NOT MATTER.

        Rest of the anchors are searched first, and the distance relation between the defined top anchor and other anchors
        are used to extract the anchor that is similar.
        """
        output_page_index = page_limiter
        top_anchor_line_data = top_anchor_line_data_multi[0]
        top_anchor_bottom_pos = get_bottom_pos(top_anchor_line_data[1])

        if left_anchor_shape and not left_adjusted:
            related_distance = fetch_relative_distance(
                defined_top_anchor_pos, defined_left_anchor_pos
            )
            left_anchor_line_data = fetch_related_anchor(
                left_anchor_line_data_multi, top_anchor_line_data, related_distance
            )
            left_anchor_right_pos = get_right_pos(left_anchor_line_data[1])

        if right_anchor_shape and not right_adjusted:
            related_distance = fetch_relative_distance(
                defined_top_anchor_pos, defined_right_anchor_pos
            )
            right_anchor_line_data = fetch_related_anchor(
                right_anchor_line_data_multi, top_anchor_line_data, related_distance
            )
            right_anchor_left_pos = get_left_pos(right_anchor_line_data[1])

        if bottom_anchor_shape and not bottom_adjusted:
            related_distance = fetch_relative_distance(
                defined_top_anchor_pos, defined_bottom_anchor_pos
            )
            bottom_anchor_line_data = fetch_related_anchor(
                bottom_anchor_line_data_multi, top_anchor_line_data, related_distance
            )
            bottom_anchor_top_pos = get_top_pos(bottom_anchor_line_data[1])

        th_set = [top_th, bottom_th, right_th, left_th]
        (
            top_anchor_bottom_pos,
            bottom_anchor_top_pos,
            right_anchor_left_pos,
            left_anchor_right_pos,
        ) = adjust_th(
            top_anchor_bottom_pos,
            bottom_anchor_top_pos,
            right_anchor_left_pos,
            left_anchor_right_pos,
            th_set,
        )

        return_dict = {
            "output_page_index": output_page_index,
            "topAnchorBottomPos": top_anchor_bottom_pos,
            "bottomAnchorTopPos": bottom_anchor_top_pos,
            "leftAnchorRightPos": left_anchor_right_pos,
            "rightAnchorLeftPos": right_anchor_left_pos,
            "leftAnchorShape": left_anchor_shape,
            "leftAnchorLineData": left_anchor_line_data,
            "rightAnchorShape": right_anchor_shape,
            "rightAnchorLineData": right_anchor_line_data,
        }
        final_output.append(return_dict)

    elif scenario == 2:
        """
        WHEN THE TOP ANCHOR COMES MULTIPLE TIMES. Using the top anchor find index, rest on the same indexes are selected
        """

        output_page_index = page_limiter
        for top_idx, top_anchor_line_data in enumerate(top_anchor_line_data_multi):
            top_anchor_bottom_pos = get_bottom_pos(top_anchor_line_data[1])

            if left_anchor_shape and not left_adjusted:
                try:
                    left_anchor_line_data = left_anchor_line_data_multi[top_idx]
                    left_anchor_right_pos = get_right_pos(left_anchor_line_data[1])
                except:
                    left_anchor_right_pos = defined_left_anchor_right_pos

            if right_anchor_shape and not right_adjusted:
                try:
                    right_anchor_line_data = right_anchor_line_data_multi[top_idx]
                    right_anchor_left_pos = get_left_pos(right_anchor_line_data[1])
                except:
                    right_anchor_left_pos = defined_right_anchor_left_pos

            if bottom_anchor_shape and not bottom_adjusted:
                try:
                    bottom_anchor_line_data = bottom_anchor_line_data_multi[top_idx]
                    bottom_anchor_top_pos = get_top_pos(bottom_anchor_line_data[1])
                except:
                    bottom_anchor_top_pos = defined_bottom_anchor_top_pos

            th_set = [top_th, bottom_th, right_th, left_th]
            (
                top_anchor_bottom_pos,
                bottom_anchor_top_pos,
                right_anchor_left_pos,
                left_anchor_right_pos,
            ) = adjust_th(
                top_anchor_bottom_pos,
                bottom_anchor_top_pos,
                right_anchor_left_pos,
                left_anchor_right_pos,
                th_set,
            )

            return_dict = {
                "output_page_index": output_page_index,
                "topAnchorBottomPos": top_anchor_bottom_pos,
                "bottomAnchorTopPos": bottom_anchor_top_pos,
                "leftAnchorRightPos": left_anchor_right_pos,
                "rightAnchorLeftPos": right_anchor_left_pos,
                "leftAnchorShape": left_anchor_shape,
                "leftAnchorLineData": left_anchor_line_data,
                "rightAnchorShape": right_anchor_shape,
                "rightAnchorLineData": right_anchor_line_data,
                "th_set": th_set,
            }

            final_output.append(return_dict)

    return final_output


def valueDirected_command(
    key,
    ra_json,
    input_doc_idx,
    page_limiter,
    json_chunking_thresholds,
    job_id,
    input_dict,
):
    anchor_version = "5.2.22112023"
    # 29/07/2022 Minor refactoring done @Emon
    # 08/08/2022 Top/Bottom Anchor Missing Bug Fixed
    # 19/08/2022 Left From the same chunk bug fixed/Comma ruled out from first char
    # 20/08/2022 Adjustments made: If bottom and top is not found on the same page then values are reset
    # 29/08/2022 Checking if same chunk appended twice - cases where line chunking mistake leads to same chunk appearing twice in consecutive lines
    # This variable is set to true when debugging
    # 05/12/2022 - Right anchor in the same chunk disregard flexibility added
    # 06/12/2022 - Both anchor in the same chunk disregard flexiblity added
    # 06/02/2023 - Both anchor trim from the same chunk bug fix, final area rectangle now adjusts with thresholds
    # 11/22/2022 - Bug fixes in extract multiples, Final text area comparison redacted

    debug = True
    # print(json_chunking_thresholds)
    # input_dict = get_redis_data(job_id).get("chunking_dictionary")
    # Getting chunking data from the document in loop
    values = input_dict[str(input_doc_idx)]
    all_data = values["data"]
    data = dict()

    if page_limiter != None:
        for x, y in all_data.items():
            if x == page_limiter:
                # print(x, page_limiter)
                data[x] = y
                break
    else:
        data = all_data

    data_word_only = values["data_word_only"]

    first_page_id = None
    left_th = None
    top_th = None
    right_th = None
    bottom_th = None

    # if anchors data is empty return none
    if not key["anchorShapes"]:
        return None

    # Emon added page limiter for multiple trigger
    if page_limiter == None:
        output_page_index = None
        # if any anchor is there get the pageIdx
        if not output_page_index:
            for anchor_type, anchor_data in key["anchorShapes"].items():
                if "pageIndex" in anchor_data.keys():
                    output_page_index = int(anchor_data["pageIndex"])
                    break
    else:
        output_page_index = page_limiter

    for page, line in all_data.items():
        while not first_page_id:
            for top_pos, chunks in line.items():
                first_page_id = chunks[0][2]

    regular_anchor_search_result = None
    multiple_anchor_search_result = None

    if page_limiter == None:
        regular_anchor_search_result = regular_anchor_search(key, data, page_limiter)

    else:
        multiple_anchor_search_result = multiple_anchor_search(key, data, page_limiter)

    final_output = list()
    if regular_anchor_search_result:
        for result in regular_anchor_search_result:
            extracted_block = extractor(data, result, first_page_id)
            if extracted_block:
                final_output.append(extracted_block)

    if multiple_anchor_search_result:
        for result in multiple_anchor_search_result:
            extracted_block = extractor(data, result, first_page_id)
            if extracted_block:
                final_output.append(extracted_block)

    return final_output, anchor_version
