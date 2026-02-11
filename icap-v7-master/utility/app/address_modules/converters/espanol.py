import csv
import json
import re
import traceback

import unidecode
from fuzzywuzzy import process

CONVERSION_DATA = {
    "spanish": {
        "street_types": {
            "calle": "street",
            "avenida": "avenue",
            "carretera": "highway",
            "camino": "road",
            "paseo": "boulevard",
            "plaza": "plaza",
        },
        "building_and_apartment_terms": {
            "edificio": "building",
            "piso": "floor",
            "puerta": "door",
            "apartamento": "apartment",
            "casa": "house",
        },
        "other_common_terms": {
            "número": "number",
            "estado": "state",
            "país": "country",
            "código postal": "zip code",
        },
        "country_names": {
            "españa": "spain",
            "méxico": "mexico",
            "estados unidos": "united states",
            "canadá": "canada",
            "reino unido": "united kingdom",
            "francia": "france",
            "alemania": "germany",
            "italia": "italy",
            "japón": "japan",
            "china": "china",
        },
    }
}
ESPANOL_MAP = None
CITY_NAMES = {}


def replace_patterns(text, source_word, context):
    global CONVERSION_DATA
    # Replace '<street_type> <string>' with '<string> <street_type>', case-insensitive
    pattern = rf"\b{source_word} (\w+)"  # Create the regex pattern dynamically
    ignore_list = ["de"]
    text = re.sub(
        pattern,
        lambda m: f"{m.group(1)} {source_word}"
        if m.group(1).lower() not in ignore_list
        else m.group(0),
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        source_word,
        conversion_data["spanish"][context][source_word],
        text,
        flags=re.IGNORECASE,
    )
    return text


def translate_line(line, replacements):
    original_line = line
    line = line.lower()
    for spanish_word, english_word in replacements.items():
        line = re.sub(
            rf"\b{re.escape(spanish_word)}\b", english_word, line, flags=re.IGNORECASE
        )
    translated_line = ""
    for original_word, translated_word in zip(original_line.split(), line.split()):
        if original_word.isupper():
            translated_word = translated_word.upper()
        elif original_word.istitle():
            translated_word = translated_word.title()
        translated_line += translated_word + " "
    return translated_line.strip()


def translate_spanish_to_english(spanish_text, master_dictionaries):
    """
    Translates Spanish address text to English, focusing on country and city names.

    Args:
        spanish_text (str): Input text in Spanish

    Returns:
        str: Translated text in English
    """

    global CONVERSION_DATA, ESPANOL_MAP, CITY_NAMES

    if not ESPANOL_MAP:
        try:
            ESPANOL_MAP = master_dictionaries.get("translationAddressMap").get("data")
        except:
            pass

    try:
        if not CITY_NAMES:
            for ck, cv in ESPANOL_MAP.items():
                for city_s, city_en in cv["City"].items():
                    CITY_NAMES[city_s] = city_en
    except:
        print(traceback.print_exc())
        pass

    spanish_data = CONVERSION_DATA["spanish"]
    kwds_to_be_removed = [
        "Direccion de recogida",
        "Direccion de entrega",
        "Direccion de facturacion",
    ]

    lines = spanish_text.split("\n")
    translated_lines = []

    detected_country = None
    detected_city = None

    for line in lines:
        line = unidecode.unidecode(line)
        line_lower = line.lower()
        for kwd in kwds_to_be_removed:
            if kwd.lower() in line_lower:
                line = re.sub(re.escape(kwd), "", line, flags=re.IGNORECASE)
        try:
            for country, country_data in ESPANOL_MAP.items():
                if country.lower() in line_lower:
                    detected_country = country
                    line = translate_line(
                        line, {country: country_data["countryEnglish"]}
                    )
        except:
            pass
        try:
            for country, country_data in ESPANOL_MAP.items():
                cities = country_data["City"]
                for city_s, city_en in cities.items():
                    if city_s.lower() in line.lower():
                        line = re.sub(
                            rf"\b{re.escape(city_s)}\b",
                            city_en,
                            line,
                            flags=re.IGNORECASE,
                        )
        except:
            pass

        try:
            for context in [
                "street_types",
                "building_and_apartment_terms",
                "other_common_terms",
            ]:
                for type_s, type_en in spanish_data[context].items():
                    if type_s in line_lower:
                        try:
                            line = replace_patterns(line, type_s, context)
                        except:
                            print(traceback.print_exc())
                            pass
        except:
            pass

        translated_lines.append(line)

    return "\n".join(translated_lines)
