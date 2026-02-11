"""
Conditioned Rule Application
=============================

Overview:
---------
This script provides utilities to apply conditional and manipulative rules on text.
It evaluates a condition on the input text and applies a sub-rule transformation if the condition is met.

Functions:
----------

1. **check_condition(rule_inputs, input_text):**
   Checks if the specified condition is met for the given input text.

   Parameters:
   - `rule_inputs` (dict): A dictionary containing the rule's condition and value.
     - `"condition"` (str): The type of condition (e.g., `doesNotContain`, `startsWithShape`).
     - `"value"` (str): The value against which the condition is evaluated.
   - `input_text` (str): The text to check the condition against.

   Returns:
   - `bool`: `True` if the condition is met, otherwise `False`.

   Supported Conditions:
   - `doesNotContain`: Returns `True` if `value` is not in `input_text`.
   - `doesNotContainShape`: Uses `str_to_shape` to check if `value` is not in the shape of `input_text`.
   - `startsWithShape`: Checks if the shape of `input_text` starts with the shape of `value`.
   - `containsRegex`: Evaluates if a regex pattern matches any part of `input_text`.

2. **apply_subrule(rule_inputs, input_text):**
   Modifies the input text based on the specified sub-rule.

   Parameters:
   - `rule_inputs` (dict): A dictionary containing the sub-rule type and its input.
     - `"subRule"` (str): The type of transformation to apply (e.g., `addPrefix`, `deleteFromString`).
     - `"subRuleInput"` (str): The value used by the sub-rule for transformation.
   - `input_text` (str): The text to be transformed.

   Returns:
   - `str`: The transformed text after applying the sub-rule.

   Supported Sub-Rules:
   - `addPrefix`: Adds `subRuleInput` as a prefix to `input_text`.
   - `deleteFromString`: Removes all characters from `input_text` starting from the first occurrence of `subRuleInput`.

3. **apply_conditioned_rule(rule_inputs, input_text):**
   Evaluates a condition and applies a sub-rule if the condition is met.

   Parameters:
   - `rule_inputs` (dict): A dictionary containing both condition and sub-rule definitions.
     - `"condition"` (str): The type of condition to evaluate.
     - `"value"` (str): The value used for the condition.
     - `"subRule"` (str): The type of transformation to apply.
     - `"subRuleInput"` (str): The value used for the transformation.
   - `input_text` (str): The text to evaluate and potentially transform.

   Returns:
   - `str`: The final transformed text if the condition is met, otherwise the original text.

   Example:
   ```python
   rule_inputs = {
       "condition": "doesNotContain",
       "value": "test",
       "subRule": "addPrefix",
       "subRuleInput": "Prefix_"
   }
   input_text = "example"
   result = apply_conditioned_rule(rule_inputs, input_text)
   print(result)  # Output: "Prefix_example"
"""

import re
import traceback

from .shape_converter import str_to_shape
from app.rules_normalizers_module.sub_rules.list_rules import perform_list_inputs_rules


def check_condition(rule_inputs, input_text):
    """Check if the condition is met or not"""
    condition = rule_inputs.get("condition")
    condition_value = rule_inputs.get("value")
    if condition == "doesNotContain":
        if condition_value not in input_text:
            return True
    elif condition == "doesNotContainShape":
        if str_to_shape(condition_value) not in str_to_shape(input_text):
            return True
    elif condition == "startsWithShape":
        if str_to_shape(input_text).startswith(str_to_shape(condition_value)):
            return True
    elif condition == "containsRegex":
        return bool(re.search(condition_value, input_text))

    return False


def apply_subrule(rule_inputs, input_text):
    """modify input text using the subrule type and value"""
    sub_rule = rule_inputs.get("subRule")
    sub_rule_input = rule_inputs.get("subRuleInput")
    output_text = input_text
    if sub_rule == "addPrefix":
        output_text = sub_rule_input + input_text
        return output_text
    elif sub_rule == "deleteFromString":
        try:
            find_idx = output_text.lower().find(sub_rule_input.lower())
            if find_idx > -1:
                output_text = output_text[:find_idx]
            return output_text.strip()
        except:
            pass
    return output_text


def apply_conditioned_rule(rule_inputs, input_text):
    try:
        if isinstance(input_text, list):
            return perform_list_inputs_rules(
                apply_conditioned_rule, input_text, rule_inputs
            )
        condition_met = check_condition(rule_inputs, input_text)
        output_text = input_text
        if condition_met:
            output_text = apply_subrule(rule_inputs, input_text)

        return output_text
    except:
        print(traceback.print_exc())
        return input_text
