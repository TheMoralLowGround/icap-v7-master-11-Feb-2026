def convert_value(value, target_type=str):
    """Helper function to convert string to appropriate type"""
    if value == "" or value is None:
        return None

    if target_type == int:
        if isinstance(value, str):
            value = value.replace(",", "")
        try:
            return int(value)
        except ValueError:
            return None

    if target_type == float:
        if isinstance(value, str):
            value = value.replace(",", "")
        try:
            return float(value)
        except ValueError:
            return None

    if target_type == bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("true", "1", "yes")
        return None

    return value


def extract_key_value(data, fields):
    """Extract key-value pairs from final_json based on fields mapping"""
    result = {}
    for field, key, field_type in fields:
        if field in data:
            raw = data[field]
            value = convert_value(raw, field_type)

            data.pop(field, None)

            if value is not None:
                result[key] = value

    return result


def clean_empty_fields(data):
    """Remove keys with None or empty values"""
    keys_to_remove = [key for key, value in data.items() if value is None or value == ""]
    for key in keys_to_remove:
        data.pop(key, None)
    return data


def map_notes(data_json):
    notes = []
    for key in list(data_json.keys()):
        # Handle flat "notes.TYPE" format
        if key.startswith("notes."):
            note_type = key.split("notes.", 1)[1]
            note_text = data_json[key]
            notes.append(
                {
                    "type": note_type,
                    "text": note_text
                }
            )
            data_json.pop(key, None)

    if notes:
        data_json["notes"] = notes

    return data_json


def map_references(data_json, project=""):    
    references = []
    for key in list(data_json.keys()):
        # Handle flat "references.TYPE" format
        if key.startswith("references."):
            keyword = key.split("references.", 1)[1]
            value = data_json[key]

            if project=="freight":
                data = {
                    "qualifier": keyword,
                    "value": value
                }
            else:
                data = {
                    "type": keyword,
                    "number": value
                }

            references.append(data)
            data_json.pop(key, None)

    if references:
        data_json["references"] = references

    return data_json


def replace_keys(data, key_map):
    """
    Recursively replace keys in JSON-like data.
    :param data: dict/list JSON data
    :param key_map: dict mapping old_key -> new_key
    :return: new data with keys replaced
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = key_map.get(key, key)
            new_dict[new_key] = replace_keys(value, key_map)
        return new_dict

    elif isinstance(data, list):
        return [replace_keys(item, key_map) for item in data]

    else:
        return data

