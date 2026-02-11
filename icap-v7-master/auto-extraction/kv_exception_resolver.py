import os
import requests

from rapidfuzz import fuzz


def get_mapped_exception_key_label(kv_list, exception_list, profile_keys):
    tmp_pk_dict = {}
    for item in tmp_pk_dict:
        tmp_pk_dict[item["keyLabel"]] = item.get("keyValue")

    done_list = []
    for kv in kv_list:
        for item in exception_list:
            if (
                fuzz.ratio(kv["key"].lower().strip(), item["label"].lower().strip())
                >= 80
                and item not in done_list
            ):
                kv["key"] = item["process_key"]
                kv["key_value"] = tmp_pk_dict.get(item["process_key"])
                done_list.append(item)
    return kv_list


def filter_kv_based_on_exception(exception_kv_list, exception_list):

    result = []
    for item in exception_list:
        is_kv_found = False
        for kv in exception_kv_list:
            if (
                fuzz.ratio(item["label"].lower().strip(), kv["key"].lower().strip())
                >= 80
            ):
                result.append(kv)
                is_kv_found = True
                break
        if not is_kv_found:
            result.append(
                {
                    "key": item["label"],
                    "key_position": "0,0,0,0",
                    "value": "",
                    "value_position": "0,0,0,0",
                    "page_id": item["page_id"],
                    "original_key": item["label"],
                    "original_key_label": item["label"],
                    "is_label_mapped": False,
                    "is_profile_key_found": False,
                    "is_data_exception_done": False,
                    "is_pure_autoextraction": True,
                }
            )
    return result


def remove_duplicate_from_extraction_kv_list(result, key_value_list):

    kv_list_filtered = []
    for kv in key_value_list:
        is_duplicate = False
        for kv_ex in result:
            if (
                fuzz.ratio(kv["key"].lower().strip(), kv_ex["key"].lower().strip())
                >= 95
            ):
                is_duplicate = True
                break
        if not is_duplicate:
            kv_list_filtered.append(kv)
    return kv_list_filtered


# def get_kv_exception_data(
#     ra_json, key_value_list, doc_wise_kv_exception_list, profile_keys
# ):

#     try:
#         result = requests.post(
#             f"{EXCEPTION_AGENT_API_URL}/api/v1/kv_exception",
#             json={
#                 "ra_json": ra_json,
#                 "kv_list": key_value_list,
#                 "exception_list": doc_wise_kv_exception_list,
#             },
#         )
#         result = result.json()
#         result = result["result"]
#     except:
#         result = []
#         pass

#     result = filter_kv_based_on_exception(result, doc_wise_kv_exception_list)
#     extraction_filtered_kv = remove_duplicate_from_extraction_kv_list(
#         result, key_value_list
#     )
#     result = get_mapped_exception_key_label(
#         result, doc_wise_kv_exception_list, profile_keys
#     )

#     return result, extraction_filtered_kv
