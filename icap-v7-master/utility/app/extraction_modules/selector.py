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
import string
import traceback

from ..json_chunking import json_chunking_main


def get_left_pos(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos(pos):
    return int(pos.split(",", 3)[3])


def replace_page_id_string(s, key, first_page_id):
    "this function replaces key to key format of datacap"

    def end_nonzero_int_count(s):  # function added here by emon 04/04/22
        s = s.replace("tm", "").replace("TM","")
        count = len(s)
        return count

    key = int(key)
    last_int_count = end_nonzero_int_count(first_page_id)
    last_int = first_page_id[-last_int_count:]
    new_key = str(key + int(last_int))
    new_key_len = len(new_key)

    output = s[:-new_key_len] + new_key

    return output


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


def get_bottom_pos_of_a_line(input_chunks):
    output = []
    for c in input_chunks:
        output.append(get_bottom_pos(c[1]))
    return min(output)


def selector_function(key, doc_idx_in_loop, job_id, input_dict):
    selector_version = "5.0.10072023"
    # @Emon on 18/10/2022 - Checking if same chunk repeated twice or not
    values = input_dict[str(doc_idx_in_loop)]
    data = values["data"]
    first_page_id = None
    output_pos_list = []

    for page, line in data.items():
        if not first_page_id:
            for top_pos, chunks in line.items():
                first_page_id = chunks[0][2]

    if ("|") in key["shape"]:
        pipe_count = key["shape"].split("|")
        pipe_found = False
        if not pipe_found:
            for pipe_idx, pipe in enumerate(pipe_count):
                pipe_page_id = key["pageId"].split("|")[pipe_idx]
                key_left = int(
                    round(float(key["startPos"].strip().split("|")[pipe_idx]))
                )
                key_top = int(round(float(key["topPos"].strip().split("|")[pipe_idx])))
                key_right = int(
                    round(float(key["endPos"].strip().split("|")[pipe_idx]))
                )
                key_bottom = int(
                    round(float(key["bottomPos"].strip().split("|")[pipe_idx]))
                )
                key_area_height = key_bottom - key_top
                output_list = []
                for page, line in data.items():
                    page_no_format = "TM000000"
                    renewed_page_no_string = replace_page_id_string(
                        page_no_format, page, first_page_id
                    )
                    try:
                        if "pageIndex" in key.keys():
                            pipe_page_index = key["pageIndex"].split("|")[pipe_idx]
                            pipe_page_id = int(pipe_page_index)
                            renewed_page_no_string = int(page)
                    except:
                        pass
                    if renewed_page_no_string == pipe_page_id:
                        for line_key, chunks in line.items():
                            line_bottom = get_bottom_pos_of_a_line(chunks)
                            if (
                                int(line_key) >= key_top
                                and (int(line_key) < key_bottom)
                            ) or (
                                int(line_key) <= key_top
                                and (int(line_key) < key_bottom)
                                and ((line_bottom - key_top) > (0.05 * key_area_height))
                            ):
                                found_in_page = replace_page_id_string(
                                    page_no_format, page, first_page_id
                                )
                                line_chunk_list = list()
                                for chunk in chunks:
                                    chunk_pos = chunk[1]
                                    chunk_text = chunk[0]
                                    chunk_left = get_left_pos(chunk_pos)
                                    chunk_right = get_right_pos(chunk_pos)
                                    breakout = False

                                    if output_pos_list:
                                        if output_pos_list[-1] == chunk_pos:
                                            breakout = True
                                    allow = False
                                    if not breakout:
                                        if (chunk_left >= key_left) and (
                                            chunk_right <= key_right
                                        ):
                                            allow = True
                                        elif (
                                            (chunk_left >= key_left)
                                            and (chunk_right >= key_right)
                                            and (chunk_left < key_right)
                                        ):
                                            allow = True
                                        elif (
                                            (chunk_left <= key_left)
                                            and (chunk_right >= key_right)
                                            and (chunk_left < key_right)
                                        ):
                                            allow = True
                                        else:
                                            pass
                                    if allow:
                                        line_chunk_list.append(chunk_text)
                                        output_pos_list.append(chunk_pos)

                                line_text = (" ").join(line_chunk_list)
                                if line_text:
                                    output_list.append(line_text)

                if output_list:
                    # print(output_list)
                    pipe_found = True
                    block_text = ("\n").join(output_list)
                    block_boundary = (
                        str(key_left)
                        + ","
                        + str(key_top)
                        + ","
                        + str(key_right)
                        + ","
                        + str(key_bottom)
                    )
                    try:
                        page_id = found_in_page
                    except:
                        found_in_page = ""
                        page_id = found_in_page
                    title = "selector"
                    output = dict()
                    output["text"] = block_text.strip()
                    output["pos"] = block_boundary
                    output["pageId"] = page_id
                    output["title"] = title
                    return output, selector_version
                # return None
    else:
        try:
            key_left = int(round(float(key["startPos"])))
            key_top = int(round(float(key["topPos"])))
            key_right = int(round(float(key["endPos"])))
            key_bottom = int(round(float(key["bottomPos"])))
            key_page_id = key["pageId"]
            value_page_id = key["pageId"]
            key_area_height = key_bottom - key_top

            output_list = []
            for page, line in data.items():
                page_no_format = "TM000000"
                renewed_page_no_string = replace_page_id_string(
                    page_no_format, page, first_page_id
                )
                try:
                    if "pageIndex" in key.keys():
                        key_page_id = int(key["pageIndex"])
                        renewed_page_no_string = int(page)
                except:
                    pass

                if renewed_page_no_string == key_page_id:
                    for line_key, chunks in line.items():
                        line_bottom = get_bottom_pos_of_a_line(chunks)
                        if (
                            int(line_key) >= key_top
                            and (int(line_key) < key_bottom)
                            or (
                                int(line_key) <= key_top
                                and (int(line_key) < key_bottom)
                                and (
                                    (int(line_bottom) - key_top)
                                    > (0.05 * key_area_height)
                                )
                            )
                        ):
                            value_page_id = replace_page_id_string(
                                page_no_format, page, first_page_id
                            )
                            line_chunk_list = list()
                            for chunk in chunks:
                                chunk_pos = chunk[1]
                                chunk_text = chunk[0]
                                chunk_left = get_left_pos(chunk_pos)
                                chunk_right = get_right_pos(chunk_pos)
                                allow = False
                                breakout = False
                                if output_pos_list:
                                    if output_pos_list[-1] == chunk_pos:
                                        breakout = True

                                if not breakout:
                                    if (chunk_left >= key_left) and (
                                        chunk_right <= key_right
                                    ):
                                        allow = True
                                    elif (
                                        (chunk_left >= key_left)
                                        and (chunk_right >= key_right)
                                        and (chunk_left < key_right)
                                    ):
                                        allow = True
                                    elif (
                                        (chunk_left <= key_left)
                                        and (chunk_right >= key_right)
                                        and (chunk_left < key_right)
                                    ):
                                        allow = True
                                    else:
                                        pass

                                if allow:
                                    line_chunk_list.append(chunk_text)
                                    output_pos_list.append(chunk_pos)

                            if line_chunk_list != []:
                                line_text = (" ").join(line_chunk_list)
                                if not all(i in string.punctuation for i in line_text):
                                    output_list.append(line_text)

            block_text = ("\n").join(output_list)
            title = "selector"
            page_id = value_page_id
            try:
                block_boundary = get_value_pos_from_list(output_pos_list)
            except:
                # print(traceback.print_exc())
                block_boundary = (
                    str(key_left)
                    + ","
                    + str(key_top)
                    + ","
                    + str(key_right)
                    + ","
                    + str(key_bottom)
                )

            output = dict()
            output["text"] = block_text.strip()
            output["pos"] = block_boundary
            output["pageId"] = page_id
            output["title"] = title

            if output["text"]:
                return output, selector_version
            return None, selector_version
        except:
            print(traceback.print_exc())
            pass
