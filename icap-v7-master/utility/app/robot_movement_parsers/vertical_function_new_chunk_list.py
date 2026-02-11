from . import sort_chunk_data


def process(data, line_data, go_line):
    text_list = []
    text = ""
    go_line_count = 0
    if go_line == 0:
        for line_idx in line_data:
            line_text_list = []
            same_line = data[line_idx[2]][line_idx[1]]

            for value in same_line:
                line_text_list.append(value[0])
            text_list.append(line_text_list)

    else:
        for key, value in data.items():
            for line_idx in line_data:
                if key == line_idx[2]:
                    for key1, value1 in value.items():
                        value1 = sort_chunk_data.process(value1)
                        if int(key1) > int(line_idx[1]):
                            line_text_list = []
                            go_line_count = go_line_count + 1
                            if go_line_count > go_line:
                                break
                            else:
                                for j in value1:
                                    # go_line_count = go_line_count + 1
                                    line_text_list.append(j[0])

                            text_list.append(line_text_list)

    return text_list
