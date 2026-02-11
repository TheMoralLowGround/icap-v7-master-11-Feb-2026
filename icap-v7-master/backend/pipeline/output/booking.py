import traceback
from .utils import (
    convert_value,
    extract_key_value,
    clean_empty_fields,
    map_notes,
    map_references
)


def map_compound_keys(final_json):
    compound_keys = ["housebill", "masterbill"]
    integer_keys = ["totalPackages"]
    float_keys = ["totalWeight", "totalVolume"]
    for key in compound_keys:
        compound_data = {}
        for k, v in list(final_json.items()):
            if k.startswith(key):
                clean_key = k.replace(key, "", 1)
                clean_key = clean_key[0].lower() + clean_key[1:]
                if clean_key in integer_keys:
                    v = convert_value(v, int)
                elif clean_key in float_keys:
                    v = convert_value(v, float)
                compound_data[clean_key] = v
                final_json.pop(k, None)

        if compound_data:
            final_json[key] = compound_data

    return final_json


def map_transport_legs(final_json):
    integer_keys = [ "sequenceNumber"]
    transport_legs_data = {}
    for key, value in final_json.items():
        if value and key.startswith("transportLegs"):
            clean_key = key.replace("transportLegs", "", 1)
            clean_key = clean_key[0].lower() + clean_key[1:]
            if clean_key in integer_keys:
                value = convert_value(value, int)
            transport_legs_data[clean_key] = value
            final_json.pop(key, None)

    if final_json.get("carrier"):
        transport_legs_data["carrier"] = final_json.pop("carrier")

    if transport_legs_data:
        final_json["transportLegs"] = [transport_legs_data]

    return final_json


def map_service(final_json):
    service = {}
    service_fields = [
        ("serviceType", "type", str),
        ("serviceRequestedDate", "requestedDate", str),
        ("serviceCompletedDate", "completedDate", str),
        ("serviceDuration", "duration", str),
        ("serviceContractor", "contractor", str),
        ("serviceCount", "count", int),
        ("serviceReference", "reference", str),
        ("serviceNotes", "notes", str),
    ]
    service = extract_key_value(final_json, service_fields)

    if final_json.get("serviceLocation"):
        service["serviceLocation"] = final_json.pop("serviceLocation")

    if service:
        final_json["service"] = [service]

    return final_json


def map_parties(final_json):
    parties = []
    party_types = [
        "supplier",
        "importer",
        "forwarder",
        "declarant",
        "seller",
        "representative",
        "notify",
        "manufacturer",
        "externalBroker",
        "exporter",
        "depot",
        "customsWarehouse",
        "CTO",
        "controllingCustomer",
        "controllingAgent",
        "containerYard",
        "carrier"
    ]
    for party_type in party_types:
        if party_type in list(final_json.keys()):
            party_data = final_json[party_type]
            party_data["partyType"] = party_type[0].upper() + party_type[1:]

            parties.append(party_data)
            final_json.pop(party_type, None)

    if parties:
        final_json["parties"] = parties

    return final_json


def map_local_transports(final_json):
    local_transports_data = {}
    for key, value in final_json.items():
        if value and key.startswith("localTransports"):
            clean_key = key.replace("localTransports", "", 1)
            clean_key = clean_key[0].lower() + clean_key[1:]
            local_transports_data[clean_key] = value

    if final_json.get("transportCompany"):
        local_transports_data["transportCompany"] = final_json.pop("transportCompany")

    if final_json.get("transportLocation"):
        local_transports_data["transportLocation"] = final_json.pop("transportLocation")

    if local_transports_data:
        final_json["localTransports"] = [local_transports_data]

    return final_json


def handle_transportunits_table(final_json, main_table):
    transport_units_data = {}

    for table in main_table:
        for row in table.get("rows", []):
            try:
                if "transportUnitsTransportUnitID" not in row:
                    continue

                transport_unit_id = row["transportUnitsTransportUnitID"]

                if transport_unit_id not in transport_units_data:
                    transport_units_data[transport_unit_id] = {}

                for key, value in row.items():
                    if key.startswith("transportUnits"):
                        clean_key = key.replace("transportUnits", "", 1)
                        clean_key = clean_key[0].lower() + clean_key[1:]
                        transport_units_data[transport_unit_id][clean_key] = value
            except:
                print(traceback.format_exc())

    if transport_units_data:
        final_json["transportUnits"] = list(transport_units_data.values())

    return final_json


def handle_goodslines(final_json, main_table):
    goodslines_data = []
    for table in main_table:
        for row in table.get("rows", []):
            try:
                goodsline_data = {}
                for key, value in row.items():
                    if value and key.startswith("goodsLines"):
                        clean_key = key.replace("goodsLines", "", 1)
                        clean_key = clean_key[0].lower() + clean_key[1:]
                        goodsline_data[clean_key] = value

                if goodsline_data:
                    goodslines_data.append(goodsline_data)
            except:
                print(traceback.format_exc())

    if goodslines_data:
        final_json["goodsLines"] = goodslines_data

    return final_json


def handle_keys(final_json):

    try:
        final_json = clean_empty_fields(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_compound_keys(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_transport_legs(final_json)
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
        final_json = map_service(final_json)
    except:
        print(traceback.format_exc())

    try:
        final_json = map_local_transports(final_json)
    except:
        print(traceback.format_exc())

    return final_json


def handle_table(final_json, main_table):

    try:
        final_json = handle_transportunits_table(final_json, main_table)
    except:
        print(traceback.format_exc())

    try:
        final_json = handle_goodslines(final_json, main_table)
    except:
        print(traceback.format_exc())

    return final_json


def handle_booking_output(final_json, main_table):

    try:
        final_json = handle_table(final_json, main_table)
    except:
        print(traceback.format_exc())

    try:
        final_json = handle_keys(final_json)
    except:
        print(traceback.format_exc())

    return final_json
