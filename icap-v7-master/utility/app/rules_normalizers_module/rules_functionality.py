import traceback

from app.address_modules.address_custom import custom_address_parser
from app.key_central.keychildren_appender import SKIP_LABELS, TO_BE_KEPT_INSIDE
from app.rules_normalizers_module.sub_rules import convert_date
from app.rules_normalizers_module.sub_rules.add_prefix import apply_prefix_rule
from app.rules_normalizers_module.sub_rules.add_suffix import apply_suffix_rule
from app.rules_normalizers_module.sub_rules.calculate import apply_calculate_function
from app.rules_normalizers_module.sub_rules.calculate_fields import (
    apply_calculate_fields,
)
from app.rules_normalizers_module.sub_rules.contains import apply_contains_function
from app.rules_normalizers_module.sub_rules.convert_decimal import (
    apply_convert_decimals_to_cw1,
)
from app.rules_normalizers_module.sub_rules.correct_data_type import (
    apply_correct_data_type,
)
from app.rules_normalizers_module.sub_rules.delete_from import apply_delete_from
from app.rules_normalizers_module.sub_rules.delete_until import apply_delete_Until
from app.rules_normalizers_module.sub_rules.ends_with import apply_ends_with_function
from app.rules_normalizers_module.sub_rules.ends_with_v5 import (
    apply_endswithv5_function,
)
from app.rules_normalizers_module.sub_rules.exclude import apply_exclude_rules_on
from app.rules_normalizers_module.sub_rules.extract import (
    apply_extract_substring_function,
)
from app.rules_normalizers_module.sub_rules.extract_pattern import apply_extract_pattern
from app.rules_normalizers_module.sub_rules.numeric_value_format import (
    apply_format_currency_to_na_standard,
)
from app.rules_normalizers_module.sub_rules.parse import parse_index_finder
from app.rules_normalizers_module.sub_rules.remove_duplicates_from_string import (
    apply_remove_duplicates_from_string,
)
from app.rules_normalizers_module.sub_rules.replace_function import (
    apply_replace_function,
)
from app.rules_normalizers_module.sub_rules.round_decimal import (
    apply_round_decimal_rule,
)
from app.rules_normalizers_module.sub_rules.split_by import apply_split_by_seperator
from app.rules_normalizers_module.sub_rules.starts_with import (
    apply_starts_with_function,
)
from app.rules_normalizers_module.sub_rules.starts_with_v5 import (
    apply_startswithv5_function,
)

"""
This script is a comprehensive data processing and transformation module that operates on structured hierarchical data, typically in JSON format. It allows for applying a wide range of rules and operations on the data, including:

1. Parsing and extracting specific information, such as dimensions, weights, volumes, package counts, temperatures, addresses, and incoterms, using dedicated parsers.

2. Text manipulation operations like replacing values, excluding patterns, extracting substrings, adding prefixes/suffixes, converting decimal formats, removing duplicates, and performing calculations.

3. Conditional operations like checking if a value contains, starts with, or ends with a specific pattern, and disregarding or modifying the data accordingly.

4. Value generation operations, such as copying values to new fields, splitting values based on separators, and generating new fields from parsed values.

5. Formatting operations like converting text to uppercase/lowercase, rounding decimal values, and formatting dates.

6. Handling of compound keys and address data, with specific rules for processing child nodes.

The script follows a hierarchical approach, processing data at multiple levels, including key nodes, child nodes, and parsed/generated nodes. It supports applying rules based on unique identifiers and accommodates different rule types for specific labels or data structures.

The script also includes functionality for merging rows based on conditions, distributing values across rows, and copying values to all rows or specific columns.

The operations are defined through a set of rules and configurations, allowing for flexible and customizable data transformations. It is designed to handle large-scale data processing tasks, with error handling and tracebacks for debugging purposes.

Sure, here's a summary for a new developer to understand this script:

The script is a data transformation and normalization module that operates on structured data in a hierarchical format, typically JSON. It consists of several sub-modules and functions that perform various operations on the data based on predefined rules.

The main function is `rules_centre`, which orchestrates the entire data processing pipeline. It takes in the input data, definitions, and configurations, and applies the appropriate rules to transform the data.

The script heavily relies on the `keyNode_level_rule` function, which processes each individual key node in the data. This function applies rules specific to that key node, such as replacing values, excluding patterns, extracting substrings, adding prefixes/suffixes, and more. It also handles compound keys and address data differently.

Several sub-modules and functions are imported from different parts of the codebase to perform specific operations. For example:

- `apply_replace_function` replaces values based on specific rules.
- `apply_exclude_rules_on` excludes values based on rules.
- `apply_extract_substring_function` extracts substrings from values.
- `custom_address_parser` handles address parsing and normalization.

The script also includes functions for processing rows, such as `merge_row_function`, `copy_to_all_rows_function`, and `copy_to_column_function`. These functions handle operations like merging rows based on conditions, copying values to all rows, and copying values to specific columns.

The script extensively uses exception handling and tracebacks to catch and log errors during execution.

Overall, the script is designed to be flexible and extensible, allowing developers to add new rules and operations as needed. It follows a modular approach, with different sub-modules responsible for specific operations.


"""


DEFINITIONS = None


def deeper_level_central_function(
    input_key_node_list,
    rules_applied_on,
    rules_applied_on_address_child,
    address_keys,
    key_node_list,
):
    try:
        output_key_node_list = list()
        extra_key_node_list = list()
        for x in input_key_node_list:
            x, extra_key_nodes_rule_born = keyNode_level_rule(
                x,
                rules_applied_on,
                rules_applied_on_address_child,
                address_keys,
                key_node_list,
            )
            if x:  # If not disgarded by contains/startsWith/EndsWith
                output_key_node_list.append(x)
            if extra_key_nodes_rule_born:
                extra_key_node_list += extra_key_nodes_rule_born

        return output_key_node_list, extra_key_node_list
    except:
        print(traceback.print_exc())
        return input_key_node_list, []


def get_children(parent, address_keys):
    global DEFINITIONS
    global MASTER_DICTIONARIES
    input_data = parent["v"]
    parent_id = parent["id"]
    parent_label = parent["label"]

    def get_digits(id_text):
        t = ""
        for c in id_text:
            if c.isdigit():
                t += c
        return t

    output = []
    if parent_label in address_keys:
        input_data = custom_address_parser(input_data, DEFINITIONS, MASTER_DICTIONARIES)
    else:  # Added by emon on 18/10/2022
        return []

    if type(input_data) != str and type(input_data) != dict:
        return []

    else:
        if type(input_data) == str:
            lines = input_data.splitlines()
            for line_idx, line in enumerate(lines):
                line_dict = dict()
                line_dict["type"] = "keyTextDetail"
                line_dict["label"] = ""
                line_dict["id"] = (
                    "keyTextDetail_" + get_digits(parent_id) + "_" + str(line_idx)
                )
                line_dict["v"] = line
                line_dict["children"] = []
                output.append(line_dict)

        else:
            count = 0
            for sub_key, sub_value in input_data.items():
                if sub_key in SKIP_LABELS:
                    continue
                if sub_key not in TO_BE_KEPT_INSIDE:
                    continue

                line_dict = dict()
                line_dict["type"] = "keyTextDetail"
                line_dict["label"] = sub_key
                line_dict["id"] = (
                    "keyTextDetail_" + get_digits(parent_id) + "_" + str(count)
                )
                line_dict["v"] = sub_value
                line_dict["children"] = []
                output.append(line_dict)
                count += 1

    return output


def execute_rule(rule, child):
    rule_type = rule["type"]
    rule_inputs = rule["inputs"]
    child_value = child["v"]
    if rule_type == "exclude":
        return apply_exclude_rules_on(rule_inputs, child_value)
    elif rule_type == "deleteFrom":
        return apply_delete_from(rule_inputs, child_value)
    elif rule_type == "replaceValue":
        return apply_replace_function(rule_inputs, child_value)
    elif rule_type == "extractSubstring":
        return apply_extract_substring_function(rule_inputs, child_value)
    elif rule_type == "contains":
        if apply_contains_function(rule_inputs, child_value):
            return child_value
        else:
            return None
    elif rule_type == "startsWith":
        if apply_starts_with_function(rule_inputs, child_value):
            return child_value
        else:
            return None
    elif rule_type == "endsWith":
        if apply_ends_with_function(rule_inputs, child_value):
            return child_value
        else:
            return None

    elif rule_type == "addPrefix":
        if apply_prefix_rule(rule_inputs, child_value):
            child_value = apply_prefix_rule(rule_inputs, child_value)
            return child_value
        else:
            return None
    elif rule_type == "addSuffix":
        if apply_suffix_rule(rule_inputs, child_value):
            child_value = apply_suffix_rule(rule_inputs, child_value)
            return child_value
        else:
            return None
    elif rule_type == "deleteUntil":
        if apply_delete_Until(rule_inputs, child_value):
            child_value = apply_delete_Until(rule_inputs, child_value)
            return child_value
        else:
            return None
    elif rule_type == "convertToUppercase":
        return child_value.upper()

    elif rule_type == "convertToLowercase":
        return child_value.lower()

    elif rule_type == "extractPattern":
        if apply_extract_pattern(rule_inputs, child_value):
            child_value = apply_extract_pattern(rule_inputs, child_value)
            return child_value
    elif rule_type == "roundDecimal":
        if apply_round_decimal_rule(rule_inputs, child_value):
            child_value = apply_round_decimal_rule(rule_inputs, child_value)
            return child_value
        else:
            return None
    elif rule_type == "correctDataType":
        if apply_correct_data_type(rule_inputs, child_value):
            child_value = apply_correct_data_type(rule_inputs, child_value)
            return child_value

    return child["v"]


def process_rules(key_node, rules_data_set, address_keys, key_node_list):
    try:
        disregard = False

        def execute_inner_child_rule():
            # children_updated = True
            # children_updated_labels.append(input_node["label"])
            def update_inner_children(input_child_name, input_node, rule):
                children = input_node["children"]
                return_children = list()
                for child_idx, child in enumerate(children[:]):
                    if child["label"] == input_child_name:
                        child["v"] = execute_rule(rule, child)
                    if child["v"] and child["label"] != "children":
                        child["modifed_by_innerchild_rule"] = True
                        return_children.append(child)
                return return_children

            key_node["children"] = update_inner_children(child_key_name, key_node, rule)
            return key_node

        def get_child_value(input_node, child_key_name):
            children = input_node["children"]
            for child_idx, child in enumerate(children[:]):
                if child["label"] == child_key_name:
                    return child["v"]
            return ""

        generation_count = 0
        extra_key_nodes = []
        inner_child_rule = False
        changed_text = key_node["v"]

        rule_applied_on_address_parent = False

        if rules_data_set:
            for rules in rules_data_set:
                if not rules:
                    return key_node, extra_key_nodes
                else:
                    for rule_idx, rule in enumerate(rules["data"]):
                        try:
                            rule_inputs = rule["inputs"]
                        except:
                            rule_inputs = rule["data"]["inputs"]

                        child_key_name = rules.get("childName")

                        if child_key_name:
                            inner_child_rule = True

                        if not inner_child_rule and (rules["label"] in address_keys):
                            rule_applied_on_address_parent = True
                        if rule["type"] == "exclude":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = apply_exclude_rules_on(
                                    rule_inputs, changed_text
                                )

                        elif rule["type"] == "deleteFrom":
                            if inner_child_rule:
                                execute_inner_child_rule()
                            else:
                                value_to_delete = rule["inputs"]["value"]["value"]
                                if value_to_delete:
                                    changed_text = apply_delete_from(
                                        rule_inputs, changed_text
                                    )

                        elif rule["type"] == "deleteUntil":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                value_to_delete = rule["inputs"]["value"]["value"]
                                if value_to_delete:
                                    changed_text = apply_delete_Until(
                                        rule_inputs, changed_text
                                    )

                        elif rule["type"] == "parseFrom":
                            parse_trigger = rule["inputs"]["value"]["value"]
                            field_name = rule["inputs"]["fieldName"]["fieldInfo"][
                                "keyValue"
                            ]
                            # field_name = rule["inputs"]["fieldName"]
                            if parse_trigger:
                                idx = parse_index_finder(rule_inputs, changed_text)
                                if idx >= 0:
                                    parse_at = idx
                                    new_text = changed_text[parse_at:]
                                    changed_text = changed_text[:parse_at]
                                    parse_key_node = key_node.copy()
                                    parse_key_node["id"] = (
                                        parse_key_node["id"] + "_parsed_" + field_name
                                    )
                                    parse_key_node["label"] = field_name
                                    parse_key_node["v"] = new_text.strip()
                                    parse_key_node["unique_id"] = (
                                        parse_key_node.get("unique_id")
                                        + "_"
                                        + field_name
                                    )
                                    generation_count += 1
                                    parse_key_node_children = get_children(
                                        parse_key_node, address_keys
                                    )
                                    parse_key_node["children"] = parse_key_node_children

                                    extra_key_nodes.append(parse_key_node)

                        elif rule["type"] == "replaceValue":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_replace_function(
                                        rule_inputs, changed_text
                                    )
                                except:
                                    print(traceback.print_exc())

                        elif rule["type"] == "convertDecimalsToCW1":
                            try:
                                changed_text = apply_convert_decimals_to_cw1(
                                    rule_inputs, changed_text
                                )

                            except:
                                print(traceback.print_exc())

                        elif rule["type"] == "copyValue":
                            copy_to = rule_inputs["value"]["fieldInfo"]["keyValue"]
                            # copy_to = rule_inputs["value"]["value"]
                            copy_to_key_node = key_node.copy()
                            copy_to_key_node["id"] = (
                                copy_to_key_node["id"] + "_" + str(rule_idx)
                            )
                            copy_to_key_node["label"] = copy_to
                            if inner_child_rule:
                                copy_to_key_node["v"] = get_child_value(
                                    key_node, child_key_name
                                )
                                copy_to_key_node_children = get_children(
                                    copy_to_key_node, address_keys
                                )
                                copy_to_key_node["children"] = copy_to_key_node_children

                            else:
                                copy_to_key_node["v"] = changed_text.strip()
                                copy_to_key_node_children = get_children(
                                    copy_to_key_node, address_keys
                                )
                                copy_to_key_node["children"] = copy_to_key_node_children
                            if copy_to_key_node["v"]:
                                copy_to_key_node["unique_id"] = (
                                    copy_to_key_node["unique_id"] + "_" + copy_to
                                )
                                copy_to_key_node["copyValue"] = True
                                generation_count += 1
                                extra_key_nodes.append(copy_to_key_node)

                        elif rule["type"] == "addPrefix":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_prefix_rule(
                                        rule_inputs, changed_text
                                    )
                                except:
                                    print(traceback.print_exc())

                        elif rule["type"] == "addSuffix":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_suffix_rule(
                                        rule_inputs, changed_text
                                    )
                                except:
                                    print(traceback.print_exc())

                        elif rule["type"] == "formatDate":
                            manual_rule_place_on_date = True
                            try:
                                # print("before changed_text", changed_text)
                                changed_text = convert_date.process(changed_text)
                                # print("after changed_text", changed_text)
                            except:
                                pass

                        elif rule["type"] == "formatCurrencyToNAStandard":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_format_currency_to_na_standard(
                                        changed_text
                                    )
                                except:
                                    pass

                        elif rule["type"] == "contains":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                if not apply_contains_function(
                                    rule_inputs, changed_text
                                ):
                                    disregard = True

                        elif rule["type"] == "endsWith":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                if not apply_ends_with_function(
                                    rule_inputs, changed_text
                                ):
                                    disregard = True

                        elif rule["type"] == "endsWithV5":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_endswithv5_function(
                                        rule_inputs, changed_text
                                    )
                                except:
                                    print(traceback.print_exc())
                        elif rule["type"] == "startsWithV5":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = apply_startswithv5_function(
                                        rule_inputs, changed_text
                                    )
                                except:
                                    print(traceback.print_exc())
                        elif rule["type"] == "trim":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                try:
                                    changed_text = changed_text.strip()
                                except:
                                    print(traceback.print_exc())
                        elif rule["type"] == "startsWith":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                if not apply_starts_with_function(
                                    rule_inputs, changed_text
                                ):
                                    disregard = True

                        elif rule["type"] == "extractSubstring":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = apply_extract_substring_function(
                                    rule_inputs, changed_text
                                )
                        elif rule["type"] == "removeDuplicatesFromString":
                            changed_text = apply_remove_duplicates_from_string(
                                rule_inputs, changed_text
                            )

                        elif rule["type"] == "extractPattern":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = apply_extract_pattern(
                                    rule_inputs, changed_text
                                )

                        elif rule["type"] == "convertToUppercase":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = changed_text.upper()

                        elif rule["type"] == "convertToLowercase":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = changed_text.lower()

                        elif rule["type"] == "calculate":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = apply_calculate_function(
                                    rule_inputs, changed_text
                                )
                        elif rule["type"] == "calculateFields":
                            try:
                                target_field = rule_inputs["value"]["fieldInfo"][
                                    "keyValue"
                                ]
                                target_condition = rule_inputs["condition"]
                                target_value = None
                                print("target_field", target_field)
                                for target_keynode in key_node_list:
                                    if target_keynode.get("label") == target_field:
                                        target_value = target_keynode.get("v")
                                        break

                                changed_text = apply_calculate_fields(
                                    changed_text, target_condition, target_value
                                )

                            except:
                                print(traceback.print_exc())

                        elif rule["type"] == "roundDecimal":
                            if inner_child_rule:
                                key_node = execute_inner_child_rule()
                            else:
                                changed_text = apply_round_decimal_rule(
                                    rule_inputs, changed_text
                                )
                        elif rule["type"] == "correctDataType":
                            if inner_child_rule:
                                keyNode = execute_inner_child_rule()
                            else:
                                changed_text = apply_correct_data_type(
                                    rule_inputs, changed_text
                                )

                        elif rule["type"] == "splitBySeparator":
                            if inner_child_rule:
                                pass
                            else:
                                if apply_split_by_seperator(rule_inputs, changed_text):
                                    split_data = apply_split_by_seperator(
                                        rule_inputs, changed_text
                                    )

                                    """FOR REFERENCES DUPLICATES ARE TO BE REMOVED"""
                                    if key_node.get("qualifierParent") == "references":
                                        split_data = list(set(split_data))

                                    changed_text = split_data[0]

                                    for data_idx, data in enumerate(split_data[1:]):
                                        if data:
                                            split_key_node = key_node.copy()
                                            split_key_node["v"] = data.strip()
                                            split_key_node["splitAndDuplicated"] = True
                                            extra_key_nodes.append(split_key_node)

                if rule_applied_on_address_parent:
                    try:
                        key_node["v"] = changed_text.strip()
                        updated_children = get_children(key_node, address_keys)
                        prev_lookup_child_list = [
                            x
                            for x in key_node.get("children")
                            if x.get("origin") == "auto_lookup"
                        ]
                        if updated_children and prev_lookup_child_list:
                            updated_children += prev_lookup_child_list
                        key_node["children"] = updated_children
                    except:
                        print(traceback.print_exc())
                        pass

            try:
                key_node["v"] = changed_text.strip()
            except:
                print(traceback.print_exc())
                pass

            if not disregard and changed_text.strip():
                # print(extra_key_nodes)
                return key_node, extra_key_nodes
            else:
                return None, extra_key_nodes
        else:
            key_node, extra_key_nodes
    except:
        print(traceback.print_exc())
        return key_node, []


def keyNode_level_rule(
    key_node,
    rules_applied_on,
    rules_applied_on_address_child,
    address_keys,
    key_node_list,
):
    """For key_node level rules, there could be of three types.
    1. MotherNode rule
    2. InnerChld rule (for addresses) Eg: Chaning the addressline1 of shipper
    3. Combo of this. (Exclude LTD from whole of consignee and also another rule that copies city to incotermsLocation)
    """
    extra_key_nodes = list()
    label = key_node["label"]
    key_node_unique_id = key_node.get("unique_id")
    auto_extracted = key_node.get("is_auto_extracted",False)
    identifier = label


    if key_node_unique_id:
        if key_node.get("isCompoundKeyChild") == True:
            identifier = key_node["motherCompund"] + "_" + key_node_unique_id
        else:
            identifier = label + "_" + key_node_unique_id

    key_identifier_check_on_rules = any(key.startswith(identifier) for key in rules_applied_on.keys())
    key_identifier_check_on_address_child = any(key.startswith(identifier) for key in rules_applied_on_address_child.keys())
        
    # Checking if the label matches
    if key_identifier_check_on_rules or (
        key_identifier_check_on_address_child
    ):  # if keynode label
        original_text = key_node["v"]
        unique_id = None
        if key_identifier_check_on_address_child:
            rules_data_set = list()
            for x in rules_applied_on_address_child[identifier]:
                unique_id = x["unique_id"]
                # SpecialChange-31/08/2022 - CopyValue from Address Drop Down was not working
                if key_node.get("isCompoundKeyChild") == True:
                    data_to_append = {"label": label, "data": x["data"]}
                else:
                    data_to_append = {
                        "childName": x["childName"],
                        "data": x["data"],
                        "label": label,
                    }
                rules_data_set.append(data_to_append)
        else:
            if not auto_extracted:
                rules = rules_applied_on[identifier]["data"]
            else:
                # Control for auto extracted values take out only the matched key item for rules applied items.
                rules = next(
                    (v["data"] for k, v in rules_applied_on.items() if k.startswith(identifier)),
                    None
                )
            # if "unique_id" in rules_applied_on[label].keys():
            #     unique_id = rules_applied_on[label]["unique_id"]

            data_to_append = {"label": label, "data": rules}
            rules_data_set = [data_to_append]
        combo_trigger = False
        combo_data = list()
        if key_identifier_check_on_rules and (
            key_identifier_check_on_address_child
        ):
            changed_text = original_text
            # if "unique_id" in rules_applied_on[label].keys():
            #     unique_id = rules_applied_on[label]["unique_id"]
            combo_trigger = True
            if not auto_extracted:
                rules = rules_applied_on[identifier]["data"]
            else:
                # Control for auto extracted values take out only the matched key item for rules applied items.
                rules = next(
                    (v["data"] for k, v in rules_applied_on.items() if k.startswith(identifier)),
                    None
                )

            data_to_append = {
                "label": label,
                "data": rules,
            }
            combo_data = [data_to_append]

        # Placeholder to indicate unique id is correct or not
        breakout = False

        """Checking for unique id to apply a rule on a specific key_node"""
        if unique_id:
            if (label in unique_id) and not (
                unique_id.startswith(label)
            ):  # If it is a parsed field
                if not (
                    (label in key_node["unique_id"])
                    and (unique_id[:36] in key_node["unique_id"][:36])
                ):
                    breakout = True
            else:
                # print(unique_id, key_node["unique_id"] )
                if unique_id != key_node_unique_id:
                    breakout = True

        if not breakout:
            """For combo type of rule set, we process the mother node first and then proceed on childItems"""
            if combo_trigger:
                try:
                    key_node, generated_key_nodes_from_address = process_rules(
                        key_node, combo_data, address_keys, key_node_list
                    )
                    if generated_key_nodes_from_address:
                        extra_key_nodes += generated_key_nodes_from_address
                except:
                    print(traceback.print_exc())

            if rules_data_set:
                try:
                    key_node, generated_key_nodes = process_rules(
                        key_node, rules_data_set, address_keys, key_node_list
                    )
                    if generated_key_nodes:
                        extra_key_nodes += generated_key_nodes
                except:
                    print(traceback.print_exc())

        return key_node, extra_key_nodes

    else:
        return key_node, extra_key_nodes


def rules_centre(request_data, d_json, address_keys):
    # @Emon added 17/08/2022 CopyTo, ReplaceWith, DateConvert, CW1Convert
    # @Emon added 18/08/2022 Contains, EndsWith, StartsWith, ExtractSubstring
    # @Emon added 19/08/2022 Delete KeyNodes for contains, endsWith, StartsWith/All lowercaps for contains/Bug Fixes related to multiple rules
    # @Emon on 25/08/2022 - ReplaceWith Functionwith will only replace strings
    # @Emon on 31/08/2022 - Edited the CW1 Standard Decimal Conversion Function
    # @Emon on 31/08/2022 - Functionalized Node level processing to allow for re-rule application of rule borne children
    # @Emon on 09/09/2022 - Apply replace Function has been updated/Restored
    # @Emon on 09/09/2022 - Unique rules can be applied from now on
    # @EMon on 10/09/2022 - ReplaceWith can not be case sensitive
    # @Emon on 16/09/2022 - Key with Empty value using exclude will not appear, Address child bug fix(rules not not working on HP PPS SLI CONSIGNEE.NAME)
    # @Emon on 16/09/2022 - Exclude made ignorecase for string type
    # @Emon on 18/09/2022 - ReplaceWith bug fixed
    # @Emon on 19/09/2022 - Rules Structure Changed
    # @Emon on 20/09/2022 - Delete From bug fixed, Delete From renamed, Delete Until Added, Add Prefix added, Add Suffix Added
    # @Emon on 20/09/2022 - Shape converter not working - Bug fixed
    # @Emon on 24/09/2022 - Parsed Fields unique id mismatch issue - Bug fixed
    # @Emon on 24/09/2022 - Fixed DateConverted - If fails then key duplicated with old text
    # @Emon on 14/10/2022 - Fixed A bug that made keyNodes disappear for an emtpy rule #112233
    # @Emon on 18/10/2022 - Children will not be generated if not an address item
    # @Emon on 18/10/2022 - Code refactored.
    # @Emon on 18/10/2022 - Add Prefix/Suffix were working opposite
    # @Emon on 19/10/2022 - Code Refactored
    # @Emon on 23/10/2022 - removeDuplicatesFromString rule added
    # @Emon on 04/11/2022 - Bug fixes: Rules of different nodes with same label was not working. And rules not working on addresses
    # @Emon on 22/11/2022 - Extract Pattern Rule added
    # @Emon on 03/12/2022 - UpperCase, LowerCase, Calculate Rules Added
    # @Emon on 16/12/2022 - Second bonrn child with an already existing label wasn't going through rules, bug fixed. Bug still in consideration
    # @Emon on 30/01/2023 - Extract Pattern Fix, CW1 Date addition
    # @Emon on 04/02/2023 - Lookups used to hide account number - fix

    rules_version = "v5.1.150022023.01"
    global MASTER_DICTIONARIES

    try:
        definitions = request_data["definitions"]
    except:
        pass
    try:
        definition_settings = request_data.get("definition_settings")
    except:
        print(traceback.print_exc())
        pass

    try:
        master_dictionaries = request_data.get("master_dictionaries")
        MASTER_DICTIONARIES = master_dictionaries
    except:
        print(traceback.print_exc())
        pass
    try:
        all_compound_keys = definition_settings.get("compoundKeys")
        compounds = dict()
        for each_compound_key in all_compound_keys:
            compound_key_labels = list()
            compound_key_items = each_compound_key.get("keyItems")
            compound_key_name = each_compound_key.get("name")
            for each_compound_key_item in compound_key_items:
                compound_key_labels.append(each_compound_key_item.get("keyValue"))
            compounds[compound_key_name] = compound_key_labels

    except:
        print(traceback.print_exc())
        pass

    DEFINITIONS = definitions

    try:
        # Getting split defintions
        rules_definitions = definitions[0]["key"]["ruleItems"]
    except:
        # print(traceback.print_exc())
        return rules_version, d_json
    try:
        if not rules_definitions:
            return rules_version, d_json

        rules_applied_on = dict()
        rules_applied_on_address_child = dict()
        for rule_item in rules_definitions:
            if rule_item:
                if rule_item.get("id"):
                    rule_item["id"] = rule_item["id"].replace("pickUp", "pickup")
            if rule_item and rule_item.get("rules"):  # 112233
                key_id = rule_item.get("keyId")
                identifier = rule_item["id"]
                if "." in rule_item["id"]:
                    mother_node = rule_item["id"].split(".")[0]
                    if key_id:
                        mother_node = mother_node + "_" + key_id

                    child_key_name = rule_item["id"].split(".")[-1]
                    if not mother_node in rules_applied_on_address_child.keys():
                        rules_applied_on_address_child[mother_node] = [
                            {"childName": child_key_name, "data": rule_item["rules"]}
                        ]
                    else:
                        rules_applied_on_address_child[mother_node].append(
                            {"childName": child_key_name, "data": rule_item["rules"]}
                        )
                    if key_id:
                        for x in rules_applied_on_address_child[mother_node]:
                            x.update({"unique_id": key_id})
                else:
                    if key_id:
                        identifier = identifier + "_" + key_id

                    rules_applied_on[identifier] = {"data": rule_item["rules"]}

                    if key_id:
                        rules_applied_on[identifier].update(
                            {"unique_id": rule_item["keyId"]}
                        )

        docs = d_json["nodes"]

        for input_doc_idx, target_doc in enumerate(docs):
            nodes = target_doc["children"]
            for i, node in enumerate(nodes):
                node_children = node["children"]
                if "key" in node["type"]:
                    processed_labels = dict()

                    processed_key_nodes = list()

                    # Added on 31/08/2022
                    def central_function(node_children):
                        extra_key_nodes_holder = list()
                        processed_nodes = list()

                        for keyNode_idx, key_node in enumerate(node_children):
                            try:
                                if key_node.get("isCompoundKey") == True:
                                    compound_key_nodes = key_node["children"]
                                    processed_compound = list()
                                    for compound_idx, compound_key_node in enumerate(
                                        compound_key_nodes
                                    ):
                                        compound_key_node["motherCompund"] = key_node[
                                            "label"
                                        ]
                                        (
                                            compound_key_node,
                                            extra_key_nodes,
                                        ) = keyNode_level_rule(
                                            compound_key_node,
                                            rules_applied_on,
                                            rules_applied_on_address_child,
                                            address_keys,
                                            node_children,
                                        )
                                        if compound_key_node:
                                            processed_compound.append(compound_key_node)
                                        if extra_key_nodes:
                                            for extra_key_node in extra_key_nodes[:]:
                                                if (
                                                    extra_key_node.get("label")
                                                    in compounds[
                                                        compound_key_node[
                                                            "motherCompund"
                                                        ]
                                                    ]
                                                ):
                                                    extra_key_nodes.remove(
                                                        extra_key_node
                                                    )
                                                    for (
                                                        processed_compound_key_node
                                                    ) in processed_compound[:]:
                                                        if processed_compound_key_node.get(
                                                            "label"
                                                        ) == extra_key_node.get(
                                                            "label"
                                                        ):
                                                            processed_compound.remove(
                                                                processed_compound_key_node
                                                            )
                                                    processed_compound.append(
                                                        extra_key_node
                                                    )
                                            extra_key_nodes_holder += extra_key_nodes

                                        if compound_idx == 0:
                                            if key_node.get(
                                                "v"
                                            ) != compound_key_node.get("v"):
                                                key_node["v"] = compound_key_node.get(
                                                    "v"
                                                )
                                    key_node["children"] = processed_compound
                                else:
                                    key_node, extra_key_nodes = keyNode_level_rule(
                                        key_node,
                                        rules_applied_on,
                                        rules_applied_on_address_child,
                                        address_keys,
                                        node_children,
                                    )
                                if (
                                    key_node
                                ):  # If not disgarded by contains/startsWith/EndsWith
                                    processed_nodes.append(key_node)
                                if extra_key_nodes:
                                    extra_key_nodes_holder += extra_key_nodes
                            except:
                                processed_nodes.append(key_node)
                                print(traceback.print_exc())
                                pass

                        try:
                            for x in extra_key_nodes_holder:
                                if not x.get("splitAndDuplicated"):
                                    processed_nodes = [
                                        j
                                        for j in processed_nodes
                                        if j["label"] != x["label"]
                                    ]

                        except:
                            print(traceback.print_exc())
                            pass

                        return processed_nodes, extra_key_nodes_holder

                    # Processing First Time
                    processed_key_nodes, extra_key_nodes_holder = central_function(
                        node_children
                    )

                    try:
                        # Processing second time
                        (
                            second_level_nodes,
                            second_level_extra_nodes,
                        ) = deeper_level_central_function(
                            extra_key_nodes_holder,
                            rules_applied_on,
                            rules_applied_on_address_child,
                            address_keys,
                            processed_key_nodes,
                        )  # Placeholder for rule born nodes
                        if second_level_nodes:
                            processed_key_nodes += second_level_nodes
                    except:
                        print(traceback.print_exc())
                        pass
                    try:
                        # Processing third time
                        (
                            third_level_nodes,
                            third_level_extra_nodes,
                        ) = deeper_level_central_function(
                            second_level_extra_nodes,
                            rules_applied_on,
                            rules_applied_on_address_child,
                            address_keys,
                            processed_key_nodes,
                        )
                        if third_level_nodes:
                            processed_key_nodes += third_level_nodes
                    except:
                        print(traceback.print_exc())
                        pass
                    try:
                        (
                            fourth_level_nodes,
                            fourth_level_extra_nodes,
                        ) = deeper_level_central_function(
                            third_level_extra_nodes,
                            rules_applied_on,
                            rules_applied_on_address_child,
                            address_keys,
                            processed_key_nodes,
                        )
                        if fourth_level_nodes:
                            processed_key_nodes += fourth_level_nodes
                    except:
                        print(traceback.print_exc())
                        pass
                    try:
                        (
                            fifth_level_nodes,
                            fifth_level_extra_nodes,
                        ) = deeper_level_central_function(
                            fourth_level_extra_nodes,
                            rules_applied_on,
                            rules_applied_on_address_child,
                            address_keys,
                            processed_key_nodes,
                        )
                        if fifth_level_nodes:
                            processed_key_nodes += fifth_level_nodes
                    except:
                        print(traceback.print_exc())
                        pass
                    # Added on 13/12/2023 by Almas
                    # Compound value assignment
                    try:
                        for processed_key_node in processed_key_nodes:
                            if processed_key_node.get("isCompoundKey") == True:
                                compound_key_nodes = processed_key_node["children"]
                                compound_child_key = processed_key_node.get(
                                    "isCompoundChildLabel"
                                )
                                for (
                                    compound_key_node_idx,
                                    compound_key_node,
                                ) in enumerate(compound_key_nodes):
                                    if (
                                        compound_key_node.get("label")
                                        == compound_child_key
                                    ):
                                        processed_key_node["v"] = compound_key_node.get(
                                            "v"
                                        )
                                        break
                    except:
                        print(traceback.print_exc())
                        pass
                    node_children = processed_key_nodes  # Changed on 31/08/2022
                nodes[i]["children"] = node_children
            target_doc["children"] = nodes
            docs[input_doc_idx] = target_doc
        d_json["nodes"] = docs
        return rules_version, d_json

    except:
        print(traceback.print_exc())
        return rules_version, d_json
