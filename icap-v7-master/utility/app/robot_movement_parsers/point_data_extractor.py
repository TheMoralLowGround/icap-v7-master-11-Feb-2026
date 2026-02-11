def process(line_data_multi, point, find_point_extra):
    """takes in a multi line data, point [anchor point/chunks] and extra chunks of the anchor.
    And returns the data of the anchor"""
    chunk_list = []

    if len(find_point_extra) > 0:
        for i, line_data in enumerate(line_data_multi):
            list_ = []
            for chunk in line_data[0]:
                list_.append(chunk[0])

            found_count = 0
            for word in find_point_extra:
                if word in list_:
                    found_count += 1
            if found_count > 1:
                for chunk in line_data[0]:
                    found = False
                    if point in chunk[0]:
                        if not found:
                            # modified by emon on 14/05/2022. Not sure where line_data was used
                            return chunk  # , line_data
    else:
        for chunk in line_data_multi[0][0]:
            found = False
            if point in chunk[0]:
                if not found:
                    return chunk
