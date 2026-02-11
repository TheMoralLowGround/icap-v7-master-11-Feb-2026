# -*- coding: utf-8 -*-
"""
Created on Sat Jul  2 22:24:54 2022

@author: Emon
"""
# Version: 5.01.20221205 @Fahim


def process(string):
    try:
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

        for [c_idx, c] in number_char_idx_val_list:
            if (c == ".") or (c == ","):
                if (c_idx - (c_idx - 1)) == 1:
                    number += c
            else:
                number += c

        # handling space before decimal
        if uom[0] == ".":
            number = number + uom
            uom = ""

        extra_data = None

        if extra_data_list:
            extra_data = " ".join(extra_data_list)

        if extra_data:
            if (uom.strip().lower() in extra_data.lower()) or (
                number.strip() in extra_data
            ):
                extra_data = None

        # checking if uom = "'"
        if uom == "'":
            uom = None

        # print("1. checing number:", number)
        # print("2. checing uom:", uom)
        # print("3. checing extra data:", extra_data)
        if number and uom:
            return [number, uom.upper(), extra_data]
        elif number:
            return [number]
        else:
            return [string]
    except:
        return [string]
