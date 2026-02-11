import re
import traceback

from .shape_converter import str_to_shape


def apply_ends_with_function(rule_inputs, input_text):
    try:
        output_text = input_text
        input_text_lower_case = input_text.lower()
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"]
        string_manipulation_type = rule_inputs["value"]["type"]
        manipulative_shape = str_to_shape(manipulative_value)

        if string_manipulation_type == "string":
            if input_text_lower_case.endswith(manipulative_value.lower()):
                return True
        elif string_manipulation_type == "shape":
            if output_shape.endswith(manipulative_shape):
                return True
        else:
            return bool(re.search(manipulative_value + "$", output_text))
        return False
    except:
        print(traceback.print_exc())
        return True
