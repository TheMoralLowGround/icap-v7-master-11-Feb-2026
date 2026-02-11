import math
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_round_decimal_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_round_decimal_rule, input_text, rule_inputs
            )
        if ("value" not in rule_inputs.keys()) or (rule_inputs.get("value") == ""):
            method = rule_inputs.get("condition")
            numerical_value = float(input_text)

            x = numerical_value

            if method == "up":
                x = math.ceil(numerical_value)

            elif method == "down":
                x = math.floor(numerical_value)

            else:
                x = round(numerical_value)
        else:
            numerical_value = float(input_text)
            round_upto = int(rule_inputs.get("value"))
            x = round(numerical_value, round_upto)

        output_text = str(x)

        return output_text

    except:
        return input_text
