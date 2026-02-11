import re

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_exclude_rules_on(rule_inputs, input_text):
    if isinstance(input_text, list):
        return perform_list_inputs_rules(
            apply_exclude_rules_on, input_text, rule_inputs
        )
    output_text = input_text
    output_shape = str_to_shape(output_text)
    manipulative_value = rule_inputs["value"]["value"]
    string_manipulation_type = rule_inputs["value"]["type"]

    if string_manipulation_type == "string":
        x = re.compile(re.escape(manipulative_value), re.IGNORECASE)
        x = x.sub("", output_text)
        return x.strip()
    elif string_manipulation_type == "shape":
        manipulative_shape = str_to_shape(manipulative_value)
        find_idx = output_shape.find(manipulative_shape)
        if find_idx > -1:
            output_text = (
                output_text[:find_idx]
                + output_text[find_idx + len(manipulative_shape) :]
            )
            return output_text.strip()
    else:
        if manipulative_value == "\s+":
            output_text = output_text.replace(" ", "")
        else:
            output_text = re.sub(manipulative_value, "", output_text)
        return output_text.strip()
    return output_text
