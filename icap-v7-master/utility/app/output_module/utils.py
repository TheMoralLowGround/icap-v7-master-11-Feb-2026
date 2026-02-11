import traceback


def reduce_data_json_for_output_json(request_data):
    """
    Reduce data json that are auto extracted to map only that user has selected.
    """
    try:
        # profile_keys = request_data["profile_keys"]
        data_json = request_data["data_json"]
        nodes = data_json["nodes"]
        for node in nodes:
            for doc in node["children"]:
                if doc.get("type") == "key":
                    new_key_children = []
                    for key_detail in doc.get("children", [])[:]:
                        if key_detail.get("v") is not None and str(key_detail.get("v")).strip() == "":
                            continue
                        new_key_children.append(key_detail)
                        # if key_detail.get("is_auto_extracted", False):
                        # for profile_key in profile_keys:
                        #     if profile_key.get("label", None) == key_detail.get(
                        #         "label", None
                        #     ):
                    doc["children"] = new_key_children
    except:
        print("Error when reducing data_json for output json", traceback.print_exc())
    return data_json
