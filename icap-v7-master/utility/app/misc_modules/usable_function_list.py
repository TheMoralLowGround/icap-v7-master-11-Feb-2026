"""
Part of parsing functions that can be used outside the parsing central too.
Specifically for reparse rule in normalizer and to offload parsing central script
"""
import traceback

def generate_dim_cells(cell, idx, inner_list):
    cells_to_be_appended = list()
    label = cell["label"]
    if "special" in inner_list:
        inner_list = inner_list[:-1]
        cells_to_be_appended.append(cell)

        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = "CMT"
        try:
            package_count = inner_list[3]
        except:
            package_count = ""
        try:
            comodity_code = inner_list[4]
        except:
            comodity_code = ""
        try:
            undg_number = inner_list[5]
        except:
            undg_number = ""
        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["v"] = l.strip()
        cell1["parser_generated"] = True

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["v"] = w.strip()
        cell2["parser_generated"] = True

        # Adding Cell3
        cell3 = cell.copy()

        cell3["label"] = "height"
        cell3["v"] = h.strip()
        cell3["parser_generated"] = True

        cells_to_be_appended.extend([cell1, cell2, cell3])

        # Adding Cell4
        cell4 = cell.copy()

        cell4["label"] = label + "Uom"
        cell4["v"] = uom.strip()
        cell4["parser_generated"] = True
        cells_to_be_appended.append(cell4)
        # Adding Cell5
        cell5 = cell.copy()

        cell5["label"] = "packageCount"
        cell5["v"] = package_count.strip()
        cell5["parser_generated"] = True
        cells_to_be_appended.append(cell5)

        cell6 = cell.copy()

        cell6["label"] = "commodityCode"
        cell6["v"] = comodity_code.strip()
        cell6["parser_generated"] = True
        cells_to_be_appended.append(cell6)

        # if undg_number:
        cell7 = cell.copy()

        cell7["label"] = "_UNDGNumber"
        cell7["v"] = undg_number.strip()
        cell7["parser_generated"] = True
        cells_to_be_appended.append(cell7)

    elif len(inner_list) == 5:
        # processed_cells.append(cell)
        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = inner_list[3]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["v"] = l.strip()
        cell1["parser_generated"] = True

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["v"] = w.strip()
        cell2["parser_generated"] = True

        # Adding Cell3

        cell3 = cell.copy()

        cell3["label"] = "height"
        cell3["parser_generated"] = True
        cell3["v"] = h.strip()

        cells_to_be_appended.extend([cell, cell1, cell2, cell3])

        if uom:
            # Adding Cell3
            cell4 = cell.copy()
            cell4["label"] = label + "Uom"
            cell4["v"] = uom.strip()
            cell4["parser_generated"] = True
            cells_to_be_appended.append(cell4)

        # For extra element
        if inner_list[-1]:
            cell5 = cell.copy()

            cell5["label"] = label
            cell5["v"] = inner_list[-1].strip()
            cell5["parser_generated"] = True
            cells_to_be_appended.append(cell3)

    # Working for extra data (packageCount only)
    elif len(inner_list) == 6:
        cells_to_be_appended.append(cell)

        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = inner_list[3]
        package_count = inner_list[5]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["v"] = l.strip()
        cell1["parser_generated"] = True

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["v"] = w.strip()
        cell2["parser_generated"] = True

        # Adding Cell3
        cell3 = cell.copy()

        cell3["label"] = "height"
        cell3["v"] = h.strip()
        cell3["parser_generated"] = True

        cells_to_be_appended.extend([cell1, cell2, cell3])

        # Adding Cell4
        cell4 = cell.copy()

        cell4["label"] = label + "Uom"
        cell4["v"] = uom.strip()
        cell4["parser_generated"] = True
        cells_to_be_appended.append(cell4)

        # Adding Cell5
        cell5 = cell.copy()

        cell5["label"] = "packageCount"
        cell5["v"] = package_count.strip()
        cell5["parser_generated"] = True
        cells_to_be_appended.append(cell5)

    # Working for extra data (packageCount and packageType)
    elif len(inner_list) == 7:
        cells_to_be_appended.append(cell)

        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = inner_list[3]
        package_count = inner_list[5]
        package_type = inner_list[6]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["v"] = l.strip()
        cell1["parser_generated"] = True

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["parser_generated"] = True
        cell2["v"] = w.strip()

        # Adding Cell3
        cell3 = cell.copy()
        cell3["id"] = cell["id"] + "_" + "2"
        cell3["label"] = "height"
        cell3["v"] = h.strip()
        cell3["parser_generated"] = True

        cells_to_be_appended.extend([cell1, cell2, cell3])

        # Adding Cell4
        cell4 = cell.copy()

        cell4["label"] = label + "Uom"
        cell4["v"] = uom.strip()
        cell4["parser_generated"] = True
        cells_to_be_appended.append(cell4)

        # Adding Cell5
        cell5 = cell.copy()
        cell5["label"] = "packageCount"
        cell5["v"] = package_count.strip()
        cell5["parser_generated"] = True
        cells_to_be_appended.append(cell5)

        # Adding Cell5
        cell6 = cell.copy()
        cell6["label"] = "packageType"
        cell6["v"] = package_type.strip()
        cell6["parser_generated"] = True
        cells_to_be_appended.append(cell6)

    # Working for WITHOUT extra data (innerPackageCount and innerPackageType)
    elif len(inner_list) == 8:
        cells_to_be_appended.append(cell)

        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = inner_list[3]
        package_count = inner_list[4]
        package_type = inner_list[5]
        inner_package_count = inner_list[6]
        inner_package_type = inner_list[7]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["parser_generated"] = True
        cell1["v"] = l.strip()

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["parser_generated"] = True
        cell2["v"] = w.strip()

        # Adding Cell3
        cell3 = cell.copy()
        cell3["label"] = "height"
        cell3["parser_generated"] = True
        cell3["v"] = h.strip()

        # Adding Cell4
        cell4 = cell.copy()
        cell4["label"] = label + "Uom"
        cell4["parser_generated"] = True
        cell4["v"] = uom.strip()

        # Adding Cell5
        cell5 = cell.copy()
        cell5["label"] = "packageCount"
        cell5["parser_generated"] = True
        cell5["v"] = package_count.strip()

        # Adding Cell6
        cell6 = cell.copy()
        cell6["label"] = "packageType"
        cell6["parser_generated"] = True
        cell6["v"] = package_type.strip()

        # Adding Cell7
        cell7 = cell.copy()
        cell7["label"] = "innerPackageCount"
        cell7["parser_generated"] = True
        cell7["v"] = inner_package_count.strip()

        # Adding Cell8
        cell8 = cell.copy()
        cell8["label"] = "innerPackageType"
        cell8["parser_generated"] = True
        cell8["v"] = inner_package_type.strip()

        # passing cells in list
        cells_to_be_appended.extend(
            [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8]
        )
    # Working for extra data (grossWeight and grossWeightUom)
    elif len(inner_list) == 9:
        cells_to_be_appended.append(cell)

        l = inner_list[0]
        w = inner_list[1]
        h = inner_list[2]
        uom = inner_list[3]
        package_count = inner_list[5]
        package_type = inner_list[6]
        gross_weight = inner_list[7]
        gross_weight_uom = inner_list[8]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["label"] = "length"
        cell1["v"] = l.strip()
        cell1["parser_generated"] = True

        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = "width"
        cell2["v"] = w.strip()
        cell2["parser_generated"] = True

        # Adding Cell3
        cell3 = cell.copy()
        cell3["label"] = "height"
        cell3["v"] = h.strip()
        cell3["parser_generated"] = True

        # Adding Cell4
        cell4 = cell.copy()
        cell4["label"] = label + "Uom"
        cell4["parser_generated"] = True
        cell4["v"] = uom.strip()

        # Adding Cell5
        cell5 = cell.copy()
        cell5["label"] = "packageCount"
        cell5["v"] = package_count.strip()
        cell5["parser_generated"] = True

        # Adding Cell6
        cell6 = cell.copy()
        cell6["label"] = "packageType"
        cell6["v"] = package_type.strip()
        cell6["parser_generated"] = True

        # Adding Cell7
        cell7 = cell.copy()
        cell7["label"] = "grossWeight"
        cell7["v"] = gross_weight.strip()
        cell7["parser_generated"] = True

        # Adding Cell8
        cell8 = cell.copy()
        cell8["label"] = "grossWeightUom"
        cell8["v"] = gross_weight_uom.strip()
        cell8["parser_generated"] = True

        # passing cells in list
        cells_to_be_appended.extend(
            [cell1, cell2, cell3, cell4, cell5, cell6, cell7, cell8]
        )

    return cells_to_be_appended


def generate_temperature_cells(cell, parsed_value_list):
    """Generate table cells after temperature parsing"""
    cells_to_be_appended = list()
    if len(parsed_value_list) == 4:
        # Retaining the original cell
        # processed_cells.append(cell)

        requires_temperature_control = parsed_value_list[0]
        required_maximum = parsed_value_list[1]
        required_minimum = parsed_value_list[2]
        temperature_uom = parsed_value_list[3]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["v"] = requires_temperature_control.strip()
        cell1["label"] = "requiresTemperatureControl"
        # Adding Cell2
        cell2 = cell.copy()

        cell2["v"] = required_maximum.strip()
        cell2["label"] = "requiredMaximum"
        # Adding Cell3
        cell3 = cell.copy()
        cell3["v"] = required_minimum.strip()
        cell3["label"] = "requiredMinimum"
        # Adding Cell4
        cell4 = cell.copy()
        cell4["v"] = temperature_uom.strip()
        cell4["label"] = "temperatureUom"

        cells_to_be_appended.extend([cell1, cell2, cell3, cell4])

    return cells_to_be_appended


def generate_weight_cells(cell, parsed_value_list):
    """Generate weight cells after weight parsing"""
    cells_to_be_appended = list()
    label = cell.get("label")
    if len(parsed_value_list) == 3:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["v"] = number.strip()
        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = label + "Uom"
        cell2["v"] = uom.strip()
        cells_to_be_appended.extend([cell1, cell2, cell3])

        # For extra element
        if parsed_value_list[-1]:
            cell3 = cell.copy()
            cell3["label"] = label + "_1"
            cell3["v"] = parsed_value_list[-1].strip()
            cells_to_be_appended.append(cell3)

    return cells_to_be_appended


def generate_volume_cells(cell, parsed_value_list):
    cells_to_be_appended = list()
    label = cell.get("label")
    if len(parsed_value_list) == 3:
        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["v"] = number.strip()
        # Adding Cell2
        cell2 = cell.copy()

        cell2["label"] = label + "Uom"
        cell2["v"] = uom.strip()

        cells_to_be_appended.extend([cell1, cell2])
        # For extra element
        if parsed_value_list[-1]:
            cell3 = cell.copy()
            cell3["label"] = label + "_1"
            cell3["v"] = parsed_value_list[-1].strip()
            cells_to_be_appended.append(cell3)

    return cells_to_be_appended


def genereate_package_count_cells(cell, parsed_value_list, utility_mapped_code_list={}):
    cells_to_be_appended = list()
    label = cell.get("label")
    if len(parsed_value_list) == 3:
        # Retaining the original cell

        number = parsed_value_list[0]
        uom = parsed_value_list[1]

        # Adding Cell1
        cell1 = cell.copy()

        cell1["v"] = number.strip()
        # Adding Cell2
        cell2 = cell.copy()

        if "inner" in label:
            cell2["label"] = "innerPackageType"
        elif "total" in label:
            cell2["label"] = "totalPackageType"
        else:
            cell2["label"] = "packageType"
        cell2["v"] = uom.strip()
        try:
            if "innerPackageType" in cell2["label"]:
                inner_package_type_mapping = utility_mapped_code_list.get(
                    "innerPackageType", []
                )
                for ip in inner_package_type_mapping:
                    if cell2["v"].lower() == ip["value"].lower():
                        cell2["v"] = ip["key"]
                        break
        except:
            print(traceback.print_exc())
        cells_to_be_appended.extend([cell, cell1, cell2])
        # For extra element
        if parsed_value_list[-1]:
            cell3 = cell.copy()
            cell3["label"] = label + "_1"
            cell3["v"] = parsed_value_list[-1].strip()
            cells_to_be_appended.append(cell3)

    return cells_to_be_appended
