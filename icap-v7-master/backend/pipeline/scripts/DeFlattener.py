import traceback
from pipeline.output.shipment import handle_shipment_output
from pipeline.output.freight import handle_freight_output
from pipeline.output.civ import handle_civ_output
from pipeline.output.booking import handle_booking_output


customs_party_types = [
    "Supplier",
    "Importer",
    "Forwarder",
    "Declarant",
    "Seller",
    "Representative",
    "Notify",
    "Manufacturer",
    "ExternalBroker",
    "Exporter",
    "Depot",
    "CustomsWarehouse",
    "CTO",
    "ControllingCustomer",
    "ControllingAgent",
    "ContainerYard",
    "Carrier"
]

shipment_party_types = [
    "ControllingAgent",
    "ArrivalCFSAddress",
    "DeliveryAgent",
    "DeliveryLocalCartage",
    "ImportBroker",
    "DepartureCFSAddress",
    "ExportBroker",
    "PickupAgent",
    "PickupLocalCartage",
    "LocalClient"
]



def handle_parties(input_json, project):
    final_json = input_json.copy()
    try:
        party_types = []
        if "customs" in project.lower():
            party_types = customs_party_types
        if "shipment" in project.lower():
            party_types = shipment_party_types
        # Perform project-specific processing
        for k, v in list(final_json.items()):
            if k[0].upper() + k[1:] in party_types:
                if "parties" not in final_json.keys():
                    final_json["parties"] = []
                final_json["parties"].append({
                    "partyType": k[0].upper() + k[1:],
                    **v
                })

                final_json.pop(k, None)
    except:
        print(traceback.format_exc())
        pass
    return final_json


def handle_references(input_json):
    final_json = input_json.copy()
    try:    
        # First, handle the flat "references.TYPE" format
        references_to_transform = {}
        keys_to_remove = []
        for key in input_json.keys():
            if key.startswith("references."):
                reference_type = key.split("references.", 1)[1]
                reference_value = input_json[key]
                references_to_transform[reference_type] = reference_value
                keys_to_remove.append(key)
        # Transform to array format
        if references_to_transform:
            transformed_references = [
                {"type": ref_type, "number": ref_value}
                for ref_type, ref_value in references_to_transform.items()
            ]
            # Merge with existing references if any
            if "references" in final_json and isinstance(final_json["references"], list):
                final_json["references"].extend(transformed_references)
            else:
                final_json["references"] = transformed_references
            # Remove the flat keys
            for key in keys_to_remove:
                final_json.pop(key, None)
    except:
        print(traceback.format_exc())
        pass

    return final_json



def handle_notes(input_json):
    final_json = input_json.copy()
    try:
        # First, handle the flat "notes.TYPE" format
        notes_to_transform = {}
        keys_to_remove = []
        
        for key in input_json.keys():
            if key.startswith("notes."):
                note_type = key.split("notes.", 1)[1]
                note_value = input_json[key]
                notes_to_transform[note_type] = note_value
                keys_to_remove.append(key)
        
        # Transform to array format
        if notes_to_transform:
            transformed_notes = [
                {"type": note_type, "text": note_value}
                for note_type, note_value in notes_to_transform.items()
            ]

            # Merge with existing notes if any
            if "notes" in final_json and isinstance(final_json["notes"], list):
                final_json["notes"].extend(transformed_notes)
            else:
                final_json["notes"] = transformed_notes

            # Remove the flat keys
            for key in keys_to_remove:
                final_json.pop(key, None)
    except:
        print(traceback.format_exc())
        pass

    return final_json


def handle_transportunits_table(final_json, main_table):
    transport_units_data = {}

    for table in main_table:
        for row in table.get("rows", []):

            if "transportUnitsTransportUnitID" not in list(row.keys()):
                continue

            transport_unit_id = row["transportUnitsTransportUnitID"]

            if transport_unit_id not in transport_units_data:
                transport_units_data[transport_unit_id] = {}

            for key, value in row.items():
                if value and key.startswith("transportUnits"):
                    clean_key = key.replace("transportUnits", "", 1)
                    clean_key = clean_key[0].lower() + clean_key[1:]
                    transport_units_data[transport_unit_id][clean_key] = value

    if transport_units_data:
        final_json["transportUnits"] = list(transport_units_data.values())

    return final_json


def rename_contact_fields(data):
    try:
        if isinstance(data, dict):
            updated_dict = {}
            for key, value in data.items():
                new_key = key
                # Check if key starts with "contact" but is not exactly "contact"
                if key.startswith("contact") and key != "contact":
                    suffix = key[len("contact"):]
                    new_key = suffix[:1].lower() + suffix[1:] if suffix else key
                # Rename phoneNumber to phone
                elif key == "phoneNumber":
                    new_key = "phone"
                
                # Recursively process nested structures
                updated_dict[new_key] = rename_contact_fields(value)
            return updated_dict
        elif isinstance(data, list):
            return [rename_contact_fields(item) for item in data]
        else:
            return data
    except:
        print(traceback.format_exc())
        pass

    return data


def nest_compound_fields(data, compound_fields):
    final_json = data.copy()
    try:        
        # Fields that should keep their full key name when nested
        exception_fields = ["housebillnumber", "masterbillnumber"]
        
        # Fields that should be arrays instead of objects
        array_fields = ["transportlegs", "transportunits", "localtransports", "service"]
        
        # Do not nest fields
        no_nesting = ["serviceLevel"]

        for compound_field in compound_fields:
            # Find all keys that start with the compound field name (case-insensitive)
            keys_to_nest = {}
            keys_to_remove = []
            
            for key in data.keys():
                if key in no_nesting:
                    continue
                # Case-insensitive comparison
                if key.lower().startswith(compound_field.lower()) and key.lower() != compound_field.lower():
                    # Extract the suffix after the compound field name
                    suffix = key[len(compound_field):]
                    
                    # Check if this is an exception field (keep full key name)
                    if key.lower() in exception_fields:
                        nested_key = key
                    else:
                        # Convert first character to lowercase for the nested key
                        nested_key = suffix[:1].lower() + suffix[1:] if suffix else key
                    
                    keys_to_nest[nested_key] = data[key]
                    keys_to_remove.append(key)
            
            # If we found keys to nest, create the compound field object or array
            if keys_to_nest:
                # Check if this should be an array field
                if compound_field.lower() in array_fields:
                    # Create an array with the object as the only element
                    if compound_field in final_json and isinstance(final_json[compound_field], list):
                        final_json[compound_field].append(keys_to_nest)
                    else:
                        final_json[compound_field] = [keys_to_nest]
                else:
                    # Regular object nesting
                    if compound_field in final_json and isinstance(final_json[compound_field], dict):
                        final_json[compound_field].update(keys_to_nest)
                    else:
                        final_json[compound_field] = keys_to_nest
                
                # Remove the flat keys
                for key in keys_to_remove:
                    final_json.pop(key, None)
    except:
        pass

    return final_json


# Delete any unwanted keys from the nesting structure
def delete_unwanted_keys(data):
    unwanted_keys = ["block", "batchid"]
    try:
        if isinstance(data, dict):
            keys_to_remove = []
            for key, value in data.items():
                if key in unwanted_keys or key.startswith("temp."):
                    keys_to_remove.append(key)
                else:
                    data[key] = delete_unwanted_keys(value)
            for key in keys_to_remove:
                data.pop(key, None)
        elif isinstance(data, list):
            data = [delete_unwanted_keys(item) for item in data]
    except:
        print(traceback.format_exc())
        pass
    return data


def nest_special_fields(data):
    """
    Nests fields ending with AccountNumber or AddressShortCode under their parent object.
    Example: representativeAccountNumber -> representative: { accountNumber: value }
    """
    final_json = data.copy()
    try:
        special_suffixes = ["AccountNumber", "AddressShortCode"]
        
        # Group fields by their prefix
        nested_groups = {}
        keys_to_remove = []
        
        for key in data.keys():
            for suffix in special_suffixes:
                if key.endswith(suffix) and key != suffix:
                    # Extract the prefix (everything before the suffix)
                    prefix = key[:-len(suffix)]
                    
                    # Create the nested key (convert suffix to camelCase)
                    nested_key = suffix[:1].lower() + suffix[1:]
                    
                    # Initialize the group if it doesn't exist
                    if prefix not in nested_groups:
                        nested_groups[prefix] = {}
                    
                    # Add the field to the group
                    nested_groups[prefix][nested_key] = data[key]
                    keys_to_remove.append(key)
                    break
        
        # Create or merge the nested objects
        for prefix, fields in nested_groups.items():
            if prefix in final_json:
                # If the prefix already exists and is a dict, merge
                if isinstance(final_json[prefix], dict):
                    final_json[prefix].update(fields)
                else:
                    # If it exists but is not a dict, replace it with the nested object
                    final_json[prefix] = fields
            else:
                # Create new nested object
                final_json[prefix] = fields
        
        # Remove the original flat keys
        for key in keys_to_remove:
            final_json.pop(key, None)
    except:
        print(traceback.format_exc())
        pass
    
    return final_json


def convert_values(data):
    """
    Recursively converts string values to appropriate numeric types based on key names.
    - Keys ending with 'volume', 'weight', 'capacity': convert to float
    - Keys ending with 'packages', 'count': convert to int
    - Key 'sequenceNumber': convert to int
    Only applies to leaf nodes (non-dict, non-list values).
    """
    try:
        if isinstance(data, dict):
            converted_dict = {}
            for key, value in data.items():
                try:
                    # Only convert leaf nodes (strings)
                    if isinstance(value, str):
                        key_lower = key.lower()
                        
                        # Check if key ends with volume/weight/capacity
                        if key_lower.endswith(('volume', 'weight', 'capacity', 'amount')):
                            try:
                                converted_dict[key] = float(value)
                            except (ValueError, TypeError):
                                converted_dict[key] = value
                        # Check if key ends with packages/count
                        elif key_lower.endswith(('packages', 'count')):
                            try:
                                converted_dict[key] = int(value)
                            except (ValueError, TypeError):
                                converted_dict[key] = value
                        # Check if key is sequenceNumber
                        elif key_lower == 'sequencenumber':
                            try:
                                converted_dict[key] = int(value)
                            except (ValueError, TypeError):
                                converted_dict[key] = value
                        else:
                            converted_dict[key] = value
                    # Recursively process nested structures
                    elif isinstance(value, (dict, list)):
                        converted_dict[key] = convert_values(value)
                    else:
                        converted_dict[key] = value
                except:
                    continue
            return converted_dict
        elif isinstance(data, list):
            return [convert_values(item) for item in data]
        else:
            return data
    except:
        print(traceback.format_exc())
        pass
    
    return data
def nest_second_level(data, project):
    final_json = data.copy()
    try:
        if "customs" in project.lower():
            mapping = {
                "localTransports": 
                [
                    "transportCompany",
                    "transportLocation",
                ],
                "service":
                [
                    "serviceLocation"
                ]
            }
            
            for parent_key, child_keys in mapping.items():
                # Check if parent key exists in the data
                parent_exists = parent_key in final_json
                
                # Find keys to nest
                keys_to_nest = {}
                keys_to_remove = []
                
                for child_key in child_keys:
                    if child_key in final_json:
                        keys_to_nest[child_key] = final_json[child_key]
                        keys_to_remove.append(child_key)
                
                # If we found keys to nest
                if keys_to_nest:
                    if parent_exists:
                        # Parent exists - nest within it
                        if isinstance(final_json[parent_key], list) and len(final_json[parent_key]) > 0:
                            # If parent is an array, add to first element
                            final_json[parent_key][0].update(keys_to_nest)
                        elif isinstance(final_json[parent_key], dict):
                            # If parent is an object, merge
                            final_json[parent_key].update(keys_to_nest)
                    else:
                        # Parent doesn't exist - create it as array with object
                        final_json[parent_key] = [keys_to_nest]
                    
                    # Remove the flat keys
                    for key in keys_to_remove:
                        final_json.pop(key, None)

            return final_json

    except:
        print(traceback.print_exc())
        pass

    return final_json

def delete_empty_values(data):
    if isinstance(data, dict):
        keys_to_remove = []
        for key, value in data.items():
            if value in ("", None, [], {}):
                keys_to_remove.append(key)
            else:
                data[key] = delete_empty_values(value)
        for key in keys_to_remove:
            data.pop(key, None)
    elif isinstance(data, list):
        data = [delete_empty_values(item) for item in data if item not in ("", None, [], {})]
    return data


def central_output_handler(request_data):
    print("Central Output Handler Invoked")
    input_json = request_data.get("input_json", {})
    final_json = input_json
    project = request_data.get("project", "")
    main_table = request_data.get("main_table")
    batch_type = request_data.get("batch_type", "")

    try:
        print(f"Project: {project}, Batch ID: {request_data.get('batchid', 'N/A')}")
    except:
        pass

    if "shipment" in project.lower():
        final_json = handle_shipment_output(final_json, main_table)

    elif "freight" in project.lower():
        final_json = handle_freight_output(final_json, main_table)

    elif "uscustoms" in project.lower():
        final_json = handle_civ_output(final_json, main_table)

    elif "(civ)" in project.lower():
        final_json = handle_civ_output(final_json, main_table)

    elif "(b+civ)" in project.lower():
        if batch_type == "commercial-invoice":
            final_json = handle_civ_output(final_json, main_table)
        else:
            final_json = handle_booking_output(final_json, main_table)

    else:
        # Nest special fields (accountNumber, addressShortCode)
        final_json = nest_special_fields(final_json)

        final_json = handle_parties(final_json, project)
        final_json = handle_references(final_json)
        final_json = handle_notes(final_json)

        # Handle contact field renaming
        final_json = rename_contact_fields(final_json)

        compound_fields=["housebill", "masterbill","transportLegs", "transportUnits", "localTransports", "service"]

        # Nest Compound fields
        final_json = nest_compound_fields(final_json, compound_fields=compound_fields)

        if "customs" in project.lower():
            final_json = handle_transportunits_table(final_json, main_table)

        # Second Level Nesting for compound fields
        final_json = nest_second_level(final_json, project=project)

        # Convert string values to appropriate numeric types
        final_json = convert_values(final_json)

        # Delete all key, value nodes that have empty value (Empty String, Null, Empty Array, Empty Object)
        final_json = delete_empty_values(final_json)

        # with open('output.json', 'w') as f:
        #     json.dump(final_json, f, indent=4)

    final_json = delete_unwanted_keys(final_json)

    print("Central Output Handler Completed")
    return final_json
