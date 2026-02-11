"""
Organization: AIDocbuilder Inc.
File: utils/assembly_utils.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-12-11

Description:
    This file handle the major parts of assembly process.

Dependencies:
    - os, json, traceback
    - Callable from typing
    - deepcopy from copy
    - ConcurrentAPIExecutor from pipeline.scripts.ConcurrentAPIExecutor
    - Batch, EmailParsedDocument from core.models
    - save_analyzer_log_time, get_merged_definition_settings, get_additional_doc_type from utils.utils
    - send_customs_json, upload_document_to_edm, send_dsc_wms_json, send_shipment_create_json,
      send_shipment_update_json, get_shipment_status, send_shipment_time_stamp, upload_document_to_usa,
      send_freight_json from utils.assembly_api_utils

Main Features:
    - Handle API call for multi-shipment or other projects.
    - Handle file by file document upload.
    - Hanlde additional document upload.
    - Clean and prepare the API request data.
    - Save API response to database.
    - Handle errors and retry mechanisms.
    - Prepare the email context based on the outcome.
"""

import os
import json
import traceback
from bs4 import BeautifulSoup
from typing import Callable
from copy import deepcopy
from itertools import zip_longest

from pipeline.scripts.ConcurrentAPIExecutor import ConcurrentAPIExecutor

from utils.utils import (
    save_analyzer_log_time,
    get_merged_definition_settings,
    get_additional_doc_type,
    extend_list_to_index,
)

from utils.assembly_api_utils import (
    send_customs_json,
    upload_document_to_edm,
    send_dsc_wms_json,
    send_shipment_create_json,
    send_shipment_update_json,
    get_shipment_status,
    send_shipment_time_stamp,
    upload_document_to_usa,
    send_freight_json,
    upload_fcm_document_to_edm,
)

from core.models import (
    Batch,
    EmailParsedDocument,
    ApplicationSettings,
    ShipmentRecord,
)


MAX_RETRY = int(os.getenv("MAX_RETRY", 0))
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 0))


def handle_api_call(
    write_parent_batch_log: Callable,
    email_instance,
    matched_profile_instance,
):
    """
    This is the main function to handle API call for multi-shipment or other projects and manage response.

    Args:
        write_parent_batch_log (Callable): Write logs for parent batch.
        email_instance (object): Instance contain email_batch data.
        matched_profile_instance (object): Instance contain profile data.

    Returns:
        all_passed (bool): Indicate all API calls were successful.
        is_retrying (bool): Indicate any API call is being retried.

    Process Details:
        - Validate if the email instance has assembled_results.
        - Initialize variables for email_id, confirmation_numbers, case_id, multi_shipment and send_time_stamp.
        - Handle API call for multi-shipment or iterate through assembled results for other projects.
        - Retrieve existing API response, clean request data, and perform API call.
        - Handle timestamps API call and manage retry for failed API call.
        - Update confirmation_numbers in the email instance and save changes.

    Notes:
        - Retry is triggered for failed API call, and retry counts are incremented.
    """
    all_passed = True
    is_retrying = False

    if not email_instance.assembled_results:
        all_passed = False
        return all_passed, is_retrying

    email_id = email_instance.id
    confirmation_numbers = []
    case_id = None
    send_time_stamp = matched_profile_instance.send_time_stamp
    multi_shipment = matched_profile_instance.multi_shipment

    if len(email_instance.api_response) == 0:
        save_analyzer_log_time(batch_id=email_id, field_name="api_call_s")

    if multi_shipment:
        all_passed, is_retrying, confirmation_numbers, milestones = (
            handle_multi_shipment_api_call(write_parent_batch_log, email_instance)
        )

        # Handle Timestamp API call for multi-shipment
        if (
            all_passed
            and send_time_stamp
            and milestones
            and len(milestones)
            and any([i["milestone"] for i in milestones])
        ):
            write_parent_batch_log(
                message=f"Initializing Timestamp API call",
                batch_id=email_id,
                status="inprogress",
            )

            timestamp_retry_limit = 3

            for i in range(timestamp_retry_limit + 1):
                is_retry_applicable = i < timestamp_retry_limit
                failed_api_call_count = handle_multi_shipment_time_stamp_api_call(
                    write_parent_batch_log,
                    email_instance,
                    milestones,
                    is_retry_applicable,
                )

                if not failed_api_call_count:
                    break
    else:
        for index, result in enumerate(email_instance.assembled_results):
            api_response = None

            # Get API response from DB if it already saved
            if len(email_instance.api_response) > index:
                api_response = email_instance.api_response[index]

            request_type = result["type"]
            request_data = deepcopy(result["data"])

            request_data, milestone, case_id, identifier = clean_api_request_data(
                email_instance, request_type, request_data, send_time_stamp
            )

            if (
                api_response
                and api_response["status_code"] == 200
                and request_type != "shipment-create"
            ):
                continue

            response_json, status_code, is_retrying = handle_project_wise_api_call(
                write_parent_batch_log,
                email_instance,
                request_type,
                request_data,
                api_response,
                case_id,
                is_retrying,
            )

            if is_retrying:
                save_analyzer_log_time(
                    batch_id=email_id, field_name="retry_each_api_time"
                )
            else:
                save_analyzer_log_time(batch_id=email_id, field_name="each_api_call_e")

            all_passed, is_breakable = log_api_response_in_timeline(
                write_parent_batch_log,
                email_instance,
                is_retrying,
                api_response,
                status_code,
                request_type,
                index,
                result,
                response_json,
            )

            if is_breakable:
                break

            save_api_response_to_db(
                email_instance, index, status_code, response_json, result
            )

            # Handle time stamp api call
            all_passed, is_retrying = handle_time_stamp_api_call(
                write_parent_batch_log,
                email_instance,
                response_json,
                milestone,
                all_passed,
                is_retrying,
                status_code,
                send_time_stamp,
                request_type,
            )

            if is_retrying:
                email_instance.api_retry_count += 1
                email_instance.save()
                break

            # Update confirmation number in DB
            confirmation_numbers = update_confirmation_numbers(
                email_instance,
                status_code,
                request_type,
                request_data,
                response_json,
                case_id,
                result,
                confirmation_numbers,
            )

    # Update the confirmation_numbers field in the EmailBatch instance
    email_instance.confirmation_numbers = confirmation_numbers
    email_instance.save()

    if not is_retrying:
        save_analyzer_log_time(batch_id=email_id, field_name="api_call_e")

    return all_passed, is_retrying


def handle_multi_shipment_api_call(write_parent_batch_log: Callable, email_instance):
    """
    Handle API call for multi-shipment by preparing payloads, executing concurrent requests and processing response.

    Args:
        write_parent_batch_log (Callable): Write logs for parent batch.
        email_instance (object): Instance contain email_batch data.

    Returns:
        all_passed (bool): Indicate all API calls were successful.
        is_retrying (bool): Indicate any API call is being retried.
        confirmation_numbers (list): Confirmation numbers from successful API call.
        milestones (list): Milestone list for Timestamp API call.

    Process Details:
        - Prepare the payload for multi-shipment API call using 'prepare_multi_shipment_api_payload'.
        - Execute concurrent API requests using 'ConcurrentAPIExecutor'.
        - Process API response to determine success, retries, and confirmation_numbers.
        - Log the response status and update the retry for failed API call.

    Notes:
        - Number of concurrent workers and timeout is configurable via 'ConcurrentAPIExecutor'.
    """
    confirmation_numbers = []
    email_id = email_instance.id

    final_jsons, identifiers, milestones = prepare_multi_shipment_api_payload(
        email_instance
    )

    if email_instance.api_retry_count == 0:
        write_parent_batch_log(
            message=f"Calling Shipment-Create API to send payload ({len(final_jsons)})",
            batch_id=email_id,
            remarks="",
            status="inprogress",
            action="display_paginated_json",
        )

    api_executor = ConcurrentAPIExecutor(max_workers=30, timeout=300)
    all_responses = api_executor.execute(final_jsons)

    all_passed, is_retrying, failed_api_call_count, confirmation_numbers = (
        process_multi_shipment_api_response(
            email_instance, all_responses, identifiers, milestones
        )
    )

    message_prefix = "Shipment-Create API call"
    is_retrying = log_multi_shipment_api_response_in_timeline(
        write_parent_batch_log,
        message_prefix,
        email_instance,
        all_responses,
        failed_api_call_count,
        is_retrying,
    )

    return all_passed, is_retrying, confirmation_numbers, milestones


def prepare_multi_shipment_api_payload(email_instance):
    """
    Prepare the payload for multi-shipment API call.

    Args:
        email_instance (object): Instance contain email_batch data.

    Returns:
        final_jsons (list): Contain request_data, response_json, status_code and callable_api.
        identifiers (list): Unique identifiers extracted from request_data.

    Process Details:
        - Iterate through 'assembled_results' to build payloads for each shipment.
        - Extract and remove the 'identifier' from the request data for each result.
        - Associate 'api_responses' and 'shipment_status_urls' with corresponding payloads if available.
        - Determine 'callable_api' function 'send_shipment_create_json' or 'get_shipment_status' based on the presence of statusURL.

    Notes:
        - Identifiers are preserved for later use in processing responses.
    """
    final_jsons = []
    identifiers = []
    milestones = []

    api_responses = email_instance.api_response
    shipment_status_urls = email_instance.shipment_status_url

    for index, result in enumerate(email_instance.assembled_results):
        request_data = deepcopy(result["data"])
        response_json = {}
        status_code = None
        callable_api = send_shipment_create_json

        identifier = request_data.get("identifier")
        if identifier:
            request_data.pop("identifier")
        identifiers.append(identifier)

        milestone = request_data.get("milestone")
        if milestone:
            request_data.pop("milestone")
        milestones.append({"milestone": milestone})

        if isinstance(api_responses, list) and index < len(api_responses):
            response_json = api_responses[index]["response_json"]
            status_code = api_responses[index]["status_code"]

        if (
            shipment_status_urls
            and index < len(shipment_status_urls)
            and shipment_status_urls[index]
        ):
            response_json["statusURL"] = shipment_status_urls[index]
            callable_api = get_shipment_status

        final_jsons.append(
            {
                "request_data": request_data,
                "response_json": response_json,
                "status_code": status_code,
                "callable_api": callable_api,
            }
        )

    return final_jsons, identifiers, milestones


def process_multi_shipment_api_response(
    email_instance, all_responses, identifiers, milestones
):
    """
    Process API response for multi-shipment API call.

    Args:
        email_instance (object): Instance contain email_batch data.
        all_responses (list): List of all API responses.
        identifiers (list): Identifiers corresponding to each shipment.
        milestones (list): Milestone list to call timestamp API.

    Returns:
        all_passed (bool): Indicate all API calls were successful.
        is_retrying (bool): Indicate any API call is being retried.
        failed_api_call_count (int): Number of failed API call.
        confirmation_numbers (list): Confirmation numbers from successful API call.

    Process Details:
        - Loop through each response and process the data based on the status_code.
        - Update the 'shipment_status_url' for each shipment if 'statusURL' is found.
        - Track confirmation_numbers and handle retry condition based on the status_code.
        - Logs API response into the database.

    Notes:
        - If 'response_json' contain "fcmID" then update confirmation_number based on it.
        - If the 'product_code' is "FCMTR" in 'request_json' then update 'productCode' in 'response_json'.
        - is_retrying is True when status_code not 200 or 400.
    """
    confirmation_numbers = []
    failed_api_call_count = 0
    all_passed = False
    is_retrying = False
    status_urls = email_instance.shipment_status_url

    if not status_urls:
        status_urls = [None] * len(all_responses)

    for response_json, status_code, index, *extras in all_responses:
        if identifiers and index < len(identifiers):
            response_json["identifier"] = identifiers[index]
        try:
            if not status_urls[index]:
                status_url = response_json.get("statusURL", None)
                status_urls[index] = status_url
        except IndexError:
            print(traceback.print_exc())

        if status_code != 200:
            failed_api_call_count += 1

        confirmation_number = None

        if response_json.get("fcmID"):
            confirmation_number = response_json["fcmID"]
        else:
            confirmation_number = response_json.get("shipmentID")

        if confirmation_number:
            confirmation_numbers.append(confirmation_number)

            if index < len(milestones):
                milestones[index].update({"shipment_id": confirmation_number})

        if not is_retrying and status_code not in {200, 400}:
            is_retrying = True

        if not all_passed and status_code == 200:
            all_passed = True

        if email_instance.assembled_results:
            product_code = email_instance.assembled_results[0]["data"].get(
                "productCode"
            )

            if product_code == "FCMTR":
                response_json["productCode"] = product_code

        save_api_response_to_db(email_instance, index, status_code, response_json)
    email_instance.shipment_status_url = status_urls
    email_instance.save()

    return all_passed, is_retrying, failed_api_call_count, confirmation_numbers


def handle_multi_shipment_time_stamp_api_call(
    write_parent_batch_log,
    email_instance,
    milestones,
    is_retry_applicable,
):
    """
    Handle API call for multi-shipment timestamp by preparing payloads, executing concurrent requests and processing response.

    Args:
        write_parent_batch_log (Callable): Write logs for parent batch.
        email_instance (object): Instance contain email_batch data.
        milestones (list): Milestone list for Timestamp API call.
        is_retry_applicable (bool): Specifies whether a retry is applicable.

    Returns:
        failed_api_call_count (int): Indicates the number of failed API call.

    Process Details:
        - Prepare the payload for multi-shipment timestamp API call using 'prepare_multi_shipment_timestamp_api_payload'.
        - Execute concurrent API requests using 'ConcurrentAPIExecutor'.
        - Process API response to determine success and failure.
        - Log the response in timeline.

    Notes:
        - Number of concurrent workers and timeout is configurable via 'ConcurrentAPIExecutor'.
    """
    final_jsons = prepare_multi_shipment_timestamp_api_payload(
        email_instance, milestones
    )

    api_executor = ConcurrentAPIExecutor(max_workers=30, timeout=300)
    all_responses = api_executor.execute(final_jsons)

    failed_api_call_count = process_multi_shipment_timestamp_api_response(
        write_parent_batch_log,
        email_instance,
        all_responses,
        final_jsons,
        is_retry_applicable,
    )

    return failed_api_call_count


def prepare_multi_shipment_timestamp_api_payload(email_instance, milestones):
    """
    Prepare the payload for multi-shipment timestamp API call.

    Args:
        email_instance (object): Instance contain email_batch data.
        milestones (list): Milestone list to Call timestamp API.

    Returns:
        final_jsons (list): Contain request_data, response_json, status_code, callable_api and parent_index.

    Process Details:
        - Iterate through 'milestones' to build payloads for each sub item.
    """

    final_jsons = []
    api_responses = email_instance.api_response

    for index, item in enumerate(milestones):
        status_code = None
        milestone = item["milestone"]

        if not milestone:
            continue

        if isinstance(api_responses, list) and index < len(api_responses):
            api_response = api_responses[index]
            status_code = api_response.get("status_code")
            existing_timestamp_responses = api_response.get("timestamp_api_response")

        for idx, milestone_obj in enumerate(milestone):
            request_data = {
                "milestone": milestone_obj,
                "shipment_id": item.get("shipment_id"),
            }

            if not status_code or status_code != 200:
                final_jsons.append(
                    {
                        "request_data": request_data,
                        "parent_index": index,
                    }
                )
                continue

            response_content = ""
            timestamp_status_code = None

            callable_api = send_shipment_time_stamp

            if (
                isinstance(existing_timestamp_responses, list)
                and idx < len(existing_timestamp_responses)
                and existing_timestamp_responses[idx]
            ):
                response_content = existing_timestamp_responses[idx].get(
                    "response_content", ""
                )
                timestamp_status_code = existing_timestamp_responses[idx].get(
                    "status_code"
                )

            final_jsons.append(
                {
                    "request_data": request_data,
                    "response_json": response_content,
                    "status_code": timestamp_status_code,
                    "callable_api": callable_api,
                    "parent_index": index,
                }
            )

    return final_jsons


def process_multi_shipment_timestamp_api_response(
    write_parent_batch_log,
    email_instance,
    all_responses,
    final_jsons,
    is_retry_applicable,
):
    """
    Process API response for multi-shipment timestamp API call.

    Args:
        email_instance (object): Instance contain email_batch data.
        milestones (list): Milestone list to Call timestamp API.
        timestamp_retry_count (bool): Indicates the number of retry attempts.
        is_retry_applicable (bool): Specifies whether a retry is applicable.

    Returns:
        failed_api_call_count (int): Indicates the number of failed API call.

    Process Details:
        - Iterate through 'all_responses' to process for each sub item.
    """
    email_id = email_instance.id
    failed_api_call_count = 0

    api_responses = email_instance.api_response

    for api_response in api_responses:
        api_response["timestamp_api_response"] = []

    for response_content, status_code, index, parent_index in all_responses:
        if (
            not isinstance(api_responses, list)
            or not isinstance(parent_index, int)
            or parent_index >= len(api_responses)
        ):
            failed_api_call_count += 1
            continue

        api_response = api_responses[parent_index]
        request_data = {}

        if index < len(final_jsons):
            request_data = final_jsons[index].get("request_data", {})

        if response_content == {}:
            response_content = (
                "Skipped Timestamp API call as no corresponding shipment_id was found."
            )
        else:
            response_content = BeautifulSoup(response_content, "xml")
            response_content = str(response_content)

        api_response["timestamp_api_response"].append(
            {
                "status_code": status_code,
                "response_content": response_content,
                "milestone": request_data.get("milestone"),
                "shipment_id": request_data.get("shipment_id"),
            }
        )

        if status_code != 200:
            failed_api_call_count += 1

    email_instance.api_response = api_responses
    email_instance.save()

    if failed_api_call_count != len(all_responses):
        success_status = (
            "partially successful" if failed_api_call_count != 0 else "successful"
        )
        write_parent_batch_log(
            message=f"Time Stamp API call was {success_status} ({len(all_responses) - failed_api_call_count}/{len(all_responses)})",
            batch_id=email_id,
            remarks="",
            status="inprogress",
            action="display_paginated_json",
        )

    if failed_api_call_count:
        failed_status = (
            "partially failed"
            if failed_api_call_count != len(all_responses)
            else "failed"
        )
        retry_message = ". Attempting to retry" if is_retry_applicable else ""
        failed_message = f"Time Stamp API call was {failed_status}{retry_message} ({failed_api_call_count}/{len(all_responses)})"

        write_parent_batch_log(
            message=failed_message,
            batch_id=email_id,
            remarks="",
            status="warning",
            action="display_paginated_json",
        )

    return failed_api_call_count


def log_multi_shipment_api_response_in_timeline(
    write_parent_batch_log: Callable,
    message_prefix,
    email_instance,
    all_responses,
    failed_api_call_count,
    is_retrying,
):
    """
    Log the result of multi-shipment API call into the batch processing timeline.

    Args:
        write_parent_batch_log (Callable): Write logs for parent batch.
        message_prefix (str): Prefix message for logging.
        email_instance (object): Instance contain email_batch data.
        all_responses (list): List of all API responses.
        failed_api_call_count (int): Number of failed API call.
        is_retrying (bool): Indicate any API call is being retried.

    Returns:
        is_retrying (bool): Updated value that indicate any API call is being retried.

    Process Details:
        - Log the multi-shipment API call was successful, partially successful or failed.
        - If retry is needed, increments the retry count.

    Notes:
        - When 'failed_api_call_count', reset the retry flag and update the 'api_retry_count' in the email instance.
    """
    email_id = email_instance.id

    if len(all_responses) != failed_api_call_count:
        sub_message = "successful"
        if failed_api_call_count:
            sub_message = "partially successful"
        else:
            email_instance.api_retry_count = 0
            is_retrying = False

        write_parent_batch_log(
            message=f"{message_prefix} was {sub_message} ({len(all_responses) - failed_api_call_count}/{len(all_responses)})",
            batch_id=email_id,
            remarks="",
            status="inprogress",
            action="display_paginated_json",
        )

    if failed_api_call_count:
        sub_message = "failed"
        if len(all_responses) != failed_api_call_count:
            sub_message = "partially failed"

        message = f"{message_prefix} was {sub_message} ({failed_api_call_count}/{len(all_responses)})"

        if is_retrying and email_instance.api_retry_count < MAX_RETRY:
            email_instance.api_retry_count += 1
            message += f". Retrying in {RETRY_INTERVAL} seconds"
        else:
            email_instance.api_retry_count = 0
            is_retrying = False

        write_parent_batch_log(
            message=message,
            batch_id=email_id,
            remarks="",
            status="warning",
            action="display_paginated_json",
        )

    email_instance.save()

    return is_retrying


def clean_api_request_data(email_instance, request_type, request_data, send_time_stamp):
    """
    Clean and prepare the API request data by removing specific fields.

    Args:
        email_instance (object): Instance contain email-batch data.
        request_type (str): Type of the request.
        request_data (dict): Request data to be cleaned.
        send_time_stamp (bool): Flag to timestamp is required for processing.

    Returns:
        request_data (dict): Cleaned request data.
        milestone (str): Extracted milestone.
        case_id (str): Extracted case ID.
        identifier (str): Extracted identifier.

    Process Details:
        - For "shipment-create" and "shipment-update" request, remove 'batchid' and extract 'identifier' from the request data.
        - For "usacustoms" request, extract the case_id from email subject.

    Notes:
        - For "shipment-create" with timestamp, extracts the first milestone.
    """
    identifier = None
    milestone = []
    case_id = None

    if request_type in ["shipment-create", "shipment-update"]:
        if request_data.get("batchid"):
            request_data.pop("batchid")

        if request_data.get("identifier"):
            identifier = request_data.pop("identifier")

        if request_type == "shipment-create" and send_time_stamp:
            milestone = request_data.pop("milestone")

    if request_type == "usacustoms":
        case_id = email_instance.email_subject.split("_")[0]

    return request_data, milestone, case_id, identifier


def handle_project_wise_api_call(
    write_parent_batch_log: Callable,
    email_instance,
    request_type,
    request_data,
    api_response,
    case_id,
    is_retrying,
):
    """
    Handle API call based on project type and request type.

    Args:
        write_parent_batch_log (Callable): Function to log the batch operation.
        email_instance (object): Instance contain email-batch data.
        request_type (str): Type of the API request.
        request_data (dict): Payload for the API call.
        api_response (dict): Response from the previous API call.
        case_id (str): Case_id for certain requests.
        is_retrying (bool): Indicate the API call is retry.

    Returns:
        response_json (dict): Response JSON from the API call.
        status_code (int): API status code.
        is_retrying (bool): Updated retrying flag.

    Process Details:
        - Handle response for each request type based on necessary logic.
        - Retrie API call if applicable and updating retry flag as needed.
        - Save necessary shipment_status_URL for further processing.

    Notes:
        - Use helper function to send requests and process responses.
        - For "shipment-create" request type, 'shipment_status_url' is updated if present in the response.
        - For "shipment-create" request type, if 'response_json' contain "fcmID" then update confirmation_number based on it.
        - For "shipment-create" request type, if the 'product_code' is "FCMTR" in 'request_json' then update 'productCode' in 'response_json'.
        - For "shipment-update" handle response, status_code and packline_error from 'send_shipment_update_json'.
    """
    email_id = email_instance.id

    if email_instance.api_retry_count == 0:
        write_parent_batch_log(
            message=f"Calling {request_type} API to send payload",
            batch_id=email_id,
            remarks=json.dumps(request_data),
            status="inprogress",
            action="display_json",
        )

    if not api_response:
        save_analyzer_log_time(batch_id=email_id, field_name="each_api_call_s")

    if request_type == "shipment-create":
        if api_response and any(
            [
                api_response.get("response_json", {}).get(key)
                for key in ["shipmentID", "fcmID"]
            ]
        ):
            status_code = api_response["status_code"]
            response_json = api_response["response_json"]

            return response_json, status_code, is_retrying

        if email_instance.shipment_status_url:
            response_json = {"statusURL": email_instance.shipment_status_url[0]}
            response_json, status_code = get_shipment_status(response_json)
        else:
            response_json, status_code = send_shipment_create_json(request_data)

        if request_data.get("productCode") == "FCMTR":
            response_json["productCode"] = request_data["productCode"]

        if not email_instance.shipment_status_url and response_json.get("statusURL"):
            email_instance.shipment_status_url.append(response_json.get("statusURL"))
            email_instance.save()
    elif request_type == "shipment-update":
        shipment_id = email_instance.email_subject.split("_")[0]

        response_json, status_code, packline_error = send_shipment_update_json(
            request_data, shipment_id
        )

        if status_code in {200, 400} and packline_error:
            write_parent_batch_log(
                message=f"No Packline Data Found",
                batch_id=email_id,
                status="warning",
            )
    elif request_type == "dsc-wms":
        response_json, status_code = send_dsc_wms_json(request_data)
    elif request_type == "freight":
        response_json, status_code = send_freight_json(request_data)
    else:
        customs_job_id = None
        if request_type == "customs-entry":
            customs_job_id = email_instance.customs_number

        response_json, status_code = send_customs_json(
            request_data,
            request_type,
            customs_job_id=customs_job_id,
            case_id=case_id,
        )

    is_retrying = handle_retry(
        write_parent_batch_log,
        email_instance,
        status_code,
        request_type,
        response_json,
        is_retrying,
    )

    return response_json, status_code, is_retrying


def handle_retry(
    write_parent_batch_log: Callable,
    email_instance,
    status_code,
    request_type,
    response_json,
    is_retrying,
):
    """
    Handle API retry logic based on the status_code and MAX_RETRY limit.

    Args:
        write_parent_batch_log (Callable): Function to log the batch operation.
        email_instance (object): Instance contain email-batch data.
        status_code (int): API status code.
        request_type (str): Type of the API request.
        response_json (dict): JSON response from API call.
        email_id (str): email_id of the email batch.
        is_retrying (bool): Indicate the API call is retry.

    Returns:
        is_retrying (bool): Updated retrying flag.

    Process Details:
        - Check the retry limit 'MAX_RETRY' has been reached.
        - Log retry attempt if the status code is not 200 or 400.

    Notes:
        - Set the 'is_retrying' flag to True when retrying is needed.
    """
    email_id = email_instance.id

    if email_instance.api_retry_count < MAX_RETRY and status_code not in {
        200,
        400,
    }:
        write_parent_batch_log(
            message=f"{request_type.title()} API call was failed with status {status_code}. Retrying in {RETRY_INTERVAL} seconds",
            batch_id=email_id,
            status="warning",
            remarks=json.dumps(response_json),
            action="display_json",
        )
        is_retrying = True

    return is_retrying


def log_api_response_in_timeline(
    write_parent_batch_log: Callable,
    email_instance,
    is_retrying,
    api_response,
    status_code,
    request_type,
    index,
    result,
    response_json,
):
    """
    Log the API response in the timeline and handle retry logic.

    Args:
        write_parent_batch_log (Callable): Function to log the batch operation.
        email_instance (object): Instance contain email-batch data.
        is_retrying (bool): Indicate the API call is retry.
        api_response (dict): API response data.
        status_code (int): API status code.
        request_type (str): Type of the API request.
        index (int): Index for logging the response.
        result (str): Result of the API call.
        response_json (dict): JSON response from the API call.

    Returns:
        all_passed (bool): Indicate all API calls were successful.
        is_breakable (bool): Flag to the process should break.

    Process Details:
        - Log the status of the API call based on the response and status_code.
        - Save failed API responses to the database.
        - Reset retry count if the status code is 200.
        - Break the process if the status code is not 200.

    Notes:
        - Save failed API responses to the database.
    """
    all_passed = True
    is_breakable = False

    if is_retrying or (api_response and api_response["status_code"] == 200):
        return all_passed, is_breakable

    email_id = email_instance.id

    if status_code == 200:
        email_instance.api_retry_count = 0
        email_instance.save()

        api_status = "successful"
        status = "inprogress"
        message = f"{request_type.title()} API call was {api_status}"
    else:
        save_api_response_to_db(
            email_instance, index, status_code, response_json, result
        )
        api_status = "failed"
        all_passed = False
        status = "warning"
        message = f"{request_type.title()} API call was {api_status} with status {status_code}"

    write_parent_batch_log(
        message=message,
        batch_id=email_id,
        remarks=json.dumps(response_json),
        status=status,
        action="display_json",
    )

    if status_code != 200:
        is_breakable = True

    return all_passed, is_breakable


def update_confirmation_numbers(
    email_instance,
    status_code,
    request_type,
    request_data,
    response_json,
    case_id,
    result,
    confirmation_numbers,
):
    """
    Update and append confirmation_number based on the API response.

    Args:
        email_instance (object): Instance contain email-batch data.
        status_code (int): API status code.
        request_type (str): Type of the API request.
        request_data (dict): Data sent in the API request.
        response_json (dict): JSON response from the API call.
        case_id (str): case_id extracted from the email.
        result (str): Result of the API call.
        confirmation_numbers (list): List of confirmation numbers to be updated.

    Returns:
        confirmation_numbers (list): Updated list of confirmation numbers.

    Process Details:
        - Verify the API response was successful.
        - Determine the confirmation_number based on the request type.
        - Update the confirmation_number for the related batches.
        - Append the confirmation_number to the list.

    Notes:
        - Each request type use specific fields from the response to extract the confirmation_number.
        - For "dsc-wms" it extract the 'deliverynoteNo'.
        - For "shipment-create" and "shipment-update," it prioritize 'fcmID' over 'shipmentID'.
        - For "commercial-invoice" it process the detail string to extract the confirmation number.
        - For "booking", "customs-entry", "usacustoms" and "freight" it use respective identifier.
    """
    if status_code != 200:
        return confirmation_numbers

    if request_type == "dsc-wms":
        confirmation_number = request_data["deliverynoteNo"]
    elif request_type in ["shipment-create", "shipment-update"]:
        if response_json.get("fcmID"):
            confirmation_number = response_json["fcmID"]
        else:
            confirmation_number = response_json["shipmentID"]
    elif request_type == "commercial-invoice":
        confirmation_number = (
            response_json["detail"]
            .replace("Commercial Invoice ", "")
            .replace(" created successfully", "")
        )
        if " " in confirmation_number:
            confirmation_number = ""

    elif request_type == "booking":
        confirmation_number = response_json["customsJobNumber"]
    elif request_type == "customs-entry":
        confirmation_number = email_instance.customs_number
    elif request_type == "usacustoms":
        confirmation_number = case_id
    elif request_type == "freight":
        confirmation_number = response_json["shipment"]["id"]

    Batch.objects.filter(id__in=result["batches"]).update(
        confirmation_number=confirmation_number
    )

    confirmation_numbers.append(confirmation_number)

    return confirmation_numbers


def save_api_response_to_db(
    email_instance, index, status_code, response_json, result=None
):
    """
    Save API response to database

    Args:
        email_instance (object): Instance contain email-batch data.
        index (int): Index where to store the response in the email instance.
        status_code (int): API status code.
        response_json (dict): JSON response from the API call.
        result (dict): Update with the API response.

    Process Details:
        - Construct api_response dictionary with status_code and response_json.
        - Update 'result' dictionary with the api_response.
        - If the email instance already contain response at the given index then update it.
        - If the index exceeds the current list size, it appends api_response to the list.
        - Save the updated email instance.

    Notes:
        - Ensure response is properly stored.
    """
    api_response = {
        "status_code": status_code,
        "response_json": response_json,
    }

    if result:
        result["api_response"] = api_response

    if len(email_instance.api_response) > index:
        email_instance.api_response[index].update(api_response)
    else:
        email_instance.api_response.append(api_response)

    if result:
        email_instance.save()


def handle_time_stamp_api_call(
    write_parent_batch_log: Callable,
    email_instance,
    response_json,
    milestone,
    all_passed,
    is_retrying,
    status_code,
    send_time_stamp,
    request_type,
):
    """
    Handle time stamp for API call

    Args:
        write_parent_batch_log (Callable): Function to log the batch details.
        email_instance (object): Instance contain email-batch data.
        response_json (dict): JSON response from API call.
        milestone (str): Milestone data required for the timestamp API.
        all_passed (bool): Indicate all operation succeeded or not.
        is_retrying (bool): Flag for retry is in progress.
        status_code (int): API status code.
        send_time_stamp (bool): Flag to timestamp call is required.
        request_type (str): The type of the API request.

    Returns:
        all_passed (bool): Updated status for overall success.
        is_retrying (bool): Updated retry status.

    Process Details:
        - Verify the condition to proceed with the time stamp API call.
        - Extract the shipment_id from API response.
        - Make the time_stamp_API_call and handle retry if the call fail.
        - Update the email instance and log the api_response.

    Notes:
        - The time stamp API is only triggered for successful "shipment-create" requests.
    """
    if not (
        status_code == 200 and send_time_stamp and request_type == "shipment-create"
    ):
        return all_passed, is_retrying

    if response_json.get("fcmID"):
        shipment_id = response_json["fcmID"]
    else:
        shipment_id = response_json["shipmentID"]

    email_id = email_instance.id

    api_responses = email_instance.api_response
    timestamp_api_responses = [None] * len(milestone)

    if (
        isinstance(api_responses, list)
        and len(api_responses) == 1
        and api_responses[0].get("timestamp_api_response")
    ):
        existing_timestamp_api_response = api_responses[0].get("timestamp_api_response")
        if isinstance(existing_timestamp_api_response, list):
            for index, item in enumerate(existing_timestamp_api_response):
                if index < len(milestone):
                    timestamp_api_responses[index] = item

    for index, milestone_dict in enumerate(milestone):
        if timestamp_api_responses[index]:
            existing_status_code = timestamp_api_responses[index].get("status_code")

            if existing_status_code and existing_status_code == 200:
                continue

        response_content, response_status_code = send_shipment_time_stamp(
            shipment_id, milestone_dict
        )

        response_content = BeautifulSoup(response_content, "html.parser")

        json_content = {
            "status_code": response_status_code,
            "response_content": str(response_content),
            "milestone": milestone_dict,
            "shipment_id": shipment_id,
        }

        timestamp_api_responses[index] = json_content

        is_retrying = handle_retry(
            write_parent_batch_log,
            email_instance,
            response_status_code,
            "Time Stamp",
            json_content,
            is_retrying,
        )

        if is_retrying or response_status_code != 200:
            all_passed = False
            break

        write_parent_batch_log(
            message="Time Stamp API call was successful",
            batch_id=email_id,
            status="inprogress",
            remarks=json.dumps(json_content, indent=4),
            action="display_json",
        )

    if isinstance(api_responses, list) and len(api_responses) == 1:
        api_responses[0]["timestamp_api_response"] = timestamp_api_responses

    if not is_retrying:
        email_instance.api_retry_count = 0

    email_instance.api_response = api_responses
    email_instance.save()

    return all_passed, is_retrying


def handle_doc_upload(
    write_parent_batch_log: Callable, email_instance, matched_profile_instance, fcm_id
):
    """
    Handle document upload for multi-shipment and other API response.

    Args:
        write_parent_batch_log (Callable): Function to log batch details.
        email_instance (object): Instance contain email_batch data.
        matched_profile_instance (object): Instance contain profile data.

    Returns:
        edm_upload_error (bool): Indicate if error occurred during edm_upload.
        identifiers (list): Identifiers for multi-shipment.
        shipment_id (list): shipment_id need to be processed.
        housebill_number (list): housebill_number need to be processed.
        is_retrying (bool): Indicate retry operation is in progress.
        failed_doc_upload_count (int): Number of failed document upload.

    Process Details:
        - Prepare necessary variables from the email_instance and matched_profile_instance.
        - Call 'handle_multi_shipment_doc_upload' to process multi-shipment document upload.
        - Update variables such as shipment_id, housebill_number, retry and error.
        - For other, iterate through 'assembled_results' to update API responses.
        - Extract shipment_id, housebill_number, and customs_clearance_numbers from API response.
        - Skip certain document upload based on criteria.
        - Upload files for each result using 'file_wise_doc_upload' and handle retry logic.
        - If no error or retries are pending then upload additional documents using 'handle_additional_doc_upload'.
        - Return the status of the EDM upload, shipment details, and retry.

    Notes:
        - Update the API response and perform additional EDM upload if required.
    """
    email_id = email_instance.id
    profile_name = matched_profile_instance.name
    project = matched_profile_instance.project
    multi_shipment = matched_profile_instance.multi_shipment
    filing_country = profile_name[0:2]
    edm_upload_error = False
    case_id = None
    shipment_id = []
    housebill_number = []
    api_response = email_instance.api_response
    is_retrying = False
    assembled_results = [*email_instance.assembled_results]
    customs_clearance_numbers = []
    edm_upload_error = False
    failed_doc_upload_count = 0
    identifiers = []
    if multi_shipment:
        (
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            edm_upload_error,
            failed_doc_upload_count,
        ) = handle_multi_shipment_doc_upload(
            write_parent_batch_log, email_instance, project, filing_country
        )
    else:
        # Update api response
        for index, item in enumerate(assembled_results):
            if item.get("api_response") is None:
                item["api_response"] = api_response[index]

        break_outer_loop = False

        # After Each CIV and B docs are sent, upload attachments to CW1 edoc
        for index, item in enumerate(assembled_results):
            if break_outer_loop:
                break

            request_type = item["type"]
            response_json = item["api_response"]["response_json"]

            if response_json.get("shipmentID"):
                shipment_id.append(response_json.get("shipmentID"))

            if response_json.get("housebillNumber"):
                housebill_number.append(response_json.get("housebillNumber"))

            # Extracting clearence number
            customs_clearance_numbers, customs_clearance_number, is_skippable = (
                update_customs_clearance_numbers(
                    email_instance,
                    customs_clearance_numbers,
                    request_type,
                    response_json,
                )
            )

            # CW1 edoc uploads for commercial-invoice (CIV) and dsc-wms batch will be skipped
            if is_skippable:
                continue

            files_list = get_file_list(item, index, project, api_response=api_response)

            save_analyzer_log_time(batch_id=email_id, field_name="document_upload_s")

            edm_upload_error, is_retrying, break_outer_loop = file_wise_doc_upload(
                write_parent_batch_log,
                email_instance,
                files_list,
                api_response,
                index,
                filing_country,
                request_type,
                customs_clearance_number,
                matched_profile_instance,
            )

    # Upload additional attachments to CW1 edoc
    if not is_retrying and not edm_upload_error:
        edm_upload_error, is_retrying = handle_additional_doc_upload(
            write_parent_batch_log,
            email_instance,
            matched_profile_instance,
            project,
            filing_country,
            case_id,
            customs_clearance_numbers,
            fcm_id,
        )

    return (
        edm_upload_error,
        identifiers,
        shipment_id,
        housebill_number,
        is_retrying,
        failed_doc_upload_count,
    )


def handle_multi_shipment_doc_upload(
    write_parent_batch_log: Callable, email_instance, project, filing_country
):
    """
    Handle document upload process for multi-shipment profile.

    Args:
        write_parent_batch_log (Callable): Function to log the batch process details.
        email_instance (object): Instance contain email_batch data.
        project (str): Associated project for the batch.
        filing_country (str): Country associated with the filing process.

    Returns:
        identifiers (list): Identifiers for each shipment in the batch.
        shipment_id (list): shipment_id processed in the batch.
        housebill_number (list): housebill_number processed in the batch.
        is_retrying (bool): Indicate retry operation is in progress.
        edm_upload_error (bool): Indicate if error occurred during edm_upload.
        failed_doc_upload_count (int): Number of failed document upload.

    Process Details:
        - Prepare multi-shipment document upload payload using 'prepare_multi_shipment_doc_upload_payload'.
        - Execute API calls concurrently for document upload using 'ConcurrentAPIExecutor'.
        - Process api_response using 'process_multi_shipment_doc_upload_response'.

    Notes:
        - Log the status of the api_response in the batch timeline.
        - Determine if retry logic should be triggered based on failed API call.
    """
    is_retrying = False
    edm_upload_error = False
    failed_api_call_count = 0

    final_jsons, identifiers, shipment_id, housebill_number, fcm_id = (
        prepare_multi_shipment_doc_upload_payload(
            email_instance, project, filing_country
        )
    )

    # Skip document upload if all are "Processing Document No Upload"
    if check_processing_document_no_upload(final_jsons):
        return (
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            edm_upload_error,
            failed_api_call_count,
        )

    api_executor = ConcurrentAPIExecutor(max_workers=30, timeout=300)
    all_responses = api_executor.execute(final_jsons)

    is_retrying, failed_api_call_count = process_multi_shipment_doc_upload_response(
        email_instance, all_responses
    )

    message_prefix = "Uploading document to CW1 edoc"
    is_retrying = log_multi_shipment_api_response_in_timeline(
        write_parent_batch_log,
        message_prefix,
        email_instance,
        all_responses,
        failed_api_call_count,
        is_retrying,
    )

    edm_upload_error = failed_api_call_count == len(all_responses)

    return (
        identifiers,
        shipment_id,
        housebill_number,
        is_retrying,
        edm_upload_error,
        failed_api_call_count,
    )


def prepare_multi_shipment_doc_upload_payload(email_instance, project, filing_country):
    """
    Prepare the payload for multi-shipment document upload.

    Args:
        email_instance (object): Instance contain email_batch data.
        project (str): Associated project for the batch.
        filing_country (str): Country associated with the filing process.

    Returns:
        final_jsons (list): Prepared payload for API calls.
        identifiers (list): Identifiers for each shipment in the batch.
        shipment_id (list): Shipment IDs extracted from the responses.
        housebill_number (list): Housebill numbers extracted from the responses.

    Process Details:
        - Iterate through 'assembled_results' to extract relevant data.
        - Validate shipment_id and associated details are present.
        - Skip processing for specific document type.

    Notes:
        - Construct request payloads for valid shipment, including document and clearance details.
    """
    customs_clearance_number = None
    final_jsons = []
    identifiers = []
    failed_identifiers = []
    shipment_id = []
    fcm_id = []
    housebill_number = []
    api_responses = email_instance.api_response

    for index, item in enumerate(email_instance.assembled_results):
        uploaded_doc_response_json = None
        uploaded_doc_status_code = None

        if isinstance(api_responses, list) and index < len(api_responses):
            response_json = api_responses[index]["response_json"]

            if not response_json.get("shipmentID") and not response_json.get("fcmID"):
                failed_identifiers.append(response_json.get("identifier"))
                final_jsons.append(None)
                continue

            uploaded_doc_response_json = api_responses[index].get(
                "uploaded_doc_response_json"
            )
            uploaded_doc_status_code = api_responses[index].get(
                "uploaded_doc_status_code"
            )
            if response_json.get("fcmID"):
                customs_clearance_number = response_json["fcmID"]
                fcm_id.append(response_json["fcmID"])
            else:
                customs_clearance_number = response_json["shipmentID"]
                shipment_id.append(response_json["shipmentID"])
            identifiers.append(response_json.get("identifier"))
            housebill_number.append(response_json.get("housebillNumber"))
        else:
            failed_identifiers.append(response_json.get("identifier"))
            final_jsons.append(None)
            continue

        files_list = get_file_list(item, index, project)

        if not files_list:
            continue

        file_item = files_list[0]

        doc_type = file_item["matched_profile_doc__doc_type"]

        if doc_type == "Processing Document No Upload":
            uploaded_doc_response_json = {"remarks": "Processing Document No Upload"}
            uploaded_doc_status_code = 200

        request_data = {
            "file_path": file_item["path"],
            "doc_number": file_item["doc_number"],
        }
        if not response_json.get("fcmID"):
            request_data.update(
                {
                    "customs_clearance_number": customs_clearance_number,
                    "filing_country": filing_country,
                }
            )
        else:
            request_data.update(
                {
                    "fcmID": customs_clearance_number,
                }
            )

        api_to_call = upload_document_to_edm
        if response_json.get("fcmID"):
            api_to_call = upload_fcm_document_to_edm

        final_jsons.append(
            {
                "request_data": request_data,
                "response_json": uploaded_doc_response_json,
                "status_code": uploaded_doc_status_code,
                "callable_api": api_to_call,
            }
        )

    identifiers = identifiers + failed_identifiers

    return final_jsons, identifiers, shipment_id, housebill_number, fcm_id


def check_processing_document_no_upload(final_jsons=None):
    empty_json_count = 0
    no_doc_upload_json_count = 0

    for final_json in final_jsons:
        response_json = (final_json or {}).get("response_json", {})

        if not response_json:
            empty_json_count += 1
        elif response_json.get("remarks") == "Processing Document No Upload":
            no_doc_upload_json_count += 1

    if no_doc_upload_json_count != 0 and len(final_jsons) == (
        no_doc_upload_json_count + empty_json_count
    ):
        return True

    return False


def process_multi_shipment_doc_upload_response(email_instance, all_responses):
    """
    Process the API response for multi-shipment document upload.

    Args:
        email_instance (object): Instance contain email_batch data.
        all_responses (list): Responses from the document upload API calls.

    Returns:
        is_retrying (bool): Indicate if retry logic is triggered.
        failed_api_call_count (int): Number of failed API calls during the process.

    Process Details:
        - Iterate through the api_responses to evaluate success and failure.
        - Update the API response data in 'email_instance' with status_code and response_json.

    Notes:
        - Retry logic should be triggered for failed or incomplete responses.
    """
    api_responses = email_instance.api_response
    is_retrying = False
    failed_api_call_count = 0

    for response_json, status_code, index, *extras in all_responses:
        if status_code != 200:
            failed_api_call_count += 1

        if not is_retrying and status_code not in {None, 200, 400}:
            is_retrying = True

        if response_json.get("customs_clearance_number"):
            response_json["shipmentID"] = response_json["customs_clearance_number"]

            del response_json["customs_clearance_number"]

        if not status_code and not response_json:
            response_json = {
                "error": "Document upload was skipped as the corresponding JSON upload API failed"
            }

        api_responses[index]["uploaded_doc_response_json"] = response_json
        api_responses[index]["uploaded_doc_status_code"] = status_code
    email_instance.save()

    return is_retrying, failed_api_call_count


def get_doc_types_data(project):
    """Retrieve document type data for specified project."""
    def_settings = get_merged_definition_settings(project)
    doc_type_items = def_settings["options"]["options-meta-root-type"]["items"]

    doc_types_data = {}

    for i in doc_type_items:
        doc_types_data[i["docType"]] = i["docNumber"]

    return doc_types_data


def update_customs_clearance_numbers(
    email_instance, customs_clearance_numbers, request_type, response_json
):
    """
    Update customs clearance numbers based on the request type and API response.

    Args:
        email_instance (object): Instance contain email_batch data.
        customs_clearance_numbers (list): Customs clearance numbers to be updated.
        request_type (str): The type of API request.
        response_json (dict): JSON response from API call.

    Returns:
        customs_clearance_numbers (list): Updated list of customs clearance numbers.
        customs_clearance_number (str): Current customs clearance number extracted from the response.
        is_skippable (bool): Flag to the request type should be skipped for further processing.

    Process Details:
        - Check the 'request_type' to determine the source of the customs clearance number.
        - Extract the clearance number from the 'response_json' or 'email_instance' based on the request type.
        - Append the extracted clearance number with the 'customs_clearance_numbers'.

    Notes:
        - Set 'is_skippable' to True for request type that need to bypass further processing.
    """
    customs_clearance_number = None
    is_skippable = False

    if request_type in ["shipment-create", "shipment-update"]:
        if response_json.get("fcmID"):
            customs_clearance_number = response_json["fcmID"]
        else:
            customs_clearance_number = response_json["shipmentID"]
    elif request_type in ["commercial-invoice", "dsc-wms"]:
        # CW1 edoc uploads for commercial-invoice (CIV) and dsc-wms batch will be skipped
        is_skippable = True
    elif request_type == "booking":
        customs_clearance_number = response_json["customsJobNumber"]
    elif request_type == "customs-entry":
        customs_clearance_number = email_instance.customs_number
    elif request_type == "freight":
        customs_clearance_number = response_json["shipment"]["id"]
    else:
        customs_clearance_number = None

    if customs_clearance_number:
        customs_clearance_numbers.append(customs_clearance_number)

    return customs_clearance_numbers, customs_clearance_number, is_skippable


def get_file_list(item, index, project, api_response=None):
    """
    Retrieve list of files associated with the given item.

    Args:
        item (dict): Contain batch-related data.
        index (int): Index of the current item in the batch.
        project (str): Associated project for the batch.
        api_response (list): api_response to update with file upload name.

    Returns:
        files_list (list): contain file details such as name, path, type, and doc_number.

    Process Details:
        - Fetche 'doc_number' value based on 'doc_type' from project definition.
        - Query 'EmailParsedDocument' model for files linked to the provided batch_id.
        - Update 'uploaded_doc_names' field in the 'api_response'.

    Notes:
        - Map 'doc_type' to 'doc_number' using project settings.
    """
    # Read definition settings to get docNumber from docType
    doc_types_data = get_doc_types_data(project)

    batches = item["batches"]

    if not isinstance(batches, list):
        batches = [batches]

    files_list = list(
        EmailParsedDocument.objects.filter(batch_id__in=batches).values(
            "name", "path", "type", "matched_profile_doc__doc_type"
        )
    )

    if api_response and not api_response[index].get("uploaded_doc_names"):
        api_response[index]["uploaded_doc_names"] = [None] * len(files_list)

    for f in files_list:
        doc_type = f["matched_profile_doc__doc_type"]
        doc_number = doc_types_data.get(doc_type, None)
        try:
            doc_number = int(doc_number)
        except:
            pass
        f["doc_number"] = doc_number

    return files_list


def file_wise_doc_upload(
    write_parent_batch_log: Callable,
    email_instance,
    files_list,
    api_response,
    index,
    filing_country,
    request_type,
    customs_clearance_number,
    matched_profile_instance,
):
    """
    Handle file by file document upload.

    Args:
        write_parent_batch_log (Callable): Function to log messages for the parent batch.
        email_instance (object): Instance contain email_batch data.
        files_list (list): Files to be uploaded
        api_response (list): api_response to be updated.
        index (int): Current index of batch.
        filing_country (str): Country associated with the filing.
        request_type (str): Type of request.
        customs_clearance_number (str): Customs clearance number for shipment.

    Returns:
        edm_upload_error (bool): Indicate for error during document upload.
        is_retrying (bool): System should retry the upload or not.
        break_outer_loop (bool): Flag to break processing loop.

    Process Details:
        - Iterate over 'files_list' and skip files that don't require upload.
        - Validate file status and avoid duplicate upload based on 'uploaded_doc_names'.
        - Extract document upload information using 'get_doc_upload_info'.
        - Upload files using 'upload_document_to_edm' or 'upload_document_to_usa'.

    Notes:
        - Log processing times and handle retries for failed upload.
        - Update 'api_response' and write log for error encountered during the process.
    """
    email_id = email_instance.id
    edm_upload_error = False
    is_retrying = False
    break_outer_loop = False

    for idx, file_item in enumerate(files_list):
        file_name = file_item["name"]
        doc_type = file_item["matched_profile_doc__doc_type"]

        if doc_type == "Processing Document No Upload":
            continue

        try:
            if api_response[index]["uploaded_doc_names"][idx] == file_name:
                continue
        except:
            pass

        try:
            info, case_id, file_path, doc_number = get_doc_upload_info(
                file_item,
                filing_country,
                request_type,
                customs_clearance_number,
                email_instance,
                matched_profile_instance,
            )

            save_analyzer_log_time(
                batch_id=email_id, field_name="each_document_upload_s"
            )
            if request_type == "usacustoms":
                status_code = upload_document_to_usa(file_path, doc_number, case_id)
            else:
                if api_response[index].get("response_json", {}).get("fcmID"):
                    status_code = upload_fcm_document_to_edm(
                        file_path, doc_number, customs_clearance_number
                    )

                    info["fcmID"] = customs_clearance_number
                    if "shipmentID" in info:
                        del info["shipmentID"]
                else:
                    status_code = upload_document_to_edm(
                        file_path,
                        doc_number,
                        customs_clearance_number,
                        filing_country,
                    )
            save_analyzer_log_time(
                batch_id=email_id, field_name="each_document_upload_e"
            )

            is_retrying, break_loop = handle_doc_upload_retry(
                write_parent_batch_log, email_instance, status_code, info
            )

            if break_loop:
                break_outer_loop = True
                break

            edm_upload_error = post_doc_upload_process(
                write_parent_batch_log,
                email_instance,
                status_code,
                file_name,
                info,
                index,
                additional_doc_item=None,
                api_response=api_response,
                idx=idx,
            )

            save_analyzer_log_time(batch_id=email_id, field_name="document_upload_e")
        except Exception as error:
            edm_upload_error = True
            trace = traceback.format_exc()
            message = (
                f"Error occured while uploading document '{file_name}' to CW1 edoc."
            )
            remarks = {
                "message": f"The following error occured in 'test_batch_p10' function : '{str(error.args[0])}' ",
                "traceback": trace,
            }
            error = traceback.format_exc()

            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="failed",
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
            )

    return edm_upload_error, is_retrying, break_outer_loop


def get_doc_upload_info(
    file_item,
    filing_country,
    request_type,
    customs_clearance_number,
    email_instance,
    matched_profile_instance,
):
    """
    Generate document upload information.

    Args:
        file_item (dict): This item holds info about the doc to be uploaded.
        filing_country (str): Country associated with the filing.
        request_type (str): Type of request.
        customs_clearance_number (str): Customs clearance number for shipment.
        email_instance (object): Instance contain email_batch data.
        matched_profile_instance (object): Instance contain profile data.

    Returns:
        info (dict): Contain upload metadata.
        case_id (str): 'case_id' extracted from the email subject.
        file_path (str): 'file_path' extracted from the file item.
        case_id (str): 'case_id' extracted from the file item.

    Process Details:
        - Construct 'info' dictionary with essential upload details.
        - Update 'info' based on the 'request_type'.

    Notes:
        - For shipment-create and shipment-update requests, add 'shipmentID'.
        - For "usacustoms", extract and add 'case_id' from email subject.
        - For other request include 'customs_clearance_number'.
    """
    profile_name = matched_profile_instance.name
    project = matched_profile_instance.project
    doc_type = file_item["matched_profile_doc__doc_type"]
    file_path = file_item["path"]
    doc_number = file_item["doc_number"]
    case_id = None

    if project == "CustomsEntryUpdate" and doc_type == "Bill Of Entry":
        doc_number = 711 if "IMPORT" in profile_name else 710

    info = {
        "file_path": file_path,
        "doc_number": doc_number,
        "filing_country": filing_country,
    }

    if request_type in ["shipment-create", "shipment-update"]:
        info["shipmentID"] = customs_clearance_number
    elif request_type == "usacustoms":
        case_id = email_instance.email_subject.split("_")[0]
        info["case_id"] = case_id
    else:
        info["customs_clearance_number"] = customs_clearance_number

    return info, case_id, file_path, doc_number


def handle_doc_upload_retry(
    write_parent_batch_log, email_instance, status_code, info, additional_doc=False
):
    """
    Handle retry logic for failed document upload.

    Args:
        write_parent_batch_log (Callable): Function to log messages for the parent batch.
        email_instance (object): Instance contain email_batch data.
        status_code (int): API status code.
        info (dict): Data related to the document being uploaded.
        additional_doc (bool): Flag to the additional document present or not.

    Returns:
        is_retrying (bool): Indicate the upload should be retried.
        break_loop (bool): Flag to break the loop.

    Process Details:
        - Check the 'status_code' not in 200 and 400.
        - Construct retry message.
        - Log retry information via 'write_parent_batch_log' and mark the retry flag.

    Notes:
        - 'api_retry_count' has not reached to 'MAX_RETRY'.
    """
    email_id = email_instance.id
    is_retrying = False
    break_loop = False

    if email_instance.api_retry_count < MAX_RETRY and status_code not in {
        200,
        400,
    }:
        save_analyzer_log_time(
            batch_id=email_id, field_name="retry_document_upload_time"
        )

        custom_message = "additional document" if additional_doc else "document"
        message = f"Uploading {custom_message} API failed with status code {status_code}. Retrying in {RETRY_INTERVAL} seconds."

        write_parent_batch_log(
            batch_id=email_id,
            status="warning",
            message=message,
            remarks=json.dumps(info),
            action="display_json",
        )

        email_instance.api_retry_count += 1
        is_retrying = True
        break_loop = True

    return is_retrying, break_loop


def post_doc_upload_process(
    write_parent_batch_log: Callable,
    email_instance,
    status_code,
    file_name,
    info,
    index,
    additional_doc_item=None,
    api_response=None,
    idx=None,
):
    """
    Process the result of document upload and log.

    Args:
        write_parent_batch_log (Callable): Function to log messages for the parent batch.
        email_instance (object): Instance contain email_batch data.
        status_code (int): Document upload API status code.
        file_name (str): Name of the file being uploaded.
        info (dict): Data related to the document being uploaded.
        index (int): Index of the document in the upload list.
        additional_doc_item (dict): Data of the additional document.
        api_response (list): Response for document uploads.
        idx (int): Index of the file in the API response.

    Returns:
        edm_upload_error (bool): Indicate the error during the upload process.

    Process Details:
        - Check 'status_code' is 200, reset 'api_retry_count'.
        - Update 'additional_doc_item' and 'api_response'.
        - Save the updated 'email_instance'.
        - Construct log message for success or failure.
        - Log the upload result via 'write_parent_batch_log'.

    Notes:
        - For other status_code, log the failure and set 'edm_upload_error' is True.
    """
    email_id = email_instance.id
    edm_upload_error = False

    if status_code == 200:
        email_instance.api_retry_count = 0

        # Applicable only for additional documents
        if additional_doc_item:
            additional_doc_item["uploaded"] = True
            email_instance.additional_docs_to_upload[index] = additional_doc_item

        # Applicable only for normal documents
        if api_response and idx is not None:
            api_response[index]["uploaded_doc_names"][idx] = file_name

        email_instance.save()

        api_status = "successful"
        status = "inprogress"
    else:
        api_status = "failed"
        status = "warning"
        edm_upload_error = True

    custom_message = "additional document" if additional_doc_item else "document"
    message = f"Uploading {custom_message} '{file_name}' to CW1 edoc {api_status} with status code {status_code}"

    write_parent_batch_log(
        message=message,
        batch_id=email_id,
        remarks=json.dumps(info),
        status=status,
        action="display_json",
    )

    return edm_upload_error


def handle_additional_doc_upload(
    write_parent_batch_log: Callable,
    email_instance,
    matched_profile_instance,
    project,
    filing_country,
    case_id,
    customs_clearance_numbers,
    fcm_id,
):
    """
    Handle the upload of additional documents and manage retries.

    Args:
        write_parent_batch_log (Callable): Function to log messages for the parent batch.
        email_instance (object): Instance contain email_batch data.
        project (str): Project name.
        filing_country (str): Country of filing for the document.
        case_id (str): case_id for "USACustoms" project.
        customs_clearance_numbers (list): Customs clearance numbers.

    Returns:
        edm_upload_error (bool): Indicate the error during the upload process.
        is_retrying (bool): Indicate the upload process should retry.

    Process Details:
        - Retrieve document type and verify if a document number exists.
        - Iterate through the additional documents.
        - Check the document has already been uploaded.
        - Construct 'info' with document details.
        - Upload the document using 'upload_document_to_usa' or 'upload_document_to_edm'.
        - Handle retries for failed upload using 'handle_doc_upload_retry'.
        - Call 'post_doc_upload_process' to finalize the upload process.

    Notes:
        - Skip processing if no additional documents need to be uploaded.
    """
    email_id = email_instance.id
    edm_upload_error = False
    is_retrying = False

    if len(email_instance.additional_docs_to_upload) == 0:
        return edm_upload_error, is_retrying

    # If it’s a multi-shipment, skip uploading additional documents.
    if matched_profile_instance.multi_shipment:
        remarks = [i["name"] for i in email_instance.additional_docs_to_upload]

        write_parent_batch_log(
            message="Uploading of additional documents has been skipped",
            batch_id=email_id,
            status="warning",
            action="display_json",
            remarks=json.dumps(remarks, indent=4),
        )
        return edm_upload_error, is_retrying

    # Nayem - Refactor this check into a separate function.
    document_type = get_additional_doc_type(project)

    doc_types_data = get_doc_types_data(project)
    doc_number = doc_types_data.get(document_type)

    if not doc_number:
        edm_upload_error = True

        write_parent_batch_log(
            batch_id=email_id,
            status="warning",
            message=f"Uploading additional document failed due to no doc number found in the definition",
        )

        return edm_upload_error, is_retrying

    doc_number = int(doc_number)

    for index, item in enumerate(email_instance.additional_docs_to_upload):
        if item["uploaded"]:
            continue

        file_name = item["name"]
        file_path = item["path"]
        info = {
            "file_path": file_path,
            "doc_number": doc_number,
            "filing_country": filing_country,
        }

        if project in ["ShipmentCreate", "ShipmentUpdate"]:
            if fcm_id:
                info["fcmID"] = ", ".join(customs_clearance_numbers)
            else:
                info["shipmentID"] = ", ".join(customs_clearance_numbers)
        elif project == "USACustoms":
            info["case_id"] = case_id
        else:
            info["customs_clearance_number"] = ", ".join(customs_clearance_numbers)

        if project == "USACustoms":
            status_code = upload_document_to_usa(file_path, doc_number, case_id)
        else:
            if fcm_id:
                status_code = upload_fcm_document_to_edm(
                    file_path, doc_number, ", ".join(customs_clearance_numbers)
                )
            else:
                status_code = upload_document_to_edm(
                    file_path,
                    doc_number,
                    ", ".join(customs_clearance_numbers),
                    filing_country,
                )
        save_analyzer_log_time(batch_id=email_id, field_name="each_document_upload_e")

        is_retrying, break_loop = handle_doc_upload_retry(
            write_parent_batch_log,
            email_instance,
            status_code,
            info,
            additional_doc=True,
        )

        if break_loop:
            break

        edm_upload_error = post_doc_upload_process(
            write_parent_batch_log,
            email_instance,
            status_code,
            file_name,
            info,
            index,
            additional_doc_item=item,
        )

    return edm_upload_error, is_retrying

def safe_int(value):
    try:
        return int(float(value))
    except:
        return 0
    
def prepare_email_context(
    email_instance,
    multi_shipment,
    identifiers,
    shipment_id,
    fcm_id,
    housebill_number,
    failed_api_call_count,
    failed_doc_upload_count,
):
    """
    Prepare the email context based on the outcome of the assembly process.

    Args:
        email_instance (object): Instance contain email_batch data.
        multi_shipment (bool): Indicate the process is for multiple_shipment.
        identifiers (list): List of identifiers.
        shipment_id (list): List of shipment_id.
        fcm_id (list): List of fcm_id.
        housebill_number (list): List of housebill_number.
        failed_api_call_count (int): Count of failed API call.
        failed_doc_upload_count (int): Count of failed document upload.

    Returns:
        context (dict): Context contain metadata.
        message (str): Status message of the process.

    Process Details:
        - Set a default message.
        - For multi-shipment proces, determine the process was partially completed.
        - Then construct context with multi_shipment_info.
        - For other process, construct context with confirmation_numbers, housebill_number, and shipment_id or fcm_id.

    Notes:
        - Update the message if fcm_id is present.
    """
    message = "Assembly process completed successfully"
    context = {}

    if multi_shipment:
        error_count = 0
        if failed_api_call_count or failed_doc_upload_count:
            message = "Assembly process was partially completed"
            if failed_api_call_count:
                error_count = failed_api_call_count
            else:
                error_count = failed_doc_upload_count
        multi_shipment_info = list()
        id_type = ""
        if shipment_id:
            multi_shipment_info = list(
                zip_longest(identifiers, shipment_id, housebill_number)
            )
            id_type = "Shipment ID"
        elif fcm_id:
            multi_shipment_info = list(
                zip_longest(identifiers, fcm_id, housebill_number)
            )
            id_type = "FCM ID"

        context = {
            "error_count_dict": {
                "error_count": error_count,
                "has_api_call_failure": failed_api_call_count != 0,
            },
            "multi_shipment_info": multi_shipment_info,
            "id_type": id_type,
        }

        profile_name = email_instance.matched_profile_name
        assembled_results = email_instance.assembled_results
        sheet_name = get_sheet_name(profile_name)
        if sheet_name:
            context["customTemplate"] = True
            context["sheetName"] = sheet_name

            templateData = []
            for index, item in enumerate(assembled_results):
                data = item["data"]
                temp_dict = {}

                if shipment_id and len(shipment_id) > index:
                    temp_dict["shipmentID"] = shipment_id[index]
                    temp_dict["housebillNumber"] = housebill_number[index]

                if data.get("destinationLocationCode"):
                    temp_dict["destinationLocation"] = data.get(
                        "destinationLocationCode"
                    )

                if data.get("shipper"):
                    shipper = data["shipper"]
                    if shipper.get("name"):
                        temp_dict["shipperName"] = shipper.get("name")

                if data.get("consignee"):
                    consignee = data["consignee"]
                    if consignee.get("name"):
                        temp_dict["consigneeName"] = consignee.get("name")

                if data.get("references"):
                    referencesData = data["references"]

                    for references in referencesData:
                        if references.get("number"):
                            temp_dict["mappingID"] = references.get("number")

                if data.get("goodsLines"):
                    goodsLinesData = data["goodsLines"]

                    for goodsLines in goodsLinesData:
                        if goodsLines.get("packageCount"):
                            if not temp_dict.get("packageCount"):
                                temp_dict["packageCount"] = safe_int(goodsLines.get("packageCount"))
                            else:
                                temp_dict["packageCount"] = (safe_int(temp_dict["packageCount"]) + safe_int(goodsLines.get("packageCount")))

                        if goodsLines.get("grossWeight"):
                            temp_dict["grossWeight"] = goodsLines.get("grossWeight")

                templateData.append(temp_dict)
            context["templateData"] = templateData

    else:
        confirmation_numbers = email_instance.confirmation_numbers

        context = {
            "confirmation_numbers": ",".join(confirmation_numbers),
        }

        if len(housebill_number) > 0:
            housebill_number = list(set(housebill_number))
            context["housebillNumber"] = ",".join(housebill_number)

        if shipment_id and len(shipment_id) > 0:
            context["shipmentID"] = ",".join(shipment_id)

        if len(fcm_id) > 0:
            context["fcmID"] = ",".join(fcm_id)

    return context, message


def get_sheet_name(profile_name):
    """Retrieve custom email template profile and sheet name from application settings"""
    sheet_name = None
    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data
        custom_profiles_data = application_settings["profileSettings"].get(
            "custom_email_template_profiles"
        )
        if not custom_profiles_data:
            raise ValueError(
                "custom_email_template_profiles could not be found in Application Settings"
            )

        for profile_data in custom_profiles_data:
            if profile_data.get("name") == profile_name:
                sheet_name = profile_data.get("sheetName")

    return sheet_name


def get_profile_settings_key_value(key):
    """Retrieve specific profile settings key data from application settings"""

    if not ApplicationSettings.objects.exists():
        raise ValueError("Application Settings not found")

    application_settings = ApplicationSettings.objects.first().data
    profile_settings = application_settings.get("profileSettings")

    if not profile_settings:
        raise ValueError("Profile Settings not found in the Application Settings")

    profile_settings_key_value = profile_settings.get(key)

    if not profile_settings_key_value:
        raise ValueError(
            f"'{key}' Profile Settings key could not found in the Application Settings"
        )

    return profile_settings_key_value


def duplicate_shipment_id_checker(
    write_parent_batch_log: Callable, assembled_results, profile_name, email_id
):
    """
    Reduce assembled_results if shipment_id is already exists for specific profiles.

    Args:
        write_parent_batch_log (Callable): Callable cfunction to write logs in timeline.
        assembled_results (list): Transaction result list.
        profile_name (str): Profile name.
        email_id (str): Email id.

    Returns:
        assembled_results (list): Updated list of assembled_results.
    """

    targeted_profiles = get_profile_settings_key_value(
        "shipment_id_duplication_check_profiles"
    )

    if profile_name not in targeted_profiles:
        return assembled_results

    removed_results = []
    filtered_results = []
    removed_results = []

    for result in assembled_results:
        references = result.get("data", {}).get("references", [])
        should_remove = False

        for reference in references:
            if reference.get("type") != "CCR":
                continue
            ref_shipment_id = reference.get("number").strip()
            if ShipmentRecord.objects.filter(shipment_id=ref_shipment_id).exists():
                removed_results.append(ref_shipment_id)
                should_remove = True
                break

        if not should_remove:
            filtered_results.append(result)
    removed_results_len = len(removed_results)

    if removed_results_len == 0:
        return assembled_results

    message = f"{removed_results_len} item{'s' if removed_results_len > 1 else ''} has been removed from Transaction result."
    write_parent_batch_log(
        message=message,
        batch_id=email_id,
        remarks=json.dumps(removed_results),
        status="warning",
        action="display_json",
    )
    return filtered_results
