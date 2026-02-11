import re


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
