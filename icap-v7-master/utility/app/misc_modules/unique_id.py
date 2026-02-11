def assign_unique_id_helper(element):
    """
    This function accepts dictionary object. Based on ID of the provided dictionary object,
    it recursively provides ID to all its nested (child) elements.
    """
    base_id = element["id"]
    children = element.get("children")
    if children:
        for index, child in enumerate(children):
            child_id = f"{base_id}.{str(index + 1).zfill(3)}"
            # print(child_id, child['type'])
            child["id"] = child_id
            assign_unique_id_helper(child)


def assign_unique_id(d_json):
    nodes = d_json["nodes"]
    for node in nodes:
        assign_unique_id_helper(node)
    return d_json
