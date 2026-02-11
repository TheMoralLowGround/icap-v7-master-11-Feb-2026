# -*- coding: utf-8 -*-
"""
Created on Sat Jul  2 22:24:54 2022

@author: Emon
"""


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

        number = ""
        for c in new_string:
            if c == "," or c == "." or c.isdigit():
                number += c
        extra_data = None

        if extra_data_list:
            extra_data = " ".join(extra_data_list)

        if extra_data:
            if (uom in extra_data) or (number in extra_data):
                extra_data = None

        if number and uom:
            return [number, uom.upper(), extra_data]

        else:
            return [string]
    except:
        return [string]
