"""
Document Processing Script
===========================

Purpose:
--------
This script processes JSON representations of documents to handle and update location codes (origin and destination) by combining country and location codes. It ensures proper formatting of combined codes in both parent and compound key structures.

Functions:
----------
1. **process(d_json)**:
   Processes the input JSON to combine and update origin and destination location codes based on their respective country codes.
   - **Parameters**:
     - `d_json` (dict): The input JSON containing document data.
   - **Returns**:
     - A processed JSON with updated location codes.
   - **Features**:
     - Identifies and updates compound keys with `originCountryCode`, `originLocationCode`, `destinationCountryCode`, and `destinationLocationCode`.
     - Combines country and location codes into a single value if both are valid and meet length criteria.
     - Updates both parent and child nodes with the combined values where applicable.
     - Handles nested structures with compound keys (`isCompoundKey`).

Workflow:
---------
1. Iterates through documents and nodes to locate key nodes.
2. For each key node:
   - Processes child elements (`children`) to identify `originCountryCode`, `originLocationCode`, `destinationCountryCode`, and `destinationLocationCode`.
   - Combines valid country and location codes into a single value.
   - Updates both parent and compound child nodes with the combined value.
3. Returns the updated JSON.

Key Features:
-------------
- **Compound Key Support**:
  Handles nested child nodes in compound keys, ensuring updates are applied consistently across both parent and child structures.
  
- **Validation**:
  Combines codes only if:
  - `originLocationCode` and `destinationLocationCode` are exactly 3 characters long.
  - `originCountryCode` and `destinationCountryCode` are exactly 2 characters long.

- **Error Handling**:
  - Employs `try-except` blocks to prevent processing interruptions.
  - Logs errors using `traceback` for debugging purposes.

Usage:
------
1. Import the script and call the `process()` function with a valid document JSON.
2. Extend or modify the rules for additional profiles or custom transformations.

Example:
--------
```python
processed_json = process(input_json)
print(processed_json)
"""

import traceback


def process(d_json):
    input_json = d_json.copy()
    documents = input_json["nodes"]

    try:
        origin_country_code = None
        origin_location_code = None
        destination_country_code = None
        destination_location_code = None
        child_origin_country_code = None
        child_origin_location_code = None
        child_destination_country_code = None
        child_destination_location_code = None
        for document_idx, document in enumerate(documents):
            nodes = document["children"]

            for node_idx, node in enumerate(nodes):
                if node["type"] == "key":
                    new_list = list()
                    key_value_items = node["children"]

                    for key_value_item in key_value_items:
                        if key_value_item.get("isCompoundKey"):
                            compound_children = key_value_item["children"]
                            child_list = list()
                            for child_key_value_item in compound_children:
                                child_label = child_key_value_item["label"]
                                try:
                                    if child_label == "originCountryCode":
                                        child_origin_country_code = (
                                            child_key_value_item["v"]
                                        )
                                    if child_label == "originLocationCode":
                                        child_origin_location_code = (
                                            child_key_value_item["v"]
                                        )
                                    child_list.append(child_key_value_item)
                                    key_value_item["children"] = child_list
                                except:
                                    pass

                            if child_origin_country_code and child_origin_location_code:
                                if (
                                    len(child_origin_location_code) == 3
                                    and len(child_origin_country_code) == 2
                                ):
                                    try:
                                        child_origin_combined = (
                                            child_origin_country_code
                                            + child_origin_location_code
                                        )
                                        for child_key_value_item in compound_children:
                                            if (
                                                child_key_value_item["label"]
                                                == "originLocationCode"
                                            ):
                                                # if len(child_key_value_item["v"]) =
                                                child_key_value_item[
                                                    "v"
                                                ] = child_origin_combined
                                    except:
                                        pass

                        label = key_value_item["label"]
                        try:
                            if label == "originCountryCode":
                                origin_country_code = key_value_item["v"]
                            if label == "originLocationCode":
                                origin_location_code = key_value_item["v"]
                            new_list.append(key_value_item)
                            node["children"] = new_list
                        except:
                            pass

                    if origin_country_code and origin_location_code:
                        if (
                            len(origin_location_code) == 3
                            and len(origin_country_code) == 2
                        ):
                            try:
                                origin_combined = (
                                    origin_country_code + origin_location_code
                                )
                                for key_value_item in key_value_items:
                                    if key_value_item["label"] == "originLocationCode":
                                        key_value_item["v"] = origin_combined
                            except:
                                pass

                    nodes[node_idx] = node

            for node_idx, node in enumerate(nodes):
                if node["type"] == "key":
                    new_list = list()
                    key_value_items = node["children"]
                    for key_value_item in key_value_items:
                        if key_value_item.get("isCompoundKey"):
                            compound_children = key_value_item["children"]
                            child_list = list()

                            for child_key_value_item in compound_children:
                                child_label = child_key_value_item["label"]
                                try:
                                    if child_label == "destinationCountryCode":
                                        child_destination_country_code = (
                                            child_key_value_item["v"]
                                        )
                                    if child_label == "destinationLocationCode":
                                        child_destination_location_code = (
                                            child_key_value_item["v"]
                                        )
                                    child_list.append(child_key_value_item)
                                    key_value_item["children"] = child_list
                                except:
                                    pass

                            if (
                                child_destination_country_code
                                and child_destination_location_code
                            ):
                                if (
                                    len(child_destination_location_code) == 3
                                    and len(child_destination_country_code) == 2
                                ):
                                    try:
                                        destination_combined = (
                                            child_destination_country_code
                                            + child_destination_location_code
                                        )
                                        for child_key_value_item in compound_children:
                                            if (
                                                child_key_value_item["label"]
                                                == "destinationLocationCode"
                                            ):
                                                child_key_value_item[
                                                    "v"
                                                ] = destination_combined
                                    except:
                                        pass

                        label = key_value_item["label"]
                        try:
                            if label == "destinationCountryCode":
                                destination_country_code = key_value_item["v"]
                            if label == "destinationLocationCode":
                                destination_location_code = key_value_item["v"]
                            new_list.append(key_value_item)
                            node["children"] = new_list
                        except:
                            pass

                    nodes[node_idx] = node

            if destination_country_code and destination_location_code:
                if (
                    len(destination_location_code) == 3
                    and len(destination_country_code) == 2
                ):
                    try:
                        destination_combined = (
                            destination_country_code + destination_location_code
                        )
                        for node_idx, node in enumerate(nodes):
                            if node["type"] == "key":
                                key_value_items = node["children"]
                                for key_value_item in key_value_items:
                                    if (
                                        key_value_item["label"]
                                        == "destinationLocationCode"
                                    ):
                                        key_value_item["v"] = destination_combined
                    except:
                        pass

            document["children"] = nodes
            documents[document_idx] = document

    except:
        print(traceback.print_exc())
        pass

    return d_json
