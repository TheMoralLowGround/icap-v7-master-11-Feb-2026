from . import get_left_pos_str, get_right_pos_str


def process(list_):
    """function that cleans the line data and only gives chunks close to each
    other"""
    output_list = []
    prev = None
    for item in list_:
        item_boundary = item[1]
        item_right_pos = get_right_pos_str.process(item_boundary)
        if prev:
            item_left_pos = get_left_pos_str.process(item_boundary)
            diff = item_left_pos - prev
            if diff > 100:
                break
            else:
                output_list.append(item)
            prev = item_right_pos
        else:
            output_list.append(item)
            prev = item_right_pos

    return output_list
