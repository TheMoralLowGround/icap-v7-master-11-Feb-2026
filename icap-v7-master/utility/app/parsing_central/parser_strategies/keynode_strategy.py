"""
KeyNode Parsing and Transformation Strategies
=============================================

Overview:
---------
This module provides a set of strategies to parse, transform, and process key nodes based on specific parsing rules 
and labels. Each strategy is tailored for a unique use case, such as handling dimensions, weights, or temperatures. 
The base class `KeyNodeStrategy` defines a common interface for all strategies, ensuring a consistent structure for 
key node processing.

Base Class:
-----------
**KeyNodeStrategy**
- Attributes:
  - `labels`: A list of suffixes or modifications applied to key node labels.
  - `expected_parser_value_length`: Expected number of parsed values for the key node.
  - `key_node`: The original key node being processed.
  - `label`: The label of the key node.
  - `parsed_value_list`: A list of parsed values extracted from the key node.
  - `processed_key_nodes`: A list that accumulates processed key nodes.
  - `key_node_unique_id`: Unique identifier for the original key node.
  - `append_count`: A counter used to generate unique IDs for new key nodes.

- Methods:
  - `process()`: Core logic for processing and transforming the key node based on specific rules.
  - `update_unique_id(new_key_node)`: Updates the unique ID for a newly generated key node.
  - `generate_key_node(value, label)`: Creates a new key node with a specified value and label.

Derived Classes:
----------------
1. **WeightUOMKeyNodeStrategy**:
   - Handles weight and its unit of measurement (UOM).
   - Labels: ["", "Uom", ""].
   - Expected Values: 3.

2. **VolumeUOMKeyNodeStrategy**:
   - Handles volume and its UOM.
   - Labels: ["", "Uom", "_1"].
   - Expected Values: 3.

3. **PackageCountKeyNodeStrategy**:
   - Handles package counts and associated types (e.g., inner or total package types).
   - Labels: ["", "", "_1"].
   - Expected Values: 3.
   - Custom logic for different label contexts such as "innerPackageType" or "totalPackageType".

4. **TemperatureKeyNodeStrategy**:
   - Processes temperature-related data, including requirements for temperature control, min/max values, and UOM.
   - Labels: ["", "requiredMaximum", "requiredMinimum", "temperatureUom"].
   - Expected Values: [1, 4].
   - Handles scenarios for single or multiple temperature values.

5. **IncotermParserKeyNodeStrategy**:
   - Parses Incoterms and associated location data.
   - Labels: ["", "Location"].
   - Expected Values: [1, 2].

6. **ValueOfGoodsKeyNodeStrategy**:
   - Parses the value of goods and their associated currency codes.
   - Labels: ["", "CurrencyCode", "_1"].
   - Expected Values: 3.

7. **LocationNameKeyNodeStrategy**:
   - Handles location names, codes, and associated country codes.
   - Labels: ["", "", ""].
   - Expected Values: 3.
   - Adjusts label suffixes for country codes based on their length.

8. **LocationNameKeyNodeStrategyVariantFour**:
   - Processes extended location data with additional fields for codes and country codes.
   - Labels: ["", "Code", "CountryCode"].
   - Expected Values: 4.

9. **FinanciaParserKeyNodeStrategy**:
   - Handles financial values and associated currency codes.
   - Labels: ["", "CurrencyCode"].
   - Expected Values: 2.

10. **DimensionUOMKeyNodeStrategy**:
    - Processes dimension-related values such as length, width, height, and their UOM.
    - Handles complex structures with additional data like `packageCount`, `grossWeight`, and `innerPackageType`.

Key Features:
-------------
- **Dynamic Label Handling**:
  Each strategy uses predefined suffixes to generate labels dynamically for new key nodes.

- **Unique ID Management**:
  Ensures unique identifiers for newly generated key nodes by appending a counter to the original key node's ID.

- **Flexible Parsing**:
  Supports various scenarios with single or multiple parsed values, adjusting behavior accordingly.

- **Complex Data Structures**:
  Strategies like `DimensionUOMKeyNodeStrategy` handle nested or multi-element data, supporting a wide range of use cases.

Usage Example:
--------------
```python
key_node = {"unique_id": "key1", "v": "100 kg", "label": "weight"}
parsed_value_list = ["100", "kg", ""]
processed_key_nodes = []

strategy = WeightUOMKeyNodeStrategy(processed_key_nodes, parsed_value_list, "weight", key_node)
strategy.process()

print(processed_key_nodes)
"""


from typing import List


class KeyNodeStrategy:
    labels = ["", "label", ""]
    expected_parser_value_length = 3

    def __init__(
        self,
        processed_key_nodes: list,
        parsed_value_list: list,
        label: str,
        key_node: dict,
    ):
        self.append_count = 0
        self.parsed_value_list = parsed_value_list
        self.label = label
        self.key_node = key_node
        self.processed_key_nodes = processed_key_nodes
        self.key_node_unique_id = key_node["unique_id"]

    def process(self) -> List[dict]:
        """
        Process the parsed value list
        """
        self.append_count = 0
        # Check if the length of the parsed value list is in the expected parser value length
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            key_node1, key_node2 = [
                self.generate_key_node(node, f"{self.label}{label}")
                for node, label in zip(self.parsed_value_list[:2], self.labels[:2])
            ]

            self.update_unique_id(key_node2)
            self.processed_key_nodes.extend([key_node1, key_node2])

            if node := self.parsed_value_list[-1]:
                key_node3 = self.generate_key_node(
                    node, f"{self.label}{self.labels[-1]}"
                )
                self.update_unique_id(key_node3)
                self.processed_key_nodes.append(key_node3)
            self.append_count = 0
        else:
            self.processed_key_nodes.append(self.key_node)
        return self.processed_key_nodes

    def update_unique_id(self, new_key_node: dict):
        """
        Update unique ID of new key node
        """
        try:
            # Generate a new unique_id by concatenating the existing unique_id,
            # the label from the new_key_node, and the append_count
            new_key_node["unique_id"] = (
                f"{self.key_node_unique_id}-"
                f"{new_key_node['label']}-"
                f"{self.append_count}"
            )

            # Increment the append_count by 1
            self.append_count += 1
            return new_key_node

        except Exception as e:
            # Print the exception encountered
            print(f"Exception encountered: {e}")

    def generate_key_node(self, value, label):
        # Create a copy of the input dictionary
        new_dict = self.key_node.copy()

        # Strip any leading or trailing whitespace from the value and assign it to the "v" key in the new dictionary
        new_dict["v"] = value.strip()
        new_dict["label"] = label

        # Return the modified new dictionary
        return new_dict


# ** Done test
class WeightUOMKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "Uom", ""]
    expected_parser_value_length = 3


# ** Done test
class VolumeUOMKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "Uom", "_1"]
    expected_parser_value_length = 3


# ** Done test
class PackageCountKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "", "_1"]
    expected_parser_value_length = 3

    def process(self) -> List[dict]:
        self.append_count = 0
        # Check if the length of the parsed value list is in the expected parser value length
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            label_1 = f"{self.label}{self.labels[0]}"

            if "inner" in self.label:
                label_2 = "innerPackageType"
            elif "total" in self.label:
                label_2 = "totalPackageType"
            else:
                label_2 = "packageType"

            key_node1, key_node2 = [
                self.generate_key_node(node, label)
                for node, label in zip(self.parsed_value_list[:2], [label_1, label_2])
            ]
            self.update_unique_id(key_node2)
            self.processed_key_nodes.extend([key_node1, key_node2])

            if value := self.parsed_value_list[-1]:
                key_node3 = self.generate_key_node(
                    value, f"{self.label}{self.labels[-1]}"
                )
                self.processed_key_nodes.append(key_node3)
            self.append_count = 0
        else:
            self.processed_key_nodes.append(self.key_node)
        return self.processed_key_nodes


class TemperatureKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "requiredMaximum", "requiredMinimum", "temperatureUom"]
    expected_parser_value_length = [1, 4]

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length[0]:
            requires_temperature_control = self.parsed_value_list[0]

            key_node1 = self.generate_key_node(
                requires_temperature_control.strip(), "requiresTemperatureControl"
            )
            self.update_unique_id(key_node1)
            self.processed_key_nodes.append(key_node1)
        elif len(self.parsed_value_list) == self.expected_parser_value_length[1]:
            key_node1 = self.generate_key_node(
                self.parsed_value_list[0].strip(), self.parsed_value_list[0]
            )

            self.update_unique_id(key_node1)
            self.processed_key_nodes.append(key_node1)

            for value, label in zip(self.parsed_value_list[1:], self.labels[1:]):
                key_node = self.generate_key_node(value, f"{label}")
                self.update_unique_id(key_node)
                self.processed_key_nodes.append(key_node)
        else:
            self.processed_key_nodes.append(self.key_node)
        self.append_count = 0
        return self.processed_key_nodes


# ** need to test
class IncotermParserKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "Location"]
    expected_parser_value_length = [1, 2]

    def process(self) -> List[dict]:
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length[0]:
            in_co_terms = self.parsed_value_list[0]
            if in_co_terms:
                key_node1 = self.generate_key_node(in_co_terms.strip(), self.label)
            else:
                key_node1 = self.generate_key_node("", self.label)
            self.processed_key_nodes.append(key_node1)

        elif len(self.parsed_value_list) == self.expected_parser_value_length[1]:
            key_node1, key_node2 = [
                self.generate_key_node(value, f"{self.label}{label}")
                for value, label in zip(self.parsed_value_list, self.labels)
            ]
            self.update_unique_id(key_node2)
            self.processed_key_nodes.extend([key_node1, key_node2])
            self.append_count = 0
        else:
            self.processed_key_nodes.append(self.key_node)
        return self.processed_key_nodes


# ** Done Test
class ValueOfGoodsKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "CurrencyCode", "_1"]
    expected_parser_value_length = 3


# ** Done test
class LocationNameKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "", ""]
    expected_parser_value_length = 3

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            location, extra_value, location_country = self.parsed_value_list
            key_node1 = self.generate_key_node(location.strip(), self.label)
            self.processed_key_nodes.append(key_node1)

            if location_country != None:
                key_node2 = self.generate_key_node(location_country.strip(), self.label)
                if len(key_node2["v"]) == 2:
                    key_node2["label"] = (
                        self.label.replace("LocationName", "") + "CountryCode"
                    )
                self.update_unique_id(key_node2)
                self.processed_key_nodes.append(key_node2)

            if extra_value:
                key_node3 = self.generate_key_node(
                    extra_value.strip(), self.label.replace("Name", "") + "Code"
                )
                self.update_unique_id(key_node3)
                self.processed_key_nodes.append(key_node3)

            self.append_count = 0
        else:
            self.processed_key_nodes.append(self.key_node)


# ** Done Test
class LocationNameKeyNodeStrategyVariantFour(KeyNodeStrategy):
    labels = ["", "Code", "CountryCode"]
    expected_parser_value_length = 4

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            location, location_code, location_country = self.parsed_value_list[:3]
            key_node1 = self.generate_key_node(location.strip(), self.label)

            key_node2_label = self.label.replace("Name", "") + self.labels[1]
            key_node2 = self.generate_key_node(location_code.strip(), key_node2_label)
            key_node3 = self.generate_key_node(location_country.strip(), self.label)

            if len(key_node3["v"]) == 2:
                key_node3["label"] = (
                    self.label.replace("LocationName", "") + "CountryCode"
                )
            else:
                key_node3["label"] = self.label.replace("LocationName", "") + "Country"
            self.update_unique_id(key_node3)
            self.processed_key_nodes.extend([key_node1, key_node2, key_node3])
            self.append_count = 0
        else:
            self.processed_key_nodes.append(self.key_node)
        return self.processed_key_nodes


# ** Done test
class FinanciaParserKeyNodeStrategy(KeyNodeStrategy):
    labels = ["", "CurrencyCode"]
    expected_parser_value_length = 2

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            key_node1, key_node2 = [
                self.generate_key_node(value, f"{self.label}{label}")
                for value, label in zip(self.parsed_value_list, self.labels)
            ]
            self.processed_key_nodes.extend([key_node1, key_node2])
        else:
            self.processed_key_nodes.append(self.key_node)


class DimensionUOMKeyNodeStrategy(KeyNodeStrategy):
    def process(self):
        self.append_count = 0
        for inner_list in self.parsed_value_list:
            # print(parsed_value_list)
            if len(inner_list) == 5:
                self.processed_key_nodes.append(self.key_node)
                l = inner_list[0]
                w = inner_list[1]
                h = inner_list[2]
                uom = inner_list[3]

                # Adding key_node1
                key_node1 = self.generate_key_node(l.strip(), "length")
                key_node2 = self.generate_key_node(w.strip(), "width")
                key_node3 = self.generate_key_node(h.strip(), "height")

                for new_key_node in [key_node1, key_node2, key_node3]:
                    self.update_unique_id(new_key_node)
                    new_key_node["parentLabel"] = "dimensions"

                self.processed_key_nodes.extend([key_node1, key_node2, key_node3])

                if uom:
                    # Adding Cell3
                    key_node4 = self.generate_key_node(uom.strip(), self.label + "Uom")
                    self.update_unique_id(key_node4)
                    key_node4["parentLabel"] = "dimensions"
                    self.processed_key_nodes.append(key_node4)

                # For extra element
                if inner_list[4]:
                    key_node5 = self.generate_key_node(
                        inner_list[-1].strip(), self.label + "_1"
                    )
                    self.update_unique_id(key_node5)
                    key_node5["parentLabel"] = "dimensions"
                    self.processed_key_nodes.append(key_node5)

            # # Working for extra data (packageCount only)
            elif len(inner_list) == 6:
                self.processed_key_nodes.append(self.key_node)
                l = inner_list[0]
                w = inner_list[1]
                h = inner_list[2]
                uom = inner_list[3]
                package_count = inner_list[5]

                # Adding key_node1
                key_node1 = self.generate_key_node(l.strip(), "length")
                key_node2 = self.generate_key_node(w.strip(), "width")
                key_node3 = self.generate_key_node(h.strip(), "height")
                key_node4 = self.generate_key_node(uom.strip(), self.label + "Uom")
                key_node5 = self.generate_key_node(
                    package_count.strip(), "packageCount"
                )

                for new_key_node in [
                    key_node1,
                    key_node2,
                    key_node3,
                    key_node4,
                    key_node5,
                ]:
                    self.update_unique_id(new_key_node)
                    new_key_node["parentLabel"] = "dimensions"

                self.processed_key_nodes.extend(
                    [key_node1, key_node2, key_node3, key_node4, key_node5]
                )

            # Working for extra data
            elif len(inner_list) == 7:
                self.processed_key_nodes.append(self.key_node)
                l = inner_list[0]
                w = inner_list[1]
                h = inner_list[2]
                uom = inner_list[3]
                package_count = inner_list[5]
                package_type = inner_list[6]

                # Adding key_node1
                key_node1 = self.generate_key_node(l.strip(), "length")
                key_node2 = self.generate_key_node(w.strip(), "width")
                key_node3 = self.generate_key_node(h.strip(), "height")
                key_node4 = self.generate_key_node(uom.strip(), self.label + "Uom")
                key_node5 = self.generate_key_node(
                    package_count.strip(), "packageCount"
                )
                key_node6 = self.generate_key_node(package_type.strip(), "packageType")

                for new_key_node in [
                    key_node1,
                    key_node2,
                    key_node3,
                    key_node4,
                    key_node5,
                    key_node6,
                ]:
                    self.update_unique_id(new_key_node)
                    new_key_node["parentLabel"] = "dimensions"

                self.processed_key_nodes.extend(
                    [key_node1, key_node2, key_node3, key_node4, key_node5, key_node6]
                )

            # Working for WITHOUT extra data (innerPackageCount and innerPackageType)
            elif len(inner_list) == 8:
                self.processed_key_nodes.append(self.key_node)
                l = inner_list[0]
                w = inner_list[1]
                h = inner_list[2]
                uom = inner_list[3]
                package_count = inner_list[4]
                package_type = inner_list[5]
                inner_package_count = inner_list[6]
                inner_package_type = inner_list[7]

                # Adding key_node1
                key_node1 = self.generate_key_node(l.strip(), "length")
                key_node2 = self.generate_key_node(w.strip(), "width")
                key_node3 = self.generate_key_node(h.strip(), "height")
                key_node4 = self.generate_key_node(uom.strip(), self.label + "Uom")
                key_node5 = self.generate_key_node(
                    package_count.strip(), "packageCount"
                )
                key_node6 = self.generate_key_node(package_type.strip(), "packageType")
                key_node7 = self.generate_key_node(
                    inner_package_count.strip(), "innerPackageCount"
                )
                key_node8 = self.generate_key_node(
                    inner_package_type.strip(), "innerPackageType"
                )

                for new_key_node in [
                    key_node1,
                    key_node2,
                    key_node3,
                    key_node4,
                    key_node5,
                    key_node6,
                    key_node7,
                    key_node8,
                ]:
                    self.update_unique_id(new_key_node)
                    new_key_node["parentLabel"] = "dimensions"

                self.processed_key_nodes.extend(
                    [
                        key_node1,
                        key_node2,
                        key_node3,
                        key_node4,
                        key_node5,
                        key_node6,
                        key_node7,
                        key_node8,
                    ]
                )

            # Working for extra data (grossWeight and grossWeightUom)
            elif len(inner_list) == 9:
                self.processed_key_nodes.append(self.key_node)
                l = inner_list[0]
                w = inner_list[1]
                h = inner_list[2]
                uom = inner_list[3]
                package_count = inner_list[5]
                package_type = inner_list[6]
                gross_weight = inner_list[7]
                gross_weight_uom = inner_list[8]

                # Adding key_node1
                key_node1 = self.generate_key_node(l.strip(), "length")
                key_node2 = self.generate_key_node(w.strip(), "width")
                key_node3 = self.generate_key_node(h.strip(), "height")
                key_node4 = self.generate_key_node(uom.strip(), self.label + "Uom")
                key_node5 = self.generate_key_node(
                    package_count.strip(), "packageCount"
                )
                key_node6 = self.generate_key_node(package_type.strip(), "packageType")
                key_node7 = self.generate_key_node(gross_weight.strip(), "grossWeight")
                key_node8 = self.generate_key_node(
                    gross_weight_uom.strip(), "grossWeightUom"
                )

                for new_key_node in [
                    key_node1,
                    key_node2,
                    key_node3,
                    key_node4,
                    key_node5,
                    key_node6,
                    key_node7,
                    key_node8,
                ]:
                    self.update_unique_id(new_key_node)
                    new_key_node["parentLabel"] = "dimensions"

                self.processed_key_nodes.extend(
                    [
                        key_node1,
                        key_node2,
                        key_node3,
                        key_node4,
                        key_node5,
                        key_node6,
                        key_node7,
                        key_node8,
                    ]
                )

            else:
                self.processed_key_nodes.append(self.key_node)
        self.append_count = 0
        return self.processed_key_nodes
