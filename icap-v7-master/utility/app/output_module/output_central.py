import traceback

from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

from .output_cw1 import output_cw1_main
from .regular_output import regular_output_main
from .utils import reduce_data_json_for_output_json
from .helper import restructure_output_json

"""
API that takes a data json and converts that to output json/other filetypes.

"""


def check_skipped_labels(label):
    """Check if label is in skip labels"""
    if label and label.lower() in ["None", "notInUse", "", "filler"]:
        return True
    return False

def create_output_json_from_data_json(data_json):
    simplified_data = {}
    simplified_data["tables"] = []
    for document in data_json.get("nodes", []):
        simplified_data["Document Issuer"] = document.get("Vendor")
        for node in document.get("children", []):
            try:
                if node.get("type") == "key":
                    for key_object in node.get("children", []):
                        # Skip for not in use
                        if key_object.get("notInUse"):
                            continue
                        try:
                            if key_object["v"]:
                                if key_object.get("children",[]):
                                    sub_key_data = []
                                    for sub_key in key_object["children"]:
                                        # Skip for not in use
                                        if sub_key.get("notinUse"):
                                            continue
                                        try: 
                                            if sub_key["v"]:
                                                sub_key_data.append({sub_key["label"]: sub_key["v"]})
                                        except:
                                            continue
                                    simplified_data[key_object["label"]] = sub_key_data
                                else:
                                    if key_object.get("qualifierParent"):
                                        qualifier = key_object.get("qualifierParent")
                                        if qualifier not in simplified_data.keys():
                                            simplified_data[qualifier] = []
                                        simplified_data[qualifier].append({key_object.get("label"):key_object.get("v")})
                                    else:
                                        simplified_data[key_object["label"]] = key_object["v"]
                        except:
                            print(traceback.print_exc())
                            continue

                elif node.get("type") == "table":
                    table_data = {}
                    table_data["table_name"] = node.get("table_name")
                    table_data["data"] = []
                    for row in node.get("children", []):
                        row_data = {}
                        for cell in row.get("children", []):
                            label = cell["label"]
                            if check_skipped_labels(label):
                                continue
                            try:
                                if cell.get("v"): row_data[cell["label"]] = cell["v"]
                            except: 
                                continue
                        table_data["data"].append(row_data)

                    if not table_data.get("data"):
                        continue
                    
                    if table_data not in simplified_data["tables"]:
                        simplified_data["tables"].append(table_data)
                else:
                    continue
            except:
                import traceback
                print(traceback.print_exc())
                continue

    return simplified_data

def output_json(request_data):
    try:
        print("Generating output Json")
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)
        request_data["data_json"] = reduce_data_json_for_output_json(request_data)
        # output_json = create_output_json_from_data_json(request_data.get("data_json"))
        # print("output_json",output_json)
        # set_redis_data(job_id, "output_json", output_json)

        # result = {"job_id": job_id, "status_code": 200, "messages": []}

        # publish("output_json_response", "to_pipeline", result)
        cw1 = None

        project_type = request_data["project"]

        try:
            definitions = request_data.get("definitions")[0]
            cw1 = definitions.get("cw1")
            definition_settings = request_data.get("definition_settings", {})
            master_dictionaries = request_data.get("master_dictionaries")

            output_field_allowlist = master_dictionaries.get(
                "output_field_allowlist", {}
            )
            output_field_allowlist_project = output_field_allowlist.get("data", {}).get(
                project_type, {}
            )
            custom_output_projects = definition_settings.get("projectSettings", {}).get(
                "custom_output_projects", []
            )
        except:
            pass

        script_response = dict()

        multi_table = None
        table_model_name = None
        try:
            table_definitions = definitions["table"]
            for table_definition_idx, table_definition in enumerate(table_definitions):
                table_model = table_definition["table_definition_data"]["models"]
                try:
                    table_model_name = table_model["type"]
                    if "multishipment" in table_model_name:
                        multi_table = True
                except:
                    print(traceback.print_exc())
                    multi_table = None
        except:
            pass

        if project_type not in custom_output_projects:
            if multi_table:
                print("Calling Multi Shipment Output")
                from customs_output.output_multi_shipment import (
                    output_multi_shipment_main,
                )

                script_response = output_multi_shipment_main(request_data)
            elif cw1:
                script_response = output_cw1_main(request_data)
                script_response["output_json"] = restructure_output_json(
                    output_field_allowlist_project, script_response["output_json"]
                )
            else:
                script_response = regular_output_main(request_data)
                script_response["output_json"] = restructure_output_json(
                    output_field_allowlist_project, script_response["output_json"]
                )
        else:
            """Please import customs_output_central from a folder inside robot
            scripts/robots/customs -- something in this order
            from robot.customs import main as customs_output_central


            This function call has to return a output json and a json version
            Depending on the project type and docType -- if the
            project type is
            C -- has to follow invoice schema
            if (B+C) or only B -- has to follow customs booking api schema



            script_response = customs_output_central(request_data)

            Please maintain all sort of versioning in sharepoint/git for this specific robot file
            """
            from customs_output.customs_output_central import customs_output_central

            print("Calling customs output central")
            script_response = customs_output_central(request_data)

            pass

        error = script_response.get("error")
        messages = script_response.get("messages")

        if not error:
            output_json = script_response.get("output_json")
            output_json_version = script_response.get("outputJsonVersion")

            if not output_json:
                output_json = {}

            set_redis_data(job_id, "output_json", output_json)

            result = {"job_id": job_id, "status_code": 200, "messages": messages}

            publish("output_json_response", "to_pipeline", result)
            return

        else:
            result = {
                "job_id": job_id,
                "error": str(error),
                "messages": messages,
                "traceback": traceback.print_exc(),
                "status_code": 400,
            }
            publish("output_json_response", "to_pipeline", result)
            return

    except Exception as error:
        result = {
            "job_id": job_id,
            "error": str(error),
            "messages": [],
            "traceback": traceback.print_exc(),
            "status_code": 400,
        }
        publish("output_json_response", "to_pipeline", result)
