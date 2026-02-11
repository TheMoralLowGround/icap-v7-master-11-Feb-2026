"""
Organization: AIDocbuilder Inc.
File: flask_app.py
Version: 6.0
 
Authors:
    - Rageeb - Initial implementation
    - Emon - Code optimization
 
Last Updated By: Emon
Last Updated At: 2024-03-18
 
Description:
    This file contains core functionalities for processing document data using key grid processing, 
    table extraction, and JSON alteration. This file serves as a backbone for document processing.
 
Dependencies:
    - os, josn, random, traceback
    - Flask, jsonify, request from flask
    - CORS from flask_cors
    - alternator.d_json_alternator as alternator
    - extraction_process as table_extraction from algo.table_extraction_core
    - position_calculation_per_page from algo.automate_positionShift_cal
    - atm from algo.automated_table_model
    - chunk_process from algo.chunking
    - start_p as table_model_validation from algo.table_model_validation
    - publish from rabbitmq_publisher
    - get_redis_data, set_redis_data from redis_utils
 
Main Features:
    - Manage the complete workflow for document processing.
    - Fetch and store intermediate data.
    - Execute algorithm for structured data extraction.
    - Apply rules for extracting tabular data.
    - Modify the final JSON output to fit specific requirements.
    - Create and clean up temporary files during processing.
    - Handle the Automated Table Model (ATM) process.
    - Publish success or failure results to_pipeline.
"""
import json
import os
import random
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

import alternator.d_json_alternator as alternator
from algo.table_extraction_core import extraction_process as table_extraction
from algo.automate_positionShift_cal import position_calculation_per_page
from algo.automated_table_model import atm
from algo.chunking import chunk_process
from algo.table_model_validation import start_p as table_model_validation
from rabbitmq_publisher import publish
from redis_utils import get_redis_data, set_redis_data

TEMP_TH_FILENAME = "THRESHOLD_DATA.json"

SINGLE_COLUMN_EXTRACTOR_FILE_NAME = "./single_column_extractor"

app = Flask(__name__)
CORS(app)


def check_in_boundary(input_position, check_position):
    """
    Check whether the 'check_position' rectangle lies entirely within the 'input_position' rectangle.

    Args:
        input_position (str): Boundaries of the input rectangle.
        check_position (str): Boundaries of the rectangle to be checked.

    Returns:
        bool: True if 'check_position' is within 'input_position', otherwise False.

    Process Details:
        - Parse the boundary positions from the input string.
        - Verify the 'check_position' rectangle lies entirely within the 'input_position' rectangle.

    Notes:
        - Both input strings should contain exactly 4 comma-separated integers.
    """
    input_positions = [int(i) for i in input_position.split(",")]
    check_positions = [int(i) for i in check_position.split(",")]
    if (len(input_positions) == 4) and (len(check_positions) == 4):
        # Left, Top, Right, Bottom
        if (
            (input_positions[0] <= check_positions[0])
            and (input_positions[1] <= check_positions[1])
            and (input_positions[2] >= check_positions[2])
            and (input_positions[3] >= check_positions[3])
        ):
            return True

    return False


def checkIfKeyGridSetToFalse(request_data):
    """
    If the 'disableKeygrid' flag is set to 'true' in the provided request data or if keygrids should be skipped.

    Args:
        request_data (dict): Contain definitions and key configurations.

    Returns:
        bool: True if the 'disableKeygrid' flag is set to 'true' or key grids should be skipped, otherwise False.

    Process Details:
        - Check for the 'disableKeygrid' flag in the key model.
        - Determine if any 'keys' method is present in key items or table definitions.
        - Set the escape trigger if neither is found or if 'disableKeygrid' is enabled.

    Notes:
        - Exceptions are caught and logged for missing fields in the input data.
    """
    ESCAPE_TRIGGER = False
    try:
        key_definitions = request_data["definitions"][0]["key"]
    except:
        key_definitions = dict()

    key_model = None
    try:
        key_model = key_definitions["models"][0]
    except:
        pass
    try:
        if key_model:
            if "disableKeygrid" in key_model.keys() and (
                key_model["disableKeygrid"] == "true"
            ):
                ESCAPE_TRIGGER = True
    except:
        print(traceback.print_exc())
        pass

    # Auto escaping keygrids if not keys method
    try:
        keys_method_present = False
        key_items = key_definitions.get("items")
        for key_item in key_items:
            if key_item.get("type") == "keys":
                keys_method_present = True
        table_defs = request_data["definitions"][0]["table"]
        for table_def in table_defs:
            table_keys = table_def.get("table_definition_data").get("keyItems")
            for table_key in table_keys:
                if table_key.get("type") == "keys":
                    keys_method_present = True
        if not keys_method_present:
            ESCAPE_TRIGGER = True
    except:
        print(traceback.print_exc())
        pass

    return ESCAPE_TRIGGER


def block_data_adder(input_d_json, BLOCKS_OUTPUT_FILENAME):
    """
    Append block data from a file to the 'children' nodes in the input JSON.

    Args:
        input_d_json (dict): Input JSON object contain document nodes.
        BLOCKS_OUTPUT_FILENAME (str): Path to the file contain block data.

    Returns:
        Update the input JSON by appending block data to the children nodes.

    Process Details:
        - Read block data from the specific file.
        - Matche document nodes with block nodes by index and appends the block data.
        - Remove existing block entries before appending new data.

    Notes:
        - Blocks are not appended if the children of the corresponding node are empty.
    """
    try:
        f = open(BLOCKS_OUTPUT_FILENAME, "r")
        blocks_data_full = json.load(f)
        blocks_data = blocks_data_full["nodes"]
        docs = input_d_json["nodes"]
        for i, document in enumerate(docs):
            children = document["children"]
            if not children and not (blocks_data[i]["children"]):
                continue
            for node in children:
                if "blocks" in node["id"]:
                    children.remove(node)
            try:
                children.append(blocks_data[i]["children"])
            except:
                print("Blocks Appending Issue")
                pass
        f.close
    except:
        pass


def create_processed_json(input_json_object):
    """
    This function is executed upon no processed json is output from docbuilder to create export data.

    Args:
        input_json_object (dict): Input JSON object, which include data_json or ra_josn.

    Returns:
        dict: A processed JSON object ready to export.

    Process Details:
        - If 'data_json' exists in the input, it is returned with 'children' fields cleared.
        - Otherwise, the function initialize a new JSON structure from 'ra_json'.

    Notes:
        - Modify 'nodes' to ensure children are empty in the processed JSON.
    """
    content_in_use = input_json_object.copy()
    if "data_json" in content_in_use.keys():
        # if data_json already exists in temp_req then return that
        nodes = content_in_use["data_json"]["nodes"]
        for node in nodes:
            node["children"] = []  # empty children
        return content_in_use["data_json"]
    else:
        data_json = content_in_use["ra_json"]
        data_json["nodes"]["children"] = []
        return data_json


def get_process_logs(LOG_FILENAME, exec_time=" ", module="docbuilder"):
    """
    Read Logs from log file and return as messages.
    
    Args:
        LOG_FILENAME (str): Log file name which contain JSON-formatted messages.
        exec_time (str): Execution time to be appended to the log message.
        module (str): Module to be included in the log message.

    Returns:
        list: A list of formatted log messages.

    Process Details:
        - Read the log file.
        - Parse the log message, appends execution time and module.

    Notes:
        - Returns an empty list if the log file does not exist.
    """
    messages = []

    if os.path.exists(LOG_FILENAME):
        with open(LOG_FILENAME, "r") as f:
            message = json.loads((f.read()))

            message["message"] = message["message"] + " " + exec_time
            message["module"] = module
            messages.append(message)

    return messages


def get_process_logs_from_func(message, module="docbuilder"):
    """
    Read Logs from log file and return as messages.

    Args:
        message (dict): Contain the log message to be formatted.
        module (str): Module to be included in the log message.

    Returns:
        list: A list contain the formatted log message.

    Process Details:
        - Add the 'module' information to the input message.
        - Return the message as a single-item list.

    Notes:
        - processe the provided log dictionary.
    """
    messages = []

    message["message"] = message["message"]
    message["module"] = module
    messages.append(message)

    return messages


def start_process(request_data):
    """
    This function handle the processing of document data using key grid processing, table extraction, 
    and JSON alteration.

    Args:
        request_data (dict): Contain the job ID and input parameters.

    Returns:
        Result is handled via Redis and Rabbitmq.

    Process Details:
        - Generate a unique identifier for temporary files.
        - Clean up existing temp files to ensure a fresh processing state.
        - Execute the key grid processing algorithm if 'skip_key_processing' is False.
        - Runs the table extraction algorithm if 'skip_table_processing' is False.
        - Use 'table_extraction' for primary processing or a fallback 'create_processed_json' function.
        - Integrate block data into the final output if key grid processing is not skipped.
        - Modify the JSON output via the 'alternator.process' method.
        - Ensure temp files are removed to prevent file system clutter.
        - Store the final processed JSON data back into Redis.
        - Publish the success or failure response to_pipeline.

    Notes:
        - The function relies on Redis for intermediate storage and a messaging system for response handling.
        - Modular functions like 'table_extraction', 'block_data_adder', and 'alternator.process' conatin key logic.
    """
    try:
        job_id = request_data["job_id"]
        request_data = get_redis_data(job_id)

        log_message = {"message": "Docbuilder Failed to Run", "code": 400}

        # Set a random ID
        _id = str(random.randint(0, 50000))

        # Set Temporary file name
        TEMP_REQ_FILENAME = os.path.join("temp", ("temp_request_" + _id + ".json"))
        TEMP_EXPORT_FILENAME = os.path.join("temp", "processed_" + _id + ".json")

        # If Exist, Remove
        try:
            if os.path.exists(TEMP_REQ_FILENAME) or os.path.exists(
                TEMP_EXPORT_FILENAME
            ):
                os.remove(TEMP_REQ_FILENAME)
                os.remove(TEMP_EXPORT_FILENAME)
                print("Removed Temporary Files")
            else:
                pass
        except:
            pass

        content = request_data

        # Serializing json
        json_object = json.dumps(content)

        # Writing to sample.json
        with open(TEMP_REQ_FILENAME, "w") as outfile:
            outfile.write(json_object)

        skip_key = request_data["skip_key_processing"]
        skip_table = request_data["skip_table_processing"]
        
        master_dictionaries = request_data.get("master_dictionaries")
        
        CustomEntryChargesData = master_dictionaries.get("CustomEntryChargesData").get("data")

        # Added by emon on 09/10/2022 - Pre-Escaping keygrid if set to False
        try:
            skip_key = checkIfKeyGridSetToFalse(request_data)
        except:
            pass

        # Skip Features added by emon on 19/09/2022
        if not skip_key:
            # Keygrid process
            try:
                print("Running Keygrid")
                os.system("./keygrid_main" + (" " + _id))
                print("Keygrid successfully executed")
            except:
                print(traceback.format_exc())
                print("Keygrid Algo did not run")
                pass

        # Skip Features added by emon on 19/09/2022
        if not skip_table:
            # Run DocBuilder and get result
            # os.system(DOCBUILDER_FILE_NAME + (" "+_id))
            try:
                EXPORT_DATA, log_message = table_extraction(content, CustomEntryChargesData)

                if EXPORT_DATA is None:
                    EXPORT_DATA = create_processed_json(content)

            except Exception as e:
                """Backup in case the docbuilder does not produce processed json"""

                print("Processed json wasn't producted by docbuilder")
                print(e)
                EXPORT_DATA = create_processed_json(content)

        # Skip Features added by emon on 19/09/2022
        if not skip_key:
            """KEYGRID PRODUECS A BLOCK OUTPUT JSON FILE WHICH IS THEN ADDED TO THE EXPORT DATA
            THIS WAS KEPT SEPERATE NOT TO HURT THE FLOW OF DOCBUILDER IN CASE KEYGRID SO FILE FAILS @EMON 30/07/2022
            """
            # adding blocks data in export data
            BLOCKS_OUTPUT_FILENAME = os.path.join(
                "temp", "blocks_output_" + _id + ".json"
            )
            try:
                block_data_adder(EXPORT_DATA, BLOCKS_OUTPUT_FILENAME)
            except:
                print("Blocks could not be appended")
                # print(traceback.print_exc())
                pass

            try:
                if os.path.exists(BLOCKS_OUTPUT_FILENAME):
                    os.remove(BLOCKS_OUTPUT_FILENAME)
                    print("Removed Temporary Blocks Files")
                else:
                    pass
            except:
                pass

        # Alternation Process //NOT USED FREQUENTLY//CLOSE TO DEPRECIATION//EMON
        try:
            # JSON ALTERATION
            EXPORT_DATA = alternator.process(content, EXPORT_DATA)
        except:
            print("JSON Not altered")
            pass

        log_messages = get_process_logs_from_func(log_message)

        print(log_messages)

        # Lastly Remove the files after process
        try:
            if os.path.exists(TEMP_REQ_FILENAME) or os.path.exists(
                TEMP_EXPORT_FILENAME
            ):
                os.remove(TEMP_REQ_FILENAME)
                os.remove(TEMP_EXPORT_FILENAME)
                print("Removed Temporary Files")
            else:
                pass
        except:
            pass

        # Bug fix for a list as a document child
        for x_idx, x in enumerate(EXPORT_DATA.get("nodes")):
            for y_idx, y in enumerate(x.get("children")):
                if y == []:
                    EXPORT_DATA["nodes"][x_idx]["children"].pop(y_idx)

        data_json = EXPORT_DATA

        set_redis_data(job_id, "data_json", data_json)

        print("PROCESSING DONE:")
        result = {"job_id": job_id, "messages": log_messages, "status_code": 200}
        publish("start_process_response", "to_pipeline", result)

    except Exception as error:
        print(traceback.format_exc())
        result = {
            "job_id": job_id,
            "messages": log_messages,
            "error": str(error),
            "traceback": str(traceback.format_exc()),
            "status_code": 400,
        }
        publish("start_process_response", "to_pipeline", result)


@app.route("/validation_process", methods=["POST"])
def validation_process():
    """
    This function handle the validation process for table models by processing the input JSON.

    Args:
        Data is received via POST request in JSON format.

    Returns:
        JSON Response: Exported data from the table_model_validation process.

    Process Details:
        - Generate a random ID to uniquely identify the validation log.
        - Call the 'table_model_validation' function to process the input JSON.
        - Retrieve log messages using 'get_process_logs'.
        - Handle errors, provide error messages and tracebacks in the response.

    Notes:
        - Logs are stored in the 'temp' directory with the unique ID.
        - Validates the presence of processed data and logs.
    """
    try:
        # Set a random ID
        _id = str(random.randint(0, 50000))

        # Model Validation Log File Name
        LOG_FILENAME = os.path.join("temp", "model_validation_log_" + _id + ".json")

        content = request.json

        try:
            EXPORT_DATA = table_model_validation(str(_id), content)

            try:
                log_messages = get_process_logs(LOG_FILENAME)
            except:
                log_messages = "No log produced."

            print(log_messages)

            if EXPORT_DATA is None:
                print("Model Validation data json wasn't producted")

                response = {
                    "messages": log_messages,
                    "traceback": str(traceback.format_exc()),
                }
                return jsonify(response), 400

            else:
                return EXPORT_DATA

        except:
            print("Model Validation data json wasn't producted")

            response = {
                "messages": log_messages,
                "traceback": str(traceback.format_exc()),
            }
            return jsonify(response), 400

    except Exception as error:
        print(traceback.format_exc())
        response = {"error": str(error), "traceback": str(traceback.format_exc())}
        return jsonify(response), 400


@app.route("/get_text_by_pos", methods=["POST"])
def get_text_by_pos():
    """
    Extract text from the specific position within a document structure.

    Args:
        Data is received via POST request in JSON format. 
        Query parameter:
            - document_index (int): Index of the document in the JSON structure.
            - page_index (int): Index of the page within the document.
            - positions (str): Comma-separated boundary positions - Left, Top, Right, Bottom.

    Returns:
        JSON Response: Extracted text from the specified positions.

    Process Details:
        - Retrieve the document and page based on indices from the JSON structure.
        - Identify all word nodes ('W_nodes') within the specified page's children.
        - Filter word nodes within the provided boundary positions using 'check_in_boundary'.
        - Sort the words based on their top-left positions (left and top).
        - Concatenate the filtered word values into a single string for response.

    Notes:
        - Nested helper function 'find_all_words' to traverse the hierarchical JSON structure.
    """
    content = request.json

    # Serializing json
    FULL_JSON_DATA = content

    document_id = int(request.args["document_index"])
    page_id = int(request.args["page_index"])
    positions = request.args["positions"]

    # RA JSON DATA
    RA_JSON = FULL_JSON_DATA["ra_json"]

    document_index = document_id
    DOCUMENT = RA_JSON["nodes"][document_index]

    PAGE_ID = page_id
    PAGE = DOCUMENT["children"][page_id]

    # Extract all the W_nodes
    W_nodes = []

    def find_all_words(data):
        """collect all nodes of type word"""
        if isinstance(data, list):
            for elem1 in data:
                find_all_words(elem1)
        elif isinstance(data, dict):
            for k, v in data.items():
                if (k == "type") and (v == "word"):
                    W_nodes.append(data)
                elif isinstance(v, list):
                    find_all_words(v)

    # Find All Word elements and put it into W_nodes
    find_all_words(PAGE["children"])

    found_w_nodes = []

    for W_node in W_nodes:
        check = check_in_boundary(positions, W_node["pos"])
        if check:
            found_w_nodes.append(
                [
                    W_node["v"],
                    int(W_node["pos"].split(",")[0]),
                    int(W_node["pos"].split(",")[1]),
                ]
            )

    found_w_nodes = sorted(found_w_nodes, key=lambda left: left[1])
    found_w_nodes = sorted(found_w_nodes, key=lambda top: top[2])

    text_data = " ".join([i[0] for i in found_w_nodes])

    response_json = {"text": text_data}

    return response_json, 200


@app.route("/single_col_extractor", methods=["POST"])
def single_col_extractor():
    """
    This function handle the extraction of single-column data from the provided JSON input.

    Args:
        Data is received via POST request in JSON format.

    Returns:
        JSON Response: Extracted single-column data and log messages.

    Process Details:
        - Generate a unique random ID for file naming.
        - Create temporary files for the request JSON and key definitions.
        - Read the processed output and logs from temporary files.
        - Clean up temporary files after processing.

    Notes:
        - Logs are stored and retrieved from the 'temp' directory with unique IDs.
        - The external system configured in 'SINGLE_COLUMN_EXTRACTOR_FILE_NAME'.
    """
    try:
        # Set a random ID
        _id = str(random.randint(0, 50000))

        # Model Validation Log File Name
        LOG_FILENAME = os.path.join(
            "temp", "single_column_extractor_log_" + _id + ".json"
        )

        # Remove Temp Files
        TEMP_REQ_FILENAME = os.path.join(
            "temp", "temp_request_single_col_" + _id + ".json"
        )

        TEMP_KEY_DEF_FILENAME = os.path.join(
            "temp", "temp_key_def_single_col_" + _id + ".json"
        )

        TEMP_EXPORT_FILENAME = os.path.join(
            "temp", "single_col_processed_" + _id + ".json"
        )
        try:
            if (
                os.path.exists(TEMP_REQ_FILENAME)
                or os.path.exists(TEMP_EXPORT_FILENAME)
                or os.path.exists(TEMP_KEY_DEF_FILENAME)
            ):
                os.remove(TEMP_REQ_FILENAME)
                os.remove(TEMP_EXPORT_FILENAME)
                os.remove(TEMP_KEY_DEF_FILENAME)
                print("Removed Temporary Files")
            else:
                pass
        except:
            pass

        try:
            if os.path.exists(LOG_FILENAME):
                os.remove(LOG_FILENAME)
        except:
            pass

        request_data = request.get_json()

        input_data = request_data["input_data"].get("singleColumnExtractor")
        input_data["keyLabel"] = request_data["input_data"]["keyLabel"]
        input_data["qualifierValue"] = request_data["input_data"]["qualifierValue"]
        if input_data.get("shape") == None:
            input_data["shape"] = ""

        input_json = request_data["input_ra_json"]

        # Writing RA JSON
        with open(TEMP_REQ_FILENAME, "w") as outfile:
            json.dump(input_json, outfile)

        # Writing Key Def
        with open(TEMP_KEY_DEF_FILENAME, "w") as outfile:
            json.dump(input_data, outfile)

        os.system(SINGLE_COLUMN_EXTRACTOR_FILE_NAME + (" " + _id))

        try:
            f = open(TEMP_EXPORT_FILENAME, "r")
            # Reading from file
            EXPORT_DATA = json.loads(f.read())
            f.close()

            log_message = get_process_logs(LOG_FILENAME)

            print(log_message)

            # Lastly Remove the files after process
            try:
                if (
                    os.path.exists(TEMP_REQ_FILENAME)
                    or os.path.exists(TEMP_EXPORT_FILENAME)
                    or os.path.exists(TEMP_KEY_DEF_FILENAME)
                ):
                    os.remove(TEMP_REQ_FILENAME)
                    os.remove(TEMP_EXPORT_FILENAME)
                    os.remove(TEMP_KEY_DEF_FILENAME)
                    print("Removed Temporary Files")
                else:
                    pass
            except:
                print(traceback.print_exc())
                pass

            try:
                if os.path.exists(LOG_FILENAME):
                    os.remove(LOG_FILENAME)
            except:
                pass

            return jsonify({"data": EXPORT_DATA, "messages": log_message})

        except:
            print("Single Column Extraction data json wasn't producted")
            print(traceback.print_exc())
            return {}, 400

    except:
        print(traceback.print_exc())
        return []


@app.route("/get_chunk_data", methods=["POST"])
def get_chunk_data():
    """
    Processe a JSON input to create chunk data in a structured format.

    Args:
        Data is received via POST request in JSON format.

    Returns:
        JSON Response: Processed Chunk data in dictionary format.

    Process Details:
        - Accept JSON input from the request.
        - Processe the data into chunks using 'chunk_process'.
        - Return the processed chunks in a JSON response.

    Notes:
        - The 'chunk_process' function handle the core logic for splitting the data into chunks.
    """
    try:
        # Get FULL DATA JSON
        request_data = request.get_json()

        # Process to get JSON format batck
        data = chunk_process(request_data, return_type="dict")

        return jsonify({"data": data}), 200
    except:
        print("Chunking process have issues")
        print(traceback.print_exc())
        return {"Chunking process have issues"}, 400


@app.route("/get_position_shift_data", methods=["POST"])
def get_position_shift_data():
    """
    This function calculates position shifts for elements on a page based on provided definitions and RA JSON data.

    Args:
        Data is received via POST request in JSON format.

    Returns:
        JSON Response: Processed position shift data in JSON format.

    Process Details:
        - Accept RA JSON and definitions from the request.
        - Compute position shifts using 'position_calculation_per_page'.
        - Return the calculated data as JSON.

    Notes:
        - Position shifts are calculated per page based on definitions.
    """
    try:
        request_data = request.get_json()

        ra_json = request_data["ra_json"]
        definitions = request_data["definitions"]

        data = position_calculation_per_page(ra_json, definitions)

        return jsonify({"data": data}), 200
    except Exception as error:
        print("Position shift calculation have issues")
        print(traceback.print_exc())
        return {"error": str(error)}, 400


def atm_process(request_data):
    """
    This function process ATM (Automated Table Model) pipeline using the provided request data.

    Args:
        request_data (dict): JSON object contain the job details and input parameters for the ATM process.

    Returns:
        Result is handled via Redis and Rabbitmq.

    Process Details:
        - Retrieve job-specific data from Redis using 'get_redis_data'.
        - Construct a full JSON structure ('FULL_JSON_DATA') containing batches and definitions.
        - Execute the 'atm' function with thresholds, patterns, and other parameters to generate the ATM data.
        - Store the resulting ATM data back in Redis using 'set_redis_data'.
        - Publish a success response with the 'job_id', status, and message to_pipeline channel.

    Notes:
        - Redis is used to store and retrieve intermediate job data.
        - The 'atm' function contain the core logic for automated table model.
    """
    try:
        job_id = request_data["job_id"]

        request_data = get_redis_data(job_id)

        record_line = request_data["record_line"]
        digit_threshold = request_data["digit_threshold"]
        text_threshold = request_data["text_threshold"]
        user_selected_patterns = request_data["user_selected_patterns"]
        extended_user_selected_patterns = request_data[
            "extended_user_selected_patterns"
        ]
        multiple_line_record = request_data["multiple_line_record"]
        user_selected_ob = request_data["user_selected_ob"]

        content = {
            "batches": request_data["batches"],
            "definitions": request_data["definitions"],
        }

        # Serializing json
        FULL_JSON_DATA = content

        # Run AutoPatternFinder process
        EXPORT_DATA = atm(
            int(text_threshold),
            int(digit_threshold),
            FULL_JSON_DATA,
            user_selected_patterns,
            user_selected_ob,
            extended_user_selected_patterns,
            multiple_line_record,
        )

        atm_data = EXPORT_DATA

        set_redis_data(job_id, "atm_data", atm_data)

        result = {"job_id": job_id, "messages": "Success", "status_code": 200}

        publish("atm_process_response", "to_pipeline", result)

    except Exception as error:
        print(traceback.format_exc())

        result = {
            "job_id": job_id,
            "messages": "Failed in Automated Table Model",
            "error": str(error),
            "traceback": str(traceback.format_exc()),
            "status_code": 400,
        }

        publish("atm_process_response", "to_pipeline", result)
