from rapidfuzz import fuzz
import copy

def get_filtered_data_json_based_on_profile_keys(profile_keys, data_json, is_v6_to_v7_merge = False):

    raw_data_json  = copy.deepcopy(data_json)
    updated_data_json = copy.deepcopy(data_json)
    updated_data_json["key_data"] = []
    #updated_data_json["table_data"] = []

    profile_columns_for_table = []
    if profile_keys == {} or profile_keys == []:
        return raw_data_json, raw_data_json
    

    for p_key_idx, p_key in enumerate(profile_keys):
        
        if p_key["type"] == "table":
            profile_columns_for_table.append(p_key)
        else:
            kv_temp = {}
            profile_key_type_temp = ""
            for kv_idx, kv in enumerate(data_json["key_data"]):
                qualifier_parent = kv.get("qualifier_parent")
                
                if fuzz.ratio(p_key["keyLabel"].lower().strip(),kv["key"].lower()) > 91 and not qualifier_parent:
                    print("***********",p_key["keyLabel"],kv["key"])
                    kv_temp = copy.deepcopy(kv)
                    profile_key_type_temp = p_key["type"]
                    break
                elif qualifier_parent: #and fuzz.ratio(p_key["keyLabel"].lower().strip(),qualifier_parent.lower()) >= 90:
                    print("^^^^^^^^^^",qualifier_parent)
                    kv_temp = copy.deepcopy(kv)
                    profile_key_type_temp = p_key["type"]
                    break
                
            if kv_temp != {}:
                
                data_json["key_data"].remove(kv_temp)
                if kv_temp["value"].strip() == "":
                    kv_temp["STATUS"] = -2
                if not qualifier_parent:
                    kv_temp["key"] = p_key["keyLabel"].strip()
                kv_temp["type"] = profile_key_type_temp
                kv_temp["is_profile_key_found"] = True
                kv_temp["key_value"] = p_key["keyValue"]
                updated_data_json["key_data"].append(kv_temp)
            else:
                updated_data_json["key_data"].append(
                    
                                                    { 
                                                        "key": p_key["keyLabel"].strip(),
                                                        "key_position": "0,0,0,0",
                                                        "type":p_key["type"],
                                                        "value":"",
                                                        "STATUS" :-2,
                                                        "value_position": "0,0,0,0",
                                                        "page_id": "", 
                                                        "original_key":p_key["keyLabel"].strip(),
                                                        "is_label_mapped":False,
                                                        "is_profile_key_found":False,
                                                        "is_data_exception_done": False,
                                                        "is_pure_autoextraction" : False

                                                    }
                                                        )
            
    for kv_idx, kv in enumerate(data_json["key_data"]):
        updated_data_json["key_data"].append(kv)
                
    
    
    for table_idx, table in enumerate(data_json["table_data"]):

        #single_table_new = {"table_id":table["table_id"],"table_name":table["table_name"],"table_data":{"rows":[]}}

        row_data = table["table_data"]["rows"]
        #is_table_populated = False
        for row_idx, row in enumerate(row_data):

            #single_row_new = {"row_id":row["row_id"], "row_data":[]}

            for pc_id, pc in enumerate(profile_columns_for_table):
                is_pc_found = False
                for col_id, col_data in enumerate(row["row_data"]):
                    if fuzz.ratio(pc["keyLabel"].lower().strip(),col_data["label"].lower().strip()) >= 90:
                        col_data["is_profile_key_found"] = True
                        col_data["label"] = pc["keyLabel"].strip()
                        col_data["key_value"] = pc["keyValue"].strip()
                        #single_row_new["row_data"].append(col_data)
                        is_pc_found = True
                        break
                if is_v6_to_v7_merge and not is_pc_found:
                    pass
                elif not is_pc_found:
                  
                    row["row_data"].append({
                        "label" : pc["keyLabel"],
                        "value" : "",
                        "is_profile_key_found": False
                    })

                # if not is_pc_found:
                #     row["row_data"].append({
                #         "label" : pc["keyLabel"],
                #         "value" : "",
                #         "is_profile_key_found": False
                #     })
                    
            #single_table_new["table_data"]["rows"].append(single_row_new)
        #updated_data_json["table_data"].append(single_table_new)
    updated_data_json["table_data"] = copy.deepcopy(data_json["table_data"])

    return  updated_data_json, raw_data_json
        



        
