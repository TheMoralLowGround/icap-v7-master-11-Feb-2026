import traceback
from .utils import (
    convert_value,
    extract_key_value,
    clean_empty_fields,
    map_notes
)


def map_charges(final_json):
    payer_code_fields = [
        ("chargesAmount", "amount", float),
        ("chargesCode", "code", str),
        ("chargesCurrencyCode", "currencyCode", str),
        ("chargesPrepaidCollectCode", "prepaidCollectCode", str)
    ]
    charges = extract_key_value(final_json, payer_code_fields)
    if charges:
        final_json["charges"] = [charges]

    return final_json


def map_basic_keys(final_json):
    basic_fields = {
        "exitPortCode": str,
        "filingBranchCode": str,
        "incoterms": str,
        "invoiceNumber": str,
        "issueDate": str,
        "netWeight": float,
        "netWeightUom": str,
        "originCountryCode": str,
        "originStateCode": str,
        "parentReference": str,
        "_PONumber": str,
        "totalAmount": float,
        "totalAmountCurrencyCode": str,
        "totalPackages": float,
        "totalWeight": float,
        "totalWeightUom": str,
        "valuationCode": str,
        "valuationDate": str,
        "valueForDutyCode": str,
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

        basic_row_fields = {
            "concessionOrder": str,
            "customerPackageID": str,
            "customsProcedureCode": str,
            "customsQuantity": float,
            "customsQuantityUom": str,
            "customsSecondQuantity": float,
            "customsSecondQuantityUom": str,
            "customsThirdQuantity": float,
            "customsThirdQuantityUom": str,
            "_ECCN": str,
            "entryInstructionStyle": str,
            "exportCode": str,
            "orderNumber": str,
            "licenseNumber": str,
            "licenseType": str,
            "licenseValue": float,
            "lineNumber": float,
            "originCountryCode": str,
            "originIndicator": str,
            "originStateCode": str,
            "preferenceCode": str,
            "previousMRN": str,
            "previousMRNLine": float,
            "price": float,
            "productCode": str,
            "_ROOCertificate": str,
            "supplementaryCode1": str,
            "supplementaryCode2": str,
            "tariffType": str,
            "treatmentCode": str,
            "valueForDutyCode": str
        }
        for field, field_type in basic_row_fields.items():
            if field in list(row.keys()):
                value = convert_value(row[field], field_type)
                if value is not None:
                    row[field] = value
                else:
                    row.pop(field, None)

        # goodsDetails mapping
        goods_details = {}
        goods_details_fields = {
            "commodityCode": str,
            "goodsDescription": str,
            "grossWeight": float,
            "grossWeightUom": str,
            "harmonizedCode": str,
            "marksAndNumbers": str,
            "netWeight": float,
            "netWeightUom": str,
            "packageCount": float,
            "packageType": str,
            "volume": float,
            "volumeUom": str
        }
        for field, field_type in goods_details_fields.items():
            if row.get(field):
                value = convert_value(row.get(field), field_type)
                row.pop(field, None)
                if value is not None:
                    goods_details[field] = value

        if goods_details:
            row["goodsDetails"] = goods_details
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
        final_json = map_charges(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_notes(final_json)
    except:
        print(traceback.format_exc())

    return final_json


def handle_table(final_json, main_table):
    line_items = []
    try:
        for table in main_table:
            rows = table["rows"]
            for row in rows:
                row_data = structure_row_data(row)
                if row_data:
                    line_items.append(row_data)
    except:
        print(traceback.format_exc())

    if line_items:
        final_json["lineItems"] = line_items

    return final_json


def handle_civ_output(final_json, main_table):

    try:
        final_json = handle_table(final_json, main_table)
    except:
        print(traceback.format_exc())

    try:
        final_json = handle_keys(final_json)
    except:
        print(traceback.format_exc())

    return final_json
