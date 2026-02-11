"""

This is a spceicfic exceptional alternator where we have the capability to alter the
data-json itself.

Legacy and to be made redundant by introducing GUI based post-processing.

"""


def process(d_json):
    input_json = d_json.copy()
    profile_id = input_json["DefinitionID"]
    docType = input_json["DocumentType"]
    vendor_name = input_json["Vendor"]
    documents = input_json["nodes"]

    if "arburg" in profile_id.lower() and "shipping order" in docType.lower():
        for document_idx, document in enumerate(documents):
            nodes = document["children"]
            for node_idx, node in enumerate(nodes):
                if node["type"] == "key":
                    new_list = list()
                    key_value_items = node["children"]
                    for key_value_item in key_value_items:
                        label = key_value_item["label"]
                        if (
                            label == "consigneeAccountNumber"
                            and key_value_item["v"][0] == "D"
                        ):
                            # print(key_value_item)
                            key_value_item["v"] = "0" + key_value_item["v"][1:]
                        try:
                            if label == "MRN":
                                # print(key_value_item)
                                key_value_item["v"] = key_value_item["v"].split(" ")[0]
                        except:
                            pass
                        new_list.append(key_value_item)
                    node["children"] = new_list
                nodes[node_idx] = node
            document["children"] = nodes
            documents[document_idx] = document

    try:
        if (
            "VALEOPYEONGHWAMETAL".lower() in profile_id.lower()
            and "Commercial invoice".lower() in docType.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        new_list = list()
                        key_value_items = node["children"]
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "consignee":
                                # print(key_value_item)
                                key_value_item["v"] = key_value_item["v"].replace(
                                    "VALE()", "VALEO"
                                )
                            if label == "shipper":
                                # print(key_value_item)
                                key_value_item["v"] = key_value_item["v"].replace(
                                    "VALE()", "VALEO"
                                )
                            new_list.append(key_value_item)
                        node["children"] = new_list
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        pass

    try:
        if (
            "DE_FESTO_FRA_PDF".lower() in profile_id.lower()
            and "Shipping Order".lower() in docType.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        new_list = list()
                        key_value_items = node["children"]
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "incoterms":
                                print(key_value_item)
                                if "Notify" in key_value_item["v"]:
                                    key_value_item["v"] = key_value_item["v"].split(
                                        "\n"
                                    )[0]
                            new_list.append(key_value_item)
                        node["children"] = new_list
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        pass
    try:
        if (
            "CA_GDLS_CANADA".lower() in profile_id.lower()
            and "Commercial Invoice".lower() in docType.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "key":
                        new_list = list()
                        key_value_items = node["children"]
                        for key_value_item in key_value_items:
                            label = key_value_item["label"]
                            if label == "incoterms":
                                print(key_value_item)
                                try:
                                    split_string = key_value_item["v"].split(")")
                                    key_value_item["v"] = split_string[0]
                                except:
                                    pass
                            new_list.append(key_value_item)
                        node["children"] = new_list
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        pass
    try:
        if (
            "AU_HPPPSAU".lower() in profile_id.lower()
            and "Shippers Letter of Instruction".lower() in docType.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        cells = node["children"]
                        for cell in cells:
                            new_list = list()
                            table_items = cell["children"]
                            for table_item in table_items:
                                label = table_item["label"]
                                if label == "dimensions":
                                    print(table_item)
                                    if "x" in table_item["v"]:
                                        try:
                                            table_item["v"] = table_item["v"].replace(
                                                "x", "X"
                                            )
                                        except:
                                            pass
                                new_list.append(table_item)
                            cell["children"] = new_list
                        node["children"] = cells
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        pass
    try:
        if (
            "PALL FILTERSYSTEMS".lower() in vendor_name.lower()
            and "Packing List".lower() in docType.lower()
            and "DE_PALL".lower() in profile_id.lower()
        ):
            for document_idx, document in enumerate(documents):
                nodes = document["children"]
                for node_idx, node in enumerate(nodes):
                    if node["type"] == "table":
                        cells = node["children"]
                        for cell in cells:
                            new_list = list()
                            table_items = cell["children"]
                            for table_item in table_items:
                                label = table_item["label"]
                                if label == "packageCount":
                                    print(table_item)
                                    pack_count = table_item["v"]
                                    for char in pack_count[:]:
                                        if char.isalpha() == True:
                                            pack_count = pack_count.replace(char, "")
                                    table_item["v"] = pack_count
                                new_list.append(table_item)
                            cell["children"] = new_list
                        node["children"] = cells
                    nodes[node_idx] = node
                document["children"] = nodes
                documents[document_idx] = document
    except:
        pass
    return d_json
