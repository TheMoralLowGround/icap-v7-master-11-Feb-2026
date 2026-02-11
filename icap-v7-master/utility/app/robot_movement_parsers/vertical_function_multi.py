from . import sort_chunk_data, sorter_func


def process(data, line_data, go_line):
    line_data = sorter_func.process(line_data)
    go_line_count = 0
    if go_line == 0:
        for line_idx in line_data:
            same_line = data[line_idx[2]][line_idx[1]]
            for value in same_line:
                text = text + " " + value[0]
    else:
        for key, value in data.items():
            for line_idx in line_data:
                if key == line_idx[2]:
                    for key1, value1 in value.items():
                        text = ""
                        if int(key1) > int(line_idx[1]):
                            go_line_count = go_line_count + 1
                            if go_line_count > go_line:
                                break
                            else:
                                value1 = sort_chunk_data.process(value1)
                                for j in value1:
                                    # go_line_count = go_line_count + 1
                                    text = text + j[0] + " "
                            return text
