import json
import re
import os

from dateutil import parser
from datetime import datetime, timedelta
import copy
import re
from rapidfuzz import fuzz
from typing import Dict, List, Any, Optional
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt, get_ra_json_to_text_info_list
from redis_publisher import broadcast_log_update_sync as send_log_update

from exceptions_agents.add_position_to_kv_exception import add_postion_information_to_exception_kv

MODEL_NAME = os.getenv("OLLAMA_MODEL")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")


def get_llm(model_name: str = "gemma3:27b"):
    return ChatOllama(model=MODEL_NAME, format="json", temperature=0, base_url=OLLAMA_API_URL)



# class KVPair(BaseModel):
#     key: str
#     value: str | None

# class ParsedData(BaseModel):
#     extracted: list[KVPair]

class KVPair(BaseModel):
    """Key-Value pair model"""
    key: str
    value: Optional[str] = Field(default="")

class ParsedData(BaseModel):
    """Container for extracted KV pairs"""
    extracted: List[KVPair]

json_parser = JsonOutputParser(pydantic_object=ParsedData)


def get_exception_agent_result(ra_json, page_wise_exception_dict):

    

    exception_kv_list = []

    for pageId, kv_list in page_wise_exception_dict.items():
        key_to_extract = ""
        example_kvs = []
        output_format_kvs = []
        page_data = ""
        
        entity_fields = ["supplier", "consignee", "shipper", "importer", "exporter", 
                        "buyer", "seller", "notify party", "bill to", "ship to", 
                        "deliver to", "manufacturer", "vendor"]
        
        keys_needing_full_address = []
        
        for item in kv_list:
            if not item["is_already_in_data_json"]:
                key_tmp = item["key"]
                if key_to_extract == "":
                    key_to_extract = f"{key_tmp}"
                else:
                    key_to_extract = f"{key_to_extract}, {key_tmp}"
                    
                if any(entity.lower() in key_tmp.lower() for entity in entity_fields):
                    keys_needing_full_address.append(key_tmp)
                    
                example_kvs.append({"key": item["key"], "value": item["value"]})
                output_format_kvs.append({"key": item["key"], "value": "key associated value"})
        
        if not example_kvs:
            continue
            
       
        
        for c in ra_json.get("children", []):
            if c.get("id") == pageId:
                page_data = get_ra_json_to_txt(c) 
                break
        
        example_output = {"extracted": example_kvs}
        output_format = {"extracted": output_format_kvs}

        address_instruction = ""
        if keys_needing_full_address:
            address_fields_str = ", ".join(keys_needing_full_address)
            address_instruction = f"""
        
        CRITICAL FOR ADDRESS FIELDS ({address_fields_str}):
         - Extract the COMPLETE information including company/person name AND full address
         - Include ALL parts: name, street address, city, state/province, postal code, country
         - Look for address blocks that may span multiple lines
         - Example: "COVIDIEN LP CENTRAL DC 5300 AIRWAYS BLVD MEMPHIS TN 38116 US" (not just "COVIDIEN LP CENTRAL DC")
         - Do NOT stop at just the company name - continue extracting until you have the full address block
         - Address information may appear on multiple lines below the entity name
        """

        SYSTEM_PROMPT_EXCEPTION_AGENT = """
        Extract the following keys from the document: {key_need_to_extract}
        
        You MUST return a JSON object with an "extracted" field containing an array of ALL requested key-value pairs.
        
        Output Format:
        {output_format_for_extraction}
        
        Example Output:
        {example_output_for_extraction}
        {address_instruction}
        
        Important:
         - You MUST extract ALL keys: {key_need_to_extract}
         - Return the response in the exact JSON format shown above with "extracted" field
         - If any key is not present in the document text, set its value to empty string ""
         - Do not guess any values - only extract what's explicitly in the document
         - Include ALL mentioned keys in the output, even if their values are empty
         - For entity/company fields, extract the COMPLETE information including full addresses
         - Sometimes value can be under multiple lines , so dont skip this. For exaple some time key can be column andvalue can be total value of that column written below under multiple row
        """



        print(f"Keys to extract: {key_to_extract}")
        if keys_needing_full_address:
            print(f"Keys needing full address: {keys_needing_full_address}")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT_EXCEPTION_AGENT),
            ("human", "{page_data}")
        ])
        
        llm = get_llm()
        
       
        chain = prompt | llm
        
        try:
            
            llm_result = chain.invoke({
                "key_need_to_extract": key_to_extract,
                "example_output_for_extraction": json.dumps(example_output, indent=2),
                "output_format_for_extraction": json.dumps(output_format, indent=2),
                "address_instruction": address_instruction,
                "page_data": page_data
            })
            
            
            if hasattr(llm_result, 'content'):
                result_text = llm_result.content
            elif isinstance(llm_result, dict) and 'content' in llm_result:
                result_text = llm_result['content']
            elif isinstance(llm_result, str):
                result_text = llm_result
            else:
                result_text = str(llm_result)
            
            print(f"Raw LLM response: {result_text[:500]}...")  
           
            parsed_result = json.loads(result_text)
            
           
            if hasattr(parsed_result, 'extracted'):
                extracted_items = parsed_result.extracted
            elif isinstance(parsed_result, dict) and 'extracted' in parsed_result:
                extracted_items = parsed_result['extracted']
            else:
                print(f"Unexpected result format: {type(parsed_result)}")
                extracted_items = []
            
            print(f"Extracted items: {extracted_items}")
            
            
            for item in extracted_items:
                if hasattr(item, 'key'):
                    key = item.key
                    value = item.value if item.value else ""
                else:
                    key = item.get("key", "")
                    value = item.get("value", "")
                
                exception_kv_list.append({
                    "key": key,
                    "value": value.replace("\n", " "),
                    "page_id": pageId.upper(),
                    "key_position": "0,0,0,0",
                    "value_position": "0,0,0,0",
                    "original_key": key, 
                    "is_label_mapped": False,
                    "is_profile_key_found": True,
                    "is_data_exception_done": True,
                    "is_pure_autoextraction": True
                })
            
            print(f"Successfully processed {len(extracted_items)} items for page {pageId}")
                    
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for page {pageId}: {e}")
            print(f"Failed to parse: {result_text[:200] if 'result_text' in locals() else 'N/A'}...")
            
            try:
                import re
                pattern = r'"key"\s*:\s*"([^"]+)"\s*,\s*"value"\s*:\s*"([^"]*)"'
                text_to_search = result_text if 'result_text' in locals() else str(llm_result)
                matches = re.findall(pattern, text_to_search)
                
                for key, value in matches:
                    exception_kv_list.append({
                        "key": key,
                        "value": value.replace("\n", " "),
                        "page_id": pageId.upper(),
                        "key_position": "0,0,0,0",
                        "value_position": "0,0,0,0",
                        "original_key": key,
                        "is_label_mapped": False,
                        "is_profile_key_found": True,
                        "is_data_exception_done": True,
                        "is_pure_autoextraction": True
                    })
                if matches:
                    print(f"Recovered {len(matches)} items using regex fallback")
            except Exception as regex_error:
                print(f"Regex fallback failed: {regex_error}")
                
        except Exception as e:
            print(f"Unexpected error processing page {pageId}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    return exception_kv_list


def is_value_also_in_page(page_data,value):
    for k,v in page_data[0].items():
        for doc_word_info in v:
            doc_word = doc_word_info[0]
            if value.strip() ==  doc_word.strip():
                return True
    return False


def run_kv_exception_agent(ra_json,kv_list,exception_list):

   
    page_wise_exception_dict = {}
    exception_kv_list = []

    for c in ra_json.get("children", []):
        page_data =get_ra_json_to_text_info_list(c) 
        page_id = ""
        for k,v in page_data[0].items():
            if not page_id:
                page_id = v[0][-1]
            is_exception_in_page = False
            page_wise_exception_list = []
            for doc_word_info in v:
                doc_word = doc_word_info[0]
                for ex_item in exception_list:
                    if fuzz.ratio(ex_item["label"].strip(), doc_word.strip()) >= 90:
                    
                        is_exception_value_for_this_page = is_value_also_in_page(page_data,ex_item["value"].strip())
                        if is_exception_value_for_this_page and page_id.lower() == ex_item["page_id"].lower():

                            exception_kv_list.append({
                                "key":ex_item["label"].strip(),
                                "value": ex_item["value"].strip(),
                                "page_id": page_id.upper(),
                                "key_position": "0,0,0,0",
                                "value_position": "0,0,0,0",
                                "original_key": ex_item["label"].strip(),
                                "is_label_mapped": False,
                                "is_profile_key_found": True,
                                "is_data_exception_done": True,
                                "is_pure_autoextraction": True
                            })
                        else:

                            if ex_item not in page_wise_exception_list:
                                page_wise_exception_list.append({"key":ex_item["label"],"value":ex_item["value"],"is_already_in_data_json":False})
                                is_exception_in_page = True
                            
            if is_exception_in_page:
                page_wise_exception_dict[page_id] =  page_wise_exception_list

    
    # for item in exception_list:
    #     if item["page_id"] not in page_wise_exception_dict.keys():
    #         page_wise_exception_dict[item["page_id"]] = []
    #     page_wise_exception_dict[item["page_id"]].append({"key":item["label"],"value":item["value"],"is_already_in_data_json":False})

    
    # kv_list = []
    # for item_all in data_json["nodes"]:
    #     for item in item_all["children"]:
    #         if item["type"] != "table":
    #             kv_list += item["children"]
                
    for kv in kv_list:
        
        value = kv.get("value","")
        key= kv.get("key","")
        page_id = kv.get("page_id")
        
        for k, v in page_wise_exception_dict.items():
            for kv_ex in v:
                if k == page_id and fuzz.ratio(key.lower().strip(),kv_ex["key"].lower().replace(":","").strip())>=80 and value.strip() != "":
                    exception_kv_list.append({
                        "key": key,
                        "value": value,
                        "page_id": page_id.upper(),
                        "key_position": "0,0,0,0",
                        "value_position": "0,0,0,0",
                        "original_key": key,
                        "is_label_mapped": False,
                        "is_profile_key_found": True,
                        "is_data_exception_done": True,
                        "is_pure_autoextraction": True
                    })
                    kv_ex["is_already_in_data_json"] = True

    is_any_missing_key = False
    for k, v in page_wise_exception_dict.items():
        for kv in v:
            if kv["is_already_in_data_json"] == False:
                is_any_missing_key = True
                break
        if is_any_missing_key:
            break
                    
    if not is_any_missing_key:
        return exception_kv_list

              
    exception_kv_list += get_exception_agent_result(ra_json, page_wise_exception_dict)

    #exception_kv_list = add_postion_information_to_exception_kv(ra_json, exception_kv_list)
    
    return exception_kv_list    


  