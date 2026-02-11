import traceback
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_extract_substring_function(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_extract_substring_function, input_text, rule_inputs
            )
        output_text = input_text
        try:
            start_index = int(rule_inputs["startIndex"])
        except:
            start_index = 0
        try:
            end_index = int(rule_inputs["endIndex"])
        except:
            end_index = len(input_text)

        return output_text[start_index:end_index]

    except:
        print(traceback.print_exc())
        return output_text
