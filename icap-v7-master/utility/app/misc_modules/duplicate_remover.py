import traceback


def duplicate_removal(d_json, definitions):
    """
    Function that removes multiples from data json when Remove Duplicates checkbox is clicked by the user
    """

    query_key_list = list()
    try:
        query_key_list = definitions[0]["key"]["items"]
    except:
        # print(traceback.print_exc())
        pass
    if not query_key_list:
        return d_json

    duplicate_trigger_list = list()
    label_holder = dict()
    general_list = list()

    for key in query_key_list:
        if key.get("removeDuplicates") == True:
            unique_id = key.get("id")
            label = key["keyLabel"]
            if key.get("qualifierValue"):
                label = key.get("qualifierValue")

            if unique_id:
                duplicate_trigger_list.append(unique_id)
                label_holder[unique_id] = label
            else:
                general_list.append(label)

    docs = d_json["nodes"]

    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if not node_children:
                continue
            if "key" in node["type"]:
                duplicate_checked = list()
                final_d_json_data_holder = dict()
                general_data_holder = dict()

                for keyNode_idx, key_node in enumerate(node_children):
                    duplicate_recognized = False
                    key_node_unique_id = key_node.get("unique_id")
                    if (
                        key_node_unique_id in duplicate_trigger_list
                        and key_node["label"] == label_holder[unique_id]
                    ):
                        if key_node_unique_id in final_d_json_data_holder.keys():
                            if key_node["v"] in final_d_json_data_holder.get(
                                key_node_unique_id
                            ):
                                duplicate_recognized = True
                            else:
                                final_d_json_data_holder[key_node_unique_id].append(
                                    key_node["v"]
                                )
                        else:
                            final_d_json_data_holder[key_node_unique_id] = [
                                key_node["v"]
                            ]
                    elif key_node["label"] in general_list:
                        if key_node["label"] in general_data_holder.keys():
                            if key_node["v"] in general_data_holder[key_node["label"]]:
                                duplicate_recognized = True
                            else:
                                general_data_holder[key_node["label"]].append(
                                    key_node["v"]
                                )

                        else:
                            general_data_holder[key_node["label"]] = [key_node["v"]]

                    if not duplicate_recognized:
                        duplicate_checked.append(key_node)

                target_doc["children"][i]["children"] = duplicate_checked

    return d_json
