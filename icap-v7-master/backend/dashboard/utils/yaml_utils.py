import yaml
import json
import traceback
from typing import Dict, List
import re
import requests


def check_yaml_syntax(file) -> bool:
    """Check for YAML syntax errors and report the location if any."""
    try:
        file.seek(0)
        yaml.safe_load(file)
        file.seek(0)
        return False
    except yaml.YAMLError as exc:
        if hasattr(exc, "problem_mark"):
            mark = exc.problem_mark
            print(
                f"YAML syntax error at line {mark.line + 1}, column {mark.column + 1}"
            )
        print(f"Error message: {exc}")
        return True


def camel_to_normal(text):
    normal = re.sub(r"(?<!^)(?=[A-Z])", " ", text)
    return " ".join(word.capitalize() for word in normal.split())


def extract_normal_keys(data, project):
    normal_keys = []
    for key, value in data[project]["properties"].items():
        if "properties" not in value.keys() and "items" not in value.keys():
            normal_keys.append({key: value})
    return normal_keys


def get_option_key(
    key,
    value,
    required_items=[],
    compoundKeys="",
    modType="",
    qualifier="",
    type="key",
    keyLabel=None,
    allowed_values=[],
):
    is_value_dict = isinstance(value, dict)
    # Assign qualifier if it is lookupcode and not assigned
    if not qualifier and (type == "lookupCode" or type == "compound"):
        qualifier = key
    return {
        "type": type,
        "export": True,
        "modType": modType,
        "keyLabel": keyLabel if keyLabel else key,
        "keyValue": key,
        "qualifier": qualifier,
        "compoundKeys": compoundKeys,
        "maxLength": value.get("maxLength", None) if is_value_dict else None,
        "example": value.get("example", "") if is_value_dict else None,
        "description": value.get("description", "") if is_value_dict else None,
        "required": key in required_items,
        "addToProcess": key in required_items,
        "prompt": "",
        "allowed_values": allowed_values,
    }


def extract_other_keys(iterator_dict, schema_data):
    key_qualifier = []
    compound_keys = []
    normal_key_list = []
    for key, value in iterator_dict.items():
        ref_item = value.get("items", {}).get("$ref") or value.get("$ref")
        if ref_item:
            # "#/components/schemas/parties"
            ref_value_split = ref_item.split("/")[1:]
            new_data = get_nested_value(schema_data, ref_value_split)
            ck_items, kq_items, nk_l = extract_other_keys(
                {ref_value_split[-1]: new_data}, schema_data
            )
            normal_key_list.extend(nk_l)
            compound_keys.extend(ck_items)
            key_qualifier.extend(kq_items)
            # Create normal key from ref keys
            normal_key_list.append({key: value})
            continue
        properties = value.get("properties", {})
        if not properties:
            properties = value.get("items", {}).get("properties", {})
        if not properties:
            continue
        if (
            ("type" in properties.keys() and "text" in properties.keys())
            or "type" in properties.keys()
            and "number" in properties.keys()
        ):
            key_qualifier.append({key: value})
            continue
        if properties:
            compound_keys.append({key: value})
    return compound_keys, key_qualifier, normal_key_list


def get_nested_value(data, keys):
    """Access nested dictionary using list of keys"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise KeyError(f"Key '{key}' not found at path {keys}")
    return current


def fetch_api_data(description: str):
    try:
        if "list, see" in description:
            api_link = description.split("list, see")[1].strip()
            code = api_link.split("codeListID=")
            if len(code) > 1:
                code = code[1]
                response = requests.get(api_link)
                # print(f"Calling API {api_link} for {code}")
                if response.status_code == 200:
                    response_json = response.json()
                    return response_json, code
                else:
                    print(
                        f"Failed to fetch for code {code} — Status: {response.status_code}"
                    )
    except:
        print("----------Error Fetching DHL API Data-----------")
        print("description", description)
        print(traceback.print_exc())
    return None, ""


def get_all_keys(data):
    keys = set()
    for item in data:
        keys.update(item.keys())
    return list(keys)


def convert_yaml_format_to_def_settings(data: Dict, required_items: List[str]):
    address_block_keys = [
        "parties",
        "consignee",
        "transportcompany",
        "delivery",
        "transportlocation",
        "shipper",
        "pickup",
        "customer",
        "carrier",
        "contact",
        "servicelocation",
        "buyer",
        "supplier",
        "notify",
        "vendoraddress",
    ]
    table_block_keys = ["goodsLines"]

    # Step1:  Go through normal
    new_normal_data = []
    new_compound_keys = []
    new_qualifier_keys = []
    print("PROCESSING NORMAL KEYS")
    for normal_key_item in data["normal"]:
        for key, val in normal_key_item.items():
            # Create compound or lookupCode keys from this.
            # "parties": {
            #     "type": "array",
            #     "items": {
            #       "$ref": "#/components/schemas/parties"
            #     }
            #   }
            if key.lower() in address_block_keys:
                # If it is addressblock just append in normal and then continue the loop
                if key not in [i.get("keyValue") for i in new_normal_data]:
                    new_normal_data.append(
                        get_option_key(
                            key=key,
                            value=val,
                            type="addressBlock",
                            required_items=required_items,
                        )
                    )
                continue
            ref_item = val.get("items", {}).get("$ref", {}) or val.get("$ref")
            if ref_item:
                key_type = "key"
                if key in get_all_keys(data["compound"]):
                    key_type = "compound"
                if key in get_all_keys(data["key_qualifiers"]):
                    key_type = "lookupCode"
                # Append normal key if found ref
                if key not in [
                    i.get("keyValue")
                    for i in new_normal_data
                    if i.get("type") == key_type
                ]:
                    new_normal_data.append(
                        get_option_key(
                            key=key,
                            value=val,
                            type=key_type,
                            required_items=required_items,
                        )
                    )
            else:
                # Normal keys
                # If description has data fetch from DHL API and add to normal array
                allowed_values = []
                if isinstance(val, dict):
                    val_description = val.get("description", "")
                    val_response_data, modType = fetch_api_data(val_description)
                    if val_response_data:
                        try:
                            for api_data in val_response_data.get("Result", []):
                                allowed_values.append(api_data)
                        except:
                            print(traceback.print_exc())
                            pass
                normal_key_item = get_option_key(
                    key,
                    val,
                    required_items=required_items,
                    allowed_values=allowed_values,
                )
                new_normal_data.append(normal_key_item)
    print("COMPLETE NORMAL KEYS PROCESSING")
    # Step2: Go through compound keys
    print("PROCESSING COMPOUND KEYS")
    for compound_key_item in data["compound"]:
        for key, val in compound_key_item.items():
            properties = val.get("properties", {})
            child_required_items = val.get("required", [])
            if not properties:
                properties = val.get("items", {}).get("properties", {})
                if not child_required_items:
                    child_required_items = val.get("items", {}).get("required", [])
            if not properties:
                continue
            if key.lower() in address_block_keys:
                # If it is addressblock just append in normal and then continue the loop
                if key not in [i.get("keyValue") for i in new_normal_data]:
                    new_normal_data.append(
                        get_option_key(
                            key=key,
                            value=val,
                            type="addressBlock",
                            required_items=required_items,
                        )
                    )
                continue
            else:
                compound_dict = {}
                compound_dict["name"] = key
                compound_dict["keyItems"] = []
                if key not in [i.get("keyValue") for i in new_normal_data]:
                    new_normal_data.append(
                        get_option_key(
                            key=key,
                            value=val,
                            type="compound",
                            required_items=required_items,
                        )
                    )
            for property_key, property_value in properties.items():
                if property_key.lower() in address_block_keys:
                    # If it is addressblock found in nested loop just append in normal and then continue the loop
                    if property_key not in [i.get("keyValue") for i in new_normal_data]:
                        new_normal_data.append(
                            get_option_key(
                                key=property_key,
                                value=property_value,
                                type="addressBlock",
                                required_items=required_items,
                            )
                        )
                    continue
                allowed_values = []
                # If description has data fetch from DHL API and add to normal array
                if isinstance(property_value, dict):
                    description = property_value.get("description", "")
                    response_data, modType = fetch_api_data(description)
                    if response_data:
                        try:
                            for api_data in response_data["Result"]:
                                allowed_values.append(api_data)
                        except:
                            print(traceback.print_exc())
                            pass
                key_item_type = "key"
                if key in table_block_keys:
                    key_item_type = "table"
                compound_key_item = get_option_key(
                    type=key_item_type,
                    value=property_value,
                    keyLabel=camel_to_normal(property_key),
                    key=property_key,
                    required_items=child_required_items,
                    allowed_values=allowed_values,
                )
                # compound_key_item = {**compound_key_item, "parent_compound_key": key}
                if compound_key_item.get("keyValue") not in [
                    i.get("keyValue") for i in new_normal_data
                ]:
                    new_normal_data.append(compound_key_item)
                # Now append compound keys to compound
                compound_dict["keyItems"].append(compound_key_item)
            new_compound_keys.append(compound_dict)
    print("COMPLETE COMPOUND KEYS PROCESSING")
    # Step 3: Go through key qualifiers
    print("PROCESSING KEY QUALIFIERS PROCESSING")
    for key_qualifier_item in data["key_qualifiers"]:
        for kq_item, kq_value in key_qualifier_item.items():
            key_qualifier_dict = {}
            key_qualifier_dict["name"] = kq_item
            key_qualifier_dict["options"] = []
            properties = kq_value.get("properties", {})
            # Get properties
            if not properties:
                properties = kq_value.get("items", {}).get("properties", {})
            if not properties:
                continue
            # Append to keys as a lookupCode if key qualifier found
            if kq_item not in [
                i.get("keyValue")
                for i in new_normal_data
                if i.get("type") == "lookupCode"
            ]:
                new_normal_data.append(
                    get_option_key(
                        key=kq_item,
                        value=kq_value,
                        type="lookupCode",
                        required_items=required_items,
                        qualifier=kq_item,
                    )
                )
            for property_key, property_value in properties.items():
                # If description has data fetch from DHL API and add to normal array
                if isinstance(property_value, dict):
                    description = property_value.get("description", "")
                    response_data, _ = fetch_api_data(description)
                    if response_data:
                        try:
                            for api_data in response_data["Result"]:
                                key_qualifier_dict["options"].append(
                                    {
                                        "label": api_data.get("Description"),
                                        "value": api_data.get("Code"),
                                    }
                                )
                        except:
                            print(traceback.print_exc())
                            pass
            new_qualifier_keys.append(key_qualifier_dict)
    print("KEY QUALIFIER PROCESSING")
    # Append data
    data["normal"] = new_normal_data
    data["compound"] = new_compound_keys
    data["key_qualifiers"] = new_qualifier_keys
    return data


def convert_dict_to_settings(converted_data: dict, project: str):
    options = {
        "options": {
            "options-keys": {
                "items": converted_data["normal"],
            },
        },
        "compoundKeys": converted_data["compound"],
        "keyQualifiers": converted_data["key_qualifiers"],
    }
    result = {
        "project": project,
        "settings": options,
    }
    return result


def merge_new_keys_with_existing_one(existing_keys: list, new_keys: list) -> list:
    """
    Merge new compound keys into existing ones.
    Match on 'name'. If name exists, extend its 'options'. Else, add new.
    """
    existing_map = {entry["name"]: entry for entry in existing_keys}

    for new_entry in new_keys:
        name = new_entry["name"]
        new_options = new_entry.get("options", [])

        if name in existing_map:
            # Append new options to existing one
            existing_options = existing_map[name].setdefault("options", [])
            existing_options.extend(new_options)
        else:
            # Add new compound key
            existing_keys.append(new_entry)

    return existing_keys


def extract_keys_as_tree(
    data: dict, prefix: str = "", current_depth: int = 1, max_depth: int = 3,
    id_counter: list = None, required_fields: list = None
) -> List[Dict]:
    """
    Extract keys from a YAML/JSON structure as a nested tree structure.
    Returns a list compatible with vue-drag-tree: {name, id, children}

    Args:
        data: Dictionary to extract keys from
        prefix: Path prefix for nested keys
        current_depth: Current nesting level
        max_depth: Maximum nesting depth (default 3)
        id_counter: Mutable list to track unique IDs across recursive calls
        required_fields: List of required field names at current level
    """
    if id_counter is None:
        id_counter = [0]

    if required_fields is None:
        required_fields = []

    tree_nodes = []

    if not isinstance(data, dict) or current_depth > max_depth:
        return tree_nodes

    for key, value in data.items():
        full_path = f"{prefix}.{key}" if prefix else key

        # Generate unique ID
        node_id = id_counter[0]
        id_counter[0] += 1

        # Check if this key is required
        is_required = key in required_fields

        node = {
            "name": key,
            "id": node_id,
            "children": [],
            "path": full_path,
            # Uncomment below fields if needed in future
            "description": "",
            "example": "",
            "maxLength": None,
            "minLength": None,
            "required": is_required,
        }

        if isinstance(value, dict):
            # Uncomment below to extract metadata if needed in future
            if "description" in value:
                node["description"] = value.get("description", "")
            if "example" in value:
                node["example"] = str(value.get("example", ""))
            if "maxLength" in value:
                node["maxLength"] = value.get("maxLength")
            if "minLength" in value:
                node["minLength"] = value.get("minLength")

            # Check for required field within the value itself (parameter style)
            if "required" in value and isinstance(value.get("required"), bool):
                node["required"] = value.get("required")

            # Check for nested properties and build children
            nested_data = None
            child_required_fields = []

            if "properties" in value:
                nested_data = value["properties"]
                # Get required fields for children from the value's "required" array
                if "required" in value and isinstance(value.get("required"), list):
                    child_required_fields = value.get("required", [])
            elif "items" in value and isinstance(value["items"], dict):
                if "properties" in value["items"]:
                    nested_data = value["items"]["properties"]
                    # Get required fields from items
                    if "required" in value["items"] and isinstance(value["items"].get("required"), list):
                        child_required_fields = value["items"].get("required", [])
            elif not any(k in value for k in ["type", "description", "example", "$ref"]):
                # Generic nested dict (not a schema definition)
                nested_data = value
                # Check if nested dict has a "required" array at this level
                if "required" in value and isinstance(value.get("required"), list):
                    child_required_fields = value.get("required", [])

            if nested_data and current_depth < max_depth:
                node["children"] = extract_keys_as_tree(
                    nested_data, full_path, current_depth + 1, max_depth, id_counter, child_required_fields
                )

        tree_nodes.append(node)

    return tree_nodes


def extract_keys_from_yaml_json(data: dict, max_depth: int = 3) -> List[Dict]:
    """
    Extract keys from YAML/JSON content as nested tree structure.
    Supports OpenAPI/Swagger specs and generic JSON/YAML structures.
    Returns format compatible with vue-drag-tree: {name, id, children}
    Each key includes a 'required' flag indicating if it's marked as required.

    Args:
        data: Parsed YAML/JSON dictionary
        max_depth: Maximum nesting depth (default 3)
    """
    tree = []
    id_counter = [0]

    # Try to detect OpenAPI/Swagger format
    schemas = None
    if "components" in data and "schemas" in data.get("components", {}):
        # OpenAPI 3.x format
        schemas = data["components"]["schemas"]
    elif "definitions" in data:
        # Swagger 2.0 / OpenAPI 2.x format
        schemas = data["definitions"]

    if schemas:
        # Extract keys from all schemas as parent nodes
        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict):
                node_id = id_counter[0]
                id_counter[0] += 1

                parent_node = {
                    "name": schema_name,
                    "id": node_id,
                    "children": [],
                    "path": schema_name,
                    # Uncomment below fields if needed in future
                    "description": schema_def.get("description", ""),
                    "example": "",
                    "maxLength": None,
                    "required": False,  # Schema names themselves are not required
                }

                # Extract child properties and required fields
                properties = schema_def.get("properties", {})
                required_fields = schema_def.get("required", [])

                # Ensure required_fields is a list
                if not isinstance(required_fields, list):
                    required_fields = []

                if properties:
                    parent_node["children"] = extract_keys_as_tree(
                        properties, schema_name, 2, max_depth, id_counter, required_fields
                    )

                tree.append(parent_node)
    else:
        # Generic YAML/JSON - extract all keys as tree
        # Check for root-level required array
        root_required_fields = data.get("required", [])
        if not isinstance(root_required_fields, list):
            root_required_fields = []

        tree = extract_keys_as_tree(data, "", 1, max_depth, id_counter, root_required_fields)

    return tree
