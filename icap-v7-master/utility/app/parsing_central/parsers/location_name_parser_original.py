import re
import traceback

from app.address_modules.address_parser import postal_parse_address
from app.common_dictionary import (
    loc_parser_exception_list,
    replace_country_name,
    replace_locationCode,
)
from app.rules_normalizers_module.sub_rules.exclude import apply_exclude_rules_on

global master_dictionaries
# version#5.01.17112022 @Fahim

# Exclusion list added


def process(master_dictionaries, string):
    # master_dictionaries = request_data.get("master_dictionaries")
    country_Map = master_dictionaries.get("country_Map").get("data")
    string = string.strip()
    # print("1. checking input string:", string)
    try:
        exclusion_list = ["country of origin", "airport"]

        country_list = [
            "Afghanistan",
            "Aland Islands",
            "Albania",
            "Algeria",
            "American Samoa",
            "Andorra",
            "Angola",
            "Anguilla",
            "Antarctica",
            "Antigua and Barbuda",
            "Argentina",
            "Armenia",
            "Aruba",
            "Australia",
            "Austria",
            "Azerbaijan",
            "Bahamas",
            "Bahrain",
            "Bangladesh",
            "Barbados",
            "Belarus",
            "Belgium",
            "Belize",
            "Benin",
            "Bermuda",
            "Bhutan",
            "Bolivia, Plurinational State of",
            "Bonaire, Sint Eustatius and Saba",
            "Bosnia and Herzegovina",
            "Botswana",
            "Bouvet Island",
            "Brazil",
            "British Indian Ocean Territory",
            "Brunei Darussalam",
            "Bulgaria",
            "Burkina Faso",
            "Burundi",
            "Cambodia",
            "Cameroon",
            "Canada",
            "Cape Verde",
            "Cayman Islands",
            "Central African Republic",
            "Chad",
            "Chile",
            "China",
            "Christmas Island",
            "Cocos (Keeling) Islands",
            "Colombia",
            "Comoros",
            "Congo",
            "Congo, The Democratic Republic of the",
            "Cook Islands",
            "Costa Rica",
            "Côte d'Ivoire",
            "Croatia",
            "Cuba",
            "Curaçao",
            "Cyprus",
            "Czech Republic",
            "Denmark",
            "Djibouti",
            "Dominica",
            "Dominican Republic",
            "Ecuador",
            "Egypt",
            "El Salvador",
            "Equatorial Guinea",
            "Eritrea",
            "Estonia",
            "Ethiopia",
            "Falkland Islands (Malvinas)",
            "Faroe Islands",
            "Fiji",
            "Finland",
            "France",
            "French Guiana",
            "French Polynesia",
            "French Southern Territories",
            "Gabon",
            "Gambia",
            "Georgia",
            "Germany",
            "Ghana",
            "Gibraltar",
            "Greece",
            "Greenland",
            "Grenada",
            "Guadeloupe",
            "Guam",
            "Guatemala",
            "Guernsey",
            "Guinea",
            "Guinea-Bissau",
            "Guyana",
            "Haiti",
            "Heard Island and McDonald Islands",
            "Holy See (Vatican City State)",
            "Honduras",
            "Hong Kong",
            "Hungary",
            "Iceland",
            "India",
            "Indonesia",
            "Iran, Islamic Republic of",
            "Iraq",
            "Ireland",
            "Isle of Man",
            "Israel",
            "Italy",
            "Jamaica",
            "Japan",
            "Jersey",
            "Jordan",
            "Kazakhstan",
            "Kenya",
            "Kiribati",
            "Korea, Democratic People's Republic of",
            "Korea, Republic of",
            "South Korea",
            "North Korea",
            "Kuwait",
            "Kyrgyzstan",
            "Lao People's Democratic Republic",
            "Latvia",
            "Lebanon",
            "Lesotho",
            "Liberia",
            "Libya",
            "Liechtenstein",
            "Lithuania",
            "Luxembourg",
            "Macao",
            "Macedonia, Republic of",
            "Madagascar",
            "Malawi",
            "Malaysia",
            "Maldives",
            "Mali",
            "Malta",
            "Marshall Islands",
            "Martinique",
            "Mauritania",
            "Mauritius",
            "Mayotte",
            "Mexico",
            "Micronesia, Federated States of",
            "Moldova, Republic of",
            "Monaco",
            "Mongolia",
            "Montenegro",
            "Montserrat",
            "Morocco",
            "Mozambique",
            "Myanmar",
            "Namibia",
            "Nauru",
            "Nepal",
            "Netherlands",
            "New Caledonia",
            "New Zealand",
            "Nicaragua",
            "Niger",
            "Nigeria",
            "Niue",
            "Norfolk Island",
            "Northern Mariana Islands",
            "Norway",
            "Oman",
            "Pakistan",
            "Palau",
            "Palestinian Territory, Occupied",
            "Panama",
            "Papua New Guinea",
            "Paraguay",
            "Peru",
            "Philippines",
            "Pitcairn",
            "Poland",
            "Portugal",
            "Puerto Rico",
            "Qatar",
            "Réunion",
            "Romania",
            "Russian Federation",
            "Rwanda",
            "Saint Barthélemy",
            "Saint Helena, Ascension and Tristan da Cunha",
            "Saint Kitts and Nevis",
            "Saint Lucia",
            "Saint Martin (French part)",
            "Saint Pierre and Miquelon",
            "Saint Vincent and the Grenadines",
            "Samoa",
            "San Marino",
            "Sao Tome and Principe",
            "Saudi Arabia",
            "Senegal",
            "Serbia",
            "Seychelles",
            "Sierra Leone",
            "Singapore",
            "Sint Maarten (Dutch part)",
            "Slovakia",
            "Slovenia",
            "Solomon Islands",
            "Somalia",
            "South Africa",
            "South Georgia and the South Sandwich Islands",
            "Spain",
            "Sri Lanka",
            "Sudan",
            "Suriname",
            "South Sudan",
            "Svalbard and Jan Mayen",
            "Swaziland",
            "Sweden",
            "Switzerland",
            "Syrian Arab Republic",
            "Taiwan, Province of China",
            "Tajikistan",
            "Tanzania, United Republic of",
            "Thailand",
            "Timor-Leste",
            "Togo",
            "Tokelau",
            "Tonga",
            "Trinidad and Tobago",
            "Tunisia",
            "Turkey",
            "Turkmenistan",
            "Turks and Caicos Islands",
            "Tuvalu",
            "Uganda",
            "Ukraine",
            "United Arab Emirates",
            "United Kingdom",
            "United States",
            "United States Minor Outlying Islands",
            "Uruguay",
            "Uzbekistan",
            "Vanuatu",
            "Venezuela, Bolivarian Republic of",
            "Viet Nam",
            "Virgin Islands, British",
            "Virgin Islands, U.S.",
            "Wallis and Futuna",
            "Yemen",
            "Zambia",
            "Zimbabwe",
        ]
        # city names must be small case
        city_exception_list = ["guarulous"]
        extraData = None

        # grabbing location, locationCode and locationCountry @Fahim (24/09/2022)
        if "(" in string:
            if ")" in string:
                # print("2. checking string count:", string.count("("))
                # print("3. checking string count:", string.count(")"))
                if not string.count("(") == string.count(")"):
                    if string.count("(") == 3 and string.count(")") == 2:
                        start_index = string.index("(", string.index("(") + 1)
                        second_start_index = string.index(
                            "(", string.index("(", string.index("(") + 1) + 1
                        )
                        end_index = string.index(")", string.index(")") + 1)
                        location = string[0:second_start_index].strip()
                        locationCode = string[second_start_index + 1 : end_index]
                        locationCountry = string[end_index + 1 :].strip()

                if string.count("(") == 1 and string.count(")") == 1:
                    start_index = string.index("(")
                    end_index = string.index(")")
                    location = string[0:start_index].strip()
                    locationCode = string[start_index + 1 : end_index]
                    locationCountry = string[end_index + 1 :].strip()
                if string.count("(") == 2 and string.count(")") == 2:
                    if (string.index(")") - string.index("(")) > 6:
                        start_index = string.index(
                            "(", string.index("(") + 1
                        )  # finding the second occurance/index of "("
                        end_index = string.index(
                            ")", string.index(")") + 1
                        )  # finding the second occurance/index of ")"
                        location = string[0:start_index].strip()
                        locationCode = string[start_index + 1 : end_index]
                        locationCountry = string[end_index + 1 :].strip()
                    elif string.index(")") - string.index("(") == 5:
                        modified_string = string.replace(
                            string[string.index("(") : string.index(")") + 1], ""
                        ).replace(",", "")
                        location = modified_string[: modified_string.index("(")].strip()
                        locationCode = modified_string[
                            modified_string.index("(") + 1 : modified_string.index(")")
                        ].strip()
                        locationCountry = modified_string[
                            string.index(")") + 1 :
                        ].strip()

            elif ")" not in string:
                if string.count("(") == 1 and string.count(")") == 0:
                    start_index = string.index("(")
                    location = string[0:start_index].strip()
                    other_part_list = string[start_index + 1 :].strip().split(" ")
                    locationCode = other_part_list[0].strip()
                    locationCountry = (
                        string[start_index + 1 :]
                        .strip()
                        .replace(locationCode, "")
                        .strip()
                    )

            # Handling OCR errors of locationCode
            for i in replace_locationCode:
                if i["original_value"].lower() == locationCode.lower():
                    locationCode = i["translate_value"]
            # Handling OCR errors of locationCountry
            for i in replace_country_name:
                if i["original_value"].lower() == locationCountry.lower():
                    locationCountry = i["translate_value"]

            if "," in locationCountry:
                locationCountry = locationCountry.replace(",", "")
            if "\n" in locationCountry:
                locationCountry = locationCountry.replace("\n", " ")
            locationCountry = locationCountry.strip()
            if len(locationCountry.split(" ")) == 2:
                if len(locationCountry.split(" ")[1]) <= 3:
                    locationCountry = locationCountry.replace(" ", "")
            if locationCountry:
                for key, countryiso in country_Map["Country"].items():
                    if locationCountry.lower() in key.lower():
                        locationCountry = countryiso["ISO2"]
                        break
            # print("5. checking location:", location)
            # print("6. checking location code:", locationCode)
            # print("7. checking location country:", locationCountry)
            return [location, locationCode, locationCountry, extraData]

        try:
            for x in exclusion_list:
                y = re.compile(re.escape(x), re.IGNORECASE)
                string = y.sub("", string)
                if string[0] == ":":
                    string = string[1:]
                string = string.strip()
        except:
            # print(traceback.print_exc())
            pass

        # checking if there's more than one country
        country_count = 0
        country_part_list = string.split(" ")
        for i in country_part_list:
            if "," in i:
                i = i.replace(",", "")
            if i.strip().title() in country_list:
                country_count += 1
        if country_count > 1:
            return [country_part]

        loc_text = string.strip()
        postal_result = postal_parse_address(loc_text)
        extraData = None
        try:
            # Fix for port identified as a city
            for x, y in postal_result:
                if y == "city" and (x.lower() == "port"):
                    value_text = value_text.lower().replace("port", "")
                    postal_result = postal_parse_address(value_text)
        except:
            pass
        loc_parsed = dict()
        country_full = None
        for x, y in postal_result:
            loc_parsed[y] = x

        # print("7. checking loc parsed:", loc_parsed)
        city = None
        country = None
        # fix for port identified as city
        if "city" in loc_parsed.keys() and (
            loc_parsed["city"].strip().lower() == "port"
        ):
            loc_parsed.pop("city", None)

        if "city" in loc_parsed.keys():
            city = loc_parsed["city"].title()
            # print("5. checking city:", city)
        else:
            if "state" in loc_parsed.keys():
                city = loc_parsed["state"].title()
        if "country" in loc_parsed.keys():
            country_full = loc_parsed["country"].title()

        # grabbing city and country from input string if city and country not found @Fahim (12/10/2022)
        if city == None and country == None:
            for i in city_exception_list:
                if i in string.lower():
                    city = i.title()
                    string = string.lower().replace(i, "")
                    break
            country = string.strip()
            if "," in country:
                country = country.replace(",", "")
                country = country.strip()
            country_full = country

        iso_found = False
        if country_full:
            if not iso_found:
                for key, countryiso in country_Map["Country"].items():
                    if country_full.strip().lower() in key.lower():
                        country = countryiso["ISO2"]
                        iso_found = True

        # grabbing the word before port as city too (e.g. FREMANTLE PORT, AUSTRALIA)
        if "house" in loc_parsed.keys() and "city" in loc_parsed.keys():
            if loc_parsed["city"] == "port":
                city = loc_parsed["house"] + " " + loc_parsed["city"]
                city = city.title()

        if not "country" in loc_parsed.keys() and country == None:
            return [string]

        for exception_text, exception_iso in loc_parser_exception_list.items():
            if exception_text in loc_text:
                country = exception_iso
                city = loc_text.replace(exception_text, "", 1).strip()
                if city[-1] == ",":
                    city = city[:-1]

            else:
                pass
                # print(exception_text, loc_text)

        # print("6. checking city:", city)
        location = None
        if city:
            location = city
        if country:
            locationCountry = country
        else:
            if country_full:
                locationCountry = country_full
        if (not location) and locationCountry:
            location = string

        # checking if the country is valid or not @Fahim(17/11/2022)
        if locationCountry.strip().title() not in country_list:
            locationCountry = None

        # print("2. checking location:", location)
        # print("3. checking location country:", locationCountry)
        # print("4. checking extra Data:", extraData)
        return [location, locationCountry, extraData]
    except:
        print(traceback.print_exc())
        return [string]
