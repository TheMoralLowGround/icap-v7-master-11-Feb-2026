"""

def get_converted_label(project_config, data_json):

    try:
        key_value_list = data_json['key_data']
        table_data = data_json['table_data']

        for idx, item in enumerate(project_config['keys']):
            if item['type'] != 'Key':
                continue
            
            try:
                mapped_list = [mi.strip() for mi in item['mappedItems'].split('|')]
            except:
                mapped_list = []
                pass
            
            for item_to_map in mapped_list:
                for kv in key_value_list:
                    if kv.get('updated'):
                        continue
                    kv['updated'] = False
                    
                    if item_to_map.lower().strip() == kv['key'].lower().strip():
                        kv['key'] = item['keyLabel']
                        kv['updated'] = True
                    
        
        for idx, item in enumerate(project_config['keys']):
            if item['type'] != 'Table':
                continue
            
            try:
                mapped_list = [mi.strip() for mi in item['mappedItems'].split('|')]
            except:
                mapped_list = []
                pass
            
            for item_to_map in mapped_list:
                
                for table_id, table in enumerate(table_data):
                    for row_id, row in enumerate(table['table_data']['rows']):
                        for col_id, col_value in enumerate(row['row_data']):
                            if col_value.get('updated'):
                                continue
                            col_value['updated'] = False
                            
                            if item_to_map.lower().strip() == col_value['label'].lower().strip():
                                col_value['label'] = item['keyLabel']
                                col_value['updated'] = True
    
    except:
        return data_json
        pass
    return data_json



def get_converted_label(profile_keys, data_json):

    try:
        key_value_list = data_json['key_data']
        for kv in key_value_list:
            if kv.get("is_data_exception_done"):
                kv["key"] = kv["original_key"]
                kv['is_label_mapped'] = False
                kv['is_label_exception_done'] = False
                continue
            
            kv["key"] = kv["original_key"]
            kv['is_label_mapped'] = False
            kv['is_label_exception_done'] = False
            kv["is_data_exception_done"] = False

        if profile_keys == {}:
            return data_json
        
        for idx, item in enumerate(profile_keys):
            if item["project_field__type"] != 'key':
                continue
            
            mapped_list_label_list = item["mapped_labels"]

            for item_to_map in mapped_list_label_list:
                for kv in key_value_list:
                    if kv.get('is_label_mapped'):
                        continue
                    
                    if item_to_map.strip() == kv['original_key'].strip():
                        kv['key'] = item["project_field__label"]
                        kv['is_label_mapped'] = True
                    
    except:
        return data_json
        pass
    return data_json

"""
from rapidfuzz import fuzz




def get_mapped_label(mapped_keys, data_json, is_v6_to_v7_merge = False):

    
    try:
        trace_list = []
        table_col_to_key_list = []
        mapped_keys_for_address_block = []
        if mapped_keys == {}:
            return data_json, mapped_keys_for_address_block, table_col_to_key_list
        mapped_column_for_table = []
        key_value_list = data_json['key_data']
        table_list = data_json["table_data"]
        for idx, item in enumerate(mapped_keys):
            if item.get("keyType","") == "table":
                mapped_column_for_table.append(item)
            elif "[address]" in item["mappedKey"]:
                mapped_keys_for_address_block.append(item)
            else:
                for kv in key_value_list:
                    if kv.get('is_label_mapped'):
                        continue
                    
                    if fuzz.ratio(item["mappedKey"].lower().replace(" ","").strip(), kv['original_key'].lower().replace(" ","").strip()) > 91:

                        print("#######################")
                        print(item["mappedKey"])
                        print(item["keyLabel"])
                        print(kv['original_key'])
                        
                        
                        qualifier_value = item.get("qualifierValue")
                        
                        if item.get("qualifierValue","") in trace_list or item["keyLabel"] in trace_list:
                            continue
                        
                        if is_v6_to_v7_merge and qualifier_value and qualifier_value.strip():
                            
                            kv['key'] = item["qualifierValue"]
                            kv["qualifier_parent"] = item["keyLabel"]
                            trace_list.append(item["qualifierValue"])
                            #print("*******########",kv)
                            #kv['key'] = item["keyLabel"]
                            print("Im in qualifier")
                        elif is_v6_to_v7_merge:
                            kv['key'] = item["keyLabel"]
                            trace_list.append(item["keyLabel"])
                            print("Im in v7")
                        else:
                            kv['key'] = item["keyValue"]
                            print("Im in old way")
                            trace_list.append(item["keyValue"])

                        print("#######################")

                        kv['is_label_mapped'] = True    

        
        for table_idx, table in enumerate(table_list):

            row_data = table["table_data"]["rows"]

            for row_idx, single_row_data in enumerate(row_data):
                single_row = single_row_data["row_data"]
                col_name_tracker = {}
                for col_id, col_data in enumerate(single_row):
                    is_mapped = False
                    is_column_mapped_to_key = False
                    for item_to_map in mapped_column_for_table:
                        if fuzz.ratio(item_to_map["mappedKey"].lower().replace(" ","").strip(), col_data["label"].lower().replace(" ","").strip()) >= 95:
                            
                            
                            # count_tmp = 0
                            
                            # try:
                            #     for idx_tmp in range(col_id):
                            #         if item_to_map["keyLabel"].lower().strip() == single_row[idx_tmp]['label'].lower().strip():
                            #             single_row[idx_tmp]['label'] = f"{single_row[idx_tmp]['label']}_{count_tmp}"
                            #             count_tmp += 1
                            # except:
                            #     pass
                            
                            # try:
                            #     if col_id+1 < len(single_row):
                            #         for idx_tmp in range(col_id+1,len(single_row)):
                            #             if item_to_map["keyLabel"].lower().strip() == single_row[idx_tmp]['label'].lower().strip():
                            #                 single_row[idx_tmp]['label'] = f"{single_row[idx_tmp]['label']}_{count_tmp}"
                            #                 count_tmp += 1    
                            # except:
                            #     pass
                            new_label = item_to_map["keyLabel"]
                            if item_to_map["keyLabel"] not in col_name_tracker.keys():
                                new_label = item_to_map["keyLabel"]
                                col_name_tracker[item_to_map["keyLabel"]] = 0
                            else:
                                tmp_label = item_to_map["keyLabel"]
                                ext = col_name_tracker[item_to_map["keyLabel"]]
                                new_label = f"{tmp_label}_{ext}"
                                col_name_tracker[item_to_map["keyLabel"]] =  col_name_tracker[item_to_map["keyLabel"]] + 1
                                
                                
                            actual_col_label = col_data["label"]
                            if is_v6_to_v7_merge:
                                col_data["label"] = new_label
                            else:
                                col_data["label"] = new_label
                            



                            if item_to_map.get("isTableKey",False):
                                table_key_already_picked = False
                                for single_key_from_table in table_col_to_key_list:
                                    if col_data["label"] == single_key_from_table["key"]:
                                        if col_data['value'].strip() != "":
                                            single_key_from_table["value"] = f"{single_key_from_table['value']},{col_data['value']}"
                                        table_key_already_picked = True
                                        break

                                    
                                if not table_key_already_picked:
                                    table_col_to_key_list.append({
                                    "key": col_data["label"],
                                    "key_position": "0,0,0,0",
                                    "value": col_data["value"],
                                    "value_position": col_data["position"],
                                    "page_id": col_data["page_id"], 
                                    "original_key":col_data["label"],
                                    "is_label_mapped":False,
                                    "is_key_from_table":True,
                                    "is_profile_key_found":True,
                                    "is_data_exception_done": False,
                                    "is_pure_autoextraction" : True,
                                    "original_key_label" : actual_col_label
                                    })
                                
                                is_column_mapped_to_key = True
                                col_data["is_column_mapped_to_key"] = True
                            else:
                                col_data["is_label_mapped"] = True
                                is_mapped = True


                             
                    if not is_mapped:
                        col_data["is_label_mapped"] = False
                    if not is_column_mapped_to_key:
                        col_data["is_column_mapped_to_key"] = False



    except:
        return data_json, [], []
        pass
    return data_json, mapped_keys_for_address_block, table_col_to_key_list