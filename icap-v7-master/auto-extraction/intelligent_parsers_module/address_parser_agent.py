import copy
from rapidfuzz import fuzz
from generate_llm_result import get_llm_result_address_parser
from format_llm_result import get_formatted_address_data



def get_sub_label_mapping(children, mapped_keys_for_address_block, parent_key, profile_keys):

    #try:

    tmp_pf_dict = {}
    for item in profile_keys:
        tmp_pf_dict[item["keyLabel"]] = item.get("keyValue")

    trace_list = []
    if mapped_keys_for_address_block == []:
        return children

    for idx, item in enumerate(mapped_keys_for_address_block):
        
        for kv in children:
            if kv.get("is_label_mapped"):
                continue
            
            if fuzz.ratio(parent_key.lower().strip(),item["mappedKey"].split("[address]")[0].lower().strip())>=95 and fuzz.ratio(item["mappedKey"].split("[address]")[-1].lower().strip(), kv["original_key_label"].lower().strip()) >= 90:
                
                qualifier_value = item.get("qualifierValue")
                
                if item.get("qualifierValue","") in trace_list or item["keyLabel"] in trace_list:
                    continue
                
                if qualifier_value and qualifier_value.strip():
                    
                    kv['key'] = item["qualifierValue"]
                    kv["qualifier_parent"] = item["keyLabel"]
                    kv["is_label_mapped"] = True
                    kv["key_value"] = tmp_pf_dict[item["keyLabel"]]
                    trace_list.append(item["qualifierValue"])
                    
                else:
                    kv['key'] = item["keyLabel"]
                    kv["is_label_mapped"] = True
                    kv["key_value"] = tmp_pf_dict[item["keyLabel"]]
                    trace_list.append(item["keyLabel"])
    # except:
    #     pass

    return children
    

def lowercase_first_char(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]


def get_parsed_address(data_json, address_parser_example,address_field_name, address_partial_field_name, doc_type):
    if data_json == {}:
        return data_json
    
    kv_list = data_json.get("key_data",[])
    address_data = {}
    address_partial_data = {}
    for kv_idx, kv_pair in enumerate(kv_list):
        if kv_pair["key"] in address_field_name and kv_pair["value"].strip() != "":
            address_data[kv_idx] = kv_pair["value"]
        elif (kv_pair["value"].strip() != "" and any(kv_pair["key"].lower().strip() == field.lower().strip() for field in address_partial_field_name )):
            address_partial_data[kv_idx] = copy.deepcopy(kv_pair)


    if address_data != {}:
        address_data_parsed_list = get_llm_result_address_parser(address_data, address_parser_example, doc_type)
    
        address_data_parsed_list = get_formatted_address_data(address_data_parsed_list)

        mapping_address_data_to_data_json_kv = address_data.keys()
        
        for address_idx, kv_idx in enumerate(mapping_address_data_to_data_json_kv):
            children = []
            block = kv_list[kv_idx]["value"]
            parent_key = kv_list[kv_idx]["key"]
            for addresss_key, address_value in address_data_parsed_list[address_idx].items():
                if isinstance(address_value, dict):
                    
                    if addresss_key == "contact":
                        address_value = {
                                        "contactName": address_value.get("name"),
                                        "contactPhone": address_value.get("phone"),
                                        "contactEmail": address_value.get("email")
                                    }

                    for address_key_inner, address_value_inner in address_value.items():
                        if address_value_inner.strip() != "":
                            children.append({
                            "key":address_key_inner.strip(),
                            "value":address_value_inner.strip(),
                            "is_profile_key_found" : True,
                            "is_label_mapped" : False,
                            "original_key_label" : address_key_inner.strip(),
                            "key_value": address_key_inner.strip()
                            }) 
                    
                else:
                    if address_value.strip() != "" and addresss_key.strip() != "name":
                        children.append({
                        "key":addresss_key.strip(),
                        "value":address_value.strip(),
                        "is_profile_key_found" : True,
                        "is_label_mapped" : False,
                        "original_key_label" : addresss_key.strip(),
                        "key_value": addresss_key.strip()
                        })
                    elif address_value.strip() != "" and addresss_key.strip() == "name":

                        children.append({
                        "key":addresss_key.strip(),
                        "value":address_value.strip(),
                        "is_profile_key_found" : True,
                        "is_label_mapped" : False,
                        "original_key_label" : addresss_key.strip(),
                        "key_value": addresss_key.strip()
                        })
                        
                        kv_list[kv_idx]["value"] = address_value.strip()
                        
            children.append({
                        "key":"block",
                        "value":block.strip(),
                        "is_profile_key_found" : True,
                        "is_label_mapped" : False,
                        "original_key_label" : "block",
                        "key_value": "block"
                        })
            
            # try:
            #children = get_sub_label_mapping(children,mapped_keys_for_address_block,parent_key)
            # except:
            #     pass
            #print(addresss_key, address_value)
           
            kv_list[kv_idx]["children"] = copy.deepcopy(children)

    print("#######.  888. 888. ######")
    print(address_partial_data)
    print("#############")

    for adp_idx, adp_item_main in address_partial_data.items():

        for kv_idx, kv in enumerate(kv_list):
            is_placement_done = False
            if kv['key'].lower().strip() in adp_item_main["key"].lower().strip() and kv['key'].lower().strip() != adp_item_main["key"].lower().strip():
                for child_idx, child in enumerate(kv.get("children", [])):
                    if child['key'].lower().strip() in adp_item_main["key"].lower().strip():
                        child["value"] = adp_item_main["value"]
                        is_placement_done = True
                        break
                if not is_placement_done:
                    
                    r_key = adp_item_main["key"]

                    if "accountnumber" in r_key.lower().strip():
                        tmp_key = "accountNumber"
                    elif "name" in r_key.lower().strip():
                        tmp_key = "name"
                    elif "addressline1" in r_key.lower().strip():
                        tmp_key = "addressLine1"
                    elif "addressline2" in r_key.lower().strip():
                        tmp_key = "addressLine2"
                    elif "postalcode" in r_key.lower().strip():
                        tmp_key = "postalCode"
                    elif "city" in r_key.lower().strip():
                        tmp_key = "city"
                    elif "stateprovince" in r_key.lower().strip():
                        tmp_key = "stateProvince"
                    elif "countrycode" in r_key.lower().strip():
                        tmp_key = "countryCode"
                    elif "contactName" in r_key.lower().strip():
                        tmp_key = "contactName"
                    elif "contactNumber" in r_key.lower().strip():
                        tmp_key = "contactNumber"
                    elif "contactEmail" in r_key.lower().strip():
                        tmp_key = "contactEmail"
                    elif "addressshortcode" in r_key.lower().strip():
                        tmp_key = "addressShortCode"
                    else:
                        tmp_key = lowercase_first_char(r_key.replace(kv['key'],"").strip())

                    if not kv.get("children"):
                        print("^^^^^^^^^^^^^^^^^")
                        print("Im inside block")
                        print(kv)
                        print(adp_item_main)
                        print("^^^^^^^^^^^^^^^^^")
                        
                        kv["value"] = adp_item_main["value"]
                        kv["children"] = []
                        kv["children"].append(
                        {
                            "key":"block",
                            "value":adp_item_main["value"],
                            "is_profile_key_found" : True,
                            "is_label_mapped" : False,
                            "original_key_label" : "block",
                            "key_value": "block"
                        }
                    )

                    kv["children"].append(
                        {
                            "key":tmp_key,
                            "value":adp_item_main["value"],
                            "is_profile_key_found" : True,
                            "is_label_mapped" : False,
                            "original_key_label" : tmp_key,
                            "key_value": tmp_key
                        }
                    )
                    is_placement_done = True
                    adp_item_main["is_placement_done"] = True
                    break

            if is_placement_done:
                adp_item_main["is_placement_done"] = True
                break

    for adp_idx, adp_item_main in address_partial_data.items():
        for item_idx, item in enumerate(kv_list):
            if item["key"] == adp_item_main["key"]:
                kv_list.pop(item_idx)
                break

    return data_json