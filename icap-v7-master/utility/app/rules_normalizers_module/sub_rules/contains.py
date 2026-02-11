import re
import traceback

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_contains_function(rule_inputs, input_text):
    try:
        output_text = input_text.strip()
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"].strip()
        string_manipulation_type = rule_inputs["value"]["type"]
        manipulative_shape = str_to_shape(manipulative_value)
        if string_manipulation_type == "string":
            if manipulative_value.lower() in output_text.lower():
                return True
        elif string_manipulation_type == "shape":
            if manipulative_shape in output_shape:
                return True
        else:
            return bool(re.search(manipulative_value, output_text))
        return False
    except:
        print(traceback.print_exc())
        return True


def apply_contains_function_list(rule_inputs, input_text):
    new_input_list = []
    if isinstance(input_text, list):
        for text in input_text:
            if apply_contains_function(rule_inputs, text):
                new_input_list.append(text)
    return new_input_list
