def process(data, data_detail, find_key):
    output_multi_list = []
    output = ""
    text_key = ""
    page = ""
    for key, value in data.items():
        for key1, value1 in value.items():
            for elem in value1:
                text = elem
                if find_key in text:  # fuzz.WRatio(text, find_key) > 90:
                    text_key = key1
                    page = key
                    output = data_detail[page][text_key]
                    pos = ""
                    for j in output:
                        if j[0] == elem:
                            pos = j[1]
                            output_multi_list.append([output, text_key, page, pos])
    return output_multi_list
