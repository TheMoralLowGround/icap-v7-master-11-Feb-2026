import json
import re
import traceback

import pycountry
import rapidfuzz
from rapidfuzz import fuzz, process, utils
from rapidfuzz.distance import Levenshtein
from redis_utils import (
    get_port_json_from_redis,
    get_redis_keys,
    upload_port_json_file_to_redis,
    update_port_dict_cache,
)


def dict_formatter(seaport_dictionary):
    new_dict = {}
    duplicate_count = 0
    success_count = 0
    fail_count = 0
    for i in seaport_dictionary:
        try:
            CountryCode, LocationCode, LocationName = (
                i["CountryCode"],
                i["LocationCode"],
                i["LocationName"],
            )
        except:
            CountryCode, LocationCode, LocationName = (
                i["COUNTRY"],
                i["CODE"],
                i["PORT_NAME"],
            )

        locationCountry = pycountry.countries.get(alpha_2=CountryCode)
        try:
            locationCountry = locationCountry.name
        except:
            locationCountry = locationCountry
        k = f"{LocationName},{LocationCode},{locationCountry}"
        v = CountryCode
        if k not in new_dict:
            new_dict[k] = v
            success_count += 1
        else:
            duplicate_count += 1

    return new_dict


def semantic_matching_percentage(string1, string2):
    string1_normalized = string1.lower().strip()
    string2_normalized = string2.lower().strip()

    ratio = fuzz.ratio(string1_normalized, string2_normalized)
    partial_ratio = fuzz.partial_ratio(string1_normalized, string2_normalized)
    token_sort_ratio = fuzz.token_sort_ratio(string1_normalized, string2_normalized)
    token_set_ratio = fuzz.token_set_ratio(string1_normalized, string2_normalized)

    combined_score = (ratio + partial_ratio + token_sort_ratio + token_set_ratio) / 4

    return combined_score


def get_sea_port_location_info(
    given_location, given_location_cleaned, seaport_dictionary
):
    location_country_mapping = dict_formatter(seaport_dictionary)
    locations = list(location_country_mapping.keys())
    given_location = given_location.strip()
    remove_ex_name = False
    location = None
    locationCode = None
    countryCode = None
    locationCountry = None
    max_score = 0

    if not re.search(r"\s*\(.*?ex[^\)]*\)", given_location, flags=re.IGNORECASE):
        remove_ex_name = True

    for l in locations:
        l_prev = l
        if remove_ex_name and re.search(r"\s*\(.*?ex[^\)]*\)", l, flags=re.IGNORECASE):
            l = re.sub(r"\s*\(.*?ex[^\)]*\)", "", l, flags=re.IGNORECASE)
        if len(given_location) <= len(l.split(",")[0].strip()):
            location_to_compare = l.split(",")[0]
        elif (
            len(given_location)
            <= len(l.split(",")[0].strip()) + len(l.split(",")[2].strip()) + 1
        ):
            location_to_compare = (
                l.split(",")[0].strip() + " " + l.split(",")[2].strip()
            )
        else:
            location_to_compare = (
                l.split(",")[0].strip()
                + " "
                + l.split(",")[1].strip()
                + " "
                + l.split(",")[2].strip()
            )

        score = semantic_matching_percentage(
            given_location_cleaned, location_to_compare
        )

        if score > max_score:
            l = l_prev
            max_score = score
            l = l.strip()
            location = l.split(",")[0].strip()
            locationCode = l.split(",")[1].strip()
            countryCode = locationCode[:2].strip()
            locationCountry = l.split(",")[2].strip()

    return [location, locationCode, countryCode]


def get_alpha2_country_code(country: str) -> str:
    country = pycountry.countries.get(name=country)
    return country.alpha_2


def get_country_name(country_alpha2: str) -> str:
    country = pycountry.countries.get(alpha_2=country_alpha2)
    return country.name


def calculate_similarity_ratio_fuzzy_match_partial(string1: str, string2: str):
    return fuzz.partial_ratio(
        string1.lower(), string2.lower(), processor=utils.default_process
    )


def calculate_similarity_ratio_fuzzy_match_wratio(string1: str, string2: str):
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
            similarity_ratio = calculate_similarity_ratio_fuzzy_match_wratio(
                country.name, string
            )

            if similarity_ratio > max_similarity_ratio:
                max_similarity_ratio = similarity_ratio
                best_match_country = country
    return best_match_country


def get_exception_word_list(master_dictionaries):
    try:
        location_exception_words = master_dictionaries.get(
            "location_exception_words"
        ).get("data")
        return [word.lower() for word in location_exception_words]
    except:
        pass


def clean_up_location_string(master_dictionaries: dict, location_string: str) -> str:
    def remove_words_with_digits(string: str) -> str:
        string = remove_special_characters(string)
        string = remove_words_with_only_digits(string)

        words = string.split()
        cleaned_words = []

        for word in words:
            consecutive_digits = 0
            for i in range(len(word) - 1):
                if word[i].isdigit() and word[i + 1].isdigit():
                    consecutive_digits += 1
                    if consecutive_digits >= 2:
                        break
                else:
                    consecutive_digits = 0

            if consecutive_digits < 2:
                cleaned_words.append(word)

        cleaned_string = " ".join(cleaned_words)
        return cleaned_string

    def remove_words_with_only_digits(location_string: str) -> str:
        words = location_string.split()
        words = [word for word in words if not word.isdigit()]
        return (" ").join(words)

    def remove_special_characters(sting: str) -> str:
        tokens = sting.split()
        filtered_tokens = [re.sub("[^a-zA-Z0-9]+", "", _) for _ in tokens]
        while "" in filtered_tokens:
            filtered_tokens.remove("")
        string = (" ").join(filtered_tokens)
        return string

    def clean(location_string: str) -> str:
        replacements = {
            ",": "",
            "\n": " ",
            "1": "I",
            "0": "O",
            "4": "A",
            "8": "B",
            "7": "T",
            "5": "S",
            "VV": "W",
            "2": "Z",
        }
        for old, new in replacements.items():
            location_string = location_string.replace(old, new)
        return location_string

    def remove_exception_word_from_string(location_string: str) -> str:
        tokens = location_string.split()
        exception_word_list = get_exception_word_list(master_dictionaries)

        for idx, word in enumerate(tokens):
            if word.lower() in exception_word_list:
                tokens[idx] = ""
        while "" in tokens:
            tokens.remove("")
        return (" ").join(tokens)

    location_string = remove_special_characters(location_string)
    location_string = remove_words_with_only_digits(location_string)
    location_string = remove_words_with_digits(location_string)
    location_string = clean(location_string)
    location_string = remove_exception_word_from_string(location_string)

    print(location_string)

    return location_string.strip()

def find_best_match_airport_location_old(
    master_dictionaries: dict, location_string: str, airport_dict: dict
) -> dict:
    max_similarity_ratio = 0
    best_matching_location = None
    best_match_location_string = ""
    airport_dict = airport_dict["airports"]
    for key, values in airport_dict.items():
        name_list = [name.lower() for name in airport_dict[key]["name"]]
        similarity_ratio = 0

        for name in name_list:
            similarity_ratio_sub = semantic_matching_percentage(name, location_string)
            if similarity_ratio_sub > similarity_ratio:
                similarity_ratio = similarity_ratio_sub

        if similarity_ratio > max_similarity_ratio:
            max_similarity_ratio = similarity_ratio
            best_matching_location = airport_dict[key]

    best_matching_location["name"] = best_match_location_string
    return best_matching_location


def find_best_match_airport_location(
    master_dictionaries: dict, location_string: str, airport_dict: dict
) -> dict:
    airport_dict = airport_dict["airports"]
    original_location_string = location_string
    
    # Check if location_string contains "/" and handle accordingly
    airport_code_from_string = None
    
    if "/" in location_string:
        parts = location_string.split("/")
        location_name = parts[0].strip()
        second_part = parts[1].strip().replace("0","O") if len(parts) > 1 else ""
        pattern_match = re.search(r"^.{3}([A-Z]{3})", second_part)
        
        if pattern_match:
            airport_code_from_string = pattern_match.group(1)
        
        # Use the first part (location name) for matching
        location_string = location_name
    
    # Find best matches based on location name
    all_matches = []
    for key in airport_dict.keys():
        name_list = [name.lower() for name in airport_dict[key]["name"]]
        
        for name in name_list:
            similarity_ratio = semantic_matching_percentage(name, location_string)
            all_matches.append({
                "airport_key": key,
                "name": name,
                "similarity": similarity_ratio,
                "airport_data": airport_dict[key]
            })
    
    if not all_matches:
        # Return the whole string if no matches found
        return {"name": original_location_string, "original_string": True}
    
    all_matches.sort(key=lambda x: x["similarity"], reverse=True)
    top_3_matches = all_matches[:3]
    
    # If we have an airport code from the string, try to match it with top 3 matches
    if airport_code_from_string:
        for match in top_3_matches:
            if match["airport_key"] == airport_code_from_string:
                exact_match_location = match["airport_data"].copy()
                exact_match_location["name"] = match["name"]
                return exact_match_location
    
    # If no airport code match in top 3, return the best match ratio
    best_match = top_3_matches[0]
    best_matching_location = best_match["airport_data"].copy()
    best_matching_location["name"] = best_match["name"]
    return best_matching_location


def load_port_dictionary_with_cache_fallback(
    master_dictionaries: dict, 
    port_dictionary_pattern: str, 
    is_airport: bool,
) -> dict:
    """
    Load port dictionary from Redis cache with automatic cache update fallback.
    
    Args:
        master_dictionaries: Master dictionaries for cache updates
        port_dictionary_pattern: Regex pattern to match Redis keys
        is_airport: True for airports, False for seaports
    
    Returns:
        Dictionary containing port data with 'airports' or 'seaports' key
    """
    port_type = "airports" if is_airport else "seaports"
    port_dict = {port_type: []}
    
    def load_from_cache() -> dict:
        """Load port data from Redis cache based on pattern."""
        redis_keys = get_redis_keys()
        decoded_keys = [key.decode("utf-8") for key in redis_keys]
        
        for key in decoded_keys:
            if re.search(port_dictionary_pattern, key):
                chunk_port_dict = get_port_json_from_redis(key)
                port_dict[port_type] = chunk_port_dict
                break
        
        return port_dict
    
    # First attempt to load from cache
    result = load_from_cache()
    
    # If cache is empty, update cache and try again
    if len(result[port_type]) == 0:
        print(f"Cache empty for {port_type}, updating cache...")
        update_port_dict_cache(master_dictionaries)
        result = load_from_cache()
    
    return result

def process(master_dictionaries: dict, string: str, doc_type) -> list:
    # New location fuzzy matcher by Asik - July 2, 2024
    locationCode = None
    locationCountry = None
    location = None
    print(f"{string=}")
    if doc_type.lower() in  ["airway bill", "house air waybill"]:
        airport_dictionary_name_pattern = "airport_dict_part"
        airport_dictionary = load_port_dictionary_with_cache_fallback(
            master_dictionaries, airport_dictionary_name_pattern, True
        )
        if "/" not in string:
            string_cleaned = clean_up_location_string(master_dictionaries, string)
            print(f"{string_cleaned=}")
        else:
            string_cleaned = string
        matched_location = find_best_match_airport_location(
            master_dictionaries, string_cleaned, airport_dictionary
        )

        if not matched_location:
            return [location, locationCode, locationCountry]
        else:
            location = matched_location["city"]
            locationCountry = matched_location["country"]
            locationCode = f"{locationCountry}{matched_location['iata']}"

            return [location, locationCode, locationCountry]

    else:
        seaport_dictionary_name_pattern = "seaport_dict_part1"
        seaport_dictionary = load_port_dictionary_with_cache_fallback(
            master_dictionaries,
            seaport_dictionary_name_pattern, False
        )

        string_cleaned = clean_up_location_string(master_dictionaries, string)
        return get_sea_port_location_info(
            string, string_cleaned, seaport_dictionary["seaports"]
        )
