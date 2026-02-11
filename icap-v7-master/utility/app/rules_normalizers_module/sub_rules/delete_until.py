import re

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_delete_Until(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_delete_Until, input_text, rule_inputs
            )
        output_text = input_text
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"]
        string_manipulation_type = rule_inputs["value"]["type"]

        if string_manipulation_type == "string":
            # Edited by emon on 09/08/2022
            find_idx = output_text.lower().find(manipulative_value.lower())
            if find_idx > -1:
                output_text = output_text[find_idx + len(manipulative_value) :]
            return output_text.strip()

        elif string_manipulation_type == "shape":
            manipulative_shape = str_to_shape(manipulative_value)
            find_idx = output_shape.find(manipulative_shape)
            if find_idx > -1:
                output_text = output_text[find_idx + len(manipulative_shape) :]
                return output_text.strip()
        else:
            output_text = re.split(manipulative_value, output_text)[-1]
            return output_text.strip()
    except:
        pass
    return input_text
