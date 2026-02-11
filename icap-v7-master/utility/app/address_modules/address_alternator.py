import re

"""
This is a script that altered parsing results for address parser. Mostly legacy code pieces.
These were ad-hoc changes made by dev team for a particular project.
This script is to be made redundant soon.
"""


def address_alternator_process(
    final_dict,
    address_text,
    parser_dict,
    key_val_dict,
    replace_company_name,
    replace_city_name,
    project="",
):
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
    # put all country, countryCode, state and ignore_removal in lowercase letters (as we are checking for lowercase)
    country_exception_list = [
        "argentina",
        "china",
        "u.s.a.",
        "us",
        "canada",
        "italy",
        "slowakei",
        "br-brazil",
        "brazil",
        "hungary",
        "united arab emiratesates",
        "fiji",
        "fill",
        "i ndia",
        "singapore",
        "sudsouth korea",
        "korea",
        "vietnam",
        "kenya",
        "utd.arab emir",
        "taiwan",
        "hongkong",
        "egypt",
        "united kingdom",
        "sweden",
        "chile",
    ]
    country_code_exception_list = ["kr", "cr", "ae", "de"]
    state_exception_list = ["gyeonggi-do", "gyeonggi-00"]
    ignore_removal_list = ["branch", "service oph"]
    AD1_exception_list = ["sri city"]
    city_exception_list = [
        "HYDERABAD",
        "SHANGHAI",
        "Shanghai",
        "Shanghai,",
        "Buchs",
        "SG",
        "Chonburi",
        "Province",
        "Dubai",
        "DUBAI",
        "BHIWANDI",
        "Dudelang",
        "bangalore",
        "Bangalore",
        "Somerset",
        "SAN",
        "JOSE",
        "ITAPEVI-SP",
        "Kancheepuram",
        "Hai",
        "Duong",
        "City",
        "Gumi-Si",
        "NAIROBI",
        "(Barcelona)",
        "CANCUN",
        "Kwai-Chung",
        "Horsley",
        "Park,",
    ]
    postcode_exception_list = [
        "l-3451",
        "9999",
        "39422",
        "10135",
        "77560",
        "33182",
        "110-240",
        "17711",
        "13140-970",
        "30043",
        "AU-2175",
    ]
    company_exception_list = [
        "Olympus Medical Systems India",
        "husqvarna south africa ltd",
        "DDP SPECIALITY PRODUCTS INDIA",
        "Husky Injection Molding Sys SA",
        "Tic. A.S.",
        "Kerry Logistics (M) Sdn Bhd, C/O NCR Malaysia SDN BHD",
        "NCR CORPORATION C/O FEDEX GLOBAL SUPPLY CHAIN SERVICES",
    ]
    remove_word_list = [
        "Service",
        "Hot Runners & Molds, Lux",
        "E-",
        "e-",
        "p.r.",
        "of",
        "kwr.ca",
        "Systems(Shanghai) Machi",
        "country",
        "Country",
        "REPUBLIC OF",
        "REF# 320001937",
        "pincode",
        "ku 2-1-1",
        "Nikki Basaraba e-",
        "Paul Naran e-",
    ]
    remove_fax_list = ["(571) 647 68 90"]
    startswith_remove_list = ["address", "street", "place"]

    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for FLEXTRONICS)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if len(final_dict["name"].split(" ")) > 15:
            if "Cainiao" in final_dict["name"]:
                final_dict["addressLine2"] = final_dict["addressLine1"]
                splitted_name_list = final_dict["name"].split("Cainiao")
                final_dict["name"] = splitted_name_list[0]
                final_dict["addressLine1"] = "Cainiao" + splitted_name_list[1]
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for BIOSENSE)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if len(final_dict["name"].split(" ")) > 5:
            if "JACOB" in final_dict["name"]:
                final_dict["addressLine2"] = final_dict["addressLine1"]
                splitted_name_list = final_dict["name"].split("JACOB")
                final_dict["name"] = splitted_name_list[0]
                final_dict["addressLine1"] = "JACOB " + splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for Olympus)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            "Olympus Hong Kong and China Ltd".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 10
        ):
            final_dict["addressLine2"] = final_dict["addressLine1"]
            splitted_name_list = final_dict["name"].split("Ltd.")
            final_dict["name"] = splitted_name_list[0] + "Ltd."
            final_dict["addressLine1"] = splitted_name_list[1]
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for 3M PANAMA)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            "3M Panama Pacifico S de RL".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 10
        ):
            final_dict["addressLine2"] = final_dict["addressLine1"]
            splitted_name_list = final_dict["name"].split("RL")
            final_dict["name"] = splitted_name_list[0] + "RL"
            final_dict["addressLine1"] = splitted_name_list[1]
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for GALAXY SURFACTANTS)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "TRI-K INDUSTRIES, INC.".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 3
        ):
            # final_dict["addressLine2"] = final_dict["addressLine1"].strip() + " " + final_dict["addressLine2"]
            splitted_name_list = final_dict["name"].split("INC.")
            final_dict["name"] = splitted_name_list[0].strip() + " INC."
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for BALLANDE ET MENERET)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            "Summergate International Trading (Shanghai) Limited Company".lower()
            in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 6
        ):
            splitted_name_list = final_dict["name"].split("Company")
            final_dict["name"] = splitted_name_list[0].strip() + " Company"
            final_dict["addressLine1"] = (
                splitted_name_list[1].strip() + " " + final_dict["addressLine1"].strip()
            )
    # shortening 'name' field if it's too long, splitting it into AD1 and AD2 (exceptional case for ANTONIO PUIG)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            "MUFEL S.A. DE CV".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 8
        ):
            if "méxico" in final_dict["addressLine2"].lower():
                final_dict["country"] = "México"
            final_dict["addressLine2"] = final_dict["addressLine1"]
            splitted_name_list = final_dict["name"].split("CV")
            final_dict["name"] = splitted_name_list[0].strip() + " CV"
            final_dict["addressLine1"] = splitted_name_list[1]
        elif (
            "AGENCIA ADUANAL PALAZUELOS ACEVAL".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 8
        ):
            if "77560" in final_dict["addressLine2"].lower():
                final_dict["postcode"] = "77560"
            if "CANCÚN" in final_dict["addressLine2"].upper():
                final_dict["city"] = "CANCÚN"
            final_dict["addressLine2"] = final_dict["addressLine1"]
            splitted_name_list = final_dict["name"].split("ACEVAL")
            final_dict["name"] = splitted_name_list[0].strip() + " ACEVAL"
            final_dict["addressLine1"] = splitted_name_list[1]
    # shortening 'name' field if it's too long, splitting it into AD1 (if AD1 not there) (exceptional case for HUSQVARNA)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "SOCOMAQ SPA AMERICO VESPUCIO".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 6
        ):
            splitted_name_list = final_dict["name"].split("AMERICO")
            final_dict["name"] = splitted_name_list[0].strip()
            final_dict["addressLine1"] = "AMERICO " + splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (if AD1 not there) (exceptional case for WORLDEX I & T)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "West Coast Quartz Corporation".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 9
        ):
            splitted_name_list = final_dict["name"].split("Corporation")
            final_dict["name"] = splitted_name_list[0].strip() + " Corporation"
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (if AD1 not there) (exceptional case for BIOMERIEUX)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "BIOMERIEUX MEXICO SA DE CV".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 8
        ):
            splitted_name_list = final_dict["name"].split("CV")
            final_dict["name"] = splitted_name_list[0].strip() + " CV"
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field (upto Ltd.) if it's too long, splitting it into AD1 (adding with AD1) (exceptional case for BIOMERIEUX)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "bioMerieux Colombia S.A.S.".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 5
        ):
            splitted_name_list = final_dict["name"].split("S.A.S.")
            final_dict["name"] = splitted_name_list[0].strip() + " S.A.S."
            final_dict["addressLine1"] = (
                splitted_name_list[1].strip() + " " + final_dict["addressLine1"].strip()
            )
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for I.F.F.)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" not in final_dict.keys()
    ):
        if (
            "I.F.F. (MEXICO)".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 12
        ):
            splitted_name_list = final_dict["name"].split("SAN")
            final_dict["name"] = splitted_name_list[0].strip()
            final_dict["addressLine2"] = final_dict["addressLine1"]
            final_dict["addressLine1"] = "SAN " + splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for SCHNEIDER ELECTRIC)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "SCHNEIDER ELECTRIC ESPANA, S.A.".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 9
        ):
            splitted_name_list = final_dict["name"].split("S.A.")
            final_dict["name"] = splitted_name_list[0].strip() + " S.A."
            if "addressLine2" not in final_dict.keys():
                final_dict["addressLine2"] = final_dict["addressLine1"]
                final_dict["addressLine1"] = splitted_name_list[1].strip()
            else:
                if "spain" in final_dict["addressLine2"].lower():
                    final_dict["country"] = "spain"
                if (
                    "08830-Sant Boi de Llobregat".lower()
                    in final_dict["addressLine1"].lower()
                ):
                    final_dict["postcode"] = "08830"
                    final_dict["city"] = "boi de llobregat"
                final_dict["addressLine2"] = final_dict["addressLine1"]
                final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field (upto Ltd.) if it's too long, splitting it into AD1 (adding with AD1) (exceptional case for Karl)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "Husky Injection".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 5
        ):
            if "Ltd." in final_dict["name"]:
                splitted_name_list = final_dict["name"].split("Ltd.")
                final_dict["name"] = splitted_name_list[0].strip() + " Ltd."
                final_dict["addressLine1"] = (
                    splitted_name_list[1].strip()
                    + " "
                    + final_dict["addressLine1"].strip()
                )
        elif (
            "Shanghai SK Transformer Company".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 5
        ):
            splitted_name_list = final_dict["name"].split("Ltd,")
            final_dict["name"] = splitted_name_list[0].strip() + " Ltd,"
            final_dict["addressLine1"] = (
                splitted_name_list[1].strip() + " " + final_dict["addressLine1"].strip()
            )
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for PPS Australia)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" not in final_dict.keys()
    ):
        if (
            "Savnil Chand".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 10
        ):
            splitted_name_list = final_dict["name"].split("Chand")
            final_dict["name"] = splitted_name_list[0].strip() + " Chand"
            final_dict["addressLine2"] = final_dict["addressLine1"]
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for PHOENIX CONTACT)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" not in final_dict.keys()
    ):
        if (
            'TOO "COMPANY ECOS" CONTRACT'.lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 4
        ):
            splitted_name_list = final_dict["name"].split("CONTRACT")
            final_dict["name"] = splitted_name_list[0].strip()
            final_dict["addressLine2"] = final_dict["addressLine1"]
            final_dict["addressLine1"] = "CONTRACT " + splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for Husqvarna)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "husqvarna".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 8
        ):
            if "LTD." in final_dict["name"]:
                splitted_name_list = final_dict["name"].split("LTD.")
                if "addressLine2" not in final_dict.keys():
                    final_dict["name"] = splitted_name_list[0].strip() + " LTD."
                    final_dict["addressLine2"] = final_dict["addressLine1"]
                    final_dict["addressLine1"] = splitted_name_list[1].strip()
                else:
                    final_dict["name"] = splitted_name_list[0].strip() + " LTD."
                    final_dict["addressLine2"] = (
                        final_dict["addressLine1"].strip()
                        + " "
                        + final_dict["addressLine2"]
                    )
                    final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for PALL FILTERSYSTEMS)
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" not in final_dict.keys()
    ):
        if (
            "Pall Australia Pty".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 5
        ):
            if "Ltd" in final_dict["name"]:
                splitted_name_list = final_dict["name"].split("Ltd")
                final_dict["name"] = splitted_name_list[0].strip() + " Ltd"
                final_dict["addressLine2"] = final_dict["addressLine1"]
                final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 in there's no AD1 (exceptional case for 3M PERU SA)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "3M PERU SA".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 9
        ):
            splitted_name_list = final_dict["name"].split("SA")
            final_dict["name"] = splitted_name_list[0].strip() + " SA"
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 in there's no AD1 (exceptional case for BAUER)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "BAUER Equipment America, Inc.".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 7
        ):
            splitted_name_list = final_dict["name"].split("Inc.")
            final_dict["name"] = splitted_name_list[0].strip() + " Inc."
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 in there's no AD1 (exceptional case for CARL ZEISS MEDITEC)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "Megalabs-Pharma S.A.".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 6
        ):
            splitted_name_list = final_dict["name"].split("S.A.")
            final_dict["name"] = splitted_name_list[0].strip() + " S.A."
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into AD1 in there's no AD1 (exceptional case for BAUER MASCHINEN)
    if "name" in final_dict.keys() and "addressLine1" not in final_dict.keys():
        if (
            "BAUER Equipment America, Inc".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 7
        ):
            splitted_name_list = final_dict["name"].split("Inc")
            final_dict["name"] = splitted_name_list[0].strip() + " Inc"
            final_dict["addressLine1"] = splitted_name_list[1].strip()
    # shortening 'name' field if it's too long, splitting it into Attn (exceptional case for PACOVIS)
    if "name" in final_dict.keys() and "Attn" not in final_dict.keys():
        if (
            "Connie".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 5
        ):
            splitted_name_list = final_dict["name"].split("Connie")
            final_dict["name"] = splitted_name_list[0].strip()
            final_dict["Attn"] = "Connie " + splitted_name_list[1].strip()
        elif (
            "Cooper".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 4
        ):
            splitted_name_list = final_dict["name"].split("Cooper")
            final_dict["name"] = splitted_name_list[0].strip()
            final_dict["Attn"] = "Cooper " + splitted_name_list[1].strip()

    # adding AD1 having "C/O" to name
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if "c/o" in final_dict["addressLine1"].lower():
            final_dict["addressLine1"] = final_dict["addressLine1"].strip()
            if final_dict["addressLine1"].lower().startswith("c/o"):
                final_dict["name"] = (
                    final_dict["name"].strip() + " " + final_dict["addressLine1"]
                )
                final_dict["addressLine1"] = final_dict["addressLine2"]
                final_dict.pop("addressLine2")
        if final_dict["name"].lower().endswith("c/o"):
            final_dict["name"] = (
                final_dict["name"].strip() + " " + final_dict["addressLine1"]
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
        if final_dict["addressLine1"].lower().startswith("do"):
            final_dict["name"] = (
                final_dict["name"].strip()
                + " c/o "
                + final_dict["addressLine1"].replace("do", "").strip()
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
        if final_dict["addressLine1"].lower().startswith("• do"):
            final_dict["name"] = (
                final_dict["name"].strip()
                + " c/o "
                + final_dict["addressLine1"].replace("• do", "").strip()
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # keeping it after c/o as this is the only profile where we need to ignore c/o
    # shortening 'name' field if it's too long, splitting it into AD1 (and AD2 = AD1) (exceptional case for Siemens)
    if "name" in final_dict.keys() and "addressLine1" in final_dict.keys():
        if (
            "SIEMENS".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) > 3
        ):
            name_list = final_dict["name"].strip().split(" ")
            if "" in name_list:
                name_list.remove("")
            final_dict["name"] = " ".join(address_text.split(" ")[0 : len(name_list)])
            if " cl- " in final_dict["name"].lower():
                final_dict["name"] = (
                    final_dict["name"].lower().replace(" cl- ", " c/o ")
                )
            if " cio " in final_dict["name"].lower():
                final_dict["name"] = (
                    final_dict["name"].lower().replace(" cio ", " c/o ")
                )
            if " re " in final_dict["name"].lower():
                final_dict["name"] = final_dict["name"].lower().replace(" re ", " pte ")
            if "," in final_dict["name"]:
                name = final_dict["name"]
                last_index = name.index(",")
                final_dict["name"] = name[0:last_index]
                if "addressLine2" not in final_dict.keys():
                    final_dict["addressLine2"] = final_dict["addressLine1"]
                else:
                    final_dict["addressLine2"] = (
                        final_dict["addressLine1"].strip()
                        + " "
                        + final_dict["addressLine2"]
                    )
                final_dict["addressLine1"] = name[last_index + 1 :].strip()
        elif (
            "SIEMENS".lower() in final_dict["name"].lower()
            and len(final_dict["name"].split(" ")) <= 3
        ):
            final_dict["addressLine1"] = final_dict["addressLine1"].strip()
            if "cl-" in final_dict["addressLine1"].lower():
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].lower().replace("cl-", "c/o")
                )
            if "c/-" in final_dict["addressLine1"].lower():
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].lower().replace("cl-", "c/o")
                )

    # Fixing name by taking AD1 into name as c/o is missing due to OCR issues
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
        and "city" in final_dict.keys()
    ):
        if (
            "BOEHRINGER INGELHEIM LTDA".lower() in final_dict["name"].lower()
            and "NOVOFARMA SERVICE S. A.".lower() in final_dict["addressLine1"].lower()
        ):
            final_dict["name"] = (
                final_dict["name"].strip() + " C/O " + final_dict["addressLine1"]
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict["addressLine2"] = "comuna quilicura"
            final_dict["city"] = "santiago"
    # Fixing name by taking AD1 into name
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
        and "postcode" in final_dict.keys()
    ):
        if (
            "Boehringer Ingelheim Animal".lower() in final_dict["name"].lower()
            and "Health Canada Inc.".lower() in final_dict["addressLine1"].lower()
        ):
            final_dict["name"] = (
                final_dict["name"].strip() + " " + final_dict["addressLine1"]
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
            final_dict.pop("postcode")
    # Fixing name by taking AD1 into name
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            "Boehringer Ingelheim".lower() in final_dict["name"].lower()
            and "Peru S.A.C.".lower() in final_dict["addressLine1"].lower()
        ):
            final_dict["name"] = (
                final_dict["name"].strip() + " " + final_dict["addressLine1"]
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]

    # Fixing name (cleaning name)
    if "name" in final_dict.keys():
        if "Changzhou SynTheAll".lower() in final_dict["name"].lower():
            splitted_name_list = final_dict["name"].split("Changzhou")
            final_dict["name"] = "Changzhou " + splitted_name_list[1].strip()

    # removing caption names using startswith_remove_list
    if "name" in final_dict.keys():
        for i in startswith_remove_list:
            if final_dict["name"].lower().startswith(i):
                final_dict["name"] = final_dict["name"].lower().replace(i, "")
    if "addressLine1" in final_dict.keys():
        for i in startswith_remove_list:
            if final_dict["addressLine1"].lower().startswith(i):
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].lower().replace(i, "")
                )
    if "addressLine2" in final_dict.keys():
        for i in startswith_remove_list:
            if final_dict["addressLine2"].lower().startswith(i):
                final_dict["addressLine2"] = (
                    final_dict["addressLine2"].lower().replace(i, "")
                )

    # setting postal code from addressLine2 if not found earlier
    if "postcode" not in final_dict.keys():
        if (
            "addressLine2" in final_dict.keys()
            and "POSTAL CODE" in final_dict["addressLine2"]
        ):
            address_line2_list = final_dict["addressLine2"].split(" ")
            if address_line2_list.index("POSTAL") + 1 == address_line2_list.index(
                "CODE"
            ):
                index_of_postal_code = address_line2_list.index("CODE") + 1
                if address_line2_list[index_of_postal_code].isnumeric():
                    final_dict["postcode"] = address_line2_list[index_of_postal_code]
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        final_dict["postcode"], ""
                    )
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        "POSTAL CODE", ""
                    )
                    if final_dict["addressLine2"][-3] == ",":
                        final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                            ",", ""
                        )

    # removing country from addressLine2
    if (
        "addressLine2" in final_dict.keys()
        and "country" in final_dict.keys()
        and final_dict["country"].upper() in final_dict["addressLine2"]
    ):
        final_dict["addressLine2"] = final_dict["addressLine2"].replace(
            final_dict["country"].upper(), ""
        )

    # removing final_dict["country"] if it is not alphabetical only
    if "country" in final_dict.keys():
        country_string = final_dict["country"]
        if " " in final_dict["country"]:
            country_string = country_string.replace(" ", "")
        if country_string.isalpha() == False:
            final_dict.pop("country")

    # removing state if it is numeric
    if "state" in final_dict.keys():
        state_string = final_dict["state"]
        if "-" in final_dict["state"]:
            state_string = state_string.replace("-", "")
        if state_string.isnumeric():
            final_dict.pop("state")

    # removing country/part of country name from 'city' key and setting addressLine2 as city if it has only one word
    if (
        "city" in final_dict.keys()
        and "country" in final_dict.keys()
        and final_dict["city"] in final_dict["country"]
    ):
        if (
            "addressLine2" in final_dict.keys()
            and len(final_dict["addressLine2"].split(" ")) == 1
        ):
            final_dict["city"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # removing city key from final dict if final_dict["city"] = 'city'
    if "city" in final_dict.keys():
        if final_dict["city"].lower() == "city".lower():
            final_dict.pop("city")

    # removing whole AD1 if it is in remove_word_list and setting AD2 as AD1
    if "addressLine1" in final_dict.keys() and "addressLine2" in final_dict.keys():
        if final_dict["addressLine1"] in remove_word_list:
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # removing words of remove_word_list from AD2
    if "addressLine2" in final_dict.keys():
        for i in remove_word_list:
            if i in final_dict["addressLine2"]:
                if final_dict["addressLine2"][
                    final_dict["addressLine2"].index(i) - 1
                ] == " " and (
                    (final_dict["addressLine2"].index(i) + len(i))
                    == len(final_dict["addressLine2"])
                    or (
                        final_dict["addressLine2"][
                            final_dict["addressLine2"].index(i) + len(i)
                        ]
                        == " "
                    )
                ):
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        i, ""
                    )
                    break

    # removing wrongly parsed name from 'name' and setting name = AD1 and AD1 = AD2 (Exception: Warren [name: Hot Runners & Molds, Lux])
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if final_dict["name"] in remove_word_list:
            final_dict["name"] = final_dict["addressLine1"]
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
        if (
            len(final_dict["addressLine1"].strip().split(" ")) > 8
            and "BUILDING" in final_dict["addressLine1"]
        ):
            addressline1_list = final_dict["addressLine1"].strip().split("BUILDING")
            final_dict["addressLine1"] = addressline1_list[0].strip()
            final_dict["addressLine2"] = "building " + addressline1_list[1].strip()

    # removing whole city if it is in remove_word_list
    if "city" in final_dict.keys():
        if final_dict["city"] in remove_word_list:
            final_dict.pop("city")

    # grabbing city from addressLine1 if city is not in final_dict
    if "city" not in final_dict.keys() and "addressLine1" in final_dict.keys():
        address_line1_list = final_dict["addressLine1"].split(" ")
        city_name = ""
        for i in address_line1_list:
            if i in city_exception_list:
                city_name += i + " "
        city_name = city_name.strip()
        if city_name != "" and city_name != "City" and city_name != "Province":
            final_dict["city"] = city_name
            final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                city_name, ""
            )
            # removing extra commma from the end
            try:
                if final_dict["city"][-1] == ",":
                    final_dict["city"] = final_dict["city"][:-1]
                # removing single bracket around single word city
                if len(final_dict["city"].split(" ")) == 1:
                    if final_dict["city"][0] == "(" and final_dict["city"][-1] == ")":
                        final_dict["city"] = final_dict["city"][1:-1]
            except:
                pass

    # grabbing city from addressLine2 if city is not in final_dict
    if "city" not in final_dict.keys() and "addressLine2" in final_dict.keys():
        address_line2_list = final_dict["addressLine2"].split(" ")
        city_name = ""
        for i in address_line2_list:
            try:
                if i[-1] == ",":
                    i = i[:-1]
                if "-" in i:
                    i_list = i.split("-")
                    if i_list[1] in city_exception_list:
                        city_name += i_list[1] + " "
            except:
                pass
            if i in city_exception_list:
                city_name += i + " "
        city_name = city_name.strip()
        if len(city_name.split(" ")) == 2:
            if city_name.split(" ")[0] == city_name.split(" ")[1]:
                city_name = city_name.split(" ")[0]
        if city_name != "":
            final_dict["city"] = city_name
            final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                city_name, ""
            )
            # removing extra commma from the end
            try:
                if final_dict["city"][-1] == ",":
                    final_dict["city"] = final_dict["city"][:-1]
                # removing single bracket around single word city
                if len(final_dict["city"].split(" ")) == 1:
                    if final_dict["city"][0] == "(" and final_dict["city"][-1] == ")":
                        final_dict["city"] = final_dict["city"][1:-1]
            except:
                pass

    # grabbing city from addressLine1 if incorrect city is already there
    if "addressLine1" in final_dict.keys():
        city_already_modified_in_addressline1 = False
        address_line1_list = final_dict["addressLine1"].split(" ")
        city_name = ""
        for i in address_line1_list:
            try:
                if i[-1] == ",":
                    i = i[:-1]
            except:
                pass
            if i in city_exception_list:
                city_name += i + " "
        city_name = city_name.strip()
        if city_name != "" and city_name != "City" and city_name != "Province":
            final_dict["city"] = city_name
            final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                city_name, ""
            )
            city_already_modified_in_addressline1 = True
            if len(final_dict["addressLine1"].strip().split(" ")) == 1:
                if address_line1_list[0] in final_dict.values():
                    final_dict.pop("addressLine1")
            # removing extra commma from the end
            try:
                if final_dict["city"][-1] == ",":
                    final_dict["city"] = final_dict["city"][:-1]
                # removing single bracket around single word city
                if len(final_dict["city"].split(" ")) == 1:
                    if final_dict["city"][0] == "(" and final_dict["city"][-1] == ")":
                        final_dict["city"] = final_dict["city"][1:-1]
            except:
                pass

    # grabbing city from addressLine2 if incorrect city is already there
    if "addressLine2" in final_dict.keys():
        if city_already_modified_in_addressline1 == False:
            address_line2_list = final_dict["addressLine2"].split(" ")
            city_name = ""
            for i in address_line2_list:
                try:
                    # if i[-1] == ",":
                    #     i = i[:-1]
                    if i[0] != "," and "," in i:
                        i = i[0 : i.index(",")]
                except:
                    pass
                if i in city_exception_list:
                    city_name += i + " "
            city_name = city_name.strip()

            if project.lower() == "freight" and city_name == "SAN":
                pass
            elif city_name != "" and city_name != "City" and city_name != "Province":
                final_dict["city"] = city_name
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    city_name, ""
                )
                if len(final_dict["addressLine2"].strip().split(" ")) == 1:
                    if address_line2_list[0] in final_dict.values():
                        final_dict.pop("addressLine2")
                # removing extra commma from the end
                try:
                    if final_dict["city"][-1] == ",":
                        final_dict["city"] = final_dict["city"][:-1]
                    # removing single bracket around single word city
                    if len(final_dict["city"].split(" ")) == 1:
                        if (
                            final_dict["city"][0] == "("
                            and final_dict["city"][-1] == ")"
                        ):
                            final_dict["city"] = final_dict["city"][1:-1]
                except:
                    pass

    # grabbing postcode from city if postcode is not in final_dict
    if "postcode" not in final_dict.keys() and "city" in final_dict.keys():
        city_list = final_dict["city"].split(" ")
        for i in city_list:
            if i in postcode_exception_list:
                final_dict["postcode"] = i
                final_dict["city"] = final_dict["city"].replace(i, "")

    # grabbing postcode from addressLine1 if postcode is not in final_dict
    if "postcode" not in final_dict.keys() and "addressLine1" in final_dict.keys():
        for i in postcode_exception_list:
            if i in final_dict["addressLine1"]:
                final_dict["postcode"] = i
                final_dict["addressLine1"] = final_dict["addressLine1"].replace(i, "")
                break
    # grabbing postcode from addressLine2 if postcode is not in final_dict
    if "postcode" not in final_dict.keys() and "addressLine2" in final_dict.keys():
        for i in postcode_exception_list:
            if i in final_dict["addressLine2"]:
                final_dict["postcode"] = i
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
                break

    # grabbing postcode from addressLine1 if wrong postcode is already there in final_dict
    if "postcode" in final_dict.keys() and "addressLine1" in final_dict.keys():
        for i in postcode_exception_list:
            if i in final_dict["addressLine1"]:
                final_dict["postcode"] = i
                final_dict["addressLine1"] = final_dict["addressLine1"].replace(i, "")
                break
    # grabbing postcode from addressLine2 if wrong postcode is already there in final_dict
    if "postcode" in final_dict.keys() and "addressLine2" in final_dict.keys():
        for i in postcode_exception_list:
            if i in final_dict["addressLine2"]:
                final_dict["postcode"] = i
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
                break

    # grabbing country from addressLine1 if country is not in final_dict
    if "country" not in final_dict.keys() and "addressLine1" in final_dict.keys():
        for i in country_exception_list:
            if i in final_dict["addressLine1"].lower():
                if i == "us":
                    idx = final_dict["addressLine1"].lower().index("us")
                    if (
                        len(final_dict["addressLine1"]) >= 4
                        and idx != 0
                        and (idx + 2 != len(final_dict["addressLine1"]))
                        and final_dict["addressLine1"][idx - 1] != " "
                        and final_dict["addressLine1"][idx + 2] != " "
                    ):
                        continue
                final_dict["country"] = i
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].lower().replace(i, "")
                )
                break

    # grabbing country from addressLine2 if country is not in final_dict
    if "country" not in final_dict.keys() and "addressLine2" in final_dict.keys():
        for i in country_exception_list:
            if i in final_dict["addressLine2"].lower():
                if i == "us":
                    idx = final_dict["addressLine2"].lower().index("us")
                    if (
                        len(final_dict["addressLine2"]) >= 4
                        and idx != 0
                        and (idx + 2 != len(final_dict["addressLine2"]))
                        and final_dict["addressLine2"][idx - 1] != " "
                        and final_dict["addressLine2"][idx + 2] != " "
                    ):
                        continue
                final_dict["country"] = i
                final_dict["addressLine2"] = (
                    final_dict["addressLine2"].lower().replace(i, "")
                )
                break
        # poping addressline2 from final_dict if it is empty
        addressLine_2_list = final_dict["addressLine2"].strip().split(" ")
        for i in addressLine_2_list:
            if i in final_dict.values():
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
        final_dict["addressLine2"] = final_dict["addressLine2"].strip()
        if len(final_dict["addressLine2"]) == 0:
            final_dict.pop("addressLine2")

    # grabbing country from city if country is not in final_dict
    if "country" not in final_dict.keys() and "city" in final_dict.keys():
        for i in country_exception_list:
            if i in final_dict["city"].lower():
                final_dict["country"] = i
                if i != "singapore":
                    final_dict["city"] = final_dict["city"].lower().replace(i, "")
                break

    # grabbing state from addressLine1 if state is not in final_dict
    if "state" not in final_dict.keys() and "addressLine1" in final_dict.keys():
        for i in state_exception_list:
            if i in final_dict["addressLine1"].lower():
                final_dict["state"] = i
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].lower().replace(i, "")
                )
                break

    # grabbing state from addressLine2 if state is not in final_dict
    if "state" not in final_dict.keys() and "addressLine2" in final_dict.keys():
        for i in state_exception_list:
            if i in final_dict["addressLine2"].lower():
                final_dict["state"] = i
                final_dict["addressLine2"] = (
                    final_dict["addressLine2"].lower().replace(i, "")
                )
                break

    # adding city = "Seoul" if state = "Gyeonggi-Do"
    if "state" in final_dict.keys():
        final_dict["state"] = final_dict["state"].strip()
        if final_dict["state"].lower() == "gyeonggi-do":
            final_dict["city"] = "Seoul"
        elif final_dict["state"].lower() == "gyeonggi-00":
            final_dict["state"] = "Gyeonggi-Do"
            final_dict["city"] = "Seoul"

    # grabbing the last part of AD1 from AD2 searching from AD1_exception_list
    if "addressLine1" in final_dict.keys() and "addressLine2" in final_dict.keys():
        for i in AD1_exception_list:
            if i in final_dict["addressLine2"].lower():
                final_dict["addressLine1"] = (
                    final_dict["addressLine1"].strip() + " " + i
                )
                final_dict["addressLine2"] = (
                    final_dict["addressLine2"].lower().replace(i, "")
                )
                break

    # grabbing company name from AD1 if wrongly detected
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        if (
            final_dict["addressLine1"] in company_exception_list
            and "PRIVATE LIMITED".lower() in final_dict["name"].lower()
        ):
            final_dict["name"] = final_dict["addressLine1"].strip() + " Private Limited"
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
        elif (
            final_dict["addressLine1"] in company_exception_list
            and "Daikin Isitma ye Sogutma".lower() in final_dict["name"].lower()
        ):
            final_dict["name"] = (
                final_dict["name"].strip() + " " + final_dict["addressLine1"].strip()
            )
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")
        elif final_dict["addressLine1"] in company_exception_list:
            final_dict["name"] = final_dict["addressLine1"]
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # grabbing company name from AD2 if wrongly detected
    if (
        "name" in final_dict.keys()
        and "addressLine1" in final_dict.keys()
        and "addressLine2" in final_dict.keys()
    ):
        for i in company_exception_list:
            if i in final_dict["addressLine2"]:
                final_dict["name"] = i
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
                final_dict["addressLine1"] = final_dict["addressLine2"]
                final_dict.pop("addressLine2")
                break

    # grabbing company name from parser_dict['house'] if wrongly detected
    if (
        "name" in final_dict.keys()
        and len(final_dict["name"].strip().split(" ")) == 1
        and "house" in parser_dict.keys()
    ):
        if parser_dict["house"] in company_exception_list:
            final_dict["name"] = parser_dict["house"]

    # grabbing email from addressLine2
    if "addressLine2" in final_dict.keys() and "contactEmail" not in final_dict.keys():
        addressLine_2_list = final_dict["addressLine2"].strip().split(" ")
        for i in addressLine_2_list:
            if "@" in i:
                final_dict["contactEmail"] = i
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
                break

    # taking one name from duplicate names
    if "name" in final_dict.keys():
        name_list = final_dict["name"].split(" ")
        first_part = name_list[0 : len(name_list) // 2]
        second_part = name_list[len(name_list) // 2 :]
        if first_part == second_part:
            first_part_string = ""
            for i in first_part:
                first_part_string += i + " "
            first_part_string.strip()
            final_dict["name"] = first_part_string

    # removing already parsed or excess words from Address_Line_1
    if "addressLine1" in final_dict.keys():
        should_remove = True
        for i in ignore_removal_list:
            if i in final_dict["addressLine1"].lower():
                should_remove = False
                break
        if should_remove == True:
            if "—" in final_dict["addressLine1"]:
                final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                    "—", "-"
                )
            addressLine_1_list = final_dict["addressLine1"].strip().split(" ")
            for i in addressLine_1_list:
                try:
                    if i[-1] == ",":
                        i = i[:-1]
                except:
                    pass
                if i in remove_word_list:
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        i, ""
                    )
                elif (
                    "country" in final_dict.keys()
                    and i.lower() in final_dict["country"].lower()
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        i, ""
                    )
                elif (
                    "state" in final_dict.keys()
                    and i.lower() in final_dict["state"].lower()
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        i, ""
                    )
                elif "city" in final_dict.keys():
                    if (
                        len(final_dict["city"].split(" ")) > 1
                        and i.lower() in final_dict["city"].lower()
                        and len(i) > 1
                    ) or (
                        len(final_dict["city"].split(" ")) == 1
                        and final_dict["city"].lower() in i.lower()
                    ):
                        final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                            i, ""
                        )
                elif (
                    "postcode" in final_dict.keys()
                    and i in final_dict["postcode"]
                    and len(i) > 2
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        i, ""
                    )
            # removing extra commmas and spaces from addressLine1 and poping addressline1 from final_dict if it is empty
            for i in range(len(final_dict["addressLine1"]) - 1, -1, -1):
                if (
                    final_dict["addressLine1"][i] == " "
                    or final_dict["addressLine1"][i] == ","
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"][:-1]
                else:
                    break
            if len(final_dict["addressLine1"]) == 0:
                final_dict.pop("addressLine1")

    # removing already parsed or excess words from Address_Line_2
    if "addressLine2" in final_dict.keys():
        if "—" in final_dict["addressLine2"]:
            final_dict["addressLine2"] = final_dict["addressLine2"].replace("—", "-")
        addressLine_2_list = final_dict["addressLine2"].strip().split(" ")
        for i in addressLine_2_list:
            try:
                if i[-1] == ",":
                    i = i[:-1]
            except:
                pass
            if i in remove_word_list:
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
            elif "www" in i.lower():
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
            elif (
                "country" in final_dict.keys()
                and i.lower() in final_dict["country"].lower()
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
            elif (
                "state" in final_dict.keys()
                and i.lower() in final_dict["state"].lower()
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
            elif (
                "city" in final_dict.keys()
                and i.lower() in final_dict["city"].lower()
                and len(i) > 1
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
            elif "postcode" in final_dict.keys() and final_dict["postcode"] in i:
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(i, "")
        for i in range(len(final_dict["addressLine2"]) - 1, -1, -1):
            if (
                final_dict["addressLine2"][i] == " "
                or final_dict["addressLine2"][i] == ","
                or final_dict["addressLine2"][i] == "-"
                or final_dict["addressLine2"][i] == "."
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"][:-1]
            else:
                break
        if len(final_dict["addressLine2"]) == 0:
            final_dict.pop("addressLine2")

    # print("15. checking final dict:", final_dict)
    # grabbing telephone number from addressLine2
    if "contactPhone" not in final_dict.keys():
        if (
            "addressLine2" in final_dict.keys()
            and "contactPhone" not in final_dict.keys()
        ):
            address_line2_list = final_dict["addressLine2"].strip().split(" ")
            tel_number = ""
            for i in range(len(address_line2_list)):
                if "+" in address_line2_list[i]:
                    tel_number += address_line2_list[i] + " "
                    tel_probable_list = address_line2_list[i + 1 :]
                    for j in tel_probable_list:
                        if j.isnumeric() or j == "(0)":
                            tel_number += j + " "
                        else:
                            break
                    break
                elif "Ph." in final_dict["addressLine2"]:
                    tel_number = final_dict["addressLine2"].strip().split("Ph.")[1]
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        "Ph.", ""
                    )
                    break
                elif "ph." in final_dict["addressLine2"]:
                    tel_number = final_dict["addressLine2"].strip().split("ph.")[1]
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        "ph.", ""
                    )
                    break
                elif "Phone" in final_dict["addressLine2"]:
                    tel_number = final_dict["addressLine2"].strip().split("Phone")[1]
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        "Phone", ""
                    )
                    break
            final_dict["contactPhone"] = tel_number.strip()
            final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                final_dict["contactPhone"], ""
            )
            if final_dict["contactPhone"] == "":
                final_dict.pop("contactPhone")
        # grabbing attention from contactPhone
        if "contactPhone" in final_dict.keys() and "Att." in final_dict["contactPhone"]:
            contactPhone_attn_list = final_dict["contactPhone"].strip().split("Att.")
            final_dict["Attn"] = contactPhone_attn_list[1].strip()
            final_dict["contactPhone"] = final_dict["contactPhone"].replace(
                final_dict["Attn"], ""
            )
            final_dict["contactPhone"] = final_dict["contactPhone"].replace("Att.", "")

    # grabbing telephone number from addressLine1
    if "contactPhone" not in final_dict.keys():
        if (
            "addressLine1" in final_dict.keys()
            and "contactPhone" not in final_dict.keys()
        ):
            address_line1_list = final_dict["addressLine1"].strip().split(" ")
            tel_number = ""
            for i in range(len(address_line1_list)):
                if "+" in address_line1_list[i]:
                    tel_number += address_line1_list[i] + " "
                    tel_probable_list = address_line1_list[i + 1 :]
                    for j in tel_probable_list:
                        if j.isnumeric() or j == "(0)":
                            tel_number += j + " "
                        else:
                            break
                    break
                elif (
                    "PH" in final_dict["addressLine1"]
                    and "oph" not in final_dict["addressLine1"].lower()
                ):
                    tel_number = final_dict["addressLine1"].strip().split("PH")[1]
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        "PH", ""
                    )
                    break
                elif "ph" in final_dict["addressLine1"]:
                    tel_number = final_dict["addressLine1"].strip().split("ph")[1]
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        "ph", ""
                    )
                    break
            final_dict["contactPhone"] = tel_number.strip()
            final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                final_dict["contactPhone"], ""
            )
            if final_dict["contactPhone"] == "":
                final_dict.pop("contactPhone")
        if (
            "house_number" in parser_dict.keys()
            and "contactPhone" not in final_dict.keys()
        ):
            if (
                parser_dict["house_number"].isnumeric()
                and len(parser_dict["house_number"]) == 12
            ):
                final_dict["contactPhone"] = parser_dict["house_number"]
                if final_dict["contactPhone"] in final_dict["addressLine2"]:
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        final_dict["contactPhone"], ""
                    )

    # removing contactPhone from final_dict if it is non_numeric (all the letters are alphabetic)
    if "contactPhone" in final_dict.keys():
        phone_number = final_dict["contactPhone"]
        if " " in phone_number:
            phone_number = phone_number.replace(" ", "")
        if "." in phone_number:
            phone_number = phone_number.replace(".", "")
        if phone_number.isalpha():
            final_dict.pop("contactPhone")

    # removing fax from contactPhone if it is in remove_fax_list
    if "contactPhone" in final_dict.keys():
        for i in remove_fax_list:
            if i in final_dict["contactPhone"]:
                final_dict["contactPhone"] = final_dict["contactPhone"].replace(i, "")
                break

    # removing city from final_dict if it is numeric
    if "city" in final_dict.keys():
        city_name = final_dict["city"]
        if " " in city_name:
            city_name = city_name.replace(" ", "")
        if "(" in city_name:
            city_name = city_name.replace("(", "")
        if ")" in city_name:
            city_name = city_name.replace(")", "")
        if "-" in city_name:
            city_name = city_name.replace("-", "")
        if city_name.isnumeric():
            final_dict.pop("city")

    # setting Attention if "Attn" in key_val_dict
    if "Attn" in key_val_dict.keys() and "Attn" not in final_dict.keys():
        final_dict["Attn"] = key_val_dict["Attn"]

    # grabbing attention from addressline2 if not found in key_val_dict and also not in final_dict
    if "Attn" not in key_val_dict.keys() and "Attn" not in final_dict.keys():
        if "addressLine2" in final_dict.keys():
            if "attention" in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("attention")
                )
                final_dict["Attn"] = address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    "attention", ""
                )
            elif "Attention" in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("Attention")
                )
                final_dict["Attn"] = address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    "Attention", ""
                )
            elif "attenti" in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("attenti")
                )
                final_dict["Attn"] = address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    "attenti", ""
                )
            elif "mr." in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("mr.")
                )
                final_dict["Attn"] = "mr. " + address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
            elif "Mr." in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("Mr.")
                )
                final_dict["Attn"] = "Mr. " + address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
            elif "ms." in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("ms.")
                )
                final_dict["Attn"] = "ms. " + address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
            elif "Ms." in final_dict["addressLine2"]:
                address_line2_attn_list = (
                    final_dict["addressLine2"].strip().split("Ms.")
                )
                final_dict["Attn"] = "Ms. " + address_line2_attn_list[1].strip()
                final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                    final_dict["Attn"], ""
                )
        # grabbing cell number from Attn
        if "Attn" in final_dict.keys() and "cell." in final_dict["Attn"]:
            final_dict["cell"] = final_dict["Attn"].strip().split("cell.")[1].strip()
            final_dict["Attn"] = final_dict["Attn"].replace("cell.", "")
            final_dict["Attn"] = final_dict["Attn"].replace(final_dict["cell"], "")

    # grabbing attention from addressline1 if not found in key_val_dict and also not in final_dict
    if "Attn" not in key_val_dict.keys() and "Attn" not in final_dict.keys():
        if "addressLine1" in final_dict.keys():
            if (
                "att" in final_dict["addressLine1"]
                and "attenstrasse" not in final_dict["addressLine1"]
            ):
                address_line1_attn_list = (
                    final_dict["addressLine1"].strip().split("att")
                )
                final_dict["Attn"] = address_line1_attn_list[1].strip()
                final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                    final_dict["Attn"], ""
                )
                final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                    "att", ""
                )

    # grabbing postal code from addressLine2 if AD2 is numeric only and adding it to previous postcode
    if "postcode" in final_dict.keys() and len(final_dict["postcode"]) <= 3:
        if (
            "addressLine2" in final_dict.keys()
            and len(final_dict["addressLine2"].strip().split(" ")) == 1
        ):
            try:
                final_dict["addressLine2"] = final_dict["addressLine2"].strip()
                if final_dict["addressLine2"][-1] == ",":
                    final_dict["addressLine2"] = final_dict["addressLine2"][:-1]
            except:
                pass
            if (
                final_dict["addressLine2"].isnumeric()
                and len(final_dict["addressLine2"]) <= 5
            ):
                final_dict["postcode"] = (
                    final_dict["addressLine2"] + " " + final_dict["postcode"]
                )
                final_dict.pop("addressLine2")
            elif (
                final_dict["addressLine2"].isnumeric()
                and len(final_dict["addressLine2"]) <= 6
            ):
                final_dict["postcode"] = final_dict["addressLine2"]
                final_dict.pop("addressLine2")

    # swapping AD1 and AD2 if addressline1 is empty
    if "addressLine1" in final_dict.keys() and "addressLine2" in final_dict.keys():
        if final_dict["addressLine1"].strip() == "":
            final_dict["addressLine1"] = final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # adding addressline2 at the end of AD1 if addressline2 contains digits only
    if "addressLine1" in final_dict.keys() and "addressLine2" in final_dict.keys():
        final_dict["addressLine2"] = final_dict["addressLine2"].strip()
        if (
            len(final_dict["addressLine2"].split(" ")) == 1
            and final_dict["addressLine2"].isnumeric()
        ):
            final_dict["addressLine1"] += " " + final_dict["addressLine2"]
            final_dict.pop("addressLine2")

    # distributing addressLine1 to AD2 if AD2 not in final_dict and len(AD1) > 50
    if "addressLine1" in final_dict.keys() and "addressLine2" not in final_dict.keys():
        if len(final_dict["addressLine1"]) > 50:
            if "south zone jebel" in final_dict["addressLine1"].lower():
                splitted_address_list = (
                    final_dict["addressLine1"].lower().split("south zone")
                )
                final_dict["addressLine1"] = splitted_address_list[0].strip()
                final_dict["addressLine2"] = "South Zone Jebel ALI Free Zone"

    # taking 50 characters of addressline1
    if "addressLine1" in final_dict.keys():
        if len(final_dict["addressLine1"]) > 50:
            if final_dict["addressLine1"][50] == " ":
                final_dict["addressLine1"] = final_dict["addressLine1"][0:50]
            else:
                final_dict["addressLine1"] = final_dict["addressLine1"][0:50]
                for i in range(len(final_dict["addressLine1"]) - 1, -1, -1):
                    if final_dict["addressLine1"][i] != " ":
                        final_dict["addressLine1"] = final_dict["addressLine1"][:-1]
                    else:
                        break
            final_dict["addressLine1"] = final_dict["addressLine1"].strip()

    # taking 50 characters of addressline2
    if "addressLine2" in final_dict.keys():
        if len(final_dict["addressLine2"]) > 50:
            if final_dict["addressLine2"][50] == " ":
                final_dict["addressLine2"] = final_dict["addressLine2"][0:50]
            else:
                final_dict["addressLine2"] = final_dict["addressLine2"][0:50]
                for i in range(len(final_dict["addressLine2"]) - 1, -1, -1):
                    if final_dict["addressLine2"][i] != " ":
                        final_dict["addressLine2"] = final_dict["addressLine2"][:-1]
                    else:
                        break
            final_dict["addressLine2"] = final_dict["addressLine2"].strip()
    try:
        # removing comma from Address_Line_1
        if "addressLine1" in final_dict.keys():
            # from backwards
            for i in range(len(final_dict["addressLine1"]) - 1, -1, -1):
                if (
                    final_dict["addressLine1"][i] == " "
                    or final_dict["addressLine1"][i] == ","
                    or final_dict["addressLine1"][i] == "-"
                    or final_dict["addressLine1"][i] == "."
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"][:-1]
                else:
                    break
            # from the front
            for i in range(len(final_dict["addressLine1"])):
                if (
                    final_dict["addressLine1"][i] == " "
                    or final_dict["addressLine1"][i] == ","
                    or final_dict["addressLine1"][i] == "-"
                    or final_dict["addressLine1"][i] == "."
                ):
                    final_dict["addressLine1"] = final_dict["addressLine1"][i + 1 :]
                else:
                    break
            if len(final_dict["addressLine1"]) == 0:
                final_dict.pop("addressLine1")
    except:
        pass

    # removing comma from Address_Line_2
    if "addressLine2" in final_dict.keys():
        # from backwards
        for i in range(len(final_dict["addressLine2"]) - 1, -1, -1):
            if (
                final_dict["addressLine2"][i] == " "
                or final_dict["addressLine2"][i] == ","
                or final_dict["addressLine2"][i] == "-"
                or final_dict["addressLine2"][i] == "."
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"][:-1]
            else:
                break
        # from the front
        for i in range(len(final_dict["addressLine2"])):
            if (
                final_dict["addressLine2"][i] == " "
                or final_dict["addressLine2"][i] == ","
                or final_dict["addressLine2"][i] == "-"
                or final_dict["addressLine2"][i] == "."
            ):
                final_dict["addressLine2"] = final_dict["addressLine2"][i + 1 :]
            else:
                break
        if len(final_dict["addressLine2"]) == 0:
            final_dict.pop("addressLine2")

    # changing country to countryCode if length is two
    if "country" in final_dict.keys():
        if "countryCode" in final_dict.keys():
            final_dict.pop("countryCode")
        if len(final_dict["country"]) == 2:
            final_dict["countryCode"] = final_dict["country"]
            final_dict.pop("country")

    # Grabbing Canadian Postcode from AD1 and AD2 (e.g., "V5K 0A9")
    if "country" in final_dict.keys() and "postcode" not in final_dict.keys():
        if final_dict["country"].lower() == "canada":
            canadian_post_code_pattern = r"[A-Z][0-9][A-Z] [0-9][A-Z][0-9]"
            if "addressLine1" in final_dict.keys():
                match = re.search(
                    canadian_post_code_pattern, final_dict["addressLine1"]
                )
                if match:
                    canadian_post_code = match.group()
                    final_dict["postcode"] = canadian_post_code
                    final_dict["addressLine1"] = final_dict["addressLine1"].replace(
                        canadian_post_code, ""
                    )
            elif "addressLine2" in final_dict.keys():
                match = re.search(
                    canadian_post_code_pattern, final_dict["addressLine2"]
                )
                if match:
                    canadian_post_code = match.group()
                    final_dict["postcode"] = canadian_post_code
                    final_dict["addressLine2"] = final_dict["addressLine2"].replace(
                        canadian_post_code, ""
                    )

    # breakpoint 2
    # print("13. checking final dict:", final_dict)

    # replacing company name with proper name @fahim(15.08.2022)
    if "name" in final_dict.keys():
        for i in replace_company_name:
            if "Husky".lower() in i["original_value"].lower():
                if i["original_value"].lower() == final_dict["name"].lower():
                    final_dict["name"] = final_dict["name"].replace(
                        i["original_value"], i["translate_value"]
                    )
                    final_dict["addressLine1"] = (
                        "Machi " + final_dict["addressLine1"].strip()
                    )
            elif i["original_value"].lower() in final_dict["name"].lower():
                final_dict["name"] = final_dict["name"].replace(
                    i["original_value"], i["translate_value"]
                )

    # replacing city name with proper name @fahim(24.02.2023)
    if "city" in final_dict.keys():
        for i in replace_city_name:
            if i["original_value"].lower() in final_dict["city"].lower():
                final_dict["city"] = final_dict["city"].replace(
                    i["original_value"], i["translate_value"]
                )

    # removing comma or other extra character from contactPhone @fahim(30.08.2022)
    if "contactPhone" in final_dict.keys():
        for i in range(len(final_dict["contactPhone"]) - 1, -1, -1):
            if (
                final_dict["contactPhone"][i] == " "
                or final_dict["contactPhone"][i] == ","
                or final_dict["contactPhone"][i] == "/"
            ):
                final_dict["contactPhone"] = final_dict["contactPhone"][:-1]
            else:
                break
        if len(final_dict["contactPhone"]) == 0:
            final_dict.pop("contactPhone")
    # removing comma or other extra character from Contact @fahim(16.09.2022)
    if "Contact" in final_dict.keys():
        for i in range(len(final_dict["Contact"]) - 1, -1, -1):
            if (
                final_dict["Contact"][i] == " "
                or final_dict["Contact"][i] == ","
                or final_dict["Contact"][i] == "/"
            ):
                final_dict["Contact"] = final_dict["Contact"][:-1]
            else:
                break
        if len(final_dict["Contact"]) == 0:
            final_dict.pop("Contact")

    return final_dict
