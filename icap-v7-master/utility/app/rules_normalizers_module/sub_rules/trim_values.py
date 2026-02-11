from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def trim_values_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(trim_values_rule, input_text, rule_inputs)
        return input_text.strip()
    except:
        return input_text
