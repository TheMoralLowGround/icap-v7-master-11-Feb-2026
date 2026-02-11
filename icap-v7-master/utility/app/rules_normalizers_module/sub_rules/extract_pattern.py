import re
import traceback

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_extract_pattern(rule_inputs, input_text):
    if isinstance(input_text, list):
        return perform_list_inputs_rules(apply_extract_pattern, input_text, rule_inputs)
    output_text = input_text
    output_shape = str_to_shape(output_text)
    manipulative_value = rule_inputs["value"]["value"]
    string_manipulation_type = rule_inputs["value"]["type"]

    if string_manipulation_type == "string":
        # Edited by emon on 09/08/2022
        find_idx = output_text.lower().find(manipulative_value.lower())
        if find_idx > -1:
            output_text = output_text[find_idx : len(manipulative_value)]
        return output_text.strip()

    elif string_manipulation_type == "shape":
        manipulative_shape = str_to_shape(manipulative_value)
        find_idx = output_shape.find(manipulative_shape)
        if find_idx > -1:
            output_text = output_text[find_idx : (find_idx + len(manipulative_shape))]
            return output_text.strip()
    else:
        try:
            match = re.search(manipulative_value, output_text, re.IGNORECASE)
            if match:
                return match.group(0)
        except:
            print(traceback.print_exc())
            return input_text
    return input_text
