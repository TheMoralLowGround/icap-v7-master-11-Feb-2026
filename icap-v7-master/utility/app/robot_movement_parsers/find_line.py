# function takes in robot file name, batch_id and path as input and generates xml file
def process(data, data_detail, find_key):
    output = ""
    text_key = ""
    page = ""
    pos = ""
    for key, value in data.items():
        for key1, value1 in value.items():
            for elem in value1:
                text = elem
                if find_key in text:  # fuzz.WRatio(text, find_key) > 90:
                    text_key = key1
                    page = key
                    output = data_detail[page][text_key]
                    for j in output:
                        if j[0] == elem:
                            pos = j[1]
                            break
                    break
                else:
                    continue
                break
            else:
                continue
            break
        else:
            continue
        break
    return [[output, text_key, page, pos]]
