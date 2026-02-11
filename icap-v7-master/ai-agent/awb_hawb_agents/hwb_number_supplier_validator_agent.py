

import json
import re
import os

from dateutil import parser
from datetime import datetime, timedelta
import copy
import re
from rapidfuzz import fuzz

from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt
from redis_publisher import broadcast_log_update_sync as send_log_update

MODEL_NAME = os.getenv("OLLAMA_MODEL")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")



class ParsedData(BaseModel):
    executedOnDate: str | None
    
json_parser = JsonOutputParser(pydantic_object=ParsedData)

SYSTEM_PROMPT_HWB_NO = """
You are a precise extraction system designed to identify the 'House Air Waybill Number (HAWB)' or 'Airway Bill Number' from free-form document text.

Your job is to:
1. Detect labels or variations indicating an airway bill number, such as:
   - "HAWB"
   - "House Air Waybill No."
   - "House Airway Bill Number"
   - "Airway Bill No."
   - "AWB No."
   - "HAWB No."
   - Variations with minor typos (use fuzzy matching ≥90%).
2. Extract the nearest valid airway bill number.  
   - The number may start with specific prefixes (e.g., "WEB", "AWB", "HAWB") or be a sequence of alphanumeric characters.
   - Common formats include:  
     - "WEB123456789"  
     - "AWB-987654321"  
     - "HAWB12345"  
     - Pure numeric sequence (e.g., "123-45678901").
3. Standardize the extracted number by removing prefixes (e.g., WEB, AWB, HAWB), spaces, and punctuation so that only the pure numeric sequence remains.

RULES:
- Do NOT extract unrelated numbers (e.g., invoice numbers, container numbers, phone numbers).
- Only extract if both a valid label (or variation) and a valid airway bill number exist in proximity.
- Do NOT guess. If no valid airway bill number is confidently found, return null.
- Use regular expressions for number pattern matching.
- Ensure output is always valid JSON compatible with a Pydantic model.

OUTPUT FORMAT:
```json
{{
  "airWayBillNo": "STRING"  // or null if not found
}}
```
"""


def get_llm():
    print("^^^^^^^^^^",MODEL_NAME)
    print("^^^^^^^^^^",OLLAMA_API_URL)
    return ChatOllama(model=MODEL_NAME, format="json", temperature=0, base_url=OLLAMA_API_URL)

def get_hwb_number_from_llm(ra_json_all):

    try:
        page = ra_json_all["nodes"][0]["children"][0]
    except:
        page = "test text"
        pass
    
    page_data = get_ra_json_to_txt(page)

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT_HWB_NO), ("human", page_data)])
    llm = get_llm()
    parser_chain = prompt | llm | json_parser
    return parser_chain.invoke({})


    

def find_supplier_from_data_json(data_json):
    
    def find_supplier_name(value_list):
        supplier_name = ""
        for item in value_list:
            if item["label"].lower().strip() == "name":
                return item["v"]
        return supplier_name

    def is_desired_supplier(label):
        
        valid_supplier_label = ["supplier"]

        if any(fuzz.partial_ratio(label.lower().strip(), valid.lower()) >= 90 for valid in valid_supplier_label):
            return True 
    
        return False

    
    found_supplier = ""
    kv_list = []
   
    try:
        for item_all in data_json["nodes"]:
            for item in item_all["children"]:
                if item["type"] != "table":
                    kv_list += item["children"]
    except:
        kv_list = []
        pass

    
    
    for kv in kv_list:
        value = kv.get("v","")
        label = kv.get("label","")
        
        is_valid = is_desired_supplier(label)
        
        if is_valid:
            
            try:
                found_supplier = find_supplier_name(kv["children"])
            except:
                pass
            break
           
    return found_supplier
            

def find_hwb_number_from_data_json(data_json):

    def is_desired_hwb_number(value, label):
        
        valid_hwb_number_label = ["housebillnumber"]
        if any(fuzz.partial_ratio(label.lower().strip(), valid.lower()) >= 90 for valid in valid_hwb_number_label):
            return True
        return False

    
    found_hwb_number = ""
    kv_list = []
    try:
        for item_all in data_json["nodes"]:
            for item in item_all["children"]:
                if item["type"] != "table":
                    kv_list += item["children"]
    except:
        kv_list = []
        pass
        
        
        
    for kv in kv_list:
        value = kv["v"]
        label = kv["label"]
        
        is_valid  = is_desired_hwb_number(value, label)

        if is_valid:
            found_hwb_number = value
            break
      
    return found_hwb_number


def validate_supplier(civ_data_json, hwb_awb_data_json,data_payload_for_reasoning):
    
    #print("$$$$$$$$$$$")
    #print(civ_data_json)
    #print("$$$$$$$$$$$")
    
    data_payload_for_reasoning["message"] = f"Searching suppliers from extracted data of the document"
    send_log_update(data_payload_for_reasoning)
    
    color_code = "red"
    supplier_civ = find_supplier_from_data_json(civ_data_json) 
    supplier_hwb = find_supplier_from_data_json(hwb_awb_data_json)
    
    if fuzz.ratio(supplier_civ.lower().strip(),supplier_hwb.lower().strip()) >= 80 and supplier_civ.strip() != "":
        
        data_payload_for_reasoning["message"] = f"Successfully accumulated all the supplier informations from the documents and starting the validation process"
        send_log_update(data_payload_for_reasoning)
        
        data_payload_for_reasoning["message"] = f"The supplier details are consistent across all desired documents. \n\nSupplier : {supplier_civ}"
        send_log_update(data_payload_for_reasoning)
        
        color_code = "green"
        return f"The supplier details are consistent across all desired documents. \n\nSupplier : {supplier_civ}",  color_code
    elif supplier_civ.strip() == "" and supplier_hwb.strip() == "":
        color_code = "red"
        
        data_payload_for_reasoning["message"] = f"There is no supplier information in extraction data, may be appropiate key mapping can resolve the issue"
        send_log_update(data_payload_for_reasoning)
        
        return f"There is no supplier information in extraction data", color_code
    else:
        color_code = "red"
        
        data_payload_for_reasoning["message"] = f"Successfully accumulated all the supplier informations from the documents and starting the validation process"
        send_log_update(data_payload_for_reasoning)
        
        data_payload_for_reasoning["message"] = f"The supplier details are not consistent across all desired documents. They are diffierent from each other. For Commercial Invoice, supplier is {supplier_civ.strip()} and for Airway Bill, supplier is {supplier_hwb.strip()}"
        send_log_update(data_payload_for_reasoning)
        
        return f"The supplier details are not consistent across all desired documents. \n\nCommercial Invoice : {supplier_civ.strip()}\nAirway Bill : {supplier_hwb.strip()}", color_code
    






def validate_hwb_number(pre_alert_data_json, pre_alert_ra_json, hwb_awb_data_json, hwb_awb_ra_json,data_payload_for_reasoning):
    
    
    def extract_numeric_only(text):
   
        return re.sub(r'[^0-9]', '', text)
    
    hwb_validation_msg = ""
    
    color_code = "red"
    hwb_number_pre_alert_final = ""
    hwb_number_hwb_final = ""
    
    data_payload_for_reasoning["message"] = f"Searching AWB/HAWB number from extracted data of the documents"
    send_log_update(data_payload_for_reasoning)
    
    
    hwb_number_pre_alert_data_json = find_hwb_number_from_data_json(pre_alert_data_json)
    hwb_number_hwb_data_json = find_hwb_number_from_data_json(hwb_awb_data_json)
    
    
    
    
    if hwb_number_pre_alert_data_json == "":
        
        data_payload_for_reasoning["message"] = f"There is no AWB/HAWB number in Pre Alert data json"
        send_log_update(data_payload_for_reasoning)
        
        data_payload_for_reasoning["message"] = f"Initiating Pre Alert document search for AWB/HAWB number"
        send_log_update(data_payload_for_reasoning)
        
        try:
            hwb_number_pre_alert_llm = get_hwb_number_from_llm(pre_alert_ra_json)["airWayBillNo"]
        except:
            hwb_number_pre_alert_llm = ""
            pass
        
        if hwb_number_pre_alert_llm == "":
            data_payload_for_reasoning["message"] = f"There is no AWB/HAWB number in Pre Alert document"
            send_log_update(data_payload_for_reasoning)
        else:
            data_payload_for_reasoning["message"] = f"Successfully founded AWB/HAWB number in Pre Alert document. AWB/HAWB No:{hwb_number_pre_alert_llm}"
            send_log_update(data_payload_for_reasoning)
            
        hwb_number_pre_alert_final = hwb_number_pre_alert_llm
        
    else:
        
        data_payload_for_reasoning["message"] = f"Successfully founded AWB/HAWB number in Pre Alert data json. AWB/HAWB No:{hwb_number_pre_alert_data_json}"
        send_log_update(data_payload_for_reasoning)
        hwb_number_pre_alert_final = hwb_number_pre_alert_data_json
        
        
        
    if hwb_number_hwb_data_json == "":
        
        data_payload_for_reasoning["message"] = f"There is no AWB/HAWB number in {hwb_awb_data_json['DocumentType']} data json"
        send_log_update(data_payload_for_reasoning)
        
        data_payload_for_reasoning["message"] = f"Initiating {hwb_awb_data_json['DocumentType']} document search for AWB/HAWB number"
        send_log_update(data_payload_for_reasoning)
        
        try:
            hwb_number_hwb_llm = get_hwb_number_from_llm(hwb_awb_ra_json)["airWayBillNo"]
        except:
            hwb_number_hwb_llm = ""
            pass
        
        if hwb_number_hwb_llm == "":
            data_payload_for_reasoning["message"] = f"There is no AWB/HAWB number in {hwb_awb_data_json['DocumentType']} document"
            send_log_update(data_payload_for_reasoning)
        else:
            data_payload_for_reasoning["message"] = f"Successfully founded AWB/HAWB number in {hwb_awb_data_json['DocumentType']} document. AWB/HAWB No:{hwb_number_hwb_llm}"
            send_log_update(data_payload_for_reasoning)
            
        hwb_number_hwb_final = hwb_number_hwb_llm
        
    else:
        
        data_payload_for_reasoning["message"] = f"Successfully founded AWB/HAWB number in {hwb_awb_data_json['DocumentType']} data json. AWB/HAWB No:{hwb_number_hwb_data_json}"
        send_log_update(data_payload_for_reasoning)
        hwb_number_hwb_final = hwb_number_hwb_data_json
    
    
    normalized_hwb_no_pre_alert = extract_numeric_only(hwb_number_pre_alert_final.strip())
    normalized_hwb_no_hwb = extract_numeric_only(hwb_number_hwb_final.strip())
    
    print("********"*10)
    print(normalized_hwb_no_pre_alert)
    print(normalized_hwb_no_hwb)
    print("********"*10)
    
    if normalized_hwb_no_pre_alert.strip() != "" and fuzz.ratio(normalized_hwb_no_pre_alert,normalized_hwb_no_hwb)>= 90:
        color_code = "green"
        hwb_validation_msg = f"The AWB or HAWB numbers are consistent across all desired documents. \n\nAWB/HAWB number : {hwb_number_pre_alert_final}"
    elif normalized_hwb_no_pre_alert.strip() == "" and normalized_hwb_no_hwb.strip() == "":
        color_code = "red"
        hwb_validation_msg = f"There is no AWB/HAWB number in the desired documents"
    else:
        color_code = "red"
        hwb_validation_msg = f"The AWB or HAWB numbers are not consistent across all desired documents. \n\nPre Alert: {hwb_number_pre_alert_final}\n{hwb_awb_data_json['DocumentType']}: {hwb_number_hwb_final}"
        
    return hwb_validation_msg, color_code


def run_awb_or_hawb_no_and_supplier_validator_agent(data_json,other_data_jsons,ra_json,other_ra_jsons,data_payload_for_reasoning):
    
    
    
    data_payload_for_reasoning["message"] = f"I need to check wheather the supplier entities of the given documents have any inconsistency or not"
    send_log_update(data_payload_for_reasoning)
    
    combined_color_code = "red"
    combined_validation_msg = ""
    
    pre_alert_data_json = {}
    pre_alert_ra_json = {}
    
    hwb_awb_data_json = {}
    hwb_awb_ra_json = {}
    
    civ_data_json = {}
    civ_ra_json = {}
    
    if data_json['DocumentType'].lower().replace(" ","").strip() == "commercialinvoice":
        civ_data_json = data_json
        civ_ra_json = ra_json
    elif data_json['DocumentType'].lower().replace(" ","").strip() == "houseairwaybill" or data_json['DocumentType'].lower().replace(" ","").strip()  == "airwaybill":
        hwb_awb_data_json = data_json
        hwb_awb_ra_json = ra_json
    elif data_json['DocumentType'].lower().replace(" ","").strip()  == "prealert":
        pre_alert_data_json =data_json
        pre_alert_ra_json = ra_json
   
    for idx, other_data_json in enumerate(other_data_jsons):
       
        if other_data_json['DocumentType'].lower().replace(" ","").strip()  == "commercialinvoice" and civ_data_json == {}:
            civ_data_json = other_data_json
            civ_ra_json = other_ra_jsons[idx]
        elif (other_data_json['DocumentType'].lower().replace(" ","").strip()  == "houseairwaybill" or other_data_json['DocumentType'].lower().replace(" ","").strip()  == "airwaybill") and hwb_awb_data_json == {}:
            hwb_awb_data_json = other_data_json
            hwb_awb_ra_json = other_ra_jsons[idx]
        elif other_data_json['DocumentType'].lower().replace(" ","").strip()  == "prealert" and pre_alert_data_json == {}:
            pre_alert_data_json = other_data_json
            pre_alert_ra_json = other_ra_jsons[idx]
                
        
    
    supplier_validator_msg, color_code_supplier = validate_supplier(civ_data_json, hwb_awb_data_json,data_payload_for_reasoning)  
    
    hwb_validation_msg, color_code_hwb = validate_hwb_number(pre_alert_data_json,pre_alert_ra_json, hwb_awb_data_json,hwb_awb_ra_json,data_payload_for_reasoning)
    
    
    if color_code_supplier == "green" and color_code_hwb == "green":
        combined_color_code = "green"
    
    combined_validation_msg = f"{supplier_validator_msg}\n\n{hwb_validation_msg}"
          
    return  supplier_validator_msg, color_code_supplier, hwb_validation_msg, color_code_hwb
    
    
