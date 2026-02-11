import re
import traceback


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


def process(string):
    # Version 5.0.10102022
    # Emon on 10/10/2022 made kg to KGM change
    try:
        # added by Almas
        try:
            if "/" in string:
                if "kg" in string.lower():
                    if "lb" or "1b" in string.lower():
                        string = string.split("/")[0]
        except:
            pass

        # added by emon
        try:
            if str_to_shape(string) == "XXbDDD":
                string = string.replace(".", " ")
        except:
            pass

        split_at = 0
        for idx, c in enumerate(string):
            if c.isalpha():
                split_at = idx
                break

        uom_string = string[split_at:]
        uom_string_split = uom_string.split()
        uom = ""
        extra_data_list = []
        for x_idx, x in enumerate(uom_string_split):
            if (len(x)) > 3:
                for extra in uom_string_split[x_idx:]:
                    extra_data_list.append(extra)
                break

            elif not x[0].isdigit():
                uom += x

        new_string = string.replace(uom, "").strip()

        number_char_idx_val_list = []
        number = ""
        for c_idx, c in enumerate(new_string):
            if c == "," or c == "." or c.isdigit():
                number_char_idx_val_list.append([c_idx, c])

        for list_idx, [c_idx, c] in enumerate(number_char_idx_val_list):
            # print(number_char_idx_val_list)
            if (c == ".") or (c == ","):
                if (c_idx - (c_idx - 1)) == 1 and (
                    (list_idx + 1) != len(number_char_idx_val_list)
                ):
                    number += c
            else:
                number += c

        extra_data = None

        if extra_data_list:
            extra_data = " ".join(extra_data_list)

        if extra_data:
            if (uom.strip().lower() in extra_data.lower()) or (
                number.strip() in extra_data
            ):
                extra_data = None

        if (
            uom == ""
            or uom == "'"
            or uom == ","
            or uom.lower() == "kgs"
            or uom.lower() == "kg"
            or uom.lower() == "kgm"
            or uom.lower() == "kg:"
        ):
            uom = "KGM"

        if number and uom:
            # Replacing decimal in uom
            if "." in uom:
                uom = uom.replace(".", "")

            if uom.lower() == "kg":
                uom = "KGM"
            return [number, uom.upper(), extra_data]

        else:
            return [string]
    except:
        print(traceback.print_exc())
        return [string]
