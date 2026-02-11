from rapidfuzz import fuzz

def get_entities(data_json):
    
    candidates = [
                "shipper","consignee","seller","buyer","sold to","ship to",
                "bill to","pay to","notify party","carrier","forwarder","broker",
                "agent","consignor","incoterm","incoterms","carrier", "ship from", "supplier", "exporter", "vendor address", "shipper name", "consignee name","seller name","buyer name"
                ]
    
    entity_list = []
    
    for doc_item in data_json["nodes"]:
        for extracted_item in doc_item["children"]:
            if extracted_item["type"] != "key":
                continue
            else:
                for kv_pair in extracted_item["children"]:
                    label = kv_pair["label"]
                    scores = [(cand, fuzz.ratio(label.lower().strip(), cand.lower().strip())) for cand in candidates]
                    best_match, best_score = max(scores, key=lambda x: x[1])
                    if best_score >= 90:
                        entity_list.append(kv_pair)
                        
    return entity_list


                    
                    
