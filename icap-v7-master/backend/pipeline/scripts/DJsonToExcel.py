"""
Organization: AIDocbuilder Inc.
File: scripts/DJsonToExcel.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script convert data_json to Excel file.

Dependencies:
    - deepcopy from copy
    - pandas as pd
    - Workbook from xlsxwriter.workbook

Main Features:
    - Process data_json to Excel file.
"""

import traceback
import os
from copy import deepcopy

import pandas as pd
from xlsxwriter.workbook import Workbook


def process_table(table, document_id):
    """
    This function process table rows and convert them into DataFrame.

    Args:
        table (dict): Table data with rows and cells.
        document_id (str): Identifier of the document.

    Returns:
        df (DataFrame): DataFrame contain the processed table data.

    Process Details:
        - Iterate through the rows of the table and process each cell.
        - Construct DataFrame from the rows.
        - Remove completely empty rows from the DataFrame.
        - Add 'document_id' and 'table_id' columns into the DataFrame.

    Notes:
        - Empty rows are identified and removed.
    """
    table_id = table["id"]
    table_rows = table["children"]
    rows = []
    for row in table_rows:
        result_row = {}
        cells = row["children"]
        for cell in cells:
            result_row[cell["label"]] = cell["v"]
        rows.append(result_row)

    df = pd.DataFrame(rows)
    df = df.dropna(how="all")  # Remove empty lines

    df["document_id"] = document_id
    df["table_id"] = table_id

    return df


def process_key(key, prefix=None):
    """
    This function process key label, value and children.

    Args:
        key (dict): Key data, including label, value, and children.
        prefix (str): Used for nested key structure.

    Returns:
        result (dict or list): Processed key data, including label, value, and children.

    Process Details:
        - Extract the label and value from the key.
        - Add a prefix to the label if provided.
        - Process child keys, combining them with the current key.

    Notes:
        - Return list if the key has children otherwise dictionary.
    """
    label = key["label"]
    value = key["v"]

    result = {}
    result["label"] = label if prefix is None else f"{prefix}.{label}"
    result["value"] = value

    key_childrens = key["children"]

    if key_childrens:
        child_results = [process_key(c, prefix=key["label"]) for c in key_childrens]
        result = [result] + child_results

    return result


def process_document(document):
    """
    This function process the document to extract tables and keys.

    Args:
        document (dict): Contain tables, keys, and their hierarchical structure.

    Returns:
        dict: Processed data with 'document_id', 'keys', and 'tables'.

    Process Details:
        - Extract tables and process them into DataFrame using 'process_table'.
        - Identify and process keys using 'process_key', flattening keys data.
        - Combine the processed tables and keys into dictionary.

    Notes:
        - Handle multiple tables and keys in the document.
    """
    document_id = document["id"]
    document_items = document["children"]
    tables = [i for i in document_items if i["type"] == "table"]
    table_data_dfs = [process_table(t, document_id) for t in tables]
    keys = [i for i in document_items if i["type"] == "key"]
    if keys:
        keys = keys[0]["children"]
        processed_keys_data = [process_key(k) for k in keys]

        keys_data = []
        # Flaten the keys data
        for i in processed_keys_data:
            if isinstance(i, dict):
                keys_data.append(i)
            else:
                for x in i:
                    keys_data.append(x)
    else:
        keys_data = []
    return {"document_id": document["id"], "keys": keys_data, "tables": table_data_dfs}


class DJsonToExcel:
    def __init__(self, data_json, batch_path, batch_id):
        """Initialize the DJsonToExcel class instance"""
        self.data_json = deepcopy(data_json)
        self.batch_path = batch_path
        self.batch_id = batch_id

    def process(self):
        """
        Main function to process the data_json to excel file with keys and tables.

        Args:
            Operate on class attributes.

        Process Details:
            - Parse the JSON data and process each document using 'process_document'.
            - Create an Excel workbook with separate sheets for keys and tables.
            - Write key data including document IDs and key-value pairs to the "Keys" sheet.
            - Combine and write table data to the "Tables" sheet with 'document_id' and 'table_id'.

        Notes:
            - Generate an Excel file named 'd_json.xlsx' in the specified batch directory.
            - Handle hierarchical key structure and concatenate table data from multiple documents.
        """
        docs = self.data_json["nodes"]
        docs_data = [process_document(doc) for doc in docs]

        # output_json_path = os.path.join(self.batch_path, self.batch_id, 'd_json.json')
        # with open(output_json_path, 'w') as f:
        #     json.dump(docs_data, f)

        output_excel_path = os.path.join(self.batch_path, self.batch_id, "d_json.xlsx")
        workbook = Workbook(output_excel_path)
        keys_sheet = workbook.add_worksheet("Keys")

        #  Write Keys Data
        key_records = []

        for doc in docs_data:
            key_records.append(["Document ID:", doc["document_id"]])

            for k in doc["keys"]:
                key_records.append([k["label"], k["value"]])

        row = 0
        column = 0
        for i in key_records:
            if type(i[1]) == list:
                i[1] = "\n".join(i[1])
                keys_sheet.write_row(row, column, i)
            else:
                keys_sheet.write_row(row, column, i)
            row += 1

        tables_sheet = workbook.add_worksheet("Tables")

        #  Write Table Data
        tables_dfs = [pd.DataFrame()]

        for doc in docs_data:
            for table_df in doc["tables"]:
                tables_dfs.append(table_df)

        if len(tables_dfs) > 1:
            combined_results = pd.concat(tables_dfs)
            combined_results.fillna("", inplace=True)

            columns = list(combined_results.columns)
            columns.remove("document_id")
            columns.remove("table_id")

            columns.insert(0, "table_id")
            columns.insert(0, "document_id")

            combined_results = combined_results.reindex(columns=columns)
            table_records = combined_results.values.tolist()

            # Add table columns as first row
            try:
                table_records = [columns] + table_records
            except:
                print(traceback.print_exc())
                table_records = []
            row = 0
            column = 0
            for i in table_records:
                for idx, j in enumerate(i):
                    if type(j) == list:
                        i[idx] = "\n".join(j)
                tables_sheet.write_row(row, column, i)
                row += 1

        workbook.close()
