import os
import requests
from dotenv import load_dotenv
load_dotenv()

vector_data_base_url = os.getenv("VECTOR_DATA_BASE_API")
DATA_BASE_ID = "dictionaries"

def query_auto_match(process, table, query_data, top_k=5, threshold=0.2):
    
    url = f"{vector_data_base_url}/{DATA_BASE_ID}/query/auto-match"
    payload = {
        "process_uid": process,
        "table": table,
        "query": query_data,
        "top_k": top_k,
        "threshold": threshold
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during auto-match query: {e}")
        return None

def get_mandatory_column(table_item):
    res = []
    for col_name, col_data in table_item["column_schema"].items():
        if col_data["ismandatory"]:
            res.append(col_name)
    return res

def get_table_and_mandatory_column_info(all_table_info,key_list):
    
    best_score_idx = 0
    prev_best_score = 0
    result = []
    for idx, item in enumerate(all_table_info):
        score = 0
        mandatory_col_list = get_mandatory_column(item)
        mandatory_col_list_for_query = [{}]
        for m_col in mandatory_col_list:
            for kv in key_list:
                if m_col.lower().strip() == kv["key"].lower().strip():
                    mandatory_col_list_for_query[0][m_col] = kv["value"]
                    score += 1
        result.append({"table_name": item["table_name"],"mandatory_col_list": mandatory_col_list_for_query})
        if score >= prev_best_score:
            prev_best_score = score
            best_score_idx = idx

    return result[best_score_idx]["table_name"],result[best_score_idx]["mandatory_col_list"]


        


# def get_probable_declarent_info(combined_data_json):
#     probable_declarent_info_from_doc = []
#     for data_json in  combined_data_json["documents"]:
#         if data_json["doc_type"].lower().replace(" ","").strip() == "commercialinvoice":
#             for kv_item in data_json["key_data"]:
#                 if kv_item["key"].lower().strip() == "importer":
#                     for inner_item in kv_item["children"]:
#                         if inner_item["key"].lower().strip() == "name":
#                             probable_declarent_info_from_doc.append("label":"importerName","value":inner_item["value"])
#                         elif inner_item["key"].lower().strip() == "accountNumber":
#                             probable_declarent_info_from_doc.append("label":"importerAccountNumber","value":inner_item["value"])
#                     break
#     if probable_declarent_info_from_doc == {}:
#         for data_json in  combined_data_json["documents"]:
#             if data_json["doc_type"].lower().replace(" ","").strip() != "commercialinvoice":
#                 for kv_item in data_json["key_data"]:
#                     if kv_item["key"].lower().strip() == "importer":
#                         for inner_item in kv_item["children"]:
#                             if inner_item["key"].lower().strip() == "name":
#                                 probable_declarent_info_from_doc.append("label":"importerName","value":inner_item["value"])
#                             elif inner_item["key"].lower().strip() == "accountNumber":
#                                 probable_declarent_info_from_doc.append("label":"importerAccountNumber","value":inner_item["value"])
#                         break
#     return probable_declarent_info_from_doc


def get_top_columns(payload: dict) -> dict:
    
    if not payload or "results" not in payload or not payload["results"]:
        return {}

    top_entry = max(payload["results"], key=lambda x: x.get("score", 0))
    print("************* dictionary ****************")
    print(top_entry)

    if top_entry.get("score", 0) >= 0.85:
        return top_entry.get("columns", {})
    else:
        return {}

def get_agent_reference_for_forwarder(retrived_data_from_data_base, r_value):

    trigger = "agentsreference"
    desired_value = r_value

    for k,v in retrived_data_from_data_base.items():
        if trigger in k.lower().replace(" ", "").strip():
            desired_value = v
            break
    return desired_value


def check_if_address_partial_field(r_key, address_field_name_list, address_partial_field_name_list):

    parent_key = None
    is_address_partial_field = False
    for abp_idx, abp in enumerate(address_partial_field_name_list):
        if abp.lower().strip() == r_key.lower().strip():
            is_address_partial_field = True
            if is_address_partial_field:
                for ab_idx, ab in enumerate(address_field_name_list):
                    if ab.lower().strip() in abp.lower().strip():
                        parent_key = ab
                        break
            if is_address_partial_field:
                break
    if is_address_partial_field and parent_key:
        return is_address_partial_field, parent_key
    else:
        return None, None

def lowercase_first_char(s: str) -> str:
    if not s:
        return s
    return s[0].lower() + s[1:]

def get_vector_data(combined_data_json, process_uid, address_field_name_list, address_partial_field_name_list):

    try:
        all_table_info = requests.get(f"{vector_data_base_url}/{DATA_BASE_ID}/tables/{process_uid}")
        all_table_info = all_table_info.json()
    except:
        all_table_info = {}
        pass


    if not isinstance(all_table_info, list) : 
        if all_table_info == {} or "not found" in all_table_info.get("detail",""):
            return combined_data_json


    
    # probable_declarent_info_from_doc = get_probable_declarent_info(combined_data_json)

    # table_name, query_data = get_table_and_mandatory_column_info(all_table_info,probable_declarent_info_from_doc)
    # declarent_info_from_database = query_auto_match(process_name, table_name, query_data)
    # declarent_info_from_database = get_top_columns(declarent_info_from_database)

    for data_json in  combined_data_json["documents"]:
        kv_list = data_json["key_data"]
        mandatory_col_list = []
        result_from_database = []
        
        table_name = ""
        

        for idx, table in enumerate(all_table_info):
            query_data = [{}]
            table_name = table["table_name"]
            for col_name, col_data in table["column_schema"].items():
                if col_data["ismandatory"]:
                    mandatory_col_list.append(col_name.lower().strip())
                    for kv_item in kv_list:
                        if kv_item.get("children",[]) != [] and kv_item["key"].lower().strip() in col_name.lower().strip():
                            for inner_item in kv_item["children"]:
                                if inner_item["key"].lower().strip() in col_name.lower().strip() and inner_item["value"].replace(" ","").strip() != "":
                                    query_data[0][col_name] = inner_item["value"]
                        else:
                            if kv_item["key"].lower().strip() == col_name.lower().strip() and kv_item["value"].replace(" ","").strip() != "":
                                query_data[0][col_name] = kv_item["value"]


            if query_data != [{}]:
                if list(query_data[0].keys())[0] == "modeOfTransport" and len(query_data[0]) == 1:
                    continue

            if query_data != [{}]:
                if list(query_data[0].keys())[0] == "customsEntryType" and len(query_data[0]) == 1:
                    continue

            if query_data == [{}]:
                continue
                
            retrived_data_from_data_base = query_auto_match(process_uid, table_name, query_data)
            
            retrived_data_from_data_base = get_top_columns(retrived_data_from_data_base)
            
            print("!!!!!!!!!!!!!!!!!!!!!******")
            print("Table name:", table_name)
            print("Query data:", query_data)
            print("Retrieved data:", retrived_data_from_data_base)
            print("!!!!!!!!!!!!!!!!!!!!!******")

            query_data = [{}]


            for r_key, r_value in retrived_data_from_data_base.items(): 
        
                if r_key.lower().strip() in mandatory_col_list and "forwarder" not in r_key.lower().strip():
                    continue
                    
                is_placement_done = False
                for kv_item in kv_list:
                    
                    
                    if kv_item["key"].lower().replace(" ","").strip() in table_name.lower().replace(" ","").strip():
                        kv_item["STATUS"] = 111
                        kv_item["auto_lookup_unresolved"] = True


                    if kv_item["key"].lower().replace(" ","").strip() == r_key.lower().replace(" ","").strip() and kv_item.get("children",[]) == [] and r_value != "" and r_value != None:
                        kv_item["value"] = r_value
                        is_placement_done = True
                        break
                    elif kv_item["key"].lower().strip() in r_key.lower().strip() and kv_item.get("children",[]) != [] and r_value != "" and r_value != None:

                        for inner_item in kv_item["children"]:
                            if inner_item["key"].lower().strip() in r_key.lower().strip() and r_value != "" and r_value != None:

                                if r_key.lower().strip().replace(kv_item["key"].lower().strip(),"").replace(inner_item["key"].lower().strip(),"").replace(" ","").strip() != "":
                                    continue

                                if kv_item["key"].lower().strip() == "forwarder" and "name" in r_key.lower().strip():
                                    #inner_tmp_value = retrived_data_from_data_base.get("agentsReference",r_value)
                                    inner_tmp_value = get_agent_reference_for_forwarder(retrived_data_from_data_base, r_value)
                                else:
                                    inner_tmp_value = r_value

                                inner_item["value"] = inner_tmp_value
                                is_placement_done = True
                                break

                        if not is_placement_done:
                            
                            
                            if kv_item["key"].lower().strip() == "forwarder" and "name" in r_key.lower().strip():
                                #tmp_value = retrived_data_from_data_base.get("agentsReference",r_value)
                                tmp_value = get_agent_reference_for_forwarder(retrived_data_from_data_base, r_value)
                            else:
                                tmp_value = r_value



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
                                tmp_key = r_key

                            if r_key.lower().strip().replace(kv_item["key"].lower().strip(),"").replace(tmp_key.lower().strip(),"").replace(" ","").strip() != "":
                                continue

                            is_placement_done = True
                            
                            kv_item["children"].append({
                                        "key": tmp_key,
                                        "key_position": "0,0,0,0",
                                        "value": str(tmp_value),
                                        "value_position": "0,0,0,0",
                                        "page_id": "", 
                                        "original_key":tmp_key,
                                        "is_label_mapped":False,
                                        "is_profile_key_found":True,
                                        "is_data_exception_done": False,
                                        "is_pure_autoextraction" : True,
                                        "original_key_label" :tmp_key,
                                        "key_value":tmp_key
                                        })
                
                if not is_placement_done and r_value != "" and r_value != None and r_value != "None":

                    is_address_partial_field, parent_key = check_if_address_partial_field(r_key, address_field_name_list, address_partial_field_name_list)
                    print("is_address_partial_field",is_address_partial_field)
                    print("parent_key",parent_key)
                    print(r_key)
                    if is_address_partial_field and parent_key:
                        
                        new_parent = {
                                "key": parent_key,
                                "key_position": "0,0,0,0",
                                "value": str(r_value),
                                "value_position": "0,0,0,0",
                                "page_id": "", 
                                "original_key":parent_key,
                                "is_label_mapped":False,
                                "is_profile_key_found":True,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label":parent_key,
                                "key_value":parent_key,
                                "children":[]
                                }
                        new_block = {
                                "key": "block",
                                "key_position": "0,0,0,0",
                                "value": str(r_value),
                                "value_position": "0,0,0,0",
                                "page_id": "", 
                                "original_key":"block",
                                "is_label_mapped":False,
                                "is_profile_key_found":True,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label":"block",
                                "key_value":"block",
                                }
                        new_tmp_child_key = ""

                        if "accountnumber" in r_key.lower().strip():
                                new_tmp_child_key = "accountNumber"
                        elif "name" in r_key.lower().strip():
                            new_tmp_child_key = "name"
                        elif "addressline1" in r_key.lower().strip():
                            new_tmp_child_key = "addressLine1"
                        elif "addressline2" in r_key.lower().strip():
                            new_tmp_child_key = "addressLine2"
                        elif "postalcode" in r_key.lower().strip():
                            new_tmp_child_key = "postalCode"
                        elif "city" in r_key.lower().strip():
                            new_tmp_child_key = "city"
                        elif "stateprovince" in r_key.lower().strip():
                            new_tmp_child_key = "stateProvince"
                        elif "countrycode" in r_key.lower().strip():
                            new_tmp_child_key = "countryCode"
                        elif "contactName" in r_key.lower().strip():
                            new_tmp_child_key = "contactName"
                        elif "contactNumber" in r_key.lower().strip():
                            new_tmp_child_key = "contactNumber"
                        elif "contactEmail" in r_key.lower().strip():
                            new_tmp_child_key = "contactEmail"
                        elif "addressshortcode" in r_key.lower().strip():
                            new_tmp_child_key = "addressShortCode"
                        else:
                            new_tmp_child_key = lowercase_first_char(r_key.replace(parent_key,"").strip())

                        new_child = {
                                "key": new_tmp_child_key,
                                "key_position": "0,0,0,0",
                                "value": str(r_value),
                                "value_position": "0,0,0,0",
                                "page_id": "", 
                                "original_key":new_tmp_child_key,
                                "is_label_mapped":False,
                                "is_profile_key_found":True,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label" :new_tmp_child_key,
                                "key_value":new_tmp_child_key,
                                }  

                        new_parent["children"].append(new_child)
                        new_parent["children"].append(new_block)
                        kv_list.append(new_parent)

                    else:
                        kv_list.append({
                                    "key": r_key,
                                    "key_position": "0,0,0,0",
                                    "value": str(r_value),
                                    "value_position": "0,0,0,0",
                                    "page_id": "", 
                                    "original_key":r_key,
                                    "is_label_mapped":False,
                                    "is_profile_key_found":True,
                                    "is_data_exception_done": False,
                                    "is_pure_autoextraction" : True,
                                    "original_key_label" :r_key,
                                    "key_value":r_key
                                    })
    return combined_data_json
                
                        
                    
        





        


