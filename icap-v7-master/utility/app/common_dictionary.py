"""
Script that holds some dictionaries and variables used by other scripts.
"""

incoterms_list = [
    "CIF",
    "CIP",
    "CFR",
    "CPT",
    "DAT",
    "DAP",
    "DDP",
    "DDU",
    "EXW",
    "FAS",
    "FCA",
    "FOB",
]
loc_parser_exception_list = {"Kuwait": "KW", "South Africn": "ZA", "Utd.Arab Em": "AE"}


replace_country_name = [
    {"original_value": "Deutschland", "translate_value": "Germany"},
    {"original_value": "Osterreich", "translate_value": "Austria"},
    {"original_value": "Fill", "translate_value": "Fiji"},
    {"original_value": "i ndia", "translate_value": "India"},
    {
        "original_value": "French Polynesia",
        "translate_value": "Tahiti French Polynesia",
    },
    {"original_value": "br-brazil", "translate_value": "Brazil"},
    {"original_value": "sudsouth korea", "translate_value": "South Korea"},
    {"original_value": "peru peru", "translate_value": "Peru"},
    {"original_value": "utd.arab emir", "translate_value": "United Arab Emirates"},
    {
        "original_value": "united arab emiratesates",
        "translate_value": "United Arab Emirates",
    },
    {"original_value": "hongkong hongkong", "translate_value": "hongkong"},
    {"original_value": "mex mexico", "translate_value": "mexico"},
    {"original_value": ", bolnia", "translate_value": "Bolivia"},
]

replace_locationCode = [
    {"original_value": "KM,", "translate_value": "KIX"},
    {"original_value": "IQX", "translate_value": "KIX"},
    {"original_value": "MM,", "translate_value": "MTY"},
    {"original_value": "UM", "translate_value": "LIM"},
    {"original_value": "510", "translate_value": "SJO"},
]


remove_unwanted_values = ["CONTACT TEL", "ACCOUNTS PAYABLE", "CONSIGNEE"]

# suffixes that are missing from cleanco
missing_company_suffixes = ["s.a.s", "limited", "s.r.i", "s.r.L"]

unwanted_chars = ["■"]

MERGE_OUTPUT_TRIGGER_PROFILE_IDS = []
