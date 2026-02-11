

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


        
            


