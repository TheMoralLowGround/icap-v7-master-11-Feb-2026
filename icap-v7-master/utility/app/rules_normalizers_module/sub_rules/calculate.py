import traceback
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_calculate_function(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_calculate_function, input_text, rule_inputs
            )
        manipulative_value = rule_inputs["value"]
        full_formula = input_text + manipulative_value
        answer = float(eval(full_formula))
        try:
            output_text = str(round(answer, 3))
            return output_text
        except:
            return answer
    except:
        print(traceback.print_exc())
        return input_text
