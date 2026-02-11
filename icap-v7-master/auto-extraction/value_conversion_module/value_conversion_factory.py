from value_conversion_module.convert_to_decimal import apply_convert_decimals_to_cw1
from rapidfuzz import fuzz

def get_converted_value(data_json):

    kv_list = data_json["key_data"]
    table_list = data_json["table_data"]


    decimal_conversion_label = ["grossweight","length","height","width","netweight","packagecount"]

    for kv_idx, kv in enumerate(kv_list):
        if kv["key"].lower().replace(" ","").strip() in decimal_conversion_label:
            try:
                kv["value"] = apply_convert_decimals_to_cw1(kv["value"])
            except:
                pass

    
           

    for table_idx, table in enumerate(table_list):
            row_data = table["table_data"]["rows"]
            for row_idx, single_row_data in enumerate(row_data):
                single_row = single_row_data["row_data"]
                for col_id, col_data in enumerate(single_row):
                     if col_data["label"].lower().replace(" ","").strip() in decimal_conversion_label:
                        try:
                            col_data["value"] = apply_convert_decimals_to_cw1(col_data["value"])
                        except:
                            pass
                     
    return data_json



    