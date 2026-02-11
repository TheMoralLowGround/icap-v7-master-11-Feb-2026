import re
import traceback


def apply_remove_duplicates_from_string(rule_inputs, input_text):
    try:
        if ";" in input_text:
            input_text = input_text.strip()
            y = [c.strip() for c in re.split(";", input_text)]
            y = list(set(y))
            output = (";").join(y)
            return output
        else:
            return input_text
    except:
        print(traceback.print_exc())
        return input_text
