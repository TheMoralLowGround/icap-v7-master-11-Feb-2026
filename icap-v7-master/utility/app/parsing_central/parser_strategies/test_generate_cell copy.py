"""
Unit Tests for Data Processing Strategies
=========================================

Overview:
---------
This module contains a suite of unit tests to validate the functionality of data processing strategies and their
corresponding linear processing functions. These strategies are responsible for parsing and transforming
data into a structured format based on specific rules.

Test Classes:
-------------
1. **TestWeightUomCell**
   - Tests the `WeightUOMStrategy` and `weight_uom_linear` functions.
   - Verifies scenarios such as missing first/last value and handling of incorrect lengths.

2. **TestVolumeCell**
   - Tests the `VolumeUOMStrategy` and `volume_uom_linear` functions.
   - Includes tests for scenarios with all values present, missing values, and incorrect lengths.

3. **TestTemperatureCell**
   - Tests the `TemperatureParserStrategy` and `temperature_uom_linear` functions.
   - Covers cases with different lengths of parsed values (1 or 4).

4. **TestValueOfGoodsCell**
   - Tests the `ValueOfGoodsParserStrategy` and `value_of_goods_linear` functions.
   - Includes tests for handling currency and extra elements.

5. **TestPackageCountCell**
   - Tests the `PackageCountStrategy` and `package_count_linear` functions.
   - Verifies behavior for different labels such as `inner`, `total`, and standard package counts.

6. **TestHeightUomCell**
   - Tests the `HeightUOMStrategy` and `height_uom_linear` functions.
   - Checks behavior with and without UOM availability in metadata.

7. **TestWidthUomCell**
   - Tests the `WidthUOMStrategy` and `width_uom_linear` functions.
   - Similar to `TestHeightUomCell` but for width-specific functionality.

8. **TestFinancialParserCell**
   - Tests the `FinancialParserStrategy` and `financial_linear` functions.
   - Validates currency metadata handling and financial value parsing.

Parameters:
-----------
- `cell` (dict): The original cell data structure to process.
- `parsed_value_list` (list): The input list of parsed values.
- `label` (str): The label associated with the cell.
- `processed_cells` (list): A list to store the processed cells.
- `dimension_uom_available` (bool): Tracks if the dimension UOM is already processed (specific to dimension tests).
- `dimension_metadata` (dict): Metadata for dimensions, including UOM availability and data.
- `currency_metadata` (dict): Metadata for currencies, including currency availability and data.

Structure:
----------
- Each test class targets a specific strategy and its corresponding linear function.
- Test methods include:
  - Handling of all values present.
  - Missing values at different positions (first, last).
  - Scenarios with unexpected parsed value lengths.
  - Metadata updates for dimensions and currencies.

Execution:
----------
To execute the tests, run the script using a Python interpreter:
```bash
python <script_name>.py
"""


import unittest

from cell_strategy import *
from strategy_original import *

from app.platform_utility_dgf_v6.app.parsing_central.parser_strategies.cell_strategy import *

cell = {}
parsed_value_list = ["value_1", "value_2", "value_3"]
label = "label"
processed_cells = []


class TestWeightUomCell(unittest.TestCase):
    def test_weight_uom_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        WeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        weight_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_weight_uom_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        WeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        weight_uom_linear(processed_cells_original, parsed_value_list, label, cell)

    def test_weight_uom_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        WeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        weight_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_weight_uom_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        VolumeUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        volume_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)


class TestVolumeCell(unittest.TestCase):
    def test_volume_uom_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        VolumeUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        volume_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        VolumeUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        volume_uom_linear(processed_cells_original, parsed_value_list, label, cell)

    def test_volume_uom_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        VolumeUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        volume_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        VolumeUOMStrategy(cell, processed_cells, parsed_value_list, label).process()
        volume_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)


class TestTemperatureCell(unittest.TestCase):
    def test_temperature_uom_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_2", "value_3", "value_4"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        TemperatureParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        temperature_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_temperature_uom_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3", "Value_4"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        TemperatureParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        temperature_uom_linear(processed_cells_original, parsed_value_list, label, cell)

    def test_temperature_uom_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        TemperatureParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        temperature_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        TemperatureParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        temperature_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_with_expected_length_one(self):
        cell = {}
        parsed_value_list = ["value_1"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        TemperatureParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        temperature_uom_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)


class TestValueOfGoodsCell(unittest.TestCase):
    def test_volume_uom_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        ValueOfGoodsParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        value_of_goods_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        ValueOfGoodsParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        value_of_goods_linear(processed_cells_original, parsed_value_list, label, cell)

    def test_volume_uom_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        ValueOfGoodsParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        value_of_goods_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_volume_uom_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        ValueOfGoodsParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process()
        value_of_goods_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)


class TestPackageCountCell(unittest.TestCase):
    def test_package_count_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        PackageCountStrategy(cell, processed_cells, parsed_value_list, label).process()
        package_count_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_package_count_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        PackageCountStrategy(cell, processed_cells, parsed_value_list, label).process()
        package_count_linear(processed_cells_original, parsed_value_list, label, cell)

    def test_package_count_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        PackageCountStrategy(cell, processed_cells, parsed_value_list, label).process()
        package_count_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_package_count_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []

        PackageCountStrategy(cell, processed_cells, parsed_value_list, label).process()
        package_count_linear(processed_cells_original, parsed_value_list, label, cell)

        self.assertEqual(processed_cells, processed_cells_original)

    def test_package_count_with_different_label(self):
        label = ["label", "inner", "total"]

        for i in range(3):
            cell = {}
            parsed_value_list = ["value_1", "value_2", "value_3"]
            processed_cells = []
            processed_cells_original = []

            PackageCountStrategy(
                cell, processed_cells, parsed_value_list, label[i]
            ).process()
            package_count_linear(
                processed_cells_original, parsed_value_list, label[i], cell
            )
            self.assertEqual(processed_cells, processed_cells_original)


class TestHeightUomCell(unittest.TestCase):
    def test_height_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        HeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        height_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_height_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        HeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        height_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

    def test_height_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        HeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        height_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_height_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        HeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        height_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_height_check_dimension_metadata(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": False,
            "dimension_UOM_data": None,
        }

        HeightUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        d_u_d = height_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)
        self.assertEqual(dimension_metadata.get("dimension_UOM_available"), True)
        self.assertEqual(dimension_metadata.get("dimension_UOM_data"), d_u_d)


class TestWidthUomCell(unittest.TestCase):
    def test_width_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        WidthUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        width_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_width_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        WidthUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        width_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

    def test_width_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        WidthUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        width_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_width_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": True,
            "dimension_UOM_data": None,
        }

        WidthUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        width_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_width_check_dimension_metadata(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        dimension_metadata = {
            "dimension_UOM_available": False,
            "dimension_UOM_data": None,
        }

        WidthUOMStrategy(cell, processed_cells, parsed_value_list, label).process(
            dimension_metadata
        )
        d_u_d = width_uom_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)
        self.assertEqual(dimension_metadata.get("dimension_UOM_available"), True)
        self.assertEqual(dimension_metadata.get("dimension_UOM_data"), d_u_d)


class TestFinancialParserCell(unittest.TestCase):
    def test_financal_first_value_null(self):
        cell = {}
        parsed_value_list = ["", "value_3"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        currency_metadata = {"currency_available": True, "currency_data": None}

        FinancialParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process(currency_metadata)
        financial_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_financal_all_value(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        currency_metadata = {"currency_available": True, "currency_data": None}

        FinancialParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process(currency_metadata)
        financial_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

    def test_financal_last_value_null(self):
        cell = {}
        parsed_value_list = ["value_1", ""]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        currency_metadata = {"currency_available": True, "currency_data": None}

        FinancialParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process(currency_metadata)
        financial_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_financal_without_expected_length(self):
        cell = {}
        parsed_value_list = ["value_1"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        currency_metadata = {"currency_available": True, "currency_data": None}

        FinancialParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process(currency_metadata)
        financial_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)

    def test_financal_check_currency_metadata(self):
        cell = {}
        parsed_value_list = ["value_1", "value_2"]
        label = "label"
        processed_cells = []
        processed_cells_original = []
        dimension_uom_available = False
        currency_metadata = {"currency_available": False, "currency_data": None}

        FinancialParserStrategy(
            cell, processed_cells, parsed_value_list, label
        ).process(currency_metadata)
        d_u_d = financial_linear(
            processed_cells_original,
            parsed_value_list,
            label,
            cell,
            dimension_uom_available,
        )

        self.assertEqual(processed_cells, processed_cells_original)
        self.assertEqual(currency_metadata.get("currency_available"), True)
        self.assertEqual(currency_metadata.get("currency_data"), d_u_d)


if __name__ == "__main__":
    unittest.main()
