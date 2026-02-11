import copy
import re
from utils.llm_clients import run_llm

def count_account_numbers(text):

    tokens = re.findall(r'\b[A-Za-z0-9]+\b', text)

    accounts = []
    for t in tokens:
        if (
            any(c.isdigit() for c in t) and   
            any(c.isalpha() for c in t) and   
            len(t) >= 7 and len(t) <= 20 and  
            not t.islower()                   
        ):
            accounts.append(t)
    return len(accounts)

def get_field_precedence_dict(process_keys):


    field_precedence_map = {}
    for item in process_keys:
        item_precedence = item.get("precedence", [])
        if item_precedence == {}:
            item_precedence = []
        field_precedence_map[item["keyValue"]] = item_precedence
    return field_precedence_map

def process_parties(parties,field_precedence_map, msg_dict):

    processed_parties = {}
    source_document_id_dict = {}
    for key, value_list in parties.items():

        precedence = field_precedence_map.get(key,[])
        selected_idx = -1

        if precedence != []:
            for doc_type_p in precedence:
                for field_idx, field_item in enumerate(value_list):
                    if doc_type_p == field_item["doc_type"] and field_item["children"] != {}:

                        #if key.lower().strip()  == "importer" and count_account_numbers(field_item.get("children",{}).get("address",{}).get("block",""))>= 2:
                        if key.lower().strip()  == "importer" and field_item.get("doc_type","").lower().replace(" ","").strip() == "prealert" and count_account_numbers(field_item.get("children",{}).get("address",{}).get("block",""))>= 2:
                            continue

                        selected_idx = field_idx
                        break
                if selected_idx != -1:
                    break

            if selected_idx == -1 :
                continue
                   
            processed_parties[key] =  value_list[selected_idx]["children"]
        
            
            text_msg_doc_type = value_list[selected_idx]["doc_type"]
            source_document_id_dict[key] = [value_list[selected_idx]["doc_id"]]

        else:
            
            selected_idx = -1
            for i in range(len(value_list)-1, -1, -1):
                if value_list[i]["children"] != {}:

                    if key.lower().strip() == "importer" and value_list[i].get("doc_type","").lower().replace(" ","").strip() == "prealert" and count_account_numbers(value_list[i].get("children",{}).get("address",{}).get("block",""))>= 2:
                        continue

                    selected_idx = i
                    break

            if selected_idx == -1:
                pass
            else:
                processed_parties[key] =  value_list[selected_idx]["children"]
                source_document_id_dict[key] = [value_list[selected_idx]["doc_id"]]    

    return processed_parties, source_document_id_dict

def get_precedence_of_party(combined_data_json, process_keys):

    field_precedence_map = get_field_precedence_dict(process_keys)
    
    flatten_kv = {}
    flatten_table = []

    
    doc_wise_table = {}
    
    general_fields = {}
    parties = {}
    housebill_fields = {}

    value_trim_reference = {
        "accountNumber": 12,
        "name": 100,
        "addressShortCode": 25,
        "addressLine1": 50,
        "addressLine2": 50,
        "postalCode": 10,
        "city": 50,
        "stateProvince": 25,
        "countryCode": 2,
        "contactName": 256,
        "contactPhone": 20,
        "contactEmail": 254,
    }

    
    
    msg_dict = {}
    
    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):

        if batch_wise_data_json == {}:
            continue

        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            

            doc_type = doc_wise_data_json["DocType"]
            doc_id = doc_wise_data_json["id"]
            
            
            kv_list = []
            for item in doc_wise_data_json["children"]:
                if item["type"] == "key":
                    kv_list = item["children"]
                elif item["type"] == "table":
                    doc_wise_table[doc_wise_data_json["id"]] = copy.deepcopy(item)
                    
            for kv_idx, kv_item in enumerate(kv_list):
                if kv_item["label"].lower().strip() == "subdocclass":
                    continue

                if kv_item["children"] != []:

                    address = {}
                    contact = {}
                    address_key = ["addressLine1","addressLine2","postalCode","city","countryCode", "stateProvince","block"]
                    
                    parent_key = kv_item["label"]
                    
                    child_kv_dict = {}
                    
                    for child in kv_item["children"]:
                        
                        c_k = child["label"]
                        c_v = child["v"]
                        trim_idx = value_trim_reference.get(c_k, len(c_v))
                        c_v = c_v[:trim_idx]

                        
                        if c_k in address_key:
                            address[c_k] = c_v
                            
                        elif "contact" in c_k.lower().strip():
                            if "name" in c_k.lower().strip():
                                contact["name"] = c_v
                            elif "phone" in c_k.lower().strip():
                                contact["phoneNumber"] = c_v
                            elif "email" in c_k.lower().strip():
                                contact["email"] = c_v
                        else:
                             child_kv_dict[c_k] = c_v

                    if address != {}:
                        child_kv_dict["address"] = address
                    if contact != {}:
                        child_kv_dict["contact"] = contact
                    
                    if parent_key not in parties:
                        parties[parent_key] = []
                        parties[parent_key].append({"doc_type":doc_type,"doc_id":doc_id,"children":child_kv_dict})
                    else:
                        parties[parent_key].append({"doc_type":doc_type,"doc_id":doc_id,"children":child_kv_dict})
                        
                    
                    
                        
        
    processed_parties, source_document_id_list =  process_parties(parties, field_precedence_map, msg_dict)
    return processed_parties, source_document_id_list


def run_dynamic_content_creation_agent(combined_ra_json, combined_data_json, process_field):

    msg = "Dynamic content creation completed"
    updated_combined_data_json = {}
    should_run = False

    n_cst_batch_idx = None
    n_cst_doc_idx = None
    n_cst_item_idx = None
    n_cst_kv_idx = None
    n_cst_value = None

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):

        batch_id = batch_wise_data_json["id"]
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            if doc_wise_data_json["DocType"].lower().replace(" ", "").strip() == "prealert":
                for item_idx, item in enumerate(doc_wise_data_json["children"]):
                    if item["type"] == "key":
                        for kv_idx, kv in enumerate(item["children"]):
                            if kv["label"].lower().strip() == "importer":
                                for child in kv["children"]:
                                    if child["label"].lower().strip() == "block":
                                        if count_account_numbers(child["v"]) > 1:
                                            should_run = True
                                            break
                            elif kv['label'].lower().strip() == "notes.cst":
                                n_cst_batch_idx = batch_idx
                                n_cst_doc_idx = doc_idx
                                n_cst_item_idx = item_idx
                                n_cst_kv_idx = kv_idx
                                n_cst_value = kv['v']

                               
    if not should_run:
        return combined_data_json, msg
    
    _, source_document_id_dict = get_precedence_of_party(combined_data_json, process_field)
    
    selected_doc_id_importer = source_document_id_dict.get("importer", None)
    print(f" ###***## selected_doc_id_importer: {selected_doc_id_importer}")

    if not selected_doc_id_importer:
        return combined_data_json,  f"{msg}\n: No importer document found"
        
    else:
        selected_doc_id_importer = selected_doc_id_importer[0]
    
    ref_oth_val = None  

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):

        batch_id = batch_wise_data_json["id"]
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            if doc_id == selected_doc_id_importer:
                for item_idx, item in enumerate(doc_wise_data_json["children"]):
                    if item["type"] == "key":
                        for kv_idx, kv in enumerate(item["children"]):
                            if kv["label"].lower().strip() == "references.oth":
                                ref_oth_val = kv["v"]
                                break


    print(f"ref_oth_val: {ref_oth_val}")
    print(f"n_cst_value: {n_cst_value}")
    if not ref_oth_val or not n_cst_value:
        return combined_data_json, f"{msg}\n: No references.oth value found"

    
    system_prompt = f"Your Task is to replace SME ACCOUNT VAK IMPORTER value (keep value in same line of SME ACCOUNT VAK IMPORTER) with {ref_oth_val} (keep same format and structure) in a given text and return the updated modfied text only. No extra line or word"                           
    updated_text, _ = run_llm(system_prompt, n_cst_value)

    before_update = combined_data_json[n_cst_batch_idx]["nodes"][n_cst_doc_idx]["children"][n_cst_item_idx]["children"][n_cst_kv_idx]["v"]
    print(f"before_update: {before_update}")
    combined_data_json[n_cst_batch_idx]["nodes"][n_cst_doc_idx]["children"][n_cst_item_idx]["children"][n_cst_kv_idx]["v"] = updated_text
    after_update = combined_data_json[n_cst_batch_idx]["nodes"][n_cst_doc_idx]["children"][n_cst_item_idx]["children"][n_cst_kv_idx]["v"]
    print(f"after_update: {after_update}")
    return combined_data_json, f"{msg}\nUpdated notes.CST = {updated_text}"
