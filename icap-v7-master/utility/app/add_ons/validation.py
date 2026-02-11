import traceback

from app.misc_modules.unique_id import assign_unique_id_helper

"""

This script is a background check on the extracted values against specific keys.
There are schematic validations of data types that need to be followed for proper integration.
Planned to be moved to a GUI based data validation rule set up.

This script is designed to validate extracted data from documents against a set of predefined rules and requirements. It ensures that the data adheres to specific data types, length restrictions, and other constraints before integrating it into a system.

Here's a non-technical summary of what the script does:

1. It checks the extracted data against a set of validation rules defined for different fields or labels.
2. For each field or label, it verifies if the data meets the required data type (e.g., numeric, string, boolean).
3. It validates the data against any specified length restrictions, such as minimum or maximum length.
4. If a list of valid codes or values is provided for a field, it ensures that the extracted data matches one of the codes in the list.
5. The script performs additional checks specific to address fields, dimensions, and units of measurement.
6. If any validation fails, it generates error messages describing the issue.

The script is designed to be a part of a larger system that extracts data from documents and ensures data quality and integrity before further processing or integration. It helps catch and prevent errors or inconsistencies in the extracted data, ultimately improving the overall reliability and accuracy of the system.

Here's a technical summary of the script:

The script is a Python module that performs data validation on extracted values against a set of pre-defined rules. It follows a schematic validation process to ensure that the data types and constraints are met for proper integration into a system. The main function is `validation_main`, which takes the request data, existing JSON data, and a list of messages as input.

The script fetches the validation rules from the `master_dictionaries` object, which contains the rules for different labels. It performs validations on key-value nodes, table cells, and address block partials based on the fetched rules. The validations include:

1. **Data type checks**: It verifies if the extracted value matches the expected data type (float, int, bool, string) defined in the rule.
2. **Length restrictions**: It checks if the value length falls within the specified minimum and maximum lengths.
3. **Code list checks**: If a list of valid codes is provided for a label, it ensures that the extracted value is present in that list.
4. **Dimension validations**: It checks if all required dimension labels (length, width, height, dimensionsUom) are present for the "dimensions" label.
5. **Unit of measurement checks**: It validates if a unit of measurement is provided for non-zero weight or volume values.

The script also handles specific cases for address blocks, address block partials, and qualifier fields, applying different validation rules accordingly.

If any validation fails, it appends an error message to the `messages` list, indicating the issue and the corresponding module.

The script returns the updated JSON data and the list of messages, which can be further processed or integrated into the system.

It also includes helper functions for checking numeric values, fetching sub-dictionaries, transforming labels, and checking if a label is a qualifier or an address block partial.

Overall, the script is designed to ensure data quality and consistency by enforcing predefined validation rules on the extracted data before integration.


"""


REQUIRED_DIMENSION_LABELS = ["length", "width", "height", "dimensionsUom"]

# creating a list of addressBlock keyValues to run the parser
ADDRESS_KEYS = list()


def fetch_validation_rule(input_label, validation_rules_by_label):
    fetch_rule = validation_rules_by_label.get("fetch_rule")
    rule = fetch_rule.get(input_label)
    return rule


def fetch_validation_rule_qualifiers(label, parent, validation_rules_by_label):
    fetch_qualifiers_rule = validation_rules_by_label.get("fetch_qualifiers_rule")
    rule = fetch_qualifiers_rule.get(parent)
    return rule


def fetch_addressChild_rule(label, validation_rules_by_label):
    fetch_addressChild_ruleset = validation_rules_by_label.get(
        "fetch_addressChild_rule"
    )
    rule = fetch_addressChild_ruleset.get(label)
    return rule


def multiple_decimals(some_string):
    """Check if multiple decimal indicators are present"""
    try:
        if some_string.count(",") > 1 and not "." in some_string:
            return True
        else:
            if some_string.count(".") > 1:
                return True
        return False
    except:
        return False


def is_numeric(some_string):
    """checks if a string is a float number convertible"""
    try:
        if multiple_decimals(some_string):
            return False

        if "," in some_string:
            some_string = some_string.replace(",", "")
        float(some_string)
        return True
    except ValueError:
        return False


def perfrom_check_data_type(value, data_type):
    if data_type == "float":
        return is_numeric(value)

    elif data_type == "int":
        # Handle cases where value is already an int
        if isinstance(value, int):
            return True
        # Handle cases where value is a float or string
        try:
            # If value is float-like, ensure it's a whole number
            if isinstance(value, float) and value.is_integer():
                return True
            # Convert string to int to check validity
            int(value)
            return True
        except (ValueError, TypeError):
            return False
    elif data_type == "bool":
        if value.upper() == "FALSE" or value.upper() == "TRUE":
            return True
        else:
            return False
    else:
        if data_type == type(value):
            return True


def fetch_code_list(master_dictionaries, code_list):
    """Fetch a sub dictionary from master dictionary list"""
    output = list()
    try:
        result_list = master_dictionaries.get(code_list).get("data").get("Result")
    except:
        result_list = list()

    for x in result_list:
        output.append(x.get("Code"))
    return output


def check_rule(rule, value, label, master_dictionaries, messages):
    """checks a rule for different sub-rules and performs validations based on that"""

    status = 0

    if rule:
        check_data_type = False
        data_type = rule.get("type")
        max_length = rule.get("maxLength")
        label_length = rule.get("typeMaxLength")
        min_length = rule.get("minLength")
        code_list = rule.get("codeList")
        decimal_max_length = rule.get("decimalMaxLength")

        status_assigned = False

        if label_length:
            if len(label) <= label_length:
                status = -1
            else:
                """LABEL LENGTH EXCEEDS VALIDATION SET RULE"""
                status = -2

                validation_text = label + " - label length exceeds set max length"
                full_message_dict = {
                    "message": validation_text,
                    "code": 400,
                    "module": "Validation",
                }

                if not full_message_dict in messages:
                    messages.append(full_message_dict)
            status_assigned = True

        if data_type == "number":
            data_type = "float"
            check_data_type = True

        if data_type == "boolean":
            data_type = "bool"
            check_data_type = True

        if data_type == "integer":
            data_type = "int"
            check_data_type = True

        if data_type == "string":
            data_type = "str"

        if check_data_type and not status_assigned:
            if perfrom_check_data_type(value, data_type):
                status = 1

            else:
                """VALUE DATA TYPE DID NOT MATCH"""
                status = -2

                validation_text = label + " value type did not match"
                full_message_dict = {
                    "message": validation_text,
                    "code": 400,
                    "module": "Validation",
                }

                if not full_message_dict in messages:
                    messages.append(full_message_dict)
            status_assigned = True

        if not status_assigned:
            if min_length:
                if len(value) >= min_length:
                    status = 1
                else:
                    """VALUE LENGTH DOES NOT MEET MINIMUM LENGTH"""
                    status = -2

                    validation_text = (
                        label + " value length is smaller than minimum required"
                    )
                    full_message_dict = {
                        "message": validation_text,
                        "code": 400,
                        "module": "Validation",
                    }

                    if not full_message_dict in messages:
                        messages.append(full_message_dict)
                status_assigned = True

            if max_length:
                if len(value) <= max_length:
                    status = 1
                else:
                    """VALUE LENGTH EXCEEDS MAXIMUM LENGTH"""
                    status = -2

                    validation_text = (
                        label + " value length exceeds maximum length allowed"
                    )
                    full_message_dict = {
                        "message": validation_text,
                        "code": 400,
                        "module": "Validation",
                    }
                    if not full_message_dict in messages:
                        messages.append(full_message_dict)
                status_assigned = True

        if code_list and not status_assigned:
            code_list_values = fetch_code_list(master_dictionaries, code_list)
            if code_list_values:
                if value in code_list_values:
                    status = 1
                else:
                    """VALUE IS NOT PRESENT IN GIVEN CODE LIST"""
                    status = -2

                    validation_text = label + " value is not present in set list"
                    full_message_dict = {
                        "message": validation_text,
                        "code": 400,
                        "module": "Validation",
                    }

                    if not full_message_dict in messages:
                        messages.append(full_message_dict)
            status_assigned = True
        if decimal_max_length is not None:
            # Decimal status check for volume
            value = value.replace(",", ".")
            splitted_value = value.split(".")
            if splitted_value:
                if (
                    len(splitted_value) > 1
                    and len(splitted_value[1]) > decimal_max_length
                ):
                    status = -2
                    validation_text = (
                        f"{label} has more than {decimal_max_length} decimal places."
                    )
                    full_message_dict = {
                        "message": validation_text,
                        "code": 400,
                        "module": "Validation",
                    }
                    if not full_message_dict in messages:
                        messages.append(full_message_dict)
    return status


def check_children_status(children):
    """creates a list of all the statuses of child elements and then returns a decision based on that"""
    status_list = list()
    for x in children:
        status_list.append(x.get("STATUS"))
    if -2 in status_list:
        return -2
    elif -1 in status_list:
        return -1
    elif 1 in status_list:
        return 1

    return None


def check_if_qualifier(input_label, key_qualifiers):
    """takes a label and checks if that label corresponds to a qualifers field and returns the category"""
    for setting in key_qualifiers:
        options = setting["options"]
        for option in options:
            if input_label == option["value"]:
                # print(label, '----', option["value"])
                target_key_node_name = setting["name"]
                return target_key_node_name

    return None


def transform_label(label):
    """
    Transforms a label. Usually gets rid of mother label name in address block partials. EG: consignee from consigneeAddressLine1 to addressLine1
    """

    for y in ADDRESS_KEYS:
        if label.lower().startswith(y.lower()):
            label = label.replace(y, "")
            return label[0].lower() + label[1:]
    return label


def check_if_addressBlockPartial(label, address_block_partial_list):
    if label in address_block_partial_list:
        return True
    return False


def perform_keyNode_validation(
    input_key_node,
    key_qualifiers,
    address_block_partial_list,
    master_dictionaries,
    messages,
):
    """perform key_node level validation and status assignment"""

    label = input_key_node["label"]
    is_qualifier = check_if_qualifier(label, key_qualifiers)
    is_addressBlockPartial = check_if_addressBlockPartial(
        label, address_block_partial_list
    )
    validation_rules_by_label = master_dictionaries.get(
        "validation_rules_by_label"
    ).get("data")

    if label and label.lower() in ADDRESS_KEYS:
        children = input_key_node["children"]

        for child in children:
            if child.get("notInUse"):
                continue
            childKeyName = child["label"]
            rule = fetch_addressChild_rule(childKeyName, validation_rules_by_label)
            value = child["v"]
            status = check_rule(rule, value, label, master_dictionaries, messages)
            if status:
                child["STATUS"] = status

        input_key_node["children"] = children
        motherNodeStatus = check_children_status(children)

        if motherNodeStatus:
            input_key_node["STATUS"] = motherNodeStatus

    elif is_qualifier:
        """If qualifer field seperate set of validation rules apply"""
        rule = fetch_validation_rule_qualifiers(
            label, is_qualifier, validation_rules_by_label
        )
        value = input_key_node["v"]
        if rule:
            status = check_rule(rule, value, label, master_dictionaries, messages)
            if status:
                input_key_node["STATUS"] = status

    elif is_addressBlockPartial:
        """then regular addressBlock children validation rules will be applied"""
        transformed_label = transform_label(label)
        rule = fetch_addressChild_rule(transformed_label, validation_rules_by_label)
        value = input_key_node["v"]
        status = check_rule(rule, value, label, master_dictionaries, messages)
        if status:
            input_key_node["STATUS"] = status

    else:
        rule = fetch_validation_rule(label, validation_rules_by_label)
        value = input_key_node["v"]
        if rule:
            status = check_rule(rule, value, label, master_dictionaries, messages)
            if status:
                input_key_node["STATUS"] = status

            return input_key_node, messages

    for child in input_key_node["children"]:
        if "is_profile_key_found" not in child.keys():
            child["is_profile_key_found"] = True
        if child.get("label").startswith("AWB"):
            child["STATUS"] = -111
        if input_key_node.get("STATUS") == -1000:
            child["STATUS"] = -1000

    return input_key_node, messages


def perform_cell_validation(
    cell, key_qualifiers, address_block_partial_list, master_dictionaries, messages
):
    """
    Performs cell validations of table node
    """
    label = cell["label"]
    is_qualifier = check_if_qualifier(label, key_qualifiers)
    is_addressBlockPartial = check_if_addressBlockPartial(
        label, address_block_partial_list
    )

    validation_rules_by_label = master_dictionaries.get(
        "validation_rules_by_label"
    ).get("data")

    if is_qualifier:
        """If qualifer field seperate set of validation rules apply"""
        rule = fetch_validation_rule_qualifiers(
            label, is_qualifier, validation_rules_by_label
        )
        value = cell["v"]
        if rule:
            status = check_rule(rule, value, label, master_dictionaries, messages)
            if status:
                cell["STATUS"] = status

    else:
        rule = fetch_validation_rule(label, validation_rules_by_label)
        value = cell["v"]
        if rule:
            status = check_rule(rule, value, label, master_dictionaries, messages)
            if status:
                cell["STATUS"] = status

            return cell, messages
    return cell, messages


def fetch_cell_indexes(cells, input_label):
    """
    Fetches index of cells in a table row node children array
    """
    cell_indexes_at = list()
    for cell_idx, cell in enumerate(cells):
        if cell["label"] == input_label:
            cell_indexes_at.append(cell_idx)
    return cell_indexes_at


def check_uom_command(cell, cells):
    """
    This checks if unit of measurements are present in the table row
    """
    try:
        label = cell.get("label")
        if "uom" in label.lower():
            mother_label = label[:-3]
        else:
            return True

        checks = ["weight", "volume"]

        if not any(x in mother_label.lower() for x in checks):
            return True

        value_present = None
        for x in cells:
            if x.get("label") == mother_label and x.get("v"):
                value_present = x.get("v")
        if value_present:
            if value_present != "0":
                return True
        return False
    except:
        # print(traceback.print_exc())
        return True


def fetch_labels(input_cells):
    output_list = list()
    for x in input_cells:
        output_list.append(x["label"])
    return output_list


def validation_main(request_data, d_json, messages):
    # Version 5.0.11122022 - Script Initiation
    try:
        definitions = request_data["definitions"]
        definition_id = definitions[0]["definition_id"]
    except:
        definition_id = None

    global ADDRESS_KEYS
    if definitions:
        use_cw1 = definitions[0].get("cw1")
        if not use_cw1:
            return d_json, messages

    definition_settings = request_data.get("definition_settings")
    key_qualifiers = definition_settings.get("keyQualifiers")
    key_options_items = (
        definition_settings.get("options", {}).get("options-keys", {}).get("items")
    )

    # lookupLables
    for item_settings_from_def in key_options_items:
        if item_settings_from_def["type"] == "addressBlock":
            ADDRESS_KEYS.append(item_settings_from_def["keyValue"].lower())

    master_dictionaries = request_data.get("master_dictionaries")

    """Creating lst of address block partials"""
    address_block_partial_list = list()
    for x in key_options_items:
        if x.get("type") == "addressBlockPartial":
            address_block_partial_list.append(x["keyValue"])
    docs = d_json["nodes"]
    two_targets = ["valueOfGoods", "insuranceValueCurrencyCode"]
    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if not node_children:
                continue
            if "key" in node["type"]:
                labels = list()
                for keyNode_idx, key_node in enumerate(node_children):
                    if not key_node.get("is_profile_key_found", False):
                        continue
                    
                    if (
                        definition_id
                        and (definition_id == "AU_SLI_SEA_ShipmentCreate")
                        and (key_node.get("label") in two_targets)
                    ):
                        key_node["STATUS"] = 1
                    else:
                        if not key_node.get("notInUse"):
                            label = key_node.get("label")
                            labels.append(key_node.get("label"))
                            if label.startswith("AWB"):
                                key_node["STATUS"] = -111
                            if not key_node.get(
                                "type"
                            ) == "key_detail_static" and not key_node.get(
                                "auto_lookup_unresolved"
                            ):
                                if not key_node.get("type") == "key_detail_robot":
                                    try:
                                        key_node, messages = perform_keyNode_validation(
                                            key_node,
                                            key_qualifiers,
                                            address_block_partial_list,
                                            master_dictionaries,
                                            messages,
                                        )
                                    except:
                                        # print(traceback.print_exc())
                                        pass
                # Second loop for adding a flag is_address_block_partial
                for kn in node_children:
                    if kn.get("children", []):
                        for key_child in kn.get("children", []):
                            key_child["is_address_block_partial"] = True
            elif "table" in node["type"]:
                for row_idx, row in enumerate(node_children):
                    cells = row["children"]
                    all_labels = fetch_labels(cells)
                    for cell_idx, cell in enumerate(cells):
                        if not cell.get("is_profile_key_found", False):
                            continue

                        if cell["label"] == "dimensions":
                            if not any(
                                x in all_labels for x in REQUIRED_DIMENSION_LABELS
                            ):
                                cell["STATUS"] = -2
                                validation_text = (
                                    "Dimension not parsed in doc {}".format(
                                        target_doc["id"][-2:]
                                    )
                                )

                                full_message_dict = {
                                    "message": validation_text,
                                    "code": 400,
                                    "module": "Validation",
                                }

                                messages.append(full_message_dict)
                        else:
                            try:
                                cell_indexes_at = fetch_cell_indexes(
                                    cells, cell["label"]
                                )
                                if cell_idx == cell_indexes_at[-1]:
                                    uom_check_pass = check_uom_command(cell, cells)
                                    if uom_check_pass:
                                        cell, messages = perform_cell_validation(
                                            cell,
                                            key_qualifiers,
                                            address_block_partial_list,
                                            master_dictionaries,
                                            messages,
                                        )
                            except:
                                print(traceback.print_exc())
                                pass

    # d_json = assign_unique_id_helper(d_json)
    return d_json, messages
