import traceback
from app.misc_modules.status_assigner import assing_node_status
from app.misc_modules.list_to_str import list_to_string_conversion
from app.key_central.key_module_central import (
    extract_anchor_thresholds,
    update_shipment_type_key,
)
from redis_utils import get_redis_data, set_redis_data
from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

from app.add_ons.dictionary_central import dictionary_main

# from app.add_ons.lookup_central import lookup_central_main
from app.add_ons.lookup_main import lookup_central_main
from app.add_ons.table_lookups import table_lookups_main
from app.add_ons.validation import validation_main
from app.address_modules.table_address_parser import table_address_parser
from app.custom_pipeline_modules import moderator
from app.custom_pipeline_modules.auto_rule_applier import auto_apply_rule
from app.custom_pipeline_modules.not_in_use_centre import root_out_notInUse
from app.custom_pipeline_modules.package_type_checker import process as packTypeChecker
from app.custom_pipeline_modules.volume_uom_setter import process as volumeUomSetter
from app.custom_pipeline_modules.trunication import trunicator
from app.custom_pipeline_modules.v4_alternators import (
    d_json_alternator_v4,
    postprocessing_alternator_v4,
)
from app.custom_pipeline_modules.value_merger import (
    merge_value_keys,
    merge_table_key_items,
)
from app.json_chunking import json_chunking_main
from app.key_central import key_extractor_function
from app.key_central.key_module_central import extract_anchor_thresholds

# from app.parsing_central.original_parsing_centre import parser_main
from app.key_central.keychildren_appender import key_child_appender_process
from app.misc_modules.duplicate_remover import duplicate_removal
from app.misc_modules.list_to_str import list_to_string_conversion
from app.misc_modules.status_assigner import assing_node_status
from app.parsing_central.parsing_centre import (
    parser_main,
    transfer_singleColumn_type_to_table,
)
from app.rules_normalizers_module.rules_functionality import rules_centre
from app.rules_normalizers_module.table_normalizer import normalize_table
from app.rules_normalizers_module.table_rules_centre import table_rules_process
from app.labels_processing import rename_duplicate_labels

from .alternator import d_json_alternator

"""
Central Utility Docker API Call.

Precendence:
Key Extraction> Parsing Central > Lookups > Rules > Normalizer.
Contains some alternating scripts in between this chain of actions.

"""


def check_if_multi_shipment(definitions):
    definition = definitions[0]
    if definition == {}:
        return None
    cw1 = definition.get("cw1")
    table_definitions = definition.get("table")
    table_model_name = None
    multi_table = None
    for table_definition_idx, table_definition in enumerate(table_definitions):
        table_model = table_definition["table_definition_data"]["models"]
        try:
            table_model_name = table_model["type"]
            if "multishipment" in table_model_name:
                multi_table = True
        except:
            print(traceback.print_exc())
            multi_table = None
    return multi_table


def UtilityCentral(request_data):
    # @Emon on 19/09/2022 - Key Extractor function has been sliced off from this script
    # @Emon on 20/09/2022 - notInUse Central was added
    # @Emon on 23/09/2022 - Seperated key extraction module
    # @Emon on 04/10/2022 - Added PackageType checker
    # @Emon on 10/05/2022 - Table Rules Added
    # @Emon on 08/10/2022 - Table Normalizer Added
    # @Emon on 16/10/2022 - Added auto rule adder
    # @Emon on 18/10/2022 - Child not to be displayed for non address keys
    # @Emon on 20/10/2022 - Rules refactored
    # @Emon on 21/10/2022 - Duplicate Removal also works for post rule duplicate references
    # @Emon on 23/10/2022 - Repetitive nodes were produced in front end bug fix
    # @Emon on 05/11/2022 - Lookups Feature Added added
    # @Emon on 05/12/2022 - Validations Added
    # @Emon on 05/12/2022 - Anchors updated
    # @Emon on 05/13/2022 - Anchors updated - Right Left added
    # @Emon on 16/02/2023 - Regex Extractor Added
    # @Emon on 14/05/2023 - Company Name Suffix Dictionary, Address Parser Updates(AstraZeneca), Trim Till Country, Lookups will display yellow when multiples of close match
    # @Emon on 22/05/2023 - Added Utility Caching
    # @Almas on 04/09/2023 - Adedd defintion settings to parser main
    # @Emon

    utility_central_version = "v7.0"  # By five means utility now has normalizer. Six - Lookups live. Seven- Validations Eight - Output CW1
    key_value_extractor_version = "5.04122023.01"
    messages = []
    messages.append(
        {
            "message": "Utility Version " + utility_central_version,
            "code": 200,
            "module": "Utility",
        }
    )
    messages.append(
        {
            "message": "KeyValueExtractor Version " + key_value_extractor_version,
            "code": 200,
            "module": "keyValueExtractor",
        }
    )

    try:
        print("Processing Request")
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)
        request_data["job_id"] = job_id
        definitions = request_data["definitions"]
        d_json = request_data["data_json"]
        master_dictionaries = request_data.get("master_dictionaries")
        project = request_data.get("project")
        # print("master",master_dictionary)
        if definitions == []:
            definitions = [{}]
        # For anchors
        json_chunking_thresholds = extract_anchor_thresholds(request_data)
        chunking_dictionary = json_chunking_main(
            request_data["ra_json"], json_chunking_thresholds
        )
        set_redis_data(job_id, "chunking_dictionary", chunking_dictionary)

        # Fixing
        for x_idx, x in enumerate(d_json.get("nodes")):
            for y_idx, y in enumerate(x.get("children")):
                if y == []:
                    d_json["nodes"][x_idx]["children"].pop(y_idx)
                    request_data["data_json"] = d_json

        try:
            definition_settings = request_data.get("definition_settings")
        except:
            result = {
                "job_id": job_id,
                "error": "definition_settings not found",
                "traceback": traceback.print_exc(),
                "status_code": 400,
            }
            publish("keyval_extractor_response", "to_pipeline", result)
            return

        try:
            key_options_items = (
                definition_settings.get("options", {})
                .get("options-keys", {})
                .get("items",[])
            )
        except:
            result = {
                "job_id": job_id,
                "error": "keyOptions Items not found",
                "traceback": traceback.print_exc(),
                "status_code": 400,
            }
            publish("keyval_extractor_response", "to_pipeline", result)
            return

        try:
            multi_table = check_if_multi_shipment(definitions)
        except:
            print(traceback.print_exc())
        # creating a list of addressBlock keyValues to run the parser
        address_keys = list()

        # lookupLables
        for item_settings_from_def in key_options_items:
            if item_settings_from_def["type"] == "addressBlock":
                address_keys.append(item_settings_from_def["keyValue"])

        skip_key = request_data["skip_key_processing"]

        if not skip_key:
            # Extract table and key items
            try:
                query_key_list = definitions[0].get("key", {}).get("items", [])
                d_json = key_extractor_function.main(
                    request_data=request_data,
                    d_json=d_json,
                    messages=messages,
                    query_key_list=query_key_list,
                )
                d_json = key_extractor_function.update_data_json_based_on_definition(request_data,d_json)
            except:
                #print(traceback.print_exc())
                pass
        # Update shipment_type_key for checkboxes
        try:
            d_json = update_shipment_type_key(d_json, request_data)
        except:
            print(traceback.print_exc())
        # Updated by Almas on 30/08/2022
        # Sending data json to Data Json Alternator
        try:
            definitions = request_data.get("definitions", [])
            cw1 = definitions[0].get("cw1") if definitions else None

            if not cw1:
                try:
                    d_json = d_json_alternator.process(d_json)
                except:
                    print(traceback.print_exc())
                    pass
            else:
                try:
                    d_json = d_json_alternator_v4.process(d_json)
                except:
                    print(traceback.print_exc())
                    pass
        except IndexError:
            pass

        try:
            # Sending data json to parsing centre

            d_json = parser_main(d_json, definition_settings, request_data)

        except:
            print(traceback.print_exc())
            pass

        try:
            d_json = packTypeChecker(request_data, d_json)
        except:
            print(traceback.print_exc())
            pass

        try:
            d_json = volumeUomSetter(request_data, d_json)
        except:
            print(traceback.print_exc())
            pass

        try:
            d_json = assing_node_status(d_json)
        except:
            print(traceback.print_exc())

        """
        try:
            d_json = table_address_parser(
                d_json, address_keys, definitions, request_data, project
            )
        except:
            print(traceback.print_exc())
            pass
        """

        if not skip_key:
            """
            # Creating key children for GUI
            d_json = key_child_appender_process(
                d_json, address_keys, definitions, request_data, project
            )
            """

            try:
                d_json = list_to_string_conversion(d_json)
            except:
                pass

            try:
                d_json = assing_node_status(d_json)
            except:
                print(traceback.print_exc())

            # Dictionary
            # try:
            #     d_json = dictionary_main(request_data, d_json)
            # except:
            #     print(traceback.print_exc())
            #     pass

            # Lookup under dev
            # try:
            #     d_json, messages = lookup_central_main(
            #         request_data, d_json, messages, master_dictionaries
            #     )
            # except:
            #     print(traceback.print_exc())
            #     pass

            # try:
            #     if not multi_table:
            #         d_json, messages = table_lookups_main(
            #             request_data, d_json, messages, master_dictionaries
            #         )
            # except:
            #     print(traceback.print_exc())
            #     pass

            # Sending data json to rules centre
            rules_version, d_json = rules_centre(request_data, d_json, address_keys)
            messages.append(
                {
                    "message": "Rules Version " + rules_version,
                    "code": 200,
                    "module": "Rules",
                }
            )

            try:
                d_json = auto_apply_rule(d_json, request_data)
            except:
                print(traceback.print_exc())
                pass

            try:
                d_json = duplicate_removal(d_json, request_data["definitions"])
            except:
                print(traceback.print_exc())
                pass

            try:
                d_json = root_out_notInUse(d_json, request_data)
            except:
                pass
        # Merge functionality for table
        try:
            d_json = merge_table_key_items(d_json, request_data, messages)
        except:
            print(traceback.print_exc())

        try:
            d_json = rename_duplicate_labels(d_json)
        except:
            print(traceback.print_exc())
        try:
            d_json = table_rules_process(request_data, d_json)
        except:
            pass

        try:
            d_json = normalize_table(request_data, d_json)
        except:
            print(traceback.print_exc())
            pass

        try:
            if multi_table:
                d_json, messages = table_lookups_main(
                    request_data, d_json, messages, master_dictionaries
                )
        except:
            print(traceback.print_exc())
            pass

        try:
            d_json = postprocessing_alternator_v4.process(d_json)
        except:
            print(traceback.print_exc())
            pass

        try:
            d_json = moderator.process(d_json)
        except:
            print(traceback.print_exc())
            pass

        try:

            d_json = merge_value_keys(d_json)
        except:
            print(traceback.print_exc())
            pass
        # try:
        #     d_json = transfer_singleColumn_type_to_table(d_json)
        # except:
        #     print(traceback.print_exc())

        if project in ("ShipmentCreate", "ShipmentUpdate"):
            try:
                d_json = trunicator(d_json)
            except:
                print(traceback.print_exc())
                pass
        try:
            # Validation Script Integration\

            d_json, messages = validation_main(request_data, d_json, messages)
        except:
            print(traceback.print_exc())
            pass
        data_json = d_json
        set_redis_data(job_id, "data_json", data_json)

        result = {
            "job_id": job_id,
            "messages": messages,
            "status_code": 200,
        }
        publish("keyval_extractor_response", "to_pipeline", result)

    except Exception as error:
        print(traceback.print_exc())
        result = {
            "job_id": job_id,
            "error": str(error),
            "traceback": traceback.print_exc(),
            "messages": messages,
            "status_code": 400,
        }
        publish("keyval_extractor_response", "to_pipeline", result)
