import json
import re
from typing import Dict, Any, Union, List, Tuple
from dotenv import load_dotenv
from utils.llm_clients import run_llm
from utils.xml_or_ra_json_to_text import get_xml_to_text, get_ra_json_to_txt_kvv, get_ra_json_to_txt_table_old, get_ra_json_to_txt_table_new
from shipment_table_agents.position_adder import add_postion_information_to_table
import copy


def parse_doc_info(prompt_data):
    if isinstance(prompt_data, dict):
        doc_class_str = prompt_data.get("DocClass", "").strip()
        doc_class = [cls.strip() for cls in doc_class_str.split(",") if cls.strip()]
        field_description = prompt_data.get("Field_Description", "").strip()
        rules_description = prompt_data.get("Rules_Description", "").strip()
        return doc_class, field_description, rules_description
    
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
        project_prompt = field_item.get("project_prompt", {})
        process_prompt = field_item.get("process_prompt", {})

        project_doc_class_list, project_field_description, project_rules_description = parse_doc_info(project_prompt)
        process_doc_class_list, process_field_description, process_rules_description = parse_doc_info(process_prompt)
        
        if project_field_description.strip() == "" and process_field_description.strip() == "":
            project_field_description = "Field_Name"

        prompt_map = {}
        project_is_universal = not project_doc_class_list or project_doc_class_list[0].strip().lower() == "none"
        
        has_process_prompt = False
        if isinstance(process_prompt, dict):
            has_process_prompt = bool(process_prompt.get("DocClass") or process_prompt.get("Field_Description"))
        elif isinstance(process_prompt, str):
            has_process_prompt = process_prompt.strip() != ""

        if has_process_prompt:
            if process_field_description.strip() == "":
                process_field_description = project_field_description
            
            if process_rules_description.strip() == "":
                process_rules_description = project_rules_description
            
            if process_doc_class_list and process_doc_class_list[0].strip().lower() != "none":
                for doc_class in process_doc_class_list:
                    prompt_map[doc_class] = (process_field_description, process_rules_description)
            else:
                if project_is_universal:
                    prompt_map["none"] = (process_field_description, process_rules_description)
                else:
                    for doc_class in project_doc_class_list:
                        if doc_class.strip().lower() != "none":
                            prompt_map[doc_class] = (process_field_description, process_rules_description)
                    prompt_map["none"] = (process_field_description, process_rules_description)
        else:
            if project_is_universal:
                prompt_map["none"] = (project_field_description, project_rules_description)
            else:
                for doc_class in project_doc_class_list:
                    if doc_class.strip().lower() != "none":
                        prompt_map[doc_class] = (project_field_description, project_rules_description)

        prompt_groups = {}
        
        for doc_class, (field_desc, rules_desc) in prompt_map.items():
            prompt_key = (field_desc, rules_desc)
            if prompt_key not in prompt_groups:
                prompt_groups[prompt_key] = []
            prompt_groups[prompt_key].append(doc_class)
        
        for (field_description, rules_description), doc_class_group in prompt_groups.items():
            if len(doc_class_group) == 1 and doc_class_group[0] == "none":
                field_item_copy = copy.deepcopy(field_item_new)
                field_item_copy["doc_class_list"] = []
                field_item_copy["field_description"] = field_description
                field_item_copy["rules_description"] = rules_description
                
                if field_item_copy not in process_field_without_doc_type:
                    process_field_without_doc_type.append(field_item_copy)
            else:
                for doc_class in doc_class_group:
                    if doc_class != "none":
                        if doc_class not in updated_process_field_dict:
                            updated_process_field_dict[doc_class] = []
                        
                        field_item_copy = copy.deepcopy(field_item_new)
                        field_item_copy["doc_class_list"] = doc_class_group
                        field_item_copy["field_description"] = field_description
                        field_item_copy["rules_description"] = rules_description
                        
                        updated_process_field_dict[doc_class].append(field_item_copy)
    
    updated_process_field_dict["no_doc_class"] = process_field_without_doc_type
    updated_process_field_dict["address_field_name"] = address_field_name
    return updated_process_field_dict, False, ""


def get_definition_key_list_based_on_doc_id(definition_data, doc_id):
    for item in definition_data:
        if item["document_id"] == doc_id:
            return item["exception_list"]
    return []


def get_modified_keys_based_on_definition(definition_data, field_need_to_extract, doc_id):
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


# ============================================================================
# EXTRACTION PROMPT - Also captures document totals
# ============================================================================

def generate_extraction_system_prompt(field_need_to_extract):
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
        table_section = "Columns to extract:\n"
        for col_item in table_columns:
            table_section += '  - "' + col_item["column"] + '": ' + col_item["description"]
            if col_item["rule"]:
                table_section += ' (Rule: ' + col_item["rule"] + ')'
            table_section += '\n'
    
    system_prompt = """You are a Table Extractor that works with documents in ANY language.

Your task:
1. Extract table rows based on the column definitions provided
2. ALSO look for document-level summary/total values (these are important for validation)

""" + table_section + """

IMPORTANT - While extracting, also look for these DOCUMENT-LEVEL VALUES (not per-row):
- Total package count (total pieces, total quantity, total cartons, etc.)
- Total gross weight (total weight, gross weight total, etc.)
- Total net weight (if available)
- General HS code or harmonized code (if there's a single code for the whole shipment)
- General goods description (if there's one description for all items)
- Package type (if there's a common package type mentioned)

These totals might be labeled in ANY language. Look for summary sections, headers, footers.

OUTPUT FORMAT (strict JSON only):
{
    "item_value": [
        [
            {"label": "COLUMN_NAME", "value": "extracted value or null", "page_no": page number or null}
        ]
    ],
    "document_totals": {
        "total_package_count": <number or null>,
        "total_gross_weight": <number or null>,
        "total_gross_weight_unit": <"kg" or "lbs" or null>,
        "total_net_weight": <number or null>,
        "general_hs_code": <string or null>,
        "general_goods_description": <string or null>,
        "package_type": <string or null>
    }
}

RULES:
1. Extract ALL rows - do not skip any
2. Handle page breaks - merge split rows
3. If value not found, use null
4. Document totals are SEPARATE from row data - look for summary/total lines
5. Return ONLY JSON, no explanations
"""
    
    return system_prompt


# ============================================================================
# VALIDATION PROMPT - Uses accumulated totals
# ============================================================================

def generate_validation_system_prompt():
    return """You are a Table Data Validator. You will validate and correct extracted table data.

You receive:
1. Extracted table data
2. Document totals (accumulated from the entire document during extraction)

## VALIDATION RULES - APPLY STRICTLY:

### RULE 1: PACKAGE COUNT (packageCount column)
Look at document_totals.total_package_count and compare with extracted data:
- Calculate SUM of all packageCount values in the table
- IF document total exists AND sum != document total:
    -> Set FIRST row packageCount = document total
    -> Set all other rows packageCount = 0
- ELSE IF document total exists AND sum == document total:
    -> Set row wise packageCount = row wise packageCount value as-is
- ELSE IF row wise packageCount available only:
    -> Set packageCount = 1 for EVERY row
- ELSE IF all packageCount values are null/empty:
    -> Set packageCount = 1 for EVERY row

### RULE 2: PACKAGE TYPE (packageType column)
- IF any row has packageType = null or empty:
    -> Set that row's packageType = "PCE"
- IF document_totals.package_type exists, you may use it as reference

### RULE 3: GROSS WEIGHT (grossWeight column)
Look at document_totals.total_gross_weight:
- IF individual rows have grossWeight values -> Keep them
- ELSE IF rows have null/0 but document total exists:
    -> Set FIRST row grossWeight = document total
    -> Set ALL other rows grossWeight = 0

### RULE 4: HARMONIZED CODE (harmonizedCode column)
- Count unique harmonizedCode values in the table
- IF harmonizedCode value exists for all rows -> Keep as-is (already correct)
- IF all rows are null but document_totals.general_hs_code exists:
    -> Apply general_hs_code to ALL rows
- IF number of harmonizedCode more than row count:
    -> apply first harmonizedCode to all rows

### RULE 5: GOODS DESCRIPTION (goodsDescription column)
- IF individual rows have goods description values -> Keep as-is (already correct)
- IF all rows null but document_totals.general_goods_description exists:
    -> Apply to ALL rows

### RULE 6: DIMENSIONS (dimensions column)
- IF null -> Keep as null (never invent)
- IF exists -> Keep as-is

## OUTPUT FORMAT:
{
    "validation_summary": {
        "total_rows": <number>,
        "document_total_packages": <from document_totals or null>,
        "sum_extracted_packages": <calculated sum>,
        "corrections_applied": ["list of corrections made"]
    },
    "corrected_item_value": [
        [
            {"label": "column", "value": "value", "page_no": 1}
        ]
    ]
}

Return ONLY JSON. Return ALL rows with ALL columns.
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def llm_json_to_dict(llm_response):
    if not llm_response:
        return {}
        
    cleaned = llm_response.strip()
    
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    start_brace = cleaned.find("{")
    
    if start_brace == -1:
        print("Error: No JSON object found in response")
        return {}
    
    brace_count = 0
    end_pos = -1
    for i, char in enumerate(cleaned[start_brace:], start_brace):
        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                end_pos = i
                break
    
    if end_pos != -1:
        cleaned = cleaned[start_brace:end_pos + 1]
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("Error parsing JSON: " + str(e))
        print("Attempted to parse: " + cleaned[:300] + "...")
        return {}


def convert_data_to_json(table_data, page_map):
    tmp_data_json = {"table_data": []}
    single_table = {"table_id": 1, "table_name": "Main Table", "table_data": {"rows": []}}
    
    if "item_value" not in table_data or not table_data["item_value"]:
        tmp_data_json["table_data"].append(single_table)
        return tmp_data_json
    
    for row_id, row_items in enumerate(table_data["item_value"]):
        single_row = {"row_id": row_id, "row_data": []}
        for col_id, col_data in enumerate(row_items):
            value = col_data.get("value", "")
            if value is None:
                value = ""
            single_row["row_data"].append({
                "value": str(value),
                "label": col_data.get("label", ""),
                "is_label_mapped": False,
                "is_profile_key_found": True,
                "is_pure_autoextraction": True,
                "is_data_exception_done": False,
                "original_key_label": col_data.get("label", ""),
                "pos": "0,0,0,0",
                "position": "0,0,0,0",
                "is_column_mapped_to_key": False,
                "key_value": col_data.get("label", ""),
                "page_no": col_data.get("page_no")
            })
        single_table["table_data"]["rows"].append(single_row)
    
    tmp_data_json["table_data"].append(single_table)
    return tmp_data_json


def get_merged_chunk_wise_table(llm_result_hub):
    combined_data_json = {}

    for chunk_data in llm_result_hub:
        if not chunk_data.get("table_data"):
            continue
            
        if combined_data_json == {}:
            combined_data_json = copy.deepcopy(chunk_data)
        else:
            try:
                existing_rows = combined_data_json["table_data"][0]["table_data"]["rows"]
                continued_row_id = existing_rows[-1]["row_id"] + 1 if existing_rows else 0
            except:
                continued_row_id = 0

            new_rows = chunk_data.get("table_data", [{}])[0].get("table_data", {}).get("rows", [])
            for new_row_data in new_rows:
                new_row_copy = copy.deepcopy(new_row_data)
                new_row_copy["row_id"] = continued_row_id
                combined_data_json["table_data"][0]["table_data"]["rows"].append(new_row_copy)
                continued_row_id += 1

    if not combined_data_json:
        combined_data_json = {"table_data": [{"table_id": 1, "table_name": "Main Table", "table_data": {"rows": []}}]}
    
    return combined_data_json


def merge_document_totals(all_totals):
    """
    Merge document totals from multiple chunks.
    Takes the first non-null value found for each field.
    """
    merged = {
        "total_package_count": None,
        "total_gross_weight": None,
        "total_gross_weight_unit": None,
        "total_net_weight": None,
        "general_hs_code": None,
        "general_goods_description": None,
        "package_type": None
    }
    
    for totals in all_totals:
        if not totals:
            continue
        
        for key in merged.keys():
            if merged[key] is None and totals.get(key) is not None:
                merged[key] = totals[key]
    
    return merged


def get_formatted_table_with_required_parameter(merged_table, ct_doc_id):
    row_children = []
    
    rows = merged_table.get("table_data", [{}])[0].get("table_data", {}).get("rows", [])
    
    for row_idx, row_data in enumerate(rows):
        single_row = {
            "id": ct_doc_id + ".001." + str(row_idx + 1).zfill(3),
            "pos": "",
            "type": "row",
            "STATUS": 0,
            "pageId": "",
            "children": []
        }
        for col_idx, col_data in enumerate(row_data.get("row_data", [])):
            single_row["children"].append({
                "v": col_data.get("value", ""),
                "id": ct_doc_id + ".001." + str(row_idx + 1).zfill(3) + "." + str(col_idx + 1).zfill(3),
                "pos": col_data.get("position", "0,0,0,0"),
                "type": "cell",
                "label": col_data.get("label", ""),
                "STATUS": 1,
                "pageId": col_data.get("page_id", ""),
                "key_value": col_data.get("label", ""),
                "static_value": False,
                "is_label_mapped": False,
                "original_key_label": col_data.get("label", ""),
                "table_key_generated": False,
                "is_profile_key_found": True,
                "is_data_exception_done": False,
                "is_pure_autoextraction": True,
                "is_column_mapped_to_key": False
            })
        row_children.append(single_row)

    return row_children


def merged_table_to_item_value(merged_table):
    """Convert merged table format to item_value format for validation."""
    item_value = []
    
    rows = merged_table.get("table_data", [{}])[0].get("table_data", {}).get("rows", [])
    
    for row_data in rows:
        row_items = []
        for col_data in row_data.get("row_data", []):
            value = col_data.get("value")
            if value == "":
                value = None
            row_items.append({
                "label": col_data.get("label", ""),
                "value": value,
                "page_no": col_data.get("page_no")
            })
        item_value.append(row_items)
    
    return item_value


# ============================================================================
# VALIDATION FUNCTION
# ============================================================================

def validate_extracted_table(item_value, document_totals):
    """
    Validate and correct the extracted table.
    
    Args:
        item_value: List of rows (each row is list of {label, value, page_no})
        document_totals: Accumulated totals from extraction phase
    
    Returns:
        Corrected item_value
    """
    
    if not item_value:
        print("No data to validate")
        return item_value
    
    system_prompt = generate_validation_system_prompt()
    
    user_prompt = """## EXTRACTED TABLE DATA:
```json
""" + json.dumps({"item_value": item_value}, indent=2) + """
```

## DOCUMENT TOTALS (found during extraction):
```json
""" + json.dumps(document_totals, indent=2) + """
```

Apply the validation rules and return corrected data.
"""
    
    print("\n" + "=" * 60)
    print("VALIDATION: Applying rules to extracted table")
    print("Rows: " + str(len(item_value)))
    print("Document totals available: " + str(document_totals))
    print("=" * 60)
    
    response, reasoning = run_llm(system_prompt, user_prompt)
    
    if reasoning:
        print("\nValidation reasoning: " + (reasoning[:500] + "..." if len(reasoning) > 500 else reasoning))
    
    result = llm_json_to_dict(response)
    
    if result and "validation_summary" in result:
        summary = result["validation_summary"]
        print("\n--- Validation Summary ---")
        print("Total rows: " + str(summary.get("total_rows", "N/A")))
        print("Document total packages: " + str(summary.get("document_total_packages", "N/A")))
        print("Sum extracted packages: " + str(summary.get("sum_extracted_packages", "N/A")))
        print("Corrections: " + str(summary.get("corrections_applied", [])))
        print("--------------------------")
    
    if result and "corrected_item_value" in result:
        print("Validation successful, using corrected data")
        return result["corrected_item_value"]
    else:
        print("Validation failed or no corrections needed, using original data")
        return item_value


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def get_table_with_correction(combined_ra_json, doc_class_wise_process_field, ct_doc_id, ct_batch_idx, ct_doc_idx, definition_data=[], page_sampling_rate=15):
    """
    Main extraction and validation function.
    
    Phase 1: Extract table + document totals from each chunk
    Phase 2: Merge rows and accumulate totals
    Phase 3: Validate using accumulated totals
    """
    
    llm_result_hub = []
    all_document_totals = []
    document_pages = []
    page_map = {}
    
    ra_json = combined_ra_json[ct_batch_idx]["nodes"][ct_doc_idx]
    doc_type = ra_json["DocType"]
    
    # Get fields to extract
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

    system_prompt = generate_extraction_system_prompt(field_need_to_extract)

    # Build page list
    for page_idx, page in enumerate(ra_json["children"]):
        page_map[str(page_idx + 1)] = page["id"]
        page_text = get_ra_json_to_txt_table_new(page)
        document_pages.append("PAGE " + str(page_idx + 1) + ":\n" + page_text)

    total_pages = len(document_pages)
    
    print("\n" + "=" * 60)
    print("PHASE 1: EXTRACTION")
    print("Total pages: " + str(total_pages))
    print("Pages per chunk: " + str(page_sampling_rate))
    print("=" * 60)

    # Build chunks
    chunks = []
    for i in range(0, total_pages, page_sampling_rate):
        chunk_end = min(i + page_sampling_rate, total_pages)
        chunk_text = "\n\n".join(document_pages[i:chunk_end])
        chunks.append({
            "text": chunk_text,
            "start": i + 1,
            "end": chunk_end
        })
    
    print("Processing " + str(len(chunks)) + " chunks...")
    
    # Extract from each chunk
    for idx, chunk in enumerate(chunks):
        print("\nChunk " + str(idx + 1) + "/" + str(len(chunks)) + 
              " (pages " + str(chunk["start"]) + "-" + str(chunk["end"]) + ")")
        
        response, reasoning = run_llm(system_prompt, chunk["text"])
        
        if reasoning:
            print("  Reasoning: " + (reasoning[:200] + "..." if len(reasoning) > 200 else reasoning))
        
        chunk_result = llm_json_to_dict(response)
        
        if chunk_result:
            # Get rows
            if "item_value" in chunk_result and chunk_result["item_value"]:
                rows_count = len(chunk_result["item_value"])
                print("  Extracted " + str(rows_count) + " rows")
                converted = convert_data_to_json(chunk_result, page_map)
                llm_result_hub.append(converted)
            else:
                print("  No rows found in this chunk")
            
            # Get document totals
            if "document_totals" in chunk_result:
                totals = chunk_result["document_totals"]
                print("  Document totals found: " + str({k: v for k, v in totals.items() if v is not None}))
                all_document_totals.append(totals)
        else:
            print("  Failed to parse response")

    # ========================================
    # PHASE 2: MERGE
    # ========================================
    
    print("\n" + "=" * 60)
    print("PHASE 2: MERGING")
    print("=" * 60)
    
    merged_table = get_merged_chunk_wise_table(llm_result_hub)
    merged_totals = merge_document_totals(all_document_totals)
    
    total_rows = len(merged_table.get("table_data", [{}])[0].get("table_data", {}).get("rows", []))
    print("Total rows after merge: " + str(total_rows))
    print("Merged document totals: " + str({k: v for k, v in merged_totals.items() if v is not None}))

    # ========================================
    # PHASE 3: VALIDATION
    # ========================================
    
    print("\n" + "=" * 60)
    print("PHASE 3: VALIDATION")
    print("=" * 60)
    
    if total_rows > 0:
        # Convert to item_value format
        item_value = merged_table_to_item_value(merged_table)
        
        # Validate
        corrected_item_value = validate_extracted_table(item_value, merged_totals)
        
        # Convert back
        if corrected_item_value:
            corrected_table = {"item_value": corrected_item_value}
            merged_table = convert_data_to_json(corrected_table, page_map)
    else:
        print("No rows to validate")

    # ========================================
    # PHASE 4: FORMAT OUTPUT
    # ========================================
    
    merged_table = add_postion_information_to_table([], ra_json, True, merged_table)
    merged_table = get_formatted_table_with_required_parameter(merged_table, ct_doc_id)

    print("\n" + "=" * 60)
    print("COMPLETE: Final table has " + str(len(merged_table)) + " rows")
    print("=" * 60)

    return merged_table


# ============================================================================
# CANDIDATE TABLE FUNCTIONS
# ============================================================================

def find_best_candidate_table(table_report):
    def count_priority_columns(data):
        columns = set(data.get("column_list", []))
        priority_columns = ["packageCount", "packageType", "dimensions", "grossWeight", "commodityCode", "harmonizedCode", "goodsDescription"]
        return sum(1 for col in priority_columns if col in columns)
    
    def get_column_count(data):
        return len(data.get("column_list", []))
    
    if table_report == {}:
        return ""
    
    tables_with_dimensions = {}
    for key, data in table_report.items():
        if "dimensions" in data.get("column_list", []):
            tables_with_dimensions[key] = data
    
    if len(tables_with_dimensions) == 1:
        return list(tables_with_dimensions.keys())[0]
    
    elif len(tables_with_dimensions) > 1:
        max_row_count = max(data["row_count"] for data in tables_with_dimensions.values())
        top_candidates = {}
        for key, data in tables_with_dimensions.items():
            if data["row_count"] == max_row_count:
                top_candidates[key] = data
        
        if len(top_candidates) == 1:
            return list(top_candidates.keys())[0]
        else:
            best_table = max(
                top_candidates.keys(),
                key=lambda k: (count_priority_columns(top_candidates[k]), get_column_count(top_candidates[k]))
            )
            return best_table
    
    else:
        best_table = max(
            table_report.keys(),
            key=lambda k: (count_priority_columns(table_report[k]), get_column_count(table_report[k]))
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

    for batch_idx, batch_wise_data_json in enumerate(combined_data_json):
        for doc_idx, doc_wise_data_json in enumerate(batch_wise_data_json["nodes"]):
            doc_id = doc_wise_data_json["id"]
            
            for item_idx, item in enumerate(doc_wise_data_json["children"]):
                if item["type"] == "table":
                    item["table_name"] = "Table " + str(item_idx + 1)
                    col_list, row_count = accumulate_meaningful_column_and_row_count(item)
                    table_report[doc_id] = {
                        "column_list": col_list,
                        "row_count": row_count,
                        "batch_idx": batch_idx,
                        "doc_idx": doc_idx
                    }
    
    best_candidate_table_id = find_best_candidate_table(table_report)
    if best_candidate_table_id == "":
        return "", "", ""
    else:
        return (
            best_candidate_table_id,
            table_report.get(best_candidate_table_id)["batch_idx"],
            table_report.get(best_candidate_table_id)["doc_idx"]
        )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def run_shipment_table_agent(combined_ra_json, combined_data_json, process_field):
    msg = "Shipment table generation completed"
    combined_data_json_raw = copy.deepcopy(combined_data_json)
    doc_class_wise_process_field, _, _ = get_doc_class_wise_process_field(process_field)
    ct_doc_id, ct_batch_idx, ct_doc_idx = find_candidate_table(combined_data_json)
    msg += "\nCandidate table document: " + str(ct_doc_id)
    
    if ct_doc_id == "":
        return combined_data_json_raw, msg

    desired_table = get_table_with_correction(
        combined_ra_json,
        doc_class_wise_process_field,
        ct_doc_id,
        ct_batch_idx,
        ct_doc_idx
    )
    
    combined_data_json[ct_batch_idx]["nodes"][ct_doc_idx]["children"][0]["children"] = desired_table
    combined_data_json[ct_batch_idx]["nodes"][ct_doc_idx]["children"][0]["table_name"] = "Main Table"
    
    return combined_data_json, msg