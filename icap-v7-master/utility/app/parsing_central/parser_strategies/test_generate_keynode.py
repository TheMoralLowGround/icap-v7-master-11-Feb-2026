"""
Unit Tests for Parsing and Transformation Strategies
====================================================

Overview:
---------
This module provides a comprehensive suite of unit tests for verifying the correctness of various parsing and 
transformation strategies used to process and transform data into structured formats. The tests ensure that 
each strategy aligns with its corresponding linear processing function, producing consistent and accurate results.

Purpose:
--------
- Validate the behavior of parsing strategies (`Strategy`-based implementations).
- Ensure consistency between strategy-based and linear implementations.
- Test handling of different input scenarios, such as null values, incomplete data, and metadata updates.

Key Components:
---------------
1. **WeightUOM Tests (`WeightUOMStrategy` and `weight_uom_linear`)**:
   - Verify behavior with missing values and unexpected lengths.
   - Validate consistency of processed cells.

2. **VolumeUOM Tests (`VolumeUOMStrategy` and `volume_uom_linear`)**:
   - Test cases with all values, missing values, and incorrect lengths.

3. **Temperature Tests (`TemperatureParserStrategy` and `temperature_uom_linear`)**:
   - Test scenarios with one or four parsed values.
   - Ensure metadata and processed cells are accurate.

4. **Value of Goods Tests (`ValueOfGoodsParserStrategy` and `value_of_goods_linear`)**:
   - Validate parsing of goods values and associated currency data.

5. **Package Count Tests (`PackageCountStrategy` and `package_count_linear`)**:
   - Handle variations in package types (inner, total, and standard).

6. **HeightUOM Tests (`HeightUOMStrategy` and `height_uom_linear`)**:
   - Validate parsing and metadata handling for height dimensions.

7. **WidthUOM Tests (`WidthUOMStrategy` and `width_uom_linear`)**:
   - Ensure consistent processing for width dimensions and UOM metadata.

8. **Financial Parser Tests (`FinancialParserStrategy` and `financial_linear`)**:
   - Validate parsing of financial data, including currency metadata updates.

Test Methodology:
-----------------
- **Strategy Testing**:
  Each test instantiates a `Strategy` object, processes the input data, and verifies the results.
  
- **Linear Function Testing**:
  The same input data is processed using a linear function to ensure consistency with the strategy-based output.

- **Scenarios**:
  - All values present.
  - Missing values (first, last, or intermediate).
  - Unexpected lengths of parsed values.
  - Metadata validation (dimensions, currency).

Execution:
----------
Run the tests using Python's `unittest` framework:
```bash
python <test_script>.py
"""


import unittest

from cell_strategy import *
from strategy_original import *

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
