

def manage_table_keys(vendor_definition, data_json):

    try:
        table_keys = vendor_definition["settings"]["table_exceptions"]["keys"]
    except:
         table_keys = []
         pass
    table_list = data_json["table_data"]

    if table_list == []:
        single_table_new = {"table_id":0,"table_name":"Table 1","table_data":{"rows":[{"row_id":0,"row_data":[]}]}}
        for idx_tk, tk in enumerate(table_keys):
            single_table_new["table_data"]["rows"][0]["row_data"].append({
                                                                          "value": tk["label"],
                                                                          "label": tk["keyFieldName"],
                                                                          "is_table_key":True,
                                                                          "is_profile_key_found":True
                                                                            })
        table_list.append(single_table_new)
    else:
        for idx_tk, tk in enumerate(table_keys):
            table_list[0]["table_data"]["rows"][0]["row_data"].append({
                                                                          "value": tk["label"],
                                                                          "label": tk["keyFieldName"],
                                                                          "is_table_key":True,
                                                                          "is_profile_key_found":True
                                                                            })


    return data_json