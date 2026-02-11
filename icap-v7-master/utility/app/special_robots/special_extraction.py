import traceback

from redis_utils import get_redis_data

from app.json_chunking import json_chunking_main


def get_left_pos(pos):
    return int(pos.split(",", 3)[0])


def get_top_pos(pos):
    return int(pos.split(",", 3)[1])


def get_right_pos(pos):
    return int(pos.split(",", 3)[2])


def get_bottom_pos(pos):
    return int(pos.split(",", 3)[3])


def replace_page_id_string(s, key, first_page_id):
    def end_nonzero_int_count(s):  # function added here by emon 04/04/22
        s = s.replace("TM", "")
        count = len(s)
        return count

    key = int(key)
    last_int_count = end_nonzero_int_count(first_page_id)
    last_int = first_page_id[-last_int_count:]
    new_key = str(key + int(last_int))
    new_key_len = len(new_key)

    "this function replaces key to key format of datacap"
    output = s[:-new_key_len] + new_key

    return output


def special_extraction_function(ra_json, doc_idx_in_loop, job_id):
    input_dict = get_redis_data(job_id).get("chunking_dictionary")
    values = input_dict[str(doc_idx_in_loop)]
    data = values["data"]

    first_page_id = None

    for page, line in data.items():
        if not first_page_id:
            for top_pos, chunks in line.items():
                first_page_id = chunks[0][2]

    vendor = ra_json["Vendor"]
    doc_type = ra_json["DocumentType"]

    rough_dict = dict()

    if "sick" in vendor.lower() and "shipping order" in doc_type.lower():
        try:
            print("Special Extraction from RAJSON Triggered")
            extracted_data = dict()
            key_name = "SRN"
            position = ""
            page_id = ""
            target_doc = ra_json["nodes"][doc_idx_in_loop]
            barcode_text = target_doc["children"][0]["Barcode1"]
            extracted_data["v"] = barcode_text
            extracted_data["pageId"] = page_id
            extracted_data["pos"] = position
            extracted_data["qualiferParent"] = "references"
            extracted_data["title"] = "special_extraction"
            rough_dict[key_name] = extracted_data
        except:
            pass
        try:
            extracted_data = dict()
            key_name = "SRN"
            position = ""
            page_id = ""
            target_doc = ra_json["nodes"][doc_idx_in_loop]
            shipping_order_ocr = target_doc["children"][0]["ShippingOrderOCR"]
            extracted_data["v"] = shipping_order_ocr
            extracted_data["pageId"] = page_id
            extracted_data["pos"] = position
            extracted_data["qualiferParent"] = "references"
            extracted_data["title"] = "special_extraction"
            rough_dict[key_name] = extracted_data
        except:
            pass

    elif "EMTEKO SIA" in vendor:
        try:
            print("Special Extraction from RAJSON Triggered")
            extracted_data = dict()
            key_name = "housebillNumber"
            position = ""
            page_id = ""
            target_doc = ra_json["nodes"][doc_idx_in_loop]
            barcode_text = target_doc["children"][0]["GetBarCode"]
            extracted_data["v"] = barcode_text
            extracted_data["pageId"] = page_id
            extracted_data["pos"] = position
            extracted_data["title"] = "special_extraction"
            rough_dict[key_name] = extracted_data
        except:
            print(traceback.print_exc())
            pass
    else:
        return {}

    return rough_dict
