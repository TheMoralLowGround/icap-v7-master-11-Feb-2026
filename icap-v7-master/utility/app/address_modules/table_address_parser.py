import traceback

from app.address_modules.address_custom import custom_address_parser
from app.address_modules.simple_detectors.company_by_email import (
    detect_company_by_email_and_rearrange,
)
from app.address_modules.simple_detectors.trim_till_country import trim_address

from ..response_formator import populate_error_response


def table_address_parser(d_json, address_keys, definitions, request_data, project):
    docs = d_json["nodes"]
    master_dictionaries = request_data.get("master_dictionaries")

    # store the definitions
    try:
        definition_settings = request_data.get("definition_settings")
    except:
        response = populate_error_response(
            data={},
            error="definition_settings not found",
            traceback=traceback.print_exc(),
        )
        return response

    try:
        key_options_items = (
            definition_settings.get("options", {}).get("options-keys", {}).get("items")
        )

    except:
        response = populate_error_response(
            data={}, error="keyOptions Items not found", traceback=traceback.print_exc()
        )
        return response

    for input_doc_idx, target_doc in enumerate(docs):
        nodes = target_doc["children"]

        for input_node_idx, target_node in enumerate(nodes):
            if target_node["type"] == "table":
                rows = target_node["children"]

                for input_row_idx, target_row in enumerate(rows):
                    cells = target_row["children"]

                    for input_cell_idx, target_cell in enumerate(cells):
                        label = target_cell.get("label")
                        if label in address_keys:
                            cell_value = target_cell.get("v")
                            co_ordinates = target_cell.get("co_ordinates")
                            if cell_value:
                                try:
                                    address = custom_address_parser(
                                        cell_value,
                                        definitions,
                                        master_dictionaries,
                                        project,
                                    )
                                    for address_key, address_value in address.items():
                                        if address_key.lower() == "shortcode":
                                            address_key = "addressshortcode"
                                        address_keyoption = label + address_key
                                        address_keyoption = address_keyoption.lower()
                                        for key_options_item in key_options_items:
                                            key_option_value = key_options_item.get(
                                                "keyValue"
                                            )
                                            if (
                                                key_option_value.lower()
                                                == address_keyoption.lower()
                                            ):
                                                name_label = label + "name"
                                                name_label = name_label.lower()
                                                if (
                                                    name_label
                                                    == key_option_value.lower()
                                                ):
                                                    target_cell[
                                                        "label"
                                                    ] = key_option_value
                                                    target_cell["v"] = address_value
                                                else:
                                                    new_cell = {
                                                        "label": key_option_value,
                                                        "v": address_value,
                                                        "address_generated": True,
                                                        "pos": "",
                                                        "pageId": "",
                                                        "STATUS": "0",
                                                        "type": "cell",
                                                        "id": target_cell["id"]
                                                        + "_address_generated",
                                                    }
                                                    if co_ordinates:
                                                        new_cell[
                                                            "co_ordinates"
                                                        ] = co_ordinates
                                                    cells.append(new_cell)
                                except:
                                    print(traceback.print_exc())

    return d_json
