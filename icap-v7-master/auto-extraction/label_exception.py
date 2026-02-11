from rapidfuzz import fuzz

def get_exception_handled_label(vendor_definition, data_json):

    if vendor_definition == {}:
        return data_json
    
    vendor_name_from_definition = vendor_definition["vendor_name"]

    try:
        label_exception_list = vendor_definition["settings"]["label_exceptions"]
    except:
        label_exception_list = []
        pass

    vendor_name_from_extraction = data_json["vendor"]["vendor"]

    if fuzz.ratio(vendor_name_from_definition,vendor_name_from_extraction) >= 90:
        try:
            key_value_list = data_json['key_data']
            
            for idx, item in enumerate(label_exception_list):
                for kv in key_value_list:
                    if kv.get('is_label_exception_done'):
                       continue
                    
                    if item["convert_from"].strip() == kv['key'].strip():
                        kv['key'] = item["convert_to"]
                        kv['is_label_exception_done'] = True

            return data_json    

        except:
            return data_json
            pass
    else:
        return data_json



