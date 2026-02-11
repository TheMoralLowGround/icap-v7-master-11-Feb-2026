import re
import traceback

import pycountry
from rapidfuzz import fuzz, utils

from app.address_modules.address_parser import postal_parse_address
from app.common_dictionary import (
    loc_parser_exception_list,
    replace_country_name,
    replace_locationCode,
)
from app.parsing_central.parsers.dictionaries.ports_dictonary import port_dict

global master_dictionaries


def get_alpha2_country_code(country: str) -> str:
    country = pycountry.countries.get(name=country)
    return country.alpha_2


def calculate_similarity_ratio_fuzzy_match(string1: str, string2: str) -> float:
    return fuzz.WRatio(
        string1.lower(), string2.lower(), processor=utils.default_process
    )


def find_best_match_country_from_string(string: str) -> str:
    max_similarity_ratio = 0
    best_match_country = None

    for country in pycountry.countries:
        if country.name.lower() in string.lower():
            best_match_country = country.name
            break
        else:
            similarity_ratio = calculate_similarity_ratio_fuzzy_match(
                country.name, string
            )

            if similarity_ratio > max_similarity_ratio:
                max_similarity_ratio = similarity_ratio
                best_match_country = country.name
    return best_match_country


def filter_country_data_by_coutry_code(
    port_dict: dict, country_alpha2_codes: str
) -> dict:
    country_data = [
        {
            "data": [
                location
                for location in item["data"]
                if (
                    "CountryCode" in location
                    and location["CountryCode"].strip().lower()
                    == country_alpha2_codes.strip().lower()
                )
                or (
                    "COUNTRY" in location
                    and location["COUNTRY"].strip().lower()
                    == country_alpha2_codes.strip().lower()
                )
            ]
        }
        for item in port_dict
    ]
    return country_data


def find_best_match_port_location(
    port_dict: dict, location_name: str, country_alpha2: str
) -> dict:
    max_similarity_ratio = 0
    best_matching_location = None

    filtered_country_data = filter_country_data_by_coutry_code(
        port_dict, country_alpha2
    )

    # Traverse the filtered_country_data and check similarity
    for item in filtered_country_data:
        for data in item["data"]:
            if "LocationName" in data:
                location_code = data["LocationCode"].replace(country_alpha2, "")
                similarity_ratio = calculate_similarity_ratio_fuzzy_match(
                    f"{data['LocationName']}{location_code}", location_name
                )
            # if 'PORT_NAME' in data:
            else:
                location_code = data["CODE"].replace(country_alpha2, "")
                similarity_ratio = calculate_similarity_ratio_fuzzy_match(
                    f"{data['PORT_NAME']}{location_code}", location_name
                )

            if similarity_ratio > max_similarity_ratio:
                max_similarity_ratio = similarity_ratio
                best_matching_location = data

    print(f"percentage: {max_similarity_ratio}")
    print(f"Data: {best_matching_location}")
    return best_matching_location


def clean_up_location_country_string(locationCountry: str) -> str:
    replacements = {",": "", "\n": " "}
    for old, new in replacements.items():
        locationCountry = locationCountry.replace(old, new)
    return locationCountry.strip()


def process(master_dictionaries: dict, string: str) -> list:
    locationCode = ""
    locationCountry = ""
    location = ""

    string = clean_up_location_country_string(string)

    country = find_best_match_country_from_string(string)
    print("-" * 25)
    print(f"Recived String : [---{string}---]")
    print(f"Extracted Country: {country}")

    country_alpha2 = get_alpha2_country_code(country)
    updated_string = string.lower().replace(country.lower(), "")

    matched_location = find_best_match_port_location(
        port_dict, updated_string, country_alpha2
    )
    print("-" * 25)
    if "LocationName" in matched_location:
        location = matched_location["LocationName"]
        locationCode = matched_location["LocationCode"]
        locationCountry = matched_location["CountryCode"]

    else:
        location = matched_location["PORT_NAME"]
        locationCode = matched_location["CODE"]
        locationCountry = matched_location["COUNTRY"]

    return [location, locationCode, locationCountry]
