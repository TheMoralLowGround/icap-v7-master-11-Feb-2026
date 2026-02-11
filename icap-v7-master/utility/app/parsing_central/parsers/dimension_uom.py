def old_parser_process(full_sentence):
    try:

        def single_dimension_checker(sentence):
            try:
                sentence = sentence.strip()
                # key_part = sentence.split(":")[0]
                value_part = sentence.strip()
                length = width = height = uom = extra_data = None
                dimension_separator = None
                type_separator = None
                package_count = package_type = None
                innerPackageCount = innerPackageType = None
                grossWeight = grossWeightUom = None
                string_of_separators = """"xX@*+-—/'\~"""
                common_package_type_list = ["ctn", "plt"]
                if (
                    sentence[-1] == "+"
                ):  # removing the last index if it's a separator (e.g., "2x 115x140x92cm +")
                    sentence = sentence[:-1].strip()
                    value_part = value_part[:-1].strip()
                separator_list = []

                # finding separators
                for i in range(len(value_part)):
                    if value_part[i] in string_of_separators and (
                        value_part[i - 1] == " "
                        or value_part[i - 1] in "0123456789IilZBSb"
                    ):
                        separator_list.append(value_part[i])
                    # fixing OCR issues for same separator and value (e.g., 31x1Xx21)
                    elif value_part[i] == "x" and value_part[i - 1] == "X":
                        # separator_list.append(value_part[i])
                        dimension_separator = "x"

                # handling dimensions with no separators or with only one type separator (e.g., "120 120 188" or "120 120 188 - 3 pallets")
                if (len(sentence.split(" ")) == 3 and separator_list == []) or (
                    len(separator_list) == 1 and separator_list[0] == "-"
                ):
                    sentence_list = sentence.split(" ")
                    length = sentence_list[0].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[2].strip()
                    uom = "CMT"
                    if len(sentence_list) == 3:
                        output_list = [length, width, height, uom, extra_data]
                        return output_list
                    elif len(sentence_list) == 6:
                        package_count = sentence_list[4].strip()
                        package_type = sentence_list[5].strip()
                        output_list = [
                            length,
                            width,
                            height,
                            uom,
                            extra_data,
                            package_count,
                            package_type,
                        ]
                        return output_list
                # handling dimensions with no separators and exceptional cases (e.g., "1 31 27 48")
                if len(sentence.split(" ")) == 4 and separator_list == []:
                    sentence_list = sentence.split(" ")
                    package_count = sentence_list[0].strip()
                    length = sentence_list[1].strip()
                    width = sentence_list[2].strip()
                    height = sentence_list[3].strip()
                    uom = "CMT"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                    ]
                    return output_list
                # handling dimensions with no separators and exceptional cases (e.g., "Karton 63 55 47 CM")
                if len(sentence.split(" ")) == 5 and separator_list == []:
                    sentence_list = sentence.split(" ")
                    length = sentence_list[1].strip()
                    width = sentence_list[2].strip()
                    height = sentence_list[3].strip()
                    uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling dimensions with no separators and exceptional cases with 3 cms (e.g., "134.00 cm 92.00 cm 137.00 cm")
                if sentence.count("cm") == 3 and separator_list == []:
                    value_list = value_part.split("cm")
                    if "" in value_list:
                        value_list.remove("")
                    length = value_list[0].strip()
                    width = value_list[1].strip()
                    height = value_list[2].strip()
                    uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling dimensions with no separators (e.g. "Length 47 Width 20 Height 20 CM")
                if separator_list == []:
                    value_list = value_part.split(" ")
                    for i in range(len(value_list)):
                        if value_list[i].lower() == "length":
                            length = value_list[i + 1]
                        if value_list[i].lower() == "width":
                            width = value_list[i + 1]
                        if value_list[i].lower() == "height":
                            height = value_list[i + 1]
                    uom = value_list[-1].upper()
                    if uom == "CM":
                        uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # hadling dimensions with 3 same separators (e.g., "1 x120 x80 x 195" or "2x 115x140x92cm" or "6x(1.90x0.95x1.80)")
                if (
                    len(separator_list) == 3
                    and separator_list[0] == separator_list[1] == separator_list[2]
                ):
                    if "(" in value_part and ")" in value_part:
                        value_part = value_part.replace("(", "")
                        value_part = value_part.replace(")", "")
                    value_list = value_part.split(separator_list[0])
                    package_count = value_list[0].strip()
                    length = value_list[1].strip()
                    width = value_list[2].strip()
                    if "cm" in value_list[3].strip():
                        height = value_list[3].strip().replace("cm", "").strip()
                    else:
                        height = value_list[3].strip()
                    uom = "CMT"
                    if package_count == "l" or package_count == "I":
                        package_count = "1"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                    ]
                    return output_list
                # handling exceptional cases (e.g. "120 x 100 x 107 cm @ 1 plt (14 ctns)")
                if (
                    ("(" in sentence)
                    and (")" in sentence)
                    and "cm" in sentence.lower()
                    and "plt" in sentence.lower()
                    and "ctns" in sentence.lower()
                    and "@" in sentence
                ):
                    package_count = sentence.split("@")[1].split("plt")[0].strip()
                    package_type = "PLT"
                    value_part = sentence.split("@")[0].replace("cm", "")
                    sentence_list = value_part.split("x")
                    length = sentence_list[0].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[2].strip()
                    uom = "CMT"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                    ]
                    return output_list
                # handling exceptional cases (e.g., "5PLTS 1@80X120X100" or '1PLT@80X60X85' or '3 Pallets @ 80*120*85 cm')
                if (
                    "PLT" in sentence.upper()
                    or "CTN" in sentence.upper()
                    or "pallet" in sentence.lower()
                    or "carton" in sentence.lower()
                ) and "@" in sentence:
                    sentence_list = sentence.split(" ")
                    if "PLT" in sentence_list[0].upper():
                        package_type = "PLT"
                    elif "CTN" in sentence_list[0].upper():
                        package_type = "CTN"
                    elif "pallet" in sentence_list[1].lower():
                        package_type = "PLT"
                    elif "carton" in sentence_list[1].lower():
                        package_type = "CTN"
                    if len(sentence_list) == 1:
                        package_count = sentence_list[0][0]
                        dim_values = sentence_list[0][5:].split(
                            separator_list[-1]
                        )  # here last index of separator_list contains the real separator here
                        length = dim_values[0]
                        width = dim_values[1]
                        height = dim_values[2]
                    elif len(sentence_list) == 2:
                        package_count = sentence_list[1][0]
                        dim_value_part = sentence_list[1][2:]
                        if "cm" in dim_value_part:  # (exception: "1PLT 1@BOX60X50cm")
                            dim_value_part = dim_value_part.replace("cm", "")
                            if "B" in dim_value_part:
                                dim_value_part = dim_value_part.replace("B", "8")
                        dim_values = dim_value_part.split(
                            separator_list[-1]
                        )  # here last index of separator_list contains the real separator here
                        length = dim_values[0]
                        width = dim_values[1]
                        height = dim_values[2]
                    elif len(sentence_list) == 5:
                        package_count = sentence_list[0]
                        if (
                            "/*" in sentence_list[3]
                        ):  # (exception: "1 Carton @ 21*16/*16 cm")
                            sentence_list[3] = sentence_list[3].replace("/", "")
                            dim_values = sentence_list[3].split("*")
                        else:
                            dim_values = sentence_list[3].split(
                                separator_list[-1]
                            )  # here last index of separator_list contains the real separator here
                        length = dim_values[0]
                        width = dim_values[1]
                        height = dim_values[2]
                    uom = "CMT"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                    ]
                    return output_list
                # handling exceptional cases (e.g., "1 CARDBOARD BOX 25 x 19 x 9 cm 0,30 kg")
                if "kg" in sentence.lower():
                    # adding space before and after separators
                    for i in range(len(sentence)):
                        if sentence[i] in separator_list:
                            if sentence[i - 1] != " ":
                                sentence = sentence.replace(
                                    sentence[i], " " + sentence[i], 1
                                )
                            if sentence[i + 1] != " ":
                                sentence = sentence.replace(
                                    sentence[i], sentence[i] + " ", 1
                                )
                    input_sentence_list = sentence.split(" ")
                    for i in range(len(input_sentence_list)):
                        if input_sentence_list[i] in separator_list:
                            if input_sentence_list[i] == input_sentence_list[i + 2]:
                                length = input_sentence_list[i - 1]
                                width = input_sentence_list[i + 1]
                                height = input_sentence_list[i + 3]
                                if input_sentence_list[i + 4].isnumeric() == False:
                                    uom = input_sentence_list[i + 4].upper()
                                if input_sentence_list[i + 6].lower() == "kg":
                                    grossWeight = input_sentence_list[i + 5]
                                    grossWeightUom = "KGM"
                            input_sentence_list = input_sentence_list[0 : i - 1]
                            break
                    if input_sentence_list[0].isnumeric():
                        package_count = input_sentence_list[0]
                        input_sentence_list = input_sentence_list[1:]
                    package_type = ""
                    if len(input_sentence_list) == 1:
                        package_type = input_sentence_list[0]
                    else:
                        for i in input_sentence_list:
                            package_type += i + " "
                    package_type = package_type.strip()
                    if package_type.lower() == "cardboard box":
                        package_type = "CTN"
                    elif (
                        package_type.lower() == "kiste"
                        or package_type.lower() == "case"
                        or package_type.lower() == "caja"
                    ):
                        package_type = "CAS"
                    elif (
                        package_type.lower() == "kartonpalette"
                        or package_type.lower() == "karton-palette"
                        or package_type.lower() == "cardboard pallet"
                        or package_type.lower() == "cardboard-palett"
                        or package_type.lower() == "einweg-palette"
                    ):
                        package_type = "PLT"
                    if uom == "CM":
                        uom = "CMT"
                    return [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                        grossWeight,
                        grossWeightUom,
                    ]
                # handling exceptional cases (e.g., "0,70x0,46x0,50 m")
                if (
                    sentence.count(",") == 3
                    and len(sentence.split(" ")) == 2
                    and sentence.count("m") == 1
                ):
                    sentence_list = sentence.split("x")
                    length = sentence_list[0].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[2].strip().split(" ")[0].strip()
                    uom = "MTR"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling exceptional cases (e.g., "3 Pallet Euro 1,270 x 0,870 x 0,870 M STACKABLE")
                if "STACKABLE" in sentence.upper():
                    sentence_list = sentence.split(" ")
                    package_count = sentence_list[0].strip()
                    package_type = "PLT"
                    for i in range(1, len(sentence_list)):
                        if sentence_list[i].lower() == "x":
                            if sentence_list[i + 2].lower() == "x":
                                length = sentence_list[i - 1].strip()
                                width = sentence_list[i + 1].strip()
                                height = sentence_list[i + 3].strip()
                                break
                    uom = "MTR"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                    ]
                    return output_list
                # handling exceptional cases (e.g., "1,100 X 1,200 X 1,470" or, "252.00*75.00*68.00" or "77,000 X 22,000 X 45,000 cm")
                if (
                    sentence.count(",") == 3 or sentence.count(".") == 3
                ) and separator_list[0] == separator_list[1]:
                    sentence_list = sentence.split(separator_list[0])
                    length = sentence_list[0].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[2].strip()
                    if "cm" in height.lower():
                        height = height.replace("cm", "").strip()
                    uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling exceptional cases (e.g., "N°1 PALLET DIM. 120x80x130 (MADE OF 17 CARTONS)")
                if "N°1" in sentence.upper():
                    if "DIM." in sentence:
                        if sentence[sentence.index("D") + 4] != " ":
                            sentence = (
                                sentence[: sentence.index("D") + 4]
                                + " "
                                + sentence[sentence.index("D") + 4 :]
                            )
                    sentence_list = sentence.split(" ")
                    dimension_data = sentence_list[3].strip()
                    if dimension_data[-1] == "x" and sentence_list[4].isnumeric():
                        dimension_data += sentence_list[4]
                    dimension_data_list = dimension_data.split("x")
                    length = dimension_data_list[0].strip()
                    width = dimension_data_list[1].strip()
                    height = dimension_data_list[2].strip()
                    uom = "CMT"
                    package_count = "1"
                    package_type = "PALLET"
                    innerPackageCount = sentence_list[-2]
                    innerPackageType = "CARTON"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        package_count,
                        package_type,
                        innerPackageCount,
                        innerPackageType,
                    ]
                    return output_list
                # handling dimensions with two same separators and exceptional cases with 3 cms (e.g., "54cm * 54cm * 37cm (2BOX)")
                if (
                    sentence.count("cm") == 3
                    and "BOX)" in sentence
                    and (separator_list[0] == separator_list[1])
                ):
                    sentence_list = sentence.split(separator_list[0])
                    length = sentence_list[0].replace("cm", "").strip()
                    width = sentence_list[1].replace("cm", "").strip()
                    other_part = sentence_list[2].strip().split("(")
                    height = other_part[0].replace("cm", "").strip()
                    package_count = other_part[1].replace("BOX)", "").strip()
                    package_type = "BOX"
                    uom = "CMT"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                    ]
                    return output_list
                # handling exceptional cases (e.g. "x 26 x 30 CM Karton 45")
                if sentence[0] == separator_list[0]:
                    sentence_list = sentence.split(" ")
                    length = sentence_list[-1].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[3].strip()
                    uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling exceptional cases (e.g. "80 x 60 66 CM")
                if (
                    len(separator_list) == 1
                    and len(sentence.split(" ")) == 5
                    and "CM" in sentence.upper()
                ):
                    sentence_list = sentence.split(" ")
                    length = sentence_list[0].strip()
                    width = sentence_list[2].strip()
                    height = sentence_list[3].strip()
                    uom = "CMT"
                    output_list = [length, width, height, uom, extra_data]
                    return output_list
                # handling exceptional cases (e.g. "48 X 45 X 12 (2)")
                if (
                    ("(" in sentence)
                    and (")" in sentence)
                    and ((sentence.index("(") + 2) == sentence.index(")"))
                ):
                    package_count = sentence[
                        sentence.index("(") + 1 : sentence.index(")")
                    ]
                    value_part = sentence[: sentence.index("(")].strip()
                    sentence_list = value_part.split("X")
                    length = sentence_list[0].strip()
                    width = sentence_list[1].strip()
                    height = sentence_list[2].strip()
                    uom = "CMT"
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                    ]
                    return output_list

                # setting separators
                if separator_list[0] == separator_list[1]:
                    dimension_separator = separator_list[0]
                    if len(separator_list) > 2:
                        type_separator = separator_list[2]
                elif separator_list.count(separator_list[1]) > 1:
                    type_separator = separator_list[0]
                    dimension_separator = separator_list[1]

                # handling dimensions with brackets
                if value_part[0] == "(" and value_part[-1] == ")":
                    dimension_list = value_part[1:-1].split(dimension_separator)
                elif value_part[0] == "(" and value_part[-1] != ")":
                    extra_data = value_part.split(")")[1].strip()
                    if type_separator != None and type_separator in extra_data:
                        if extra_data[0] == type_separator:
                            extra_data = extra_data[1:].strip()
                    dimension_list = value_part.split(")")[0][1:].split(
                        dimension_separator
                    )
                elif value_part[0] != "(" and value_part[-1] == ")":
                    extra_data = value_part.split("(")[0].strip()
                    if type_separator != None and type_separator in extra_data:
                        if (
                            extra_data[extra_data.index(type_separator) + 1 :].strip()
                            == ""
                        ):
                            extra_data = extra_data[
                                0 : extra_data.index(type_separator)
                            ].strip()
                    dimension_list = value_part.split("(")[1][0:-1].split(
                        dimension_separator
                    )

                # handling dimensions without brackets
                if "(" not in value_part and type_separator == None:
                    dimension_list = value_part.split(dimension_separator)
                elif "(" not in value_part and type_separator != None:
                    left_part = value_part.split(type_separator)[0].strip()
                    right_part = value_part.split(type_separator)[1].strip()
                    if left_part.count(dimension_separator) > 1:
                        extra_data = right_part
                        dimension_list = left_part.split(dimension_separator)
                    elif right_part.count(dimension_separator) > 1:
                        extra_data = left_part
                        dimension_list = right_part.split(dimension_separator)

                # extracting the dimension values
                length = dimension_list[0].strip()
                if " " in length:
                    length_check = length.replace(" ", "")
                    if length_check.isnumeric() == False:
                        length_list = length.split(" ")
                        for i in length_list:
                            if i.isnumeric():
                                length = i
                        if len(length_list) >= 2:  # (exception: 1 CTN 30*23*23)
                            for (
                                i
                            ) in common_package_type_list:  # (exception: 1PLT 80X60X60)
                                if i in length_list[0].lower():
                                    length_list[0] = (
                                        length_list[0].lower().replace(i, "")
                                    )
                                    length_list[0] = length_list[0].strip()
                                    break
                            if length_list[0].isnumeric():
                                package_count = length_list[0].strip()
                            if length_list[0] == "l":
                                package_count = "1"
                    else:  # (exception: "6 57 x 34.5 x 34.5")
                        length_list = length.split(" ")
                        package_count = length_list[0]
                        length = length_list[1]
                width = dimension_list[1].strip()
                if " " in dimension_list[2].strip():
                    height = dimension_list[2].strip().split(" ")[0]
                    uom = dimension_list[2].strip().split(" ")[1]
                elif dimension_list[2].strip().isalnum():
                    height = ""
                    uom = ""
                    for i in dimension_list[2].strip():
                        if ord("0") <= ord(i) <= ord("9"):
                            height += i
                        elif ord("A") <= ord(i) <= ord("z"):
                            uom += i
                    height = height
                    uom = uom.strip()
                else:
                    height = dimension_list[2].strip()
                if uom == "":
                    uom = None
                elif uom != "" and uom != None and uom[-1] == ".":
                    uom = uom[0:-1]
                if uom == None or uom == "cms" or len(uom) < 2:
                    uom = "CM"
                uom = uom.upper()
                if uom == "CM":
                    uom = "CMT"

                # handling package_count and package_type
                if extra_data != None:
                    if (
                        ("box" in extra_data)
                        or ("Box" in extra_data)
                        or ("BOX" in extra_data)
                        or ("Pc" in extra_data)
                        or ("PC" in extra_data)
                        or ("PCS" in extra_data)
                        or ("pcs" in extra_data)
                        or ("Pcs" in extra_data)
                    ) and " " in extra_data:
                        package_count_value = extra_data.split(" ")[0]
                        if package_count_value.isnumeric():
                            package_count = package_count_value
                        package_type = extra_data.split(" ")[1]
                    # handling packageCount only if the whole extra data is numeric (e.g. 1*250x340x34)
                    elif extra_data.isnumeric():
                        package_count = extra_data
                        extra_data = None
                # checking if any common package_type exists in the sentence
                if package_type == None:
                    for i in common_package_type_list:
                        if i in sentence.lower():
                            package_type = i.upper()
                            break

                # Generating the output list
                output_list = [length, width, height, uom, extra_data]
                if package_count != None and package_type != None:
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                        package_type,
                    ]
                elif package_count != None and package_type == None:
                    output_list = [
                        length,
                        width,
                        height,
                        uom,
                        extra_data,
                        package_count,
                    ]

                return output_list
            except:
                # print(traceback.print_exc())
                return [sentence]

        # -------------------------------- driver code for the outer (main) function ----------------------------
        # finding multiple dimension's separator first
        full_sentence = full_sentence.strip()
        if (
            "Dimension" in full_sentence
        ):  # removing the word/caption "Dimension :" from dimension input
            full_sentence = full_sentence.replace("Dimension", "")
            full_sentence = full_sentence.strip()
            if full_sentence[0] == ":":
                full_sentence = full_sentence[1:]
                full_sentence = full_sentence.strip()
        multiple_dimension_output_list = []
        multiple_dimension_sentence_list = []
        multiple_separator = None
        for i in full_sentence:
            if i == "," or i == "\n" or i == ";" or i == ":":
                multiple_separator = i
                break
        # if there's no dimensions (no numeric values), return the none directly without checking
        non_numeric_check = ""
        for i in full_sentence:
            if i != " ":
                non_numeric_check += i
        if non_numeric_check.isalpha():
            return []

        # if no multiple separator, handling space issues (e.g., "1 x 120/80/130 1 x 120/80/90" or "1 31 27 48 1 36 25 17")
        string_of_separators = """"xX@*+-—/'\~"""
        total_number_of_separators = 0
        space_slicing_point = None
        full_sentence_without_space = full_sentence.replace(" ", "")
        if multiple_separator == None:
            for i in full_sentence:
                if i in string_of_separators:
                    total_number_of_separators += 1
        if multiple_separator == None and (
            total_number_of_separators > 5
            or (
                full_sentence_without_space.isnumeric()
                and (full_sentence.count(" ") > 3)
            )
        ):
            space_index = (full_sentence.count(" ") // 2) + 1
            space_count = 0
            for i in range(len(full_sentence)):
                if full_sentence[i] == " ":
                    space_count += 1
                    if space_count == space_index:
                        space_slicing_point = i
                        break

        # splitting the full sentence into multiple dimensions
        if multiple_separator != None:
            if "\n" in full_sentence and multiple_separator != "\n":
                full_sentence = full_sentence.replace("\n", multiple_separator)
            multiple_dimension_sentence_list = full_sentence.split(multiple_separator)
            if "" in multiple_dimension_sentence_list:
                multiple_dimension_sentence_list.remove("")
        elif space_slicing_point != None:
            first_part = full_sentence[0:space_slicing_point]
            second_part = full_sentence[space_slicing_point + 1 :]
            multiple_dimension_sentence_list.append(first_part)
            multiple_dimension_sentence_list.append(second_part)
        else:
            multiple_dimension_sentence_list = [full_sentence]
        # handling exceptional cases (e.g., "1 CARDBOARD BOX 25 x 19 x 9 cm 0,30 kg")
        if "kg" in full_sentence:
            multiple_dimension_sentence_list = []
            full_sentence_list = full_sentence.split(" ")
            if "\n" in full_sentence:
                full_sentence_kg_list = full_sentence.split("\n")
                for i in full_sentence_kg_list:
                    if "*" in i:
                        i = i.replace("*", "")
                        i = i.strip()
                    multiple_dimension_sentence_list.append(i)
            elif full_sentence_list.count("kg") > 1:
                full_sentence_kg_list = full_sentence.split("kg")
                if " *" in full_sentence_kg_list:
                    full_sentence_kg_list.remove(" *")
                for i in full_sentence_kg_list:
                    if i != "":
                        multiple_dimension_sentence_list.append(i + "kg")
            else:
                multiple_dimension_sentence_list = [full_sentence]
        # handling exceptional cases (e.g., "* PALLET SIZE: 1,100 X 1,200 X 1,470 * 1,100 X 1,200 X 1,250 * 1,100 X 1,200 X 590")
        if "PALLET SIZE" in full_sentence.upper():
            full_value_part = full_sentence.split(":")[1].strip()
            multiple_dimension_sentence_list = []
            given_sentence_list = full_value_part.split("*")
            for i in given_sentence_list:
                multiple_dimension_sentence_list.append(i.strip())
        # handling exceptional cases (e.g. "58 * 23 * 60cm * 2") by ignoring the last packageCount
        if len(full_sentence.split(" ")) == 7:
            if (
                ("cm" in full_sentence.split(" ")[4])
                and (full_sentence.split(" ")[5] == "*")
                and (full_sentence.split(" ")[6].isnumeric())
            ):
                full_sentence_list = full_sentence.split(" ")[0:5]
                new_sentence = ""
                for i in full_sentence_list:
                    new_sentence += i + " "
                new_sentence = new_sentence.strip()
                multiple_dimension_sentence_list = [new_sentence]
        # handling exceptional cases (e.g., "N°1 PALLET DIM. 120x80x131 (MADE OF 18 CARTONS) N°1 PALLET DIM. 80x60x 53 (MADE OF 2 CARTONS)")
        if "N°1" in full_sentence.upper():
            full_sentence_list = full_sentence.split("N°1")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if "\n" in i:
                    i = i.replace("\n", " ")
                if "-" in i:
                    i = i.replace("-", "")
                if i != "":
                    multiple_dimension_sentence_list.append("N°1 " + i.strip())
        # handling exceptional cases (e.g., "120,00 x 80,00 x 70,00 cm" or "77,000 X 22,000 X 45,000 CM")
        if (
            full_sentence.count(",") == 3
            and len(full_sentence.split(" ")) == 6
            and full_sentence.lower().count("cm") == 1
        ):
            full_sentence_list = full_sentence.lower().split("cm")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if i != "":
                    multiple_dimension_sentence_list.append(i.strip() + " cm")
        # handling exceptional cases (e.g., "40,7x30,5x15,3" or "59,500 x 37,500 x 43,500" or "60 x 39,500 x 26,500")
        if (
            full_sentence.count(",") <= 3
            and len(full_sentence.split(" ")) <= 5
            and (full_sentence.count("x") == 2 or full_sentence.count("X") == 2)
        ):
            multiple_dimension_sentence_list = [full_sentence]
        # handling exceptional cases (e.g., "0,70x0,46x0,50 m")
        if (
            full_sentence.count(",") == 3
            and len(full_sentence.split(" ")) == 2
            and full_sentence.count("m") == 1
        ):
            full_sentence_list = full_sentence.split("m")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if i != "":
                    multiple_dimension_sentence_list.append(i.strip() + " m")
        # handling exceptional cases (e.g., "1 Pallet Euro 1,200 x 0,800 x 0,450 M NON-STACKABLE\n9 Pallet Euro 1,200 x 0,800 x 1,270 M NON-STACKABLE")
        if "STACKABLE" in full_sentence.upper():
            full_sentence_list = full_sentence.split("STACKABLE")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if "\n" in i:
                    i = i.replace("\n", " ")
                if "-" in i:
                    i = i.replace("-", "")
                if i != "":
                    multiple_dimension_sentence_list.append(i.strip() + " STACKABLE")
        # handling exceptional cases (e.g., "TOTAL- 5BOX 52cm * 50cm * 50cm (1BOX) 60cm * 60cm * 39cm (2BOX) 71cm * 71cm * 36cm (2BOX)")
        if "BOX)" in full_sentence.upper() and (full_sentence.count("cm") % 3 == 0):
            if "\n" in full_sentence:
                full_sentence = full_sentence.replace("\n", " ")
            full_sentence_list = full_sentence.split(" ")
            for i in full_sentence_list:
                if ("total" in i.lower()) or i == "-" or ("box" in i.lower()):
                    full_sentence = full_sentence.replace(i, "", 1)
                else:
                    break
            full_sentence_list = full_sentence.strip().split("BOX)")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if "\n" in i:
                    i = i.replace("\n", " ")
                if "-" in i:
                    i = i.replace("-", "")
                if "cm*" in i:
                    i = i.replace("cm*", "cm *")
                if i != "":
                    multiple_dimension_sentence_list.append(i.strip() + "BOX)")
        # handling exceptional cases (e.g., "120 x 100 x 107 cm @ 1 plt (14 ctns).120x100x107cm@1plt(14 ctns)")
        if (
            ("(" in full_sentence)
            and (")" in full_sentence)
            and "cm" in full_sentence.lower()
            and "plt" in full_sentence.lower()
            and "ctns" in full_sentence.lower()
            and "@" in full_sentence
        ):
            if "\n" in full_sentence:
                full_sentence = full_sentence.replace("\n", " ")
            if ":" in full_sentence:
                full_sentence = full_sentence.replace(":", " ")
            if ";" in full_sentence:
                full_sentence = full_sentence.replace(";", " ")
            full_sentence_list = full_sentence.strip().split("ctns)")
            multiple_dimension_sentence_list = []
            for i in full_sentence_list:
                i = i.strip()
                if i != "":
                    multiple_dimension_sentence_list.append(i.strip() + "ctns)")
        # handling exceptional cases (e.g., "5PLTS 1@80X120X100 3@80X120X85 1@80X60X50")
        if (
            (
                "PLT" in full_sentence.upper()
                or "CTN" in full_sentence.upper()
                or "pallet" in full_sentence.lower()
            )
            and "@" in full_sentence
            and ("CTNS" not in full_sentence.upper())
        ):
            if (
                full_sentence.count("T") == 1
            ):  # (e.g. "3PLTS - 1@80X120X85, 1@80X120X65 & 1@80X120X85")
                if "-" in full_sentence:
                    full_sentence = full_sentence.replace("-", "")
                if "," in full_sentence:
                    full_sentence = full_sentence.replace(",", "")
                if "&" in full_sentence:
                    full_sentence = full_sentence.replace("&", "")
                if full_sentence[1] == " ":
                    full_sentence = full_sentence.replace(" ", "", 1)
                if "@ " in full_sentence:
                    full_sentence = full_sentence.replace("@ ", "@")
            full_sentence_list = full_sentence.split(" ")
            if (
                "PLT" in full_sentence_list[0].upper()
                or "CTN" in full_sentence_list[0].upper()
            ):
                unit = full_sentence_list[0].strip()
                full_sentence_list = full_sentence_list[1:]
            multiple_dimension_sentence_list = []
            if full_sentence.count("@") == 1:  # (e.g. "2PLTs@80X60X50")
                if full_sentence[full_sentence.index("@") - 1].isnumeric() != True:
                    new_sentence = (
                        full_sentence[: full_sentence.index("@")]
                        + " "
                        + full_sentence[0]
                        + full_sentence[full_sentence.index("@") :]
                    )
                    if "   " in new_sentence:
                        new_sentence = new_sentence.replace("   ", " ")
                    if "  " in new_sentence:
                        new_sentence = new_sentence.replace("  ", " ")
                    multiple_dimension_sentence_list = [new_sentence]
            elif (
                "pallet" in full_sentence.lower()
                and "/" in full_sentence
                and "@" in full_sentence
                and "cm" in full_sentence
            ):  # (e.g. "5 Pallets / 4 @ 60*120*50 / 1 @ 60*60*85 cm")
                pallet_list = full_sentence[:-2].split("/")
                for i in pallet_list:
                    if "@" in i:
                        i = i.replace("@", "Pallets @")
                        i = i.strip() + " cm"
                        multiple_dimension_sentence_list.append(i)
            else:
                for i in full_sentence_list:
                    i = i.strip()
                    if "CTM" in i.upper():
                        i = i.replace("CTM", "CTN")
                    if (
                        i != ""
                        and ("@" in i)
                        and ("PLT" in i.upper() or "CTN" in i.upper())
                    ):
                        multiple_dimension_sentence_list.append(i.strip())
                    elif i != "" and len(i) != 1 and ("CTN" not in i.upper()):
                        multiple_dimension_sentence_list.append(unit + " " + i.strip())

        # calling dimension checker for all dimensions and appending the output lists
        for i in multiple_dimension_sentence_list:
            single_output_list = single_dimension_checker(i)
            multiple_dimension_output_list.append(single_output_list)

        return multiple_dimension_output_list

    except:
        return [full_sentence]


############################### New Parser Begin ######################################

import re
import traceback


def get_separator(filtered_input_string):
    separators = """"xX@*+-—/'\~|_"""
    main_separator_count = 0
    main_separator = None
    for sep in separators:
        count = filtered_input_string.count(sep)
        if count > main_separator_count:
            main_separator_count = count
            main_separator = sep
    if main_separator == None:
        main_separator = " "
        main_separator_count = filtered_input_string.count(" ")
    return main_separator, main_separator_count, separators


def get_token(s):
    pattern = re.compile(r"\d+[\.,]?\d*|[a-zA-Z]+|[^a-zA-Z\d\s]")
    return pattern.findall(s)


def reconstract_exceptional_string(input_string):
    input_string = input_string.strip()

    if (
        (
            "length" in input_string.lower()
            and "width" in input_string.lower()
            and "height" in input_string.lower()
        )
        or "(l)" in input_string.lower()
        and "(w)" in input_string.lower()
        and "(h)" in input_string.lower()
    ):
        input_string = (
            input_string.lower()
            .replace("length", " ")
            .replace("width", " ")
            .replace("height", " ")
            .replace("(l)", " ")
            .replace("(w)", " ")
            .replace("(h)", " ")
        )

    if (
        input_string.lower().count("x") == 1
        and input_string.lower().count(" ") == 4
        and input_string.lower().count("cm") == 1
        and input_string.lower()[-1] == "m"
    ):
        input_string = input_string.lower().replace("x", "")

    if (
        input_string.lower().count("-") == 1
        and input_string.lower().count("pallets") == 1
        and input_string.lower().count(" ") == 5
    ):
        input_string = input_string.lower().replace("pallets", "").split("-")
        input_string = input_string[1] + " pallets " + input_string[0]

    if ". " in input_string and input_string.count("*") == 2:
        input_string = input_string.split("*")
        token_all = ""
        for token in input_string:
            token = token.strip()
            if " " in token and "." not in token:
                token = token.replace(" ", ".")
            else:
                token = token.strip().replace(" ", "")
            token_all = token_all + " " + token
        input_string = token_all

    # if "\n" not in input_string:
    #     if (
    #         input_string.count(".") == 2
    #         and len(input_string.split(".")) == 3
    #         and input_string[1] != " "
    #     ):
    #         input_string = input_string.replace(".", "*")

    if "Karton" in input_string and input_string[-1].isdigit():
        input_string = input_string.split("Karton")
        input_string = input_string[1] + input_string[0]

    if (
        input_string.count("cm") == 1
        and input_string.count("*") == 3
        and input_string[-1].isdigit()
    ):
        input_string = input_string.split("cm")
        input_string = input_string[1].replace("*", "") + "*" + input_string[0] + " cm"

    if input_string.count(" ") == 1 and input_string.lower().count("x") == 2:
        input_string = input_string.replace(" ", " x ")

    if "lx" in input_string.lower() and input_string[0].lower() == "l":
        input_string = "1" + input_string[1:].strip()

    return input_string


def get_blank_output_pattern(inner_pkg_list_trigger=False):
    if not inner_pkg_list_trigger:
        return {
            "length": None,
            "width": None,
            "height": None,
            "uom": None,
            "extra_data": None,
            "package_count": None,
            "package_type": None,
            "grossWeight": None,
            "grossWeightUom": None,
        }
    else:
        return {
            "length": None,
            "width": None,
            "height": None,
            "uom": None,
            "package_count": None,
            "package_type": None,
            "innerPackageCount": None,
            "innerPackageType": None,
        }


def select_output_for_result(all_output_patterns, inner_pkg_list_trigger=False):
    selected_result = []

    if not inner_pkg_list_trigger:
        for idx, output_pattern in enumerate(all_output_patterns):
            result_sub = []

            if (
                output_pattern["package_count"] == None
                and output_pattern["package_type"] == None
                and output_pattern["grossWeight"] == None
                and output_pattern["grossWeightUom"] == None
            ):
                result_sub = [
                    output_pattern["length"],
                    output_pattern["width"],
                    output_pattern["height"],
                    output_pattern["uom"],
                    output_pattern["extra_data"],
                ]

            elif (
                output_pattern["package_count"] != None
                and output_pattern["package_type"] == None
                and output_pattern["grossWeight"] == None
                and output_pattern["grossWeightUom"] == None
            ):
                result_sub = [
                    output_pattern["length"],
                    output_pattern["width"],
                    output_pattern["height"],
                    output_pattern["uom"],
                    output_pattern["extra_data"],
                    output_pattern["package_count"],
                ]
            elif (
                output_pattern["package_type"] != None
                and output_pattern["grossWeight"] == None
                and output_pattern["grossWeightUom"] == None
            ):
                result_sub = [
                    output_pattern["length"],
                    output_pattern["width"],
                    output_pattern["height"],
                    output_pattern["uom"],
                    output_pattern["extra_data"],
                    output_pattern["package_count"],
                    output_pattern["package_type"],
                ]

            elif output_pattern["grossWeight"] != None:
                result_sub = [
                    output_pattern["length"],
                    output_pattern["width"],
                    output_pattern["height"],
                    output_pattern["uom"],
                    output_pattern["extra_data"],
                    output_pattern["package_count"],
                    output_pattern["package_type"],
                    output_pattern["grossWeight"],
                    output_pattern["grossWeightUom"],
                ]

            selected_result.append(result_sub)
    else:
        for idx, output_pattern in enumerate(all_output_patterns):
            result_sub = [
                output_pattern["length"],
                output_pattern["width"],
                output_pattern["height"],
                output_pattern["uom"],
                output_pattern["package_count"],
                output_pattern["package_type"],
                output_pattern["innerPackageCount"],
                output_pattern["innerPackageType"],
            ]
            selected_result.append(result_sub)

    return selected_result


def add_output_pattern(output_pattern, value_list, inner_pkg_list_trigger=False):
    idx_key_map_1 = {
        0: "length",
        1: "width",
        2: "height",
        3: "uom",
        4: "extra_data",
        5: "package_count",
        6: "package_type",
        7: "grossWeight",
        8: "grossWeightUom",
    }

    idx_key_map_2 = {
        0: "length",
        1: "width",
        2: "height",
        3: "uom",
        4: "package_count",
        5: "package_type",
        6: "innerPackageCount",
        7: "innerPackageType",
    }

    if not inner_pkg_list_trigger:
        for idx, value in enumerate(value_list):
            output_pattern[idx_key_map_1[idx]] = value
    else:
        for idx, value in enumerate(value_list):
            output_pattern[idx_key_map_2[idx]] = value
    return output_pattern


def get_uom(unchanged_input_keeper, token_list):
    uom = None
    uom_from_token = None
    uom_from_str = None

    for token in token_list:
        if token.lower() == "cm":
            uom_from_token = "CMT"
        elif token.lower() == "mm":
            uom_from_token = "MM"
        elif token.lower() == "m":
            uom_from_token = "MTR"

    if "cm" in unchanged_input_keeper.lower():
        uom_from_str = "CMT"
    elif "mm" in unchanged_input_keeper.lower():
        uom_from_str = "MM"
    elif " m" in unchanged_input_keeper.lower():
        uom_from_str = "MTR"

    if uom_from_token == uom_from_str and uom_from_str != None:
        uom = uom_from_str
    elif (
        uom_from_token != uom_from_str
        and uom_from_token != None
        and uom_from_str == None
    ):
        uom = uom_from_token
    elif (
        uom_from_token != uom_from_str
        and uom_from_token == None
        and uom_from_str != None
    ):
        uom = uom_from_str
    else:
        uom = "CMT"

    return uom


def handle_special_format(token_list):
    """
    Parses a list of tokens to extract special dimension-related information.

    The function expects a token list that, when joined, ends with "/special" and contains a pattern
    like "<length>*<width>*<height>[CM]x<quantity>/.../special". It extracts the dimensions, an optional
    'CM' unit, quantity, additional segments, and the "special" tag.
    """
    try:
        token_string = "".join(token_list)

        if not token_string.endswith("/special"):
            return None

        dimensions_pattern = r"^(\d+(?:\.\d+)?)\*(\d+(?:\.\d+)?)\*(\d+(?:\.\d+)?)"
        dimensions_match = re.search(dimensions_pattern, token_string)

        if not dimensions_match:
            return None

        length, width, height = dimensions_match.groups()

        remainder = token_string[dimensions_match.end() :]

        # Check for CM unit
        has_cm = False
        if remainder.startswith("CM"):
            has_cm = True
            remainder = remainder[2:]

        # Look for 'x' followed by quantity or 'x/' pattern
        x_pattern = r"[xX](\d+(?:\.\d+)?)|[xX]/"
        x_match = re.search(x_pattern, remainder)

        if not x_match:
            return None

        if x_match.group(1):
            quantity = x_match.group(1)
            remainder = remainder[x_match.end() :]
        else:
            remainder = remainder[x_match.end() - 1 :]
            # Fallback: try to extract quantity after slash
            qty_match = re.search(r"^(\d+)", remainder)
            if qty_match:
                quantity = qty_match.group(1)
                remainder = remainder[qty_match.end() :]
            else:
                quantity = None

        remainder = remainder[:-8]

        segments = []
        if remainder:
            if remainder.startswith("/"):
                remainder = remainder[1:]
            # Split additional segments by slash
            segments = [s for s in remainder.split("/") if s]

        result = [length, width, height]
        if has_cm:
            result[-1] += "CM"
        if quantity is not None:
            result.append(quantity)
        result.extend(segments)
        result.append("special")

        return [result]

    except Exception as e:
        print(f"Special format parsing failed: {e}")
        return None


def get_output(unchanged_input_keeper, filtered_input_string, token_list):
    # First try to handle the special format
    unchanged_input_keeper = unchanged_input_keeper.replace("/special", "")
    filtered_input_string = filtered_input_string.replace("/special", "")
    if "special" in token_list:
        special_format_result = handle_special_format(token_list)
        if special_format_result is not None:
            print(f"found special format {special_format_result=}")
            return special_format_result
    token_list = token_list[:-2] if "special" in token_list else token_list

    # Original code starts here
    all_output_patterns = []
    idx_done_list = []
    combine_length_width_height_list = []
    combine_pkg_count_list = []
    combine_gross_weight_list = []
    inner_pkg_count_list = []
    uom = None
    pkg_type = None
    gross_weight_uom = None
    extra_data = None
    inner_pkg_type = None
    inner_pkg_list_trigger = False

    kgm_list = ["kg"]
    plt_list = ["pallets", "plt", "pallet", "plts", "@", "x", "*", "X", ")"]
    ctn_list = ["ctn", "ctns", "carton", "cardboard", "cartons", "cardboards"]
    box_list = ["box", "boxs"]

    main_separator, main_separator_count, all_separators = get_separator(
        filtered_input_string
    )

    # finding length,width and height using this loop
    for idx, token in enumerate(token_list):
        is_token_a_digit = (
            token.replace(" ", "").replace(",", "").replace(".", "").isdigit()
        )

        if (
            is_token_a_digit
            and idx + 1 < len(token_list)
            and token_list[idx + 1] == main_separator
        ):
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)
        elif is_token_a_digit and token_list[idx - 1] == main_separator:
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)
        elif (
            is_token_a_digit
            and idx + 2 < len(token_list)
            and token_list[idx + 1].lower() == "cm"
            and token_list[idx + 2] == main_separator
            and unchanged_input_keeper.lower().count("cm") > 1
        ):
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)
        elif (
            is_token_a_digit
            and idx + 1 < len(token_list)
            and token_list[idx + 1].lower() == "cm"
            and main_separator == " "
            and unchanged_input_keeper.lower().count("cm") > 1
        ):
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)
        elif (
            is_token_a_digit
            and main_separator == " "
            and idx + 1 < len(token_list)
            and token_list[idx + 1]
            .replace(" ", "")
            .replace(",", "")
            .replace(".", "")
            .isdigit()
        ):
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)
        elif is_token_a_digit and main_separator == " ":
            combine_length_width_height_list.append(token.replace(" ", "").strip())
            idx_done_list.append(idx)

    # finding uom
    uom = get_uom(unchanged_input_keeper, token_list)

    # finding mainly package count, inner package count and grossweight using this loop beside it also find the prior finding of pkg type, inner pkg type and grossweight uom
    for idx, token in enumerate(token_list):
        is_token_a_digit = (
            token.replace(" ", "").replace(",", "").replace(".", "").isdigit()
        )

        if (
            is_token_a_digit
            and idx not in idx_done_list
            and idx + 1 < len(token_list)
            and token_list[idx + 1].lower().replace(".", "").replace(",", "")
            in kgm_list
        ):
            combine_gross_weight_list.append(token)
            gross_weight_uom = "KGM"
        elif (
            is_token_a_digit
            and idx not in idx_done_list
            and idx + 1 < len(token_list)
            and token_list[idx + 1].lower().replace(".", "").replace(",", "")
            in plt_list
        ):
            combine_pkg_count_list.append(token)

            if token_list[idx + 1].lower().replace(".", "").replace(",", "") in [
                "pallets",
                "plt",
                "pallet",
                "plts",
            ]:
                pkg_type = "PLT"
        elif (
            is_token_a_digit
            and idx not in idx_done_list
            and idx + 1 < len(token_list)
            and token_list[idx + 1].lower().replace(".", "").replace(",", "")
            in ctn_list
        ):
            inner_pkg_count_list.append(token)
            inner_pkg_type = "CTN"
        elif (
            is_token_a_digit
            and idx not in idx_done_list
            and idx + 1 < len(token_list)
            and token_list[idx + 1].lower().replace(".", "").replace(",", "")
            in box_list
        ):
            inner_pkg_count_list.append(token)
            inner_pkg_type = "BOX"
        elif (
            is_token_a_digit
            and idx not in idx_done_list
            and idx + 1 < len(token_list)
            and token_list[idx + 1].replace(".", "").replace(",", "").isdigit()
        ) or (
            is_token_a_digit and idx not in idx_done_list and idx + 1 == len(token_list)
        ):
            combine_pkg_count_list.append(token)

    # finding pkg type, inner pkg type
    if pkg_type == None:
        for idx, token in enumerate(token_list):
            if token in ["pallets", "plt", "pallet", "plts"]:
                pkg_type = "PLT"
                break
    if inner_pkg_type == None:
        for idx, token in enumerate(token_list):
            if token in [
                "ctn",
                "ctns",
                "carton",
                "cardboard",
                "cartons",
                "cardboards",
                "box",
                "boxs",
            ]:
                if "box" in token.lower():
                    inner_pkg_type = "BOX"
                    break
                else:
                    inner_pkg_type = "CTN"
                    break

    combine_length_width_height_list_spilited = []

    if len(combine_length_width_height_list) % 3 == 0:
        combine_length_width_height_list_spilited = [
            combine_length_width_height_list[i : i + 3]
            for i in range(0, len(combine_length_width_height_list), 3)
        ]
    elif len(combine_length_width_height_list) % 4 == 0:
        combine_length_width_height_list_spilited = [
            combine_length_width_height_list[i : i + 4]
            for i in range(0, len(combine_length_width_height_list), 4)
        ]

    if (
        len(combine_length_width_height_list_spilited) > 1
        and len(combine_pkg_count_list) > 1
        and len(combine_length_width_height_list_spilited)
        != len(combine_pkg_count_list)
    ):
        combine_pkg_count_list = combine_pkg_count_list[1:]

    if (
        len(combine_length_width_height_list_spilited) > 1
        and len(inner_pkg_count_list) > 1
        and len(combine_length_width_height_list_spilited) != len(inner_pkg_count_list)
    ):
        inner_pkg_count_list = inner_pkg_count_list[1:]

    for idx, combine_length_width_height_list in enumerate(
        combine_length_width_height_list_spilited
    ):
        if len(combine_length_width_height_list) == 3:
            if (
                combine_pkg_count_list == []
                and inner_pkg_count_list == []
                and combine_gross_weight_list == []
            ):
                output_pattern = get_blank_output_pattern()
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        extra_data,
                    ],
                )
            elif (
                combine_pkg_count_list != []
                and inner_pkg_count_list == []
                and combine_gross_weight_list == []
            ):
                output_pattern = get_blank_output_pattern()
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        extra_data,
                        combine_pkg_count_list[idx],
                        pkg_type,
                    ],
                )
            elif (
                combine_pkg_count_list != []
                and inner_pkg_count_list == []
                and combine_gross_weight_list != []
            ):
                output_pattern = get_blank_output_pattern()
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        extra_data,
                        combine_pkg_count_list[idx],
                        pkg_type,
                        combine_gross_weight_list[idx],
                        gross_weight_uom,
                    ],
                )
            elif (
                combine_pkg_count_list != []
                and inner_pkg_count_list != []
                and combine_gross_weight_list == []
            ):
                output_pattern = get_blank_output_pattern(True)
                inner_pkg_list_trigger = True
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        combine_pkg_count_list[idx],
                        pkg_type,
                        inner_pkg_count_list[idx],
                        inner_pkg_type,
                    ],
                    True,
                )
            elif (
                combine_pkg_count_list == []
                and inner_pkg_count_list != []
                and combine_gross_weight_list == []
            ):
                output_pattern = get_blank_output_pattern()
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        extra_data,
                        inner_pkg_count_list[idx],
                        inner_pkg_type,
                    ],
                )

            elif (
                combine_pkg_count_list == []
                and inner_pkg_count_list != []
                and combine_gross_weight_list != []
            ):
                output_pattern = get_blank_output_pattern()
                output_pattern = add_output_pattern(
                    output_pattern,
                    [
                        combine_length_width_height_list[0],
                        combine_length_width_height_list[1],
                        combine_length_width_height_list[2],
                        uom,
                        extra_data,
                        inner_pkg_count_list[idx],
                        inner_pkg_type,
                        combine_gross_weight_list[idx],
                        gross_weight_uom,
                    ],
                )

        elif len(combine_length_width_height_list) == 4:
            output_pattern = get_blank_output_pattern()
            output_pattern = add_output_pattern(
                output_pattern,
                [
                    combine_length_width_height_list[1],
                    combine_length_width_height_list[2],
                    combine_length_width_height_list[3],
                    uom,
                    extra_data,
                    combine_length_width_height_list[0],
                    pkg_type,
                ],
            )
        all_output_patterns.append(output_pattern.copy())
    if not inner_pkg_list_trigger:
        selected_result = select_output_for_result(all_output_patterns)
    else:
        selected_result = select_output_for_result(all_output_patterns, True)
    return selected_result


def count_digits_followed_by_star(input_string):
    # Created by - ganesh - 21.02.2025
    """
    Function that checks the count of numbers that is after or behind *
    """
    parts = input_string.split("*")

    count = 0
    for part in parts:
        try:
            float(part)
            count += 1
        except ValueError:
            pass

    return count


def standardize_dimensions(input_string, is_exceptional_profile=False):
    """
    Function that standerize dimension in l*w*hxpt
    where l = length, w=width, h=height and pt=package type
    """
    # Created by - ganesh - 21.02.2025
    copy_string = input_string
    try:
        if "\n" in input_string:
            input_string = input_string.split("\n")[0]
    except Exception:
        print(traceback.print_exc())
    try:
        input_string = (
            input_string.replace("×", "*").replace("x", "*").replace("X", "*")
        )
        if "CTNS:" in input_string:
            parts = input_string.split(":")
            quantity = parts[0].replace("CTNS", "")
            dimensions = parts[1]
            input_string = f"{dimensions}x{quantity}"

        if "@" in input_string:
            parts = input_string.split("@")
            dimensions = parts[0]
            quantity = parts[1].split("/")[0]
            quantity = "".join(filter(str.isdigit, quantity))
            if len(parts[1].split("/")) > 1:
                return f"{dimensions}x{parts[1]}/special"
            input_string = f"{dimensions}x{quantity}"

        if "cm*" in input_string.lower() or "CM*" in input_string:
            input_string = input_string.replace("cm*", "*").replace("CM*", "*")

        elif "cm" in input_string.lower() or "CM" in input_string:
            input_string = input_string.lower().replace("cm", "").replace("CM", "")
        parts = input_string.replace(" ", "").split("*")
        # Handle scenario like this "5x 120x80x84"
        has_digit_x_space = bool(re.search(r"\d+[xX×]\s", copy_string))
        if has_digit_x_space:
            package_count = parts[0]
            dimensions = "*".join(parts[1:])
            input_string = f"{dimensions}x{package_count}"
        if count_digits_followed_by_star(input_string) == 4:
            input_string_split = input_string.split("*")
            if is_exceptional_profile:
                asteric_string = "*".join(input_string_split[1:])
                package_count = input_string_split[0]
            else:
                asteric_string = "*".join(
                    input_string_split[: len(input_string_split) - 1]
                )
                package_count = input_string_split[-1]
            input_string = f"{asteric_string}x{package_count}"
        return input_string
    except:
        print(traceback.print_exc())
        return copy_string


def process(input_string, is_exceptional_profile=False):
    # Created by - ashik - 30.07.2024
    # Modified by - ganesg - 21.02.2025
    try:
        input_string = standardize_dimensions(input_string, is_exceptional_profile)
        unchanged_input_keeper = input_string.strip()
        filtered_input_string = reconstract_exceptional_string(input_string)
        token_list = get_token(filtered_input_string)
        output_list = get_output(
            unchanged_input_keeper, filtered_input_string, token_list
        )
        if output_list == [] or output_list == [[]]:
            return old_parser_process(unchanged_input_keeper)
        return output_list

    except Exception:
        print(traceback.format_exc())
        return old_parser_process(unchanged_input_keeper)
