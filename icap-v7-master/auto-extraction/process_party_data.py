import os
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz
load_dotenv()

vector_data_base_url = os.getenv("VECTOR_DATA_BASE_API")
DATA_BASE_ID = "parties"

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

def get_top_columns_best_score(payload: dict) -> dict:
    
    if not payload or "results" not in payload or not payload["results"]:
        return {}

    top_entry = max(payload["results"], key=lambda x: x.get("score", 0))
    
    return top_entry.get("columns", {})
    

def get_top_columns(payload: dict) -> dict:
    
    if not payload or "results" not in payload or not payload["results"]:
        return {}

    top_entry = max(payload["results"], key=lambda x: x.get("score", 0))
    

    if top_entry.get("score", 0) >= 0.82:
        print("^^##^^##^^##^^## Party Lookup Matched")
        print(top_entry)

        return top_entry.get("columns", {})
    else:
        return {}
    
def get_party_data(combined_data_json, process_uid):
    
    STATUS = 111
    auto_lookup_unresolved = False

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

        for kv_item in kv_list:
            if kv_item.get("children",[]) != []:

                desired_table = {}
                retrived_data_from_data_base = {}
                for idx, table in enumerate(all_table_info):
                    table_name = table["table_name"]
                    if table_name.lower().strip() == kv_item["key"].lower().strip():
                        desired_table = table
                        break
                if desired_table == {}:
                    continue

                STATUS = -1000
                auto_lookup_unresolved = True

                query_col_list = [] 
                for col_name, col_data in desired_table["column_schema"].items():
                    if col_data["ismandatory"]:
                        query_col_list.append(col_name)
                    
                query_data_full = [{}]
                query_data_short = [{}]

                
                full_address_key = ""
                block_text = ""
                for inner_item in kv_item["children"]:
                    if inner_item["key"].lower().strip() == "block":
                        block_text = inner_item["value"]
                        continue

                    for col_name in query_col_list:
                        if full_address_key == "" and "full_address" in col_name.lower().strip():
                            full_address_key = col_name
                            break

                        if inner_item["key"].lower().strip() in col_name.lower().strip() and col_name:
                            if inner_item["key"].lower().strip() == "name":
                                query_data_short[0][col_name] = inner_item["value"]
                            query_data_full[0][col_name] = inner_item["value"]
                            break

                query_data_short[0][full_address_key] = block_text
                is_raw_retrived_data_from_short = True
                retrived_data_from_data_base_short = query_auto_match(process_uid, desired_table["table_name"], query_data_short)
                retrived_data_from_data_base_raw = retrived_data_from_data_base_short
                retrived_data_from_data_base_short = get_top_columns(retrived_data_from_data_base_short)

                if retrived_data_from_data_base_short == {}:
                    retrived_data_from_data_base_full = query_auto_match(process_uid, desired_table["table_name"], query_data_full)
                    retrived_data_from_data_base_raw = retrived_data_from_data_base_full
                    is_raw_retrived_data_from_short = False
                    best_retrived_below_threshold = get_top_columns_best_score(retrived_data_from_data_base_full)
                    retrived_data_from_data_base_full = get_top_columns(retrived_data_from_data_base_full)
                    retrived_data_from_data_base = retrived_data_from_data_base_full
                else:
                    retrived_data_from_data_base = retrived_data_from_data_base_short
                

                # retrived_data_from_data_base = get_top_columns(retrived_data_from_data_base)
                # print("########### This is Query Data short parties")
                # print(query_data_short)
                # print(retrived_data_from_data_base_short)
                # print("########### This is Full Query")
                # print(query_data_full)
                # print(retrived_data_from_data_base_full)
                # print("########### This is Final Retrived Data")
                # print(retrived_data_from_data_base)
                # print("########### This is Best retrived below threshold")
                # print(best_retrived_below_threshold)
                # print("########### This is retrived below threshold all")
                # print(retrived_data_from_data_base_raw)


                if retrived_data_from_data_base == {}:
                    if best_retrived_below_threshold == {}:
                        kv_item["STATUS"] = STATUS
                        kv_item["auto_lookup_unresolved"] = auto_lookup_unresolved
                        continue
                    else:
                        matched_item_count = 0
                        total_item_count = 0
                        for r_k, r_v in best_retrived_below_threshold.items():
                            if r_v != "" and r_v != None and r_v != "None" and r_k in query_data_full[0].keys():
                                total_item_count += 1
                                if fuzz.ratio(query_data_full[0][r_k].lower().replace(" ", "").strip(),r_v.lower().replace(" ", "").strip()) >= 82:
                                    matched_item_count += 1
                        
                        if matched_item_count == total_item_count:
                            retrived_data_from_data_base = best_retrived_below_threshold

                if retrived_data_from_data_base_raw != {} and retrived_data_from_data_base == {}:
                    if is_raw_retrived_data_from_short:
                        check_dict = query_data_short[0]
                    else:
                        check_dict = query_data_full[0]

                    desired_idx = -1
                    best_score = 0

                    for matched_items_idx, matched_items in enumerate(retrived_data_from_data_base_raw["results"]):
                    
                        for matched_col, matched_val in matched_items["columns"].items():
                            if "name" in matched_col and "cw1_name" not in matched_col and matched_val != "":
                                local_score =  fuzz.ratio(matched_val.lower().replace(" ", "").strip(),check_dict.get(matched_col,"").lower().replace(" ", "").strip())

                                if local_score >= best_score:
                                    best_score = local_score
                                    desired_idx = matched_items_idx
                                break

                    if best_score >= 92:
                        retrived_data_from_data_base = retrived_data_from_data_base_raw["results"][desired_idx]["columns"]
                        


                                
                for r_key, r_value in retrived_data_from_data_base.items():

                    tmp_key = ""

                    if "accountnumber" in r_key.lower().strip():
                        STATUS = 111
                        tmp_key = "accountNumber"
                    elif "cw1_name" in r_key.lower().strip():
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
                    elif "full_address" in r_key.lower().strip():
                        tmp_key = "block"
                    
                    if tmp_key == "block":
                        continue

                    is_placement_done = False
                    for inner_item in kv_item["children"]:
                            
                        if inner_item["key"].lower().strip() == tmp_key.lower().strip()  and r_value != "" and r_value != "None" and r_value != None:
                            inner_item["value"] = r_value
                            is_placement_done = True
                            break

                    if not is_placement_done and r_value != "" and tmp_key != "" and r_value != "" and r_value != "None" and r_value != None:
                        kv_item["children"].append(
                            {
                            "key": tmp_key.replace(desired_table["table_name"],"").replace("_","").strip(),
                            "key_position": "0,0,0,0",
                            "value": str(r_value),
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

                kv_item["STATUS"] = STATUS
                kv_item["auto_lookup_unresolved"] = auto_lookup_unresolved
                        
    return combined_data_json