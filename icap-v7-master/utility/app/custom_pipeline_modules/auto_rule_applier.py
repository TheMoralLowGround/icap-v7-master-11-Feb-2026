import traceback

from app.rules_normalizers_module.sub_rules import convert_date, convert_date_cw1

"""
This script is designed to automatically convert date values extracted from documents into a standardized format. It helps ensure that date information is consistent and properly formatted before further processing or integration into a system.

Here's a non-technical summary of what the script does:

1. It checks the extracted data for any fields or labels that contain the word "date," indicating that the value represents a date.
2. For each date field, it examines the settings to determine if the date format is European (day/month/year) or not.
3. If specific date rules are defined, such as adjusting the day, it applies those rules to the date value.
4. The script then processes the date value using a conversion function that takes into account the detected date format (European or not) and any applicable date rules.
5. The converted date value is updated in the extracted data, ensuring that it follows a standardized format.

The purpose of this script is to automatically normalize and standardize date information extracted from various documents, making it easier to process and integrate the data into other systems or applications. By consistently formatting date values, it helps prevent errors and inconsistencies that could arise from different date representations.

Here's a technical summary of the script:

The script is a Python module named `auto_apply_rule` that automatically applies date conversion rules to extracted date fields in the JSON data. It utilizes two sub-modules, `convert_date_cw1` and `convert_date`, for specific date conversion logic.

The main function `auto_apply_rule` takes two arguments: `d_json` (the existing JSON data) and `request_data` (a dictionary containing various definitions and settings).

The script first checks if the document being processed is a CW1 document by examining the `definitions` dictionary in `request_data`. It then retrieves the `ruleItems` from the `key` section of the first definition, which contains any date adjustment rules.

The script also attempts to identify a specific document to process based on the `document_id` in `request_data`.

The script then iterates through each node in the JSON data. For each node of type "key," it checks if the node's label contains the word "date." If so, it performs the following operations:

1. Retrieves the unique identifier (`unique_id`) of the key node.
2. Checks if there are any advance settings, such as a specific date format (European or not).
3. Iterates through the `ruleItems` to find any "adjustDay" rules associated with the unique identifier.
4. If the document is a CW1 document, it calls the `convert_date_cw1.process` function with the date value, European format flag, and any adjustment rules. Otherwise, it calls the `convert_date.process` function with just the date value.
5. Updates the converted date value in the key node.

The script also handles compound keys by iterating through their children and applying the same date conversion logic if a child node's label contains the word "date."

The script uses the `traceback` module to print any exceptions that occur during the date conversion process.

Finally, the script returns the updated `d_json` with the converted date values.

The purpose of this script is to automate the process of converting date values extracted from documents into a standardized format, considering any specific date formats or adjustment rules defined in the definitions or settings. This ensures that date information is consistently formatted for further processing or integration into other systems.

"""


def auto_apply_rule(d_json, request_data):
    # version 5.0.16102022
    # @Emon on 16/10/2022 - Initiated the script
    """
    This function primarily automatically applies date converter to date type fields
    """
    try:
        definitions = request_data["definitions"]
    except:
        pass
    if definitions == []:
        definitions = [{}]
    cw1 = definitions[0].get("cw1")
    try:
        rules_definitions = definitions[0]["key"]["ruleItems"]
    except:
        rules_definitions = list()
        pass

    try:
        table_definitions = definitions[0].get("table", [])
        table_rules_defintion = list()
        for table_definition in table_definitions:
            table_rule_items = table_definition.get("table_definition_data").get(
                "ruleItems"
            )
            if table_rule_items != []:
                table_rules_defintion.extend(table_rule_items)
    except:
        print(traceback.print_exc())
        pass
    # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = int(request_data["document_id"].split(".")[-1]) - 1
    except:
        pass

    docs = d_json["nodes"]

    for input_doc_idx, target_doc in enumerate(docs):
        # Figuring a way out here
        if test_document_trigger != None:
            if test_document_trigger != input_doc_idx:
                continue
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if "key" in node["type"]:
                node_children = node["children"]
                for key_node in node_children:
                    if ("date" in key_node["label"].lower()) or (
                        key_node.get("qualifierParent") == "milestone"
                    ):
                        try:
                            unique_id = key_node["unique_id"]
                            date_format = None
                            date_rule = None
                            advance_settings = key_node.get("advanceSettings")
                            is_european = False
                            if advance_settings:
                                date_format = advance_settings.get("dateFormat")

                            if date_format == "European":
                                is_european = True
                            for rule_definition in rules_definitions:
                                if rule_definition["keyId"] == unique_id:
                                    for rule in rule_definition["rules"]:
                                        if rule["type"] == "addDays":
                                            date_rule = rule["inputs"]["value"]
                                        elif rule["type"] == "deductDays":
                                            date_rule = rule["inputs"]["value"]
                                            if "-" in date_rule:
                                                date_rule = date_rule.replace("-", "")
                                            date_rule = "-" + date_rule

                            if cw1:
                                key_node["v"] = convert_date_cw1.process(
                                    key_node["v"], is_european, date_rule
                                )

                            else:
                                key_node["v"] = convert_date.process(key_node["v"])
                        except:
                            print(traceback.print_exc())
                            pass
                    elif key_node.get("isCompoundKey") == True:
                        compound_key_children = key_node["children"]
                        for compound_key_child in compound_key_children:
                            if (
                                "date" in compound_key_child["label"].lower()
                                or "milestone" in compound_key_child["label"].lower()
                            ):
                                try:
                                    unique_id = compound_key_child["unique_id"]
                                    date_format = None
                                    date_rule = None
                                    advance_settings = compound_key_child.get(
                                        "advanceSettings"
                                    )
                                    is_european = False
                                    if advance_settings:
                                        date_format = advance_settings.get("dateFormat")

                                    if date_format == "European":
                                        is_european = True
                                    for rule_definition in rules_definitions:
                                        if rule_definition["keyId"] == unique_id:
                                            for rule in rule_definition["rules"]:
                                                if rule["type"] == "addDays":
                                                    date_rule = rule["inputs"]["value"]
                                                elif rule["type"] == "deductDays":
                                                    date_rule = rule["inputs"]["value"]
                                                    if "-" in date_rule:
                                                        date_rule = date_rule.replace(
                                                            "-", ""
                                                        )
                                                    date_rule = "-" + date_rule

                                    if cw1:
                                        compound_key_child[
                                            "v"
                                        ] = convert_date_cw1.process(
                                            compound_key_child["v"],
                                            is_european,
                                            date_rule,
                                        )

                                    else:
                                        compound_key_child["v"] = convert_date.process(
                                            compound_key_child["v"]
                                        )
                                except:
                                    print(traceback.print_exc())
                                    pass

            elif node["type"] == "table":
                rows = node["children"]
                for row in rows:
                    cells = row["children"]
                    for cell in cells:
                        if "date" in cell["label"].lower():
                            try:
                                date_format = None
                                date_rule = None
                                advance_settings = cell.get("advanceSettings")
                                is_european = False
                                if advance_settings:
                                    date_format = advance_settings.get("dateFormat")

                                if date_format == "European":
                                    is_european = True
                                for rule_definition in table_rules_defintion:
                                    if rule_definition["label"] == cell["label"]:
                                        for rule in rule_definition["rules"]:
                                            if rule["type"] == "addDays":
                                                date_rule = rule["inputs"]["value"]
                                            elif rule["type"] == "deductDays":
                                                date_rule = rule["inputs"]["value"]
                                                if "-" in date_rule:
                                                    date_rule = date_rule.replace(
                                                        "-", ""
                                                    )
                                                date_rule = "-" + date_rule

                                if cw1:
                                    # print("before cw1", cell["v"])
                                    cell["v"] = convert_date_cw1.process(
                                        cell["v"], is_european, date_rule
                                    )
                                    cell["formated_date"] = True
                                    # print("after cw1", cell["v"])

                                else:
                                    # print("before", cell["v"])
                                    cell["v"] = convert_date.process(cell["v"])
                                    # print("after", cell["v"])
                            except:
                                print(traceback.print_exc())
                                pass

    return d_json
