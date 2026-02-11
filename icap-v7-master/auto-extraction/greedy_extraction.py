import asyncio
from generate_llm_result import get_llm_result_kvv, get_llm_result_table_old
from format_llm_result import get_formatted_llm_kvv_data, get_formatted_llm_table_data
from redis_publisher import broadcast_log_update


async def send_log_update(
    batch_id, title, sub_messages_list, is_agent=False
):
    """Async wrapper for broadcast_log_update to match old signature"""
    await broadcast_log_update(
        {
            "batch_id": batch_id,
            "title": title,
            "sub_messages_list": sub_messages_list,
            "is_agent": is_agent,
        }
    )


def get_result_with_highest_key_data(
    kvv_llm_result_1, kvv_llm_result_2, kvv_llm_result_3
):
    return max(
        [kvv_llm_result_1, kvv_llm_result_2, kvv_llm_result_3],
        key=lambda x: len(x["key_data"]),
    )


def empty_value_count(d_json):
    count = 0
    for item in d_json["key_data"]:
        if item["value"].strip() == "":
            count += 1
    return count


async def get_greedy_kvv_result(
    layout_paths, ra_json, is_ra_json_available, batch_id
):
    await send_log_update(
        batch_id, "Triggering greedy approach of KVV LLM", [], False
    )

    kvv_llm_result_1 = {}
    for i in range(5):
        kvv_llm_result_1_tmp = get_llm_result_kvv(
            layout_paths,
            ra_json,
            is_ra_json_available,
            False,
            True,
            {"temperature": 0.8},
        )
        kvv_llm_result_1_tmp = get_formatted_llm_kvv_data(kvv_llm_result_1_tmp)

        if i == 0:
            kvv_llm_result_1 = kvv_llm_result_1_tmp
        elif empty_value_count(kvv_llm_result_1_tmp) < empty_value_count(
            kvv_llm_result_1
        ) and len(kvv_llm_result_1_tmp["key_data"]) > len(kvv_llm_result_1["key_data"]):
            kvv_llm_result_1 = kvv_llm_result_1_tmp

    await send_log_update(
        batch_id,
        "Completed greedy depth level 1 for KVV LLM",
        [],
        False,
    )

    kvv_llm_result_2 = {}
    for i in range(5):
        kvv_llm_result_2_tmp = get_llm_result_kvv(
            layout_paths,
            ra_json,
            is_ra_json_available,
            False,
            True,
            {"temperature": 0.9},
        )
        kvv_llm_result_2_tmp = get_formatted_llm_kvv_data(kvv_llm_result_2_tmp)
        if i == 0:
            kvv_llm_result_2 = kvv_llm_result_2_tmp
        elif empty_value_count(kvv_llm_result_2_tmp) < empty_value_count(
            kvv_llm_result_2
        ) and len(kvv_llm_result_2_tmp["key_data"]) > len(kvv_llm_result_2["key_data"]):
            kvv_llm_result_2 = kvv_llm_result_2_tmp

    await send_log_update(
        batch_id,
        "Completed greedy depth level 2 for KVV LLM",
        [],
        False,
    )

    kvv_llm_result_3 = {}
    for i in range(5):
        kvv_llm_result_3_tmp = get_llm_result_kvv(
            layout_paths, ra_json, is_ra_json_available, False, True, {"temperature": 1}
        )
        kvv_llm_result_3_tmp = get_formatted_llm_kvv_data(kvv_llm_result_3_tmp)
        if i == 0:
            kvv_llm_result_3 = kvv_llm_result_3_tmp
        elif empty_value_count(kvv_llm_result_3_tmp) < empty_value_count(
            kvv_llm_result_3
        ) and len(kvv_llm_result_3_tmp["key_data"]) > len(kvv_llm_result_3["key_data"]):
            kvv_llm_result_3 = kvv_llm_result_3_tmp

    await send_log_update(
        batch_id,
        "Completed greedy depth level 3 for KVV LLM",
        [],
        False,
    )

    result = get_result_with_highest_key_data(
        kvv_llm_result_1, kvv_llm_result_2, kvv_llm_result_3
    )

    return result



#     kvv_llm_result = get_llm_result_kvv(layout_paths, ra_json, is_ra_json_available, False, True,{"temperature":1, "num_of_generation" : 7})
#     kvv_llm_result = get_formatted_llm_kvv_data(kvv_llm_result)
#     # kvv_llm_result_2 = get_llm_result_kvv(layout_paths, ra_json, is_ra_json_available, False, True, {"temperature":0.9, "num_of_generation" : 5})
#     # kvv_llm_result_2 = get_formatted_llm_kvv_data(kvv_llm_result)

#     # kvv_llm_result_3 = get_llm_result_kvv(layout_paths, ra_json, is_ra_json_available, False, True,{"temperature":1, "num_of_generation" : 7})
#     # kvv_llm_result_3 = get_formatted_llm_kvv_data(kvv_llm_result)


#     return  kvv_llm_result
