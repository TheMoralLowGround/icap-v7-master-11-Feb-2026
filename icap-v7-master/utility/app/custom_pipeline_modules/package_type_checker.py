import copy
import json
import traceback

from app.misc_modules.unique_id import assign_unique_id_helper
from app.rules_normalizers_module.table_rules_centre import get_first_valid_row


def process(request_data, d_json):
    """
    Fucntion to check if package type is present in a table row if that row contains
    the dimension column in it
    """
    # @Emon on 14/10/2022 First valid row finder added
    # Version 1.0.15102022

    docs = d_json["nodes"]

    # added by emon on 19/05/2022
    test_document_trigger = None
    try:
        test_document_trigger = request_data["document_id"]
    except:
        pass

    for input_doc_idx, target_doc in enumerate(docs):
        try:
            table = None

            for x in target_doc["children"]:
                try:
                    if "table" in x["type"]:
                        table = x
                except:
                    print(x)

            # Figuring a way out here
            if test_document_trigger != None:
                if test_document_trigger != target_doc["id"]:
                    continue

            for x in target_doc["children"]:
                if "table" in x.get("type", ""):
                    table = x
                    first_row_had_dim = False
                    first_row = get_first_valid_row(table["children"])
                    for row_idx, row in enumerate(table["children"]):
                        try:
                            breakout = False
                            empty_package_count_row = False
                            is_package_count_present = False
                            package_type_present = False
                            cells = row["children"]
                            dim_idx = None
                            # dim_val = None
                            for x_idx, x in enumerate(cells):
                                if x.get("label", "").lower().startswith("packagecount"):
                                    is_package_count_present = True
                                    if row_idx == first_row:
                                        first_row_had_dim = True
                                    dim_idx = x_idx
                                    if x.get("v", "").strip() == "":
                                        empty_package_count_row = True
                                    # dim_val = x["v"]

                                elif ("packagetype" in x["label"].lower()) and (
                                    not "inner" in x["label"].lower()
                                ):
                                    package_type_present = True

                            if not is_package_count_present:
                                if not first_row_had_dim:
                                    breakout = True

                            if not breakout:
                                if is_package_count_present and (not package_type_present) and not empty_package_count_row:
                                    package_type_cell = dict()
                                    package_type_cell["v"] = "PCE"
                                    package_type_cell["pos"] = ""
                                    package_type_cell["pageID"] = ""
                                    package_type_cell["STATUS"] = "0"
                                    package_type_cell["label"] = "packageType"
                                    package_type_cell["type"] = "cell"
                                    package_type_cell["is_profile_key_found"] = True
                                    try:
                                        row["children"].insert(
                                            dim_idx + 1, package_type_cell
                                        )
                                    except:
                                        try:
                                            row["children"].insert(
                                                dim_idx, package_type_cell
                                            )
                                        except:
                                            row["children"].append(package_type_cell)
                                assign_unique_id_helper(row)  # Assigning unique id
                        except:
                            print(traceback.print_exc())
                            pass

        except:
            print(traceback.print_exc())
            pass

    return d_json
 