from . import find_line, value_to_the_right


def process(data_word_only, data, find_key_a, find_key_b):
    try:
        line_data = find_line.process(data_word_only, data, find_key_a)
        find_key = find_key_a
    except:
        line_data = find_line.process(data_word_only, data, find_key_b)
        find_key = find_key_b
    try:
        text = line_data[0][0][0][0]
        output_text = text.split(":", 2)[1]
    except:
        output_text = value_to_the_right.process(
            data_word_only, data, find_key_a, find_key_b
        )

    return output_text
