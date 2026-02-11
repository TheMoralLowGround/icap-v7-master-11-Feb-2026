# -*- coding: utf-8 -*-
"""
Created on Thu Apr 28 10:02:21 2022

@author: Administrator
"""

from fuzzywuzzy import fuzz


def process(data, data_detail, find_key):
    output_multi_list = []
    output = ""
    text_key = ""
    page = ""
    for key, value in data.items():
        for key1, value1 in value.items():
            for elem in value1:
                text = elem
                if (find_key in text) or (fuzz.WRatio(text, find_key) > 90):
                    text_key = key1
                    page = key
                    output = data_detail[page][text_key]
                    pos = ""
                    for j in output:
                        if j[0] == elem:
                            pos = j[1]
                            output_multi_list.append([output, text_key, page, pos])
    return output_multi_list
