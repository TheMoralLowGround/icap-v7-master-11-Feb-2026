from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_suffix_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(apply_suffix_rule, input_text, rule_inputs)
        output_text = input_text
        manipulative_value = rule_inputs["value"]
        output_text = output_text + manipulative_value
        return output_text
    except:
        return input_text
