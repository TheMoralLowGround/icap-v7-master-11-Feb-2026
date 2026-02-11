from operator import itemgetter

from . import get_left_pos_str


def process(line_data):
    line_data_new = []
    sorter = {}
    line_data_output = line_data.copy()
    i = 0
    line = line_data_output

    line_data_idx_left_list = []
    for j, k in enumerate(line[0]):
        left = get_left_pos_str.process(k[1])
        line_data_idx_left_list.append([j, left])
    line_data_idx_left_list = sorted(line_data_idx_left_list, key=itemgetter(1))

    sorter[i] = line_data_idx_left_list

    all_data = []
    for key, value in sorter.items():
        each_line = []
        if key == i:
            for idx_left in value:
                data_a = line[0][idx_left[0]]
                each_line.append(data_a)

            all_data.append(each_line)
            all_data.append(line[1])
            all_data.append(line[2])
            all_data.append(line[3])

    return all_data
