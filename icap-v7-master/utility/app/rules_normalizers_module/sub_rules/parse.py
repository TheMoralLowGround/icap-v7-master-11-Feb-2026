import re
import traceback

from .shape_converter import str_to_shape


def parse_index_finder(rule_inputs, input_text):
    try:
        output_text = input_text
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"]

        string_manipulation_type = rule_inputs["value"]["type"]
        if string_manipulation_type == "string":
            idx = output_text.lower().find(manipulative_value.lower())
            return idx
        elif string_manipulation_type == "shape":
            manipulative_shape = str_to_shape(manipulative_value)
            idx = output_shape.find(manipulative_shape)
            return idx
        else:
            idx = re.search(manipulative_value, output_text).start()
            return idx
    except:
        # print(traceback.print_exc())
        return -1
