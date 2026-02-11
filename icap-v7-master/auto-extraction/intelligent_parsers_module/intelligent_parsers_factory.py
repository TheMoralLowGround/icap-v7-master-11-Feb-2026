


"""
def get_parsed_address(data_json):
    if data_json == {}:
        return data_json
    
    kv_list = data_json.get("key_data",[])
    for kv_idx, kv_pair in enumerate(kv_list):
        if kv_pair.get("key_type","") == "addressBlock":
            results = process(kv_pair["value"])
            children = []

            if len(results) == 1:
                continue
            elif len(results) == 3:
                children = [
                    {"key":"Location", "value":results[0]},
                    {"key":"Location Country", "value":results[1]},
                    {"key":"Extra Data", "value":results[2]}
                ]
            elif len(results) == 4:
                children = [
                    {"key":"Location", "value":results[0]},
                    {"key":"Location Code", "value":results[1]},
                    {"key":"Location Country", "value":results[2]},
                    {"key":"Extra Data", "value":results[3]}
                ]
                
            kv_pair["children"] = copy.deepcopy(children)

    return data_json
"""



"""
def get_parsed_address(data_json):
    if data_json == {}:
        return data_json
    
    kv_list = data_json.get("key_data",[])
    for kv_idx, kv_pair in enumerate(kv_list):
        if kv_pair.get("type","") == "addressBlock" or kv_pair.get("type","") == "addressBlockPartial":
            try:
                results = custom_address_parser(kv_pair["value"], {}, master_dictionary,"")
            except:
                results = {}
                pass
            children = []
            for k,v in results.items():
                children.append({
                    "key":k,
                    "value":v,
                    "is_profile_key_found" : True
                })
            kv_pair["children"] = copy.deepcopy(children)

            
    return data_json
"""


from intelligent_parsers_module.address_parser_agent import get_parsed_address
from intelligent_parsers_module.dimension_parser_agent import get_parsed_dimension




def get_intelligent_parsers_result(data_json, address_parser_example,address_field_name, address_partial_field_name, doc_type):

    data_json = get_parsed_address(data_json, address_parser_example,address_field_name, address_partial_field_name, doc_type)
    #data_json = get_parsed_dimension(data_json)

    return data_json