import traceback


def root_out_notInUse(d_json, request_data):
    """
    This function assigns a status -111 for fields where the user has selected not in use, and this status
    is used by output central to root out these and not sending them in the final output data.
    """
    try:
        definitions = request_data["definitions"]
    except:
        pass

    docs = d_json["nodes"]

    not_in_use_list = []
    if "notInUseItems" in definitions[0]["key"].keys():
        for idx, x in enumerate(definitions[0]["key"]["notInUseItems"]):
            not_in_use_dict = {}
            if "." in x["nestedLabel"]:
                mother_label = x["nestedLabel"].split(".")[0]
                child_label = x["nestedLabel"].split(".")[1]
            else:
                mother_label = x["nestedLabel"]
                child_label = mother_label
            keyId = x["keyId"][:36]
            not_in_use_dict["keyId"] = keyId
            not_in_use_dict["childLabel"] = child_label
            not_in_use_dict["motherLabel"] = mother_label

            not_in_use_list.append(not_in_use_dict)

    german_customs_status = False

    if request_data.get("project") == "ShipmentCreate":
        if definitions[0]["definition_id"][:2] == "DE":
            if (
                definitions[0]["type"].lower()
                == "export customs clearance documentation"
            ):
                german_customs_status = True

    def check(uid_label_combo, not_in_use_list):
        for data in not_in_use_list:
            if data["keyId"] + data["motherLabel"] == uid_label_combo:
                return True
        return False

    def check_compound(uid_label_combo, not_in_use_list):
        for data in not_in_use_list:
            if data["keyId"] + data["childLabel"] == uid_label_combo:
                return True
        return False

    if not not_in_use_list:
        return d_json

    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]
        for i, node in enumerate(nodes):
            node_children = node["children"]
            if not node_children:
                continue
            if "key" in node["type"]:
                for keyNode_idx, key_node in enumerate(node_children):
                    try:
                        uid_label_combo = key_node["unique_id"][:36] + key_node["label"]

                        if (german_customs_status == True) and (
                            key_node["label"] == "customsStatus"
                        ):
                            key_node["notInUse"] = True
                            key_node["STATUS"] = -111
                        if check(uid_label_combo, not_in_use_list):
                            all_data = [
                                d
                                for d in not_in_use_list
                                if d["keyId"] + d["motherLabel"] == uid_label_combo
                            ]
                            for data in all_data:
                                if data["motherLabel"] == key_node["label"]:
                                    if data["childLabel"] == data["motherLabel"]:
                                        for y in key_node["children"]:
                                            y["notInUse"] = True
                                            y["STATUS"] = -111
                                        key_node["notInUse"] = True
                                        key_node["STATUS"] = -111
                                    else:
                                        for y in key_node["children"]:
                                            if y["label"] == data["childLabel"]:
                                                y["notInUse"] = True
                                                y["STATUS"] = -111

                        for keyNode_idx_compound, key_node_compound in enumerate(
                            key_node["children"]
                        ):
                            if "unique_id" not in key_node_compound.keys():
                                continue
                            uid_label_combo_compound = (
                                key_node_compound["unique_id"][:36]
                                + key_node_compound["label"]
                            )
                            if check_compound(
                                uid_label_combo_compound, not_in_use_list
                            ):
                                all_data_compound = [
                                    d
                                    for d in not_in_use_list
                                    if d["keyId"] + d["childLabel"]
                                    == uid_label_combo_compound
                                ]
                                for data in all_data_compound:
                                    for y in key_node_compound["children"]:
                                        y["notInUse"] = True
                                        y["STATUS"] = -111
                                    key_node_compound["notInUse"] = True
                                    key_node_compound["STATUS"] = -111
                    except:
                        print(traceback.print_exc())

    return d_json
