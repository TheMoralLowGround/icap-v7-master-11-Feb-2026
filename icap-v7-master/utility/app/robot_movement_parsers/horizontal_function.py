def process(data, line_data, goline):
    text_list = []
    for key, value in data.items():
        for line_idx in line_data:
            if key == line_idx[2]:
                text = ""
                for key1, value1 in value.items():
                    if int(key1) == int(line_idx[1]):
                        for sub_value in value1:
                            text = text + " " + sub_value[0]
                        text_list.append(text)
    return text_list
