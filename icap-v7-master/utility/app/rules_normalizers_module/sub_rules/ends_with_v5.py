"""
EndsWith V5 Rule Application
=============================

Overview:
---------
This script provides functionality for advanced text manipulation based on matching conditions.
It allows replacing parts of a string using conditions based on string content, shape, or regular expressions.

Functions:
----------

1. **apply_endswithv5_function(rule_inputs, input_text):**
   Applies the EndsWith V5 transformation to the given input text.

   Parameters:
   - `rule_inputs` (dict): Contains the rule's conditions and transformation details.
     - `"value"` (dict):
       - `"value"` (str): The manipulative value to search for.
       - `"type"` (str): The type of the value, which can be:
         - `"string"`: Matches the exact string.
         - `"shape"`: Matches based on the shape of the string (requires `str_to_shape`).
         - Regular expression patterns for complex matching.
     - `"replaceWith"` (str): The value that will replace the matched part of the input text.
   - `input_text` (str): The input string to be transformed.

   Returns:
   - `str`: The modified string if the condition is met and the transformation is applied,
            or the original string if no condition is satisfied.

   Functionality:
   --------------
   - For `"string"` type:
     - If the `manipulative_value` is `"."`, it replaces all occurrences of `"."` with `replaceWith`.
     - If `input_text` matches `manipulative_value` (case-insensitive), it replaces the entire string.
     - Otherwise, it searches for `manipulative_value` using regex and replaces matched substrings.
   - For `"shape"` type:
     - Converts both `input_text` and `manipulative_value` to their shape representations (via `str_to_shape`).
     - If the shape of `manipulative_value` is found in the shape of `input_text`, it replaces it with `replaceWith`.
   - For regular expressions:
     - If the `manipulative_value` is `"\s+"` or `"\s*"`, it replaces whitespace patterns with `replaceWith`.
     - For other patterns, it uses regex to search for and replace matching substrings.

Error Handling:
---------------
The script gracefully handles exceptions during execution. If any error occurs, the original `input_text` is returned,
and a traceback is printed for debugging purposes.

Dependencies:
-------------
- `str_to_shape`: A custom utility (imported from `.shape_converter`) to convert text into its "shape" representation.
- `traceback`: For printing detailed error traces during exception handling.
- `re`: For regex-based pattern matching and replacement.

Usage:
------
This function is suitable for:
- Advanced text manipulation pipelines.
- Automated string correction or formatting workflows.
- Regex-based string transformations.

Example:
--------
```python
from shape_converter import str_to_shape

rule_inputs = {
    "value": {"value": "example", "type": "string"},
    "replaceWith": "sample"
}

input_text = "This is an example."
result = apply_endswithv5_function(rule_inputs, input_text)
print(result)  # Output: "This is an sample."
"""

import re
import traceback

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_endswithv5_function(rule_inputs, input_text):
    # v5.0.19102022 Replace Version not working for whole string match
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_endswithv5_function, input_text, rule_inputs
            )
        output_text = input_text
        output_shape = str_to_shape(output_text)
        manipulative_value = rule_inputs["value"]["value"]
        string_manipulation_type = rule_inputs["value"]["type"]
        replace_value = rule_inputs["replaceWith"]
        if string_manipulation_type == "string":
            if (
                manipulative_value == "."
            ):  # Added on 24/12/2022 - as regex match takes "." as any char
                return output_text.replace(".", replace_value)
            if output_text.lower() == manipulative_value.lower():
                return replace_value
            else:
                x = re.compile(manipulative_value.strip(), re.IGNORECASE)
                x = x.sub(replace_value, output_text)
                return x
        elif string_manipulation_type == "shape":
            manipulative_shape = str_to_shape(manipulative_value)
            shape_idx = output_shape.find(manipulative_shape)
            if shape_idx > -1:
                return (
                    output_text[:shape_idx]
                    + replace_value
                    + output_text[len(manipulative_shape) :].strip()
                )

        else:
            if manipulative_value == "\s+" or manipulative_value == "\s*":
                changed_value = re.sub("\s+", replace_value, output_text)
                return changed_value
            else:
                search_regex = re.compile(manipulative_value)
                try:
                    re_span = search_regex.search(output_text).span()
                except:
                    return output_text
                if re_span:
                    return (
                        output_text[: re_span[0]]
                        + replace_value
                        + output_text[re_span[1] :].strip()
                    )
                else:
                    return output_text
    except:
        print(traceback.print_exc())
        return input_text
