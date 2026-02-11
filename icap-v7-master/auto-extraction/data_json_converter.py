import uuid

def generate_unique_id():
    return str(uuid.uuid4())



def convert_data_json_to_v6_type(data_json_current,ra_json,combined_data_json_ids):

    doc_id = ra_json["id"].strip()
    v6_type_data_json = {
        "id": doc_id,
        "TYPE": ra_json.get("TYPE"),
        "bvOCR": ra_json.get("bvOCR"),
        "nodes": [],
        "STATUS": ra_json.get("STATUS"),
        "Vendor": "",
        "DocType": ra_json.get("DocType"),
        "Project": ra_json.get("Project"),
        "Language": ra_json.get("Language"),
        "batch_type": ra_json.get("batch_type"),
        "bvFilePath": ra_json.get("bvFilePath"),
        "bvBatchType": ra_json.get("bvBatchType"),
        "DefinitionID": ra_json.get("DefinitionID"),
        "DocumentType": ra_json.get("DocumentType"),
        "aidbServerIP": ra_json.get("aidbServerIP"),
        "bvPageRotate": ra_json.get("bvPageRotate"),
        "bvBarcodeRead": ra_json.get("bvBarcodeRead"),
        "NameMatchingText": ra_json.get("NameMatchingText"),
        "bvSelectedDocTypes": ra_json.get("bvSelectedDocTypes"),
        "definition_version": ra_json.get("definition_version")
    }



    for data_json_idx, data_json_single in enumerate(data_json_current["documents"]):
        data_json_id_actual = combined_data_json_ids[data_json_idx] - 1
        doc_children_counter = 1
        vendor = data_json_single.get("vendor",{}).get("vendor","")
        key_value_list = data_json_single["key_data"]
        table_list = data_json_single["table_data"]

        if  v6_type_data_json["Vendor"] == "":
            v6_type_data_json["Vendor"] = vendor

        doc_wise_v6_type_data_json  = {
            "id": f"{doc_id}.{data_json_id_actual+1:02}",
            "ext": ra_json.get("batch_type"),
            "type": ra_json["nodes"][data_json_idx]["type"],
            "Vendor": vendor,
            "DocType": ra_json["nodes"][data_json_idx]["DocType"],
            "Project": ra_json["nodes"][data_json_idx]["Project"],
            "file_path": ra_json["nodes"][data_json_idx]["file_path"],
            "layout_id": ra_json["nodes"][data_json_idx]["layout_id"],
            "Language":ra_json["nodes"][data_json_idx]["Language"],
            "children": [],
            "DefinitionID":ra_json["nodes"][data_json_idx]["DefinitionID"],
            "DocumentType":ra_json["nodes"][data_json_idx]["DocumentType"],
            "NameMatchingText" : ra_json["nodes"][data_json_idx]["NameMatchingText"]
        }


        for table_idx, single_table in enumerate(table_list):
            table_wise_v6_type_data_json = {
                "id": f"{doc_id}.{data_json_id_actual+1:02}.{table_idx+1:03}",
                "pos": "",
                "type": "table",
                "STATUS": 0,
                "pageId": "",
                "children": [],
                "table_id":single_table["table_id"],
                "table_name":single_table["table_name"],
                "table_unique_id": generate_unique_id()
            }
            doc_children_counter += 1
            for row_idx, single_row in enumerate(single_table["table_data"]["rows"]):
                row_wise_v6_type_data_json = {
                    "id": f"{doc_id}.{data_json_id_actual+1:02}.{table_idx+1:03}.{row_idx+1:03}",
                    "pos": "",
                    "type": "row",
                    "STATUS": 0,
                    "pageId": "",
                    "children": []
                }

                for col_id, col_data in enumerate(single_row["row_data"]):
                    cell_wise_v6_type_data_json = {
                        "v": col_data.get("value"),
                        "id":f"{doc_id}.{data_json_id_actual+1:02}.{table_idx+1:03}.{row_idx+1:03}.{col_id+1:03}",
                        "pos": col_data.get("position",""),
                        "type": "cell",
                        "label": col_data.get("label"),
                        "STATUS": 0,
                        "pageId": col_data.get("page_id",""),
                        "static_value": False,
                        "table_key_generated": False,
                        "is_profile_key_found":col_data.get("is_profile_key_found"),
                        "is_label_mapped":col_data.get("is_label_mapped"),
                        "is_data_exception_done": col_data.get("is_data_exception_done"),
                        "is_pure_autoextraction" : col_data.get("is_pure_autoextraction"),
                        "original_key_label" : col_data.get("original_key_label"),
                        "is_column_mapped_to_key": col_data.get("is_column_mapped_to_key",False),
                        "key_value": col_data.get("key_value")
                        }
                    
                    row_wise_v6_type_data_json["children"].append(cell_wise_v6_type_data_json)
                table_wise_v6_type_data_json["children"].append(row_wise_v6_type_data_json)
            doc_wise_v6_type_data_json["children"].append(table_wise_v6_type_data_json)



        key_wise_v6_type_data_json = {
          "id": f"{doc_id}.{data_json_id_actual+1:02}.{doc_children_counter:03}",
          "pos": "",
          "type": "key",
          "STATUS": 0,
          "pageId": "",
          "children": []
        }
        for kv_idx, kv_pair in enumerate(key_value_list):
            status_code_for_v6 = kv_pair.get("STATUS",111)
            #status_code_for_v6 = 111
            
            if kv_pair.get("children",[]) == []:
                
                single_kv_v6_wise = {
                    "v": kv_pair.get("value"),
                    "id": f"{doc_id}.{data_json_id_actual+1:02}.{doc_children_counter:03}.{kv_idx+1:03}",
                    "pos": kv_pair.get("value_position"),
                    "type": "key_detail",
                    "label": kv_pair.get("key"),
                    "STATUS": status_code_for_v6,
                    "export": False,
                    "pageId": kv_pair.get("page_id"),
                    "children": [],
                    "unique_id": generate_unique_id(),
                    "block_type": "",
                    "advanceSettings": {},
                    "is_label_mapped":kv_pair.get("is_label_mapped"),
                    "is_profile_key_found":kv_pair.get("is_profile_key_found"),
                    "is_data_exception_done": kv_pair.get("is_data_exception_done"),
                    "is_pure_autoextraction" : kv_pair.get("is_pure_autoextraction"),
                    "original_key_label" : kv_pair.get("original_key_label"),
                    "is_key_from_table" : kv_pair.get("is_key_from_table",False),
                    "key_value": kv_pair.get("key_value")
                }
                
                if kv_pair.get("qualifier_parent"):
                    single_kv_v6_wise["qualifier_parent"] = kv_pair["qualifier_parent"]
                    
                key_wise_v6_type_data_json["children"].append(single_kv_v6_wise)
            else:
                single_kv_v6_wise = {
                    "v": "",
                    "id": f"{doc_id}.{data_json_id_actual+1:02}.{doc_children_counter:03}.{kv_idx+1:03}",
                    "pos": kv_pair.get("value_position"),
                    "type": "key_detail",
                    "label": kv_pair.get("key"),
                    "STATUS": status_code_for_v6,
                    "export": False,
                    "pageId": kv_pair.get("page_id"),
                    "children": [],
                    "unique_id": generate_unique_id(),
                    "block_type": "",
                    "advanceSettings": {},
                    "auto_lookup_unresolved" : kv_pair.get("auto_lookup_unresolved",False),
                    "is_label_mapped":kv_pair.get("is_label_mapped"),
                    "is_profile_key_found":kv_pair.get("is_profile_key_found"),
                    "is_data_exception_done": kv_pair.get("is_data_exception_done"),
                    "is_pure_autoextraction" : kv_pair.get("is_pure_autoextraction"),
                    "original_key_label" : kv_pair.get("original_key_label"),
                    "is_key_from_table" : kv_pair.get("is_key_from_table",False),
                    "key_value": kv_pair.get("key_value")
                }
                block_data = ""
                for inner_kv_idx, inner_kv_pair in enumerate(kv_pair["children"]):
                    if inner_kv_pair["key"] == "block":
                        block_data = inner_kv_pair["value"]
                        
                    inner_single_kv_v6_wise = {
                        "v": inner_kv_pair["value"],
                        "id":f"{doc_id}.{data_json_id_actual+1:02}.{doc_children_counter:03}.{kv_idx+1:03}.{inner_kv_idx+1:03}",
                        "type": "keyTextDetail",
                        "label": inner_kv_pair["key"],
                        "STATUS": status_code_for_v6,
                        "children": [],
                        "is_profile_key_found":inner_kv_pair.get("is_profile_key_found"),
                        "is_label_mapped":inner_kv_pair.get("is_label_mapped"),
                        "is_pure_autoextraction" : kv_pair.get("is_pure_autoextraction"),
                        "original_key_label" : inner_kv_pair.get("original_key_label"),
                        "key_value": inner_kv_pair.get("key_value")

                    }
                   
                    single_kv_v6_wise["children"].append(inner_single_kv_v6_wise)
                single_kv_v6_wise["v"] = block_data
                
                if kv_pair.get("qualifier_parent"):
                    single_kv_v6_wise["qualifier_parent"] = kv_pair["qualifier_parent"]
                    
                key_wise_v6_type_data_json["children"].append(single_kv_v6_wise)

        doc_wise_v6_type_data_json["children"].append(key_wise_v6_type_data_json)
        v6_type_data_json["nodes"].append(doc_wise_v6_type_data_json)
        
    return v6_type_data_json