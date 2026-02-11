import copy
import logging
from typing import Dict, Any
from producer import publish
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awb_hawb_agents.date_validator_agent import run_awb_or_hawb_date_validator_agent
from awb_hawb_agents.hwb_number_supplier_validator_agent import (
    run_awb_or_hawb_no_and_supplier_validator_agent,
)
from sub_doc_class_agents.sub_doc_class_selector_agents import (
    run_sub_doc_class_selector_agent,
)
from cdz_data_modification_agents.cdz_data_modification_agent import (
    run_cdz_data_modification_agent,
)
from dynamic_content_creation_agents.dynamic_content_creation_agent import (
    run_dynamic_content_creation_agent,
)
from shipment_table_agents.shipment_table_agent import (
    run_shipment_table_agent,
)
from utils.normalized_process_or_project_name import normalize_process_or_project_name

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def run_ai_agents(data):

    active_agents = data.get("active_agents", [])
    output_queue = data.get("output_queue")
    client_id = data.get("client_id")
    batch_id = data.get("batch_id")
    transaction_id = data.get("transaction_id")
    message_type = data.get("message_type")
    service_identifier = data.get("service_identifier")
    combined_msg = {}
    combined_sub_msg = {}
    combined_color_code = {}
    combined_status_code = {}
    combined_error = {}
    try:
        for idx, agent_name in enumerate(active_agents):
            logger.info(f"Running agent {idx}: {agent_name}")
            if agent_name == "hbl_mbl":
                updated_combined_data_json, msg, sub_msg, color_code, status_code, error =  sub_doc_class_selector_task(data)
                combined_msg[agent_name] = msg
                combined_sub_msg[agent_name] = sub_msg
                combined_color_code[agent_name] = color_code
                combined_status_code[agent_name] = status_code
                combined_error[agent_name] = error
                data["combined_data_json"] = updated_combined_data_json
                
            elif agent_name == "data_modification":
                updated_combined_data_json, msg, sub_msg, color_code, status_code, error = cdz_data_modification_task(data)
                combined_msg[agent_name] = msg
                combined_sub_msg[agent_name] = sub_msg
                combined_color_code[agent_name] = color_code
                combined_status_code[agent_name] = status_code
                combined_error[agent_name] = error
                data["combined_data_json"] = updated_combined_data_json
                
                
            elif agent_name == "shipment_table":
                updated_combined_data_json, msg, sub_msg, color_code, status_code, error = shipment_table_agent_task(data)
                combined_msg[agent_name] = msg
                combined_sub_msg[agent_name] = sub_msg
                combined_color_code[agent_name] = color_code
                combined_status_code[agent_name] = status_code
                combined_error[agent_name] = error
                data["combined_data_json"] = updated_combined_data_json
                
            elif agent_name == "dynamic_content_creation":
                updated_combined_data_json, msg, sub_msg, color_code, status_code, error = dynamic_content_creation_agent_task(data)
                combined_msg[agent_name] = msg
                combined_sub_msg[agent_name] = sub_msg
                combined_color_code[agent_name] = color_code
                combined_status_code[agent_name] = status_code
                combined_error[agent_name] = error
                data["combined_data_json"] = updated_combined_data_json

        result = {
                "batch_id": batch_id,
                "active_agents": active_agents,
                "service_identifier": service_identifier,
                "message_type": message_type,
                "output_queue": output_queue,
                "client_id": client_id,
                "message": combined_msg,
                "sub_message": combined_sub_msg,
                "combined_data_json": data["combined_data_json"],
                "result": data["combined_data_json"],
                "remarks": [],
                "color_code": combined_color_code,
                "transaction_id": transaction_id,
                "status_code": combined_status_code,
                "error":combined_error
            }
        publish('ai_agent_response', 'to_pipeline', result)
    except Exception as error:
        logger.error(f"Error in run_ai_agents: {str(error)}")
        all_error_msg = f"Process failed: {str(error)}"
        result = {
                "batch_id": batch_id,
                "active_agents": active_agents,
                "service_identifier": service_identifier,
                "message_type": message_type,
                "output_queue": output_queue,
                "client_id": client_id,
                "message": {"all": all_error_msg},
                "sub_message": {"all": ""},
                "combined_data_json": {},
                "remarks": [],
                "color_code": {"all": "red"},
                "status_code": {"all": 400},
                "transaction_id": transaction_id,
                "error": {"all": all_error_msg}
        }
        publish('ai_agent_response', 'to_pipeline', result)
        
  
        
def awb_hawb_date_validator_task(data: Dict[str, Any]):
    """RABBITMQ task for date validation"""
    batch_id = data.get("batch_id")
    AGENT_NAME = "Transportation_Date_Validator_Agent"

    logger.info(f"Starting date validation for batch {batch_id}")

    ra_json = data.get("ra_json")
    data_json = data.get("data_json")
    message_type = data.get("message_type")
    other_data_jsons = data.get("other_data_jsons", [])
    other_ra_jsons = data.get("other_ra_jsons", [])
    transaction_id = data.get("transaction_id")

    try:
        data_payload_for_reasoning = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": "reasoning",
            "message": "",
            "sub_message": "",
            "remarks": [],
            "color_code": "",
            "transaction_id": transaction_id,
            "status_code": 200,
        }

        result_from_agent, color_code, position_data = (
            run_awb_or_hawb_date_validator_agent(
                ra_json,
                other_ra_jsons,
                data_json,
                other_data_jsons,
                data_payload_for_reasoning,
            )
        )

        result = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": message_type,
            "message": result_from_agent,
            "sub_message": "",
            "remarks": [],
            "color_code": color_code,
            "position_data": position_data,
            "transaction_id": transaction_id,
            "status_code": 200,
        }

        logger.info(f"Date validator result for batch {batch_id}: {result}")
        publish('ai_agent_response', 'to_pipeline', result)

    except Exception as error:
        logger.error(f"Date validator failed for batch {batch_id}: {error}")
        result = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": message_type,
            "message": f"Process failed: {str(error)}",
            "sub_message": "",
            "remarks": [],
            "color_code": "red",
            "position_data": {},
            "status_code": 400,
            "transaction_id": transaction_id,
            "error": f"Process failed: {str(error)}",
        }
        publish('ai_agent_response', 'to_pipeline', result)


def awb_or_hawb_no_and_supplier_validator_task(data: Dict[str, Any]):
    """RABBITMQ task for entity validation"""
    batch_id = data.get("batch_id")
    AGENT_NAME = "Entity_Validator_Agent"

    logger.info(f"Starting entity validation for batch {batch_id}")

    ra_json = data.get("ra_json")
    data_json = data.get("data_json")
    message_type = data.get("message_type")
    other_data_jsons = data.get("other_data_jsons", [])
    other_ra_jsons = data.get("other_ra_jsons", [])
    transaction_id = data.get("transaction_id")

    try:
        data_payload_for_reasoning = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": "reasoning",
            "message": "",
            "sub_message": "",
            "remarks": [],
            "color_code": "",
            "transaction_id": transaction_id,
            "status_code": 200,
        }

        (
            supplier_validator_msg,
            color_code_supplier,
            hwb_validation_msg,
            color_code_hwb,
        ) = run_awb_or_hawb_no_and_supplier_validator_agent(
            data_json,
            other_data_jsons,
            ra_json,
            other_ra_jsons,
            data_payload_for_reasoning,
        )

        result = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": message_type,
            "message": supplier_validator_msg,
            "sub_message": "",
            "remarks": [],
            "color_code": color_code_supplier,
            "transaction_id": transaction_id,
            "status_code": 200,
        }
        publish('ai_agent_response', 'to_pipeline', result)

        result = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": message_type,
            "message": hwb_validation_msg,
            "sub_message": "",
            "remarks": [],
            "color_code": color_code_hwb,
            "transaction_id": transaction_id,
            "status_code": 200,
        }
        publish('ai_agent_response', 'to_pipeline', result)

    except Exception as error:
        logger.error(f"Entity validator failed for batch {batch_id}: {error}")
        result = {
            "batch_id": batch_id,
            "agent_name": AGENT_NAME,
            "message_type": message_type,
            "message": f"Process failed: {str(error)}",
            "sub_message": "",
            "remarks": [],
            "color_code": "red",
            "status_code": 400,
            "transaction_id": transaction_id,
            "error": f"Process failed: {str(error)}",
        }
        publish('ai_agent_response', 'to_pipeline', result)


def sub_doc_class_selector_task(data: Dict[str, Any]):
    """RABBITMQ task for sub doc class selection"""
    batch_id = data.get("batch_id")
    AGENT_NAME = "hbl_mbl"

    logger.info(f"Starting sub doc class selection for batch {batch_id}")

    combined_data_json = data.get("combined_data_json")
    project_name = data.get("project_name")
    project_name = normalize_process_or_project_name(project_name)
    combined_ra_json = data.get("combined_ra_json")
    process_name = data.get("process_name")
    process_name = normalize_process_or_project_name(process_name)
    transaction_id = data.get("transaction_id")
    message_type = data.get("message_type")
    
    try:
        updated_combined_data_json, msg = run_sub_doc_class_selector_agent(
            combined_ra_json, combined_data_json, project_name
        )
        
        return updated_combined_data_json, msg, "", "green", 200, ""
    except Exception as error:
        logger.error(f"Sub doc class selector failed for batch {batch_id}: {error}")
        return combined_data_json, f"Process failed: {str(error)}", "", "red", 400, f"Process failed: {str(error)}"
        


def cdz_data_modification_task(data: Dict[str, Any]):
    """RABBITMQ task for data modification"""

    def cdz_plus_civ_checker(combined_data_json):
        is_b_plus_civ = False
        combined_data_json_new = []
        civ_data_json_all = []
        for single_data_json in combined_data_json:
            if "CustomsDeclaration(B+CIV)" in single_data_json["Project"]:
                is_b_plus_civ = True
                if single_data_json["DocType"].lower().replace(" ","").strip() == "commercialinvoice":
                    for doc_wise_data_json in single_data_json["nodes"]:
                        skeleton_civ_data_json = copy.deepcopy(single_data_json)
                        skeleton_civ_data_json["nodes"] = []
                        skeleton_civ_data_json["nodes"].append(doc_wise_data_json)
                        civ_data_json_all.append([skeleton_civ_data_json])   
                else:
                    combined_data_json_new.append(single_data_json)
            else:
                combined_data_json_new.append(single_data_json)
        return combined_data_json_new, civ_data_json_all, is_b_plus_civ
        
    batch_id = data.get("batch_id")
    AGENT_NAME = "data_modification"

    logger.info(f"Starting data modification for batch {batch_id}")

    combined_data_json = data.get("combined_data_json")
    project_name = data.get("project_name")
    project_name = normalize_process_or_project_name(project_name)
    combined_ra_json = data.get("combined_ra_json")
    process_name = data.get("process_name")
    process_name = normalize_process_or_project_name(process_name)
    transaction_id = data.get("transaction_id")
    message_type = data.get("message_type")
    process_keys = data.get("process_keys")

    try:
        combined_output = []
        combined_data_json_new, civ_data_json_all, is_b_plus_civ = cdz_plus_civ_checker(combined_data_json)

        output_cdz = run_cdz_data_modification_agent(combined_data_json_new, process_keys)
        if is_b_plus_civ:
            output_cdz["type"] = "booking"

        combined_output.append(output_cdz)

        for civ_data_json in civ_data_json_all:
            output_civ = run_cdz_data_modification_agent(civ_data_json, [])
            output_civ["type"] = "commercial-invoice"
            combined_output.append(output_civ)

        return combined_output, "CDZ data modification completed", "", "green", 200, ""
    except Exception as error:
        logger.error(f"CDZ data modification failed for batch {batch_id}: {error}")
        return combined_data_json, f"Process failed: {str(error)}", "", "red", 400, f"Process failed: {str(error)}"
    

def shipment_table_agent_task(data: Dict[str, Any]):
    """RABBITMQ task for shipment table processing"""
    batch_id = data.get("batch_id")
    AGENT_NAME = "shipment_table"

    logger.info(f"Starting shipment table processing for batch {batch_id}")

    combined_data_json = data.get("combined_data_json")
    project_name = data.get("project_name")
    project_name = normalize_process_or_project_name(project_name)
    combined_ra_json = data.get("combined_ra_json")
    process_name = data.get("process_name")
    client_id = data.get("client_id")
    output_queue = data.get("output_queue")
    transaction_id = data.get("transaction_id")
    rabbitmq_message_type = data.get("rabbitmq_message_type")
    message_type = data.get("message_type")
    service_identifier = data.get("service_identifier")
    process_field = data.get("process_keys")

    try:
        updated_combined_data_json, msg = run_shipment_table_agent(combined_ra_json, combined_data_json, process_field)

        return updated_combined_data_json, msg, "", "green", 200, ""
    except Exception as error:
        logger.error(f"Shipment table processing failed for batch {batch_id}: {error}")
        return combined_data_json, f"Process failed: {str(error)}", "", "red", 400, f"Process failed: {str(error)}"


def dynamic_content_creation_agent_task(data: Dict[str, Any]):
    """RABBITMQ task for dynamic content creation"""
    batch_id = data.get("batch_id")
    AGENT_NAME = "dynamic_content_creation"

    logger.info(f"Starting dynamic content creation for batch {batch_id}")

    combined_data_json = data.get("combined_data_json")
    project_name = data.get("project_name")
    project_name = normalize_process_or_project_name(project_name)
    combined_ra_json = data.get("combined_ra_json")
    process_name = data.get("process_name")
    client_id = data.get("client_id")
    output_queue = data.get("output_queue")
    transaction_id = data.get("transaction_id")
    rabbitmq_message_type = data.get("rabbitmq_message_type")
    message_type = data.get("message_type")
    service_identifier = data.get("service_identifier")
    process_field = data.get("process_keys")

    try:
        updated_combined_data_json, msg = run_dynamic_content_creation_agent(combined_ra_json, combined_data_json, process_field)

        return updated_combined_data_json, msg, "", "green", 200, ""
    except Exception as error:
        logger.error(f"Dynamic content creation failed for batch {batch_id}: {error}")
        return combined_data_json, f"Process failed: {str(error)}", "", "red", 400, f"Process failed: {str(error)}"

