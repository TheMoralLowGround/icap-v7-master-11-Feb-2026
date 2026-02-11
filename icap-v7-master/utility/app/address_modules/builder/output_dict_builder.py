"""
OutputDictBuilder Class
========================

Purpose:
--------
The `OutputDictBuilder` class processes a given dictionary of address and related data (`final_dict`) to create a structured and organized output dictionary. It ensures proper sorting, formatting, and cleanup of data while handling specific requirements such as reordering, renaming, and removing unwanted fields.

Attributes:
-----------
- `sort_idx_list`: List defining the order of keys for sorting the final dictionary.
- `final_dict`: Input dictionary containing the processed address and related data.
- `key_val_dict`: Additional key-value pairs to include in the output dictionary.
- `block`: String representing a block value to append to the output dictionary.
- `company_stop_words`: List of stop words for processing company names.
- `output_dict`: Dictionary to store the final, formatted output.

Methods:
--------
1. **get_output_dict()**:
   Returns the final output dictionary after sorting and processing the data.

2. **process_output_dict(sorted_dict)**:
   Processes the sorted dictionary to create the output dictionary:
   - Removes empty `Contact` fields.
   - Cleans and updates `addressLine2` to exclude redundant data (e.g., city, postal code, country).
   - Handles formatting of the company name and ensures the `name` field does not end with a comma.
   - Renames the `Contact` field to `contactName`.

3. **get_sorted_dict()**:
   Sorts the `final_dict` based on `sort_idx_list`. Appends additional fields from `key_val_dict` and the `block` value. If a required key is missing, it adds the key to the sorting list dynamically.

4. **reorganize_company_name(input_dict)**:
   Adjusts the `name` field to handle stop words, splitting and reformatting the company name as necessary. Moves any leftover content to `addressLine1` or `addressLine2` if needed.

5. **address_parser_sorter()**:
   Sorts the `final_dict` items based on their position in `sort_idx_list`. Dynamically handles missing keys by raising a `KeyError` and adjusting the list.

Usage:
------
1. Instantiate the class with required parameters:
   ```python
   builder = OutputDictBuilder(final_dict, key_val_dict, block, company_stop_words)
"""


class OutputDictBuilder:
    sort_idx_list = [
        "name",
        "addressLine1",
        "addressLine2",
        "city",
        "stateProvince",
        "postalCode",
        "country",
        "countryCode",
        "contactPhone",
        "contactEmail",
        "Attn",
        "accountNumber",
        "destinationCountryCode",
        "destinationLocationCode",
        "originLocationCode",
        "incoterms",
        "pickUpAgent",
        "deliveryAgent",
        "customerAccountNumber",
    ]

    def __init__(
        self, final_dict: dict, key_val_dict: dict, block: str, company_stop_words: list
    ):
        self.final_dict = final_dict
        self.key_val_dict = key_val_dict
        self.block = block
        self.company_stop_words = company_stop_words
        self.output_dict = {}

    def get_output_dict(self):
        sorted_dict = self.get_sorted_dict()
        self.process_output_dict(sorted_dict)
        return self.output_dict

    def process_output_dict(self, sorted_dict):
        for a, b in sorted_dict:
            self.output_dict[a] = b

        if (
            "Contact" in self.output_dict.keys()
            and len(self.output_dict["Contact"]) == 0
        ):
            self.output_dict.pop("Contact")

        if "addressLine2" in self.output_dict.keys():
            city = self.output_dict.get("city", "")
            postal_code = self.output_dict.get("postalCode", "")
            country = self.output_dict.get("country", "")

            address_line2 = self.output_dict["addressLine2"].replace(" ,", ",")
            address_line2_list = address_line2.split(" ")
            new_addressLine2_list = [
                item
                for item in address_line2_list
                if item.replace(",", "") not in [city, postal_code, country]
            ]
            self.output_dict["addressLine2"] = " ".join(new_addressLine2_list)

        if self.company_stop_words:
            try:
                self.output_dict = self.reorganize_company_name(self.output_dict)
            except:
                pass

        if self.output_dict.get("name") and self.output_dict.get("name")[-1] == ",":
            self.output_dict["name"] = self.output_dict["name"][:-1]

        if self.output_dict.get("Contact"):
            self.output_dict["contactName"] = self.output_dict.pop("Contact", None)

    def get_sorted_dict(self):
        try:
            sorted_dict = self.address_parser_sorter()
        except KeyError as e:
            """if a key is not found in the sorting index list"""
            key_name_not_found = e.args[0]
            if "address" in key_name_not_found:
                place_at = self.sort_idx_list.index("city")
                self.sort_idx_list.insert(place_at, key_name_not_found)
            else:
                self.sort_idx_list.append(e.args[0])
            sorted_dict = self.address_parser_sorter()

        for extra_key, extra_value in self.key_val_dict.items():
            sorted_dict.append((extra_key, extra_value))

        sorted_dict.append(("block", self.block.strip()))
        return sorted_dict

    def reorganize_company_name(self, input_dict):
        # CODE ADDED HERE BY ALMAS- 13/03/2023
        left_out = None
        for i in self.company_stop_words:
            if i.lower() in input_dict["name"].lower():
                name = input_dict["name"].split(i)
                name[0] = name[0] + " " + i
                input_dict["name"] = name[0]
                try:
                    left_out = name[1]
                except:
                    pass
        # print(left_out)
        length_count = 50
        if left_out != None:
            if "addressLine1" in input_dict.keys():
                input_dict["addressLine1"] = (
                    left_out.strip() + " " + input_dict["addressLine1"]
                )
            else:
                input_dict["addressLine1"] = left_out.strip()
            if len(input_dict["addressLine1"]) > length_count:
                left_out = input_dict["addressLine1"][length_count - 1 :]
                input_dict["addressLine1"] = input_dict["addressLine1"][:50]
                if "addressLine2" in input_dict.keys():
                    input_dict["addressLine2"] = (
                        left_out.strip() + " " + input_dict["addressLine2"]
                    )
                else:
                    input_dict["addressLine2"] = left_out.strip()
        return input_dict

    def address_parser_sorter(self):
        index_map = {v: i for i, v in enumerate(self.sort_idx_list)}
        sorted_dict_output = sorted(
            self.final_dict.items(), key=lambda pair: index_map[pair[0]]
        )
        return sorted_dict_output
