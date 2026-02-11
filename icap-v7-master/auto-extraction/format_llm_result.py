import json
from rapidfuzz import fuzz
import copy
import re
import ast
import html
import unicodedata


def replace_unicode_escape(match):
    """
    Helper function to replace Unicode escape sequences with actual characters
    """
    try:
        code_point = int(match.group(1), 16)
        return chr(code_point)
    # Return original if conversion fails
    except ValueError:
        return match.group(0)

def normalize_unicode_text(text):
    """
    Normalize Unicode text by handling escaped sequences and HTML entities
    """
    if not text:
        return text
    
    try:
        # Handle escaped Unicode sequences like \\u00f3 -> ó
        text = text.encode().decode('unicode_escape')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Handle patterns like \\u00f3, \\U00b0, etc. if unicode_escape fails
        text = re.sub(r'\\[uU]([0-9a-fA-F]{4})', replace_unicode_escape, text)
    
    try:
        # Decode HTML entities like &amp;, &lt;, etc.
        text = html.unescape(text)
    except:
        pass
    
    try:
        # Normalize Unicode to NFC form (composed characters)
        text = unicodedata.normalize('NFC', text)
    except:
        pass
    
    return text


def format_vendor(page_id,vendor_data):
    try:
        vendor_data = vendor_data.replace(":","").split("vendor")[1].replace(","," ").replace('"','')
    except:
        return {"vendor": "",
            "vendor_position": "0,0,0,0",
            "page_id": page_id}
        pass
    
    # Add Unicode normalization
    vendor_name = normalize_unicode_text(vendor_data.strip())
    return {"vendor": vendor_data.strip(),
            "vendor_position": "0,0,0,0",
            "page_id": page_id}
    
def is_kv_unique(k_new,v_new,prev_key_list):
    
    is_kv_unq = True
    for kv_old in prev_key_list:
        key_matched_score = fuzz.ratio(kv_old["key"].lower(), k_new.lower())
        value_matched_score = fuzz.ratio(kv_old["value"].lower(), v_new.lower())
        if  key_matched_score >= 90 and  value_matched_score >= 90:
            is_kv_unq = False
            break
        
    return is_kv_unq
    

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

            # Add Unicode normalization and HTML entity decoding
            k = normalize_unicode_text(k.strip())
            v = normalize_unicode_text(v.strip())
            
            # Exceptional case
            if "§ £ £ £ £ £ £ £ £ £ £ £ £ £ £ £" in v:
                v = v.split("§ £ £ £ £ £ £ £ £ £ £ £ £ £ £ £")[0].strip()

            if is_kv_unique(k.strip(),v.strip(),result):
                result.append({
                                "key": k.strip(),
                                "key_position": "0,0,0,0",
                                "value": v.strip(),
                                "value_position": "0,0,0,0",
                                "page_id": page_id,
                                "original_key":k.strip(),
                                "is_label_mapped":False,
                                "is_profile_key_found":False,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label" : k.strip()
                                })
            
    else:
   
        key_value_data = key_value_data.strip("[]").replace("\n", "").replace("    ", " ")
        pattern = r'"([^"]+)":\s*"([^"]+)"'
        matches = re.findall(pattern, key_value_data)
        
        for kv in matches:
            k,v = kv[0],kv[1]

            # Add Unicode normalization and HTML entity decoding
            k = normalize_unicode_text(k.strip())
            v = normalize_unicode_text(v.strip())

            # Exceptional case
            if "§ £ £ £ £ £ £ £ £ £ £ £ £ £ £ £" in v:
                v = v.split("§ £ £ £ £ £ £ £ £ £ £ £ £ £ £ £")[0].strip()
            
            if is_kv_unique(k.strip(),v.strip(),result):
                result.append({
                                "key": k.strip(),
                                "key_position": "0,0,0,0",
                                "value": v.strip(),
                                "value_position": "0,0,0,0",
                                "page_id": page_id, 
                                "original_key":k.strip(),
                                "is_label_mapped":False,
                                "is_profile_key_found":False,
                                "is_data_exception_done": False,
                                "is_pure_autoextraction" : True,
                                "original_key_label" : k.strip()
                                })
        
            
    return result

def format_table_data_old_v1(page_id,table_data):
    table_data_all = {"table_data":[]}
    for table_id, table in enumerate(table_data):
        
        rows = table.split("row")[1:]
        table_data_single = {"table_id":table_id,"table_name":f"table{table_id+1}","table_data":{"rows":[]}}
        for row_id , row in enumerate(rows):
            row_single = {"row_id":row_id,"row_data":[]}
            row_values = re.findall(r'\{.*?\}', row, re.DOTALL)
            if len(row_values) == 1 and row_values[0].count("label") > 1 and row_values[0].count("value") > 1:
                row_values = [rv for rv in row_values[0].split('"label":') if "value" in rv]
                
                for rv in row_values:
                    
                    label = rv.split('"value":')[0].replace('"','').replace(',','').replace('}','').replace('{','').replace(']','').replace('[','')
                    value = rv.split('"value":')[1].replace('"','')
                    if value[-1] == ",":
                        value = value[:-1]
                    value = value.replace('}','').replace('{','').replace(']','').replace('[','')
                    row_single["row_data"].append({"value":value.strip(),"label":label.strip(),"page_id":page_id,"position":"0,0,0,0"})
                table_data_single["table_data"]["rows"].append(row_single)
            else:
                for rv in row_values:
                    value = rv.split('"label":')[1].split('"value":')[1].replace('}','').replace('{','').replace(']','').replace('[','').replace('"','').strip()
                    if len(value) > 1 :
                        if value[-1] == ",":
                            value = value[:-1]
                    label = rv.split('"label":')[1].split('"value":')[0].replace('"','').replace(',',' ').replace('}','').replace('{','').replace(']','').replace('[','')
                    row_single["row_data"].append({"value":value.strip(),"label":label.strip(),"page_id":page_id,"position":"0,0,0,0"})
                table_data_single["table_data"]["rows"].append(row_single)
                
        table_data_all["table_data"].append(table_data_single)   
    return table_data_all



def get_formatted_llm_kvv_data(results):
    
    vendor = {}
    key_value_pairs = []
    is_vendor_added = False
    
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
            key_value_data = ""
            pass

        
        
        
        if not is_vendor_added:
            vendor = format_vendor(page_id,vendor_data)
            is_vendor_added = True
        
        
        
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
             
    return {"vendor" : vendor,"key_data":key_value_pairs}








def format_table_data_old_v2(input_str):
    
    def parse_string_manually(input_str):
        input_str = re.sub(r"^[^:]*:", "", input_str)
        items = re.split(r"'\], \['|], \[", input_str)
        
        dict_list = []
        for item in items:
            parts = item.split("', '")
            if len(parts) == 2:
                value = parts[0].strip(" '[]")
                label = re.sub(r"'].*$", "", parts[1].strip(" '[]"))
                dict_list.append({'value': value, 'label': label, 'is_pure_autoextraction':True, 'is_data_exception_done': False, 'original_key_label' : label,"is_column_mapped_to_key":False})
        
        return dict_list
    
    results = {"table_data":[]}
    
    table_all = input_str.split('Summary Table')
    normal_tables = table_all[0].split('table')[1:]
    summary_table = table_all[1]
    table_id_tracker = 0
    for table_id, table in enumerate(normal_tables):
        table_id_tracker = table_id
        single_table = {"table_id":table_id, "table_name":f"table{table_id+1}","table_data":{"rows":[]}}
        rows = table.split("row")[1:]
        for row_id, row in enumerate(rows):
            row_data = {"row_id":row_id,"row_data":parse_string_manually(row)}
            single_table["table_data"]["rows"].append(row_data)
            
        results["table_data"].append(single_table)
    
    summary_table_temp = {"table_id":table_id_tracker+1, "table_name":f"Summary Table","table_data":{"rows":[]}}
    rows = summary_table.split("row")[1:]
    for row_id, row in enumerate(rows):
        row_data = {"row_id":row_id,"row_data":parse_string_manually(row)}
        summary_table_temp["table_data"]["rows"].append(row_data)
        
    results["table_data"].append(summary_table_temp)
            
    
    return results


def get_column_name_extension_added(col_name_tracker,label):
    new_label = label
    if label not in col_name_tracker.keys():
        col_name_tracker[label] = ["0"]
        return new_label
    else:
        new_label = f"{label}_{col_name_tracker[label][-1]}"
        col_name_tracker[label].append(f"{len(col_name_tracker[label])}")
        return new_label
        
    
    
    
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
                col_name_tracker = {}
                for item_id, item in enumerate(row_items):
                    if item_id == 0:
                        item = item[1:]
                    try:
                        try:
                            value = item.split("', '")[0].replace("['","").strip()
                            label = item.split("', '")[1].replace("']","").strip()
                            if label.startswith("'"):
                                label = label[len("'"):]
                            if value.startswith('["'):
                                value = value[len('["'):]
                                
                            label = get_column_name_extension_added(col_name_tracker,label)
                            
                            single_row["row_data"].append({"value":value,"label":label,"is_pure_autoextraction":True, "is_data_exception_done": False, "original_key_label" : label,"is_column_mapped_to_key":False})
                        except:
                            value = item.split('", ')[0].replace("['","").strip()
                            label = item.split('", ')[1].replace("']","").strip()
                            if label.startswith("'"):
                                label = label[len("'"):]
                            if value.startswith('["'):
                                value = value[len('["'):]
                            label = get_column_name_extension_added(col_name_tracker,label)
                            single_row["row_data"].append({"value":value,"label":label, "is_pure_autoextraction":True, "is_data_exception_done": False, "original_key_label" : label,"is_column_mapped_to_key":False})
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
                col_name_tracker = {}
                for item in row_data:
                    label = get_column_name_extension_added(col_name_tracker,item[1])
                    #label = item[1]
                    single_row["row_data"].append({"value":item[0],"label":label,"is_pure_autoextraction":True,  "is_data_exception_done": False,"original_key_label" : label,"is_column_mapped_to_key":False})
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




# def get_formatted_address_data(address_data):
#     result = []
#     try:
#         result  = [json.loads(item.replace("'",'"')) for item in address_data]
#     except:
#         result = [json.loads(json.dumps(ast.literal_eval(item))) for item in address_data]
#         pass
#     return result





def get_formatted_address_data(address_data):
    result = []
    
    for idx, item in enumerate(address_data):
        try:
            parsed = json.loads(item)
            result.append(parsed)
        except:
            try:
                parsed = ast.literal_eval(item)
                result.append(json.loads(json.dumps(parsed)))
            except:
                try:
                    open_curly = item.count('{')
                    close_curly = item.count('}')
                    open_square = item.count('[')
                    close_square = item.count(']')
                    
                    repaired = item
                    if open_square > close_square:
                        repaired += ']' * (open_square - close_square)
                    if open_curly > close_curly:
                        repaired += '}' * (open_curly - close_curly)
                    
                    parsed = json.loads(repaired.replace("'", '"'))
                    result.append(parsed)
                    print(f"WARNING: Repaired incomplete JSON at index {idx}")
                except:
                    print(f"ERROR: Could not parse item {idx}: {item[:200]}...")
                    continue
    
    return result