import traceback
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


# Written by Emon on October 24 2023
def apply_correct_data_type(rule_inputs, input_string):
    """
    This function converts characters of specific indexes in a given string to their Correct OCR counterpart
    """
    try:
        if isinstance(input_string, list):
            return perform_list_inputs_rules(
                apply_correct_data_type, input_string, rule_inputs
            )
        # Define character mappings for OCR correction
        numeric_mappings = {
            "O": "0",
            "Q": "0",
            "q": "0",
            "o": "0",
            "I": "1",
            "l": "1",
            "i": "1",
            "S": "5",
            "s": "5",
        }

        alpha_mappings = {value: key for key, value in numeric_mappings.items()}

        pattern = rule_inputs["pattern"]
        alpha_indices = [i for i, k in enumerate(pattern) if k == "A"]
        num_indices = [i for i, k in enumerate(pattern) if k == "N"]
        output_string = ""
        for char_idx, char in enumerate(input_string):
            if char_idx in alpha_indices and char.isdigit():
                try:
                    if char.isdigit():
                        try:
                            char = alpha_mappings[
                                char
                            ].upper()  # replace_from_the dictionary
                        except:
                            # print(traceback.print_exc())
                            pass

                    elif char.isalpha():
                        char = char.upper()
                    else:
                        pass
                except:
                    # print(traceback.print_exc())
                    pass

            elif char_idx in num_indices and char.isalpha():
                try:
                    char = numeric_mappings[char]
                except:
                    # print(traceback.print_exc())
                    pass

            else:
                pass

            output_string += char
        return output_string

    except:
        print(traceback.print_exc())
        return input_string
