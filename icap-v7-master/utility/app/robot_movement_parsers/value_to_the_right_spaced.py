from . import find_line, get_left_pos_str, get_right_pos_str


def process(data_word_only, data, find_key_a, find_key_b):
    empty_check = False
    line_data = find_line.process(data_word_only, data, find_key_a)
    find_key = find_key_a
    try:
        if all("" == s or s.isspace() for s in line_data[0][0]):
            empty_check = True

        if empty_check:
            line_data = find_line.process(data_word_only, data, find_key_b)
            find_key = find_key_b
    except:
        pass

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
