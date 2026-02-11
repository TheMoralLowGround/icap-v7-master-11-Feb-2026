"""
Merge Value Keys Script
========================

Purpose:
--------
This script processes JSON data to merge values of keys based on specified rules. It identifies keys marked with a `mergeValue` setting and concatenates their values using a specified separator. The merged values are then updated in the JSON structure.

Functions:
----------
1. **merge_value_keys(d_json)**:
   Processes the input JSON to merge values of specific keys based on their `mergeValue` settings.
   - **Parameters**:
     - `d_json` (dict): The input JSON containing document data with nodes and key-value items.
   - **Returns**:
     - A processed JSON with merged key values.

Workflow:
---------
1. Iterates through the JSON structure to locate `key` nodes.
2. Identifies keys with the `mergeValue` setting and:
   - Collects their labels and separators defined in `advanceSettings["mergeValueSeparator"]`.
   - Concatenates their values using the specified separator.
3. Removes the merged keys from the JSON and updates the parent key or compound key with the merged value.
4. Performs a second pass to ensure merged values are correctly updated in both parent and compound keys.

Key Features:
-------------
- **Merge Value Support**:
  Identifies keys with `advanceSettings["mergeValue"]` and merges their values using the specified separator.

- **Compound Key Handling**:
  Processes nested compound keys (`isCompoundKey`) to merge child key values where applicable.

- **Error Handling**:
  - Employs `try-except` blocks to ensure smooth execution.
  - Logs detailed error traces using `traceback` for debugging.

- **Non-Destructive Updates**:
  Updates the JSON structure while preserving other data fields.

Usage:
------
1. Import the script and call the `merge_value_keys()` function with a valid JSON structure.
2. Ensure the input JSON contains nodes and key-value items with `advanceSettings["mergeValue"]` for keys to be merged.

Example:
--------
```python
processed_json = merge_value_keys(input_json)
print(processed_json)
"""

import traceback
from app.extraction_modules.excel_sub_module import excel_extraction_request


# TODO: This function is not removed because it might be implemented in future for merge items.
# def sort_by_merge_value(data):
#     try:
#         return sorted(
#             data,
#             key=lambda x: not x.get("advanceSettings", {}).get("mergeValue", False),
#         )
#     except:
#         return data


def merge_key_value_items(key_value_items):
    new_key_value_items = []
    merge_value_labels = list()
    merge_value_separators = dict()
    for key_value_item in key_value_items[:]:
        advanced_settings = key_value_item.get("advanceSettings", {})
        if advanced_settings is not None:
            if advanced_settings.get("mergeValue"):
                try:
                    merge_value_labels.append(key_value_item["label"])
                    merge_value_separators[key_value_item["label"]] = dict()
                    merge_value_separators[key_value_item["label"]]["separator"] = (
                        key_value_item["advanceSettings"]["mergeValueSeparator"]
                    )
                    merge_value_separators[key_value_item["label"]]["value"] = (
                        key_value_item["v"]
                    )
                except:
                    print(traceback.format_exc())
                continue
        if key_value_item.get("isCompoundKey"):
            compound_children = key_value_item["children"]
            for child_key_value_item in compound_children[:]:
                child_label = child_key_value_item["label"]
                if child_key_value_item["advanceSettings"].get("mergeValue"):
                    try:
                        merge_value_labels.append(child_label)
                        merge_value_separators[child_label] = dict()
                        merge_value_separators[child_label]["separator"] = (
                            child_key_value_item["advanceSettings"][
                                "mergeValueSeparator"
                            ]
                        )
                        merge_value_separators[child_label]["value"] = (
                            child_key_value_item["v"]
                        )
                        continue
                    except:
                        print(traceback.format_exc())
                try:
                    if child_label in merge_value_labels:
                        merge_value_separators[child_label]["value"] += (
                            merge_value_separators[child_label]["separator"]
                            + child_key_value_item["v"]
                        )
                        compound_children.remove(child_key_value_item)
                except:
                    print(traceback.format_exc())
        if key_value_item.get("label", None) in merge_value_labels:
            merge_value_separators[key_value_item["label"]]["value"] += (
                merge_value_separators[key_value_item["label"]]["separator"]
                + key_value_item["v"]
            )
            key_value_items.remove(key_value_item)

    # second pass to add merged values
    for key_value_item in key_value_items[:]:
        if key_value_item.get("label", None) in merge_value_labels:
            key_value_item["v"] = merge_value_separators[key_value_item["label"]][
                "value"
            ]
            new_key_value_items.append(key_value_item)
        if key_value_item.get("isCompoundKey"):
            compound_children = key_value_item["children"]
            for child_key_value_item in compound_children[:]:
                if child_key_value_item["label"] in merge_value_labels:
                    child_key_value_item["v"] = merge_value_separators[
                        child_key_value_item["label"]
                    ]["value"]
    return new_key_value_items


def process_key_advanced_settings(documents):
    """Merge the values that are true and update the document key section"""
    try:
        for document in documents:
            nodes = document["children"]

            for node in nodes:
                if node["type"] == "key":
                    key_value_items = node["children"]
                    merge_key_value_items(key_value_items)
    except:
        print(traceback.format_exc())


def merge_value_keys(d_json):
    input_json = d_json.copy()
    documents = input_json["nodes"]
    process_key_advanced_settings(documents)
    return input_json


# For table key items


def make_key_value_items(results):
    key_val_items = []
    for result in results:
        for key, val in result.items():
            key_val_items.append(
                {
                    "qualifierParent": val.get("qualifierParent"),
                    "advanceSettings": val.get("advanceSettings", {}),
                    "label": key,
                    "pageId": "",
                    "pos": "",
                    "worksheet_name": val.get("worksheet_name"),
                    "cellRange": val.get("cellRange"),
                    "STATUS": 0,
                    "v": val.get("text"),
                    "block_type": val.get("title"),
                    "children": [],
                }
            )
    return key_val_items


def table_value_merger(target_doc, key_val_items):
    """This function is supposed to merge the advanceSettings functionality"""
    try:
        if not key_val_items:
            return target_doc
        nodes = target_doc["children"]
        for node in nodes:
            if node["type"] == "table":
                rows = node["children"]
                for row in rows:
                    merged_labels = []
                    for item_idx, row_item in enumerate(row["children"]):
                        if isinstance(row_item["v"], list):
                            continue
                        if row_item["v"]:
                            for key_val_idx, key_value in enumerate(key_val_items):
                                # if isinstance(row_item["v"], str):
                                if key_value["label"] == row_item["label"]:
                                    # If merging value not in the abo0ve merged_labels array continue
                                    if key_value["label"] not in merged_labels:
                                        row_item["v"] = key_value["v"]
                                        merged_labels.append(key_value["label"])
                                    else:
                                        # If it is already merge to the table just remove that specific column
                                        if row_item in row["children"]:
                                            row["children"].remove(row_item)
                # Second pass to check if any unmerged value are there then remove the row_item
                for row in rows:
                    for cell_idx, cell in enumerate(row["children"]):
                        if isinstance(row_item["v"], list):
                            continue
                        for key_value_1 in key_val_items:
                            if key_value_1["label"] == cell["label"]:
                                if key_value_1["v"]:
                                    # If value not equal just remove that cell
                                    if key_value_1["v"] != cell["v"]:
                                        if cell in row["children"]:
                                            row["children"].remove(cell)
    except:
        print(traceback.print_exc())
    return target_doc


def merge_table_key_items(d_json, request_data, messages):
    docs = d_json["nodes"]
    try:
        definitions = request_data["definitions"]
        if definitions == []:
            definitions = [{}]
        query_key_list = (
            definitions[0]
            .get("table", [])[0]
            .get("table_definition_data", {})
            .get("keyItems", [])
        )
    except:
        print(traceback.print_exc())
        return d_json
    for input_doc_idx, target_doc in enumerate(docs):
        if (
            target_doc.get("ext", None) == ".xlsx"
            or target_doc.get("ext", None) == ".pdf"
        ):
            try:
                # If the querykeylist is present then only go
                results, messages = excel_extraction_request(
                    query_key_list, request_data, input_doc_idx, messages, merge=True
                )
                # First convert table key items to key iitems to reuse the function merge_key_value_items which is for merging key view
                key_value_items = make_key_value_items(results)
                # Pass to the merger function above
                new_key_value_items = merge_key_value_items(key_value_items)
                # Update table d_json accordingly
                target_doc = table_value_merger(target_doc, new_key_value_items)
            except:
                print(traceback.print_exc())
    return d_json
