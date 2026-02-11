import os

import requests

UTILITY_ENGINE_API_URL = os.getenv("UTILITY_ENGINE_API_URL")


def postal_parse_address(address):
    """
    Consume Address parser API
    """
    try:
        resp = requests.post(
            f"{UTILITY_ENGINE_API_URL}/parse_address", json={"address": address}
        )
        resp.raise_for_status()
        response_json = resp.json()
        parser_result = response_json["data"]
        return parser_result
    except Exception as error:
        print(error)
        return []
