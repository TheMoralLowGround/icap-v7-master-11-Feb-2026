"""
Linear Data Processing Functions
================================

Overview:
---------
This module contains a set of utility functions to process data related to various key-value pairs. Each function 
takes a parsed value list, processes it based on predefined rules, and appends the processed cells to a list. 
These functions are designed for specific data structures like weights, volumes, temperatures, goods values, and dimensions.

Function Definitions:
---------------------
1. **generate_cell(value, label, input_cell)**
   - Creates a new cell by copying an existing cell and updating its value and label.
   - **Parameters**:
     - `value`: The new value for the cell.
     - `label`: The new label for the cell.
     - `input_cell`: The original cell dictionary.
   - **Returns**:
     - A dictionary representing the new cell.

2. **weight_uom_linear(processed_cells, parsed_value_list, label, cell)**
   - Processes weight and unit of measurement (UOM).
   - Adds cells for weight, UOM, and any extra element.

3. **volume_uom_linear(processed_cells, parsed_value_list, label, cell)**
   - Processes volume and its UOM.
   - Adds cells for volume, UOM, and any extra element.

4. **temperature_uom_linear(processed_cells, parsed_value_list, label, cell)**
   - Processes temperature-related data such as requirements for temperature control, maximum and minimum values, and UOM.
   - Handles both single and multiple parsed values.

5. **value_of_goods_linear(processed_cells, parsed_value_list, label, cell)**
   - Processes the value of goods along with its currency code.
   - Adds cells for the value, currency code, and any extra element.

6. **package_count_linear(processed_cells, parsed_value_list, label, cell)**
   - Processes package counts and their associated types.
   - Customizes the label based on context (e.g., `innerPackageType`, `totalPackageType`).

7. **height_uom_linear(processed_cells, parsed_value_list, label, cell, dimension_uom_available=False)**
   - Processes height and its UOM.
   - Ensures that the UOM is added only once if not already available.

8. **width_uom_linear(processed_cells, parsed_value_list, label, cell, dimension_uom_available=False)**
   - Processes width and its UOM.
   - Similar to `height_uom_linear`, ensures UOM is added only once.

9. **financial_linear(processed_cells, parsed_value_list, label, cell, currency_available=False)**
   - Processes financial values and their associated currency.
   - Adds cells for the value and currency, ensuring the currency is added only once.

Parameters:
-----------
- `processed_cells` (list): A list to store processed cells.
- `parsed_value_list` (list): The parsed values to process.
- `label` (str): The label for the processed cells.
- `cell` (dict): The original cell dictionary.
- `dimension_uom_available` (bool, optional): Tracks whether the dimension UOM is already added.
- `currency_available` (bool, optional): Tracks whether the currency cell is already added.

Usage Example:
--------------
```python
cell = {"v": "100 kg", "label": "weight"}
parsed_value_list = ["100", "kg", ""]
processed_cells = []

weight_uom_linear(processed_cells, parsed_value_list, "weight", cell)

print(processed_cells)
"""


def generate_cell(value, label, input_cell):
    new_cell = input_cell.copy()
    new_cell["v"] = value.strip()
    new_cell["label"] = label
    return new_cell


def weight_uom_linear(processed_cells, parsed_value_list, label, cell):
    if len(parsed_value_list) == 3:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # add label value key in the shell
        cell1 = generate_cell(number.strip(), label, cell)

        # Adding Cell2
        cell2 = generate_cell(uom.strip(), label + "Uom", cell)

        processed_cells.append(cell1)
        processed_cells.append(cell2)
        # For extra element
        if parsed_value_list[-1]:
            cell3 = generate_cell(parsed_value_list[-1].strip(), label + "_1", cell)
            processed_cells.append(cell3)
    else:
        processed_cells.append(cell)


def volume_uom_linear(processed_cells, parsed_value_list, label, cell):
    if len(parsed_value_list) == 3:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # add label value key in the shell
        cell1 = generate_cell(number.strip(), label, cell)

        # Adding Cell2
        cell2 = generate_cell(uom.strip(), label + "Uom", cell)

        processed_cells.append(cell1)
        processed_cells.append(cell2)
        # For extra element
        if parsed_value_list[-1]:
            cell3 = generate_cell(parsed_value_list[-1].strip(), label + "_1", cell)
            processed_cells.append(cell3)
    else:
        processed_cells.append(cell)


def temperature_uom_linear(processed_cells, parsed_value_list, label, cell):
    if len(parsed_value_list) == 4:
        # Retaining the original cell
        processed_cells.append(cell)

        requires_temperature_control = parsed_value_list[0]
        required_maximum = parsed_value_list[1]
        required_minimum = parsed_value_list[2]
        temperature_uom = parsed_value_list[3]

        # Adding Cell1
        cell1 = generate_cell(
            requires_temperature_control.strip(), "requiresTemperatureControl", cell
        )
        # Adding Cell2
        cell2 = generate_cell(required_maximum.strip(), "requiredMaximum", cell)
        # Adding Cell3
        cell3 = generate_cell(required_minimum.strip(), "requiredMinimum", cell)
        # Adding Cell4
        cell4 = generate_cell(temperature_uom.strip(), "temperatureUom", cell)

        processed_cells.append(cell1)
        processed_cells.append(cell2)
        processed_cells.append(cell3)
        processed_cells.append(cell4)

    elif len(parsed_value_list) == 1:
        # Retaining the original cell
        processed_cells.append(cell)

        requires_temperature_control = parsed_value_list[0]

        # Adding Cell1
        cell1 = generate_cell(
            requires_temperature_control.strip(), "requiresTemperatureControl", cell
        )

        processed_cells.append(cell1)
    else:
        processed_cells.append(cell)


def value_of_goods_linear(processed_cells, parsed_value_list, label, cell):
    if len(parsed_value_list) == 3:
        number = parsed_value_list[0]
        currency_code = parsed_value_list[1]

        # Adding Cell1
        cell1 = generate_cell(number.strip(), label, cell)
        # Adding Cell2
        cell2 = generate_cell(currency_code.strip(), label + "Currency", cell)

        processed_cells.append(cell1)
        processed_cells.append(cell2)
        # For extra element
        if parsed_value_list[-1]:
            cell3 = generate_cell(parsed_value_list[-1].strip(), label + "_1", cell)
            processed_cells.append(cell3)
    else:
        processed_cells.append(cell)


def package_count_linear(processed_cells, parsed_value_list, label, cell):
    if len(parsed_value_list) == 3:
        # Retaining the original cell
        # processed_cells.append(cell)

        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = generate_cell(number.strip(), label, cell)
        # Adding Cell2
        cell2_label = label
        if "inner" in label:
            cell2_label = "innerPackageType"
        elif "total" in label:
            cell2_label = "totalPackageType"
        else:
            cell2_label = "packageType"

        cell2 = generate_cell(uom.strip(), cell2_label, cell)

        processed_cells.append(cell1)
        processed_cells.append(cell2)
        # For extra element
        if parsed_value_list[-1]:
            cell3 = generate_cell(parsed_value_list[-1].strip(), label + "_1", cell)
            processed_cells.append(cell3)
    else:
        processed_cells.append(cell)


def height_uom_linear(
    processed_cells, parsed_value_list, label, cell, dimension_uom_available=False
):
    if len(parsed_value_list) == 2:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = generate_cell(number.strip(), label, cell)
        # Adding Cell2
        cell2 = generate_cell(uom.strip(), "dimensionsUom", cell)

        processed_cells.append(cell1)
        if not dimension_uom_available:
            dimension_uom_available = True
            dimension_uom_data = cell2
            # processed_cells.append(cell2)
        return dimension_uom_data
    else:
        processed_cells.append(cell)


def width_uom_linear(
    processed_cells, parsed_value_list, label, cell, dimension_uom_available=False
):
    if len(parsed_value_list) == 2:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = generate_cell(number.strip(), label, cell)
        # Adding Cell2
        cell2 = generate_cell(uom.strip(), "dimensionsUom", cell)

        processed_cells.append(cell1)
        if not dimension_uom_available:
            dimension_uom_available = True
            dimension_uom_data = cell2
        return dimension_uom_data
    else:
        processed_cells.append(cell)


def financial_linear(
    processed_cells, parsed_value_list, label, cell, currency_available=False
):
    if len(parsed_value_list) == 2:
        number = parsed_value_list[0]
        currency = parsed_value_list[1]
        cell1 = generate_cell(number, label, cell)
        # currency_label = cell["label"] + \
        #     "Currency"
        currency_label = "Currency"
        cell2 = generate_cell(currency, currency_label, cell)

        processed_cells.append(cell1)
        # processed_cells.append(cell2)
        if not currency_available:
            currency_available = True
            currency_data = cell2
        return currency_data
    else:
        processed_cells.append(cell)
