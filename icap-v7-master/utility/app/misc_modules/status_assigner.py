def assign_status(element):
    """
    This function accepts dictionary object. Goes inside and assigns a status 0 to each cell in table
    """
    children = element.get("children")
    if children:
        for index, child in enumerate(children):
            if not child.get("STATUS"):
                child["STATUS"] = 0
            assign_status(child)


def assing_node_status(d_json):
    nodes = d_json["nodes"]
    for node in nodes:
        assign_status(node)
    return d_json
