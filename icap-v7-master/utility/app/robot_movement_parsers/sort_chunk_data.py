from operator import itemgetter

from . import get_left_pos_str


def process(list_):
    output_list = []
    first_copy = list_.copy()
    sorter_list = []
    for i, chunk in enumerate(first_copy):
        left_pos = get_left_pos_str.process(chunk[1])
        sorter_list.append([i, left_pos])
    sorter_list = sorted(sorter_list, key=itemgetter(1))

    for [i, left_pos] in sorter_list:
        output_list.append(first_copy[i])

    return output_list
