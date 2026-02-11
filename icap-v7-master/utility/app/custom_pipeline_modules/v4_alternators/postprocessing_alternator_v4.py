"""
Document Processing Script
===========================

Purpose:
--------
This script processes document data represented in JSON format, applying specific rules and transformations based on profiles and document types. It cleans, merges, and enhances data fields for better downstream usability.

Functions:
----------
1. **generate_keyNode(value, label)**:
   Creates a key node dictionary with specified value and label.
   - **Parameters**:
     - `value` (str): The value for the key node.
     - `label` (str): The label for the key node.
   - **Returns**:
     - A dictionary representing a key node.

2. **process(d_json)**:
   The main function to process the document JSON. It applies transformations based on specific profiles and document types.
   - **Parameters**:
     - `d_json` (dict): The input JSON containing document data.
   - **Returns**:
     - A processed JSON with transformed and enhanced fields.
   - **Features**:
     - **Profile: BOEHRINGER INGELHEIM PROMECO S.A. DE C.V. and Commercial Invoice**:
       - Adds or modifies `goodsDescription` and `notifyAccountNumber` fields based on `consignee` values.
       - Appends new key nodes or modifies existing nodes.
     - **Profile: IT_HENKEL_SEA and Shippers Letter of Instruction**:
       - Merges multiple fields (`notInUse`, `grossWeight`, etc.) into `goodsDescription`.
       - Handles `_UNDGNumber` and appends it to the first row of the table.
       - Removes unnecessary fields (`packageID`, `_UNDGNumber`) from rows.
   - **Error Handling**:
     - Utilizes `try-except` blocks for robust processing and logs exceptions with `traceback`.

Workflow:
---------
1. Copies the input JSON to avoid modifying the original data.
2. Iterates through documents and their nodes, applying transformations specific to profiles.
3. Modifies tables, key nodes, and other components based on business rules.
4. Returns the transformed JSON.

Profiles and Rules:
-------------------
1. **BOEHRINGER INGELHEIM PROMECO S.A. DE C.V. and Commercial Invoice**:
   - Identifies `consignee` values and sets `goodsDescription` and `notifyAccountNumber` based on predefined mappings.
   - Updates or appends new key nodes with the calculated fields.

2. **IT_HENKEL_SEA and Shippers Letter of Instruction**:
   - Merges multiple values (`goodsDescription`, `grossWeight`, `packageID`, etc.) into a single `goodsDescription` field.
   - Appends `_UNDGNumber` values to the first row's `goodsDescription`.
   - Removes unnecessary fields like `_UNDGNumber` and `packageID` from table rows.

Error Handling:
---------------
- Uses `try-except` blocks to ensure smooth execution even when exceptions occur.
- Logs detailed error traces using `traceback` for debugging purposes.

Usage:
------
1. Import the script and call the `process()` function with a valid document JSON.
2. Extend or modify the rules within `process()` for additional profiles or custom transformations.

Example:
--------
```python
processed_json = process(input_json)
print(processed_json)
"""


import traceback


def generate_keyNode(value, label):
    new_keyNode = dict()
    new_keyNode["children"] = []
    new_keyNode["unique_id"] = "abc"
    new_keyNode["v"] = value.strip()
    new_keyNode["label"] = label
    return new_keyNode


def process(d_json):
    input_json = d_json.copy()
    profile_id = input_json["DefinitionID"]
    doc_type = input_json["DocumentType"]
    vendor_name = input_json["Vendor"]
    documents = input_json["nodes"]

    try:
        if (
            "BOEHRINGER INGELHEIM PROMECO S.A. DE C.V.".lower() in vendor_name.lower()
            and "Commercial Invoice".lower() in doc_type.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                goods_description = ""
                notify_account_number = ""
                key_node1 = None
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        key_nodes = node["children"]
                        key_node1 = generate_keyNode(
                            notify_account_number, "notifyAccountNumber"
                        )
                        for key_node in key_nodes:
                            label = key_node["label"]
                            if label == "consignee":
                                # full_text = key_node["v"]
                                sub_key_nodes = key_node["children"]
                                for sub_key_node in sub_key_nodes:
                                    if sub_key_node["type"] == "keyTextDetail":
                                        consignee_account_number = sub_key_node["v"]
                                        if "JPBOI003" in consignee_account_number:
                                            goods_description = "NEXGARD"
                                            notify_account_number = "KUNAMIK1"
                                        elif "GBALU002" in consignee_account_number:
                                            goods_description = (
                                                "EQVALAN / MOLEMEC / IVOMEC"
                                            )
                                            notify_account_number = "DEBOE021"
                                        elif "DEBOE021" in consignee_account_number:
                                            goods_description = (
                                                "NEXGARD SPECTRA, IVOMEC, FUREXEL"
                                            )
                                            notify_account_number = "FRMER001"
                                        elif "FRMER001" in consignee_account_number:
                                            goods_description = (
                                                "VOMEC,FUREXEL,GASTROGARD,EQVALAN,N"
                                            )
                                            notify_account_number = "CABOI005"
                                        elif "CABOI005" in consignee_account_number:
                                            goods_description = (
                                                "EQVALAN , NEXGARD, GASTROGARD"
                                            )
                                            notify_account_number = "DEBOE021"
                                        elif "PHBOI005" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "PHBOI005"
                                        elif "CNBOI009" in consignee_account_number:
                                            goods_description = (
                                                "VOMEC SWINE, INJVI/200ML"
                                            )
                                            notify_account_number = "DEBOE021"
                                        elif "VNASV001" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "VNASV001"
                                        elif "ECBOI001" in consignee_account_number:
                                            goods_description = "NEXGARD"
                                            notify_account_number = "DEBOE021"
                                        elif "THMET011" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "THMET011"
                                        elif "ZABOI002" in consignee_account_number:
                                            goods_description = "NEXGARD"
                                            notify_account_number = "ZABOI002"
                                        elif "COBOI003" in consignee_account_number:
                                            goods_description = "ETHANOL SOLUTION"
                                            notify_account_number = "COBOI003"
                                        elif "NZBOI004" in consignee_account_number:
                                            goods_description = "NEXGARD"
                                            notify_account_number = "NZBOI004"
                                        elif "ITSIC003" in consignee_account_number:
                                            goods_description = "EQVALAN, IVOMEC"
                                            notify_account_number = "ITSIC003"
                                        elif "BEBOI003" in consignee_account_number:
                                            goods_description = "EQVALAN"
                                            notify_account_number = "BEBOI003"
                                        elif "TRBOI002" in consignee_account_number:
                                            goods_description = "IVOMEC"
                                            notify_account_number = "TRBOI002"
                                        elif "ESBOI004" in consignee_account_number:
                                            goods_description = "VOMEC, NEXGARD"
                                            notify_account_number = "ESBOI004"
                                        elif "USBOI023" in consignee_account_number:
                                            goods_description = "DILUENTE"
                                            notify_account_number = "USKUN044"
                                        elif "TWMET006" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "DEBOE021"
                                        elif "KRMEK009" in consignee_account_number:
                                            goods_description = (
                                                "DIL MAREK, INJVI/1200ML"
                                            )
                                            notify_account_number = "KRMEK009"
                                        elif "MYTAT001" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "DEBOE021"
                                        elif "PEBOI002" in consignee_account_number:
                                            goods_description = "DILUENTE MAREK"
                                            notify_account_number = "DEBOE021"
                                        elif "DKBOI001" in consignee_account_number:
                                            goods_description = "GASTROGARD , IVOMEC"
                                            notify_account_number = "DEBOE021"
                                        elif "DEBOE029" in consignee_account_number:
                                            goods_description = (
                                                "NEXGARD SPECTRA, IVOMEC, FUREXEL"
                                            )
                                            notify_account_number = "DEBOE029"
                                        elif "DEBOI026" in consignee_account_number:
                                            goods_description = (
                                                "NEXGARD SPECTRA, IVOMEC, FUREXEL"
                                            )
                                            notify_account_number = "DEBOI026"
                                        elif "DEPHP004" in consignee_account_number:
                                            goods_description = (
                                                "NEXGARD SPECTRA, IVOMEC, FUREXEL"
                                            )
                                            notify_account_number = "DEPHP004"
                                        elif "DEPHL007" in consignee_account_number:
                                            goods_description = (
                                                "NEXGARD SPECTRA, IVOMEC, FUREXEL"
                                            )
                                            notify_account_number = "DEPHL007"
                if goods_description:
                    for node in nodes:
                        if node["type"] == "table":
                            rows = node["children"]
                            for r in rows:
                                cells = r["children"]
                                cell_dict = dict()
                                cell_dict["type"] = "cell"
                                cell_dict["v"] = goods_description
                                cell_dict["label"] = "goodsDescription"
                                cells.append(cell_dict)
                if notify_account_number:
                    for node in nodes:
                        if node["type"] == "key":
                            keyNodes_list = node["children"]
                            new_keyNode = dict()
                            new_keyNode["children"] = []
                            new_keyNode["unique_id"] = "abc"
                            new_keyNode["v"] = notify_account_number
                            new_keyNode["label"] = "notifyAccountNumber"
                            new_keyNode["type"] = "key_detail"
                            new_keyNode["pos"] = ""
                            new_keyNode["pageId"] = ""
                            keyNodes_list.append(new_keyNode)

    except:
        print(traceback.print_exc())
        pass

    try:
        if (
            "IT_HENKEL_SEA".lower() in profile_id.lower()
            and "Shippers Letter of Instruction".lower() in doc_type.lower()
        ):
            undg_list = []
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        rows = node["children"]
                        undgn_number = ""
                        for row in rows:
                            cells = row["children"]
                            not_in_use10 = None
                            goods_description = None
                            gross_weight = None
                            package_id = None
                            not_in_use = None
                            merged_value = ""
                            for cell in cells:
                                if cell["label"] == "filler":
                                    not_in_use10 = cell["v"]
                                elif cell["label"] == "goodsDescription":
                                    goods_description = cell["v"]
                                elif cell["label"] == "grossWeight":
                                    gross_weight = cell["v"]
                                    if cell["v"] == "0":
                                        gross_weight = None
                                        cell["v"] = ""
                                elif cell["label"] == "packageID":
                                    package_id = cell["v"]
                                elif cell["label"] == "notInUse":
                                    not_in_use = cell["v"]
                                elif cell["label"] == "_UNDGNumber":
                                    if cell["v"] != "":
                                        if cell["v"] not in undg_list:
                                            undgn = cell["v"]
                                            undg_list.append(undgn)
                                            new_udg = undg_list[-1]
                                            undgn_number = undgn_number + new_udg + " "

                            for cell in cells[:]:
                                if cell["label"] == "goodsDescription":
                                    if not_in_use10:
                                        merged_value += not_in_use10 + " "
                                    if goods_description:
                                        merged_value += goods_description + " "
                                    if gross_weight:
                                        merged_value += gross_weight + " "
                                    if package_id:
                                        merged_value += package_id + " "
                                    if not_in_use:
                                        merged_value += not_in_use + " "
                                    cell["v"] = merged_value.strip()
                                elif cell["label"] == "packageID":
                                    cells.remove(cell)
                                elif cell["label"] == "_UNDGNumber":
                                    cells.remove(cell)

                            row["children"] = cells
                        if undgn_number != "":
                            undgn_number = undgn_number.strip()
                            first_row = rows[0]
                            first_row_cells = first_row["children"]
                            for first_row_cell in first_row_cells:
                                if first_row_cell["label"] == "goodsDescription":
                                    first_row_cell["v"] = (
                                        first_row_cell["v"] + " " + undgn_number
                                    )
                            rows[0]["children"] = first_row_cells
                        node["children"] = rows
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
        return input_json

    except:
        print(traceback.print_exc())
        pass

    return d_json
