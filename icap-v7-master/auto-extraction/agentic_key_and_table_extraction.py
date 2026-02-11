# from generate_llm_result import get_llm_result_kvv, get_llm_result_table
# from format_llm_result import get_formatted_llm_kvv_data, get_formatted_llm_table_data
# from websocket_service import send_log

# MAX_GENERATION_RETRY = 100


#     result = {}
#     for idx in range(MAX_GENERATION_RETRY):
#         kvv_llm_result = get_llm_result_kvv(layout_paths,ra_json,is_ra_json_available,True)
#         kvv_llm_result = get_formatted_llm_kvv_data(kvv_llm_result)
#         if kvv_llm_result["key_data"] != []:
#             result = kvv_llm_result
#             break
#     if result["key_data"] == []:
#     return result




#     result = {'table_data':[]}
#     for idx in range(MAX_GENERATION_RETRY):

#         table_llm_result = get_llm_result_table(layout_paths,ra_json,is_ra_json_available,True)
#         try:
#             table_llm_result = get_formatted_llm_table_data(table_llm_result)
#         except:
#             table_llm_result = {'table_data':[]}
#             pass


#         if table_llm_result["table_data"] != []:
#             result = table_llm_result
#             break
#     if result["table_data"] == []:
#     return result


import asyncio
from generate_llm_result import get_llm_result_kvv, get_llm_result_table_old
from format_llm_result import get_formatted_llm_kvv_data, get_formatted_llm_table_data
from redis_publisher import broadcast_log_update

MAX_GENERATION_RETRY_KVV_AGENT = 100
MAX_GENERATION_RETRY_TABLE_AGENT = 5


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


async def get_kvv_result_from_agent(
    layout_paths, ra_json, is_ra_json_available, batch_id
):
    await send_log_update(
        batch_id,
        "Auto-extraction LLM failed to extract any key-value data",
        [],
        True,
    )
    await send_log_update(batch_id, "Initiating key-value agent", [], True)

    result = {}
    for idx in range(MAX_GENERATION_RETRY_KVV_AGENT):
        kvv_llm_result = get_llm_result_kvv(
            layout_paths, ra_json, is_ra_json_available, True, False
        )
        kvv_llm_result = get_formatted_llm_kvv_data(kvv_llm_result)
        if kvv_llm_result["key_data"] != []:
            result = kvv_llm_result
            await send_log_update(
                batch_id,
                "Key-value agent generation completed",
                [],
                True,
            )
            break

    if result.get("key_data", []) == []:
        await send_log_update(
            batch_id,
            "Key-value agent also failed to extract any key-value data",
            [],
            True,
        )

    return result


async def get_table_result_from_agent(
    layout_paths, ra_json, is_ra_json_available, batch_id
):
    await send_log_update(
        batch_id,
        "Auto-extraction LLM failed to extract any table data",
        [],
        True,
    )
    await send_log_update(batch_id, "Initiating table agent", [], True)

    result = {"table_data": []}
    for idx in range(MAX_GENERATION_RETRY_TABLE_AGENT):
        table_llm_result = get_llm_result_table_old(
            layout_paths, ra_json, is_ra_json_available, True
        )
        try:
            table_llm_result = get_formatted_llm_table_data(table_llm_result)
        except:
            table_llm_result = {"table_data": []}

        if table_llm_result["table_data"] != []:
            result = table_llm_result
            await send_log_update(
                batch_id,
                "Table agent generation completed",
                [],
                True,
            )
            break

    if result.get("table_data", []) == []:
        await send_log_update(
            batch_id,
            "Table agent also failed to extract any table data",
            [],
            True,
        )

    return result
