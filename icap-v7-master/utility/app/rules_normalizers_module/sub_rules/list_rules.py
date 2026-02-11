def perform_list_inputs_rules(rule_function, input_text, rule_inputs=None):
    new_input_text = []
    for text in input_text:
        new_input_text.append(rule_function(rule_inputs, text))
    return new_input_text
