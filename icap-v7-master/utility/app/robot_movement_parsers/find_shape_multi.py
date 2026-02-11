import re

from . import get_left_pos_str

# version : 1.14102022


def str_to_shape(string):
    """
    Converts string into Shape
    """
    convert_string = []
    for i in string:
        if re.findall("[A-Z]", i):
            convert_string.append("X")
        elif re.findall("[a-z]", i):
            convert_string.append("x")
        elif re.findall("[0-9]", i):
            convert_string.append("D")
        elif i == ".":
            convert_string.append("b")
        elif i == ",":
            convert_string.append("c")
        elif i == ":":
            convert_string.append("y")
        else:
            convert_string.append(i)

    return "".join(convert_string)


def sorter(line):
    left_poses = []
    for lin in line:
        left_poses.append(get_left_pos_str.process(lin[1]))
    left_poses.sort()
    line_new = []
    for y in left_poses:
        for lin in line:
            if y == get_left_pos_str.process(lin[1]):
                line_new.append(lin[0])
    # print(line_new)
    return line_new


def process(data, data_detail, find_key):
    output_multi_list = []
    output = ""
    text_key = ""
    page = ""
    for key, value in data_detail.items():
        for key1, value1 in value.items():
            value1 = sorter(value1)
            # print(value1)
            key_list = [str_to_shape(x) for x in value1]

            if len(key_list) > 2:
                key_list = key_list[:3]

                if key_list == find_key:
                    # print(key_list)
                    output_multi_list.append(value1)
    return output_multi_list
