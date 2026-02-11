import re
import os
import requests
import traceback
from fuzzywuzzy import fuzz
from app.address_modules.address_custom import get_iso2
from app.key_central.keychildren_appender import SKIP_LABELS, TO_BE_KEPT_INSIDE

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")
MINIMUM_ADDRESS_LINE_MATCH_SCORE = 90
MINIMUM_COMPANYNAME_MATCH_SCORE = 90
MINIMUM_BLOCK_MATCH_SCORE = 80
AUTO_QUERY_LABELS = [
    "consignee",
    "shipper",
    "notify",
    "pickup",
    "delivery",
    "importer",
    "supplier",
]
CDZ_FIELDS = ["supplier", "importer"]



directives = {
    "single_row_found": {"directive": True, "color": "green"},
    "Nothing found with this company initials / Additional Data do not match": {
        "directive": True,
        "color": "red",
    },
    "Address Line Mismatch": {"directive": True, "color": "yellow"},
    "Company Name did not reach minimum required match score of 90%": {
        "directive": True,
        "color": "red",
    },
    "Company Name has multiple close matches": {
        "directive": True,
        "color": "yellow",
    },
}



def fetch_notfound_message_for_process(process_type):
    if not process_type:
        return "Functional Error"
    if process_type == "set1":
        return "Nothing found with this company initials / Additional Data do not match"

    return ""


def get_process_type(key_node, address_keys):
    """Get process type depending on the key_node Label"""
    if key_node["label"] in address_keys:
        return "set1"
    return "set2"


def check_if_close_matches(numbers, target):
    try:
        if len(numbers) > 1:
            if numbers.count(target) > 1:
                return True

        for number in numbers:
            if abs(number - target) <= 2 and number != target:
                return True
    except:
        pass

    return False


def get_child_value(key_node, child_node):
    """extract specific address child value from a keynode children list"""
    for child_dict in key_node["children"]:
        if child_dict["label"] == child_node:
            return child_dict["v"]
    return None


def get_name_cell(label, row):
    """Get name cell from table row"""
    for key, value in row.items():
        if (
            ("name" in key.lower())
            and (label.lower() in key.lower())
            and not ("cw1" in key.lower())
        ):
            return value
    return None


def check_db_adLines(row, label):
    if row.get(label + "addressline1"):
        return False
    return True


def check_addresslines(key_node, row, label):
    disregard = False
    if row.get(label + "addressline1"):
        ad1_kn = get_child_value(key_node, "addressLine1")
        if ad1_kn:
            if (
                fuzz.ratio(row[label + "addressline1"].lower(), ad1_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True

    if row.get(label + "addressline2"):
        ad2_kn = get_child_value(key_node, label + "addressline2")
        if ad2_kn:
            if (
                fuzz.ratio(row[label + "addressline2"].lower(), ad2_kn.lower())
                > MINIMUM_ADDRESS_LINE_MATCH_SCORE
            ):
                disregard = True
    return disregard


def clean_keyNode(input_json):
    """
    This function is triggered when a address that is queried in lookups might have full addresses entered in the records
    for proper refinement of the address( OCR errors and as such). The function matches the full address there and address keynode's block
    and then if matches over a certain threshold, replacing the keynode on the left of the screen and returns an index of the matched record

    """
    try:
        """This function takes in an input json and returns the updated keyNode and the matched row index"""

        key_node = input_json.get("keyNode")

        # PLEASE REFRAIN FROM USING IT
        use_cw1 = input_json.get("cw1")
        rows = input_json.get("rows")

        updated_key_node = None
        matched_index = None

        label = key_node["label"].upper()

        score_holder_dict = {}
        ratio_th = 80
        input_block = ""

        # If husky ratio is to be lower
        children = key_node["children"]
        for x in children:
            if x.get("label") == "block":
                input_block = x["v"]
                input_block = input_block.replace("\r", " ").replace("\n", " ")
                if "husky" in x["v"].lower():
                    ratio_th = 70

        if not input_block:
            input_block = key_node["v"]

        # DO THE WHOLE PROCESS AND UPDATE THE ABOVE VARS
        for i in range(len(rows)):
            try:
                full_address = rows[i].get(label + "_full_address")
                if not full_address:
                    continue
                match_score = fuzz.ratio(input_block.lower(), full_address.lower())
                if match_score >= ratio_th:
                    score_holder_dict[i] = match_score
            except:
                print(traceback.print_exc())
                continue

        if score_holder_dict:
            matched_index = max(score_holder_dict, key=score_holder_dict.get)
            i = matched_index
            updated_key_node = key_node
            updated_key_node["v"] = rows[i][label + "_full_address"]
            children = updated_key_node["children"]

            # print(children)
            for d_child in children:
                if d_child["label"] == "name" and rows[i].get(label + "_cw1_name"):
                    d_child["v"] = rows[i][label + "_cw1_name"]
                elif d_child["label"] == "name" and rows[i].get(label + "_name"):
                    d_child["v"] = rows[i][label + "_name"]
                if d_child["label"] == "addressLine1" and rows[i].get(
                    label + "addressline1"
                ):
                    d_child["v"] = rows[i][label + "addressline1"]
                if d_child["label"] == "addressLine2" and rows[i].get(
                    label + "addressline2"
                ):
                    d_child["v"] = rows[i][label + "addressline2"]
                if d_child["label"] == "city" and rows[i].get(label + "city"):
                    d_child["v"] = rows[i].get(label + "city")
                if d_child["label"] == "postcode" and rows[i].get(label + "postalcode"):
                    d_child["v"] = rows[i][label + "postalcode"]
                if d_child["label"] == "state" and rows[i].get(label + "state"):
                    d_child["v"] = rows[i][label + "state"]
                if d_child["label"] == "country" and rows[i].get(label + "country"):
                    d_child["v"] = rows[i][label + "country"]
                if d_child["label"] == "block" and rows[i].get(label + "_full_address"):
                    d_child["v"] = rows[i][label + "_full_address"]

        output_dict = dict()

        if updated_key_node and type(matched_index) == int:
            output_dict["keyNode"] = updated_key_node
            output_dict["matched_index"] = matched_index
            return output_dict
        return None
    except:
        print(traceback.print_exc())
        return None


def fetch_single_result_v7(
    global_lookup,
    key_node,
    address_keys,
    MESSAGES,
    doc_id,
    use_cw1,
    lookup_type,
    disable_country_code_check,
    master_dictionaries,
):
    country_Map = master_dictionaries.get("country_Map").get("data")
    """Fetch result from api and use fuzzyuzzy to return the one with the highest match"""
    decision_item = {"decision_message": fetch_notfound_message_for_process(None)}
    try:
        # print("global_lookup", global_lookup)
        request_body = global_lookup
        headers = {
            "Content-Type": "application/json",
        }
        lookup_url = f"{BACKEND_BASE_URL}/api/lookup/execute/"

        response = requests.post(
            lookup_url, headers=headers, json=request_body
        ).json()

        # print(response)

        all_query_result = response["all_results"]
        auto_query_message = None

        process_type = get_process_type(key_node, address_keys)
        decision_item = {
            "decision_message": fetch_notfound_message_for_process(process_type)
        }
        label = key_node["label"]

        if (
            process_type == "set1"
        ):  # Search by first company word in company name and then filter by fuzzy
            for single_query_result in all_query_result:
                key_nested_label = key_node["label"] + ".name"
                table_name = single_query_result.get("source_table")

                scores_list = list()
                rows = single_query_result.get("results")

                if not rows:
                    decision_item = {
                        "decision_message": fetch_notfound_message_for_process(
                            process_type
                        )
                    }
                    auto_query_message = {
                        "message": "No match found for {}".format(key_node["label"]),
                        "code": 400,
                        "module": "Lookups",
                    }

                    reason = "Nothing found with company initials"
                    # execute_write(key_node, batch_id, reason)
                    MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                return_dict = None
                try:
                    full_address_present = False
                    for row in rows:
                        if row.get(label + "_full_address"):
                            full_address_present = True
                    
                    print("full_address_present", full_address_present)

                    if full_address_present:
                        prepared_json = {
                            "rows": rows,
                            "keyNode": key_node,
                            "use_cw1": use_cw1,
                        }
                        return_dict = clean_keyNode(prepared_json)
                except:
                    print(traceback.print_exc())
                    pass

                if return_dict:
                    cleaned_keyNode = return_dict.get("keyNode")
                    row_idx = return_dict.get("matched_index")
                    final_row = rows[row_idx]
                    max_score = 95

                    decision_item = {
                        "key_nested_label": key_nested_label,
                        "motherLabel": key_node["label"],
                        "result_dict": final_row,
                        "key_unique_id": key_node["unique_id"],
                        "decision_message": "single_row_found",
                        "address_cleaned": cleaned_keyNode,
                    }

                    auto_query_message = {
                        "message": " LOOKUPS: {} auto query matched at {} pct".format(
                            decision_item["key_nested_label"], max_score
                        ),
                        "code": 200,
                        "module": "Lookups",
                    }

                    # MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                # Fetching company name and the relevant iso2
                company_name_original_case = get_child_value(key_node, "name")
                company_name = company_name_original_case.upper()

                country_iso_check = False
                if not disable_country_code_check:
                    company_country = get_child_value(key_node, "country")
                    company_country_iso = get_child_value(key_node, "countryCode")
                    country_iso_check = True

                    # Creating a placeholder if country or country code exists
                    if not company_country_iso:
                        if company_country:
                            try:
                                company_country_iso = get_iso2(
                                    company_country, country_Map
                                )
                            except:
                                pass

                        if not company_country_iso:
                            country_iso_check = False

                    if country_iso_check:
                        if company_country == company_country_iso:
                            country_iso_check = False

                # placeholder for rows considered by company name fuzzy match
                consideration_1 = list()
                consideration_1_fuzz_score = list()

                # Step 1 - By Company Name Match
                for row_idx, row in enumerate(rows):
                    account_number_first_two_digit_mismatch = False
                    name_cell = get_name_cell(label, row)
                    if not name_cell:
                        continue
                    try:
                        # Extra Spaces Removal
                        if "  " in name_cell.lower():
                            name_cell = name_cell.lower().replace("  ", " ")
                    except:
                        pass

                    # Checking the ratio of the match
                    fuzz_score = fuzz.ratio(name_cell.lower(), company_name.lower())

                    if fuzz_score >= MINIMUM_COMPANYNAME_MATCH_SCORE:
                        scores_list.append(fuzz_score)

                        if lookup_type == "Normal":
                            consideration_1.append(row)  # Storing the rows
                            consideration_1_fuzz_score.append(
                                fuzz_score
                            )  # Storing the indexes

                            continue

                        disregard = False

                        # If address lines are present address lines are checked
                        address_line_consideration_out = False
                        address_line_consideration_out = check_db_adLines(row, label)
                        address_line_match = check_addresslines(key_node, row, label)
                        if (
                            not address_line_match
                            and not address_line_consideration_out
                        ):
                            disregard = True

                        if not disregard:
                            account_number_holder = None
                            # Extracting account number and further checks
                            try:
                                account_number_holder = row.get(
                                    key_node["label"] + "accountnumber"
                                )
                            except:
                                pass
                            if country_iso_check and account_number_holder:
                                if account_number_holder[:2] != company_country_iso:
                                    account_number_first_two_digit_mismatch = True

                            if not account_number_first_two_digit_mismatch:
                                consideration_1.append(row)  # Storing the rows
                                consideration_1_fuzz_score.append(
                                    fuzz_score
                                )  # Storing the indexes

                # Placeholder for the final row
                final_row = None

                if not final_row and consideration_1:
                    """If step 2 didn't work best match from consideration_1 is to be chosen"""
                    max_score = max(consideration_1_fuzz_score)
                    if not check_if_close_matches(
                        consideration_1_fuzz_score, max_score
                    ):
                        target_index = consideration_1_fuzz_score.index(max_score)
                        final_row = consideration_1[target_index]
                    else:
                        decision_item = {
                            "decision_message": "Company Name has multiple close matches"
                        }
                        auto_query_message = {
                            "message": " {} Company Name has multiple close matches - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                if final_row:
                    decision_item = {
                        "key_nested_label": key_nested_label,
                        "motherLabel": key_node["label"],
                        "result_dict": final_row,
                        "key_unique_id": key_node["unique_id"],
                        "decision_message": "single_row_found",
                        "source_table": table_name,
                    }

                    auto_query_message = {
                        "message": " LOOKUPS: {} auto query matched at {} pct".format(
                            decision_item["key_nested_label"], max_score
                        ),
                        "code": 200,
                        "module": "Lookups",
                    }
                    # MESSAGES.append(auto_query_message)
                    return decision_item, MESSAGES

                else:
                    if not scores_list:
                        decision_item = {
                            "decision_message": "Company Name did not reach minimum required match score of 90%"
                        }
                        auto_query_message = {
                            "message": "{} Company Name did not reach minimum required match score of 90% - doc {}".format(
                                label, doc_id[-2:]
                            ),
                            "code": 400,
                            "module": "Lookups",
                        }
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES

                    else:
                        message = "{} Address Line/Account Number initials Mismatch - doc {}".format(
                            label, doc_id[-2:]
                        )
                        auto_query_message = {
                            "message": message,
                            "code": 400,
                            "module": "Lookups",
                        }

                        # execute_write(key_node, batch_id, reason)
                        decision_item = {"decision_message": "Address Line Mismatch"}
                        MESSAGES.append(auto_query_message)
                        return decision_item, MESSAGES
    except:
        print(traceback.print_exc())
        pass

    auto_query_message = {
        "message": "No match found for {}".format(key_node["label"]),
        "code": 400,
        "module": "Lookups",
    }
    MESSAGES.append(auto_query_message)
    reason = "General Error"
    # execute_write(key_node, batch_id, reason)
    return decision_item, MESSAGES


def get_table_name(label):
    """
    NAMESPACING CONVENTION OF THE TABLE NAME FORMAT
    FOR CDZ FIELDS: CDZ_{FIELDNAME}
    FOR SHIPMENT FIELDS: FIELDNAME_{MASTER}
    """
    if label.lower() in CDZ_FIELDS:
        return label.upper()
        # return "CDZ_" + label.upper()

    return label.upper() + "_MASTER"


def fetch_global_lookup_v7(key_node, process_name):
    """fetching global lookups by keynode label"""

    lookup_command_set = list()
    input_value = None
    label = key_node["label"]
    if label.lower() in AUTO_QUERY_LABELS:
        table_name = get_table_name(label)
        if "ebooking" in table_name.lower():
            return None
        column_to_search = label.upper() + "NAME"

        for x in key_node["children"]:
            if x["label"] == "name":
                try:
                    input_value = x["v"].strip().split()[0].upper()
                    if len(input_value) < 4:
                        # If the company's first word is only a single letter word two words are taken instead of only one
                        input_value = (" ").join(
                            x["v"].strip().split()[:1]
                        ).upper()
                except:
                    input_value = x["v"].strip()
                    if input_value[-1] == ",":
                        input_value = input_value[:-1]
                    pass

        if input_value:
            lookup_command_set.append({
                "table": table_name,
                "query": [
                    {
                        "queryData": [
                            {
                                "column": column_to_search,
                                "operator": "semantic_match",
                                "keyValue": input_value
                            },
                            {
                                "column": "process_name",
                                "operator": "=",
                                "keyValue": process_name
                            }
                        ]
                    }
                ]
            })

    return lookup_command_set


def create_key_node(extra):
    """Create a dummy keynode with a given label and value"""
    extra_keynode = dict()
    extra_keynode["children"] = []
    extra_keynode["v"] = extra["v"].upper()
    extra_keynode["pos"] = ""
    extra_keynode["id"] = extra["child_label"] + "addressManualBorn" + "01"
    extra_keynode["label"] = extra["child_label"]
    extra_keynode["pageId"] = ""
    extra_keynode["type"] = "key_detail"
    extra_keynode["origin"] = "lookup"

    extra_keynode["unique_id"] = (
        extra["motherNode_unique_id"]
        + "-"
        + extra["child_label"]
        + "-"
        + str(extra["extra_idx"])
    )
    extra_keynode["STATUS"] = 1
    if extra.get("qualifierParent"):
        disregard = False
        if (
            extra.get("qualifierParent") == "references"
            and len(extra["child_label"]) != 3
        ):
            disregard = True
        if not disregard:
            extra_keynode["qualifierParent"] = extra.get("qualifierParent")

    return extra_keynode


def get_key_value(key_nodes, key):
    value = ""
    for key_node in key_nodes:
        if key_node["label"] == key:
            value = key_node["v"]
            break

    return value


def execute_process_lookup(lookup_items, process_name, key_nodes, messages):
    result_storage = list()
    for lookup_item in lookup_items:
        process_query = {
            "column": "process_name",
            "operator": "=",
            "keyValue": process_name
        }
        lookup_queries = lookup_item["query"]
        for lookup_query in lookup_queries:
            query_data = lookup_query["queryData"]
            for query in query_data:
                if query["valueType"] == "key":
                    query["valueType"] = "input"
                    key = query["keyValue"]
                    query["keyValue"] = get_key_value(key_nodes, key)

            query_data.append(process_query)

        headers = {
            "Content-Type": "application/json",
        }
        lookup_url = f"{BACKEND_BASE_URL}/api/lookup/execute/"

        response = requests.post(
            lookup_url, headers=headers, json=query_data
        ).json()

        all_query_result = response["all_results"]

        if all_query_result:
            for single_query_data in all_query_result:
                table_name = single_query_data.get("source_table")
                decision, decision_item = get_process_decision(single_query_data)

                if decision == "pass":
                    decision_item["source_table"] = table_name
                    decision_item["decision_message"] = "single_row_found"
                    result_storage.append(decision_item)
                else:
                    process_query_error_message = {
                        "message": "Multiple/No rows found with process lookup query",
                        "code": 400,
                        "module": "Lookups",
                    }
                    messages.append(process_query_error_message)

    return result_storage


def get_process_decision(single_query_data):
    decision = "fail"
    decision_item = dict()

    single_query_data = single_query_data.get("results")
    if single_query_data:
        # If multi row
        if len(single_query_data) > 1:
            decision = "incomplete"

        # If single row result
        elif len(single_query_data) == 1:
            single_row = single_query_data[0]
            decision = "pass"
            result_dict = single_row

            if decision == "pass":
                decision_item = {
                    "result_dict": result_dict,
                }
    else:
        decision = "incomplete"

    return decision, decision_item


def get_key_node_type(label, address_keys):
    """Return the type of a kenode using the label"""
    if label in address_keys:
        return "address"
    else:
        return "others"


def get_table_skip_label(source_table, result_dict):
    """GENERATE A LIST OF LABELS THAT NEEDS TO BE SKIPPED FOR PARTICULAR TABLES"""
    TABLE_SPECIFIC_SKIP_LABELS = list()
    try:
        if "template" in source_table.lower():
            for child_label in result_dict.keys():
                if not "template" in child_label.lower():
                    if len(child_label) != 3 and (child_label.lower() != "tid"):
                        TABLE_SPECIFIC_SKIP_LABELS.append(child_label)
    except:
        # print(traceback.print_exc())
        pass
    return TABLE_SPECIFIC_SKIP_LABELS


def lookup_code_conversion(child_label, key_qualifiers):
    """Checks if column is of a lookup code type (References type) and converts and passes a flag"""
    check_tuples = ("PARTIES_", "NOTES_", "TIME_", "CUSTOMSENTRIES_", "SERVICE_")
    lookup_code_type = None
    if len(child_label) == 3:
        lookup_code_type = "references"
        child_label = child_label.upper()

    if child_label.startswith(check_tuples):
        lookup_code_type = child_label.split("_")[0]
        for setting in key_qualifiers:
            if setting["name"].lower() == lookup_code_type.lower():
                lookup_code_type = setting["name"]

        child_label = convert_lookup_code(
            child_label.split("_")[1], lookup_code_type, key_qualifiers
        )

    return lookup_code_type, child_label


def convert_lookup_code(child_label, settings_name, key_qualifiers):
    """Finds proper key for the qualifier from lookup codes in definition settings"""
    for setting in key_qualifiers:
        if setting["name"].lower() == settings_name.lower():
            options = setting["options"]
            for option in options:
                if child_label.lower() == option["value"].lower():
                    return option["value"]


def label_converter(s, label, key_val_arr, source_table):
    """convert labels to output json format"""
    # print("s", s)
    if s.lower() == "template_id":
        return "TID"

    if s.lower() == "consignee_account":
        s = "consigneeaccountnumber"

    if s.lower() == "shipper_account":
        s = "shipperaccountnumber"

    if s.lower() == "dest_code":
        s = "destinationlocationcode"

    if (s.lower() == "code") and ("ebooking_inco_terms" in source_table.lower()):
        s = "incoterms"

    if (s.lower() == "location_code") and (
        "ebooking_origin_location" in source_table.lower()
    ):
        s = "origincountrycode"

    if (s.lower() == "location_code") and (
        "ebooking_dest_location" in source_table.lower()
    ):
        s = "destinationcountrycode"

    if s.lower() == "parties_deliveryagent":
        s = "deliveryagent"

    if s.lower() == "dest_agent":
        s = "deliveryagent"

    transformed = ""

    if len(s) == 3:
        transformed = s.upper()

    # USING KEYVALUE LIST FROM DEFINITION SETTINGS
    for val in key_val_arr:
        if s.lower() == val.lower():
            transformed = val

    try:
        # Removing key_node label from the string
        if transformed.lower().startswith(label.lower()) and (
            transformed.lower() != label.lower()
        ):
            full_text = re.compile(label, re.IGNORECASE)
            full_text = full_text.sub("", transformed)
            transformed = full_text[0].lower() + full_text[1:]
    except:
        pass

    if transformed == "fullAddress":
        transformed = "block"

    if transformed.lower() == "templateid":
        transformed = "TID"

    if transformed.lower() == "accountnumber":
        transformed = "accountNumber"

    return transformed


def get_child_value(key_node, child_node):
    """extract specific address child value from a keynode children list"""
    for child_dict in key_node["children"]:
        if child_dict["label"] == child_node:
            return child_dict["v"]
    return None


def update_key_node_with_lookup_result(
    key_node, index, lookup_result, address_keys, key_val_arr, key_qualifiers
):
    """Based on different type of key_nodes the processes are different"""

    SHIFT_DATA_HOLDER = list()
    key_node_type = get_key_node_type(key_node["label"], address_keys)
    result_dict = lookup_result.get("result_dict")
    additional_key_nodes = lookup_result.get("additional_keys")

    unique_id = key_node.get("unique_id")
    color_decision = directives[(lookup_result.get("decision_message"))]["color"]
    # print("color_decision", color_decision)

    source_table = lookup_result.get("source_table")
    # print("source_table", source_table)

    TABLE_SPECIFIC_SKIP_LABELS = get_table_skip_label(source_table, result_dict)

    if color_decision == "yellow":
        key_node["STATUS"] = -1
        key_node["auto_lookup_unresolved"] = True

    elif color_decision == "red":
        key_node["STATUS"] = -1000
        key_node["auto_lookup_unresolved"] = True

    else:
        # print("key_node_type", key_node_type)
        if key_node_type == "address":
            address_cleaned = result_dict.get("address_cleaned")
            if address_cleaned:
                """IF THE ADDRESS IS CLEANED WE HAVE NO WORRIES"""
                key_node = address_cleaned

            """If it is an address we have to work out the child nodes differently"""
            previous_child_items = key_node["children"]
            additional_child_items = list()
            for child_label, child_value in result_dict.items():
                # Only if the value is present for child item
                if child_value and child_label:
                    if type(child_value) == str:
                        if not child_value.strip():
                            continue

                    if TABLE_SPECIFIC_SKIP_LABELS:
                        if child_label in TABLE_SPECIFIC_SKIP_LABELS:
                            continue

                    # Replacing Name child from cw1 name
                    if child_label.lower() == key_node["label"].lower() + "_cw1_name":
                        for previous_child in previous_child_items:
                            if previous_child["label"] == "name":
                                previous_child["v"] = child_value
                                continue

                    # References field check (Lookup codes. Different from lookups of this script)
                    lookupcode_type, child_label = lookup_code_conversion(
                        child_label, key_qualifiers
                    )
                    if additional_key_nodes:
                        for extra in additional_key_nodes:
                            if extra["target_column"].lower() == child_label.lower():
                                key_dict = {
                                    "child_label": extra["target_key"]["fieldInfo"][
                                        "keyValue"
                                    ],
                                    "v": child_value,
                                    "index": index,
                                    "motherNode_unique_id": unique_id,
                                }
                                (
                                    lookupcode,
                                    key_dict["child_label"],
                                ) = lookup_code_conversion(
                                    key_dict["child_label"], key_qualifiers
                                )
                                if lookupcode:
                                    key_dict["qualifierParent"] = lookupcode

                                SHIFT_DATA_HOLDER.append(key_dict)

                    if not lookupcode_type:
                        # print(key_node["label"], key_val_arr)
                        child_label = label_converter(
                            child_label, key_node["label"], key_val_arr, source_table
                        )
                    if not child_label:
                        continue

                    if child_label not in TO_BE_KEPT_INSIDE:
                        # print("TO_BE_KEPT_INSIDE", TO_BE_KEPT_INSIDE)
                        dict_data = {
                            "child_label": child_label,
                            "v": child_value,
                            "index": index,
                            "motherNode_unique_id": unique_id,
                        }
                        if lookupcode_type:
                            dict_data["qualifierParent"] = lookupcode_type

                        SHIFT_DATA_HOLDER.append(dict_data)

                    else:
                        # print("progressed_child_label", child_label)
                        if "name" in child_label.lower():
                            continue

                        if "account" in child_label.lower():
                            # print("key_node", key_node)
                            # print("accountNumber", get_child_value(key_node, "accountNumber"))
                            if not get_child_value(key_node, "accountNumber"):
                                # For template Id a new key text detail child has to be added
                                sample_dict = dict()
                                sample_dict["v"] = child_value
                                sample_dict["label"] = child_label
                                sample_dict["id"] = "random1234"
                                sample_dict["type"] = "keyTextDetail"
                                sample_dict["children"] = []
                                sample_dict["origin"] = "auto_lookup"
                                additional_child_items.append(sample_dict)

                        elif "shortcode" in child_label.lower():
                            if not get_child_value(key_node, "shortCode"):
                                if additional_child_items and child_label not in [i["label"] for i in additional_child_items]:
                                    # For template Id a new key text detail child has to be added
                                    sample_dict = dict()
                                    sample_dict["v"] = child_value
                                    sample_dict["label"] = child_label
                                    sample_dict["id"] = "random12345"
                                    sample_dict["type"] = "keyTextDetail"
                                    sample_dict["children"] = []
                                    sample_dict["origin"] = "auto_lookup"
                                    additional_child_items.append(sample_dict)

                        else:
                            if not address_cleaned:
                                # Matching existing children and replacing them
                                for previous_child in previous_child_items:
                                    if previous_child["label"] == child_label:
                                        previous_child["v"] = child_value
            # print("additional_child_items", additional_child_items)
            # Adding up the additional child items
            for x in additional_child_items:
                x["STATUS"] = 1

            if (
                additional_child_items
            ):  # Adding the additional non addrress child items to the keynode dictionary
                previous_child_items += additional_child_items

            key_node["children"] = previous_child_items
            key_node["STATUS"] = 1

        else:
            """FOR RULES APPLIED ON OTHER KEYNODES"""
            for child_label, child_value in result_dict.items():
                if not child_value.strip():
                    continue

                if TABLE_SPECIFIC_SKIP_LABELS:
                    if child_label in TABLE_SPECIFIC_SKIP_LABELS:
                        continue

                # References field check (Lookup codes. Different from lookups of this script)
                lookupcode_type, child_label = lookup_code_conversion(
                    child_label, key_qualifiers
                )
                if additional_key_nodes:
                    for extra in additional_key_nodes:
                        if extra["0"].lower() == child_label.lower():
                            key_dict = {
                                "child_label": label_converter(
                                    extra["1"],
                                    key_node["label"],
                                    key_val_arr,
                                    source_table,
                                ),
                                "v": child_value,
                                "index": index,
                                "motherNode_unique_id": unique_id,
                            }
                            (
                                lookupcode,
                                key_dict["child_label"],
                            ) = lookup_code_conversion(
                                key_dict["child_label"], key_qualifiers
                            )
                            if lookupcode:
                                key_dict["qualifierParent"] = lookupcode

                            SHIFT_DATA_HOLDER.append(key_dict)

                if not lookupcode_type:
                    child_label = label_converter(
                        child_label, key_node["label"], key_val_arr, source_table
                    )

                if child_label in SKIP_LABELS:
                    continue

                if child_label:
                    dict_data = {
                        "child_label": child_label,
                        "v": child_value,
                        "index": index,
                        "motherNode_unique_id": unique_id,
                    }
                    if lookupcode_type:
                        dict_data["qualifierParent"] = lookupcode_type

                    SHIFT_DATA_HOLDER.append(dict_data)

    return key_node, SHIFT_DATA_HOLDER


def lookup_central_main(request_data, d_json, messages, master_dictionaries):
    lookup_central_version = "v7.1.17102025"
    messages.append(
        {
            'message': f'Lookup Version {lookup_central_version}',
            'code': 200,
            'module': 'Lookups'
        }
    )

    MESSAGES = messages
    address_keys = list()
    kay_val_arr = list()

    try:
        definition_settings = request_data.get("definition_settings")
        key_options_items = (
            definition_settings.get("options", {}).get("options-keys", {}).get("items")
        )
    except:
        pass

    key_qualifiers = definition_settings.get("keyQualifiers")

    # lookupLables
    for item_settings_from_def in key_options_items:
        kay_val_arr.append(item_settings_from_def.get("keyValue"))
        if item_settings_from_def["type"] == "addressBlock":
            address_keys.append(item_settings_from_def["keyValue"])

    try:
        definitions = request_data["definitions"]
        if definitions != []:
            definitions = definitions[0]
        else:
            definitions = {}
    except:
        pass

    # Getting necessary flags
    use_cw1 = definitions.get("cw1")
    autoquery_disabled = False

    try:
        if definitions["key"]["models"][0].get("lookupDisableAutoQuery") == "true":
            autoquery_disabled = True
    except:
        pass

    # Placeholder for manually saved saved lookups
    lookup_items = list()
    try:
        lookup_items = definitions["key"]["lookupItems"]
    except:
        pass

    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass
    
    process_lookups = request_data.get("process_lookups", [])
    documents = d_json.get("nodes")
    batch_id = d_json.get("id")
    process_name = definitions.get("definition_id")

    if not autoquery_disabled:
        lookup_type = "Explicit"
        try:
            if definitions["key"]["models"][0].get("lookupType") == "Normal":
                lookup_type = "Normal"
        except:
            pass

        disable_country_code_check = False
        try:
            if (
                definitions["key"]["models"][0].get("lookupDisableCountryCodeCheck")
                == "true"
            ):
                disable_country_code_check = True
        except:
            pass

        # Automatic Lookup
        for input_doc_idx, target_doc in enumerate(documents):

            if test_document_trigger:
                if test_document_trigger != target_doc["id"]:
                    continue

            table_key_nodes = target_doc["children"]

            for node in table_key_nodes:
                node_type = node.get("type")
                if node_type != "key":
                    continue

                key_nodes = node["children"]
                extra_data_holder = list()

                for key_node_idx, key_node in enumerate(key_nodes):
                    label = key_node.get("label")

                    try:
                        global_lookup = fetch_global_lookup_v7(key_node, process_name)
                        if global_lookup:
                            """If global lookup exists - the execute it"""
                            lookup_result, MESSAGES = fetch_single_result_v7(
                                global_lookup,
                                key_node,
                                address_keys,
                                MESSAGES,
                                target_doc["id"],
                                use_cw1,
                                lookup_type,
                                disable_country_code_check,
                                master_dictionaries,
                            )
                            directive = None
                            try:
                                directive = directives[
                                    lookup_result.get("decision_message")
                                ].get("directive")
                            except:
                                pass
                            if directive:
                                """If a valid single row lookup result then update the keynode"""
                                (
                                    key_node,
                                    extra_data,
                                ) = update_key_node_with_lookup_result(
                                    key_node,
                                    key_node_idx,
                                    lookup_result,
                                    address_keys,
                                    kay_val_arr,
                                    key_qualifiers,
                                )
                                if extra_data:
                                    extra_data_holder += extra_data
                            else:
                                key_node["STATUS"] = -1000
                                key_node["auto_lookup_unresolved"] = True
                    except:
                        print(traceback.print_exc())

                if extra_data_holder:
                    """If address child produces non-address child data using lookups: shift them outside the keynode children and into the main list"""

                    for extra_idx, extra in enumerate(extra_data_holder):
                        keynode_label = extra.get("child_label")
                        # Removing previous nodes with the same label
                        for key in key_nodes:
                            if key.get("label") == keynode_label:
                                key_nodes.remove(key)

                        insert_index = extra["index"]
                        extra["extra_idx"] = extra_idx
                        key_nodes.insert(insert_index, create_key_node(extra))

                node["children"] = key_nodes

    if process_lookups:
        print("Process lookup start...")
        for input_doc_idx, target_doc in enumerate(documents):
            if test_document_trigger:
                if test_document_trigger != target_doc["id"]:
                    continue

            table_key_nodes = target_doc["children"]

            for node in table_key_nodes:
                node_type = node.get("type")
                if node_type != "key":
                    continue

                key_nodes = node["children"]
                extra_data_holder = list()

                result_storage = execute_process_lookup(
                    process_lookups, process_name, key_nodes, messages
                )
                if result_storage:
                    extra_data_holder = list()
                    for key_node_idx, key_node in enumerate(key_nodes):
                        try:
                            (
                                key_node,
                                extra_data,
                            ) = update_key_node_with_lookup_result(
                                key_node,
                                key_node_idx,
                                result_storage,
                                address_keys,
                                kay_val_arr,
                                key_qualifiers,
                            )

                            if extra_data:
                                extra_data_holder += extra_data
                        except:
                            print(traceback.print_exc())

                    if extra_data_holder:
                        """
                        If address child produces non-address child data using lookups: 
                        shift them outside the keynode children and into the main list
                        """
                        for extra_idx, extra in enumerate(extra_data_holder):
                            try:
                                keynode_label = extra.get("child_label")
                                # Removing previous nodes with the same label
                                for x in key_nodes:
                                    if x.get("label") == keynode_label:
                                        key_nodes.remove(x)
                                    insert_index = extra["index"]

                                extra["extra_idx"] = extra_idx
                                key_nodes.insert(insert_index, create_key_node(extra))
                            except:
                                print(traceback.print_exc())

                node["children"] = key_nodes

    # Change status of child for mother node status -1000
    for input_doc_idx, target_doc in enumerate(documents):
        nodes = target_doc["children"]

        for node in nodes:
            if "key" in node["type"]:
                key_nodes = node["children"]
                for key_node in key_nodes:
                    if key_node.get("STATUS") == -1000:
                        for child_key in key_node.get("children", []):
                            child_key["STATUS"] = -1000

    return d_json, MESSAGES

