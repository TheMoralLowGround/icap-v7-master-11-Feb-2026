"""
Organization: AIDocbuilder Inc.
File: utils/assembly_api_utils.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-11

Description:
    This file contain necessary functions to execution the DHL API.

Dependencies:
    - os, json, base64, uuid, traceback, requests

Main Features:
    -
"""

import base64
import json
import os
import uuid
import traceback
import requests
from functools import wraps
from utils.utils import get_developer_settings

ICAP_API_URL = os.getenv("ICAP_API_URL")

MOCK_ASSEMBLY_APIS = int(os.getenv("MOCK_ASSEMBLY_APIS", 0))

CUSTOMS_API_BASE_URL = os.getenv("CUSTOMS_API_BASE_URL")
CUSTOMS_API_KEY = os.getenv("CUSTOMS_API_KEY")

DSC_API_BASE_URL = os.getenv("DSC_API_BASE_URL")
DSC_API_CLIENT_ID = os.getenv("DSC_API_CLIENT_ID")
DSC_API_CLIENT_SECRET = os.getenv("DSC_API_CLIENT_SECRET")

FREIGHT_API_CLIENT_ID = os.getenv("FREIGHT_API_CLIENT_ID")
FREIGHT_API_CLIENT_SECRET = os.getenv("FREIGHT_API_CLIENT_SECRET")

EDM_API_KEY = os.getenv("EDM_API_KEY")

TIMESTAMP_API_BASE_URL = os.getenv("TIMESTAMP_API_BASE_URL")
DHL_API_KEY = os.getenv("DHL_API_KEY")

USA_API_BASE_URL = os.getenv("USA_API_BASE_URL")
USA_API_KEY = os.getenv("USA_API_KEY")

FCM_CLIENT_ID = os.getenv("FCM_CLIENT_ID")
FCM_CLIENT_SECRET = os.getenv("FCM_CLIENT_SECRET")


def handle_api_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.Timeout:
            return {"error": "Request timed out"}, 504
        except requests.ConnectionError:
            return {"error": "Connection failed"}, 503
        # except requests.HTTPError as e:
        #     return {"error": str(e)}, e.response.status_code
        except ValueError:
            return {"error": "Invalid JSON response"}, 422
        # except Exception as e:
        #     print(f"Unexpected error in {func.__name__}")
        #     return {"error": "Internal server error"}, 500

    return wrapper


def validate_api_response_200(response, error_message):
    """Validate unsuccessfull API response"""
    if response.status_code != 200:
        try:
            response_json = response.json()
            error_message = (
                error_message
                + f": {response_json['status']}, {response_json['title'], response_json['detail']}"
            )
        except:
            pass

        raise ValueError(error_message)


def print_api_response(response):
    """Print any API response"""
    print(f"{response.status_code=}")
    print(f"{response.text=}")


def get_customs_access_token():
    """
    Reteive access token using key to authenticate CIV (CommercialInvoice)
    and CreateB (Bookings) APIs
    """
    API_URL = f"{CUSTOMS_API_BASE_URL}/auth/v1/token"
    encoded_key = base64.b64encode(CUSTOMS_API_KEY.encode()).decode()
    headers = {"Authorization": f"Basic {encoded_key}"}
    params = {
        "response_type": "access_token",
        "grant_type": "client_credentials",
    }

    print("Calling /auth/v1/token API...")
    response = requests.post(API_URL, headers=headers, params=params)

    print_api_response(response)

    error_message = "/auth/v1/token API Failed"
    validate_api_response_200(response, error_message)
    response_json = response.json()
    access_token = response_json["access_token"]

    return access_token


def get_dsc_wms_access_token():
    """Reteive access token for DSC_WMS project"""
    API_URL = f"{DSC_API_BASE_URL}/dhllink/auth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    json = {
        "client_id": DSC_API_CLIENT_ID,
        "client_secret": DSC_API_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    print("Calling /dhllink/auth/token API...")
    response = requests.post(API_URL, headers=headers, data=json)

    print_api_response(response)

    error_message = "/dhllink/auth/token API Failed"
    validate_api_response_200(response, error_message)
    response_json = response.json()
    access_token = response_json["access_token"]

    return access_token


def get_freight_access_token():
    """Reteive access token for Freight project"""
    API_URL = f"{CUSTOMS_API_BASE_URL}/auth/v1/token"
    params = {
        "response_type": "access_token",
        "grant_type": "client_credentials",
    }
    json = {
        "client_id": FREIGHT_API_CLIENT_ID,
        "client_secret": FREIGHT_API_CLIENT_SECRET,
    }

    print("Calling /auth/v1/token API...")
    response = requests.post(API_URL, params=params, data=json)

    print_api_response(response)

    error_message = "/auth/v1/token API Failed"
    validate_api_response_200(response, error_message)
    response_json = response.json()
    access_token = response_json["access_token"]

    return access_token


def send_customs_json(final_json, type, customs_job_id=None, case_id=None):
    """
    Send Output JSON to customs APIs based on type.

    Args:
        final_json (dict): JSON data to be sent.
        type (str): Type of request.
        customs_job_id (str): Customs job ID for other type request.
        case_id (str): Case ID for 'usacustoms' type request.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.

    Process Details:
        - For type 'usacustoms' call 'usa_api_requests()' to handle the request with 'case_id'.
        - For other types call 'other_api_requests()' with 'customs_job_id'.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        if type == "commercial-invoice":
            return {
                "status": "200",
                "detail": "Commercial Invoice DummyComInv006 created successfully",
                "apiCorrelationID": "dummy48806158-172a-495f-b621-6b62dcafc923",
            }, 200
        if type == "booking":
            return {
                "status": "200",
                "title": "Accepted",
                "_DGFBookingID": "dummy183bc808cf8b4a63aeaabc8a271868f6",
                "housebillNumber": "TEST123",
                "customsJobNumber": "DUMMYBANC000064",
            }, 200
        if type == "customs-entry":
            return {
                "_DGFBookingID": "dummydad21f7c-0832-4ac1-9663-4c2c8cbbf0e1",
                "status": "Accepted",
                "responseCode": "200",
                "responseMessage": "OK",
                "customsJobNumber": "DUMMYBSJO000140",
            }, 200
        if type == "usacustoms":
            return {
                "apiCorrelationID": "27cb8017-42e2-4cbd-8b85-b1536a713641",
                "detail": "Receieved OCR Details.",
            }, 200

    if type == "usacustoms":
        response = usa_api_requests(type, case_id, final_json)
    else:
        response = other_api_requests(type, customs_job_id, final_json)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def other_api_requests(type, customs_job_id, final_json):
    """
    API rquests for other except usacustoms.

    Args:
        type (str): Type of request.
        customs_job_id (str): Customs job ID for other type request.
        final_json (dict): JSON data to be sent.

    Returns:
        response (dict): API response JSON.

    Process Details:
        - Define 'API_URL' for type.
        - Reteive customs access token.
        - Getting response through post requests.

    Notes:
        - Different 'API_URL' for different type.
    """
    if type == "commercial-invoice":
        API_URL = f"{CUSTOMS_API_BASE_URL}/dgff/customs/commercial-invoice"
    elif type == "booking":
        API_URL = f"{CUSTOMS_API_BASE_URL}/dgff/customs/booking"
    elif type == "customs-entry":
        assert (
            customs_job_id is not None
        ), "customs_job_id is required for customs-entry API call"
        API_URL = f"{CUSTOMS_API_BASE_URL}/dgff/customs/entry-lines/{customs_job_id}"
    else:
        raise ValueError(f"Unsupported request type {type}")

    token = get_customs_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print(f"Calling {type} API...")
    response = requests.post(API_URL, json=final_json, headers=headers)
    print_api_response(response)

    return response


def usa_api_requests(type, case_id, final_json):
    """API rquests for other type except usacustoms"""
    API_URL = f"{USA_API_BASE_URL}/uscdzicap/booking-data"

    headers = {"api_key": USA_API_KEY, "caseid": case_id}
    print(f"Calling {type} API...")
    response = requests.post(API_URL, json=final_json, headers=headers)
    print_api_response(response)
    return response


def send_dsc_wms_json(final_json):
    """
    Send Output JSON to dsc_wms APIs.

    Args:
        final_json (dict): JSON data to be sent.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.

    Process Details:
        - Define 'API_URL'.
        - Reteive DSC_WMS access token.
        - Getting response through post requests.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {
            "detail": "Message Received Successfully",
            "title": "OK",
            "instance": "Static Response",
        }, 200

    API_URL = f"{DSC_API_BASE_URL}/dhllink/amer/Siemens/us_5009/expup"
    token = get_dsc_wms_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("Calling DSC_WMS API...")
    response = requests.post(API_URL, json=final_json, headers=headers)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


@handle_api_exceptions
def send_shipment_create_json(final_json, token=None):
    """
    Send Output JSON to shipment APIs.

    Args:
        final_json (dict): JSON data to be sent.
        token (str): Access token.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.

    Process Details:
        - Define 'API_URL'.
        - Reteive customs access token if not available.
        - Getting response through post requests.
        - Check the status_code is 200.
        - If "shipmentID" or "fcmID" key not present in the response then update the status_code.
        - If "statusURL" is None then make and update it using "_DGFBookingID".

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {
            "_DGFBookingID": "dummydad21f7c-0832-4ac1-9663-4c2c8cbbf0e1",
            "status": "Accepted",
            "housebillNumber": "DUMMYQB207759",
            "shipmentID": "DUMMYBSJO000140",
            "statusURL": None,
        }, 200

    API_URL = f"{CUSTOMS_API_BASE_URL}/dgff/transportation/shipment-booking"

    if not token:
        token = get_customs_access_token()

    headers = {"Authorization": f"Bearer {token}"}

    print("Calling ShipmentCreate API...")
    response = requests.post(API_URL, json=final_json, headers=headers)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 200:
        if not any(response_json.get(key) for key in ["shipmentID", "fcmID"]):
            status_code = 504

        if response_json.get("statusURL") is None and response_json.get(
            "_DGFBookingID"
        ):
            status_url = (
                f"{API_URL}/status?_DGFBookingID={response_json['_DGFBookingID']}"
            )
            response_json["statusURL"] = status_url

    return response_json, status_code


@handle_api_exceptions
def get_shipment_status(response_json):
    """
    Status code for shipment.

    Args:
        response_json (dict): JSON data to be sent.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.

    Process Details:
        - Define 'API_URL' from response_json.
        - Getting response through get requests.
        - If the status_code is 200 and "shipmentID" or "fcmID" key not present then update status_code.

    Notes:
        - After updating status_code, update statusURL in response_json with API_URL.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {
            "status": "Accepted",
            "housebillNumber": "DUMMYQB207759",
            "shipmentID": "DUMMYBSJO000140",
        }, 200

    API_URL = response_json["statusURL"]

    print("Calling Shipment Status API...")
    response = requests.get(API_URL)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 200:
        response_json["statusURL"] = API_URL

        if not any(response_json.get(key) for key in ["shipmentID", "fcmID"]):
            status_code = 504

    return response_json, status_code


def send_freight_json(final_json):
    """
    Send Output JSON to freight APIs

    Args:
        final_json (dict): JSON data to be sent.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.

    Process Details:
        - Define 'API_URL'.
        - Reteive freight access token.
        - Getting response through post requests.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {
            "status": "Success",
            "shipment": {
                "id": "DUMMYFRT-000000298",
            },
            "references": [
                {"qualifier": "CNR", "value": "Consignor-Ref.123DUMMY"},
                {"qualifier": "CNZ", "value": "Consignee-Ref.456DUMMY"},
            ],
        }, 200

    API_URL = (
        f"{CUSTOMS_API_BASE_URL}/freight/shipping/orders/v1/sendtransportinstruction"
    )
    token = get_freight_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("Calling freight API...")
    response = requests.post(API_URL, json=final_json, headers=headers)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def send_shipment_time_stamp(shipment_id, milestone):
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
        return (
            f"""<?xml version='1.0' encoding='UTF-8'?>
            <soapenv:envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\">
                <soapenv:body>
                    <ser-root:ib_sl_rcptwebserviceresponse xmlns:ser-root=\"http://localhost/IB_SL_RcptWebService.services\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">
                        <responsemessage>a925e6e4-d162-4788-9ed4-6d5e2f309746</responsemessage>
                        <responseerror>0</responseerror>
                    </ser-root:ib_sl_rcptwebserviceresponse>
                </soapenv:body>
            </soapenv:envelope>""",
            200,
        )

    API_URL = f"{TIMESTAMP_API_BASE_URL}/dgff-eip-ws-soap/ib_sl_rcptwebservice"

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "IB_SL_RcptWebService_services_invokeWebService_Binder_IB_SL_RcptWebService",
        "DHL-API-Key": DHL_API_KEY,
    }

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

    response = requests.post(API_URL, data=body, headers=headers)

    print(response.content)

    return response.content, response.status_code


def send_shipment_update_json(final_json, shipment_id):
    """
    Send Output JSON to shipment update APIs

    Args:
        final_json (dict): JSON data to be sent.
        shipment_id (str): Which update is to be sent.

    Returns:
        response_json (dict): API response JSON.
        status_code (int): API status code.
        packline_error (bool): Flag for packline error occurred.

    Process Details:
        - Get response_json, status_code and shipment_id from 'validate_shipment_id' using shipment_id.
        - call 'get_shipment_package_details' to fetch shipment data if the shipment ID is valid.
        - If valid shipment_data exists then update the final_json using 'update_shipment_data'.
        - define API_URL using shipment ID.
        - Retrieve access token for authentication.
        - Send PATCH requests to the Customs API with the updated final_json.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined response.
    """
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return (
            {
                "shipmentID": "DUMMYBSJO000140",
            },
            200,
            True,
        )

    response_json, status_code, shipment_id = validate_shipment_id(shipment_id)

    if not shipment_id:
        packline_error = False
        return response_json, status_code, packline_error

    print(f"{shipment_id=}")

    shipment_data, status_code, packline_error = get_shipment_package_details(
        shipment_id
    )

    if status_code not in {200, 404}:
        return response_json, status_code, packline_error

    if shipment_data:
        try:
            final_json = update_shipment_data(shipment_data, final_json)
        except Exception as e:
            print("shipment_data_update_failed {}".format(e))
            print(traceback.print_exc())

    API_URL = (
        f"{CUSTOMS_API_BASE_URL}/dgff/transportation/shipment-booking/{shipment_id}"
    )
    token = get_customs_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("Calling ShipmentUpdate API...")
    response = requests.patch(API_URL, json=final_json, headers=headers)
    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    if status_code == 200 and response_json.get("shipmentID") is None:
        response_json["shipmentID"] = shipment_id

    return response_json, status_code, packline_error


def validate_shipment_id(shipment_id):
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

    # if it's not a valid shipment_id it's a house bill number which we will use to fetch shipment ID
    if is_housebill:
        response_json, status_code = get_housebill_info(shipment_id)
    else:
        # check if it's a valid shipmeent ID
        response_json, status_code = get_shipment_info(shipment_id)

    if status_code == 200:
        valid_shipment_id = response_json.get("SHIPMENTID")

    return response_json, status_code, valid_shipment_id


def get_housebill_info(housebill):
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
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {
            "SHIPMENTID": "DUMMYBSJO000140",
        }, 200

    URL = f"{ICAP_API_URL}/tms-services/getHousebillInfo"

    headers = {"edm_api_key": EDM_API_KEY}
    data = {
        "houseBill": housebill,
        "fieldNames": "SHIPMENTID",
    }

    print("Calling getHousebillInfo API...")
    response = requests.post(URL, headers=headers, json=data)

    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def get_shipment_info(shipment_id):
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
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return {"SHIPMENTID": "DUMMYBSJO000140"}, 200

    URL = f"{ICAP_API_URL}/tms-services/getShipmentInfo"

    headers = {"edm_api_key": EDM_API_KEY}
    data = {
        "shipmentId": shipment_id,
        "fieldNames": "SHIPMENTID",
    }

    print("Calling getShipmentInfo API...")
    response = requests.post(URL, headers=headers, json=data)

    print_api_response(response)

    status_code = response.status_code
    response_json = response.json()

    return response_json, status_code


def get_shipment_package_details(shipment_id):
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
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        response_json = [
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
        ]
        packline_error = False
        return response_json, 200, packline_error

    URL = f"{ICAP_API_URL}/tms-services/getShipmentPackageDetails"
    headers = {"edm_api_key": EDM_API_KEY}
    json = {
        "shipmentId": shipment_id,
        "fieldNames": "PACKAGEID,PACKAGE_TYPE,PACKAGE_COUNT,COMMODITY_CODE,GOODS_DESCRIPTION,GOODS_VALUE,GOODS_CURRENCY,GROSS_WEIGHT_UOM,GROSS_WEIGHT,PACKAGE_VOLUME,PACKAGE_VOLUME_UOM,PACKAGE_LENGTH,PACKAGE_WIDTH,PACKAGE_HEIGHT,DIMENSIONS_UOM",
    }

    print("Calling getShipmentPackageDetails API...")
    response = requests.post(URL, headers=headers, json=json)
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


def upload_document_to_edm(
    file_path, document_type, customs_clearance_number, filing_country
):
    """
    Upload document to EDM via API.

    Args:
        file_path (str): File to be uploaded.
        document_type (str): Type of the document.
        customs_clearance_number (int): Customs clearance number associated with the document.
        filing_country (str): Country associated with the customs filing.

    Returns:
        status_code (int): API status code.

    Process Details:
        - Define API_URL and headers.
        - Prepare document information as JSON string.
        - Open the file then attach it to the form data, and send POST requests to the API.
        - Close the file after sending the request.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined status_code.
    """
    if MOCK_ASSEMBLY_APIS:
        return 200

    URL = f"{ICAP_API_URL}/icapdocuploadservice/docUploadToCW1"

    headers = {"edm_api_key": EDM_API_KEY}
    doc_info = {
        "ShipmentID": customs_clearance_number,
        "DocumentType": document_type,
        "OriginCountry": filing_country,
    }
    form_data = {"documentinfo": json.dumps(doc_info)}

    opened_file = open(file_path, "rb")
    files = [("files", opened_file)]

    print("Calling adddocumenttoedm API...")
    response = requests.post(URL, headers=headers, data=form_data, files=files)

    opened_file.close()

    print_api_response(response)

    return response.status_code


def upload_document_to_usa(file_path, document_type, case_id):
    """
    Add document to usa API

    Uploads a document to the USA system via API, encoding the file in Base64 format.

    Args:
        file_path (str): File to be uploaded.
        document_type (str): Type of the document.
        case_id (str): Case ID associated with the document.

    Returns:
        status_code (int): API status code.

    Process Details:
        - Define API_URL and headers.
        - Read the file content then encode it in Base64 and prepare the document information.
        - Send POST requests with the document data as JSON.

    Notes:
        - If 'MOCK_ASSEMBLY_APIS' is enabled then return predefined status_code.
    """
    if MOCK_ASSEMBLY_APIS:
        return 200

    URL = f"{USA_API_BASE_URL}/uscdzicap/documentinfo"
    headers = {"api_key": USA_API_KEY, "caseid": case_id}

    # Read and encode the file content in base64
    with open(file_path, "rb") as opened_file:
        file_content = opened_file.read()
        encoded_file_content = base64.b64encode(file_content).decode("utf-8")

    file_name = os.path.basename(file_path)
    doc_info = {
        "splitdoc": "true" if "splitted" in file_name else "false",
        "documentName": file_name,
        "documentType": document_type,
        "documentContent": encoded_file_content,  # Base64 encoded file content
    }

    print("Calling adddocumenttousa API...")
    response = requests.post(URL, headers=headers, json=doc_info)
    print_api_response(response)

    return response.status_code


def get_fcm_token():
    API_URL = f"{CUSTOMS_API_BASE_URL}/auth/v1/token"
    token_response = requests.post(
        API_URL,
        data={"grant_type": "client_credentials"},
        auth=(FCM_CLIENT_ID, FCM_CLIENT_SECRET),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_response.status_code != 200:
        raise Exception("Failed to get token:", token_response.text)

    access_token = token_response.json().get("access_token")
    return access_token


def upload_fcm_document_to_edm(file_path, document_type, fcmID):
    mock_api = get_developer_settings("Mock API")
    if mock_api:
        return 200

    API_URL = f"{CUSTOMS_API_BASE_URL}/dgff/freight-chain-manager/attachment"

    with open(file_path, "rb") as opened_file:
        file_content = opened_file.read()
        encoded_file_content = base64.b64encode(file_content).decode("utf-8")
    file_name = os.path.basename(file_path)
    doc_info = {
        "bodyData": {
            "filename": f"ICAP_{file_name}",
            "type": document_type,
            "content": encoded_file_content,
            "transportRequest": {"fcmId": fcmID},
        }
    }
    token = get_fcm_token()

    headers = {"Authorization": f"Bearer {token}"}

    print("Calling adddocumentto FCM API...")
    response = requests.post(API_URL, headers=headers, json=doc_info)

    opened_file.close()

    print_api_response(response)

    return response.status_code
