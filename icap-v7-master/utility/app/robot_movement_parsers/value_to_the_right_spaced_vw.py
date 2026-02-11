from . import get_left_pos_str, get_right_pos_str, sorter_func


def process(data_word_only, data, find_key_a, find_key_b, line_data):
    empty_check = False
    find_key = find_key_a
    gw_extra = ["Gross", "weight", "Peso", "bruto"]

    def extra_checker(line_data_multi, extra_words):
        return_list = line_data_multi.copy()
        remove_list = []

        if len(extra_words) > 0:
            for i, line_data in enumerate(return_list):
                list_ = []
                for chunk in line_data[0]:
                    word_list = chunk[0].split(" ")
                    for smaller_words in word_list:
                        list_.append(smaller_words)

                if all(word in list_ for word in extra_words):
                    pass
                else:
                    remove_list.append(line_data)
        return_list = [x for x in return_list if x not in remove_list]
        return return_list

    line_data = extra_checker(line_data, gw_extra)
    line_data = sorter_func.process(line_data)

    # print(line_data)
    line_data_chunks = line_data[0][0]

    output_text = ""
    Key_name = ""
    key_right_pos = 0

    # finding the key inside the line_data and deleting chunks to the left
    for chunk in line_data_chunks:
        found = False
        if not found:
            if find_key.lower() in chunk[0].lower():
                Key_name = chunk[0]
                chunk_boundary = chunk[1]
                key_right_pos = get_right_pos_str.process(chunk_boundary)
                line_data_chunks.remove(chunk)

    chunks_to_be_removed = []
    for chunk in line_data_chunks:
        chunk_boundary = chunk[1]
        if get_left_pos_str.process(chunk_boundary) < key_right_pos:
            chunks_to_be_removed.append(chunk)

    line_data_chunks = [
        chunk for chunk in line_data_chunks if chunk not in chunks_to_be_removed
    ]

    horizontal_line_data_chunks = line_data_chunks

    for chunk in horizontal_line_data_chunks:
        output_text = output_text + " " + chunk[0]

    return output_text.strip()
