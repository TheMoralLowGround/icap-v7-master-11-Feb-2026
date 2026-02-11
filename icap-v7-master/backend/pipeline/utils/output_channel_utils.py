import os
import json
import uuid
import requests
import traceback
from bs4 import BeautifulSoup
from typing import Callable
from copy import deepcopy
from core.models import (
    Batch,
    EmailParsedDocument,
)
from dashboard.models import Project, OutputChannel
from utils.utils import (
    save_analyzer_log_time,
    get_developer_settings,
    get_merged_definition_settings,
    get_additional_doc_type,
)
from pipeline.scripts.OutputChannels import OutputChannels
from pipeline.utils.process_batch_utils import write_parent_batch_log
from utils.logger_config import get_logger

logger = get_logger(__name__)

MAX_RETRY = int(os.getenv("MAX_RETRY", 0))
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 0))


def process_output_channel(
    write_parent_batch_log: Callable,
    email_instance,
    matched_profile_instance,
):
    """
    This is the main function to handle API call for projects and manage response.

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
    confirmation_numbers = []
    case_id = None

    email_id = email_instance.id
    project = matched_profile_instance.project
    send_time_stamp = matched_profile_instance.send_time_stamp

    if not email_instance.assembled_results:
        all_passed = False
        write_parent_batch_log(
            message="Assembled results not found",
            batch_id=email_id,
            status="warning",
        )
        return all_passed, is_retrying

    if len(email_instance.api_response) == 0:
        save_analyzer_log_time(batch_id=email_id, field_name="api_call_s")

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

        try:
            shipment_id = None
            if request_type == "shipment-update":
                lower_keys = {k.lower(): v for k, v in request_data.items()}
                shipment_id = lower_keys.get("shipmentid", None)

                if not shipment_id:
                    shipment_id_pos = 0
                    if matched_profile_instance.email_subject_match_option == "ProcessId":
                        shipment_id_pos = 1

                    splitted_parts = email_instance.email_subject.split("_")
                    if len(splitted_parts) > shipment_id_pos:
                        raise ValueError

                    possible_id = splitted_parts[shipment_id_pos]
                    if len(possible_id) <= 15:
                        shipment_id = possible_id

                    if not shipment_id:
                        raise ValueError
        except:
            all_passed = False
            write_parent_batch_log(
                message="Shipment ID not found",
                batch_id=email_id,
                status="warning",
            )
            return all_passed, is_retrying

        # Assumed JSON upload api configured at 1st position
        output_order = 1
        if request_type == "shipment-update":
            logger.info("Processing shipment-update...")
            output_order = 4
            request_data, status_code, packline_error = process_shipment_update(project, email_id, request_data, shipment_id)
            logger.info(f"process_shipment_update_status_code: {status_code}")
            if status_code not in {200, 404}:
                all_passed = False
                return all_passed, is_retrying

            if packline_error:
                write_parent_batch_log(
                    message=f"No Packline Data Found",
                    batch_id=email_id,
                    status="warning",
                )
        elif request_type == "commercial-invoice":
            output_order = 2

        output_config = get_output_config(project, email_id, order=output_order)
        if not output_config:
            all_passed = False
            return all_passed, is_retrying

        if not output_config.is_active:
            return all_passed, is_retrying

        if request_type == "shipment-create" and email_instance.shipment_status_url:
            shipment_status_url = email_instance.shipment_status_url[0]
            response_json, status_code = process_shipment_status(shipment_status_url)

        elif request_type == "hillebrand-gori":
            request_data, response_json, status_code = process_hillebrand_output(
                email_instance,
                project,
                request_data
            )
        else:
            try:
                response_json, status_code = process_output(
                    write_parent_batch_log,
                    email_instance,
                    output_config,
                    request_data,
                    request_type,
                    api_response,
                    shipment_id,
                    case_id
                )
            except Exception as e:
                logger.error(f"Invalid output channel API configuration: {e}")
                all_passed = False
                write_parent_batch_log(
                    message=f"Invalid output channel API configuration",
                    batch_id=email_id,
                    remarks = json.dumps(traceback.format_exc()),
                    status="warning",
                    action="display_json",
                )
                return all_passed, is_retrying

        if status_code == 200 and request_type == "shipment-create":
            if not any(response_json.get(key) for key in ["shipmentID", "fcmID"]):
                status_code = 504

            if request_data.get("productCode") == "FCMTR":
                response_json["productCode"] = request_data["productCode"]

            if response_json.get("statusURL") is None and response_json.get(
                "_DGFBookingID"
            ):
                status_url = (
                    f"{output_config.endpoint_url.rstrip('/')}/status?_DGFBookingID={response_json['_DGFBookingID']}"
                )
                response_json["statusURL"] = status_url
                email_instance.shipment_status_url.append(status_url)
                email_instance.save()

        is_retrying = handle_retry(
            write_parent_batch_log,
            email_instance,
            status_code,
            request_type,
            response_json,
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
            project
        )

        if is_retrying:
            email_instance.api_retry_count += 1
            email_instance.save()
            break

        # Update confirmation number in DB
        try:
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
        except:
            write_parent_batch_log(
                message=f"Confirmation number not found",
                batch_id=email_id,
                status="warning"
            )

    # Update the confirmation_numbers field in the EmailBatch instance
    email_instance.confirmation_numbers = confirmation_numbers
    email_instance.save()

    if not is_retrying:
        save_analyzer_log_time(batch_id=email_id, field_name="api_call_e")

    return all_passed, is_retrying



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
            if request_data.get("milestone"):
                milestone = request_data.pop("milestone")

    if request_type == "usacustoms":
        case_id = email_instance.email_subject.split("_")[0]

    return request_data, milestone, case_id, identifier


def get_output_config(project, email_id, output_type="json", order=1):
    """Retrieve output configuration"""
    project_instance = Project.objects.filter(name=project).first()
    if not project_instance:
        return None

    project_settings = project_instance.settings
    output_channels = project_settings.get("outputChannels", {}).get("outputChannelTypes", [])

    if not isinstance(output_channels, list):
        return None

    output_config = None
    for channel in output_channels:
        if (
            channel.get("output_type") == output_type
            and channel.get("order") == order
        ):
            title = channel.get("title")
            output_id = channel.get("output_id")
            if not output_id:
                continue

            output_instance = OutputChannel.objects.filter(output_id=output_id)
            if output_instance.exists():
                output_config = output_instance.first()
                if not output_config.is_active:
                    logger.info(f"Output channel ({title}) configuration is disabled")
                    write_parent_batch_log(
                        message=f"Output channel ({title}) configuration is disabled",
                        batch_id=email_id,
                        status="warning",
                    )
                return output_config

    if not output_config:
        logger.info("Output channel configuration not found")
        write_parent_batch_log(
            message="Output channel configuration not found",
            batch_id=email_id,
            status="failed",
        )
        return None


def process_shipment_status(shipment_status_url):
    """Status code for shipment"""
    if get_developer_settings("Mock API"):
        response_json, status_code = manage_mock_api("shipment-status")
        return response_json, status_code

    logger.info(f"Calling {shipment_status_url}")
    response = requests.get(shipment_status_url)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 200:
        response_json["statusURL"] = shipment_status_url

    return response_json, status_code


def process_output(
    write_parent_batch_log: Callable,
    email_instance,
    output_config,
    request_data,
    request_type,
    api_response,
    shipment_id,
    case_id
):
    if request_type == "shipment-create":
        if api_response and any(
            [
                api_response.get("response_json", {}).get(key)
                for key in ["shipmentID", "fcmID"]
            ]
        ):
            status_code = api_response["status_code"]
            response_json = api_response["response_json"]

            return response_json, status_code

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

    if get_developer_settings("Mock API"):
        write_parent_batch_log(
            message=f"Mock API triggered",
            batch_id=email_id,
            status="inprogress"
        )
        response_json, status_code = manage_mock_api(request_type)
        return response_json, status_code

    logger.info(f"Calling {output_config.endpoint_url}")
    response = OutputChannels(output_config).send_json(request_data, shipment_id, case_id)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def print_api_response(response):
    """Print any API response"""
    logger.info(f"{response.status_code=}")
    logger.info(f"{response.text=}")


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
    elif request_type == "hillebrand-gori":
        confirmation_number = request_data.get("service_id")

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


def manage_mock_api(type):
    """This function performed as dummy api response"""
    if type == "commercial-invoice":
        return {
            "status": "200",
            "detail": "Commercial Invoice ComInv006 created successfully",
            "apiCorrelationID": "48806158-172a-495f-b621-6b62dcafc923",
        }, 200

    elif type == "booking":
        return {
            "status": "200",
            "title": "Accepted",
            "_DGFBookingID": "183bc808cf8b4a63aeaabc8a271868f6",
            "housebillNumber": "S00158002",
            "customsJobNumber": "BANC000064",
        }, 200

    elif type == "customs-entry":
        return {
            "_DGFBookingID": "dad21f7c-0832-4ac1-9663-4c2c8cbbf0e1",
            "status": "Accepted",
            "responseCode": "200",
            "responseMessage": "OK",
            "customsJobNumber": "BSJO000140",
        }, 200

    elif type == "usacustoms":
        return {
            "apiCorrelationID": "27cb8017-42e2-4cbd-8b85-b1536a713641",
            "detail": "Receieved OCR Details.",
        }, 200

    elif type == "dsc-wms":
        return {
            "detail": "Message Received Successfully",
            "title": "OK",
            "instance": "Static Response",
        }, 200

    elif type == "shipment-create":
        return {
            "_DGFBookingID": "dad21f7c-0832-4ac1-9663-4c2c8cbbf0e1",
            "status": "Accepted",
            "housebillNumber": "QB207759",
            "shipmentID": "BSJO000140",
            "statusURL": None,
        }, 200

    elif type == "shipment-status":
        return {
            "status": "Accepted",
            "housebillNumber": "QB207759",
            "shipmentID": "BSJO000140",
        }, 200

    elif type == "shipment-update":
        return {
            "shipmentID": "BSJO000140",
        }, 200

    elif type == "housebill_info":
        return {
            "SHIPMENTID": "BSJO000140",
        }, 200

    elif type == "shipment_info":
        return {
            "SHIPMENTID": "BSJO000140",
        }, 200

    elif type == "shipment_package_details":
        return [
            {
                "PACKAGEID": "DFODQA00710649",
                "PACKAGE_VOLUME_UOM": "MTQ",
                "PACKAGE_VOLUME": "6.912",
                "DIMENSIONS_UOM": "CMT",
                "GROSS_WEIGHT": "700.000",
                "GROSS_WEIGHT_UOM": "KGM",
                "PACKAGE_COUNT": "6",
                "GOODS_VALUE": "0.0000",
                "PACKAGE_LENGTH": "120.000",
                "GOODS_CURRENCY": "EUR",
                "PACKAGE_TYPE": "PCE",
                "COMMODITY_CODE": "",
                "PACKAGE_WIDTH": "80.000",
                "GOODS_DESCRIPTION": "",
                "PACKAGE_HEIGHT": "120.000",
            }
        ], 200, False

    elif type == "timestamp_api":
        return (
            f"""<?xml version='1.0' encoding='UTF-8'?>
            <soapenv:envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\">
                <soapenv:body>
                    <ser-root:ib_sl_rcptwebserviceresponse xmlns:ser-root=\"http://localhost/IB_SL_RcptWebService.services\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
                        <responsemessage>a925e6e4-d162-4788-9ed4-6d5e2f309746</responsemessage>
                        <responseerror>0</responseerror>
                    </ser-root:ib_sl_rcptwebserviceresponse>
                </soapenv:body>
            </soapenv:envelope>""", 200
        )

    elif type == "freight":
        return {
            "status": "Success",
            "shipment": {
                "id": "000000298",
            },
            "references": [
                {"qualifier": "CNR", "value": "Consignor-Ref.123"},
                {"qualifier": "CNZ", "value": "Consignee-Ref.456"},
            ],
        }, 200

    elif type == "service_id":
        return [
            {
                "id": 39414882,
                "shipments": [
                    {
                        "_links": {
                            "href": "/v6/shipments/14328515",
                            "rel": "self"
                        },
                        "id": 14328515
                    },
                    {
                        "_links": {
                            "href": "/v6/shipments/14323482",
                            "rel": "self"
                        },
                        "id": 14323482
                    }
                ]
            }
        ], 200

    elif type == "ticket_id":
        return {
            "href": "/v1/services/39414882/documents/Carrier_Bill_of_lading__61214c2b7b1340d3a60c315655dfc9d0.pdf/content",
            "rel": "content",
            "id": "Carrier_Bill_of_lading__61214c2b7b1340d3a60c315655dfc9d0.pdf",
            "type": "POST"
        }, 200


### Functions for shipment-update

def process_shipment_update(project, email_id, request_data, shipment_id):
    packline_error = False
    response_json, status_code, shipment_id = validate_shipment_id(
        project, email_id, shipment_id
    )

    if not shipment_id:
        write_parent_batch_log(
            message="Unable to Validate shipment ID",
            batch_id=email_id,
            status="warning",
        )
        status_code = None
        return response_json, status_code, packline_error

    logger.info(f"{shipment_id=}")

    # Assumed that ShipmentPackageDetails configured at 3rd position
    output_config = get_output_config(project, email_id, order=3)
    if not output_config:
        status_code = None
        return response_json, status_code, packline_error

    if not output_config.is_active:
        status_code = None
        return response_json, status_code, packline_error

    shipment_data, status_code, packline_error = get_shipment_package_details(output_config, shipment_id)

    write_api_call_log(
        response_json,
        status_code,
        email_id,
        api_type="Shipment-package-details"
    )

    if status_code not in {200, 404}:
        return response_json, status_code, packline_error

    if shipment_data:
        try:
            request_data = update_shipment_data(shipment_data, request_data)
        except Exception as e:
            logger.error(f"shipment_data_update_failed {str(e)}")
            logger.error(traceback.print_exc())

    return request_data, status_code, packline_error


def validate_shipment_id(project, email_id, shipment_id):
    """
    Validate the provided shipment ID and retrieve shipment details.

    Args:
        shipment_id (str): shipment_id to be validated.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.
        valid_shipment_id (str or None): Validated shipment ID.

    Process Details:
        - Determine the input is the valid shipment ID or housebill.
        - Retrieve shipment details using 'get_housebill_info' if the input is housebill otherwise 'get_shipment_info'.
        - Extract the valid shipment ID.

    Notes:
        - Valid shipment ID starts with specific prefix.
    """
    response_json = {}
    status_code = None
    valid_shipment_id = None
    valid_prefixes = ("S24", "S25", "S26")

    is_housebill = not (
        any(shipment_id.startswith(prefix) for prefix in valid_prefixes)
        and len(shipment_id) >= 11
    )

    # Assumed that housebill_info api configured at 1st position
    # Assumed that shipment_info api configured at 2nd position
    order = 1
    api_type = "Housebill-info"
    if not is_housebill:
        order = 2
        api_type = "Shipment-info"

    output_config = get_output_config(project, email_id, order=order)
    if not output_config:
        return response_json, status_code, valid_shipment_id

    logger.info(f"output_config for {order}: {output_config.is_active}")
    if not output_config.is_active:
        return response_json, status_code, valid_shipment_id

    # if it's not a valid shipment_id it's a house bill number which we will use to fetch shipment ID
    if is_housebill:
        response_json, status_code = get_housebill_info(output_config, shipment_id)
    else:
        # check if it's a valid shipmeent ID
        response_json, status_code = get_shipment_info(output_config, shipment_id)

    write_api_call_log(
        response_json,
        status_code,
        email_id,
        api_type
    )

    if status_code == 200:
        valid_shipment_id = response_json.get("SHIPMENTID")

    return response_json, status_code, valid_shipment_id


def get_housebill_info(output_config, housebill):
    """
    Uses the house bill number to get shipment id returns both response and status code

    Args:
        housebill (str): Which info is to get.

    Returns:
        response_json (dict): API response json.
        status_code (int): API status code.

    Process Details:
        - Define API_URL, headers and data.
        - Getting response need to send POST requests to API_URL.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    if get_developer_settings("Mock API"):
        response_json, status_code = manage_mock_api("housebill_info")
        return response_json, status_code

    data = {
        "houseBill": housebill,
        "fieldNames": "SHIPMENTID",
    }
    logger.info("Calling getHousebillInfo API...")
    response = OutputChannels(output_config).send_json(data)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def get_shipment_info(output_config, shipment_id):
    """
    Checks if the shipment id is valid and returns the status code

    Args:
        shipment_id (str): Which info is to get.

    Returns:
        response_json (dict): API response json.
        status_code (int): API status code.

    Process Details:
        - Define URL, headers and data.
        - Getting response need to send POST requests to URL.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    if get_developer_settings("Mock API"):
        response_json, status_code = manage_mock_api("shipment_info")
        return response_json, status_code

    data = {
        "shipmentId": shipment_id,
        "fieldNames": "SHIPMENTID",
    }

    logger.info("Calling getShipmentInfo API...")
    response = OutputChannels(output_config).send_json(data)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def get_shipment_package_details(output_config, shipment_id):
    """
    Get Shipment Package Details

    Args:
        shipment_id (str): Which package details need to get.

    Returns:
        response_json (dict): API response json.
        status_code (int): API status code.
        packline_error (bool): Flag for packline error occurred.

    Process Details:
        - Define API_URL, headers and json.
        - Getting response need to send POST requests to API_URL.
        - If the status_code 404 then packline_error will be True and update the response_json blank.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
        - For 'packline_error', error description should be 'No Data Found'.
    """
    if get_developer_settings("Mock API"):
        response_json, status_code, packline_error = manage_mock_api("shipment_package_details")
        return response_json, status_code, packline_error

    data = {
        "shipmentId": shipment_id,
        "fieldNames": "PACKAGEID,PACKAGE_TYPE,PACKAGE_COUNT,COMMODITY_CODE,GOODS_DESCRIPTION,GOODS_VALUE,GOODS_CURRENCY,GROSS_WEIGHT_UOM,GROSS_WEIGHT,PACKAGE_VOLUME,PACKAGE_VOLUME_UOM,PACKAGE_LENGTH,PACKAGE_WIDTH,PACKAGE_HEIGHT,DIMENSIONS_UOM",
    }

    logger.info("Calling getShipmentPackageDetails API...")
    response = OutputChannels(output_config).send_json(data)
    print_api_response(response)

    response_json = response.json()
    status_code = response.status_code
    packline_error = False

    if status_code == 404:
        error_desc = response_json.get("errorDesc", "")

        if error_desc == "No Data Found":
            packline_error = True
            response_json = []

    return response_json, status_code, packline_error


def write_api_call_log(response_json, status_code, email_id, api_type):
    """write api call log on parent batch"""
    status = "inprogress"
    message_ext = "successful"
    if status_code != 200:
        status = "warning"
        message_ext = "not successful"

    write_parent_batch_log(
        message=f"{api_type} API call was {message_ext}",
        batch_id=email_id,
        status=status,
        remarks=json.dumps(response_json, indent=4),
        action="display_json",
    )


def update_shipment_data(shipment_data, extracted_data):
    """
    Update shipment data with extracted goodsLines data.

    Args:
        shipment_data (dict): Shipment data to be updated.
        extracted_data (dict): Data extracted for updating the shipment.

    Returns:
        final_output (dict): Updated shipment data.

    Process Details:
        - Retrieve 'goodsLines' field from the extracted_data.
        - If 'shipment_data' and 'goodsLines' exists then updates the 'goodsLines' field.
        - Copy all other fields from the extracted data, excluding 'goodsLines'.

    Notes:
        - 'default_goodsLines_update' is used for updating goodsLines.
        - 'get_scenario' is called to determine update condition.
    """
    final_output = dict()

    extracted_goodsLines = extracted_data.get("goodsLines")

    if shipment_data:
        if extracted_goodsLines:
            # Scenario 1 Type update
            if get_scenario(True) == 1:
                final_output["goodsLines"] = default_goodsLines_update(
                    extracted_goodsLines, shipment_data
                )

    for k, v in extracted_data.items():
        if k != "goodsLines":
            final_output[k] = v

    return final_output


def get_scenario(input_):
    """return scenario based on the given input"""
    if input_:
        return 1


def default_goodsLines_update(extracted_goodsLines, existing_goodsLines):
    """
    Packline update scenario 1 Where only the first packline id is to be taken
    and added on to the first goodslines from the extracted ones.
    """
    # Take the first packline packageID
    first_packageID = existing_goodsLines[0].get("PACKAGEID")

    # And add that to extracted first gooodslines
    extracted_goodsLines[0]["goodsLineID"] = first_packageID

    return extracted_goodsLines


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
    project
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
        status_code == 200 and send_time_stamp and request_type in ["shipment-create", "shipment-update"]
    ):
        return all_passed, is_retrying

    email_id = email_instance.id
    project_instance = Project.objects.filter(name=project).first()
    if not project_instance:
        all_passed = False
        return all_passed, is_retrying

    project_settings = project_instance.settings
    output_channels = project_settings.get("outputChannels", {}).get("outputChannelTypes", [])

    order = 0
    for channel in output_channels:
        if channel.get("output_type") == "json":
            order += 1

    output_config = get_output_config(project, email_id, order=order)
    if not output_config:
        all_passed = False
        return all_passed, is_retrying

    if not output_config.is_active:
        return all_passed, is_retrying

    if response_json.get("fcmID"):
        shipment_id = response_json["fcmID"]
    else:
        shipment_id = response_json["shipmentID"]

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
            shipment_id, milestone_dict, output_config
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


def send_shipment_time_stamp(shipment_id, milestone, output_config):
    """
    After successful shipment creation, update the time stamp.

    Args:
        shipment_id (str): Which timestamp update is to be sent.
        milestone (dict): Contain the milestone details with keys.

    Returns:
        status_code (int): API status code.

    Process Details:
        - Define API_URL and headers.
        - Prepare request body using mileston data.
        - Send POST requests to the API endpoint.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined status_code.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        response_content, status_code = manage_mock_api("timestamp_api")
        return response_content, status_code

    recorded_date_time = milestone["text"]
    time_stamp_code = milestone["type"]
    remark = f"Timestamp update for: {time_stamp_code}"
    message_id = str(uuid.uuid4())

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ib=\"https://api-test.dhl.com/dgff-eip-ws-soap/ib_sl_rcptwebservice/IB_SL_RcptWebService.services\">
            <soapenv:Header/>
            <soapenv:Body>
                <ib:IB_SL_RcptWebService>
                <Service>AS_API</Service>
                <Operation>notifyShipmentStatusChange_v5_Receiver</Operation>
                <Message><![CDATA[<?xml version=\"1.0\" encoding=\"UTF-8\"?>
                    <TimestampUpdate xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"TimestampUpdateAPI.xsd\">
                        <MessageHeader>
                            <Version>1.0</Version>
                            <SenderID>WW_EDM</SenderID>
                            <ReceiverID>CW1</ReceiverID>
                            <MessageID>{message_id}</MessageID>
                            <CreationDateTime>{recorded_date_time}</CreationDateTime>
                        </MessageHeader>
                        <ReferenceType>SHP</ReferenceType>
                        <ReferenceNumber>{shipment_id}</ReferenceNumber>
                        <ContainerNumber></ContainerNumber>
                        <Code>{time_stamp_code}</Code>
                        <RecordedDateTime>{recorded_date_time}</RecordedDateTime>
                        <LocationCode></LocationCode>
                        <Signatory>EDM</Signatory>
                        <Remark>{remark}</Remark>
                    </TimestampUpdate>]]>
                </Message>
                <SessionID></SessionID>
                <ResponseAddress></ResponseAddress>
                </ib:IB_SL_RcptWebService>
            </soapenv:Body>
        </soapenv:Envelope>
    """

    logger.info("Calling TimeStamp API...")
    response = OutputChannels(output_config).send_timestamp(body)
    print_api_response(response)
    logger.info(response.content)

    status_code = response.status_code
    response_content = response.content

    return response_content, status_code


# Functions for hillebrand-gori

def process_hillebrand_output(email_instance, project, request_data):
    """"Process Hillebrand Gori"""
    response_json = {}
    status_code = None
    email_id = email_instance.id
    request_data["transactionID"] = email_id

    email_parsed_document = EmailParsedDocument.objects.filter(email_id=email_id).first()
    if email_parsed_document:
        request_data["originalFilename"] = email_parsed_document.name

    if email_instance.confirmation_numbers:
        request_data["service_id"] = email_instance.confirmation_numbers[0]
    else:
        if email_instance.api_retry_count == 0:
            write_parent_batch_log(
                message=f"Calling Hillebrand-Gori service-id API",
                batch_id=email_id,
                status="inprogress"
            )

        # Assumed that ServiceID configured at 1st position
        output_config = get_output_config(project, email_id, order=1)
        if not output_config:
            return request_data, response_json, status_code

        if not output_config.is_active:
            return request_data, response_json, status_code

        service_id = None
        if request_data.get("fileNumber"):
            reference = request_data.get("fileNumber")
            request_data["reference"] = reference

            response_json, status_code, service_id = get_service_id(output_config, request_data)

        if not service_id:
            if request_data.get("billofLadingNumber"):
                reference = request_data.get("billofLadingNumber")
                request_data["reference"] = reference

                response_json, status_code, service_id = get_service_id(output_config, request_data)

        if not service_id:
            if request_data.get("bookingNumber"):
                reference = request_data.get("bookingNumber")
                request_data["reference"] = reference

                response_json, status_code, service_id = get_service_id(output_config, request_data)

        write_api_call_log(
            response_json,
            status_code,
            email_id,
            "Hillebrand-Gori service-id"
        )
        if not service_id:
            return request_data, response_json, status_code

        request_data["service_id"] = service_id
        email_instance.confirmation_numbers.append(service_id)

        if email_instance.api_retry_count > 0:
            email_instance.api_retry_count = 0

        email_instance.save()

    payload = build_hillebrand_payload(request_data)
    if email_instance.api_retry_count == 0:
        write_parent_batch_log(
            message=f"Calling Hillebrand-Gori ticket-id API to send payload",
            batch_id=email_id,
            remarks=json.dumps(payload),
            status="inprogress",
            action="display_json",
        )

    # Assumed that TicketID configured at 2nd position
    output_config = get_output_config(project, email_id, order=2)
    if not output_config:
        status_code = None
        return request_data, response_json, status_code

    if not output_config.is_active:
        status_code = None
        return request_data, response_json, status_code
    response_json, status_code = get_ticket_id(output_config, request_data, payload)

    return request_data, response_json, status_code


def get_service_id(output_config, request_data):
    """ Get Service ID from HG GORI"""
    service_id = None
    if get_developer_settings("Mock API"):
        response_json, status_code = manage_mock_api("service_id")
        return response_json, status_code, service_id

    logger.info(f"Calling Service ID API...")
    response = OutputChannels(output_config).dynamic_api_call(request_data)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 200:
        for data in response_json:
            if data.get("id"):
                service_id = str(data.get("id"))

    if status_code == 200 and not service_id:
        status_code = 404

    return response_json, status_code, service_id


def build_hillebrand_payload(request_data):
    """Payload for Hillebrand document upload"""
    bol_type = request_data.get("bolType")
    sob_date = request_data.get("sobDate")
    original_filename = request_data.get("originalFilename")
    transaction_id  = request_data.get("transactionID")

    if bol_type and bol_type.lower() == "rated":
        code = "cbr"
        description = "Carrier Bill of Lading Rated"
    elif bol_type and bol_type.lower() == "draft":
        code = "cbd"
        description = "Carrier Bill of Lading Draft"
    else:
        code = "cbl"
        description = "Carrier Bill of Lading"

    payload = {
        "documentType": {
            "code": code,
            "description": description
        },
        "documentDateTime": sob_date,
        "fileName": original_filename,
        "user": "icap@dhl.com",
        "comment": transaction_id
    }

    return payload


def get_ticket_id(output_config, request_data, payload):
    """ Get Ticket ID from HG GORI"""
    status_code = None
    if get_developer_settings("Mock API"):
        response_json, status_code = manage_mock_api("ticket_id")
        return response_json, status_code

    logger.info(f"Calling Ticket ID API...")
    response = OutputChannels(output_config).dynamic_api_call(request_data, payload=payload)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 202:
        status_code = 200

    return response_json, status_code



### Document Upload Process###


def handle_output_doc_upload(
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
    filing_country = profile_name[0:2]
    edm_upload_error = False
    case_id = None
    shipment_id = []
    housebill_number = []
    api_response = email_instance.api_response
    is_retrying = False
    assembled_results = [*email_instance.assembled_results]
    customs_clearance_numbers = []
    failed_doc_upload_count = 0
    identifiers = []

    output_instance = OutputChannel.objects.filter(project__name=project, output_type="document")
    if not output_instance.exists():
        edm_upload_error = True
        write_parent_batch_log(
            message=f"Output channel document upload configuration not found",
            batch_id=email_id,
            status="warning"
        )
        return (
            edm_upload_error,
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            failed_doc_upload_count,
        )

    if output_instance.count() > 1:
        edm_upload_error = True
        write_parent_batch_log(
            message=f"Multiple output channel document upload configurations found",
            batch_id=email_id,
            status="warning",
        )
        return (
            edm_upload_error,
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            failed_doc_upload_count,
        )

    output_config = output_instance.first()

    if not output_config.is_active:
        write_parent_batch_log(
            message=f"Output channel document upload configuration disabled",
            batch_id=email_id,
            status="warning"
        )
        return (
            edm_upload_error,
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            failed_doc_upload_count,
        )

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
            output_config
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
            customs_clearance_number,
            fcm_id,
            output_config
        )

    return (
        edm_upload_error,
        identifiers,
        shipment_id,
        housebill_number,
        is_retrying,
        failed_doc_upload_count,
    )


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
        files_list (list): contain file details such as name, path, type, and doc_code.

    Process Details:
        - Fetche 'doc_code' value based on 'doc_type' from project definition.
        - Query 'EmailParsedDocument' model for files linked to the provided batch_id.
        - Update 'uploaded_doc_names' field in the 'api_response'.

    Notes:
        - Map 'doc_type' to 'doc_code' using project settings.
    """
    # Read definition settings to get docCode from docType
    doc_types_data = get_doc_types_data(project)

    batches = item["batches"]

    if not isinstance(batches, list):
        batches = [batches]

    files_list = list(
        EmailParsedDocument.objects.filter(batch_id__in=batches).values(
            "name", "path", "type", "matched_profile_doc__doc_type", "doc_code"
        )
    )

    if api_response and not api_response[index].get("uploaded_doc_names"):
        api_response[index]["uploaded_doc_names"] = [None] * len(files_list)

    for f in files_list:
        doc_type = f["matched_profile_doc__doc_type"]
        if f.get("doc_code"):
            continue

        doc_code = doc_types_data.get(doc_type, None)
        f["doc_code"] = doc_code

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
    output_config
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
    project = matched_profile_instance.project

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
            info, case_id, file_path, doc_code = get_doc_upload_info(
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

            if get_developer_settings("Mock API"):
                status_code = 200
                info["mock_API"] = True

            elif "hg_bol" in project.lower():
                ticket_data = api_response[index]
                ticket_id = ticket_data.get("id")
                data = {
                    "service_id": email_instance.confirmation_numbers[0],
                    "ticket_id": ticket_id,
                }
                with open(file_path, "rb") as f:
                    files = [("files", f)]
                    response = OutputChannels(output_config).dynamic_api_call(data, files=files)
                    print_api_response(response)
                    status_code = response.status_code
                    if status_code == 202:
                        status_code = 200

            else:
                doc_info = {
                    "ShipmentID": customs_clearance_number,
                    "CW1doctype": doc_code,
                    "OriginCountry": filing_country,
                }
                form_data = {"documentinfo": json.dumps(doc_info)}

                with open(file_path, "rb") as f:
                    files = [("files", f)]

                    response = OutputChannels(output_config).send_document(form_data, files, case_id)
                    print_api_response(response)
                    status_code = response.status_code

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
    doc_code = file_item["doc_code"]
    case_id = None

    # if project == "CustomsEntryUpdate" and doc_type == "Bill Of Entry":
    #     doc_code = 711 if "IMPORT" in profile_name else 710

    info = {
        "file_path": file_path,
        "CW1doctype": doc_code,
        "filing_country": filing_country,
    }

    if request_type in ["shipment-create", "shipment-update"]:
        info["shipmentID"] = customs_clearance_number
    elif request_type == "usacustoms":
        case_id = email_instance.email_subject.split("_")[0]
        info["case_id"] = case_id
    else:
        info["customs_clearance_number"] = customs_clearance_number

    return info, case_id, file_path, doc_code


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
    customs_clearance_number,
    fcm_id,
    output_config
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
        customs_clearance_number (string): Customs clearance number.

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
    doc_code = doc_types_data.get(document_type)

    if not doc_code:
        edm_upload_error = True

        write_parent_batch_log(
            batch_id=email_id,
            status="warning",
            message=f"Uploading additional document failed due to no doc number found in the definition",
        )

        return edm_upload_error, is_retrying

    for index, item in enumerate(email_instance.additional_docs_to_upload):
        if item["uploaded"]:
            continue

        file_name = item["name"]
        file_path = item["path"]
        info = {
            "file_path": file_path,
            "CW1doctype": doc_code,
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

        save_analyzer_log_time(
            batch_id=email_id, field_name="each_document_upload_s"
        )

        if get_developer_settings("Mock API"):
            status_code = 200
            info["mock_API"] = True
        else:
            doc_info = {
                "ShipmentID": customs_clearance_number,
                "CW1doctype": doc_code,
                "OriginCountry": filing_country,
            }
            form_data = {"documentinfo": json.dumps(doc_info)}

            opened_file = open(file_path, "rb")
            files = [("files", opened_file)]

            response = OutputChannels(output_config).send_document(form_data, files, case_id=case_id)
            print_api_response(response)
            status_code = response.status_code

        save_analyzer_log_time(
            batch_id=email_id, field_name="each_document_upload_e"
        )

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


def get_doc_types_data(project):
    """Retrieve document type data for specified project."""
    def_settings = get_merged_definition_settings(project)
    doc_type_items = def_settings["options"]["options-meta-root-type"]["items"]

    doc_types_data = {}

    for i in doc_type_items:
        doc_types_data[i["docType"]] = i.get("docCode", None)

    return doc_types_data

