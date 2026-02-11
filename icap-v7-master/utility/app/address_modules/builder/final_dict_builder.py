"""
FinalDictBuilder Class
=======================

Purpose:
--------
The `FinalDictBuilder` class is designed to process and structure address-related data into a standardized dictionary format. It provides a comprehensive set of methods for handling address fields, parsing, cleaning, and enriching address data.

Attributes:
-----------
- `required_address_fields`: List of essential address fields that must be included in the final dictionary.
- `address_text`: String containing the raw address text.
- `address_line_list`: List containing individual lines of the address.
- `final_dict`: Dictionary that holds the final structured address data.
- `tbr`: List to store lines to be removed from `address_line_list` after processing.

Methods:
--------
1. **set_company_name(company_name, company_line_index, missing_company_suffixes)**:
   Processes and sets the company name in the final dictionary. Handles cases where the company name is missing or located in specific lines.

2. **set_address_fields(parser_dict)**:
   Adds parsed address fields to the final dictionary, focusing only on required fields.

3. **set_postcode()**:
   Identifies and sets the postcode in the final dictionary, ensuring it is numeric and derived from relevant address lines.

4. **set_address_lines()**:
   Sets the first line and remaining lines of the address into `addressLine1` and `addressLine2` fields, respectively.

5. **set_country_name(replace_country_name)**:
   Replaces the country name in the final dictionary with a translated value if applicable.

6. **set_country_code(country_map)**:
   Converts the country name to its ISO2 code using a provided country map and updates the final dictionary.

7. **clean_final_dict()**:
   Cleans and formats all fields in the final dictionary. Ensures proper capitalization and standardization of values.

8. **set_consignee_account_number()**:
   Formats the `consigneeAccountNumber` field in the final dictionary to uppercase.

9. **set_account_number()**:
   Copies and formats the `consigneeAccountNumber` as `accountNumber` in the final dictionary.

10. **set_state_province()**:
    Renames the `state` field in the final dictionary to `stateProvince`.

11. **set_postal_code()**:
    Renames the `postcode` field in the final dictionary to `postalCode`.

12. **set_name()**:
    Formats the `name` field in the final dictionary to uppercase.

13. **remove_detected_lines_from_address_line_list()**:
    Removes lines from `address_line_list` that match values already present in the final dictionary.

14. **special_exclusion_check(s)** (static method):
    Determines whether a string meets the minimum length requirement for inclusion.

15. **get_iso2(input_country_name, country_map)** (static method):
    Retrieves the ISO2 code for a given country name from the provided country map.

16. **get_address_text()**:
    Returns the raw `address_text`.

17. **get_address_line_list()**:
    Returns the `address_line_list` after processing.
"""
import re


class FinalDictBuilder:
    required_address_fields = ["city", "block", "country", "postcode", "state"]

    def __init__(
        self, address_text: str, address_line_list: list, final_dict: dict, tbr: list
    ):
        self.address_text = address_text
        self.address_line_list = address_line_list
        self.final_dict = final_dict
        self.tbr = tbr

    def set_company_name(
        self, company_name: str, company_line_index: any, missing_company_suffixes: list
    ):
        if company_name:
            self.address_text = self.address_text.replace(company_name, "")
            self.final_dict["name"] = company_name

        elif company_line_index:
            index_ = int(company_line_index) - 1
            company_name = self.address_line_list[index_]
            self.final_dict["name"] = company_name
            self.address_text = self.address_text.replace(company_name, "")

        else:
            # if no company_names are found first check for missing company suffixes
            for line in self.address_line_list:
                if any(suffix in line.lower() for suffix in missing_company_suffixes):
                    if not line.lower().startswith("limited"):
                        company_name = line
                        self.final_dict["name"] = company_name
                        self.tbr.append(line)
            if not company_name:
                company_name = self.address_line_list[0]
                self.address_line_list = self.address_line_list[1:]
                self.final_dict["name"] = company_name

    def set_address_fields(self, parser_dict: dict):
        for key, value in parser_dict.items():
            if key in self.required_address_fields:
                self.final_dict[key] = value

    def set_postcode(self, project):
        if (
            "postcode" in self.final_dict.keys()
            and self.final_dict["postcode"].isnumeric() == False
        ):  # Please make sure the key is there in the first place @Emon28/07/22
            self.final_dict.pop("postcode")

        city_holder = self.final_dict.get("city")
        if not city_holder and project.lower() == "freight":
            for line_idx, line in enumerate(self.address_line_list):
                postcode = re.match(r"^\d+", line)
                match = re.search(r"(?<=-)[A-Za-z]+", line)

                if postcode:
                    self.final_dict["city"] = match.group().lower()
                    city_holder = match.group().lower()

        if city_holder:
            for line_idx, line in enumerate(self.address_line_list):
                if city_holder in line.lower():

                    def get_only_digits(s):
                        t = ""
                        for i, c in enumerate(s):
                            if c.isspace() or c.isdigit():
                                t += c
                            elif c == "-":
                                if s[i - 1].isdigit() and s[i + 1].isdigit():
                                    t += c
                        # print(s, ' converted to ', t)
                        return t

                    text_with_digits = get_only_digits(line).strip()
                    digit_list = text_with_digits.split(" ")
                    suggested_postcode = max(digit_list)

                    if len(suggested_postcode) > 2:
                        self.final_dict["postcode"] = suggested_postcode

                    if "-" in text_with_digits:
                        # print(text_with_digits)
                        self.final_dict["postcode"] = text_with_digits
                        break
                if project.lower() == "freight":
                    postal_code_pattern = r"\b\d{4}-\d{3}\b"
                    match = re.search(postal_code_pattern, line)
                    if match:
                        self.final_dict["postcode"] = match.group(0)
                        break

    def set_address_lines(self):
        address_line_1 = None
        rest_address_lines = []

        for i, line in enumerate(self.address_line_list):
            if "".join(char for char in line if char.isalnum()) != "":
                if i == 0:
                    address_line_1 = line
                else:
                    rest_address_lines.append(line)

        if address_line_1:
            self.final_dict["addressLine1"] = address_line_1
            if rest_address_lines:
                self.final_dict["addressLine2"] = " ".join(rest_address_lines)

    def set_country_name(self, replace_country_name):
        if "country" in self.final_dict.keys():
            country_name = self.final_dict["country"]

            for value in replace_country_name:
                if value["original_value"].lower() in country_name.lower():
                    self.final_dict["country"] = value["translate_value"]

    def set_country_code(self, country_map):
        if "country" in self.final_dict.keys():
            country_name = self.final_dict["country"]

            if self.get_iso2(country_name, country_map) != country_name:
                self.final_dict["countryCode"] = self.final_dict.pop("country")
                self.final_dict["countryCode"] = self.get_iso2(
                    country_name, country_map
                )

    def clean_final_dict(self):
        for key, value in self.final_dict.items():
            self.final_dict[key] = value.strip()
            words = value.split()
            if len(words) == 1:
                """if a word inside a line is less than 4 chars in length make it Upper
                Eg. usa to USA. Else use title function"""
                if len("".join(char for char in value if char.isalnum())) < 4:
                    self.final_dict[key] = value.upper()
                else:
                    self.final_dict[key] = value.title()
            else:
                for word_idx, word in enumerate(words):
                    if len("".join(char for char in word if char.isalnum())) < 4:
                        word = word.upper()
                    else:
                        word = word.capitalize()
                    words[word_idx] = word

                value = (" ").join(words)
                self.final_dict[key] = value

    def set_consignee_account_number(self):
        if "consigneeAccountNumber" in self.final_dict:
            self.final_dict["consigneeAccountNumber"] = self.final_dict[
                "consigneeAccountNumber"
            ].upper()

    def set_account_number(self):
        if "consigneeAccountNumber" in self.final_dict:
            consignee_account_number_value = self.final_dict[
                "consigneeAccountNumber"
            ].upper()
            self.final_dict["accountNumber"] = consignee_account_number_value

    def set_state_province(self):
        if "state" in self.final_dict.keys():
            self.final_dict["stateProvince"] = self.final_dict.pop("state")

    def set_postal_code(self):
        if "postcode" in self.final_dict.keys():
            self.final_dict["postalCode"] = self.final_dict.pop("postcode")

    def set_name(self):
        if "name" in self.final_dict.keys():
            self.final_dict["name"] = self.final_dict["name"].upper()

    def remove_detected_lines_from_address_line_list(self):
        final_values = []
        primary_final_values = list(self.final_dict.values())
        for elem in primary_final_values:
            words_in_elem = elem.strip().split()
            final_values.extend(words_in_elem)

        # removing detected lines form the address line list
        for line_idx, line in enumerate(self.address_line_list):
            line_to_be_checked = line.strip().lower()
            words = line_to_be_checked.split()
            match_count = 0
            for word in words:
                if word in final_values:
                    match_count += 1
            if len(words) <= match_count:
                self.tbr.append(line)
            elif len(words) == 1:
                if any(value.lower() == line_to_be_checked for value in final_values):
                    self.tbr.append(line)
        temp_address_line_list = [
            x for x in self.address_line_list if x not in self.tbr
        ]
        self.address_line_list.clear()
        self.address_line_list.extend(temp_address_line_list)

    @staticmethod
    def special_exclusion_check(s: str):
        return len(s.strip()) >= 3

    @staticmethod
    def get_iso2(input_country_name, country_map):
        country_data = country_map["Country"]
        for country_name, data in country_data.items():
            if country_name.lower() == input_country_name.lower():
                return data["ISO2"]
        return input_country_name

    def get_address_text(self):
        return self.address_text

    def get_address_line_list(self):
        return self.address_line_list
