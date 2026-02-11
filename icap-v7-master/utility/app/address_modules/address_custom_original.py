import json
import re
import traceback

import requests
from cleanco import basename, matches, typesources
from fuzzywuzzy import fuzz

# from .DGF_dictionary import address_dataset, focke_address_dataset
from ..common_dictionary import (
    missing_company_suffixes,
    remove_unwanted_values,
    replace_country_name,
)
from .address_alternator import address_alternator_process
from .address_parser import postal_parse_address

"""

Primary address parser script that takes a string address as input,
and performs a set of operations to get the company names and also uses libpostal library for other parts
of the address (Address lines, cities, country).
This also handles some exceptions by key models- that alters the logic of how a particular address is parsed.
"""


# version#5.02.24022023 @Fahim
# Git merge check - 28/12/2022 - AIDBEMON
# Emon on May 12 2023 - Removed unnecessary steps in parser


def get_iso2(input_countryName, country_Map):
    country_data = country_Map["Country"]
    for country_name, data in country_data.items():
        if country_name.lower() == input_countryName.lower():
            return data["ISO2"]
    return input_countryName


def get_digit_count(s):
    count = 0
    for c in s:
        if c.isdigit():
            count += 1
    return count


def special_exclusion_check(s):
    s = s.strip()
    # if get_digit_count(s) > 1:
    #     return False
    if len(s) < 3:
        return False
    return True


def reorganize_company_name(input_dict, company_stop_word):
    # CODE ADDED HERE BY ALMAS- 13/03/2023
    left_out = None
    for i in company_stop_word:
        if i.lower() in input_dict["name"].lower():
            name = input_dict["name"].split(i)
            name[0] = name[0] + " " + i
            input_dict["name"] = name[0]
            try:
                left_out = name[1]
            except:
                pass
    # print(left_out)
    length_count = 50
    if left_out != None:
        if "addressLine1" in input_dict.keys():
            input_dict["addressLine1"] = (
                left_out.strip() + " " + input_dict["addressLine1"]
            )
        else:
            input_dict["addressLine1"] = left_out.strip()
        if len(input_dict["addressLine1"]) > length_count:
            left_out = input_dict["addressLine1"][length_count - 1 :]
            input_dict["addressLine1"] = input_dict["addressLine1"][:50]
            if "addressLine2" in input_dict.keys():
                input_dict["addressLine2"] = (
                    left_out.strip() + " " + input_dict["addressLine2"]
                )
            else:
                input_dict["addressLine2"] = left_out.strip()
    return input_dict


def fetch_company_stopwords(definitions):
    """
    Fetches company stopwords from key models
    """

    output_list = list()
    try:
        key_definitions = definitions[0]["key"]
        key_model = key_definitions["models"][0]
        if key_model:
            output_list = key_model.get("companyNameStopWords")

        return output_list

    except:
        pass


def fetch_company_line_index(definitions):
    try:
        key_definitions = definitions[0]["key"]
        key_model = key_definitions["models"][0]
        if key_model:
            index_ = key_model.get("companyNameOnLine")

        return index_
    except:
        pass


def digit_count(s):
    count = 0
    for c in s:
        if c.isdigit():
            count += 1
    return count


def exclusion_check(line):
    """in yokogawa company name starting with CO is detected as the company_name. To fix this"""

    line = line.strip()

    return False


SUFFIX_TRIGGERS = list()


def check_suffix(input_text, master_dictionaries):
    global MASTER_DICTIONARIES

    words = input_text.lower().split()

    if len(words) > 1:
        company_suffix_data = master_dictionaries.get("companySuffixes").get("data")

        if company_suffix_data:
            triggers = company_suffix_data.get("list")
            if any(trigger.lower() in words for trigger in triggers):
                return True

    return False


def custom_address_parser(address_text, definitions, master_dictionaries):
    # global MASTER_DICTIONARIES

    company_stop_words = fetch_company_stopwords(definitions)
    company_line_index = fetch_company_line_index(definitions)

    # MASTER_DICTIONARIES = master_dictionaries
    # master_dictionaries = request_data.get("master_dictionaries")
    country_map = master_dictionaries.get("country_Map").get("data")
    replace_undetected_values = master_dictionaries.get(
        "replace_undetected_values"
    ).get("data")
    replace_company_name = master_dictionaries.get("replace_company_name").get("data")
    replace_city_name = master_dictionaries.get("replace_city_name").get("data")
    # print("address text:", address_text)
    final_dict = dict()

    # regex to find out keyvalue pairs
    regex_to_detect_key_value_pair = re.compile(
        r"\b(\w+)\s*:\s*([^:]*)(?=\s+\w+\s*:|$)"
    )
    key_value_pairs = dict(regex_to_detect_key_value_pair.findall(address_text))
    for extra_key, extra_value in key_value_pairs.items():
        extra_value = extra_value.split("\n")[0]
        key_value_pairs[extra_key] = extra_value

    # target key value paris
    to_be_extracted = [
        "Mail",
        "ATTN",
        "Person",
        "Fax",
        "Tel",
        "Contact",
        "PHONE",
        "Receiver",
    ]

    key_val_dict = dict()
    """Finding key value pairs initially and filtering them using target keys
    And then removing them from the address text"""
    for target_key, target_value in key_value_pairs.items():
        for trigger in to_be_extracted:
            if trigger.lower() in target_key.lower():
                address_text = address_text.replace(target_key, "")
                address_text = address_text.replace(target_value, "").strip()
                if trigger == "Mail":
                    key_val_dict["contactEmail"] = target_value
                elif trigger == "Tel" or trigger == "PHONE":
                    key_val_dict["contactPhone"] = target_value
                else:
                    key_val_dict[target_key.title()] = target_value
    # print("14. checking key value dict:", key_val_dict)

    for trigger in to_be_extracted:
        if trigger.lower() in address_text.lower():
            if (
                trigger.lower() == "contact"
                and address_text.lower().index("contact") < 10
            ):  # To keep 'Contact' of Company names as it is (e.g. 'Phoenix Contact S.A.S.) @Fahim (5/01/2023)
                pass
            else:
                address_text = address_text.replace(trigger, "")

    address_text = address_text.replace(":", "")  # replacing colon if any

    if replace_undetected_values:
        for val in replace_undetected_values:
            if val["original_value"] in address_text:
                # print(type(val['original_value']))
                # print(address_text)
                address_text = address_text.replace(
                    val["original_value"], val["translated_value"]
                )

    address_text_list = address_text.split("\n")
    # print("18. checking address text input list:", address_text_list)
    # removing the first line from address block if it contains number more than 3 digits @Fahim (24 Feb 2023)
    if len(address_text_list) > 1:
        first_line = address_text_list[0]
        first_line_list = first_line.split(" ")
        last_word_number = False
        has_number = False
        first_line_numerics = 0
        second_line_numerics = 0
        for i in first_line_list:
            if "-" in i:
                i = i.replace("-", "")
            for char in i:
                if char.isnumeric():
                    first_line_numerics += 1
            if len(i) > 3:
                percent_i = (first_line_numerics / len(first_line)) * 100
                if percent_i > 20:
                    second_line = address_text_list[1]
                    second_line_list = second_line.split(" ")
                    for j in second_line:
                        if j.isnumeric():
                            second_line_numerics += 1
                    percent_j = (second_line_numerics / len(second_line)) * 100
                    if percent_j > 20:
                        has_number = False
                    else:
                        has_number = True
            if i.isnumeric():
                if i == first_line_list[-1]:
                    last_word_number = True
        # last word number added to remove if there is numeric value after the company name
        if last_word_number:
            address_text_list[0] = " ".join(first_line_list[:-1])
        if has_number:
            address_text_list.pop(0)
    # print("19. checking address text input list:", address_text_list)
    count = 0
    for i in range(len(address_text_list)):
        item = address_text_list[count]
        for unwanted_value in remove_unwanted_values:
            if item.find(unwanted_value) != -1:
                address_text_list.remove(item)
                count -= 1
        count += 1
    address_text = "\n".join(address_text_list)

    block = address_text

    # print("---KeyValue Detection---")
    # print(key_value_pairs)
    # print("----")

    processed_block = "\n".join(item for item in block.split("\n") if item)
    address_line_list = processed_block.split("\n")
    # print("20. checking processed address line list:", address_line_list)

    address_line_count = len(address_line_list)
    if address_line_count == 1:
        address_line_list = block.split(",")
    # print(address_line_list[0])
    if address_line_list[0] == "Firma":
        address_line_list = address_line_list[1:]
    # checking if the first line only consists of digits
    if address_line_list[0].isdigit():
        address_line_list.append(address_line_list.pop(0))

    # lines to be removed
    tbr = []

    if (
        len(address_line_list) > 2
        and address_line_list[1].startswith("(")
        and address_line_list[1].endswith(")")
    ):
        address_line_list[0] = address_line_list[0] + " " + address_line_list[1]
        del address_line_list[1]

    if address_line_list[0] == "Company":
        address_line_list = address_line_list[1:]

    name = address_line_list[0].lower()
    if name.endswith("and"):
        address_line_list[0] = address_line_list[0] + " " + address_line_list[1]
        del address_line_list[1]

    company_name = None
    classification_sources = typesources()
    stop_word_set_1 = "s.a."

    for i, line in enumerate(address_line_list):
        match = matches(line, classification_sources)
        if not match:
            if check_suffix(line, master_dictionaries):
                match = True
        if match:
            # print(f"Matches {line}")
            try:
                if exclusion_check(line):
                    # print("Company Name", "------", line)
                    try:
                        if i == 1:
                            # handling the company name (Co or Ltd) in second line (merging with company_name)
                            if (
                                "co." in address_line_list[1].lower()
                                or "ltd" in address_line_list[1].lower()
                            ):
                                company_name = (
                                    address_line_list[0] + address_line_list[1]
                                )
                                address_line_list = address_line_list[2:]
                                break
                    except:
                        pass

                    company_name = line
                    address_line_list.pop(i)
                    break
                else:
                    pass
            except:
                print(traceback.print_exc())
                pass

    # company_name checks
    if company_name:
        address_text = address_text.replace(company_name, "")
        final_dict["name"] = company_name
    else:
        # print(company_name)
        if company_line_index:
            index_ = int(company_line_index) - 1
            company_name = address_line_list[index_]
            final_dict["name"] = company_name
            address_text = address_text.replace(company_name, "")
        else:
            """if no companyNames are found first check for missing company suffixes"""
            for line in address_line_list:
                if any(suffix in line.lower() for suffix in missing_company_suffixes):
                    if not line.lower().startswith("limited"):
                        company_name = line
                        final_dict["name"] = company_name
                        tbr.append(line)
            if not company_name:
                if special_exclusion_check(address_line_list[0]):
                    """if still not found just assume the first line is the company name"""
                    company_name = address_line_list[0]
                    address_line_list = address_line_list[1:]
                    final_dict["name"] = company_name
                else:
                    company_name = address_line_list[0]
                    address_line_list = address_line_list[1:]
                    final_dict["name"] = company_name

        # If only one line input is sent the list is empty. So, it returns the input line as name anyway
        # Added by Emon on 12/08/2022
        if not address_line_list:
            return {"name": address_text, "block": block}

    # print("2. checking company_name:", company_name)
    # print("3. checking address line list:", address_line_list)
    # print("4. checking final dict:", final_dict)

    parser_dict = dict()

    # running the address parsers
    result = postal_parse_address(address_text)

    # Fix for the word |port| identified as a city
    try:
        for x, y in result:
            if y == "city" and (x.lower() == "port"):
                address_text = address_text.lower().replace("port", "")
                result = postal_parse_address(address_text)
    except:
        pass

    for data in result:
        parser_dict[data[1]] = data[0]
    # print("1. checking parser dict:", parser_dict)

    if "city" in parser_dict.keys() and (parser_dict["city"].strip().lower() == "port"):
        parser_dict.pop("city", None)

    if "postcode" in parser_dict.keys() and (parser_dict["postcode"].isalpha()):
        parser_dict.pop("postcode", None)

    required_address_fields = ["city", "block", "country", "postcode", "state"]

    # print("7. checking parser dict before setting in final dict:", parser_dict)
    for key, value in parser_dict.items():
        if key in required_address_fields:
            final_dict[key] = value
    # print("8. checking final dict after setting values:", final_dict)

    # exluding postal code if it is alphaNumeric (e.g. Box19879)
    if (
        "postcode" in final_dict.keys() and final_dict["postcode"].isnumeric() == False
    ):  # Please make sure the key is there in the first place @Emon28/07/22
        final_dict.pop("postcode")

    city_holder = None
    if "city" in final_dict.keys():
        city_holder = final_dict["city"]

    if city_holder:
        for line_idx, line in enumerate(address_line_list):
            if city_holder in line.lower():

                def get_only_digits(s):
                    t = ""
                    for i, c in enumerate(s):
                        if c.isspace() or c.isdigit():
                            t += c
                        elif c == "-":
                            if s[i - 1].isdigit() and s[i + 1].isdigit():
                                t += c
                    # print(s, ' converted to ', t)
                    return t

                text_with_digits = get_only_digits(line).strip()
                digit_list = text_with_digits.split(" ")
                suggested_postcode = max(digit_list)

                if len(suggested_postcode) > 2:
                    final_dict["postcode"] = suggested_postcode

                if "-" in text_with_digits:
                    # print(text_with_digits)
                    final_dict["postcode"] = text_with_digits

    primary_final_values = list(final_dict.values())
    # print("5. checking primary final values:", primary_final_values)
    # print("6. checking final dict:", final_dict)
    # special operation for values with more than one word
    final_values = list()
    for elem in primary_final_values:
        words_in_elem = elem.strip().split()
        if len(words_in_elem) > 1:
            for word in words_in_elem:
                final_values.append(word)
        else:
            final_values.append(elem)

    # removing detected lines form the address line list
    for line_idx, line in enumerate(address_line_list):
        line_to_be_checked = line.strip().lower()
        words = line_to_be_checked.split()
        match_count = 0
        for word in words:
            if word in final_values:
                match_count += 1
        if len(words) <= match_count:
            tbr.append(line)
        elif len(words) == 1:
            if any(value.lower() == line_to_be_checked for value in final_values):
                tbr.append(line)

    address_line_list = [x for x in address_line_list if x not in tbr]
    # print("9. checking address line list:", address_line_list)

    address_line1 = None
    rest_address_lines = list()

    for i, line in enumerate(address_line_list):
        if "".join(char for char in line if char.isalnum()) != "":
            if i == 0:
                address_line1 = line
            else:
                rest_address_lines.append(line)
    if address_line1 and rest_address_lines:
        final_dict["addressLine1"] = address_line1
        final_dict["addressLine2"] = " ".join(rest_address_lines)
    elif address_line1:
        final_dict["addressLine1"] = address_line1

    # print("10. checking address line 1:", final_dict["addressLine1"])
    # print("11. checking address line 2:", final_dict["addressLine2"])
    # breakpoint 1
    # print("12. checking final dict:", final_dict)

    final_dict = address_alternator_process(
        final_dict,
        address_text,
        parser_dict,
        key_val_dict,
        replace_company_name,
        replace_city_name,
    )

    # breakpoint 3
    # print("16. checking output dict:", final_dict)

    # replacing country (changed output dict to final_dict @Fahim-19/10/2022)
    if "country" in final_dict.keys():
        country_name = final_dict["country"]
        for value in replace_country_name:
            if value["original_value"].lower() in country_name.lower():
                final_dict["country"] = value["translate_value"]

    if "country" in final_dict.keys():
        country_name = final_dict["country"]

        if get_iso2(country_name, country_map) != country_name:
            final_dict["countryCode"] = final_dict.pop("country")
            final_dict["countryCode"] = get_iso2(country_name, country_map)

    for key, value in final_dict.items():
        final_dict[key] = value.strip()
        words = value.split()
        if len(words) == 1:
            """if a word inside a line is less than 4 chars in length make it Upper
            Eg. usa to USA. Else use title function"""
            if len("".join(char for char in value if char.isalnum())) < 4:
                final_dict[key] = value.upper()
            else:
                final_dict[key] = value.title()
        else:
            for word_idx, word in enumerate(words):
                if len("".join(char for char in word if char.isalnum())) < 4:
                    word = word.upper()
                else:
                    word = word.capitalize()
                words[word_idx] = word

            value = (" ").join(words)
            final_dict[key] = value
    # making consigneeAccountNumber uppercase @Fahim(24/10/2022)
    if "consigneeAccountNumber" in final_dict:
        final_dict["consigneeAccountNumber"] = final_dict[
            "consigneeAccountNumber"
        ].upper()

    # adding block to the final dictionary

    # renaming keys according to Fields file
    final_dict_keys = final_dict.keys()
    if "state" in final_dict_keys:
        final_dict["stateProvince"] = final_dict.pop("state")
    if "postcode" in final_dict_keys:
        final_dict["postalCode"] = final_dict.pop("postcode")
    if "consigneeAccountNumber" in final_dict.keys():  # added by Fahim@7.11.2022
        final_dict["accountNumber"] = final_dict.pop("consigneeAccountNumber")

    # converting names to uppercase @Fahim(3/11/2022)
    if "name" in final_dict.keys():
        final_dict["name"] = final_dict["name"].upper()

    # this is the sorting order of the keys
    sort_idx_list = [
        "name",
        "addressLine1",
        "addressLine2",
        "city",
        "stateProvince",
        "postalCode",
        "country",
        "countryCode",
        "contactPhone",
        "contactEmail",
        "Attn",
        "accountNumber",
        "destinationCountryCode",
        "destinationLocationCode",
        "originLocationCode",
        "incoterms",
        "pickUpAgent",
        "deliveryAgent",
        "customerAccountNumber",
    ]

    def address_parser_sorter(input_dict, sort_idx_list_input):
        index_map = {v: i for i, v in enumerate(sort_idx_list_input)}
        sorted_dict_output = sorted(
            input_dict.items(), key=lambda pair: index_map[pair[0]]
        )
        return sorted_dict_output

    try:
        sorted_dict = address_parser_sorter(final_dict, sort_idx_list)
    except KeyError as e:
        """if a key is not found in the sorting index list"""
        keyName_notfound = e.args[0]
        if "address" in keyName_notfound:
            place_at = sort_idx_list.index("city")
            sort_idx_list.insert(place_at, keyName_notfound)
        else:
            sort_idx_list.append(e.args[0])
        sorted_dict = address_parser_sorter(final_dict, sort_idx_list)

    for extra_key, extra_value in key_val_dict.items():
        sorted_dict.append((extra_key, extra_value))

    sorted_dict.append(("block", block.strip()))

    output_dict = dict()
    for a, b in sorted_dict:
        output_dict[a] = b
    # print(output_dict)

    # removing emply fields from output_dict @Fahim-19/10/2022
    # removing empty contact
    if "Contact" in output_dict.keys():
        if len(output_dict["Contact"]) == 0:
            output_dict.pop("Contact")

    if "addressLine2" in output_dict.keys():
        # print(output_dict)
        city = output_dict.get("city", "")
        postalCode = output_dict.get("postalCode", "")
        country = output_dict.get("country", "")

        address_line2 = output_dict["addressLine2"].replace(" ,", ",")
        address_line2_list = address_line2.split(" ")

        new_addressLine2_list = []
        for item in address_line2_list:
            if item.replace(",", "") not in [city, postalCode, country]:
                new_addressLine2_list.append(item)
        # print(new_addressLine2_list)
        address_line2_list = new_addressLine2_list
        output_dict["addressLine2"] = " ".join(address_line2_list)
        # print(output_dict)

    if company_stop_words:
        try:
            output_dict = reorganize_company_name(output_dict, company_stop_words)
        except:
            pass

    if output_dict.get("name")[-1] == ",":
        output_dict["name"] = output_dict["name"][:-1]

    if output_dict.get("Contact"):
        output_dict["contactName"] = output_dict.pop("Contact", None)
    return output_dict
