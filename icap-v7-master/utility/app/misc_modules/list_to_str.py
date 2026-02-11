def list_to_string_conversion(d_json):
    """This function converts a list of strings to a string"""
    docs = d_json["nodes"]

    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if not node_children:
                continue
            if "key" in node["type"]:
                for key_node_idx, key_node in enumerate(node_children):
                    if type(key_node.get("v")) == list:
                        key_node["v"] = ",".join(key_node.get("v"))

    return d_json
