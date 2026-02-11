import os
import requests
import json
from dotenv import load_dotenv
from llm_clients import run_llm
from xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
import copy  
load_dotenv()

vector_data_base_url = os.getenv("VECTOR_DATA_BASE_API")
DATA_BASE_ID = "scenarios"


def get_system_prompt_scenarios(carrier_list):
    system_prompt_scenarios = """
    You are a document classification agent that determines the subDocClass based on transport mode and carrier matching.
    
    Your task is to analyze the given document text and return ONLY a JSON response with the subDocClass value.
    
    ## Classification Logic:
    
    1. **Identify Mode of Transport**
       - If the document indicates air transport → modeOfTransport = "AIR"
       - If the document indicates sea/ocean transport → modeOfTransport = "SEA"
    
    2. **Check Carrier Matching**
       - Search for carriers from the provided carrier list in the document text
       - Each carrier has an associated modeOfTransport (AIR or SEA)
    
    3. **Determine subDocClass**
       - If a carrier is found AND its modeOfTransport matches the document's transport mode:
         * modeOfTransport = "SEA" → subDocClass = "MBL"
         * modeOfTransport = "AIR" → subDocClass = "HBL"
       - If no carrier match is found → subDocClass = "None"
    
    ## Carrier List:
    {carrier_list}
    
    ## Output Format:
    {{
      "subDocClass": "MBL" | "HBL" | "None"
    }}
    
    IMPORTANT: Return ONLY the JSON object. No explanations, reasoning, or additional text.
    """
    
    
    formatted_prompt = system_prompt_scenarios.format(carrier_list=carrier_list)
    return  formatted_prompt





def query_auto_match(process, table, query_data, top_k=5, threshold=0.7):
    
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



def convert_shipping_to_transport(data):
  
    result = data.copy()
    transport_mapping = {
        "N": "AIR",
        "Y": "SEA"
    }
    
    if "results" in result:
        for item in result["results"]:
            if "columns" in item and "shippingLine" in item["columns"]:
                shipping_line = item["columns"]["shippingLine"]
                
                mode_of_transport = transport_mapping.get(shipping_line, shipping_line)
                
                del item["columns"]["shippingLine"]
                item["columns"]["modeOfTransport"] = mode_of_transport
    
    return result





def get_top_five_match(payload: dict) -> dict:
    
    if not payload or "results" not in payload or not payload["results"]:
        return {}
    
    payload = convert_shipping_to_transport(payload)

    sorted_entries = sorted(payload["results"], key=lambda x: x.get("score", 0), reverse=True)
    if len(sorted_entries) > 5:
        sorted_entries = sorted_entries[:5]

    top_entry = sorted_entries[0]
    

    if top_entry.get("score",0) == 1.0:
        return [top_entry.get("columns", {})]
    else:
        result = []
        for item in sorted_entries:
            result.append(item.get("columns", {}))
        return result


def get_defined_ra_json_txt(ra_json_combined, id):
    selected_ra_json = {}
    for ra_json in ra_json_combined["nodes"]:
        if ra_json["id"] == id:
            selected_ra_json = ra_json
            break

    
    user_content = ""
    
    for  page_idx, page in enumerate(selected_ra_json["children"]):
      page_wise_paragraph = get_ra_json_to_txt_table_new(page)
        
      if user_content == "":
        user_content =f"########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"
      else:
        user_content = f"{user_content}\n########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"

    return  user_content
    


def transform_json_string(json_str):
    obj = json.loads(json_str)
    key, value = next(iter(obj.items()))
    return {"key": key, "value": value}


def get_scenarios_data(combined_data_json, project_name, ra_json_combined):
     
    if "customsdeclaration" in project_name.lower():
        project_name = "CustomsDeclaration_B"
    else:
        project_name = "all"

    try:
        all_table_info = requests.get(f"{vector_data_base_url}/{DATA_BASE_ID}/tables/{project_name}")
        all_table_info = all_table_info.json()
    except:
        all_table_info = {}
        pass

    if not isinstance(all_table_info, list) : 
        if all_table_info == {} or "not found" in all_table_info.get("detail",""):
            return combined_data_json

    for data_json in  combined_data_json["documents"]:

        if "waybill" not in data_json["doc_type"].lower().replace(" ","").strip():
            continue

        kv_list = data_json["key_data"]
        user_content =  get_defined_ra_json_txt(ra_json_combined, data_json["id"])
        kv_list_modified = copy.deepcopy(kv_list)

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

                query_col_list = [] 
                for col_name, col_data in desired_table["column_schema"].items():
                    if col_data["ismandatory"]:
                        query_col_list.append(col_name)

                if  query_col_list == []:
                    continue 

                query_data = [{}]
               
                for inner_item in kv_item["children"]:
                   
                    for col_name in query_col_list:
                        
                        if inner_item["key"].lower().strip() in col_name.lower().strip() and col_name:
                            query_data[0][col_name] = inner_item["value"]
                            break
                
                print("############## this is query data")
                print(query_data)
                retrived_data_from_data_base = query_auto_match(project_name, desired_table["table_name"], query_data)
                retrived_data_from_data_base = get_top_five_match(retrived_data_from_data_base)
                print("############## this is retrived data")
                print(retrived_data_from_data_base)  

                system_prompt_scenarios = get_system_prompt_scenarios(retrived_data_from_data_base)
                print("############## this is system prompt")
                print(system_prompt_scenarios)
                response, reasoning = run_llm(system_prompt_scenarios, user_content)
                print("############## this is LLM response")
                desired_kv_pair = transform_json_string(response)
                print(desired_kv_pair)

                if desired_kv_pair.get("value","None") != "None":
                    kv_list_modified.append(
                        {
                            "key":desired_kv_pair.get("key"),
                            "key_position": "0,0,0,0",
                            "value": desired_kv_pair.get("value"),
                            "value_position": "0,0,0,0",
                            "page_id": "", 
                            "original_key":desired_kv_pair.get("key"),
                            "is_label_mapped":False,
                            "is_profile_key_found":True,
                            "is_data_exception_done": False,
                            "is_pure_autoextraction" : True,
                            "original_key_label" :desired_kv_pair.get("key"),
                            "key_value":desired_kv_pair.get("key")
                            }
                    )
        data_json["key_data"] = kv_list_modified
                    

                

                
                
    return combined_data_json