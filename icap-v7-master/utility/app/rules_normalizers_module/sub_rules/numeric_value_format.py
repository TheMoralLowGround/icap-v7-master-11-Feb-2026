"""
Currency Formatting to NA Standard
==================================

Overview:
---------
This script provides functions to validate and format numeric strings to match the North American (NA) currency format standard.
It ensures proper formatting of strings containing numbers, commas, periods, and apostrophes.

Functions:
----------

1. **is_valid_string(input_string, trigger_initial_string_check=False, trigger_final_string_check=False):**
   Validates whether a string meets specific formatting rules.

   Parameters:
   - `input_string` (str): The string to validate.
   - `trigger_initial_string_check` (bool): Optional. If `True`, checks if the string contains unwanted characters.
   - `trigger_final_string_check` (bool): Optional. If `True`, checks if the string matches a final valid format (e.g., `12.34`).

   Returns:
   - `bool`: `True` if the string is valid, `False` otherwise.

2. **set_dot_when_both_comma_dot_present(input_string):**
   Resolves conflicts in strings containing both commas and periods. Prioritizes the period as the decimal separator.

   Parameters:
   - `input_string` (str): The string containing both commas and periods.

   Returns:
   - `str`: The corrected string with commas and periods formatted appropriately.

3. **apply_format_currency_to_na_standard(input_string):**
   Formats a numeric string to match the NA standard.

   Parameters:
   - `input_string` (str): The input string to format.

   Returns:
   - `str`: The formatted string in NA standard if valid. Returns the original string if invalid or if an error occurs.

   Functionality:
   --------------
   - Validates the input string using `is_valid_string`.
   - Replaces apostrophes with commas where appropriate.
   - Ensures proper decimal formatting:
     - Adds `.00` for integers without a decimal.
     - Handles strings with both commas and periods using `set_dot_when_both_comma_dot_present`.
   - Validates the final format before returning the result.

Error Handling:
---------------
- Provides detailed error messages and retains the original string if the formatting fails.
- Prints traceback information in case of exceptions.

Dependencies:
-------------
- `re`: For regular expression-based string validation.
- `traceback`: For detailed error handling and logging.

Usage:
------
This script is suitable for:
- Currency formatting pipelines.
- Data cleaning and standardization tasks.
- Validating and correcting numeric string formats.

Examples:
---------
```python
# Example 1: Formatting a valid string
input_string = "1,234.56"
formatted_string = apply_format_currency_to_na_standard(input_string)
print(formatted_string)  # Output: "1234.56"

# Example 2: Handling invalid strings
input_string = "1a23.45"
formatted_string = apply_format_currency_to_na_standard(input_string)
# Output: "Error: 1a23.45 contains Alphabet/Special character, can't proceed with the conversion to the NA standard"

# Example 3: Handling strings with both commas and periods
input_string = "1,234.56"
formatted_string = set_dot_when_both_comma_dot_present(input_string)
print(formatted_string)  # Output: "1234.56"
"""

import re
import traceback
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def is_valid_string(
    input_string, trigger_initial_string_check=False, trigger_final_string_check=False
):
    if trigger_initial_string_check:
        if ("," in input_string) and ("." in input_string) and ("'" in input_string):
            return False
        else:
            True

    if trigger_final_string_check:
        if (
            (input_string.count(".") == 1)
            and ("," not in input_string)
            and ("'" not in input_string)
            and (input_string[-3] == ".")
        ):
            return True
        else:
            return False

    pattern = r"^[0-9,.']+$"
    return bool(re.match(pattern, input_string))


def set_dot_when_both_comma_dot_present(input_string):
    if input_string.rfind(".") > input_string.rfind(","):
        idx = input_string.rfind(".")
        input_string = input_string[:idx].replace(".", "") + input_string[idx:]
        return input_string.replace(",", "")
    elif input_string.rfind(".") < input_string.rfind(","):
        idx = input_string.rfind(",")
        input_string = (
            input_string[:idx].replace(".", "") + "." + input_string[idx + 1 :]
        )
        return input_string.replace(",", "")


def apply_format_currency_to_na_standard(input_string):
    try:
        if isinstance(input_string, list):
            return perform_list_inputs_rules(
                apply_format_currency_to_na_standard, input_string
            )
        input_string = input_string.strip()
        input_string_main = input_string
        input_string = input_string.replace("^", "")

        if not is_valid_string(input_string):
            print(
                f"Error: {input_string} contains Alphabet/Special character, can't proceed with the conversion to the NA standard"
            )
            return input_string_main

        if not is_valid_string(input_string, True):
            print(
                f"Error: {input_string_main} : invalid format, can't proceed with the conversion to the NA standard"
            )
            return input_string_main

        if "'" in input_string:
            if input_string[-3] == ",":
                input_string = input_string[:-3] + "." + input_string[-2:]
            input_string = input_string.replace("'", ",")

        if ("," not in input_string) and ("." not in input_string):
            input_string = input_string + ".00"
        elif ("," not in input_string) and ("." in input_string):
            if input_string[-4] == ".":
                input_string = input_string.replace(".", "")
                input_string = input_string + ".00"
            else:
                input_string = input_string
        elif ("," in input_string) and ("." not in input_string):
            if input_string[-4] == ",":
                input_string = input_string.replace(",", "")
                input_string = input_string + ".00"
            else:
                input_string = input_string.replace(",", ".")
                input_string = input_string
        elif ("," in input_string) and ("." in input_string):
            input_string = set_dot_when_both_comma_dot_present(input_string)

        if is_valid_string(input_string, False, True):
            return input_string
        else:
            print(
                f"Error: {input_string_main} : invalid format, can't proceed with the conversion to the NA standard"
            )
            return input_string_main

    except:
        print(traceback.print_exc())
        return input_string
