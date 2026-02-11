import copy
import json
import traceback

from app.misc_modules.unique_id import assign_unique_id_helper
from app.rules_normalizers_module.table_rules_centre import get_first_valid_row


def process(request_data, d_json):
    """
    Fucntion to check if volume uom is present in a table row if that row contains
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
                            empty_volume_row = False
                            dimension_present = False
                            volume_uom_present = False
                            cells = row["children"]
                            dim_idx = None
                            # dim_val = None
                            for x_idx, x in enumerate(cells):
                                if "volume" in x["label"].lower():
                                    dimension_present = True
                                    if row_idx == first_row:
                                        first_row_had_dim = True
                                    dim_idx = x_idx
                                    if x.get("v", "").strip() == "":
                                        empty_volume_row = True
                                    # dim_val = x["v"]

                                elif ("volumeuom" in x["label"].lower()) and (
                                    not "inner" in x["label"].lower()
                                ):
                                    volume_uom_present = True

                            if not dimension_present:
                                if not first_row_had_dim:
                                    breakout = True

                            if not breakout:
                                if dimension_present and (not volume_uom_present) and not empty_volume_row:
                                    volume_uom_cell = dict()
                                    volume_uom_cell["v"] = "MTQ"
                                    volume_uom_cell["pos"] = ""
                                    volume_uom_cell["pageID"] = ""
                                    volume_uom_cell["STATUS"] = "0"
                                    volume_uom_cell["label"] = "volumeuom"
                                    volume_uom_cell["type"] = "cell"
                                    volume_uom_cell["is_profile_key_found"] = True
                                    try:
                                        row["children"].insert(
                                            dim_idx + 1, volume_uom_cell
                                        )
                                    except:
                                        try:
                                            row["children"].insert(
                                                dim_idx, volume_uom_cell
                                            )
                                        except:
                                            row["children"].append(volume_uom_cell)
                                assign_unique_id_helper(row)  # Assigning unique id
                        except:
                            print(traceback.print_exc())
                            pass

        except:
            print(traceback.print_exc())
            pass

    return d_json
 