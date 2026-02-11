
"""

def get_exception_handled_data(vendor_definition, data_json):


    for kv in data_json["key_data"][:]:
        if kv["is_data_exception_done"]:
            data_json["key_data"].remove(kv)

    if vendor_definition == {}:
        return data_json

    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
    except:
        data_exception_list = []
        pass

    try:   
        for idx, item in enumerate(data_exception_list):
            
            new_kv_pair = {
                "is_data_exception_done": True,
                "key": item["label"],
                "key_position": f"{item['field']['selectorPosition']['startPos']},{item['field']['selectorPosition']['topPos']},{item['field']['selectorPosition']['endPos']},{item['field']['selectorPosition']['bottomPos']}",
                "original_key": item["label"],
                "page_id": item["value"]['selectorPosition']["pageId"],
                "value": item["value"]["text"],
                "value_position": f"{item['value']['selectorPosition']['startPos']},{item['field']['selectorPosition']['topPos']},{item['field']['selectorPosition']['endPos']},{item['field']['selectorPosition']['bottomPos']}"

                }
            
            data_json["key_data"].append(new_kv_pair)
        
    except:
        return data_json
        pass

    return data_json



from rapidfuzz import fuzz

def get_injected_prompt_for_data_exception(vendor_definition):

    missing_fileds = []
    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
        
    except:
        data_exception_list = []
        pass

    #try:   
    for idx, item in enumerate(data_exception_list):
        print("Data Exception #######", item['field']['text'])
        missing_fileds.append(item['field']['text'])

    if  missing_fileds == []:
        return ""
    else:
        return f"\n\n ### Extract the key value pairs for the key {missing_fileds} if they are or it is present."
    #except:
        #return ""
        #pass



def get_marked_data_exception_handled_kv(vendor_definition,data_json):

    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
    except:
        data_exception_list = []
        pass
    
    try:
        for idx, item in enumerate(data_exception_list):
            for kv in data_json["key_data"]:
                if fuzz.ratio(kv["original_key"].strip(), item['filed']['text']) >= 95:
                    kv["is_data_exception_done"] = True
        return data_json
    except:
        return data_json
        pass
"""


import os
import requests
import json
from rapidfuzz import fuzz
import copy
import re
from xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old
from position_adder import add_postion_information_to_key_value_vendor

LLM_SERVICE_API_URL = os.getenv("LLM_SERVICE_API_URL")

PROMPT_TEMPLATE = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"


SAMPLING_PARAM_KVV_LLM = {
                          "temperature":0,
                          "max_tokens":20000,
                          "type" : "normal"
                          }

SAMPLING_PARAM_TABLE_LLM = {
                          "temperature":0,
                          "max_tokens":25000,
                          "type" : "normal"
                          }

SAMPLING_PARAM_GENERAL_LLM = {
                            "temperature":0,
                            "max_tokens":10000,
                            "stop" : ["<|eot_id|>"],
                            "top_k" : 150,
                            "top_p" : 0.9,
                          }



SAMPLING_PARAM_KVV_LLM_FOR_MISSING_KEY = {
                                        "temperature":0.7,
                                        "max_tokens":20000,
                                        "stop" : ["<|eot_id|>"],
                                        "top_k" : 100,
                                        "top_p" : 0.8,
                                        "type" : "normal"
                                        }

SAMPLING_PARAM_TABLE_LLM_FOR_MISSING_TABLE = {
                                        "temperature":0.8,
                                        "max_tokens":25000,
                                        "stop" : ["<|eot_id|>"],
                                        "top_k" : 100,
                                        "top_p" : 0.8,
                                        "type" : "creative"
                                        }



def get_llm_result_data_exception_kvv(layout_paths,ra_json,is_ra_json_available, system_prompt_data_exception):

    page_ids = []
    llm_result = {}
    prompts = []

    if is_ra_json_available:

        for  page_idx, page in enumerate(ra_json["pages"]):
            page_id = page["id"]
            page_wise_paragraph = get_ra_json_to_txt_kvv(page)
            if page_wise_paragraph == "":
                continue
            page_ids.append(page_id)
            prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_data_exception, prompt = page_wise_paragraph+"\n\n"+system_prompt_data_exception)
            prompts.append(prompt)
    else:
        for layout_path in layout_paths:

            page_id = layout_path.replace("_layout.xml", "")[-8:] 
            
            page_wise_paragraph = get_xml_to_text(layout_path)
            if page_wise_paragraph == "":
                continue
            page_ids.append(page_id)
            prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_data_exception, prompt = page_wise_paragraph+"\n\n"+system_prompt_data_exception)
            prompts.append(prompt)
        
    
    #outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_kvv",json = {"prompts":prompts})
    print("##################************",SAMPLING_PARAM_KVV_LLM)
    outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_kvv",json = {"prompts":prompts,"sampling_param":SAMPLING_PARAM_KVV_LLM})
    outputs = outputs.json()
    outputs = outputs["llm_result_kvv"]
    

    for idx, output in enumerate(outputs):
        llm_result[page_ids[idx]] = output
    
    return llm_result



def get_system_prompt_prompt_for_data_exception_kvv(vendor_definition):

    missing_fields = []
    missing_fields_associated_labels = []
    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
        
    except:
        data_exception_list = []
        pass

    try:   
        for idx, item in enumerate(data_exception_list):
            if item["type"] != "table":
                missing_fields.append(item['value']['text'])
                missing_fields_associated_labels.append(item["label"])
        if  missing_fields == []:
            return "", [], []
        else:
            return f"""You are an AI assistant to extract key value pairs for missing keys.
                    ## Missig Key list : [{', '.join(missing_fields)}]
                    ## Your task is to extract key value pairs of these missing keys from the given data.
                    ## Output Format: 
                        [
                        {{"key":"Missing Key1","value":"Value1 associated to misssing Key1"}}, 
                        {{"key":"Missing Key2","value":"Value2 associated to misssing Key2"}}, 
                        ...
                        ]
                    ### DO NOT FORGET TO EXTRACT THE MISSING THE KEY VALUE PAIRS ASSOCIATED TO THE KEYS [{', '.join(missing_fields)}]
                    """, missing_fields, missing_fields_associated_labels

    except:
        return "", [], []
        pass



def format_key_value(page_id, key_value_data):
    result = []
    
    if "key" in key_value_data and "value" in key_value_data:
        
        for kv in key_value_data.split("}"):
            try:
                k,v = kv.split("value")
            except:
                continue
                pass
            try:
                k = k.split("key")[1].replace('"','').replace(':','').replace("'",'').strip()[:-1]
            except:
                k = k.replace('"','').replace(':','').replace("'",'').strip()[:-1]
                pass
            v = v.replace('"','').replace("'",'').replace(':','').strip()
            
            result.append({
                            "key": k.strip(),
                            "key_position": "0,0,0,0",
                            "value": v.strip(),
                            "value_position": "0,0,0,0",
                            "page_id": page_id,
                            "original_key":k.strip(),
                            "is_label_mapped":False,
                            "is_profile_key_found":False,
                            "is_data_exception_done": False
                            })
            
    else:
   
        key_value_data = key_value_data.strip("[]").replace("\n", "").replace("    ", " ")
        pattern = r'"([^"]+)":\s*"([^"]+)"'
        matches = re.findall(pattern, key_value_data)
        
        for kv in matches:
            k,v = kv[0],kv[1]
            
            result.append({
                            "key": k.strip(),
                            "key_position": "0,0,0,0",
                            "value": v.strip(),
                            "value_position": "0,0,0,0",
                            "page_id": page_id, 
                            "original_key":k.strip(),
                            "is_label_mapped":False,
                            "is_profile_key_found":False,
                            "is_data_exception_done": False
                            })
        
            
    return result



def get_formatted_llm_kvv_data_exception(results):
    
    key_value_pairs = []
    for page_id, result in results.items():
        
        result = result.replace("\n","")
        try:
            vendor_data = result.split("key-value")[0]
        except:
            vendor_data = ""
            pass
        try:
            key_value_data = result.split("key-value")[1]
        except:
            key_value_data = result
            pass

        key_value_pairs_page_wise = format_key_value(page_id, key_value_data)
        
        if key_value_pairs == []:
            key_value_pairs = key_value_pairs_page_wise
        else:
            for kv_new in key_value_pairs_page_wise:
                k_new = kv_new["key"]
                v_new = kv_new["value"]
                
                is_key_val_unique = True
                for kv_old in key_value_pairs:
                    k_old = kv_old["key"]
                    v_old = kv_old["value"]
                    key_matched_score = fuzz.ratio(k_old.lower(), k_new.lower())
                    value_matched_score = fuzz.ratio(v_old.lower(), v_new.lower())
                    if  key_matched_score >= 90 and  value_matched_score >= 90:
                         is_key_val_unique = False
                
                if is_key_val_unique:
        
                    key_value_pairs.append(kv_new)
                    
    return key_value_pairs



def get_exception_handled_data_json_for_key(layout_paths,ra_json,is_ra_json_available, vendor_definition, data_json):


    missing_kv_result = []

    system_prompt_data_exception, missing_fields, missing_fields_associated_labels = get_system_prompt_prompt_for_data_exception_kvv(vendor_definition)

    if system_prompt_data_exception == "":

        return data_json, data_json
    else:

        llm_result_dict_data_exception = get_llm_result_data_exception_kvv(layout_paths,ra_json,is_ra_json_available, system_prompt_data_exception)
       
        formatted_llm_result_list_data_exception = get_formatted_llm_kvv_data_exception(llm_result_dict_data_exception)

        for idx_missing_key, missing_item in enumerate(missing_fields):

            founded_missing_item = {}
            for idx, kv in enumerate(formatted_llm_result_list_data_exception):
                if missing_item.strip()[-1] == ":":
                    missing_item = missing_item[:-1].strip()

                if fuzz.ratio(kv["original_key"].strip(), missing_item.strip()) >= 95:
                    founded_missing_item = copy.deepcopy(kv)
                    break
            
            if founded_missing_item != {}:
                founded_missing_item["is_data_exception_done"] = True
                founded_missing_item["key"] = missing_fields_associated_labels[idx_missing_key]
                missing_kv_result.append(founded_missing_item)
        

    temp_data_json = {"vendor":{"vendor": "","vendor_position": "0,0,0,0","page_id": ""}, "key_data":missing_kv_result}
    missing_kv_result_with_position_data_json, _ = add_postion_information_to_key_value_vendor(layout_paths,ra_json,is_ra_json_available,temp_data_json)
    missing_kv_result_with_position_data_list = missing_kv_result_with_position_data_json["key_data"]
    
    data_json_exception_handled = copy.deepcopy(data_json)

    for item_idx, item in enumerate(missing_kv_result_with_position_data_list):
        for kv_idx, kv in enumerate(data_json["key_data"]):
            if item["key"].strip() == kv["key"].strip():
                data_json_exception_handled["key_data"].remove(kv)
                item["is_profile_key_found"] = True
                data_json_exception_handled["key_data"].append(item)
    

    return data_json_exception_handled, data_json





######################################### code divider ############################################


def get_system_prompt_prompt_for_data_exception_table(vendor_definition):


    #table_exception_column_list = vendor_definition["settings"]["table_exceptions"]["keys"]
    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
        
    except:
        data_exception_list = []
        pass
    
    missing_col_list = []
    missing_col_mapped_label_list = []
    for item in data_exception_list:
        if item["type"] != "table":
            continue

        try:
            missing_col_list.append(item["value"]["text"])
            missing_col_mapped_label_list.append(item["label"])
        except:
            pass

    sub_prompt = f"## YOU MUST EXTRACT THE VALUES OF THE COLUMNS {missing_col_list} IF THEY ARE AVAILAVLE IN ANY TABLE"

    if missing_col_list == []:
        return "",sub_prompt, missing_col_list, missing_col_mapped_label_list


    system_prompt_table_exception = """You are an AI language model designed to extract all table data from given text documents.The given text has appropiate spacing between word and sentence and contains multiple pages so that you can understand the document layout very appropiately.

    ## Tasks
        - Extract all Tables from the document, including any that appear at the beginning.
        - For each table, capture all column headers of the table and Each row's data, where values can span one or multiple lines.
        - Assign appropriate labels from the headers to each value.
        - Include All Tables: Ensure that no tables are omitted.
        - Extract any summary information (totals, subtotals, VAT/tax) into a separate summary_table.
        - Handle Multiple Tables across Multiple Pages appropriately.
        - If a table continues in multiple pages handle it appropiately.
        
    ### Output Format:
    {
        'Table 1': {
            'row1': [['value 1 from row 1', 'column label for value 1'], ['value 2 from row 1', 'column label for value 2'], //Other Values ],
            'row2': [['value 1 from row 2', 'column label for value 1'], ['value 2 from row 2', 'column label for value 2'], //Other Values ],
            //Other rows
        },
        ...  # Repeat for other tables
        'Summary Table 1': {
            'row1': [['summary value 1', 'summary label 1 of value 1'],['summary value 2', 'summary label 2 of value 2'], //Other Values]  # Include all summary data if presents
        }
    }
    
    ## Importants
    - DO NOT ADD EXTRA WORDS or SENTENCES FROM YOU WHEN YOU GENERATE THE OUTPUT, ONLY GENERATE THE JSON WITH APPROPIATE STRUCTURE MENTIONED in output format without any extra data.
    - Very Deeply analysis the document to extract all the tables correctly.   
    """
           

    return system_prompt_table_exception +"\n\n"+ sub_prompt, sub_prompt, missing_col_list, missing_col_mapped_label_list





def get_llm_result_table_data_exception(layout_paths,ra_json,is_ra_json_available, system_prompt_table_exception, sub_prompt):

    page_ids = []
    llm_result = []
    prompts = []
    prompt_hub = []
    sampling_rate = 15
    
    if is_ra_json_available:
            
        sampling_rate = len(ra_json["pages"])

        if len(ra_json["pages"])> 50:
            sampling_rate = 7
        elif len(ra_json["pages"])> 15:
            sampling_rate = 15
        
        batch_text = ""
        
        
        for  page_idx, page in enumerate(ra_json["pages"]):
            page_wise_paragraph_table = get_ra_json_to_txt_table_old(page)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_table_exception, prompt = batch_text + "\n\n" + sub_prompt)
                prompts.append(prompt)
                batch_text = ""
            elif page_idx+1 == len(ra_json["pages"]):
                prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_table_exception, prompt = batch_text + "\n\n" + sub_prompt)
                prompts.append(prompt)
                batch_text = ""
    else:
        sampling_rate = len(layout_paths)

        if len(layout_paths)> 50:
            sampling_rate = 7
        elif len(layout_paths)> 15:
            sampling_rate = 15
            
        batch_text = ""
        for page_idx, layout_path in enumerate(layout_paths):
            page_wise_paragraph_table = get_xml_to_text(layout_path)
            if page_wise_paragraph_table == "":
                continue
            if batch_text == "":
                batch_text = page_wise_paragraph_table
            else:
                batch_text = f"{batch_text}\n\n\n{page_wise_paragraph_table}"
                
            if (page_idx+1)%sampling_rate == 0:
                prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_table_exception, prompt= batch_text + "\n\n" + sub_prompt)
                prompts.append(prompt)
                batch_text = "" 
            elif page_idx+1 == len(layout_paths):
                prompt = PROMPT_TEMPLATE.format(system_prompt = system_prompt_table_exception, prompt= batch_text + "\n\n" + sub_prompt)
                prompts.append(prompt)
                batch_text = ""

    sub_prompt_hub = []
    
    for p_idx, p in enumerate(prompts):
        sub_prompt_hub.append(p)

        if (p_idx+1)%6 == 0:
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
        elif p_idx+1 == len(prompts):
            prompt_hub.append(sub_prompt_hub)
            sub_prompt_hub = []
            
        
    for prompt_list in prompt_hub:
        
        #outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list})
        outputs = requests.post(f"{LLM_SERVICE_API_URL}/llm_service_table",json = {"prompts":prompt_list, "sampling_param":SAMPLING_PARAM_TABLE_LLM})
        outputs = outputs.json()
        outputs = outputs["llm_result_table"]

        for out in outputs:
            llm_result.append(out)
            
    return llm_result







def get_formatted_llm_single_table_data_manual(input_str):
    
    
    def make_table(tables,table_name,table_idx,results):
        
        for table_id, table in enumerate(tables):
            single_table = {"table_id":table_idx,"table_name":f"{table_name} {table_idx+1}","table_data":{"rows":[]}}
            table_idx += 1
            rows = table.split("row")[1:]

            for row_id, row in enumerate(rows):
                single_row = {"row_id":row_id,"row_data":[]}
                list_pattern = r"\[.*?\]"
                row_items = re.findall(list_pattern, row, re.DOTALL)
                for item_id, item in enumerate(row_items):
                    if item_id == 0:
                        item = item[1:]
                    try:
                        try:
                            value = item.split("', '")[0].replace("['","").strip()
                            label = item.split("', '")[1].replace("']","").strip()
                            single_row["row_data"].append({"value":value,"label":label})
                        except:
                            value = item.split('", ')[0].replace("['","").strip()
                            label = item.split('", ')[1].replace("']","").strip()
                            single_row["row_data"].append({"value":value,"label":label})
                            pass
                    except:
                        pass
                
                single_table["table_data"]["rows"].append(single_row)
            results["table_data"].append(single_table)
        return table_idx, results
        
    
    
    table_idx = 0
    results = {"table_data":[]}
    all_tables = input_str.split("Table ")[1:]
    summary_table_names = []
    general_table_names = []
    summary_tables = []
    general_tables = []
    
    for t_id, t in enumerate(all_tables):
        if t_id > 0 and all_tables[t_id-1].strip().endswith("Summary"):
            summary_tables.append(t)
            summary_table_names.append(f"Summary Table {t.strip()[0]}")
            
    
    for t_id, t in enumerate(all_tables):
        if t not in summary_tables:
            general_tables.append(t)
            general_table_names.append(f"Table {t.strip()[0]}")
    
    
    table_names = general_table_names + summary_table_names
    
    table_idx, results = make_table(general_tables,"Table",table_idx,results)
    table_idx, results = make_table(summary_tables,"Summary Table",table_idx,results)
    
    
    for idx, table in enumerate(results["table_data"]):
        table["table_name"] = table_names[idx]

    return results




def get_formatted_llm_single_table_data_auto(input_str):
    input_str_main = input_str
    try:

        def extract_json(data_str):
            match = re.search(r"{.*}", data_str, re.DOTALL)
            if match:
                json_str = match.group(0)
                json_str = json_str.replace("'", "\"")
                
                return json.loads(json_str)
                
            
            
        input_str = extract_json(input_str)
        
        results = {"table_data":[]}
        table_idx = 0
        for table_name, table_rows in  input_str.items():
            single_table = {"table_id":table_idx,"table_name":table_name,"table_data":{"rows":[]}}
            table_idx += 1
            for row_id, row_data in enumerate(table_rows.values()):
                single_row = {"row_id":row_id,"row_data":[]}
                for item in row_data:
                    single_row["row_data"].append({"value":item[0],"label":item[1]})
                single_table["table_data"]["rows"].append(single_row)
            results["table_data"].append(single_table)
        
        return results
    except:
        return get_formatted_llm_single_table_data_manual(input_str_main)
        pass





def get_formatted_llm_table_data(tables_str_list):

    def get_header_matching_score(table_headers,table_r_headers):
        total_matched = 0
        for th in table_headers:
            for trh in table_r_headers:
                score = fuzz.ratio(th.lower(), trh.lower())
                if score >= 90:
                    total_matched += 1
        total_avg_header_count = (len(table_headers)+len(table_r_headers))/2

        final_score = (total_matched/total_avg_header_count)*100
        return final_score
        
        
    
    result = []
    
    all_tables = []
    for tables_str in tables_str_list:
        batch_wise_tables = get_formatted_llm_single_table_data_auto(tables_str)
        for formatted_table in batch_wise_tables["table_data"]:
            all_tables.append(formatted_table)
    
    for table in all_tables:
        
        if result == []:
            result.append(table)
            continue
        #elif "summary" in table["table_name"].lower():
        #    result.append(table)
        #    continue
        else:
            result_temp = copy.deepcopy(result)
            is_matched = False
            unique_tables = []
            for table_r in result_temp:
                #if "summary" in table_r["table_name"].lower():
                #    continue
                table_headers = [row_data["label"] for row_data in table["table_data"]["rows"][0]["row_data"]]
                table_r_headers = [row_data["label"] for row_data in table_r["table_data"]["rows"][0]["row_data"]]
                matching_score = get_header_matching_score(table_headers,table_r_headers)
                if matching_score >= 70:
                    is_matched = True
                    row_list_len = len(table_r["table_data"]["rows"])
                    for idx, new_row in enumerate(table["table_data"]["rows"]):
                        new_row["row_id"]= row_list_len+idx
                        table_r["table_data"]["rows"].append(copy.deepcopy(new_row))
            if not is_matched:
                unique_tables.append(copy.deepcopy(table))
            result = result_temp + unique_tables
            
    general_table_idx = 1
    summary_table_idx = 1

    for idx, processed_table in enumerate(result):
        if "summary" in processed_table["table_name"].lower():
            processed_table["table_name"] = f"Summary Table {summary_table_idx}"
            processed_table["table_id"] = idx
            summary_table_idx += 1
        else:
            processed_table["table_name"] = f"Table {general_table_idx}"
            general_table_idx += 1
            processed_table["table_id"] = idx
    
    return {"table_data":result}












def get_exception_handled_data_json_for_table(layout_paths,ra_json,is_ra_json_available, vendor_definition, modified_data_json_based_on_data_exception):

    actual_table_list = modified_data_json_based_on_data_exception["table_data"]

    """
    try:
        data_exception_list = vendor_definition["settings"]["data_exceptions"]
    except:
        data_exception_list = []
        pass

    for table_idx, table in enumerate(table_list):
            row_data = table["table_data"]["rows"]
            for row_idx, single_row_data in enumerate(row_data):
                single_row = single_row_data["row_data"]
                for col_id, col_data in enumerate(single_row):
                    for item in data_exception_list:
                        if item["type"] != "table":
                            continue
                        if item["label"].lower().strip() == col_data["label"].lower().strip():
                            col_data["value"] = item["value"]
                            col_data["is_data_exception_done"] = True
                            col_data["is_profile_key_found"] = True
                   
    """
    
    
    system_prompt_table_exception, sub_prompt, missing_col_list, missing_col_mapped_label_list = get_system_prompt_prompt_for_data_exception_table(vendor_definition)
    
    if missing_col_list == []:
        return  modified_data_json_based_on_data_exception

    llm_result_data_exception_table = get_llm_result_table_data_exception(layout_paths,ra_json,is_ra_json_available, system_prompt_table_exception, sub_prompt)
    llm_result_data_exception_table = get_formatted_llm_table_data(llm_result_data_exception_table)

    exception_handled_table = llm_result_data_exception_table["table_data"]


    for table_idx, table in enumerate(exception_handled_table):
            row_data = table["table_data"]["rows"]
            for row_idx, single_row_data in enumerate(row_data):
                single_row = single_row_data["row_data"]
                for col_id, col_data in enumerate(single_row):
                    for item_idx, item in enumerate(missing_col_list):
                        if fuzz.ratio(item.lower(),col_data["label"].lower()) >= 95:
                            is_col_already_process = False
                            for col_data_actual_idx, col_data_actual in enumerate(actual_table_list[table_idx]["table_data"]["rows"][row_idx]["row_data"]):
                                if col_data_actual["label"] == missing_col_mapped_label_list[item_idx] and col_data_actual["value"].strip() == "":
                                    col_data_actual["value"] = col_data["value"]
                                    col_data_actual["is_data_exception_done"] = True
                                    col_data_actual["is_profile_key_found"] = True
                                    col_data_actual ["position"] = "0,0,0,0"
                                    is_col_already_process = True

                            if not is_col_already_process:
                                actual_table_list[table_idx]["table_data"]["rows"][row_idx]["row_data"].append({"value":col_data["value"],"label":missing_col_mapped_label_list[item_idx],"position":"0,0,0,0","is_data_exception_done":True,"is_profile_key_found":True})

    return  modified_data_json_based_on_data_exception