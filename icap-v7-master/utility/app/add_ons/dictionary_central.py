import re
import uuid
import traceback

def process_forwarder_label(value):
    # Strip whitespace from the value
    clean_value = value.strip()

    # Check if value contains numeric characters or has no spaces
    has_numeric = bool(re.search(r'\d', clean_value))
    has_space = ' ' in clean_value

    if has_numeric or not has_space:
        search_column =  'forwarder'
        dummy_column =  'agentsReference'
    else:
        dummy_column =  'forwarder'
        search_column =  'agentsReference'

    return search_column, dummy_column


def get_required_columns(columns):
    required_columns = []
    for column in columns:
        if column.get("ismandatory", False):
            required_columns.append(column["key"])

    return required_columns


def validate_required_columns(key_nodes, required_columns, label):
    valid = True
    present_labels = set(node.get("label") for node in key_nodes)

    if label == "forwarder":
        for key_node in key_nodes:
            if key_node.get("label") == "forwarder":
                search_column, dummy_column = process_forwarder_label(key_node.get("value", ""))
                present_labels.add(search_column)
                if dummy_column in required_columns:
                    required_columns.remove(dummy_column)

    missing_columns = [col for col in required_columns if col not in present_labels]
    if missing_columns:
        valid = False

    return required_columns, valid


def get_new_key_id(key_nodes):
    last_id =  key_nodes[-1]["id"]
    parts = last_id.split('.')
    last_num = int(parts[-1])
    parts[-1] = f"{last_num + 1}"
    new_key_id = '.'.join(parts)
    return new_key_id


def find_matching_items(required_columns, key_nodes, dictionary):
    """
    Find matching records from dictionary data based on required column values in key_nodes.
    """
    search_values = {}
    for column in required_columns:
        for node in key_nodes:
            if node.get("label") == column:
                if column == "forwarder":
                    column, _ = process_forwarder_label(node.get("v", ""))

                search_values[column] = node.get("v", "").strip()
                break

    if len(search_values) != len(required_columns):
        return []

    # Search for matches in dictionary data
    matching_records = []
    dictionary_data = dictionary.get("data", [])

    print("Search values: ", search_values)
    for record in dictionary_data:
        is_match = True
        for column, search_value in search_values.items():
            record_value = str(record.get(column, "")).strip()
            if record_value.lower() != search_value.lower():
                is_match = False
                break
        if is_match:
            matching_records.append(record)

    return matching_records


def dictionary_main(request_data, d_json):
    print("+++++++++++++++++++++++++++++++++++++++++")
    dictionary_version = "v7.1.11052025"
    print("Dictionary Version: ", dictionary_version)

    test_document_trigger = request_data.get("document_id", None)

    dictionaries = request_data.get("dictionaries", [])

    try:
        for dictionary in dictionaries:
            dictionary_name = dictionary.get("name", None)
            documents = d_json.get("nodes")
            for target_doc in documents:
                if test_document_trigger:
                    if test_document_trigger != target_doc["id"]:
                        continue

                doc_type = target_doc["DocType"]
                if doc_type != "Pre Alert":
                    continue

                doc_nodes = target_doc.get("children", [])
                for node in doc_nodes:
                    node_type = node.get("type")
                    if node_type != "key":
                        continue

                    # node["children"] is a direct reference to the key_nodes in d_json
                    key_nodes = node["children"]
                    extra_data_holder = list()

                    for key_node_idx, key_node in enumerate(key_nodes):
                        label = key_node.get("label")

                        if label == dictionary_name:
                            dict_columns = dictionary.get("columns", [])
                            required_columns = get_required_columns(dict_columns)

                            required_columns, is_valid = validate_required_columns(
                                key_nodes, required_columns, label
                            )
                            if not is_valid:
                                continue

                            matching_data = find_matching_items(
                                required_columns, key_nodes, dictionary
                            )
                            print(f"Matching data: {matching_data}")
                            if not matching_data:
                                continue

                            if len(matching_data) > 1:
                                print(
                                    f"Multiple matching records found for dictionary '{dictionary_name}'"
                                )
                                continue

                            if label == "forwarder":
                                forwarder_data = matching_data[0]
                                child_key_nodes = key_node["children"]
                                is_account_number = False
                                for child_key_node in child_key_nodes:
                                    if child_key_node.get("label") == "accountNumber":
                                        is_account_number = True
                                        break

                                if not is_account_number:
                                    new_key_id = get_new_key_id(child_key_nodes)
                                    new_child = {
                                        "v": forwarder_data.pop("forwarder", ""),
                                        "id": new_key_id,
                                        "type": "keyTextDetail",
                                        "label": "accountNumber",
                                        "STATUS": 0,
                                        "children": [],
                                        "is_profile_key_found": True,
                                        "is_label_mapped": False,
                                        "is_pure_autoextraction": True,
                                        "original_key_label": "accountNumber",
                                        "key_value": "accountNumber"
                                    }
                                    child_key_nodes.append(new_child)
                                    key_node["children"] = child_key_nodes

                            extra_data_holder.extend(matching_data)

                    if extra_data_holder:
                        existing_nodes = [node.get("label") for node in key_nodes]
                        for extra_data in extra_data_holder:
                            for extra_label, extra_value in extra_data.items():
                                # if not str(extra_value).strip():
                                #     continue
                                if extra_label == "id":
                                    continue

                                if extra_label in existing_nodes:
                                    # Update existing node
                                    key = key_nodes[existing_nodes.index(extra_label)]
                                    key["v"] = str(extra_value)
                                else:
                                    # Create new node for this label
                                    new_key_id = get_new_key_id(key_nodes)
                                    new_node = {
                                        "v": str(extra_value),
                                        "id": new_key_id,  # Use similar ID pattern
                                        "pos": "0,0,0,0",
                                        "type": "key_detail",
                                        "label": extra_label,
                                        "STATUS": 1,
                                        "export": False,
                                        "pageId": "",
                                        "children": [],
                                        "key_value": extra_label,
                                        "unique_id": uuid.uuid4().hex,
                                        "block_type": "",
                                        "advanceSettings": {},
                                        "is_label_mapped": False,
                                        "is_auto_extracted": True,
                                        "is_key_from_table": False,
                                        "original_key_label": extra_label,
                                        "is_profile_key_found": True,
                                        "is_data_exception_done": False,
                                        "is_pure_autoextraction": True
                                    }
                                    key_nodes.append(new_node)

                    node["children"] = key_nodes

        print("##########################################")
        return d_json
    except:
        print(traceback.print_exc())

    return d_json
