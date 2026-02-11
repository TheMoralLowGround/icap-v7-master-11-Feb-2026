import os
import requests
import json
from dotenv import load_dotenv
from utils.llm_clients import run_llm
from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
import copy  
from rapidfuzz import fuzz
import json
import re
from typing import Dict, Any, Union

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



def get_match_flag(payload,entity_name):
    
    if not payload or "results" not in payload or not payload["results"]:
        return False
    sorted_entries = sorted(payload["results"], key=lambda x: x.get("score", 0), reverse=True)
    if len(sorted_entries) > 5:
        sorted_entries = sorted_entries[:5]

    top_entry = sorted_entries[0]
    
    print("###### top entry ####",top_entry)
    print(entity_name)
    if top_entry.get("score",0) >= 0.8:
        return True
    else:
        name_from_db = ""
        for k, v in top_entry.get("columns").items():
            if "name" in k.lower().strip():
                name_from_db = v
                break
        if entity_name.split(" ")[0].replace(" ","").lower().strip() in name_from_db.replace(" ","").lower().strip() or name_from_db.split(" ")[0].replace(" ","").lower().strip() in entity_name.replace(" ","").lower().strip():
            return True
        return False

 
        


def get_id_for_new_item(id_str):
    parts = id_str.split(".")
    last_num = int(parts[-1])
    last_num += 1
    parts[-1] = str(last_num).zfill(len(parts[-1]))
    return ".".join(parts)


def llm_json_to_dict(llm_response: str) -> Dict[str, Any]:

    cleaned = llm_response.strip()

    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*\n', '', cleaned)
        cleaned = re.sub(r'\n```$', '', cleaned)
    
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
    if json_match:
        cleaned = json_match.group(1)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Attempted to parse: {cleaned[:200]}...") 
        return {}


def get_entity_name(ra_json):

    system_prompt = """You are a document entity extractor. Your task is to identify and extract the following fields from the provided document text:

    1. issuer_name - The name of the entity that issued the document
    2. shipper_name - The name of the shipping party
    3. consignee_name - The name of the receiving party
    4. modeOfTransport - The method of transportation used

    **Output Format:**
    Return ONLY a valid JSON object in the following structure:
    {
    "issuer_name": "<full name or null>",
    "shipper_name": "<full name or null>",
    "consignee_name": "<full name or null>",
    "mode_of_transport": "<SEA or AIR>"
    }

    **Rules:**
    - Output ONLY the JSON object. No explanations, no additional text, no markdown formatting.
    - Always use the complete/full name of the entity as it appears in the document and dont include address data in name. keep only name.
    - If a field is not present or cannot be identified in the document, use null.
    - Do not guess or infer values that are not explicitly stated or clearly implied in the document.
    - Maintain exact spelling and capitalization as found in the source document for names.
    - For mode_of_transport : Use "SEA" for ocean/sea freight, "AIR" for air freight."""

    llm_result = []
    user_content = ""
   
    for  page_idx, page in enumerate(ra_json["children"]):

        
      if user_content == "":
        page_wise_paragraph = get_ra_json_to_txt_table_new(page)
        user_content =f"########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"
      else:
        user_content = f"{user_content}\n########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"



    response, reasoning = run_llm(system_prompt, user_content)
    extracted_result = llm_json_to_dict(response)
    return extracted_result
    
    




def run_sub_doc_class_selector_agent(combined_ra_json, combined_data_json, project_name):

    try:
        all_table_info = requests.get(f"{vector_data_base_url}/{DATA_BASE_ID}/tables/{project_name}")
        all_table_info = all_table_info.json()
    except:
        all_table_info = {}
        pass

    if not isinstance(all_table_info, list) : 
        if all_table_info == {} or "not found" in all_table_info.get("detail",""):
            return combined_data_json, "Sub Doc Class Selection completed."

    msg = "Sub Doc Class Selection completed."
    
    importer = {}
    forwarder = {}
    carrier = {}
    sub_doc_class_mapping = []

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):

        is_mbl_founded_already = False
        batch_id = batch_wise_data_json["id"]

        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            file_path = doc_wise_data_json.get("file_path", "")

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


                ra_json = combined_ra_json[batch_idx]["nodes"][doc_idx]
                entities = get_entity_name(ra_json)
                
                print("#### Entities")
                print(entities)
                print("&&&&&&&&&&&&&&")

                carrier_name = entities.get("issuer_name","") if entities.get("issuer_name","") != None else ""
                shipper_name = entities.get("shipper_name","") if entities.get("shipper_name","") != None else ""
                consignee_name = entities.get("consignee_name","") if entities.get("consignee_name","") != None else ""
                # forwarder_name = entities.get("forwarder_name","") if entities.get("forwarder_name","") != None else ""
                mode_of_transport = entities.get("mode_of_transport","")

                
                carrier_macth_from_data_base_carrier = query_auto_match(project_name, "CARRIER", [{"carrierName":carrier_name}])
                is_carrier_matched_carrier = get_match_flag(carrier_macth_from_data_base_carrier, carrier_name)

                
                carrier_macth_from_data_base_forwarder = query_auto_match(project_name, "FORWARDER", [{"forwarderName":carrier_name}])
                is_carrier_matched_forwarder = get_match_flag(carrier_macth_from_data_base_forwarder, carrier_name)

                # forwarder_macth_from_data_base = query_auto_match(project_name, "FORWARDER",[{"forwarderName":forwarder_name}])
                # is_forwarder_matched = get_match_flag(forwarder_macth_from_data_base, forwarder_name)

                shipper_macth_from_data_base = query_auto_match(project_name, "FORWARDER",[{"forwarderName":shipper_name}])
                is_shipper_matched = get_match_flag(shipper_macth_from_data_base, shipper_name)

                consignee_macth_from_data_base = query_auto_match(project_name, "FORWARDER",[{"forwarderName":consignee_name}])
                is_consignee_matched = get_match_flag(consignee_macth_from_data_base, consignee_name)
                
                
                
                

                msg += f"\n\nDoc ID: {doc_id} \nDocument Issuer : {carrier_name} \nDocument Shipper : {shipper_name} \nDocument Consignee : {consignee_name}\nDocument Mode of Transport : {mode_of_transport}"
                # if mode_of_transport == "AIR":
                #     msg += f"\nThis is a air waybill. No other way bill is here except this.\nSo Sub Doc Class is HBL"
                #     new_kv_item["v"] = "HBL"
                # elif is_mbl_founded_already:
                #     msg += f"\nMaster Bill had already been founded previously.\nSo Sub Doc Class is HBL"
                #     new_kv_item["v"] = "HBL"

                if mode_of_transport == "SEA":
                    if is_carrier_matched_carrier:
                        if is_shipper_matched:
                            msg += f"\nThe document issuer matched with the database (Carrier), and the shipper also matched with the database (Forwarder). So, the Sub Doc Class is MBL."
                            new_kv_item["v"] = "MBL"
                            is_mbl_founded_already = True
                        elif is_consignee_matched:
                            msg += f"\nThe document issuer matched with the database (Carrier), and the consignee also matched with the database (Forwarder). So, the Sub Doc Class is MBL."
                            new_kv_item["v"] = "MBL"
                            is_mbl_founded_already = True
                        else:
                            msg += f"\nThe document issuer matched with the database (Carrier), but the shipper or consignee did not match with the database (Forwarder). So, the Sub Doc Class is HBL."
                            new_kv_item["v"] = "HBL"
                    elif is_carrier_matched_forwarder:
                        if is_shipper_matched:
                            msg += f"\nThe document issuer matched with the database (Forwarder), and the shipper also matched with the database (Forwarder). So, the Sub Doc Class is MBL."
                            new_kv_item["v"] = "MBL"
                            is_mbl_founded_already = True
                        elif is_consignee_matched:
                            msg += f"\nThe document issuer matched with the database (Forwarder), and the consignee also matched with the database (Forwarder). So, the Sub Doc Class is MBL."
                            new_kv_item["v"] = "MBL"
                            is_mbl_founded_already = True
                        else:
                            msg += f"\nThe document issuer matched with the database (Forwarder), but the shipper or consignee did not match with the database (Forwarder). So, the Sub Doc Class is HBL."
                            new_kv_item["v"] = "HBL"
                    else:
                        msg += f"\nNo matches with database found.\nSo Sub Doc Class is HBL"
                        new_kv_item["v"] = "HBL"

                    if new_kv_item["v"] == "None":
                        msg += f"\nNo match found for carrier and forwarder\n So Sub Doc Class is None"


                    if new_kv_item["v"] != "None" and kv_list[-1]["label"] != "subDocClass":
                        sub_doc_class_mapping.append({
                            "batch_id": batch_id,
                            "document_id": doc_id,
                            "file_path": file_path,
                            "doc_code": new_kv_item["v"]
                        })
                        kv_list.append(new_kv_item)

                    if new_kv_item["v"] == "MBL":

                        is_master_bill_number_found = False
                        for kv_pair in kv_list:
                            if kv_pair["label"].lower().replace(" ","").strip() == "masterbillnumber":
                                is_master_bill_number_found = True
                                break

                        for kv_pair in kv_list:
                            if kv_pair["label"].lower().replace(" ","").strip() == "housebillnumber" and not is_master_bill_number_found:
                                kv_pair["label"] = "masterbillNumber"
                                kv_pair["key_value"] = "masterbillNumber"
                                kv_pair["original_key_label"] = "masterbillNumber"

                    doc_wise_data_json["Vendor"] = carrier_name    
        batch_wise_data_json["sub_doc_class_mapping"] = sub_doc_class_mapping
    
    return combined_data_json, msg
    # except:
    #     return combined_data_json
    #     pass

