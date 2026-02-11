def process(line_data, point, find_point_extra):
    """Designed for single find"""
    """takes in a multi line data, point [anchor point/chunks] and extra chunks of the anchor.
    And returns the data of the anchor"""

    if len(find_point_extra) > 0:
        for i, line in enumerate(line_data):
            list_ = []
            for chunk in line[0]:
                list_.append(chunk[0])
            if all(word in list_ for word in find_point_extra):
                for chunk in line_data[0]:
                    found = False
                    if point in chunk[0]:
                        if not found:
                            return chunk
    else:
        for chunk in line_data[0][0]:
            if point in chunk[0]:
                return chunk
