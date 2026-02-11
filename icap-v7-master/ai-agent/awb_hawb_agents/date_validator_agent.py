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

from awb_hawb_agents.position_finder_date import find_position_info

MODEL_NAME = os.getenv("OLLAMA_MODEL")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
#MODEL_NAME = "gemma3:27b"



class ParsedData(BaseModel):
    executedOnDate: str | None
    
json_parser = JsonOutputParser(pydantic_object=ParsedData)

SYSTEM_PROMPT_AWB_DATE_AGENT = """
You are a precise date extraction system designed to identify the 'executed on' date from free-form document text.

Your job is to:
1. Detect phrases similar to "executed on", allowing minor variations (e.g., "execution date", "executed", "executed on date", etc.) using fuzzy matching (90% similarity).
2. Extract the nearest valid date using any common date format (e.g., "30 NOV 2025", "2025-11-30", "Nov 30, 2025", etc.).
3. Standardize the extracted date to the format YYYY-MM-DD.

RULES:
- Do NOT extract unrelated dates (e.g., invoice date, due date).
- Only extract if both a valid label and a valid date exist in proximity.
- Do NOT guess. If no valid date is confidently found, return null.
- Use regular expressions for date pattern matching.
- Ensure output is always valid JSON compatible with a Pydantic model.

OUTPUT FORMAT:
```json
{{
  "executedOnDate": "YYYY-MM-DD"  // or null if not found
}}
```
"""


def get_llm():
    print("^^^^^^^^^^",MODEL_NAME)
    print("^^^^^^^^^^",OLLAMA_API_URL)
    return ChatOllama(model=MODEL_NAME, format="json", temperature=0, base_url=OLLAMA_API_URL)

def get_date_from_llm(ra_json_all):

    try:
        page = ra_json_all["nodes"][0]["children"][0]
    except:
        page = "This document is very special"
        pass
    page_data = get_ra_json_to_txt(page)

    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT_AWB_DATE_AGENT), ("human", page_data)])
    llm = get_llm()
    parser_chain = prompt | llm | json_parser
    return parser_chain.invoke({})


def is_within_one_month(date_str):
  
    try:
        input_date = parser.parse(date_str)
        today = datetime.today()
        delta = abs((input_date - today).days)
        return delta <= 30, today
    except (ValueError, OverflowError):
        return False , datetime.today()

def find_date_from_data_json(data_json):

    def is_desired_date(value, label):
        
        valid_date_label = ["executedon", "executedondate"]
        
    
        if not any(fuzz.partial_ratio(label.lower().strip(), valid.lower()) >= 80 for valid in valid_date_label):
            return False, ""
    
        date_pattern = r'\b(\d{1,2}[/-][A-Za-z]{3,9}[/-]\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\b'
    
        match = re.search(date_pattern, value)
        if not match:
            return False, ""
    
        date_str = match.group(0).strip()
    
        date_formats = [
            "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
            "%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y",
            "%d %b %Y", "%d %B %Y",
            "%d-%b-%y", "%d-%B-%y",
            "%d-%b-%Y", "%d-%B-%Y"
        ]
    
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return True, parsed_date.date().isoformat()
            except ValueError:
                continue
    
        return False, ""

    
    found_date = ""
    kv_list = []
    
    for item_all in data_json["nodes"]:
        for item in item_all["children"]:
            if item["type"] != "table":
                kv_list += item["children"]
    
    
    # for item in data_json["nodes"][0]["children"]:
    #     if item["type"] != "table":
    #         kv_list =  copy.deepcopy(item["children"])
    #         break
        
        
    for kv in kv_list:
    
        value = kv.get("v","")
        label = kv.get("label","")
        
        is_valid, probable_date = is_desired_date(value, label)

        if is_valid:
            found_date = probable_date
            break
            
    return found_date
            


# data_payload_for_reasoning = {
#                 "batch_id": data["batch_id"],
#                 "agent_name": AGENT_NAME,
#                 "message_type": "reasoning"
#                 "output_queue":data["output_queue"],
#                 "client_id" : data["client_id"],
#                 "message": "",
#                 "sub_message": "",
#                 "remarks":[],
#                 "color_code" : "",
#                 "status_code": 200
#             }




def run_awb_or_hawb_date_validator_agent(ra_json,other_ra_jsons,data_json,other_data_jsons,data_payload_for_reasoning):
    
    pre_alert_data_json = {}
    pre_alert_ra_json = {}
    
    hwb_awb_data_json = {}
    hwb_awb_ra_json = {}
    
    civ_data_json = {}
    civ_ra_json = {}
    
    data_payload_for_reasoning["message"] = f"I have to check wheather the transportation date (executed on) of the document within in one month or not"
    send_log_update(data_payload_for_reasoning)
    
    data_payload_for_reasoning["message"] = f"Document matching initiated"
    send_log_update(data_payload_for_reasoning)
    
    doc_name = "Airway Bill"
    
    if data_json['DocumentType'].lower().replace(" ","").strip() == "commercialinvoice":
        civ_data_json = data_json
        civ_ra_json = ra_json
        print("Im",data_json['DocumentType'].lower().replace(" ","").strip())
    elif data_json['DocumentType'].lower().replace(" ","").strip() == "houseairwaybill" or data_json['DocumentType'].lower().replace(" ","").strip()  == "airwaybill":
        hwb_awb_data_json = data_json
        hwb_awb_ra_json = ra_json
        doc_name =  data_json['DocumentType']
        print("Im",data_json['DocumentType'].lower().replace(" ","").strip())
    elif data_json['DocumentType'].lower().replace(" ","").strip()  == "prealert":
        pre_alert_data_json =data_json
        pre_alert_ra_json = ra_json
        print("Im",data_json['DocumentType'].lower().replace(" ","").strip())
   
    for idx, other_data_json in enumerate(other_data_jsons):
        print("Loop",other_data_json['DocumentType'].lower().replace(" ","").strip())
        if other_data_json['DocumentType'].lower().replace(" ","").strip()  == "commercialinvoice" and civ_data_json == {}:
            civ_data_json = other_data_json
            civ_ra_json = other_ra_jsons[idx]
        elif (other_data_json['DocumentType'].lower().replace(" ","").strip()  == "houseairwaybill" or other_data_json['DocumentType'].lower().replace(" ","").strip()  == "airwaybill") and hwb_awb_data_json == {}:
            hwb_awb_data_json = other_data_json
            hwb_awb_ra_json = other_ra_jsons[idx]
            doc_name =  other_data_json['DocumentType']
            print("^^^^^^^^^^^^",doc_name)
        elif other_data_json['DocumentType'].lower().replace(" ","").strip()  == "prealert" and pre_alert_data_json == {}:
            pre_alert_data_json = other_data_json
            pre_alert_ra_json = other_ra_jsons[idx]
        
        print("*********", doc_name)
    
    
 
        
    color_code = "red"
    validation_msg = ""
    desired_date = ""
    
    if hwb_awb_ra_json == {}:
        
        data_payload_for_reasoning["message"] = f"Theres no Airway Bill or House Airway Bill type doument in the batch"
        send_log_update(data_payload_for_reasoning)
        
        validation_msg = "Theres no Airway Bill or House Airway Bill type doument in the batch.\n No transportation date information founded"
        color_code = "red"
        return  validation_msg, color_code, {}
        
    data_payload_for_reasoning["message"] = f"Successfully founded Airway Bill or House Airway Bill type document"
    send_log_update(data_payload_for_reasoning)
    
    
    data_payload_for_reasoning["message"] = f"Now I need to find transportation date from this selected Airway Bill or House Airway Bill type document"
    send_log_update(data_payload_for_reasoning)
    
    
    
      
    date_from_data_json = find_date_from_data_json(hwb_awb_data_json)
    
    if date_from_data_json == "":
        data_payload_for_reasoning["message"] = f"There is no transportation date (executed on) information in extracted data json. Therefore I need to check inside the page text"
        send_log_update(data_payload_for_reasoning)
        
        desired_date = get_date_from_llm(hwb_awb_ra_json)["executedOnDate"]
    else:
        desired_date = date_from_data_json
    print("^^^^^^^^^@@@", desired_date)
    
    
    try:
        position_info = find_position_info(hwb_awb_ra_json,desired_date)
    except:
        position_info = {}
        pass
    
    print("#####",position_info)
    
    if f"{desired_date}".strip() != "" and f"{desired_date}".strip() != "null" and f"{desired_date}".strip() != "None":
        
        data_payload_for_reasoning["message"] = f"Sucessfully founded the transportation date (executed on) information inside the page text"
        send_log_update(data_payload_for_reasoning)
        
        data_payload_for_reasoning["message"] = f"Transportation date validation initiated"
        send_log_update(data_payload_for_reasoning)
        
      
        
        is_within, today = is_within_one_month(desired_date)
        if is_within :
            validation_msg = f"The document {doc_name} executed on {desired_date}, which is within 1 month from today {today.date()}"
            color_code = "green"
            
            data_payload_for_reasoning["message"] = validation_msg
            send_log_update(data_payload_for_reasoning)
            
        else:
            validation_msg = f"The document {doc_name} executed on {desired_date}, which is not within 1 month from today {today.date()}"
            color_code = "red"
            
            data_payload_for_reasoning["message"] = validation_msg
            send_log_update(data_payload_for_reasoning)
        
    else:
        validation_msg = f"No date information founded in the {doc_name} document"
        color_code = "red"
        
        data_payload_for_reasoning["message"] = validation_msg
        send_log_update(data_payload_for_reasoning)
        
    return  validation_msg, color_code, position_info
    
    