from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_dimension_sep_fix(input_text):
    if isinstance(input_text, list):
        return perform_list_inputs_rules(apply_dimension_sep_fix, input_text)
    splitters = ["x", "X", "*"]
    count_check = dict()
    for sp in splitters:
        count = input_text.count(sp)
        if count > 0:
            count_check[sp] = count

    if count_check:
        splitter_taken = max(count_check, key=count_check.get)
        if input_text.count(splitter_taken) == 2:
            return input_text
        input_text = input_text.replace("  ", " ")
        output = ""
        for c_idx, c in enumerate(input_text):
            try:
                if (
                    input_text[c_idx - 1].isdigit()
                    and input_text[c_idx + 1].isdigit()
                    and c.isspace()
                ):
                    output += splitter_taken
                else:
                    output += c
            except:
                output += c
        return output
    else:
        return input_text
