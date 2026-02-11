"""
@author: Rageeb Noor
"""

import json
import os
import string
import traceback

import spacy
from fuzzywuzzy import fuzz


# Top parse positions (Left, Top, Right, Bottom)
def parse_pos(word_object):
    return [int(coordinate) for coordinate in word_object["pos"].split(",")]


def get_left_pos(word_object):
    return parse_pos(word_object)[0]


def get_right_pos(word_object):
    return parse_pos(word_object)[2]


def get_top_pos(word_object):
    return parse_pos(word_object)[1]


def get_bottom_pos(word_object):
    return parse_pos(word_object)[3]


def check_chunk(range_list, val1, val2, threshold, extra_space=0):
    """
    Check chunk threshold by using right and left pos of 2 object
    """
    val1_right_pos = val1["pos"].split(",")[2]
    val2_left_pos = val2["pos"].split(",")[0]

    val1_top_pos = val1["pos"].split(",")[1]
    val2_top_pos = val2["pos"].split(",")[1]

    difference = abs(int(val1_right_pos) - int(val2_left_pos))

    if threshold_check(int(val1_top_pos), int(val2_top_pos), int(threshold)):
        if int(difference) >= int(range_list[0]) and int(difference) <= (
            int(range_list[1]) + int(extra_space)
        ):
            return True
        else:
            return False
    else:
        return False


def threshold_check(num1, num2, check_threshold):
    """
    Check if the difference between 2 number is less than threshold
    """
    return abs(int(num1) - int(num2)) <= int(check_threshold)


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
        words.append(chunk["v"])

    page_id = chunk_list[0]["id"].split(".")[0]

    return [" ".join(words), ",".join(pos), page_id]


def construct_sentences(word_dict):
    sentences = {}
    for key, word_list in word_dict.items():
        sentence = ""
        for i in range(len(word_list)):
            word, position = word_list[i][0], word_list[i][1]
            sentence += word

            if i < len(word_list) - 1:
                next_left = int(word_list[i + 1][1].split(",")[0])
                current_right = int(position.split(",")[2])
                space_count = max(1, round((next_left - current_right) / 15))
                sentence += " " * space_count

        sentences[key] = sentence
    return sentences


def create_text_files(batch_data_word_only, folder_path):
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for document_id, pages in batch_data_word_only.items():
        for page_id, lines in pages.items():
            # Creating the filename with the folder path
            filename = os.path.join(folder_path, f"{document_id}.{page_id}.txt")

            # Writing lines to the file
            with open(filename, "w", encoding="utf-8") as file:
                for line_id, line_text in lines.items():
                    file.write(line_text + "\n")

            print(f"File created: {filename}")


# Get Batch Level Data
def chunk_process(
    RA_JSON,
    return_type="dict",
    line_threshold=15,
    chunk_threshold=10,
    extra_chunk_space=0,
):
    # Here, we will hold data by document
    batch_data = dict()

    batch_data_word_only = dict()

    # Loop through documents of RA JSON
    for document_index, DOCUMENT in enumerate(RA_JSON["nodes"]):
        data = dict()
        data_word_only = dict()

        # Go through all the XML objects
        for PAGE_ID, PAGE in enumerate(DOCUMENT["children"]):
            # Extract all the W_nodes
            W_nodes = []

            def find_all_words(data):
                if isinstance(data, list):
                    for elem1 in data:
                        find_all_words(elem1)
                elif isinstance(data, dict):
                    for k, v in data.items():
                        if (k == "type") and (v == "word"):
                            W_nodes.append(data)
                        elif isinstance(v, list):
                            find_all_words(v)

            # Find All Word elements and put it into W_nodes
            find_all_words(PAGE["children"])

            # Word are t chunked, each are separated. Need to refactor later
            chunk_data = []

            for chunk in W_nodes:
                chunk_data.append(chunk_node_to_word([chunk]))

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

            for i in sorted_top_pos_holder:
                unique_line_data[str(i)] = []

            # Check for duplicate chunk words, leading to creation of duplicate lines
            prev_positions = set()
            for chunk in chunk_data:
                top_pos = int(chunk[1].split(",")[1])
                for key in unique_line_data.keys():
                    check = threshold_check(int(key), top_pos, line_threshold)
                    if prev_positions:
                        if chunk[1] in prev_positions:
                            check = False
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
                            prev_positions.add(chunk[1])  # using add() for a set

            # Remove if the line is empty
            for i in sorted_top_pos_holder:
                try:
                    if len(unique_line_data[str(i)]) == 0:
                        del unique_line_data[str(i)]

                    # Remove if a line have only a chunk and chunk have only 1 char
                    if len(unique_line_data[str(i)]) == 1:
                        if len(unique_line_data[str(i)][0][0].strip()) == 1:
                            del unique_line_data[str(i)]
                except:
                    pass

            # Sort by left position
            for i in sorted_top_pos_holder:
                try:
                    unique_line_data[str(i)] = sorted(
                        unique_line_data[str(i)], key=lambda left_pos: left_pos[3]
                    )
                except:
                    pass

            for i in sorted_top_pos_holder:
                try:
                    for j in unique_line_data[str(i)]:
                        j.pop()
                except:
                    pass

            # Append to Data Holder
            data[PAGE_ID] = unique_line_data

            unique_line_data_word_only = construct_sentences(unique_line_data)
            data_word_only[PAGE_ID] = unique_line_data_word_only

            batch_data[DOCUMENT["id"]] = data

            batch_data_word_only[DOCUMENT["id"]] = data_word_only

    return batch_data, batch_data_word_only


def generate_text_files():
    batches = os.listdir(batch_folder)

    for batch in batches:
        f = open(batch_folder + "/" + batch, "r")
        RA_JSON = json.loads(f.read())
        f.close()

        batch_data, batch_data_word_only = chunk_process(RA_JSON)

        create_text_files(batch_data_word_only, "awb_texts")


def reconstruct_line_with_spacing(words):
    line_text = ""
    for i, word_info in enumerate(words):
        word = word_info[0]
        line_text += word
        if i < len(words) - 1:
            next_word_info = words[i + 1]
            space_count = calculate_space_count(word_info, next_word_info)
            line_text += " " * space_count
    return line_text


def calculate_space_count(current_word_info, next_word_info):
    # Extract the right position of the current word and the left position of the next word
    current_right = int(current_word_info[1].split(",")[2])
    next_left = int(next_word_info[1].split(",")[0])
    # Calculate the space count based on your specific logic
    space_count = max(1, round((next_left - current_right) / 15))
    return space_count


def map_entities_to_words_in_batch_data(batch_data, id_, nlp):
    entity_word_mapping = {}

    for document_id, pages in batch_data.items():
        if document_id != id_:
            continue
        for page_id, lines in pages.items():
            for line_id, words in lines.items():
                # Reconstruct the line text with accurate spacing and track word boundaries
                (
                    line_text,
                    word_boundaries,
                ) = reconstruct_line_with_spacing_and_boundaries(words)
                # Process the reconstructed text with the SpaCy model
                doc = nlp(line_text)
                for ent in doc.ents:
                    if ent.label_ == "KEY":
                        words_for_entity = find_entity_words_in_line(
                            words, ent, word_boundaries
                        )
                        entity_key = (document_id, page_id, line_id, ent.text)
                        if entity_key not in entity_word_mapping:
                            entity_word_mapping[entity_key] = []
                        entity_word_mapping[entity_key].extend(words_for_entity)

    return entity_word_mapping


def reconstruct_line_with_spacing_and_boundaries(words):
    line_text = ""
    word_boundaries = []
    current_pos = 0

    for i, word_info in enumerate(words):
        word = word_info[0]
        word_start = current_pos
        word_end = word_start + len(word)
        word_boundaries.append((word_start, word_end))

        line_text += word
        current_pos = word_end

        if i < len(words) - 1:
            next_word_info = words[i + 1]
            space_count = calculate_space_count(word_info, next_word_info)
            line_text += " " * space_count
            current_pos += space_count

    return line_text, word_boundaries


def find_entity_words_in_line(words, entity, word_boundaries):
    start_char = entity.start_char
    end_char = entity.end_char

    matched_words = []
    for word, (start, end) in zip(words, word_boundaries):
        if start >= start_char and end <= end_char:
            matched_words.append(word)

    return matched_words


def create_bounding_boxes_for_entities(entity_word_mapping):
    boundary_data = []

    for (
        document_id,
        page_id,
        line_id,
        entity_text,
    ), words in entity_word_mapping.items():
        if not words:
            continue  # Skip if there are no words for the entity

        # Initialize positions with the first word's positions
        left, top, right, bottom = map(int, words[0][1].split(","))

        # The page ID is taken from the last index of the word's information
        page_id = words[0][2]

        # Iterate over the words to find the bounding box
        for word in words[1:]:
            word_left, word_top, word_right, word_bottom = map(int, word[1].split(","))
            left = min(left, word_left)
            top = min(top, word_top)
            right = max(right, word_right)
            bottom = max(bottom, word_bottom)

        boundary_data.append(
            {
                "entity": entity_text,
                "position": f"{left},{top},{right},{bottom}",
                "page_id": page_id,
            }
        )

    return boundary_data


def replace_page_id_string(s, key, first_page_id):
    "this function replaces key to key format of datacap"

    def end_nonzero_int_count(s):  # function added here by emon 04/04/22
        s = s.replace("TM", "")
        count = len(s)
        return count

    key = int(key)
    last_int_count = end_nonzero_int_count(first_page_id)
    last_int = first_page_id[-last_int_count:]
    new_key = str(key + int(last_int))
    new_key_len = len(new_key)

    output = s[:-new_key_len] + new_key

    return output


def get_bottom_pos_of_a_line(input_chunks):
    output = []
    for c in input_chunks:
        output.append(c[1].split(",")[-1])
    return min(output)


def get_value_pos_from_list(input_list):
    all_left = []
    all_top = []
    all_right = []
    all_bottom = []
    for v in input_list:
        all_left.append(int(v.split(",")[0]))
        all_top.append(int(v.split(",")[1]))
        all_right.append(int(v.split(",")[2]))
        all_bottom.append(int(v.split(",")[3]))

    output_left = str(min(all_left))
    output_top = str(min(all_top))
    output_right = str(max(all_right))
    output_bottom = str(max(all_bottom))
    output_pos = (
        output_left + "," + output_top + "," + output_right + "," + output_bottom
    )
    return output_pos


def get_match_ratio(string1, string2):
    return fuzz.WRatio(string1, string2)


def extractor(co_ordinates, pages_data):
    page_id = None
    output_pos_list = list()
    output_list = list()
    key_left, key_top, key_right, key_bottom = co_ordinates
    key_area_height = key_bottom - key_top
    for page_id, lines in pages_data.items():
        for line_key, chunks in lines.items():
            line_bottom = get_bottom_pos_of_a_line(chunks)
            if (
                int(line_key) >= key_top
                and (int(line_key) < key_bottom)
                or (
                    int(line_key) <= key_top
                    and (int(line_key) < key_bottom)
                    and ((int(line_bottom) - key_top) > (0.05 * key_area_height))
                )
            ):
                line_chunk_list = []
                for chunk in chunks:
                    chunk_pos = chunk[1]
                    chunk_text = chunk[0]

                    if not page_id:
                        page_id = chunk[-1]

                    chunk_left = int(chunk_pos.split(",")[0])
                    chunk_right = int(chunk_pos.split(",")[2])
                    allow = False
                    breakout = False
                    if output_pos_list:
                        if output_pos_list[-1] == chunk_pos:
                            breakout = True

                    if not breakout:
                        if key_left and key_right:
                            if (chunk_left >= key_left) and (chunk_right <= key_right):
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

        break

    block_text = ("\n").join(output_list)
    extracted_block = dict()
    extracted_block["text"] = block_text
    extracted_block["pageId"] = page_id
    extracted_block["title"] = "auto"

    try:
        extracted_block["pos"] = get_value_pos_from_list(output_pos_list)
    except:
        extracted_block["pos"] = ""

    return extracted_block


def get_top_line(pages_data, orientation):
    try:
        extracted_block = dict()
        for page_id, lines in pages_data.items():
            for line_key, chunks in lines.items():
                start = chunks[0][1].split(",")[0]
                end = chunks[-1][1].split(",")[2]

                difference = int(end) - int(start)
                midpoint_pixel = difference * 0.7
                if orientation == "left":
                    chunks = [
                        c for c in chunks if int(c[1].split(",")[0]) < midpoint_pixel
                    ]

                if orientation == "right":
                    chunks = [
                        c for c in chunks if int(c[1].split(",")[0]) > midpoint_pixel
                    ]

                line_chunk_list = []
                line_pos_list = []
                line_text = " ".join([chunk[0] for chunk in chunks])
                if "111111" in line_text:
                    continue

                extracted_block["text"] = line_text
                extracted_block["pageId"] = chunks[0][-1]
                extracted_block["title"] = "auto"
                try:
                    extracted_block["pos"] = get_value_pos_from_list(
                        [chunk[1] for chunk in chunks]
                    )
                except:
                    extracted_block["pos"] = ""

                return extracted_block
    except:
        print(traceback.print_exc())
        return {}


def auto_extractor(batch_data, document_id, key_data):
    extracted_block = dict()
    pages_data = None
    for id_, pages in batch_data.items():
        if id_ == document_id:
            pages_data = pages
            break

    if key_data.get("special_arg") == "first_line_left":
        return get_top_line(pages_data, "left")

    if key_data.get("special_arg") == "first_line_right":
        return get_top_line(pages_data, "right")

    # Load the SpaCy model
    nlp = spacy.load("app/key_central/awb_scripts/nlp-model/model-last")
    batch_folder = "ra_json_files"

    # Example usage
    entity_word_mapping = map_entities_to_words_in_batch_data(
        batch_data, document_id, nlp
    )
    # Process
    boundary_datas = create_bounding_boxes_for_entities(entity_word_mapping)

    left_anchor_list = None
    top_anchor_list = None
    bottom_anchor_list = None
    right_anchor_list = None

    try:
        left_anchor_list = key_data.get("left")
    except:
        pass

    try:
        top_anchor_list = key_data.get("top")
    except:
        pass

    try:
        right_anchor_list = key_data.get("right")
    except:
        pass

    try:
        bottom_anchor_list = key_data.get("bottom")
    except:
        pass

    top_position = None
    bottom_position = None
    right_position = None
    key_top = 0
    key_bottom = None
    key_left = 10
    key_right = 2000
    page_index = 0
    debug = False
    prev_left_match_ratio = 0
    prev_top_match_ratio = 0
    prev_right_match_ratio = 0
    prev_bottom_match_ratio = 0

    for boundary_data in boundary_datas:
        position = boundary_data["position"]
        top_skip = False
        left_skip = False
        right_skip = False
        bottom_skip = False
        if top_anchor_list:
            for top_anchor in top_anchor_list:
                if not top_anchor:
                    continue
                top_text = top_anchor.get("text")
                top_th = top_anchor.get("th")
                if top_text:
                    top_match_ratio = get_match_ratio(top_text, boundary_data["entity"])
                    if top_match_ratio > 80:
                        if prev_top_match_ratio:
                            if top_match_ratio <= prev_top_match_ratio:
                                top_skip = True
                        if not top_skip:
                            prev_top_match_ratio = top_match_ratio
                            # print(f"Match ratio of '{top_text}' with '{boundary_data['entity']}': {top_match_ratio}")
                            top_position = position
                            key_top = int(top_position.split(",")[-1])
                            if top_th:
                                key_top += top_th
                        break

        if bottom_anchor_list:
            for bottom_anchor in bottom_anchor_list:
                if not bottom_anchor:
                    continue
                bottom_text = bottom_anchor.get("text")
                bottom_th = bottom_anchor.get("th")
                if bottom_text:
                    bottom_match_ratio = get_match_ratio(
                        bottom_text, boundary_data["entity"]
                    )

                    if bottom_match_ratio > 80:
                        if prev_bottom_match_ratio:
                            if bottom_match_ratio <= prev_bottom_match_ratio:
                                bottom_skip = True
                        if not bottom_skip:
                            prev_bottom_match_ratio = bottom_match_ratio
                            # print(f"Match ratio of '{bottom_text}' with '{boundary_data['entity']}': {bottom_match_ratio}")
                            bottom_position = position
                            key_bottom = int(bottom_position.split(",")[1])
                            if bottom_th:
                                key_bottom += bottom_th
                        break

        if right_anchor_list:
            for right_anchor in right_anchor_list:
                if not right_anchor:
                    continue
                right_text = right_anchor.get("text")
                right_th = right_anchor.get("th")
                right_match_ratio = get_match_ratio(right_text, boundary_data["entity"])

                if right_match_ratio > 80:
                    if prev_right_match_ratio:
                        if right_match_ratio <= prev_right_match_ratio:
                            right_skip = True
                    if not right_skip:
                        prev_right_match_ratio = right_match_ratio
                        # print(f"Match ratio of '{right_text}' with '{boundary_data['entity']}': {right_match_ratio}")
                        right_position = position
                        key_right = int(right_position.split(",")[0])
                        if right_th:
                            key_right += right_th

        if left_anchor_list:
            for left_anchor in left_anchor_list:
                if not left_anchor:
                    continue
                left_text = left_anchor.get("text")
                left_th = left_anchor.get("th")
                left_match_ratio = get_match_ratio(left_text, boundary_data["entity"])
                if left_match_ratio > 80:
                    if prev_left_match_ratio:
                        if left_match_ratio <= prev_left_match_ratio:
                            left_skip = True
                    if not left_skip:
                        prev_left_match_ratio = left_match_ratio
                        # print(f"Match ratio of '{left_text}' with '{boundary_data['entity']}': {left_match_ratio}")
                        left_position = position
                        key_left = int(left_position.split(",")[2])
                        if left_th:
                            key_left += left_th
                    break

    # print("==DESIGNATED AREA===")
    # print(key_left, key_top, key_right, key_bottom)

    if not key_bottom:
        last_page = max([int(x) for x in pages_data.keys()])
        last_page_chunks = pages[last_page]
        last_chunk_top_pos = max([int(x) for x in last_page_chunks.keys()])
        key_bottom = last_chunk_top_pos

    co_ordinates = [key_left, key_top, key_right, key_bottom]
    try:
        extracted_block = extractor(co_ordinates, pages_data)
    except:
        print(traceback.print_exc())

    return extracted_block
