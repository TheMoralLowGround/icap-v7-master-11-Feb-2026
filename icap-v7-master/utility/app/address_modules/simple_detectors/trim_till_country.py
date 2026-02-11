"""
Address Trimming Script
========================

Purpose:
--------
This script provides utility functions for processing and trimming address strings. The main functionality involves identifying country names within an address and trimming the address text up to the last occurrence of the country name.

Functions:
----------
1. **trim_text(text, substring)**:
   Trims the input `text` up to the last occurrence of the specified `substring`.
   - **Parameters**:
     - `text` (str): The input text to be trimmed.
     - `substring` (str): The substring to search for.
   - **Returns**:
     - A trimmed string containing only the part of `text` up to the last occurrence of `substring`. If the substring is not found, returns the original `text`.

2. **trim_address(address)**:
   Trims an address string to include content only up to the last detected country name.
   - **Parameters**:
     - `address` (str): The full address string to be processed.
   - **Returns**:
     - A trimmed address string containing content up to the last detected country name. If no country is detected, the original `address` is returned.
   - **Workflow**:
     1. Uses `GeoText` to detect countries in the address.
     2. If `GeoText` fails to detect any countries, checks against the `pycountry` library to find country names present in the address.
     3. Calls `trim_text()` to trim the address text up to the last detected country name.

Additional Features:
---------------------
- **Error Handling**:
  Ensures exceptions are logged via `traceback` and returns the original address in case of errors.
- **Extensibility**:
  Can be easily extended to support additional trimming rules or address processing logic.

Usage:
------
1. Import the script and call `trim_address()` with an address string:
   ```python
   trimmed_address = trim_address("123 Main Street, New York, USA")
   print(trimmed_address)  # Output: "123 Main Street, New York, USA"
"""


import re
import traceback

import pycountry
from geotext import GeoText


def trim_text(text, substring):
    index = text.lower().rfind(substring.lower())
    if index != -1:
        trimmed_text = text[: index + len(substring)]
        return trimmed_text.strip()
    else:
        return text


def trim_address(address):
    """
    Trims an address text till last occurance of the country

    """
    try:
        places = GeoText(address)
        countries = places.countries
        if not countries:
            countries = [
                country.name
                for country in pycountry.countries
                if country.name.lower() in address.lower()
            ]
        if countries:
            return trim_text(address, countries[-1])
            # country = countries[-1]  # Get the last detected country
            # last_country_index = address.rfind(country)
            # trimmed_address = address[:last_country_index + len(country)].strip()
            # return trimmed_address
        else:
            return address
    except:
        print(traceback.print_exc())
        return address
