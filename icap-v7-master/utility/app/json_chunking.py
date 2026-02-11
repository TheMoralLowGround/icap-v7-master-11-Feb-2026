"""
JSON Chunking Processor
=======================

Overview:
---------
This script processes a JSON structure to extract and organize text chunks 
based on positional attributes (POS). It utilizes thresholds and spatial 
relationships between words to group them into meaningful chunks and lines. 
The output includes structured text data with positional metadata and a word-only version.

Key Components:
---------------
1. **Functions**:
   - `threshold_check`: Determines if the difference between two numbers is within a given threshold.
   - `check_chunk`: Validates if two text elements are spatially close enough to belong to the same chunk.
   - `chunk_node_to_word`: Converts a list of chunked nodes into a single string, along with positional and page metadata.
   - `get_*_pos`: Retrieves specific positional attributes (e.g., left, top, right, bottom) from a text element's POS string.
   - `json_chunking_main`: Main function to process the input JSON, extract text chunks, and organize them into structured lines.

2. **Threshold Parameters**:
   - `chunkThreshold`: Determines the spatial proximity required for words to belong to the same chunk.
   - `extraChunkSpace`: Additional space allowance for chunking.
   - `lineThreshold`: Vertical distance threshold for grouping chunks into lines.

3. **Processing Workflow**:
   - Extracts `w_nodes` (word nodes) from the input JSON.
   - Groups word nodes into chunks based on their proximity and thresholds.
   - Sorts chunks into lines based on their vertical positions.
   - Outputs structured data (`data`) and word-only data (`data_word_only`).

Execution Flow:
---------------
1. **Input**:
   - `input_ra_json`: JSON structure containing text data with positional attributes.
   - `json_chunking_thresholds`: Configuration for chunking and line thresholds.

2. **Processing**:
   - Loops through documents in the JSON, skipping non-supported formats (e.g., `.xlsx`).
   - Extracts and organizes text data into chunks and lines using spatial logic.
   - Handles specific document types (e.g., "Airway Bill") using custom processing rules.

3. **Output**:
   - A dictionary containing structured data (`data`) and word-only data (`data_word_only`) for each page in each document.

Input Example:
--------------
```json
{
    "nodes": [
        {
            "ext": ".pdf",
            "Vendor": "VendorName",
            "DocType": "DocumentType",
            "children": [
                {
                    "type": "page",
                    "children": [
                        {"type": "word", "v": "example", "pos": "10,20,30,40", "id": "1.1"}
                    ]
                }
            ]
        }
    ],
    "DocumentType": "Airway Bill"
}
"""
import traceback

from .common_dictionary import unwanted_chars

try:
    from airway_bill.unnecessary_value_removalAWB import unnecessary_value_removal
except:
    pass


def threshold_check(num1, num2, check_threshold):
    """
    Check threshold of 2 value
    """
    threshold = abs(num1 - num2)

    if threshold <= check_threshold:
        return True
    else:
        return False


def check_chunk(range_list, val1, val2, threshold, extra_space=0):
    """
    Check chunk threshold by using right and left pos of 2 object
    """
    val1_right_pos = val1["pos"].split(",")[2]
    val2_left_pos = val2["pos"].split(",")[0]

    val1_top_pos = val1["pos"].split(",")[1]
    val2_top_pos = val2["pos"].split(",")[1]

    difference = abs(int(val1_right_pos) - int(val2_left_pos))

    if threshold_check(int(val1_top_pos), int(val2_top_pos), threshold):
        if (difference >= range_list[0]) and (
            difference <= (range_list[1] + extra_space)
        ):
            return True
        else:
            return False
    else:
        return False


def chunk_node_to_word(chunk_list):
    """
    Convert Chunks data(with POS) to Word only
    """
    words = []

    pos = [
        get_left_pos(chunk_list[0]),
        get_top_pos(chunk_list[0]),
        get_right_pos(chunk_list[-1]),
        get_bottom_pos(chunk_list[0]),
    ]

    pos = [str(x) for x in pos]

    for chunk in chunk_list:
        v = chunk["v"]
        for c in unwanted_chars:
            if c in v:
                v = v.replace(c, "")
        words.append(chunk["v"])

    page_id = chunk_list[0]["id"].split(".")[0]

    return [" ".join(words), ",".join(pos), page_id]


def get_left_pos(xml_object):
    """
    Get Left POS from POS attributes which is first one. Ex. (12,43,12,43)
    Will return 12
    """
    return int(xml_object["pos"].split(",")[0])


def get_right_pos(xml_object):
    """
    Get Right POS from POS attributes which is first one. Ex. (12,43,12,43)
    Will return 12
    """
    return int(xml_object["pos"].split(",")[2])


def get_top_pos(xml_object):
    """
    Get Top POS from POS attributes which is second one. Ex. (12,43,12,43)
    Will return 43
    """
    return int(xml_object["pos"].split(",")[1])


def get_bottom_pos(xml_object):
    """
    Get Top POS from POS attributes which is last one. Ex. (12,43,12,43)
    Will return 43
    """
    return int(xml_object["pos"].split(",")[3])


def get_node_value(xml_object):
    """
    Get Value from "v" attribute
    """
    return xml_object["v"]


def get_node_pos(xml_object):
    """
    Get Pos from Node
    """
    return xml_object["pos"]


def get_left_pos_str(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos_str(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos_str(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos_str(pos):
    return int(pos.split(",", 3)[3])


def json_chunking_main(input_ra_json, json_chunking_thresholds):
    # Reading from file
    # FULL_JSON_DATA = f

    # print(type(f))

    # Set batch it
    # batch_id = FULL_JSON_DATA['id']

    # Table Definition or Configuration File
    # json_config = FULL_JSON_DATA['definitions']

    # RA JSON DATA
    # RA_JSON = FULL_JSON_DATA['ra_json']

    RA_JSON = input_ra_json
    doc_type = RA_JSON.get("DocumentType")

    output_dict = {}

    for document_index, DOCUMENT in enumerate(RA_JSON["nodes"]):
        if DOCUMENT.get("ext") == ".xlsx":
            output_dict[document_index] = {"data": {}, "data_word_only": {}}
            continue

        # Get Vendor ID otherwise raise Error
        try:
            Vendor = DOCUMENT["Vendor"]
        except:
            raise Exception("Error! Can't find the Vendor")

        # Get Document Type
        TYPE = DOCUMENT["DocType"]

        # # Filter table definition with Vendor
        # for key_num in range(len(json_config)):
        #     definition =  json_config[key_num]

        #     if (definition['vendor'].lower() == Vendor.lower()) and (definition['type'].lower() == TYPE.lower()):
        #         json_config_data = definition['table']

        #         break

        # If didn't find any column configuration, it will throw error
        # try:
        #     column_config = json_config_data['columns']
        # except NameError:
        #     raise Exception("Didn't find column configuration for this purchasers: "+str(Vendor))

        # Here we will hold data with chunking line also word only version
        data = dict()
        data_word_only = dict()

        # Go through all the XML objects
        for PAGE_ID, PAGE in enumerate(DOCUMENT["children"]):
            # Extract all the w_nodes
            w_nodes = []

            skip_word_finds = False

            if doc_type == "Airway Bill":
                try:
                    w_nodes = unnecessary_value_removal(RA_JSON)
                    skip_word_finds = True
                except:
                    # print(traceback.print_exc())
                    pass

            def find_all_words(data):
                if isinstance(data, list):
                    for elem1 in data:
                        find_all_words(elem1)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if (k == "type") and (v == "word"):
                            w_nodes.append(data)
                        elif isinstance(v, list):
                            find_all_words(v)

            if not skip_word_finds:
                # Find All Word elements and put it into w_nodes
                find_all_words(PAGE["children"])

            if not w_nodes:
                continue

            # Turn All the Data into Lines with Chuncking
            word_space_list = []

            for index, W_node in enumerate(w_nodes):
                try:
                    current_node_pos = W_node["pos"]

                    if not current_node_pos:
                        next_pos = w_nodes[index - 1]["pos"]
                        next_char_length = len(w_nodes[index - 1])
                        next_horizontal_length = get_right_pos_str(
                            next_pos
                        ) - get_left_pos_str(next_pos)
                        curr_char_length = len(W_node)
                        curr_horizontal_length = (
                            next_horizontal_length * curr_char_length
                        ) / next_char_length
                        left_pos = str(
                            int(
                                get_left_pos_str(next_pos)
                                + (curr_horizontal_length / 2)
                            )
                        )
                        right_pos = str(
                            int(get_right_pos_str(next_pos) + (curr_char_length / 2))
                        )
                        current_node_pos = (
                            left_pos
                            + ","
                            + str(get_top_pos_str(next_pos))
                            + ","
                            + right_pos
                            + ","
                            + str(get_bottom_pos_str(next_pos))
                        )
                        W_node["pos"] = current_node_pos

                    current_node_right_pos = current_node_pos.split(",")[2]

                    next_node_pos = w_nodes[index + 1]["pos"]

                    if not next_node_pos:
                        prev_pos = current_node_pos
                        prev_char_length = len(w_nodes[index + 1])
                        prev_horizontal_length = get_right_pos_str(
                            prev_pos
                        ) - get_left_pos_str(prev_pos)
                        curr_char_length = len(W_node)
                        curr_horizontal_length = (
                            prev_horizontal_length * curr_char_length
                        ) / prev_char_length
                        left_pos = str(
                            int(
                                get_left_pos_str(prev_pos)
                                - (curr_horizontal_length / 2)
                            )
                        )
                        right_pos = str(
                            int(get_right_pos_str(prev_pos) - (curr_char_length / 2))
                        )
                        next_node_pos = (
                            left_pos
                            + ","
                            + str(get_top_pos_str(prev_pos))
                            + ","
                            + right_pos
                            + ","
                            + str(get_bottom_pos_str(prev_pos))
                        )

                    next_node_left_pos = next_node_pos.split(",")[0]
                    diffr = int(next_node_left_pos) - int(current_node_right_pos)

                    if diffr < 0:
                        pass
                    else:
                        word_space_list.append(diffr)

                except IndexError:
                    pass
            try:
                # Only if there is only 1 word #Added by rageeb on 14/10/2022
                if (len(w_nodes) == 1) and word_space_list == []:
                    word_space_list = [5]
            except:
                pass

            space_list = sorted(list(set(word_space_list)))
            try:
                space_range = [space_list[0], space_list[0] + 20]
            except:
                space_range = [15, 35]

            """
            Make Chunks
            """
            chunk_list = []

            start_idx = 0
            end_idx = len(w_nodes)

            while True:
                temp_chunk = []

                while True:
                    try:
                        chunkTH, extra_chunk_space, line_threshold = 15, 0, 10
                        try:
                            if json_chunking_thresholds:
                                if (
                                    json_chunking_thresholds.get("chunkThreshold")
                                    != None
                                ):
                                    chunkTH = int(
                                        json_chunking_thresholds["chunkThreshold"]
                                    )
                                if (
                                    json_chunking_thresholds.get("extraChunkSpace")
                                    != None
                                ):
                                    extra_chunk_space = int(
                                        json_chunking_thresholds["extraChunkSpace"]
                                    )
                                if (
                                    json_chunking_thresholds.get("lineThreshold")
                                    != None
                                ):
                                    line_threshold = int(
                                        json_chunking_thresholds["lineThreshold"]
                                    )
                        except:
                            print(traceback.print_exc())
                            pass

                        check = check_chunk(
                            space_range,
                            w_nodes[start_idx],
                            w_nodes[start_idx + 1],
                            chunkTH,
                            extra_chunk_space,
                        )
                    #
                    except IndexError:
                        start_idx = start_idx + 1
                        if start_idx >= end_idx:
                            temp_chunk.append(w_nodes[start_idx - 1])
                        break

                    if check == True:
                        temp_chunk.append(w_nodes[start_idx])

                        start_idx = start_idx + 1
                    else:
                        temp_chunk.append(w_nodes[start_idx])
                        start_idx = start_idx + 1
                        break

                if temp_chunk != []:
                    chunk_list.append(temp_chunk)

                if start_idx >= end_idx:
                    break

            chunk_data = []

            for chunk in chunk_list:
                chunk_data.append(chunk_node_to_word(chunk))

            """
            Turn Data into Proper Lines
            """

            left_pos_holder = []
            top_pos_holder = []

            for chunk in chunk_data:
                left_pos_holder.append(int(chunk[1].split(",")[0]))

                top_pos_holder.append(int(chunk[1].split(",")[1]))

            sorted_top_pos_holder = sorted(set(top_pos_holder))

            # Extra Check Threshold 5 times
            for _ in range(5):
                for index, i in enumerate(sorted_top_pos_holder):
                    if index != 0:
                        check = threshold_check(
                            sorted_top_pos_holder[index],
                            sorted_top_pos_holder[index - 1],
                            line_threshold,
                        )
                        if check:
                            sorted_top_pos_holder.remove(i)

            unique_line_data = dict()
            unique_line_word_only = dict()

            for i in sorted_top_pos_holder:
                unique_line_data[str(i)] = []
                unique_line_word_only[str(i)] = []

            for chunk in chunk_data:
                top_pos = int(chunk[1].split(",")[1])
                for key in unique_line_data.keys():
                    check = threshold_check(int(key), top_pos, line_threshold)
                    if check:
                        if chunk[0].strip() != "":
                            unique_line_data[key].append(
                                [
                                    chunk[0],
                                    chunk[1],
                                    chunk[2],
                                    int(chunk[1].split(",")[0]),
                                ]
                            )
                            unique_line_word_only[key].append(chunk[0])

            # Remove if the line is empty
            for i in sorted_top_pos_holder:
                if len(unique_line_data[str(i)]) == 0:
                    del unique_line_data[str(i)]
                    del unique_line_word_only[str(i)]

            # Modified by emon on 07/02/2023
            # Sort by left position
            for i in sorted_top_pos_holder:
                try:
                    # try except added as keyError here lead to no data being extracted
                    unique_line_data[str(i)] = sorted(
                        unique_line_data[str(i)], key=lambda left_pos: left_pos[3]
                    )
                except:
                    pass

            for i in sorted_top_pos_holder:
                try:
                    for j in unique_line_data[str(i)]:
                        try:
                            j.pop()
                        except:
                            pass
                except:
                    pass

            # Append to Data Holder
            data[PAGE_ID] = unique_line_data
            data_word_only[PAGE_ID] = unique_line_word_only

        output_dict[document_index] = {"data": data, "data_word_only": data_word_only}

        # return data, data_word_only
    return output_dict
