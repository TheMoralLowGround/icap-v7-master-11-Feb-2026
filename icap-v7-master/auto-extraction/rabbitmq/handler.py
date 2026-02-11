"""
RabbitMQ handler for auto-extraction service.

This module contains handler functions for processing extraction tasks.
All async API callbacks have been replaced with RabbitMQ message publishing.
"""


import os
import sys
import json
import copy
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any
from producer import publish

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_llm_result import get_llm_result
from position_adder_old import add_postion_information_to_key_value_vendor, add_postion_information_to_table
from intelligent_parsers_module.intelligent_parsers_factory import get_intelligent_parsers_result
from sort_kv import sort_kv_by_alphabet
from data_json_converter import convert_data_json_to_v6_type
from process_doc_class_wise_process_keys import get_doc_class_wise_process_field
from process_difinition_wise_process_keys import get_modified_keys_based_on_definition
from normalized_process_name import normalize_process_name
from process_party_data import get_party_data
from process_vector_data import get_vector_data
from redis_publisher import broadcast_log_update

# Configure logging
logger = logging.getLogger(__name__)

# Thread-safe async executor for Redis publishing
_async_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="redis_publisher")

def _run_async_in_thread(coro):
    """Run async coroutine in a thread-safe manner."""
    def _run():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in async executor: {e}")
    
    future = _async_executor.submit(_run)
    # Don't wait for result to avoid blocking
    return future

def process_single_document(ra_json, doc_class_wise_process_field, definition_data, address_parser_example, batch_id, send_log):
    try:
        doc_id_based_on_ra_json = int(ra_json.get("id").split(".")[-1].strip())
        doc_type = ra_json["DocType"]
        field_need_to_extract = []
        existing_key_values = set()

        for doc_class_from_field, field_list in doc_class_wise_process_field.items():
            if (
                doc_class_from_field.lower().replace(" ", "").strip() in doc_type.lower().replace(" ", "").strip() and 
                doc_class_from_field.lower() != "no_doc_class" and 
                doc_class_from_field.lower() != "address_field_name" and 
                doc_class_from_field.lower() != "address_partial_field_name"
                ):
                field_need_to_extract.extend(field_list)
                for field in field_list:
                    existing_key_values.add(field.get("keyValue"))

        for field in doc_class_wise_process_field.get("no_doc_class", []):
            if field.get("keyValue") not in existing_key_values:
                field_need_to_extract.append(field)

        field_need_to_extract = get_modified_keys_based_on_definition(
            definition_data, field_need_to_extract, ra_json.get("id")
        )

        data_json, reasoning = get_llm_result(ra_json, field_need_to_extract)

        send_log(
            f"Autoextraction Reasoning - Doc: {ra_json.get('id')}",
            [],
            reasoning={
                "doc_id": ra_json.get("id"),
                "reasoning": reasoning,
            }
        )

        data_json, kvv_items = add_postion_information_to_key_value_vendor(
            [], ra_json, True, data_json
        )
        data_json = add_postion_information_to_table(
            [], ra_json, True, data_json, kvv_items
        )

        data_json = get_intelligent_parsers_result(
            data_json, address_parser_example,
            doc_class_wise_process_field.get("address_field_name", []),
            doc_class_wise_process_field.get("address_partial_field_name", []), 
            doc_type
        )
        data_json = sort_kv_by_alphabet(data_json)
        data_json["doc_type"] = ra_json["DocType"]
        data_json["id"] = ra_json.get("id", "")

        return (doc_id_based_on_ra_json, copy.deepcopy(data_json), None)

    except Exception as e:
        doc_id = ra_json.get("id", "unknown")
        error_msg = f"Error processing document {doc_id}: {str(e)}"
        return (None, None, error_msg)


def extraction_task(data: Dict[str, Any]):
    """RabbitMQ task for auto extraction processing"""
    profile_keys = data.get("keys", {})
    process_field = data.get("keys", {})
    mapped_keys = data.get("mappedKeys", [])
    ra_json_combined = data.get("ra_json")
    message_type = "extraction"
    job_id = data.get("job_id")
    batch_id = data.get("batch_id")
    VERSION = "v2.0.0 23122024"
    app_version_name = data.get("app_version_name")
    definition_data = data.get("exception_data", [])
    address_parser_example = data.get("address_parser_example", {})
    process_uid = data.get("process_uid","")
    
    # Helper function to send websocket logs
    def send_log(title, sub_messages_list=None, reasoning=None):
        try:
            log_data = {
                "batch_id": batch_id,
                "title": title,
                "sub_messages_list": sub_messages_list or [],
                "is_agent": False,
            }
            if reasoning:
                log_data["reasoning"] = reasoning
            _run_async_in_thread(broadcast_log_update(log_data))
        except Exception as e:
            logger.error(f"Failed to send websocket log: {e}")

    process_name = data.get("profile_name", "")
    if process_name:
        process_name = normalize_process_name(process_name)

    combined_data_json = {"documents": []}
    combined_data_json_ids = []
    entity_list = []

    doc_class_wise_process_field, is_error, msg = get_doc_class_wise_process_field(process_field)

    if is_error:
        error_msg = "Field Description missing"
        result = {
            "batch_id": data.get("batch_id"),
            "job_id": job_id,
            "error": f"Process failed: {msg}",
            "messages": [],
            "entity": entity_list,
            "status_code": 400,
        }
        publish('extraction_response', 'to_pipeline', result)
        return

    try:
        send_log(f"Autoextraction Version: {VERSION}", [])

        num_documents = len(ra_json_combined["nodes"])
        max_workers_from_env = int(os.getenv("MAX_WORKER_THREAD", 10))
        max_workers = min(max_workers_from_env, num_documents)

        send_log(f"Processing {num_documents} documents with {max_workers} parallel workers", [])

        results_dict = {}
        errors = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            future_to_index = {
                executor.submit(
                    process_single_document,
                    ra_json,
                    doc_class_wise_process_field,
                    definition_data,
                    address_parser_example,
                    batch_id,
                    send_log,
                ): idx for idx, ra_json in enumerate(ra_json_combined["nodes"])
            }


            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    doc_id, data_json, error_msg = future.result()
                    
                    if error_msg:
                        errors.append(error_msg)
                        send_log(error_msg, [])
                    else:
                        results_dict[idx] = (doc_id, data_json)
                        
                except Exception as e:
                    error_msg = f"Future execution error for index {idx}: {str(e)}"
                    errors.append(error_msg)
                    send_log(error_msg, [])

        for idx in sorted(results_dict.keys()):
            doc_id, data_json = results_dict[idx]
            combined_data_json_ids.append(doc_id)
            combined_data_json["documents"].append(data_json)

        if errors:
            send_log(
                f"Completed with {len(errors)} errors out of {num_documents} documents", []
            )

        combined_data_json = get_party_data(combined_data_json, process_uid)
        combined_data_json = get_vector_data(combined_data_json, process_uid, doc_class_wise_process_field.get("address_field_name", []), doc_class_wise_process_field.get("address_partial_field_name", []))

        combined_data_json_converted_like_v6 = convert_data_json_to_v6_type(
            combined_data_json, ra_json_combined, combined_data_json_ids
        )
        
        result = {
            "batch_id": data.get("batch_id"),
            "job_id": job_id,
            "data_json": combined_data_json_converted_like_v6,
            "error": "",
            "entity": entity_list,
            "messages": [],
            "status_code": 200,
        }

        publish('extraction_response', 'to_pipeline', result)

    except Exception as error:

        result = {
            "batch_id": data.get("batch_id"),
            "job_id": job_id,
            "error": f"Process failed: {str(error)}",
            "messages": [],
            "entity": entity_list,
            "status_code": 400,
        }

        publish('extraction_response', 'to_pipeline', result)

def extraction_task_handler(body):
    """
    RabbitMQ handler for extraction_task.
    Processes auto-extraction tasks and publishes results to RabbitMQ.
    """
    try:
        data = json.loads(body)
        extraction_task(data)
    except Exception as e:
        error_result = {
            "batch_id": data.get('batch_id', 'unknown') if 'data' in locals() else 'unknown',
            "error": f"Extraction task handler failed: {str(e)}",
            "status_code": 400,
        }
        publish('extraction_response', 'to_pipeline', error_result)

print("Auto-extraction RabbitMQ handler loaded")
