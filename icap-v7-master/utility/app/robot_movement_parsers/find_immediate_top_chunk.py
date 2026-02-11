from . import chunk_sorter, get_left_pos_str, get_right_pos_str


def process(point_right, point_top, data, point_page_id):
    chunk_list = []

    def replace_page_id_string(s, len_, key, data):
        def get_first_page(data):
            first_page = data[0]
            first_key = list(first_page.keys())[0]
            first_page_id = first_page[first_key][0][2]
            return first_page_id

        first_page_id = get_first_page(data)

        def end_nonzero_int_count(s):  # function added here by emon 04/04/22
            s = s.replace("TM", "")
            count = len(s)
            return count

        last_int_count = end_nonzero_int_count(first_page_id)
        last_int = first_page_id[-last_int_count:]
        new_key = str(key + int(last_int))
        new_key_len = len(new_key)

        "this function replaces key to key format of datacap"
        output = s[:-new_key_len] + new_key

        return output

    for key, value in data.items():
        page_no_format = "TM000000"
        len_ = len(str(key))
        renewed_page_no_string = replace_page_id_string(page_no_format, len_, key, data)
        if renewed_page_no_string == point_page_id:
            for top, line_chunks in value.items():
                if int(top) < point_top:
                    line_chunks = chunk_sorter.process(line_chunks)
                    chunk = line_chunks[0]
                    chunk_left = get_left_pos_str.process(chunk[1])
                    if chunk_left <= point_right:
                        chunk_list.append(
                            [chunk[0], get_right_pos_str.process(chunk[1])]
                        )
    # print(chunk_list)
    return chunk_list[-1][0]
