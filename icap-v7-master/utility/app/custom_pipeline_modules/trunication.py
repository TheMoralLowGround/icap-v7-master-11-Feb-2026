import re
import traceback

"""
Data Truncation Script
=======================

Purpose:
--------
This script processes JSON data to handle and standardize numerical values for specific fields. It converts values with mixed decimal formats, truncates them to three decimal places, and updates the JSON structure.

Functions:
----------
1. **trunicator(data_json)**:
   Processes the input JSON to standardize and truncate numerical values for specified fields.
   - **Parameters**:
     - `data_json` (dict): The input JSON containing document data with nodes, tables, and cells.
   - **Returns**:
     - A processed JSON with updated numerical values for target fields.
   - **Features**:
     - Targets specific labels (`grossWeight`, `volume`, `length`, etc.).
     - Converts numerical values with:
       - Commas (`,`) to dots (`.`) when no decimal points are present.
       - Removes commas if both commas and dots are present, ensuring proper decimal formatting.
     - Truncates numerical values to three decimal places.
     - Handles special cases for hazardous material fields, maintaining numerical precision without string conversion.

Workflow:
---------
1. Iterates through the JSON structure to find `table` nodes.
2. For each `table` node:
   - Iterates through rows and cells.
   - Checks if the cell label matches one of the target labels.
   - Converts and truncates the value as follows:
     - Replaces commas with dots for values lacking a decimal point.
     - Removes commas if a dot is already present after the comma.
     - Converts the value to a float, truncates it to three decimal places, and updates the cell's value.
3. Returns the updated JSON.

Target Labels:
--------------
- `grossWeight`
- `volume`
- `length`
- `width`
- `height`
- `goodsLinesHazardousMaterialVolume`
- `goodsLinesHazardousMaterialGrossWeight`

Key Features:
-------------
- **Decimal Conversion**:
  Ensures consistent decimal formatting for numerical values, replacing commas with dots or removing unnecessary commas.
  
- **Truncation**:
  All numerical values are truncated to three decimal places for standardization.

- **Hazardous Material Fields**:
  Maintains numerical precision as floats for specific fields: `goodsLinesHazardousMaterialVolume` and `goodsLinesHazardousMaterialGrossWeight`.

Usage:
------
1. Import the script and call the `trunicator()` function with a valid JSON structure.
2. Ensure the input JSON contains nodes, tables, and cells with numerical data.

Example:
--------
```python
processed_json = trunicator(input_json)
print(processed_json)
"""


def normalize_number_format(input_string):
    # Remove all commas
    processed_string = input_string.replace(",", "")

    # Find all dots in the string
    dots = [m.start() for m in re.finditer(r"\.", processed_string)]

    # If there are multiple dots, keep only the first one and remove the rest
    if len(dots) > 1:
        first_dot_index = dots[0]
        processed_string = processed_string[: first_dot_index + 1] + processed_string[
            first_dot_index + 1 :
        ].replace(".", "")

    return processed_string

# WARNING: `trunicator` and `calulate_fields_trunicator` share logic/structure — changes to one may affect the other.
# Keep them in sync to avoid inconsistencies.
def trunicator(data_json):
    target_labels = [
        "grossWeight",
        "volume",
        "length",
        "width",
        "height",
        "goodsLinesHazardousMaterialVolume",
        "goodsLinesHazardousMaterialGrossWeight",
        "insuranceValue",
    ]
    documents = data_json["nodes"]
    for document_idx, document in enumerate(documents):
        nodes = document["children"]
        for node_idx, node in enumerate(nodes):
            if node["type"] == "table":
                rows = node["children"]
                for row_idx, row in enumerate(rows):
                    cells = row["children"]
                    for cell_idx, cell in enumerate(cells):
                        if cell.get("label") in target_labels:
                            cell_value = cell.get("v")

                            if cell_value:
                                try:
                                    processed_value = normalize_number_format(
                                        cell_value
                                    )

                                except:
                                    print(traceback.print_exc())

                                if processed_value:
                                    try:
                                        cell["v"] = processed_value
                                    except:
                                        print(traceback.print_exc())

    return data_json
