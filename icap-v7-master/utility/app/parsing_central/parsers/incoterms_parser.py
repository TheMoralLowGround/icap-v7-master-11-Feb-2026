from posixpath import split

from app.address_modules.address_parser import postal_parse_address
from app.common_dictionary import incoterms_list

# import traceback


def find_incoterms(text, incoterms_list):
    # Lowercase the input text
    text_lower = text.lower()

    # Convert incoterms_list to a set for faster lookup
    incoterms_set = set(incoterms_list)

    # Iterate through incoterms_list and their variants
    for term in incoterms_set:
        # Check if the term or its variant (with dots) exist in the text
        if term.lower() in text_lower or ".".join(term).lower() in text_lower:
            return term

    return None


def process(string):
    # print("1. checking:", string)
    try:
        # Added by emon on 29/08/2022
        if "F CA" in string:
            string = string.replace("F CA", "FCA")
        # Added by Almas on 29/08/2022
        if "FCA" in string:
            split_string = string.split()
            for word in split_string:
                if word == "Graz" or word == "Graz,":
                    string = "FCA Graz, Austria"
        in_co_term_location_removal_list = [
            "Flughafen",
            "Airport",
            "Lieferbedingungen",
            '"',
        ]
        value_text = string.strip()
        in_co_terms = None
        in_co_terms_found = False
        if not in_co_terms_found:
            try:
                in_co_terms = find_incoterms(value_text, incoterms_list)
                if in_co_terms:
                    value_text = value_text.replace(in_co_terms, "")
                    in_co_terms_found = True
            except:
                pass

        postal_result = postal_parse_address(value_text)
        # print("4. checking postal result:", postal_result)
        try:
            # Fix for port identified as a city
            for x, y in postal_result:
                if y == "city" and (x.lower() == "port"):
                    value_text = value_text.lower().replace("port", "")
                    postal_result = postal_parse_address(value_text)
            # print("5. checking postal result try block:", postal_result)
        except:
            pass

        in_co_terms_parsed = dict()
        for x, y in postal_result:
            in_co_terms_parsed[y] = x
        # print("6. checking incoterms parsed:", in_co_terms_parsed)

        in_co_terms_location = None
        # print(in_co_terms_parsed)
        city = None
        # print(in_co_terms_parsed)
        if "city" in in_co_terms_parsed.keys():
            in_co_terms_location = in_co_terms_parsed["city"].title()
        else:
            if "state" in in_co_terms_parsed.keys():
                in_co_terms_location = in_co_terms_parsed["state"].title()
            elif "house" in in_co_terms_parsed.keys():
                if "incoterms" in in_co_terms_parsed["house"]:
                    in_co_terms_parsed["house"] = in_co_terms_parsed["house"].replace(
                        "incoterms", ""
                    )
                if "sea freight shipment" in in_co_terms_parsed["house"]:
                    in_co_terms_parsed["house"] = in_co_terms_parsed["house"].replace(
                        "sea freight shipment", ""
                    )
                if "/" in in_co_terms_parsed["house"]:
                    in_co_terms_parsed["house"] = in_co_terms_parsed["house"].replace(
                        "/", ""
                    )
                in_co_terms_location = in_co_terms_parsed["house"].strip().title()
        # print("7. checking incoterms parsed keys:", in_co_terms_parsed.keys())
        # print("8. checking incoterms parsed dictionary:", in_co_terms_parsed)

        extraData = None

        # removing certain words from incoterms location
        if in_co_terms_location and " " in in_co_terms_location:
            incoterms_location_list = in_co_terms_location.split(" ")
            for i in incoterms_location_list:
                if i in in_co_term_location_removal_list:
                    in_co_terms_location = in_co_terms_location.replace(i, "")

        # grabbing incoterms location from 'country' key or 'suburb' key
        if in_co_terms_location == None and "country" in in_co_terms_parsed.keys():
            in_co_terms_location = in_co_terms_parsed["country"]
        elif in_co_terms_location == None and "suburb" in in_co_terms_parsed.keys():
            in_co_terms_location = in_co_terms_parsed["suburb"]
        elif (
            in_co_terms_location == None
            and "state_district" in in_co_terms_parsed.keys()
        ):
            in_co_terms_location = in_co_terms_parsed["state_district"]

        # print("2. checking incoterms:", in_co_terms)
        # print("3. checking location:", in_co_terms_location)
        if in_co_terms != None and in_co_terms_location == None:
            idx = string.index(in_co_terms) + len(in_co_terms)
            in_co_terms_location = string[idx:].strip()
        if in_co_terms_location and in_co_terms:
            if in_co_terms_location[0] == ",":
                in_co_terms_location = in_co_terms_location[1:]
            return [
                in_co_terms,
                in_co_terms_location.title(),
            ]  # Added by Emon on 19/08/2022- Titlelized location
        else:
            # print("9. checking else part:", string)
            return [in_co_terms]
    except:
        # print(traceback.print_exc())
        return [in_co_terms]
