from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def set_uppercase_values_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                set_uppercase_values_rule, input_text, rule_inputs
            )
        return input_text.upper()
    except:
        return input_text


def set_lowercase_values_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                set_lowercase_values_rule, input_text, rule_inputs
            )
        return input_text.lower()
    except:
        return input_text
