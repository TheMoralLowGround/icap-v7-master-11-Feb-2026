def restructure_output_json(schema, output_json):
    """
    Restructure JSON according to schema while preserving existing data.

    Args:
        schema: Schema defining the structure with three field types
        output_json: Existing JSON data to be validated and restructured

    Returns:
        Restructured JSON preserving all valid existing data
    """
    result = {}

    for key, schema_value in schema.items():
        output_value = output_json.get(key)

        if not output_value:
            continue

        # Type 1: Simple boolean field (True/False)
        if isinstance(schema_value, bool) and schema_value is True:
            result[key] = output_value

        # Type 2: Object with key-value pairs
        elif isinstance(schema_value, dict) and isinstance(output_value, dict):
            restructured_object = restructure_object(schema_value, output_value)

            if restructured_object:
                result[key] = restructured_object

        # Type 3: Array type
        elif isinstance(schema_value, list) and isinstance(output_value, list):
            restructured_array = restructure_array(schema_value, output_value)

            if restructured_array:
                result[key] = restructured_array

    return result


def restructure_object(schema_obj, existing_output_value):
    """
    Restructure object according to schema while preserving all existing fields.

    Args:
        schema_obj: Schema for the object
        existing_output_value: Existing object data

    Returns:
        Restructured object with all valid existing data preserved
    """
    result = {}

    # Process only the fields defined in schema
    for key, schema_value in schema_obj.items():
        output_value = existing_output_value.get(key)

        if not output_value:
            continue

        if isinstance(schema_value, bool) and schema_value is True:
            result[key] = output_value
        elif isinstance(schema_value, dict) and isinstance(output_value, dict):
            restructured_object = restructure_object(schema_value, output_value)

            if restructured_object:
                result[key] = restructured_object

    return result


def restructure_array(schema_array, existing_output_array):
    """
    Restructure array according to schema while preserving all existing items.

    Args:
        schema_array: Schema for the array (first item is object schema, rest are allowed fields)
        existing_output_array: Existing array data

    Returns:
        Restructured array with all valid existing data preserved
    """
    if len(schema_array) == 0:
        return existing_output_array

    # First item is the object schema
    object_schema = schema_array[0]

    # Rest are string field names (if they exist)
    allowed_fields = schema_array[1:] if len(schema_array) > 1 else []

    result = []

    for output_item in existing_output_array:
        if not isinstance(output_item, dict):
            continue

        # Check if this item matches any of the allowed fields
        if allowed_fields:
            item_matches = False
            field_to_check = output_item.get("type", "").upper() or output_item.get("partyType")

            if field_to_check in allowed_fields:
                if output_item.get("type"):
                    output_item["type"] = output_item["type"].upper()
                item_matches = True

            if not item_matches:
                continue

        # Restructured item based on schema
        restructured_item = {}
        has_schema_match = False

        for key, schema_value in object_schema.items():
            if key not in output_item:
                continue

            if isinstance(schema_value, bool) and schema_value is True and output_item[key]:
                restructured_item[key] = output_item[key]
                has_schema_match = True
            elif isinstance(schema_value, dict) and isinstance(output_item[key], dict):
                restructured_object = restructure_object(
                    schema_value, output_item[key]
                )

                if restructured_object:
                    restructured_item[key] = restructured_object
                    has_schema_match = True

        # Add restructured item if it matched the schema
        if has_schema_match and restructured_item:
            result.append(restructured_item)

    return result
