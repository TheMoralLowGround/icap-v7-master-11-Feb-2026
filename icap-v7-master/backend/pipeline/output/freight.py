import traceback
from .utils import (
    convert_value,
    extract_key_value,
    clean_empty_fields,
    map_references,
    replace_keys
)

KEY_MAPPINGS = {
    "accountNumber": "id",
    "city": "cityName",
    "addressLine1": "street",
    "addressLine2": "additionalAddressInfo"
}

def map_additional_information(final_json):
    additional_information_fields = [
        ("additionalInformationCode", "code", str),
        ("additionalInformationStringValue", "stringValue", str),
        ("additionalInformationDateValue", "dateValue", str),
        ("additionalInformationNumericValue", "numericValue", float)
    ]
    additional_information = extract_key_value(final_json, additional_information_fields)

    if additional_information:
        final_json["additionalInformation"] = [additional_information]

    return final_json


def map_additional_services(final_json):
    additional_services_basic_fields = [
        ("additionalServicesDangerousGoods", "dangerousGoods", bool),
        ("additionalServicesPreAdvice", "preAdvice", bool),
        ("additionalServicesTailLiftLoading", "tailLiftLoading", bool),
        ("additionalServicesTailLiftUnloading", "tailLiftUnloading", bool),
        ("additionalServicesSideLoadingPickup", "sideLoadingPickup", bool),
        ("additionalServicesSideUnloadingDelivery", "sideUnloadingDelivery", bool),
        ("additionalServicesTimeSlotBookingPickup", "timeSlotBookingPickup", bool),
        ("additionalServicesTimeSlotBookingDelivery", "timeSlotBookingDelivery", bool),
        ("additionalServicesPriorityServiceP10", "priorityServiceP10", bool),
        ("additionalServicesPriorityServiceP12", "priorityServiceP12", bool),
        ("additionalServicesDropOffByConsignor", "dropOffByConsignor", bool),
        ("additionalServicesAfter12Delivery", "after12Delivery", bool)
    ]
    additional_services = extract_key_value(final_json, additional_services_basic_fields)

    # cashOnDelivery mapping
    cash_on_delivery_fields = [
        ("additionalServicesCashOnDeliveryAmount", "amount", int),
        ("additionalServicesCashOnDeliveryCurrency", "currency", str)
    ]
    cash_on_delivery = extract_key_value(final_json, cash_on_delivery_fields)

    if cash_on_delivery:
        additional_services["cashOnDelivery"] = cash_on_delivery

    # insurance mapping
    insurance_fields = [
        ("additionalServicesInsuranceValue", "value", float),
        ("additionalServicesInsuranceCurrency", "currency", str)
    ]
    insurance = extract_key_value(final_json, insurance_fields)

    if insurance:
        additional_services["insurance"] = insurance

    # highValueShipment mapping
    high_value_shipment_fields = [
        ("additionalServicesHighValueShipmentValue", "value", float),
        ("additionalServicesHighValueShipmentCurrency", "currency", str)
    ]
    high_value_shipment = extract_key_value(final_json, high_value_shipment_fields)

    if high_value_shipment:
        additional_services["highValueShipment"] = high_value_shipment

    # thermoCold mapping
    thermo_cold_fields = [
        ("additionalServicesThermoColdMin", "min", float),
        ("additionalServicesThermoColdMax", "max", float)
    ]
    thermo_cold = extract_key_value(final_json, thermo_cold_fields)

    if thermo_cold:
        additional_services["thermoCold"] = thermo_cold

    # fixedDeliveryDate mapping
    fixed_delivery_date_fields = [
        ("additionalServicesFixedDeliveryDateDate", "date", str)
    ]
    fixed_delivery_date = extract_key_value(final_json, fixed_delivery_date_fields)

    if fixed_delivery_date:
        additional_services["fixedDeliveryDate"] = fixed_delivery_date

    # availablePickupTime mapping
    available_pickup_time_fields = [
        ("additionalServicesAvailablePickupTimeFromTime", "fromTime", str),
        ("additionalServicesAvailablePickupTimeToTime", "toTime", str)
    ]
    available_pickup_time = extract_key_value(final_json, available_pickup_time_fields)

    if available_pickup_time:
        additional_services["availablePickupTime"] = available_pickup_time

    # availableDeliveryTime mapping
    available_delivery_time_fields = [
        ("additionalServicesAvailableDeliveryTimeFromTime", "fromTime", str),
        ("additionalServicesAvailableDeliveryTimeToTime", "toTime", str)
    ]
    available_delivery_time = extract_key_value(final_json, available_delivery_time_fields)

    if available_delivery_time:
        additional_services["availableDeliveryTime"] = available_delivery_time
    
    if additional_services:
        final_json["additionalServices"] = additional_services

    return final_json


def map_parties(final_json):
    parties = []
    party_types = [
        "Consignor",
        "Pickup",
        "Consignee",
        "Delivery"
    ]

    for party_type in party_types:
        if party_type.lower() in list(final_json.keys()):
            party_data = final_json[party_type.lower()]
            party_data["type"] = party_type

            if "additionalAddressInfo" in list(party_data.keys()):
                if "address" in list(party_data.keys()):
                    party_data["address"]["additionalAddressInfo"] = party_data["additionalAddressInfo"]
                else:
                    party_data["address"] = {
                        "additionalAddressInfo": party_data["additionalAddressInfo"]
                    }
                party_data.pop("additionalAddressInfo", None)

            vat_data = {}
            vat_fields = {
                "vatCountryCode":"countryCode",
                "vatNumber": "number"
            }
            for key, value in vat_fields.items():
                if key in list(party_data.keys()):
                    vat_data[value] = party_data[key]
                    party_data.pop(key, None)

            if vat_data:
                party_data["vat"] = vat_data

            parties.append(party_data)
            final_json.pop(party_type.lower(), None)

    if parties:
        final_json["parties"] = parties

    return final_json


def map_payer_code(final_json):
    payer_code_fields = [
        ("payerCodeCode", "code", str),
        ("payerCodeLocation", "location", str)
    ]
    payer_code = extract_key_value(final_json, payer_code_fields)
    if payer_code:
        final_json["payerCode"] = payer_code

    return final_json


def map_basic_keys(final_json):
    basic_fields = {
        "id": str,
        "productCode": str,
        "pickupDate": str,
        "requestedDeliveryDate": str,
        "pickupInstruction": str,
        "deliveryInstruction": str,
        "totalNumberOfPieces": int,
        "totalWeight": float,
        "totalVolume": float,
        "totalLoadingMeters": float,
        "totalPalletPlaces": float,
        "goodsDescription": str,
        "goodsValue": float,
        "goodsValueCurrency": str
    }
    for field, field_type in basic_fields.items():
        if field in final_json:
            value = convert_value(final_json[field], field_type)
            if value is not None:
                final_json[field] = value
            else:
                final_json.pop(field, None)

    return final_json


def structure_row_data(row):
    """Transform flat row data into structured final_row format"""
    try:
        row = clean_empty_fields(row)

        if row.get("piecesId"):
            row["id"] = [row.pop("piecesId")]

        basic_row_fields = {
            "goodsType": str,
            "packageType": str,
            "marksAndNumbers": str,
            "numberOfPieces": int,
            "weight": float,
            "volume": float,
            "loadingMeters": float,
            "palletPlaces": int,
            "width": float,
            "height": float,
            "length": float,
            "stackable": bool
        }
        for field, field_type in basic_row_fields.items():
            if field in list(row.keys()):
                value = convert_value(row[field], field_type)
                if value is not None:
                    row[field] = value
                else:
                    row.pop(field, None)

        # Dangerous goods mapping
        dangerous_goods = {}
        dangerous_goods_fields = [
            ("dangerousGoodsDgmId", "dgmId", int),
            ("dangerousGoodsAdrClass", "adrClass", str),
            ("dangerousGoodsUnNumber", "unNumber", int),
            ("dangerousGoodsProperShippingName", "properShippingName", str),
            ("dangerousGoodsFlashpointValue", "flashpointValue", float),
            ("dangerousGoodsPackageGroup", "packageGroup", str),
            ("dangerousGoodsTunnelCode", "tunnelCode", str),
            ("dangerousGoodsGrossWeight", "grossWeight", float),
            ("dangerousGoodsQuantityMeasurementUnitQualifier", "quantityMeasurementUnitQualifier", str),
            ("dangerousGoodsQuantityMeasurementValue", "quantityMeasurementValue", float),
            ("dangerousGoodsNumberOfPieces", "numberOfPieces", int),
            ("dangerousGoodsPackageType", "packageType", str),
            ("dangerousGoodsOfficialNameTechDescription", "officialNameTechDescription", str),
            ("dangerousGoodsMarinePollutant", "marinePollutant", bool),
            ("dangerousGoodsMarinePollutantName", "marinePollutantName", str),
            ("dangerousGoodsExceptedQuantity", "exceptedQuantity", bool),
            ("dangerousGoodsLimitedQuantity", "limitedQuantity", bool),
            ("dangerousGoodsEmptyContainer", "emptyContainer", bool),
            ("dangerousGoodsEnvironmentHazardous", "environmentHazardous", bool),
            ("dangerousGoodsWaste", "waste", bool)
        ]
        for source_field, target_field, field_type in dangerous_goods_fields:
            if row.get(source_field):
                value = convert_value(row.get(source_field), field_type)
                row.pop(source_field, None)
                if value is not None:
                    dangerous_goods[target_field] = value

        if dangerous_goods:
            row["dangerousGoods"] = [dangerous_goods]
    except:
        print(traceback.format_exc())

    return row


def handle_keys(final_json):

    try:
        final_json = clean_empty_fields(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_basic_keys(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_references(final_json, project="freight")
    except:
        print(traceback.format_exc())

    try:
        final_json = map_payer_code(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_parties(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_additional_services(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_additional_information(final_json)
    except:
        print(traceback.format_exc())

    return final_json


def handle_table(final_json, main_table):
    pieces = []
    try:
        for table in main_table:
            rows = table["rows"]
            for row in rows:
                row_data = structure_row_data(row)
                if row_data:
                    pieces.append(row_data)
    except:
        print(traceback.format_exc())

    if pieces:
        final_json["pieces"] = pieces

    return final_json


def handle_freight_output(final_json, main_table):

    try:
        final_json = handle_table(final_json, main_table)
    except:
        print(traceback.format_exc())

    try:
        final_json = handle_keys(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = replace_keys(final_json, KEY_MAPPINGS)
    except:
        print(traceback.format_exc())

    return final_json
