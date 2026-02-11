from . import clean_line_blocks


def process(data, line_data, go_line):
    """this function takes the horizontal first line of the block
    and then returns rest of the block lines"""
    text_list = []
    text = ""
    go_line_count = 0
    if go_line == 0:
        for line_idx in line_data:
            same_line = data[line_idx[2]][line_idx[1]]
            same_line = clean_line_blocks.process(same_line)
            for value in same_line:
                text = text + value[0]
    else:
        for key, value in data.items():
            for line_idx in line_data:
                if key == line_idx[2]:
                    for key1, value1 in value.items():
                        if int(key1) > int(line_idx[1]):
                            value1 = clean_line_blocks.process(value1)
                            go_line_count = go_line_count + 1
                            if go_line_count > go_line:
                                break
                            else:
                                multiple_chunk = ""
                                for j in value1:
                                    multiple_chunk = multiple_chunk + " " + j[0]
                                    # go_line_count = go_line_count + 1

                                    if "\n\r" in text:
                                        text = text + multiple_chunk
                                    else:
                                        text = text + multiple_chunk + "\n\r"
    text_list.append(text)
    return text_list
