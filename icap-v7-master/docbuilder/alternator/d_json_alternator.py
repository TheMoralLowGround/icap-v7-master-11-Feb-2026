"""
Organization: AIDocbuilder Inc.
File: d_json_alternator.py
Version: 6.0
 
Authors:
    - Vinay - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2023-11-08
 
Description:
    This script define functions for data cleaning and manipulating.
 
Main Features:
    - Remove unwanted cells from row.
"""
def none_removal(rows):
    """Remove unwanted cells based on specific criteria"""
    for row in rows:
        cells = row["children"].copy()
        for cell in cells:
            if (cell["label"] in ["None", "notInUse", ""]) or (
                cell["label"][-1].isnumeric()
            ):
                cells.remove(cell)
        row["children"] = cells
    return rows


def alter_function(vendorName, docType, rows):
    """Adjust the "dimensions" field in rows for specific conditions"""
    # rows = none_removal(rows)
    # Fixing dimensions`
    if ("airbus" in vendorName.lower()) and ("invoice" in docType.lower()):
        for row in rows:
            cells = row["children"].copy()
            dim_issue_found = False
            split_text = None
            for cell in cells:
                if cell["label"] == "dimensions_1":
                    dim_issue_found = True
                    split_text = cell["v"]
                    cells.remove(cell)
            if dim_issue_found and split_text:
                for cell in cells:
                    if cell["label"] == "dimensions":
                        cell["v"] += split_text

            row["children"] = cells

    return rows


# def qualifer_function(content):
#     table_definitions = content["definitions"][0]["table"]
#     column_defintions = table_definitions["columns"]
#     conversion_dict = list()
#     for column in column_defintions:
#         if column["qualifierValue"]:
#             {column["colName"] : column_defintions}


def process(input_content, data_json):
    return data_json
    # docs = data_json["nodes"]
    # for doc in docs:
    #     vendorName = doc["Vendor"]
    #     docType = doc["DocType"]
    #     nodes = doc["children"]
    #     for node in nodes:
    #         rows = node["children"]
    #         if "table" in node["id"]:
    #             node["children"] = alter_function(vendorName,docType, rows)
    #             #node["children"] = qualifer_function(input_content)

    #     nodes = parser(nodes)
    # return data_json
