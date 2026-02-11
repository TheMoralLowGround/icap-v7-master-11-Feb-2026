"""
Parser Strategies for Processed Cells
======================================

Purpose:
--------
This module defines a set of strategies to process and parse cells with specific structures, suffixes, and expected lengths. 
Each strategy handles a unique cell type or data pattern and transforms the data as required.


#updated by: Sunny
#updated on: 03/10/2021
Base Class:
-----------
**Strategy**
- A generic base class for parsing and processing cells.
- Attributes:
  - `suffix_list`: List of suffixes used to modify labels during processing.
  - `expected_parser_value_length`: The expected number of values in `parsed_value_list`.
  - `cell`: The current cell being processed.
  - `label`: The label of the cell.
  - `parsed_value_list`: A list of parsed values from the cell.
  - `processed_cells`: A list to store processed cells.
- Methods:
  - `process()`: Processes the current cell based on the strategy logic.
  - `generate_cell(value, label, input_dict)`: Creates a new cell with a specified value and label.

Derived Classes:
-----------------
1. **WeightUOMStrategy**:
   - Handles weight values and their units of measurement (UOM).
   - Suffixes: ["", "Uom", "_1"].
   - Expected Values: 3.

2. **VolumeUOMStrategy**:
   - Handles volume values and their UOM.
   - Suffixes: ["", "Uom", "_1"].
   - Expected Values: 3.

3. **TemperatureParserStrategy**:
   - Handles temperature-related values, including minimum, maximum, and UOM.
   - Suffixes: ["requiresTemperatureControl", "requiredMaximum", "requiredMinimum", "temperatureUom"].
   - Expected Values: [1, 4].
   - Special logic for single or multiple temperature values.

4. **ValueOfGoodsParserStrategy**:
   - Parses value of goods and their associated currency.
   - Suffixes: ["", "Currency", "_1"].
   - Expected Values: 3.

5. **PackageCountStrategy**:
   - Handles package counts and their types.
   - Suffixes: ["", "", "_1"].
   - Expected Values: 3.
   - Adjusts labels based on the context (e.g., "innerPackageType", "totalPackageType").

6. **FinancialParserStrategy**:
   - Parses financial values and their currency.
   - Suffixes: ["", "Currency"].
   - Expected Values: 2.
   - Tracks currency metadata.

7. **HeightWeightLengthStrategy**:
   - Generic strategy for handling height, weight, or length values and their UOM.
   - Suffixes: ["", "dimensionsUom"].
   - Expected Values: 2.
   - Tracks dimension metadata.

8. **HeightUOMStrategy, WidthUOMStrategy, LengthUOMStrategy**:
   - Specialized strategies derived from `HeightWeightLengthStrategy`.

Key Features:
-------------
- **Suffix Management**:
  Each strategy uses a predefined list of suffixes to generate new labels.

- **Dynamic Metadata Updates**:
  Strategies like `FinancialParserStrategy` and `HeightWeightLengthStrategy` track additional metadata.

- **Flexible Parsing**:
  Each strategy defines its own logic for processing cells based on the number of parsed values.

Usage:
------
1. Instantiate the appropriate strategy class.
2. Call the `process()` method with the required parameters.
3. Processed cells are stored in the `processed_cells` list.

Example:
--------
```python
cell = {"v": "123", "label": "weight"}
parsed_value_list = ["123", "kg", "extra"]
processed_cells = []

strategy = WeightUOMStrategy(cell, processed_cells, parsed_value_list, "weight")
strategy.process()

print(processed_cells)
"""

from typing import List


class Strategy:
    suffix_list = []
    expected_parser_value_length = int()

    def __init__(
        self, cell: dict, processed_cells: list, parsed_value_list: list, label: str
    ):
        self.cell = cell
        self.label = label
        self.parsed_value_list = parsed_value_list
        self.processed_cells = processed_cells

    def process(self):
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            for value, suffix in zip(self.parsed_value_list[:2], self.suffix_list[:2]):
                generated_cell = self.generate_cell(
                    value.strip(), f"{self.label}{suffix}", self.cell
                )
                self.processed_cells.append(generated_cell)

            if self.parsed_value_list[-1]:
                extra_cell = self.generate_cell(
                    self.parsed_value_list[-1].strip(),
                    f"{self.label}{self.suffix_list[-1]}",
                    self.cell,
                )
                self.processed_cells.append(extra_cell)

        else:
            self.processed_cells.append(self.cell)

    @staticmethod
    def generate_cell(value, label, input_dict):
        new_dict = input_dict.copy()
        new_dict["v"] = value.strip()
        new_dict["label"] = label
        return new_dict


# ** code done / test done
class WeightUOMStrategy(Strategy):
    suffix_list = ["", "Uom", "_1"]
    expected_parser_value_length = 3


# ** code done / test done
class VolumeUOMStrategy(Strategy):
    suffix_list = ["", "Uom", "_1"]
    expected_parser_value_length = 3

    # def process(self):
    #     super().process()
    #     for pc in self.processed_cells:
    #         if pc.get("id") == self.cell.get("id"):
    #             pc["v"] = pc["v"].replace(",", "")
        # self.processed_cells.append(self.generate_cell("UOM","volumeUOM",self.cell))

# ** code done / test done
class TemperatureParserStrategy(Strategy):
    suffix_list = [
        "requiresTemperatureControl",
        "requiredMaximum",
        "requiredMinimum",
        "temperatureUom",
    ]
    expected_parser_value_length = [1, 4]

    def process(self):
        if len(self.parsed_value_list) == self.expected_parser_value_length[1]:
            self.processed_cells.append(self.cell)
            cells = [
                self.generate_cell(node.strip(), suffix, self.cell)
                for node, suffix in zip(self.parsed_value_list, self.suffix_list)
            ]
            self.processed_cells.extend(cells)

        elif len(self.parsed_value_list) == self.expected_parser_value_length[0]:
            self.processed_cells.append(self.cell)
            cells = [
                self.generate_cell(node.strip(), suffix, self.cell)
                for node, suffix in zip(self.parsed_value_list, self.suffix_list)
            ]
            self.processed_cells.extend(cells)
        else:
            self.processed_cells.append(self.cell)


# # ** code done
# class TemperatureParserStrategyVariantOne(Strategy):
#     suffix_list = ["", "Currency", "_1"]
#     expected_parser_value_length = 3

#     def process(self):
#         if len(self.parsed_value_list) == 1:
#             processed_cells = []
#             processed_cells.append(self.cell)
#             cells = [
#                 self.generate_cell(
#                     node.strip(), suffix, self.cell
#                 ) for node, suffix in zip(self.parsed_value_list, self.labels)
#             ]
#             processed_cells.extend(cells)
#         else:
#             processed_cells.append(self.cell)


# ** code done / test done
class ValueOfGoodsParserStrategy(Strategy):
    suffix_list = ["", "Currency", "_1"]
    expected_parser_value_length = 3


# ** code done / test done
class PackageCountStrategy(Strategy):
    suffix_list = ["", "", "_1"]
    expected_parser_value_length = 3

    def process(self):
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            label_1, label_3 = [
                f"{self.label}{suffix}" for suffix in self.suffix_list[1:3:1]
            ]

            if "inner" in self.label:
                label_2 = "innerPackageType"
            elif "total" in self.label:
                label_2 = "totalPackageType"
            else:
                label_2 = "packageType"

            cell12 = [
                self.generate_cell(node, label, self.cell)
                for node, label in zip(self.parsed_value_list[:2], [label_1, label_2])
            ]
            self.processed_cells.extend(cell12)

            if self.parsed_value_list[-1]:
                cell3 = self.generate_cell(
                    self.parsed_value_list[-1].strip(), label_3, self.cell
                )
                self.processed_cells.append(cell3)
        else:
            self.processed_cells.append(self.cell)


# ** code done / test done
class FinancialParserStrategy(Strategy):
    suffix_list = ["", "Currency"]
    expected_parser_value_length = 2

    def process(self, currency_metadata: dict):
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            number, currency = self.parsed_value_list

            cell1 = self.generate_cell(number, self.label, self.cell)

            currency_label = self.suffix_list[1]
            cell2 = self.generate_cell(currency, currency_label, self.cell)

            self.processed_cells.append(cell1)
            if not currency_metadata.get("currency_available"):
                currency_metadata.update(
                    {"currency_available": True, "currency_data": cell2}
                )

        else:
            self.processed_cells.append(self.cell)


# ** code done / test done
class HeightWeightLengthStrategy(Strategy):
    suffix_list = ["", "dimensionsUom"]
    expected_parser_value_length = 2

    def process(self, dimension_metadata: dict):
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            number, uom = self.parsed_value_list
            cell1 = self.generate_cell(number.strip(), self.label, self.cell)
            cell2 = self.generate_cell(uom.strip(), self.suffix_list[1], self.cell)

            self.processed_cells.append(cell1)

            if not dimension_metadata.get("dimension_UOM_available"):
                dimension_metadata.update(
                    {"dimension_UOM_available": True, "dimension_UOM_data": cell2}
                )
        else:
            self.processed_cells.append(self.cell)


class LocationNameCellStrategy(Strategy):
    labels = ["", "", ""]
    expected_parser_value_length = 3

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            location, extra_value, location_country = self.parsed_value_list
            generated_cell1 = self.generate_cell(
                location.strip(), f"{self.label}", self.cell
            )
            self.processed_cells.append(generated_cell1)

            if location_country != None:
                generated_cell2 = self.generate_cell(
                    location_country.strip(), f"{self.label}", self.cell
                )
                if len(generated_cell2["v"]) == 2:
                    generated_cell2["label"] = (
                        self.label.replace("LocationName", "") + "CountryCode",
                    )
                self.processed_cells.append(generated_cell2)

            if extra_value:
                generated_cell3 = self.generate_cell(
                    extra_value.strip(),
                    self.label.replace("Name", "") + "Code",
                    self.cell,
                )
                self.processed_cells.append(generated_cell3)

            self.append_count = 0
        else:
            self.processed_cells.append(self.cell)


class LocationNameCellStrategyVariantFour(Strategy):
    labels = ["", "Code", "CountryCode"]
    expected_parser_value_length = 4

    def process(self):
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length:
            location, location_code, location_country = self.parsed_value_list[:3]
            generated_cell1 = self.generate_cell(
                location.strip(), self.label, self.cell
            )
            generated_cell2_label = self.label.replace("Name", "") + self.labels[1]

            generated_cell2 = self.generate_cell(
                location_code.strip(), generated_cell2_label, self.cell
            )
            generated_cell3 = self.generate_cell(
                location_country.strip(), self.label, self.cell
            )

            if len(generated_cell3["v"]) == 2:
                generated_cell3["label"] = (
                    self.label.replace("LocationName", "") + "CountryCode"
                )
            else:
                generated_cell3["label"] = (
                    self.label.replace("LocationName", "") + "Country"
                )
            self.processed_cells.extend(
                [generated_cell1, generated_cell2, generated_cell3]
            )
            self.append_count = 0
        else:
            self.processed_cells.append(self.cell)
        return self.processed_cells


class IncotermParserStrategy(Strategy):
    labels = ["", "Location"]
    expected_parser_value_length = [1, 2]

    def process(self) -> List[dict]:
        self.append_count = 0
        if len(self.parsed_value_list) == self.expected_parser_value_length[0]:
            in_co_terms = self.parsed_value_list[0]
            generated_cell1 = self.generate_cell(
                in_co_terms.strip(), self.label, self.cell
            )
            self.processed_cells.append(generated_cell1)

        elif len(self.parsed_value_list) == self.expected_parser_value_length[1]:
            generated_cell1, generated_cell2 = [
                self.generate_cell(value, f"{self.label}{label}", self.cell)
                for value, label in zip(self.parsed_value_list, self.labels)
            ]
            self.processed_cells.extend([generated_cell1, generated_cell2])
            self.append_count = 0
        else:
            self.processed_cells.append(self.cell)
        return self.processed_cells


# ** code done / test done
class HeightUOMStrategy(HeightWeightLengthStrategy):
    pass


# ** code done / code done
class WidthUOMStrategy(HeightWeightLengthStrategy):
    pass


# ** code done
class LengthUOMStrategy(HeightWeightLengthStrategy):
    pass
