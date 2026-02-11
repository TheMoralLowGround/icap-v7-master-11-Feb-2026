from . import get_left_pos_str, get_right_pos_str, sort_chunk_data, sorter_func_UT


def process(data, line_data, go_line, left_limit, right_limit):
    line_data = sorter_func_UT.process(line_data)
    go_line_count = 0
    if go_line == 0:
        same_line = data[line_data[2]][line_data[1]]
        for value in same_line:
            text = text + " " + value[0]
    else:
        for key, value in data.items():
            final_text = []
            if key == line_data[2]:
                for key1, value1 in value.items():
                    text = ""
                    if int(key1) > int(line_data[1]):
                        go_line_count = go_line_count + 1
                        if go_line_count > go_line:
                            break
                        else:
                            value1 = sort_chunk_data.process(value1)
                            for j in value1:
                                boundary = j[1]
                                left_pos = get_left_pos_str.process(boundary)
                                right_pos = get_right_pos_str.process(boundary)
                                if (left_pos > left_limit) and (
                                    right_pos < right_limit
                                ):
                                    # go_line_count = go_line_count + 1
                                    text = text + j[0] + " "
                    final_text.append(text.strip())
            return " ".join(final_text)
