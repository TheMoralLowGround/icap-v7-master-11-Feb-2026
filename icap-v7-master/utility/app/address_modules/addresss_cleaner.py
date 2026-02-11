import traceback

from fuzzywuzzy import fuzz


# from ..common_dictionary import countryMap
# version - 5.01.20230130
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
                full_address = rows[i].get(label + "_FULL_ADDRESS")
                if not full_address:
                    continue
                match_score = fuzz.ratio(input_block.lower(), full_address.lower())
                if match_score >= ratio_th:
                    score_holder_dict[i] = match_score

                    # COMMENTED BY EMON ON MARCH 14 2023
                    # # checking and converting country code to full country name
                    # if rows[i]['COUNTRY'] and len(rows[i]['COUNTRY']) == 2:
                    #     c = list(countryMap.values())
                    #     country_dict = c[0]
                    #     for key, value in country_dict.items():
                    #         if rows[i]['COUNTRY'].upper() == value['ISO2']:
                    #             rows[i]['COUNTRY'] = key
                    # if rows[i]['COUNTRY'] and rows[i]['COUNTRY'].lower() in input_block.lower():
                    #     score_holder_dict[i] = match_score
                    # elif rows[i]['COUNTRY'] and rows[i]['COUNTRY'].lower() not in input_block.lower():
                    #     country_found = False
                    #     country_value = None
                    #     children = keyNode["children"]
                    #     for d_child in children:
                    #         if d_child['label'] == 'country':
                    #             country_found = True
                    #             country_value= d_child['v']
                    #             break
                    #     if country_found:
                    #         if rows[i]['COUNTRY'].lower() == country_value.lower():
                    #             score_holder_dict[i] = match_score
                    #     else:
                    #         score_holder_dict[i] = match_score
                    # else:
                    #     score_holder_dict[i] = match_score
            except:
                print(traceback.print_exc())
                continue

        if score_holder_dict:
            matched_index = max(score_holder_dict, key=score_holder_dict.get)
            i = matched_index
            updated_key_node = key_node
            updated_key_node["v"] = rows[i][label + "_FULL_ADDRESS"]
            children = updated_key_node["children"]

            # print(children)
            for d_child in children:
                if d_child["label"] == "name" and rows[i].get(label + "_CW1_NAME"):
                    d_child["v"] = rows[i][label + "_CW1_NAME"]
                elif d_child["label"] == "name" and rows[i].get(label + "_NAME"):
                    d_child["v"] = rows[i][label + "_NAME"]
                if d_child["label"] == "addressLine1" and rows[i].get(
                    label + "ADDRESSLINE1"
                ):
                    d_child["v"] = rows[i][label + "ADDRESSLINE1"]
                if d_child["label"] == "addressLine2" and rows[i].get(
                    label + "ADDRESSLINE2"
                ):
                    d_child["v"] = rows[i][label + "ADDRESSLINE2"]
                if d_child["label"] == "city" and rows[i].get(label + "CITY"):
                    d_child["v"] = rows[i].get(label + "CITY")
                if d_child["label"] == "postcode" and rows[i].get(label + "POSTALCODE"):
                    d_child["v"] = rows[i][label + "POSTALCODE"]
                if d_child["label"] == "state" and rows[i].get(label + "STATE"):
                    d_child["v"] = rows[i][label + "STATE"]
                if d_child["label"] == "country" and rows[i].get(label + "COUNTRY"):
                    d_child["v"] = rows[i][label + "COUNTRY"]
                if d_child["label"] == "block" and rows[i].get(label + "_FULL_ADDRESS"):
                    d_child["v"] = rows[i][label + "_FULL_ADDRESS"]

        output_dict = dict()

        if updated_key_node and type(matched_index) == int:
            output_dict["keyNode"] = updated_key_node
            output_dict["matched_index"] = matched_index
            return output_dict
        return None
    except:
        print(traceback.print_exc())
        return None
