import re
import traceback

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_startswithv5_function(rule_inputs, input_text):
    # v5.0.19102022 Replace Version not working for whole string match
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_startswithv5_function, input_text, rule_inputs
            )
        output_text = input_text
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"]
        string_manipulation_type = rule_inputs["value"]["type"]
        replace_value = rule_inputs["replaceWith"]
        if string_manipulation_type == "string":
            if (
                manipulative_value == "."
            ):  # Added on 24/12/2022 - as regex match takes "." as any char
                return output_text.replace(".", replace_value)
            if output_text.lower() == manipulative_value.lower():
                return replace_value
            else:
                x = re.compile(manipulative_value, re.IGNORECASE)
                x = x.sub(replace_value, output_text)
                return x
        elif string_manipulation_type == "shape":
            manipulative_shape = str_to_shape(manipulative_value)
            shape_idx = output_shape.find(manipulative_shape)
            if shape_idx > -1:
                return (
                    output_text[:shape_idx]
                    + replace_value
                    + output_text[len(manipulative_shape) :].strip()
                )

        else:
            if manipulative_value == "\s+" or manipulative_value == "\s*":
                changed_value = re.sub("\s+", replace_value, output_text)
                return changed_value
            else:
                search_regex = re.compile(manipulative_value)
                try:
                    re_span = search_regex.search(output_text).span()
                except:
                    return output_text
                if re_span:
                    return (
                        output_text[: re_span[0]]
                        + replace_value
                        + output_text[re_span[1] :].strip()
                    )
                else:
                    return output_text
    except:
        print(traceback.print_exc())
        return input_text
