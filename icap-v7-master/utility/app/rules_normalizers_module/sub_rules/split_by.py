def apply_split_by_seperator(rule_inputs, changed_text):
    try:
        input_text = changed_text
        manipulative_value = rule_inputs["value"]
        if type(manipulative_value) == dict:
            manipulative_value = manipulative_value["value"]
        if manipulative_value == "\n":
            split_data = input_text.split()
        else:
            split_data = input_text.split(manipulative_value)
        return split_data
    except:
        return None
