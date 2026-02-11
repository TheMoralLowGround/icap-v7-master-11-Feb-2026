"""
Organization: AIDocbuilder Inc.
File: scripts/DataJson.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script modify ra_json to data_json with relevant data.

Dependencies:
    - deepcopy from copy

Main Features:
    - Modify ra_json to data_json.
"""
from copy import deepcopy


class DataJson:
    def __init__(self, ra_json):
        """Initialize the DataJson class instance"""
        self.data_json = deepcopy(ra_json)

    def process(self):
        """
        Filter out specific nodes and keep only relevant data.

        Args:
            Operate on class attributes.

        Returns:
            data_json (dict): Updated JSON data with filtered nodes.

        Process Details:
            - Loop through the 'nodes' in the JSON data.
            - Exclude nodes of type 'docBuilder'.
            - Remove the 'children' data from the remaining nodes.
            - Update the JSON data with the filtered nodes.

        Notes:
            - To prevent modification the original data used deepcopy.
        """
        documents = self.data_json["nodes"]
        new_documents = []
        for document in documents:
            if document["type"] != "docBuilder":
                document["children"] = []
                new_documents.append(document)

        self.data_json["nodes"] = new_documents
        return self.data_json
