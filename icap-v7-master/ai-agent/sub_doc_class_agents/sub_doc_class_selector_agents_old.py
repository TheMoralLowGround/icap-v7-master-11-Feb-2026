import os
import requests
import json
from dotenv import load_dotenv
from utils.llm_clients import run_llm
from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
import copy  
from rapidfuzz import fuzz

load_dotenv()

vector_data_base_url = os.getenv("VECTOR_DATA_BASE_API")
DATA_BASE_ID = "scenarios"



def query_auto_match(process, table, query_data, top_k=5, threshold=0.7):
    
    url = f"{vector_data_base_url}/{DATA_BASE_ID}/query/auto-match"
    payload = {
        "process": process,
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



def get_match_flag(payload: dict) -> dict:
    
    if not payload or "results" not in payload or not payload["results"]:
        return False
    
    sorted_entries = sorted(payload["results"], key=lambda x: x.get("score", 0), reverse=True)
    if len(sorted_entries) > 5:
        sorted_entries = sorted_entries[:5]

    top_entry = sorted_entries[0]
    
    print("###### top entry ####",top_entry)
    if top_entry.get("score",0) >= 0.85:
        return True
    else:
        return False




def get_entity_name_and_account_number(entity):

    name = ""
    account_number = ""
    
    if entity.get("children",[]) == [] :
        if entity != {}:
            return entity["v"], ""
        else:
            return "", ""

    for item in entity["children"]:
        if item["label"] == "name":
            name = item["v"]
        elif item["label"] == "accountNumber":
            account_number = item["v"]
    return name, account_number 
        


def get_id_for_new_item(id_str):
    parts = id_str.split(".")
    last_num = int(parts[-1])
    last_num += 1
    parts[-1] = str(last_num).zfill(len(parts[-1]))
    return ".".join(parts)



def run_sub_doc_class_selector_agent(combined_ra_json, combined_data_json, project_name):

    print(combined_data_json)

    try:
        all_table_info = requests.get(f"{vector_data_base_url}/{DATA_BASE_ID}/tables/{project_name}")
        all_table_info = all_table_info.json()
    except:
        all_table_info = {}
        pass

    if not isinstance(all_table_info, list) : 
        if all_table_info == {} or "not found" in all_table_info.get("detail",""):
            return combined_data_json

    msg = "Sub Doc Class Selection completed."

    #try:
    importer = {}
    forwarder = {}
    carrier = {}

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            if doc_wise_data_json["DocType"].lower().replace(" ","").strip() ==  "prealert":
                kv_list = []
                for item in doc_wise_data_json["children"]:
                    if item["type"] == "key":
                        kv_list = item["children"]
                        break
                for kv_idx, kv_item in enumerate(kv_list):
                    if kv_item["original_key_label"].lower().strip() == "importer" and importer == {}:
                        importer = copy.deepcopy(kv_item)
                    elif kv_item["original_key_label"].lower().strip() == "forwarder" and forwarder == {}:
                        forwarder = copy.deepcopy(kv_item)
                    if importer != {} and forwarder != {}:
                        break
                
    if importer == {}:
        for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):
            for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
                if doc_wise_data_json["DocType"].lower().replace(" ","").strip() ==  "commercialinvoice":
                    kv_list = []
                    for item in doc_wise_data_json["children"]:
                        if item["type"] == "key":
                            kv_list = item["children"]
                            break
                    for kv_idx, kv_item in enumerate(kv_list):
                        if kv_item["original_key_label"].lower().strip() == "importer" and importer == {}:
                            importer = copy.deepcopy(kv_item)
                        if importer != {}:
                            break
    

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            if doc_wise_data_json["DocType"].lower().replace(" ","").strip() ==  "housewaybill":
                kv_list = []
                for item in doc_wise_data_json["children"]:
                    if item["type"] == "key":
                        kv_list = item["children"]
                        break
                for kv_idx, kv_item in enumerate(kv_list):
                    if kv_item["original_key_label"].lower().strip() == "carrier":
                        carrier[doc_idx] = copy.deepcopy(kv_item)


    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            if doc_wise_data_json["DocType"].lower().replace(" ","").strip() ==  "housewaybill":
                kv_list = []
                for item in doc_wise_data_json["children"]:
                    if item["type"] == "key":
                        kv_list = item["children"]
                        break

                new_kv_item = {
                    "v": "None",
                    "id": get_id_for_new_item(kv_list[-1]["id"]),
                    "type": "keyTextDetail",
                    "label": "subDocClass",
                    "STATUS": 1,
                    "children": [],
                    "key_value": "",
                    "is_label_mapped": False,
                    "original_key_label": "",
                    "is_profile_key_found": True,
                    "is_pure_autoextraction": True,
                    "is_address_block_partial": False
                }
                carrier_entity = carrier.get(doc_idx, {})
                carrier_name, carrier_account_number = get_entity_name_and_account_number(carrier_entity)
                forwarder_name , forwarder_account_number = get_entity_name_and_account_number(forwarder)
                importer_name , importer_account_number = get_entity_name_and_account_number(importer)

                
                carrier_macth_from_data_base = query_auto_match(project_name, "CARRIER", [{ "carrierName":carrier_name}])
                forwarder_macth_from_data_base = query_auto_match(project_name, "FORWARDER",[{"forwarderName":forwarder_name}])
                

                is_carrier_matched = get_match_flag(carrier_macth_from_data_base)
                is_forwarder_matched = get_match_flag(forwarder_macth_from_data_base)

                msg += f"\n\nDoc ID: {doc_id}"
                if is_carrier_matched:
                    msg += f"\nCarrier matched with data base"
                    if fuzz.ratio(importer_name.lower().replace(" ","").strip(), forwarder_name.lower().replace(" ","").strip()) > 85 and forwarder_name.lower().replace(" ","").strip() != "":
                        msg += f"\nImporter name and Forwarder name matched\nSo Sub Doc Class is MBL"
                        new_kv_item["v"] = "MBL"
                    elif importer_account_number.lower().replace(" ","").strip() == forwarder_account_number.lower().replace(" ","").strip() and importer_account_number.lower().replace(" ","").strip() != "":
                        msg += f"\nImporter account number and Forwarder account number matched\nSo Sub Doc Class is MBL"
                        new_kv_item["v"] = "MBL"
                    else:
                        msg += f"\nImporter name and Forwarder name not matched\nSo Sub Doc Class is HBL"
                        new_kv_item["v"] = "HBL"
                elif is_forwarder_matched:
                    msg += f"\nForwarder matched with data base"
                    if fuzz.ratio(importer_name.lower().replace(" ","").strip(), forwarder_name.lower().replace(" ","").strip()) > 85 and forwarder_name.lower().replace(" ","").strip() !="":
                        msg += f"\nImporter name and Forwarder name matched\nSo Sub Doc Class is MBL"
                        new_kv_item["v"] = "MBL"
                    elif importer_account_number.lower().replace(" ","").strip() == forwarder_account_number.lower().replace(" ","").strip() and importer_account_number.lower().replace(" ","").strip() != "":
                        msg += f"\nImporter account number and Forwarder account number matched\nSo Sub Doc Class is MBL"
                        new_kv_item["v"] = "MBL"
                    else:
                        msg += f"\nImporter name and Forwarder name not Matched\nSo Sub Doc Class is HBL"
                        new_kv_item["v"] = "HBL"
                
                print("##### carrier")
                print(is_carrier_matched)
                print(carrier_name)
                print(carrier_account_number)
                print("###############")
                print("##### forwarder")
                print(is_forwarder_matched)
                print(forwarder_name)
                print(forwarder_account_number)
                print("###############")
                print("##### importer")
                print(importer_name)
                print(importer_account_number)
                print("###############")

                print("##### new_kv_item")
                print(new_kv_item)
                print("###############")

                if new_kv_item["v"] == "None":
                    msg += f"\nNo match found for carrier and forwarder\n So Sub Doc Class is None"


                if new_kv_item["v"] != "None" and kv_list[-1]["label"] != "subDocClass":
                    kv_list.append(new_kv_item)
                

    
    return combined_data_json, msg
    # except:
    #     return combined_data_json
    #     pass

