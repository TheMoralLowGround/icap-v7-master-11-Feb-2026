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
    address_partial_field_name = []
    for idx, field_item in enumerate(process_field):
        
        if field_item["type"] == "addressBlock":
            address_field_name.append(field_item["keyValue"])
        elif field_item["type"] == "addressBlockPartial":
            address_partial_field_name.append(field_item["keyValue"])

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
                print(f"[FALLBACK] Profile Field_Description is empty for '{field_item['keyValue']}', using project Field_Description: {project_field_description}")
            
            # If process Rules_Description is empty, fall back to project Rules_Description
            if process_rules_description.strip() == "":
                process_rules_description = project_rules_description
                print(f"[FALLBACK] Profile Rules_Description is empty for '{field_item['keyValue']}', using project Rules_Description: {project_rules_description}")
            
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
                    print(f"\n{'='*80}")
                    print(f"[FORWARDER PROMPT DEBUG]")
                    print(f"Key: {field_item_copy.get('keyValue')}")
                    print(f"Type: {field_item_copy.get('type')}")
                    print(f"Label: {field_item_copy.get('label')}")
                    print(f"Doc Classes: {doc_class_group}")
                    print(f"Field Description: {field_description}")
                    print(f"Rules Description: {rules_description}")
                    print(f"{'='*80}\n")
                
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
                            print(f"\n{'='*80}")
                            print(f"[FORWARDER PROMPT DEBUG - DOC CLASS SPECIFIC]")
                            print(f"Key: {field_item_copy.get('keyValue')}")
                            print(f"Type: {field_item_copy.get('type')}")
                            print(f"Label: {field_item_copy.get('label')}")
                            print(f"Doc Class: {doc_class}")
                            print(f"All Doc Classes: {doc_class_group}")
                            print(f"Field Description: {field_description}")
                            print(f"Rules Description: {rules_description}")
                            print(f"{'='*80}\n")
                        
                        updated_process_field_dict[doc_class].append(field_item_copy)
    
    updated_process_field_dict["no_doc_class"] = process_field_without_doc_type
    updated_process_field_dict["address_field_name"] = address_field_name
    updated_process_field_dict["address_partial_field_name"] = address_partial_field_name
    return updated_process_field_dict, False, ""






    