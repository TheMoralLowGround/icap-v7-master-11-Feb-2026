from operator import itemgetter

from . import get_left_pos_str


def process(line_input):
    input_lines = line_input.copy()
    output = []
    lst = []
    for i, x in enumerate(input_lines):
        boundary = x[1]
        left_pos = get_left_pos_str.process(boundary)
        lst.append([i, left_pos])
    lst = sorted(lst, key=itemgetter(1))
    for [idx, left_pos] in lst:
        output.append(input_lines[idx])
    return output
