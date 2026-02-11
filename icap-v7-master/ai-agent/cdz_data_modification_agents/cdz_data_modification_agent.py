import copy
import os
from dotenv import load_dotenv
import requests
import re
load_dotenv()
    


def create_msg(msg_dict, field_name, txt_msg, doc_type, source_document_id_list):
    msg_dict[field_name] = { "text" : txt_msg, "docType": doc_type, "source_documentIds": source_document_id_list}


def process_general_fields(general_fields,field_precedence_map, msg_dict):

    processed_general_fields = {}

    for key, value_list in general_fields.items():

        precedence = field_precedence_map.get(key,[])

        
        selected_idx = -1
        
        if precedence != []:
            for doc_type_p in precedence:
                for field_idx, field_item in enumerate(value_list):
                    if doc_type_p == field_item["doc_type"] and field_item["value"].strip() != "":
                        selected_idx = field_idx
                        break
                if selected_idx != -1:
                    break
                    
            processed_general_fields[key] =  value_list[selected_idx]["value"]
        
            txt_msg = f"This was extracted from {value_list[selected_idx]['doc_type']} according to precedence."
            text_msg_doc_type = value_list[selected_idx]["doc_type"]
            source_document_id_list = [value_list[selected_idx]["doc_id"]]

            if len(value_list) == 1:
                txt_msg = f"{txt_msg} No other value found rather than this."
                
            for field_idx, field_item in enumerate(value_list):
                if  selected_idx == field_idx:
                    continue
                else:
                    txt_msg = f"{txt_msg} Ignored value {field_item['value']} form {field_item['doc_type']}."
    
            create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
        else:
            
            
            selected_idx = -1
            
            for i in range(len(value_list)-1, -1, -1):
                if value_list[i]["value"] != "":
                    selected_idx = i
                    break

            if selected_idx == -1:
                
                txt_msg = f"No precedence was given, this key is skipped since all values are empty."
                text_msg_doc_type = "No doc class found"
                source_document_id_list = []
                create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
            else:
                processed_general_fields[key] =  value_list[selected_idx]["value"]
        
                txt_msg = f"No precedence was given hence this was extracted from {value_list[selected_idx]['doc_type']} as per last occurance."
                text_msg_doc_type = value_list[selected_idx]["doc_type"]
                source_document_id_list = [value_list[selected_idx]["doc_id"]]

                if len(value_list) == 1:
                    txt_msg = f"{txt_msg} No other value found rather than this."
                
                for field_idx, field_item in enumerate(value_list):
                    if  selected_idx == field_idx:
                        continue
                    else:
                        txt_msg = f"{txt_msg} Ignored value {field_item['value']} form {field_item['doc_type']}."
        
                create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
                
                    
    return processed_general_fields

### Exception party handling block start

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



#### Exception party handling block end


def process_parties(parties,field_precedence_map, msg_dict):

    processed_parties = {}

    for key, value_list in parties.items():

        precedence = field_precedence_map.get(key,[])
        selected_idx = -1

        exception_msg = ""

        if precedence != []:
            for doc_type_p in precedence:
                for field_idx, field_item in enumerate(value_list):
                    if doc_type_p == field_item["doc_type"] and field_item["children"] != {}:

                        #if key.lower().strip()  == "importer" and count_account_numbers(field_item.get("children",{}).get("address",{}).get("block",""))>= 2:
                        if key.lower().strip()  == "importer" and field_item.get("doc_type","").lower().replace(" ","").strip() == "prealert" and count_account_numbers(field_item.get("children",{}).get("address",{}).get("block",""))>= 2:
                            exception_msg += f" Important Note: Precedence is breaking because either multiple account numbers are present or the account number contains more than 8 characters in {field_item['doc_type']}, hence it is being ignored."
                            continue

                        selected_idx = field_idx
                        break
                if selected_idx != -1:
                    break

            if selected_idx == -1 :
                create_msg(msg_dict, key, "No valid value found according to precedence", "None" , [])
                continue
                   
            processed_parties[key] =  value_list[selected_idx]["children"]
        
            txt_msg = f"This was extracted from {value_list[selected_idx]['doc_type']} according to precedence."
            text_msg_doc_type = value_list[selected_idx]["doc_type"]
            source_document_id_list = [value_list[selected_idx]["doc_id"]]

            if len(value_list) == 1:
                txt_msg = f"{txt_msg} No other value found rather than this."
                
            for field_idx, field_item in enumerate(value_list):
                if  selected_idx == field_idx:
                    continue
                else:
                    txt_msg = f"{txt_msg} Ignored value {field_item['children']} form {field_item['doc_type']}."
            txt_msg += exception_msg
            create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
        else:
            
            
            selected_idx = -1
            
            for i in range(len(value_list)-1, -1, -1):
                if value_list[i]["children"] != {}:

                    if key.lower().strip() == "importer" and value_list[i].get("doc_type","").lower().replace(" ","").strip() == "prealert" and count_account_numbers(value_list[i].get("children",{}).get("address",{}).get("block",""))>= 2:
                        exception_msg += f" Important Note: Last occurance rule is breaking because either multiple account numbers are present or the account number contains more than 8 characters in {value_list[i]['doc_type']}, hence it is being ignored."
                        continue

                    selected_idx = i
                    break

            if selected_idx == -1:
                
                txt_msg = f"No precedence was given, this key is skipped since all values are empty."
                text_msg_doc_type = "No doc class found"
                source_document_id_list = []
                create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
            else:
                processed_parties[key] =  value_list[selected_idx]["children"]
        
                txt_msg = f"No precedence was given hence this was extracted from {value_list[selected_idx]['doc_type']} as per last occurance."
                text_msg_doc_type = value_list[selected_idx]["doc_type"]
                source_document_id_list = [value_list[selected_idx]["doc_id"]]

                if len(value_list) == 1:
                    txt_msg = f"{txt_msg} No other value found rather than this."
                
                for field_idx, field_item in enumerate(value_list):
                    if  selected_idx == field_idx:
                        continue
                    else:
                        txt_msg = f"{txt_msg} Ignored value {field_item['children']} form {field_item['doc_type']}."
                txt_msg += exception_msg
                create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
                
                    
    return processed_parties





# def process_parties(parties,field_precedence_map, msg_dict):

#     def index_of_last_max(values):
#         max_value = max(values)
#         return len(values) - 1 - values[::-1].index(max_value)

#     processed_parties = {}
    
#     for key, value_list in parties.items():
        
#         score_list = []
#         for child_value_list in value_list:
            
#             has_name = False
#             has_account_number = False
            
#             for inner_child_idx, inner_child in enumerate(child_value_list["children"]):

#                 inner_child_key = list(inner_child.keys())[0]
#                 inner_child_value = list(inner_child.values())[0]
#                 if inner_child_key == "name":
#                     has_name = True
#                 elif inner_child_key == "accountNumber":
#                     has_account_number = True
                    
#             if has_name and has_account_number:
#                 score_list.append(2)
#             elif has_name:
#                 score_list.append(1)
#             else:
#                 score_list.append(0)
    
#         desired_party_idx = index_of_last_max(score_list)   
#         processed_parties[key] = value_list[desired_party_idx]["children"]
    
#     return processed_parties




# def process_housebill_fields(housebill_fields,field_precedence_map, msg_dict):

#     processed_housebill_fields = {}

#     for key, value_list in housebill_fields.items():

#         precedence = field_precedence_map.get(key,[])

        
#         selected_idx = -1
        
#         if precedence != []:
#             for doc_type_p in precedence:
#                 for field_idx, field_item in enumerate(value_list):
#                     if doc_type_p == field_item["doc_type"] and field_item["value"] != "":
#                         selected_idx = field_idx
#                         break
#                 if selected_idx != -1:
#                     break
                    
#             processed_housebill_fields[key] =  value_list[selected_idx]["value"]
        
#             txt_msg = f"This was extracted from {value_list[selected_idx]["doc_type"]} according to precedence."
#             text_msg_doc_type = value_list[selected_idx]["doc_type"]
#             source_document_id_list = [value_list[selected_idx]["doc_id"]]

#             if len(value_list) == 1:
#                 txt_msg = f"{txt_msg}. No other value founded ratherthan this."
                
#             for field_idx, field_item in enumerate(value_list):
#                 if  selected_idx == field_idx:
#                     continue
#                 else:
#                     txt_msg = f"{txt_msg} Ignored value {field_item["value"]} form {field_item["doc_type"]}."
    
#             create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
#         else:
            
            
#             selected_idx = -1
            
#             for i in range(len(value_list)-1, -1, -1):
#                 if value_list[i]["value"] != "":
#                     selected_idx = i
#                     break

#             if selected_idx == -1:
                
#                 txt_msg = f"No precedence was given, this key is skipped since all the key has empty values"
#                 text_msg_doc_type = "No doc class found"
#                 source_document_id_list = []
#                 create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
#             else:
#                 processed_housebill_fields[key] =  value_list[selected_idx]["value"]
        
#                 txt_msg = f"No precedence was given hence this was extracted from {value_list[selected_idx]["doc_type"]}. as per last occurance"
#                 text_msg_doc_type = value_list[selected_idx]["doc_type"]
#                 source_document_id_list = [value_list[selected_idx]["doc_id"]]

#                 if len(value_list) == 1:
#                     txt_msg = f"{txt_msg}. No other value founded rather than this."
                
#                 for field_idx, field_item in enumerate(value_list):
#                     if  selected_idx == field_idx:
#                         continue
#                     else:
#                         txt_msg = f"{txt_msg} Ignored value {field_item["value"]} form {field_item["doc_type"]}."
        
#                 create_msg(msg_dict, key, txt_msg, text_msg_doc_type , source_document_id_list)
                
                
    
#     return processed_housebill_fields



# def process_housebill_fields_old(housebill_fields):
    
#     def index_of_last_max(values):
#         max_value = max(values)
#         return len(values) - 1 - values[::-1].index(max_value)
        
#     processed_housebill_fields = {}

#     for key, value_list in housebill_fields.items():
#         if len(value_list) == 1:
#             processed_housebill_fields[key] = value_list[0]["value"]
#         else:
#             score_list = []
#             for item in value_list:
#                 if item["doc_type"].lower().replace(" ","").strip() == "hosuewaybill":
#                     score_list.append(2)
#                 elif item["doc_type"].lower().replace(" ","").strip() == "commercialinvoice":
#                     score_list.append(1)
#                 else:
#                     score_list.append(0)
                    
#             desired_idx = index_of_last_max(score_list)
#             desired_value = value_list[desired_idx]["value"]
            
#             processed_housebill_fields[key] = desired_value
                    
                

#     return processed_housebill_fields

    
def get_field_precedence_dict(process_keys):


    field_precedence_map = {}
    for item in process_keys:
        item_precedence = item.get("precedence", [])
        if item_precedence == {}:
            item_precedence = []
        field_precedence_map[item["keyValue"]] = item_precedence
    return field_precedence_map



def run_cdz_data_modification_agent(combined_data_json, process_keys):

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
                                contact["phone"] = c_v
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
                        
                # elif "housebill" in  kv_item["label"].lower().strip():
                #     key = kv_item["label"]
                #     value = kv_item["v"] 
                #     if key not in housebill_fields:
                #         housebill_fields[key] = []
                #         housebill_fields[key].append({"doc_type":doc_type,"doc_id":doc_id,"value" : value})
                #     else:
                #         housebill_fields[key].append({"doc_type":doc_type,"doc_id":doc_id,"value" : value})
                    
                    
                else:
                    key = kv_item["label"]
                    value = kv_item["v"]

                    if value.strip() == "":
                        continue
                    
                    if key not in general_fields:
                        general_fields[key] = []
                        general_fields[key].append({"doc_type":doc_type,"doc_id":doc_id, "value" : value})
                    else:
                        general_fields[key].append({"doc_type":doc_type,"doc_id":doc_id, "value" : value})
                        
        
    general_fields =  process_general_fields(general_fields,field_precedence_map, msg_dict)
    # housebill_fields = process_housebill_fields(housebill_fields,ield_precedence_map, msg_dict)
    #print(general_fields)
    


    parties =  process_parties(parties, field_precedence_map, msg_dict)


    
  
    
    # housebill_fields = process_housebill_fields(housebill_fields)
    
    
    flatten_kv.update(general_fields)
    flatten_kv.update(parties)
    
    # flatten_data_json_agent.update(housebill_fields)

    for doc_id, table in doc_wise_table.items():
        table_name =  table["table_name"]
        rows = table["children"]
        single_table = {"rows":[]}
        for row in rows:
            single_row = {}
            for col_item in row["children"]:
                single_row[col_item["label"]]= col_item["v"]
            single_table["rows"].append(single_row)
        flatten_table.append(single_table)

    
            
            
   
    return {"data":flatten_kv, "main_table": flatten_table, "metadata": {"messages":msg_dict}}