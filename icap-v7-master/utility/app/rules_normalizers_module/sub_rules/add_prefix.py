"""
Apply Prefix Rule
=================

Overview:
---------
This function applies a prefix to a given input text based on the provided rule configuration.

Functionality:
--------------
The function takes a rule input dictionary containing a prefix value and appends this prefix
to the beginning of the input text. If any error occurs during the operation, the function
returns the original input text.

Parameters:
-----------
- `rule_inputs` (dict): A dictionary containing the prefix configuration.
  - Key: `"value"` (str) - The prefix string to be applied.
- `input_text` (str): The original text to which the prefix is applied.

Returns:
--------
- `output_text` (str): The modified text with the prefix applied. If an error occurs,
  the original `input_text` is returned.

Example:
--------
### Input:
```python
rule_inputs = {"value": "Prefix_"}
input_text = "OriginalText"
"""

from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def apply_prefix_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(apply_prefix_rule, input_text, rule_inputs)
        output_text = input_text
        manipulative_value = rule_inputs["value"]
        output_text = manipulative_value + output_text
        return output_text
    except:
        return input_text
