
import json
import re
from typing import Dict, Any, Union
from dotenv import load_dotenv
from utils.llm_clients import run_llm
from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
from shipment_table_agents.position_adder import add_postion_information_to_table
import copy


def parse_doc_info(prompt_data):
    """
    Parse prompt data which can be either:
    1. Old format (string): "DocClass: Pre Alert Field_Description: Extract... Rules_Description: ..."
    2. New format (dict): {"DocClass": "Pre Alert", "Field_Description": "...", "Rules_Description": "..."}
    
    Returns: (doc_class_list, field_description, rules_description)
    """
    
    # Check if prompt_data is a dictionary (new format)
    if isinstance(prompt_data, dict):
        # New dictionary format
        doc_class_str = prompt_data.get("DocClass", "").strip()
        doc_class = [cls.strip() for cls in doc_class_str.split(",") if cls.strip()]
        field_description = prompt_data.get("Field_Description", "").strip()
        rules_description = prompt_data.get("Rules_Description", "").strip()
        return doc_class, field_description, rules_description
    
    # Old string format
    text = str(prompt_data)
    parts = text.split("Field_Description:")
    doc_class_part = parts[0].replace("DocClass:", "").strip()
    doc_class = [cls.strip() for cls in doc_class_part.split(",") if cls.strip()]
    
    if len(parts) > 1:
        field_and_rules = parts[1].split("Rules_Description:")
        field_description = field_and_rules[0].strip().strip('"')
        rules_description = field_and_rules[1].strip() if len(field_and_rules) > 1 else ""
    else:
        field_description = ""
        rules_description = ""
    
    return doc_class, field_description, rules_description



def get_doc_class_wise_process_field(process_field):

    updated_process_field_dict = {}
    process_field_without_doc_type = []
    address_field_name = []
    for idx, field_item in enumerate(process_field):
        
        if field_item["type"] == "addressBlock":
            address_field_name.append(field_item["keyValue"])

        field_item_new = copy.deepcopy(field_item)
        project_prompt = field_item.get("project_prompt",{})
        process_prompt = field_item.get("process_prompt", {})
       

        # Parse project prompt - validate based on format
        # if isinstance(project_prompt, dict):
        #     # New dictionary format
        #     if not project_prompt.get("DocClass", "").strip():
        #         f_name = field_item["keyValue"]
        #         return updated_process_field_dict, True, f"Doc Class is missing in project prompt for {f_name}"
        #     # if not project_prompt.get("Field_Description", "").strip():
        #     #     f_name = field_item["keyValue"]
        #     #     return updated_process_field_dict, True, f"Field Description is missing in project prompt for {f_name}"
        # else:
        #     # Old string format
        #     if "docclass" not in str(project_prompt).lower():
        #         f_name = field_item["keyValue"]
        #         return updated_process_field_dict, True, f"Doc Class is missing in project prompt for {f_name}"
        #     if str(project_prompt).strip() == "":
        #         f_name = field_item["keyValue"]
        #         return updated_process_field_dict, True, f"Project Prompt Data is missing for {f_name}"

        project_doc_class_list, project_field_description, project_rules_description = parse_doc_info(project_prompt)
        process_doc_class_list, process_field_description, process_rules_description = parse_doc_info(process_prompt)
        
        if project_field_description.strip() == "" and process_field_description.strip() == "":
            project_field_description = "Field_Name"
        
        # if project_field_description.strip() == "":
        #     f_name = field_item["keyValue"]
        #     return updated_process_field_dict, True, f"Field Description is missing in project prompt for {f_name}"

        # Determine which prompt(s) to use based on process_prompt
        prompt_map = {}  # Maps doc_class -> (field_description, rules_description)
        project_is_universal = not project_doc_class_list or project_doc_class_list[0].strip().lower() == "none"
        
        # Check if process_prompt exists and is not empty
        has_process_prompt = False
        if isinstance(process_prompt, dict):
            # Dict format - check if it has content
            has_process_prompt = bool(process_prompt.get("DocClass") or process_prompt.get("Field_Description"))
        elif isinstance(process_prompt, str):
            # String format - check if not empty
            has_process_prompt = process_prompt.strip() != ""


        if has_process_prompt:

            # If process Field_Description is empty, fall back to project Field_Description
            if process_field_description.strip() == "":
                process_field_description = project_field_description
                #print(f"[FALLBACK] Profile Field_Description is empty for '{field_item['keyValue']}', using project Field_Description: {project_field_description}")
            
            # If process Rules_Description is empty, fall back to project Rules_Description
            if process_rules_description.strip() == "":
                process_rules_description = project_rules_description
                #print(f"[FALLBACK] Profile Rules_Description is empty for '{field_item['keyValue']}', using project Rules_Description: {project_rules_description}")
            
            # Check if process prompt has DocClass(es)
            if process_doc_class_list and process_doc_class_list[0].strip().lower() != "none":
                # Process prompt has specific DocClass(es) - use it only for those classes
                for doc_class in process_doc_class_list:
                    prompt_map[doc_class] = (process_field_description, process_rules_description)
                
                # For remaining project classes, use project prompt
                # if project_is_universal:
                #     # Project is universal (DocClass: None) - add as default for all other classes
                #     # This will be added to no_doc_class so it applies to all classes not overridden
                #     prompt_map["none"] = (project_field_description, project_rules_description)
                # else:
                #     # Project has specific classes - add those not overridden by process
                #     for doc_class in project_doc_class_list:
                #         if doc_class not in prompt_map and doc_class.strip().lower() != "none":
                #             prompt_map[doc_class] = (project_field_description, project_rules_description)
            else:
                # Process prompt has NO DocClass - use it as universal override
                if project_is_universal:
                    # Both are universal - process overrides
                    prompt_map["none"] = (process_field_description, process_rules_description)
                else:
                    # Process universal overrides all project classes
                    for doc_class in project_doc_class_list:
                        if doc_class.strip().lower() != "none":
                            prompt_map[doc_class] = (process_field_description, process_rules_description)
                    # Also add as universal default
                    prompt_map["none"] = (process_field_description, process_rules_description)

        else:
            # No process prompt - use project prompt
            if project_is_universal:
                # Project is universal - applies to all classes
                prompt_map["none"] = (project_field_description, project_rules_description)
            else:
                # Project has specific classes
                for doc_class in project_doc_class_list:
                    if doc_class.strip().lower() != "none":
                        prompt_map[doc_class] = (project_field_description, project_rules_description)

        # Group doc classes by their prompt data (field_description, rules_description)
        # This ensures classes with same prompt are grouped together
        prompt_groups = {}  # Maps (field_description, rules_description) -> [doc_classes]
        
        for doc_class, (field_desc, rules_desc) in prompt_map.items():
            prompt_key = (field_desc, rules_desc)
            if prompt_key not in prompt_groups:
                prompt_groups[prompt_key] = []
            prompt_groups[prompt_key].append(doc_class)
        
        # Organize fields by doc class with their appropriate prompts
        for (field_description, rules_description), doc_class_group in prompt_groups.items():
            if len(doc_class_group) == 1 and doc_class_group[0] == "none":
                # Add to no_doc_class list
                field_item_copy = copy.deepcopy(field_item_new)
                field_item_copy["doc_class_list"] = []
                field_item_copy["field_description"] = field_description
                field_item_copy["rules_description"] = rules_description
                
                # Log prompt details for 'forwarder' field
                if field_item_copy.get("keyValue") == "forwarder":
                    # print(f"\n{'='*80}")
                    # print(f"[FORWARDER PROMPT DEBUG]")
                    # print(f"Key: {field_item_copy.get('keyValue')}")
                    # print(f"Type: {field_item_copy.get('type')}")
                    # print(f"Label: {field_item_copy.get('label')}")
                    # print(f"Doc Classes: {doc_class_group}")
                    # print(f"Field Description: {field_description}")
                    # print(f"Rules Description: {rules_description}")
                    # print(f"{'='*80}\n")
                    pass
                
                if field_item_copy not in process_field_without_doc_type:
                    process_field_without_doc_type.append(field_item_copy)
            else:
                # Add to specific doc class lists
                for doc_class in doc_class_group:
                    if doc_class != "none":
                        if doc_class not in updated_process_field_dict:
                            updated_process_field_dict[doc_class] = []
                        
                        field_item_copy = copy.deepcopy(field_item_new)
                        field_item_copy["doc_class_list"] = doc_class_group
                        field_item_copy["field_description"] = field_description
                        field_item_copy["rules_description"] = rules_description
                        
                        # Log prompt details for 'forwarder' field
                        if field_item_copy.get("keyValue") == "forwarder":
                            # print(f"\n{'='*80}")
                            # print(f"[FORWARDER PROMPT DEBUG - DOC CLASS SPECIFIC]")
                            # print(f"Key: {field_item_copy.get('keyValue')}")
                            # print(f"Type: {field_item_copy.get('type')}")
                            # print(f"Label: {field_item_copy.get('label')}")
                            # print(f"Doc Class: {doc_class}")
                            # print(f"All Doc Classes: {doc_class_group}")
                            # print(f"Field Description: {field_description}")
                            # print(f"Rules Description: {rules_description}")
                            # print(f"{'='*80}\n")
                            pass
                        
                        updated_process_field_dict[doc_class].append(field_item_copy)
    
    updated_process_field_dict["no_doc_class"] = process_field_without_doc_type
    updated_process_field_dict["address_field_name"] = address_field_name
    return updated_process_field_dict, False, ""





def get_definition_key_list_based_on_doc_id(definition_data, doc_id):

    for item in definition_data:
        if item["document_id"] == doc_id:
            return item["exception_list"]
    return []

def get_modified_keys_based_on_definition(definition_data,field_need_to_extract, doc_id):

    if definition_data == []:
        return field_need_to_extract
    
    definition_key_list = get_definition_key_list_based_on_doc_id(definition_data, doc_id)

    if definition_key_list == []:
        return field_need_to_extract

    done_list = []

    for main_item_idx, main_item in enumerate(field_need_to_extract):
        for definition_item_idx, definition_item in enumerate(definition_key_list):
            if definition_item["process_key"] not in done_list and main_item["keyValue"] == definition_item["process_key"]:
                done_list.append(definition_item["process_key"])
                definition_field_description = definition_item["definition_prompt"]["Field_Description"]
                definition_rules_description = definition_item["definition_prompt"]["Rules_Description"]

                if definition_field_description.strip() != "":
                    main_item["field_description"] = definition_field_description
                if definition_rules_description.strip() != "":
                    main_item["rules_description"] = definition_field_description

    return field_need_to_extract


        

# def generate_system_prompt_shipment_table_agent(field_need_to_extract):
#     table_columns = []
    
#     for item in field_need_to_extract:
#         if item.get("type") == "table":
#             table_columns.append({
#                 "column": item.get("keyValue", ""),
#                 "description": item.get("field_description", ""),
#                 "rule": item.get("rules_description", "")
#             })
    
#     table_section = ""
#     if table_columns:
#         table_section = "  table:\n"
#         for col_item in table_columns:
#             table_section += f'    - {{ "column": "{col_item["column"]}", "description": "{col_item["description"]}", "value_conversion_rule": "{col_item["rule"]}"}}\n'
    
#     field_specific_rules = """
#     Field-Specific Extraction & Defaulting Rules
#     Apply these rules AFTER extracting raw data from the document. These rules determine final values for specific columns.

#     1. DIMENSIONS (Packing Lines)
#        - IF dimensions exist in the document:
#            → USE dimensions as packing lines for each row
#        - ELSE:
#            → SET dimensions = null

#     2. PACKAGE COUNT
#        - IF stated packageCount exists per row AND total package count exists in document:
#            → IF sum(all stated packageCount) == total package count:
#                → USE stated packageCount in each row as-is
#            → ELSE:
#                → SET packageCount of 1st row = total package count from document
#                → SET packageCount of all other rows = 0
#        - ELSE IF no stated packageCount per row:
#            → SET packageCount = 1 for each row

#     3. PACKAGE TYPE
#        - IF packageType exists in document:
#            → USE packageType as-is in each row
#        - ELSE:
#            → SET packageType = "PCE" for each row

#     4. GROSS WEIGHT
#        - IF grossWeight exists per row in document:
#            → USE grossWeight exactly as stated in each row
#        - ELSE IF only total gross weight exists in document:
#            → SET grossWeight of 1st row = total gross weight from document
#            → SET grossWeight of all other rows = 0
#        - ELSE:
#            → SET grossWeight = null for all rows

#     5. HARMONIZED CODE (HS Code)
#        - IF row-level harmonizedCode exists:
#            → USE harmonizedCode per row as-is
#        - ELSE IF single harmonizedCode exists in document:
#            → APPLY same harmonizedCode to ALL rows
#        - ELSE IF harmonizedCode count > total row count:
#            → APPLY first harmonizedCode to ALL rows
#        - ELSE:
#            → SET harmonizedCode = null for all rows

#     6. GOODS DESCRIPTION
#        - IF row-level goodsDescription exists:
#            → USE goodsDescription per row as-is
#        - ELSE IF general goodsDescription exists in document:
#            → APPLY that description to ALL rows
#        - ELSE:
#            → SET goodsDescription = null for all rows
#     """
    
#     system_prompt_shipment_table_agent = f"""You are an Adaptive Field & Table Extractor.

#     Task
#     Given document_text (plain text) and a table extraction spec (table columns with descriptions and rule), 
#     extract values that match—even if expressed via synonyms/abbreviations/paraphrase— and apply column wise value conversion rule accordingly then return only the JSON in the required shape. 
#     Do not calculate any amount value, quantity if not specifically mentioned in the description. 
#     Extract all possible tables data if it's present on the document or based on the data in the document, intelligently figure out other fields by making intelligent connections, always give deterministic solution. 
#     Verify what you are extracting too. Note: There might be some OCR error in the document that you need to account for and intelligently figure out.
#     Firstly process the table and based on that determine or calculate its value. 

#     Input Payload (fill this template)
#     {table_section}

#     {field_specific_rules}

#     Output (strict shape, no extra text)
#     {{
#       "item_value": [
#         [
#           {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
#           {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
#           {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
#         ],
#         [
#           {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
#           {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
#           {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
#         ]
#       ]
#     }}

#     General Extraction Rules
#     1. Preserve each provided column name exactly in output.
#     2. Use descriptions to resolve aliases/short forms; prefer label–value lines, titles, and repeated cues.
#     3. Normalize whitespace; keep original units/text unless the description demands a specific format.
#     4. Apply column wise value conversion rule correctly if there's any.
#     5. If the description defines a static value for any column, you must set that exact value—do not skip it.
#     6. Build table rows from the document's line-item sections; if a row lacks some columns, include the row with null for missing cells.
#     7. Always return the table even if it's empty.
#     8. For table, firstly check how many rows are there before extracting. Double check to verify how many rows are present in the document. To distinguish the row, if there are multiple, you will see pattern repeating.
#     9. For table, there will be cases where column data is not present in a table but it will be present in another table connected by HS Code or some code.
#     10. Extract all the items from table even if it's huge, no questions asked. You can't extract only some. You need to extract all the items/rows, MUST.
#     11. IMPORTANT: Apply the Field-Specific Extraction & Defaulting Rules above for dimensions, packageCount, packageType, grossWeight, harmonizedCode, and goodsDescription columns.
#     12. Return only the JSON object, no explanations.
#     """
    
#     return system_prompt_shipment_table_agent







#################################################
def generate_system_prompt_shipment_table_agent(field_need_to_extract):
    table_columns = []
    
    for item in field_need_to_extract:
        if item.get("type") == "table":
            table_columns.append({
                "column": item.get("keyValue", ""),
                "description": item.get("field_description", ""),
                "rule": item.get("rules_description", "")
            })
    
    table_section = ""
    if table_columns:
        table_section = "  table:\n"
        for col_item in table_columns:
            table_section += f'    - {{ "column": "{col_item["column"]}", "description": "{col_item["description"]}", "value_conversion_rule": "{col_item["rule"]}"}}\n'
    
    field_specific_rules = """
    Field-Specific Extraction & Defaulting Rules
    Apply these rules AFTER extracting raw data from the document. These rules determine final values for specific columns.

    1. DIMENSIONS (Packing Lines)
       - IF dimensions exist in the document:
           → USE dimensions as packing lines for each row
       - ELSE:
           → SET dimensions = null

    2. PACKAGE COUNT
       - IF stated packageCount exists per row AND total package count exists in document:
           → IF sum(all stated packageCount) == total package count:
               → USE stated packageCount in each row as-is
           → ELSE:
               → SET packageCount of 1st row = total package count from document
               → SET packageCount of all other rows = 0
       - ELSE IF no stated packageCount per row:
           → SET packageCount = 1 for each row

    3. PACKAGE TYPE
       - IF packageType exists in document:
           → USE packageType as-is in each row
       - ELSE:
           → SET packageType = "PCE" for each row

    4. GROSS WEIGHT
       - IF grossWeight exists per row in document:
           → USE grossWeight exactly as stated in each row
       - ELSE IF only total gross weight exists in document:
           → SET grossWeight of 1st row = total gross weight from document
           → SET grossWeight of all other rows = 0
       - ELSE:
           → SET grossWeight = null for all rows

    5. HARMONIZED CODE (HS Code)
       - IF row-level harmonizedCode exists:
           → USE harmonizedCode per row as-is
       - ELSE IF single harmonizedCode exists in document:
           → APPLY same harmonizedCode to ALL rows
       - ELSE IF harmonizedCode count > total row count:
           → APPLY first harmonizedCode to ALL rows
       - ELSE:
           → SET harmonizedCode = null for all rows

    6. GOODS DESCRIPTION
       - IF row-level goodsDescription exists:
           → USE goodsDescription per row as-is
       - ELSE IF general goodsDescription exists in document:
           → APPLY that description to ALL rows
       - ELSE:
           → SET goodsDescription = null for all rows
    """
    
    page_break_handling_rules = """
    Page Break & Split Row Handling Rules
    Documents often have table rows that get SPLIT across pages due to page breaks, headers, footers, or page numbers appearing mid-row. You MUST handle these correctly.

    DETECTION SIGNALS for Split Rows:
    1. A row appears to end abruptly without all expected column values
    2. Page markers appear mid-data (e.g., "Page 2 of 5", "--- Page Break ---", page numbers, footers like company name/date/document ID)
    3. Headers repeat after a break (column headers appearing again indicate a new page started)
    4. Continuation indicators (e.g., "continued...", "cont'd", "(cont.)")
    5. Row numbering/sequence numbers that skip or repeat across the break
    6. Incomplete data patterns: a row starts with item number but lacks quantity/price, then after footer/header, quantity/price appears without item number

    HANDLING STRATEGY:
    1. IDENTIFY page artifacts:
       - Page numbers (e.g., "1", "Page 1", "1/5", "Page 1 of 10")
       - Footers (company names, dates, document IDs, "Confidential", signatures)
       - Headers that repeat (column headers, document titles, logos text)
       - Horizontal lines or separators indicating page boundaries

    2. MENTALLY REMOVE page artifacts:
       - Strip out all identified page breaks, footers, headers, and page numbers
       - Treat the remaining content as continuous data

    3. RECONSTRUCT split rows:
       - If a row's data is interrupted by page artifacts, MERGE the fragments
       - Match row identifiers (item numbers, SKUs, line numbers) before and after breaks
       - Ensure each logical row has complete data from all its fragments

    4. VALIDATE row integrity:
       - After reconstruction, verify each row has the expected column structure
       - Check that row counts match any stated totals in the document
       - Ensure no duplicate rows were created from the same split data


    CRITICAL RULES:
    - NEVER treat page artifacts (footers, headers, page numbers) as data rows
    - ALWAYS merge fragments of the same logical row
    - COUNT unique item identifiers to determine true row count, not line count
    - When in doubt, look for repeating patterns that indicate row structure
    """
    
    system_prompt_shipment_table_agent = f"""You are an Adaptive Field & Table Extractor.

    Task
    Given document_text (plain text) and a table extraction spec (table columns with descriptions and rule), 
    extract values that match—even if expressed via synonyms/abbreviations/paraphrase— and apply column wise value conversion rule accordingly then return only the JSON in the required shape. 
    Do not calculate any amount value, quantity if not specifically mentioned in the description. 
    Extract all possible tables data if it's present on the document or based on the data in the document, intelligently figure out other fields by making intelligent connections, always give deterministic solution. 
    Verify what you are extracting too. Note: There might be some OCR error in the document that you need to account for and intelligently figure out.
    Firstly process the table and based on that determine or calculate its value. 

    Input Payload (fill this template)
    {table_section}

    {page_break_handling_rules}

    ## Must Validate (Critical Rules): {field_specific_rules}

    Output (strict shape, no extra text)
    {{
      "item_value": [
        [
          {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
        ],
        [
          {{"label":"COLUMN_NAME_1", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_2", "value": value or null, "page_no": page no mentioned at top or null}},
          {{"label":"COLUMN_NAME_M", "value": value or null, "page_no": page no mentioned at top or null}}
        ]
      ]
    }}

    General Extraction Rules
    1. Preserve each provided column name exactly in output.
    2. Use descriptions to resolve aliases/short forms; prefer label–value lines, titles, and repeated cues.
    3. Normalize whitespace; keep original units/text unless the description demands a specific format.
    4. Apply column wise value conversion rule correctly if there's any.
    5. If the description defines a static value for any column, you must set that exact value—do not skip it.
    6. Build table rows from the document's line-item sections; if a row lacks some columns, include the row with null for missing cells.
    7. Always return the table even if it's empty.
    8. For table, firstly check how many rows are there before extracting. Double check to verify how many rows are present in the document. To distinguish the row, if there are multiple, you will see pattern repeating.
    9. For table, there will be cases where column data is not present in a table but it will be present in another table connected by HS Code or some code.
    10. Extract all the items from table even if it's huge, no questions asked. You can't extract only some. You need to extract all the items/rows, MUST.
    11. IMPORTANT: Apply the Field-Specific Extraction & Defaulting Rules above for dimensions, packageCount, packageType, grossWeight, harmonizedCode, and goodsDescription columns.
    12. CRITICAL: Apply Page Break & Split Row Handling Rules. Identify and ignore page footers, headers, and page numbers. Merge row fragments that were split by page breaks into single complete rows.
    13. Before finalizing, VERIFY: Count unique item identifiers (not text lines) to confirm actual row count. Ensure no rows were duplicated or lost due to page breaks.
    14. Return only the JSON object, no explanations.
    """
    
    return system_prompt_shipment_table_agent
##################################################
def convert_data_to_json(table_data,page_map):

  tmp_data_json = {"table_data":[]}
  single_table =  {"table_id":1,"table_name":"Main Table","table_data":{"rows":[]}}
  for row_id, row_items in enumerate(table_data["item_value"]):
    single_row = {"row_id":row_id,"row_data":[]}
    for col_id, col_data in enumerate(row_items):
        value = col_data["value"]
        if col_data["value"] == None:
          value = ""
        single_row["row_data"].append({
          "value":str(value),
          "label":col_data["label"],
          "is_label_mapped":False,
          "is_profile_key_found":True,
          "is_pure_autoextraction":True,  
          "is_data_exception_done": False,
          "original_key_label" : col_data["label"],
          "pos" : "0,0,0,0",
          "position":  "0,0,0,0", 
          "is_column_mapped_to_key":False,
          "key_value":col_data["label"]})

    single_table["table_data"]["rows"].append(single_row)  
  tmp_data_json["table_data"].append(single_table)
  return tmp_data_json


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



def get_merged_chunk_wise_table(llm_result_hub):

  combined_data_json = {}

  for chunk_wise_data_json in llm_result_hub:
    if combined_data_json == {}:
      combined_data_json = chunk_wise_data_json
    else:
      try:
        continued_row_id = combined_data_json["table_data"][0]["table_data"]["rows"][-1]["row_id"]+1
      except:
        continued_row_id = 0 

      for new_row_idx, new_row_data in enumerate(chunk_wise_data_json["table_data"][0]["table_data"]["rows"]):
        new_row_data["id"] = continued_row_id
        combined_data_json["table_data"][0]["table_data"]["rows"].append(copy.deepcopy(new_row_data))
        continued_row_id += 1

  return combined_data_json



def get_formatted_table_with_required_parameter(merged_table, ct_doc_id):

    row_children = []
    
    for row_idx, row_data in enumerate(merged_table["table_data"][0]["table_data"]["rows"]):
        single_row = {
                "id": f"{ct_doc_id}.001.{row_idx+1:03}",
                "pos": "",
                "type": "row",
                "STATUS": 0,
                "pageId": "",
                "children": []
                }
        for col_idx, col_data in enumerate(row_data["row_data"]):
             single_row["children"].append(
                 {
                    "v": col_data["value"],
                    "id": f"{ct_doc_id}.001.{row_idx+1:03}.{col_idx+1:03}",
                    "pos": col_data["position"],
                    "type": "cell",
                    "label": col_data["label"],
                    "STATUS": 1,
                    "pageId": col_data["page_id"],
                    "key_value": col_data["label"],
                    "static_value": False,
                    "is_label_mapped": False,
                    "original_key_label": col_data["label"],
                    "table_key_generated": False,
                    "is_profile_key_found": True,
                    "is_data_exception_done": False,
                    "is_pure_autoextraction": True,
                    "is_column_mapped_to_key": False
                  })
        row_children.append(single_row)

    
    return row_children
    

def get_table_with_correction(combined_ra_json, doc_class_wise_process_field, ct_doc_id, ct_batch_idx, ct_doc_idx, definition_data = [],page_sampling_rate = 15):

    user_prompt_hub = []
    llm_result_hub = []
    all_reasoning = ""

    user_content_table = ""
    page_map = {}
    ra_json = combined_ra_json[ct_batch_idx]["nodes"][ct_doc_idx]

    doc_type = ra_json["DocType"]
    field_need_to_extract = []
    existing_key_values = set()

    for doc_class_from_field, field_list in doc_class_wise_process_field.items():
        if (doc_class_from_field.lower().replace(" ", "").strip() in 
            doc_type.lower().replace(" ", "").strip() and 
            doc_class_from_field.lower() != "no_doc_class" and 
            doc_class_from_field.lower() != "address_field_name"):
            field_need_to_extract.extend(field_list)
            for field in field_list:
                existing_key_values.add(field.get("keyValue"))

    for field in doc_class_wise_process_field.get("no_doc_class", []):
        if field.get("keyValue") not in existing_key_values:
            field_need_to_extract.append(field)

    field_need_to_extract = get_modified_keys_based_on_definition(
        definition_data, field_need_to_extract, ra_json.get("id")
    )

    system_prompt_shipment_table_agent = generate_system_prompt_shipment_table_agent(field_need_to_extract)

    
    for  page_idx, page in enumerate(ra_json["children"]):

        page_map[f"{page_idx+1}"] = page["id"]
        # page_wise_paragraph = render_json_to_text_with_layout(page)
        page_wise_paragraph = get_ra_json_to_txt_table_new(page)
        
        if user_content_table == "":
            user_content_table =f"########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"
        else:
            user_content_table = f"{user_content_table}\n########################\nPAGE {page_idx+1}\n########################\n{page_wise_paragraph}"


        if (page_idx + 1) % page_sampling_rate == 0:
            user_prompt_hub.append(user_content_table)
            user_content_table = ""

    user_prompt_hub.append(user_content_table)

    for cwuc_idx, chunk_wise_user_content in enumerate(user_prompt_hub):
        response, reasoning = run_llm(system_prompt_shipment_table_agent, chunk_wise_user_content)
        chunk_wise_table = llm_json_to_dict(response)
        chunk_wise_table = convert_data_to_json(chunk_wise_table ,page_map)
        llm_result_hub.append(chunk_wise_table)
        
    merged_table = get_merged_chunk_wise_table(llm_result_hub)
    merged_table = add_postion_information_to_table([], ra_json, True, merged_table)

    merged_table = get_formatted_table_with_required_parameter(merged_table, ct_doc_id)
    
    return merged_table
    


def find_best_candidate_table(table_report):
    def count_priority_columns(data):
        columns = set(data.get('column_list', []))
        return sum(1 for col in priority_columns if col in columns)
    
    def get_column_count(data):
        return len(data.get('column_list', []))
         
    if table_report == {}:
        return ""
    
    priority_columns = [
        'packageCount', 'packageType', 'dimensions', 
        'grossWeight', 'commodityCode', 'harmonizedCode', 'goodsDescription'
    ]
    
    tables_with_dimensions = {
        key: data for key, data in table_report.items() 
        if 'dimensions' in data.get('column_list', [])
    }
    
    if len(tables_with_dimensions) == 1:
        return list(tables_with_dimensions.keys())[0]
    
    elif len(tables_with_dimensions) > 1:
        max_row_count = max(data['row_count'] for data in tables_with_dimensions.values())
        top_candidates = {
            key: data for key, data in tables_with_dimensions.items() 
            if data['row_count'] == max_row_count
        }
        if len(top_candidates) == 1:
            return list(top_candidates.keys())[0]
        else:
            best_table = max(
                top_candidates.keys(),
                key=lambda k: (
                    count_priority_columns(top_candidates[k]),
                    get_column_count(top_candidates[k])
                )
            )
            return best_table
        
    else:
        candidate_tables = table_report
    
        best_table = max(
            candidate_tables.keys(),
            key=lambda k: (
                count_priority_columns(candidate_tables[k]),
                get_column_count(candidate_tables[k])
            )
        )
        
        return best_table
    


def accumulate_meaningful_column_and_row_count(single_table):
    col_list = []
    row_count = 0

    for row in single_table["children"]:
        row_count += 1
        for col in row["children"]:
            if col["v"].strip() != "" and col["label"] not in col_list:
                col_list.append(col["label"])
    return col_list, row_count
            

def find_candidate_table(combined_data_json):

    table_report = {}

    for batch_idx, batch_wise_data_json in  enumerate(combined_data_json):

        batch_id = batch_wise_data_json["id"]

        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            
            for item_idx, item in enumerate(doc_wise_data_json["children"]):
                if item["type"] == "table":
                    item["table_name"] = f"Table {item_idx+1}"
                    col_list, row_count = accumulate_meaningful_column_and_row_count(item)
                    table_report[doc_id] = {"column_list":col_list, "row_count":row_count,"batch_idx":batch_idx, "doc_idx":doc_idx}
                    
    best_candidate_table_id = find_best_candidate_table(table_report)  
    if best_candidate_table_id == "":
        return "", "", ""
    else:
        return best_candidate_table_id, table_report.get(best_candidate_table_id)["batch_idx"], table_report.get(best_candidate_table_id)["doc_idx"]


def run_shipment_table_agent(combined_ra_json, combined_data_json, process_field):
    msg = "Shipment table generation completed"
    combined_data_json_raw = copy.deepcopy(combined_data_json)
    doc_class_wise_process_field , _ , _ = get_doc_class_wise_process_field(process_field)
    ct_doc_id, ct_batch_idx, ct_doc_idx = find_candidate_table(combined_data_json)
    msg += f"\nThe candidate table was found in the document: {ct_doc_id}"
    if ct_doc_id == "":
        return combined_data_json_raw

    desired_table_with_correction = get_table_with_correction(combined_ra_json, doc_class_wise_process_field, ct_doc_id, ct_batch_idx, ct_doc_idx)
    
    combined_data_json[ct_batch_idx]["nodes"][ct_doc_idx]["children"][0]["children"] = desired_table_with_correction
    combined_data_json[ct_batch_idx]["nodes"][ct_doc_idx]["children"][0]["table_name"] = "Main Table"
    return combined_data_json, msg
    