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
from .builder.final_dict_builder import FinalDictBuilder
from .builder.output_dict_builder import OutputDictBuilder

"""

Primary address parser script that takes a string address as input,
and performs a set of operations to get the company names and also uses libpostal library for other parts
of the address (Address lines, cities, country).
This also handles some exceptions by key models- that alters the logic of how a particular address is parsed.
"""


# version#5.02.24022023 @Fahim
# Git merge check - 28/12/2022 - AIDBEMON
# Emon on May 12 2023 - Removed unnecessary steps in parser


def get_iso2(input_country_name, country_Map):
    # TODO: make a dictionary call
    country_data = country_Map["Country"]
    for countryName, data in country_data.items():
        if countryName.lower() == input_country_name.lower():
            return data["ISO2"]
    return input_country_name


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
    words = input_text.lower().split()

    if len(words) > 1:
        company_suffix_data = master_dictionaries.get("companySuffixes").get("data")

        if company_suffix_data:
            triggers = company_suffix_data.get("list")
            if any(trigger.lower() in words for trigger in triggers):
                return True
    return False


def create_key_val_dict(
    key_value_pairs: dict, to_be_extracted: list, address_text: str
) -> dict:
    key_val_dict = {}
    for extra_key, extra_value in key_value_pairs.items():
        extra_value = extra_value.split("\n")[0]
        key_value_pairs[extra_key] = extra_value

        target_key = key_value_pairs[extra_key]
        target_value = extra_value

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
    return key_val_dict


def replace_undetected_values_in_address(master_dictionaries: list, address_text: str):
    replace_undetected_values = master_dictionaries.get(
        "replace_undetected_values"
    ).get("data")
    if replace_undetected_values:
        for val in replace_undetected_values:
            if val["original_value"] in address_text:
                address_text = address_text.replace(
                    val["original_value"], val["translated_value"]
                )
    return address_text


def remove_unwanted_values_in_address(address_text_list: list) -> str:
    count = 0
    for i in range(len(address_text_list)):
        item = address_text_list[count]
        for unwanted_value in remove_unwanted_values:
            if item.find(unwanted_value) != -1:
                address_text_list.remove(item)
                count -= 1
        count += 1
    return "\n".join(address_text_list)


def check_and_process_address_text_first_line(address_text_list: list) -> list:
    if len(address_text_list) > 1:
        first_line = address_text_list[0]
        first_word_list = first_line.split(" ")
        last_word_number = False
        has_number = False
        first_line_numerics = 0
        second_line_numerics = 0

        for word in first_word_list:
            if "-" in word:
                word = word.replace("-", "")

            for char in word:
                if char.isnumeric():
                    first_line_numerics += 1

            if len(word) > 3:
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
            if word.isnumeric() and word == first_word_list[-1]:
                last_word_number = True

        # last word number added to remove if there is numeric value after the company name
        if last_word_number:
            address_text_list[0] = " ".join(first_word_list[:-1])
        if has_number:
            address_text_list.pop(0)
    return address_text_list


def parse_data_from_address(address_text: str) -> dict:
    parser_dict = {}

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

    if "city" in parser_dict.keys() and (parser_dict["city"].strip().lower() == "port"):
        parser_dict.pop("city", None)

    if "postcode" in parser_dict.keys() and (parser_dict["postcode"].isalpha()):
        parser_dict.pop("postcode", None)

    return parser_dict


def custom_address_parser(address_text, definitions, master_dictionaries, project=None):
    company_stop_words = fetch_company_stopwords(definitions)
    company_line_index = fetch_company_line_index(definitions)

    country_map = master_dictionaries.get("country_Map").get("data")
    replace_company_name = master_dictionaries.get("replace_company_name").get("data")
    replace_city_name = master_dictionaries.get("replace_city_name").get("data")

    # regex to find out keyvalue pairs
    regex_to_detect_key_value_pair = re.compile(
        r"\b(\w+)\s*:\s*([^:]*)(?=\s+\w+\s*:|$)"
    )
    key_value_pairs = dict(regex_to_detect_key_value_pair.findall(address_text))

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

    key_val_dict = create_key_val_dict(key_value_pairs, to_be_extracted, address_text)

    for trigger in to_be_extracted:
        if trigger.lower() in address_text.lower():
            # To keep 'Contact' of Company names as it is (e.g. 'Phoenix Contact S.A.S.) @Fahim (5/01/2023)
            if (
                trigger.lower() == "contact"
                and address_text.lower().index("contact") < 10
            ):
                continue
            address_text = address_text.replace(trigger, "")

    address_text = address_text.replace(":", "")
    address_text = replace_undetected_values_in_address(
        master_dictionaries, address_text
    )

    # removing the first line from address block if it contains number more than 3 digits @Fahim (24 Feb 2023)
    address_text_list = address_text.split("\n")
    address_text_list = check_and_process_address_text_first_line(address_text_list)
    address_text = remove_unwanted_values_in_address(address_text_list)

    block = address_text
    processed_block = "\n".join(item for item in block.split("\n") if item)
    address_line_list = processed_block.split("\n")

    if len(address_line_list) == 1:
        address_line_list = block.split(",")

    if address_line_list[0] == "Firma":
        address_line_list = address_line_list[1:]

    if address_line_list[0].isdigit():
        address_line_list.append(address_line_list.pop(0))

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

    for i, line in enumerate(address_line_list):
        match = matches(line, classification_sources)
        if not match and check_suffix(line, master_dictionaries):
            match = True

    # company_name checks
    # If address_text having the company name remove it from address_text and add to final_dict['name']

    # If only one line input is sent the list is empty. So, it returns the input line as name anyway
    # Added by Emon on 12/08/2022
    final_dict = dict()
    tbr = []

    final_dict_builder = FinalDictBuilder(
        address_text, address_line_list, final_dict, tbr
    )
    final_dict_builder.set_company_name(
        company_name, company_line_index, missing_company_suffixes
    )

    address_text = final_dict_builder.get_address_text()
    if not address_line_list:
        return {"name": address_text, "block": block}

    # If project name is Freight, then convert the spanish address to english

    parser_dict = parse_data_from_address(address_text)
    final_dict_builder.set_address_fields(parser_dict)
    if project is not None:
        final_dict_builder.set_postcode(project)
    final_dict_builder.remove_detected_lines_from_address_line_list()
    final_dict_builder.set_address_lines()

    if project is not None:
        address_alternator_process(
            final_dict,
            address_text,
            parser_dict,
            key_val_dict,
            replace_company_name,
            replace_city_name,
            project,
        )

    final_dict_builder.set_country_name(replace_country_name=replace_country_name)
    final_dict_builder.set_country_code(country_map=country_map)
    final_dict_builder.clean_final_dict()
    final_dict_builder.set_account_number()
    final_dict_builder.set_state_province()
    final_dict_builder.set_postal_code()
    final_dict_builder.set_name()

    return OutputDictBuilder(
        final_dict=final_dict,
        key_val_dict=key_val_dict,
        block=block,
        company_stop_words=company_stop_words,
    ).get_output_dict()
