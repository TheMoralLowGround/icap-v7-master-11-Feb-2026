import traceback
from .utils import (
    convert_value,
    extract_key_value,
    clean_empty_fields,
    map_notes,
    map_references,
)


def shift_bool_fields(final_json):
    if "_DGFDeliver" in final_json.keys():
        data = {"_DGFDeliver": convert_value(final_json.pop("_DGFDeliver"), bool)}
        if "delivery" in final_json.keys():
            final_json["delivery"].update(data)
        else:
            final_json["delivery"] = data

    if "_DGFPickup" in final_json.keys():
        data = {"_DGFPickup": convert_value(final_json.pop("_DGFPickup"), bool)}
        if "pickup" in final_json.keys():
            final_json["pickup"].update(data)
        else:
            final_json["pickup"] = data

    return final_json


def map_service(final_json):

    service = {}
    service_fields = [
        ("serviceType", "type", str),
        ("serviceRequestedDate", "requestedDate", str),
        ("serviceCompletedDate", "completedDate", str),
        ("serviceDuration", "duration", str),
        ("serviceContractor", "contractor", str),
        ("serviceCount", "count", int)
    ]
    service = extract_key_value(final_json, service_fields)

    if final_json.get("serviceLocation"):
        service["location"] = final_json.pop("serviceLocation")

    if service:
        final_json["service"] = [service]

    return final_json


def map_parties(final_json):
    parties = []
    party_types = [
        "controllingAgent",
        "arrivalCFSAddress",
        "deliveryAgent",
        "deliveryLocalCartage",
        "importBroker",
        "departureCFSAddress",
        "exportBroker",
        "pickupAgent",
        "pickupLocalCartage",
        "localClient"
    ]
    for party_type in party_types:
        if party_type in list(final_json.keys()):
            party_data = final_json[party_type]
            if isinstance(party_data, dict):
                party_data["partyType"] = party_type[0].upper() + party_type[1:]

                parties.append(party_data)
                final_json.pop(party_type, None)

    if parties:
        final_json["parties"] = parties

    return final_json


def map_other_keys(final_json):

    if final_json.get("pickup"):
        pickup = final_json.pop("pickup")
        if final_json.get("pickupDropMode"):
            pickup["dropMode"] = final_json.pop("pickupDropMode")
        final_json["pickup"] = pickup

    return final_json


def map_customs_entries(final_json):
    customs_entries = []
    for key in list(final_json.keys()):
        # Handle flat "customsEntries.TYPE" format
        if key.startswith("customsEntries."):
            entry_type = key.split("customsEntries.", 1)[1]
            entry_number = final_json[key]
            customs_entries.append(
                {
                    "type": entry_type,
                    "number": entry_number
                }
            )
            final_json.pop(key, None)

    if customs_entries:
        final_json["customsEntries"] = customs_entries

    return final_json


def map_basic_keys(final_json):

    basic_fields = {
        "_DGFInsure": bool,
        "assembly": bool,
        "destinationControlled": bool,
        "valueOfGoods": float,
        "insuranceValue": float,
        "totalChargeable": float,
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

        basic_row_fields = [
            ("goodsLineID", str),
            ("packageCount", int),
            ("packageType", str),
            ("packageID", str),
            ("grossWeight", float),
            ("grossWeightUom", str),
            ("volume", float),
            ("volumeUom", str),
            ("innerPackageCount", int),
            ("innerPackageType", str),
            ("loadingMeters", float),
            ("marksAndNumbers", str),
            ("goodsDescription", str),
            ("commodityCode", str),
            ("harmonizedCode", str),
            ("originCountryCode", str),
            ("productCode", str),
            ("loadingDate", str)
        ]
        for field, field_type in basic_row_fields:
            if field in list(row.keys()):
                value = convert_value(row[field], field_type)
                if value is not None:
                    row[field] = value
                else:
                    row.pop(field, None)

        # Customs classification mapping
        customs_classification_fields = [
            ("customsClassificationCountryCode", "countryCode", str),
            ("customsClassificationCode", "code", str)
        ]
        customs_classification = extract_key_value(row, customs_classification_fields)
        if customs_classification:
            row["customsClassification"] = [customs_classification]

        # Dimensions mapping
        dimensions = {}
        dimension_fields = [
            ("dimensionsUom", str),
            ("length", float),
            ("width", float),
            ("height", float)
        ]
        for target_field, field_type in dimension_fields:
            if row.get(target_field):
                value = convert_value(row.get(target_field), field_type)
                row.pop(target_field, None)
                if value is not None:
                    dimensions[target_field] = value

        if dimensions:
            row["dimensions"] = dimensions

        # Temperatures mapping
        temperature_fields = [
            ("requiresTemperatureControl", "requiresTemperatureControl", bool),
            ("requiredMinimum", "requiredMinimum", float),
            ("requiredMaximum", "requiredMaximum", float),
            ("temperatureUom", "uom", str)
        ]
        temperatures = extract_key_value(row, temperature_fields)
        if temperatures:
            row["temperatures"] = temperatures

        # Hazardous material mapping
        hazardous_material = {}
        haz_mat_basic_fields = [
            ("_UNDGNumber", "_UNDGNumber", str),
            ("_IMOClassCode", "_IMOClassCode", int),
            ("properShippingname", "properShippingname", str),
            ("technicalName", "technicalName", str),
            ("marinePollutant", "marinePollutant", str),
            ("packingInstructionSection", "packingInstructionSection", str),
            ("hazardousMaterialPackageCount", "packageCount", int),
            ("hazardousMaterialPackageType", "packageType", str),
            ("hazardousMaterialGrossWeight", "grossWeight", float),
            ("hazardousMaterialGrossWeightUom", "grossWeightUom", str),
            ("hazardousMaterialVolume", "volume", float),
            ("hazardousMaterialVolumeUom", "volumeUom", str)
        ]
        hazardous_material = extract_key_value(row, haz_mat_basic_fields)

        # Flashpoint temperature mapping
        flashpoint_fields = [
            ("flashPointTemperatureUom", "uom", str),
            ("flashPointTemperatureText", "text", float)
        ]
        flashpoint = extract_key_value(row, flashpoint_fields)
        if flashpoint:
            hazardous_material["flashpointTemperature"] = flashpoint

        # Contact mapping
        haz_mat_contact_fields = [
            ("hazardousMaterialContactName", "name", str),
            ("hazardousMaterialContactPhone", "phone", str),
            ("hazardousMaterialContactEmail", "email", str)
        ]
        haz_mat_contact = extract_key_value(row, haz_mat_contact_fields)
        if haz_mat_contact:
            hazardous_material["contact"] = haz_mat_contact

        if hazardous_material:
            row["hazardousMaterial"] = [hazardous_material]
    except:
        print(traceback.format_exc())

    return row


def handle_keys(final_json):

    try:
        final_json = clean_empty_fields(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = shift_bool_fields(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_basic_keys(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_service(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_customs_entries(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_parties(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_references(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_notes(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_other_keys(final_json)
    except:
        print(traceback.format_exc())

    return final_json


def handle_table(final_json, main_table):
    goods_lines = []
    try:
        for table in main_table:
            rows = table["rows"]
            for row in rows:
                row_data = structure_row_data(row)
                if row_data:
                    goods_lines.append(row_data)
    except:
        print(traceback.format_exc())

    if goods_lines:
        final_json["goodsLines"] = goods_lines

    return final_json


def handle_shipment_output(final_json, main_table):

    try:
        final_json = handle_table(final_json, main_table)
    except:
        print(traceback.format_exc())

    try:
        final_json = handle_keys(final_json)
    except:
        print(traceback.format_exc())

    return final_json
