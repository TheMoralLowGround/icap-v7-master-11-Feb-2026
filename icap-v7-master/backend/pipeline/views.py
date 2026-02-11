"""
Organization: AIDocBuilder Inc.
File: dashboard/views.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature updates
    - Sunny - Feature updates


Last Updated By: Nayem
Last Updated At: 2024-11-30

Description:
    This file contain functions that handle the different necessary features and functionalities
    of the application, processing requests and responses

Dependencies:
    - PyPDF2, redis, fitz, zipfile
    - xml.etree.ElementTree as ET
    - pandas as pd
    - * from typing
    - deepcopy from copy
    - datetime from datetime
    - async_to_sync from asgiref.sync
    - get_channel_layer from channels.layers
    - settings from django.conf
    - InMemoryUploadedFile from django.core.files.uploadedfile
    - Paginator from django.core.paginator
    - cache from django.core.cache
    - IntegrityError, connection from django.db
    - Q from django.db.models
    - post_save from django.db.models.signals
    - receiver from django.dispatch
    - HttpResponse from django.http
    - timezone from django.utils
    - status from rest_framework
    - api_view, permission_classes from rest_framework.decorators
    - AllowAny from rest_framework.permissions
    - Response from rest_framework.response
    - remove_null_characters, save_analyzer_log_time, batch_awaiting_datacap from utils.utils

    - Batch, BatchStatus, DefinedKey, Definition, ApplicationSettings, EmailBatch,
      EmailParsedDocument, EmailToBatchLink, MasterDictionary, TranslationCode, OutputJson,
      TrainBatch, TrainParsedDocument, TrainToBatchLink, TransactionLog from core.models

    - BatchStatusSerializer, BatchSerializer, DefinitionSerializer, MasterDictionarySerializer,
      EmailBatchSerializer, TrainBatchSerializerAll, TrainBatchSerializer from core.serializers

    - Profile, Project, ProfileDocument, Template from dashboard.models
    - ProjectSerializer from dashboard.serializers
    - Template from dashboard.models
    - write_timeline_log from utils.utils

    - get_instance_classes, convert_doc_instance_to_dict, load_doc_instance_from_dict,
      organize_docs_inside_copy_batches_xml, get_info_from_copy_batches_xml, join_with_escaped_commas,
      document_matching_p1, get_profile_doc_info, get_master_dictionaries_for_classifier, match_attachment,
      update_matched_docs, get_pages_by_doc_type, create_batch_folder, rewrite_copy_batches_xml,
      update_copy_batches_xml, save_manual_classification_data from utils.classification_utils

    - DataCap from pipeline.scripts.DataCap
    - DataJson from pipeline.scripts.DataJson
    - DJsonToExcel from pipeline.scripts.DJsonToExcel
    - parse_email, parse_email_metadata, detect_garbled_text from pipeline.scripts.EmailParser
    - OrganizeFiles from pipeline.scripts.OrganizeFiles
    - RAJson from pipeline.scripts.RAJson

    - send_failure_notification, send_success_notification from pipeline.email_utils
    - publish from rabbitmq_producer import
    - schedule_delayed_publish_to_rabbitmq from core.tasks

Main Features:
    - Batch Processing and Re-Processing
    - Profile matching from email parsing
    - Document classification
    - Manage manual classification data
    - Timeline status and logging
    - Handles API calls
    - Verification and validation processes
    - Retrieve RA json data
    - Retrieve chunk data
    - Retrieve ATM chunk data
    - Recreate datacap batch
    - Split batches
    - Download transaction data
    - Download and upload zip files from Batches (storage)
    - Download and upload transaction batch
    - Download and upload training batch
    - Handle batch path content
    - Remove unused batches
"""

import io
import sys
import json
import uuid
import os
import fitz
import glob
import re
import base64
import random
import shutil
import string
import time
import traceback
import logging
import xml.etree.ElementTree as ET
import zipfile
from copy import deepcopy
from datetime import datetime
from asgiref.sync import async_to_sync
from operator import itemgetter

import requests
import PyPDF2
from channels.layers import get_channel_layer
from django.conf import settings
from pathlib import Path
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q, Case, When, Value, IntegerField
from django.db.models.functions import Length
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions import IsAdminUser

import redis
from utils.create_default_definitions import DefaultDefinitions
from core.models import (
    Batch,
    BatchStatus,
    DefinedKey,
    Definition,
    ApplicationSettings,
    EmailBatch,
    EmailParsedDocument,
    EmailToBatchLink,
    MasterDictionary,
    TranslationCode,
    OutputJson,
    TrainBatch,
    TrainParsedDocument,
    TrainToBatchLink,
    ShipmentRecord,
    AiAgentConversation,
)
from core.serializers import (
    BatchStatusSerializer,
    BatchSerializer,
    DefinitionSerializer,
    MasterDictionarySerializer,
    EmailBatchSerializer,
    TrainBatchSerializerAll,
    EmailParsedDocumentSerializer,
    TrainParsedDocumentSerializer,
    AiAgentConversationSerializer,
)
from dashboard.models import Profile, Project, ProfileDocument, Template, OutputChannel

from pipeline.utils.process_batch_utils import (
    gerenate_job_id_for_batch,
    get_new_email_batch_id,
    write_batch_log,
    write_parent_batch_log,
    write_failed_log,
    send_to_group,
    prepare_parent_batch_path,
    get_extraction_payload,
    trigger_manual_extraction,
    merge_data_json,
    update_ra_json_from_auto_extraction,
    fix_id_auto_extraction,
    fix_string_format,
    normalize_merged_data,
    get_new_batch_id,
    get_exception_data,
    get_classifier_settings,
)

from pipeline.utils.excel_utils import convert_xls_to_xlsx, validate_xls_file

from pipeline.worker_tasks import (
    process_pdfs_and_docs_p1,
    process_files_for_ocr,
    convert_excel_files_to_pdf,
)
from pipeline.utils.convert_excel_or_doc_to_pdf import EXCEL_FORMATS

from utils.utils import (
    remove_null_characters,
    save_analyzer_log_time,
    batch_awaiting_datacap,
    write_timeline_log,
    get_merged_definition_settings,
    get_other_settings,
    create_additional_doc,
    get_developer_settings,
    to_camel_case,
    convert_to_title,
    load_json_file,
    restructure_ra_json,
    restructure_data_json,
    get_selected_dataset_batches_info,
    is_dense_page_check_enabled,
    get_active_agents_by_project,
)
from utils.classification_utils import (
    is_excel_read_only,
    add_file_path_to_ra_json,
    get_instance_classes,
    update_ra_json_doc_order,
    convert_doc_instance_to_dict,
    load_doc_instance_from_dict,
    organize_docs_inside_copy_batches_xml,
    get_info_from_copy_batches_xml,
    document_matching_p1,
    get_profile_doc_info,
    get_master_dictionaries_for_classifier,
    match_attachment,
    handle_multiple_matching_doc_types,
    handle_single_matching_doc_type,
    create_supporting_batch,
    save_manual_classification_data,
    post_classification_process,
    get_merged_batch,
    generate_ra_json_file_path,
    handle_ocr_mismatch,
    get_doc_info,
    publish_to_classifier,
)
from utils.email_utils import (
    send_failure_notification,
    send_success_notification,
)
from utils.assembly_utils import (
    handle_api_call,
    handle_doc_upload,
    prepare_email_context,
    duplicate_shipment_id_checker,
)
from pipeline.scripts.DataCap import DataCap
from pipeline.scripts.DataJson import DataJson
from pipeline.scripts.DeFlattener import central_output_handler
from pipeline.scripts.DJsonToExcel import DJsonToExcel
from pipeline.scripts.EmailParser import (
    parse_email,
    parse_email_metadata,
    detect_garbled_text,
)
from pipeline.scripts.OutputChannels import OutputChannels
from pipeline.scripts.OrganizeFiles import OrganizeFiles
from pipeline.scripts.RAJson import RAJson

from rabbitmq_producer import publish
from dashboard.views import get_profiles_data_by_ids
from core.tasks import schedule_delayed_publish_to_rabbitmq

from pipeline.ra_json_or_xml_to_text import get_ra_json_to_txt

# from pipeline.utils.detect_pdf import is_electronic_pdf
# from pipeline.utils.electronic_pdf import extract_ra_json_from_pdf
from pipeline.utils.ddh_search_utils import get_ddh_token
from pipeline.utils.annotation_utils import get_annotation_token
from pipeline.utils.generate_layout_id_utils import get_layout_id
from pipeline.utils.input_channel_utils import get_input_channel_token
from pipeline.utils.output_channel_utils import (
    process_output_channel,
    handle_output_doc_upload,
)

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
DATASET_BATCH_INPUT_PATH = settings.DATASET_BATCH_INPUT_PATH
INPUT_FILES_PATH = settings.INPUT_FILES_PATH
DOCBUILDER_API_URL = settings.DOCBUILDER_API_URL
UTILITY_API_URL = settings.UTILITY_API_URL
ICAP_API_URL = settings.ICAP_API_URL
CLASSIFIER_API_URL = settings.CLASSIFIER_API_URL
MAX_RETRY = int(os.getenv("MAX_RETRY", 0))
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 0))
DDH_BASE_URL = os.getenv("DDH_BASE_URL")
ANNOTATION_BASE_URL = os.getenv("ANNOTATION_BASE_URL")
INPUT_CHANNEL_BASE_URL = os.getenv("INPUT_CHANNEL_BASE_URL")
SELECTED_DATASET_LIST_FILE = os.getenv("SELECTED_DATASET_LIST_FILE")
QDRANT_VECTOR_DB_BASE_URL = os.getenv("QDRANT_VECTOR_DB_BASE_URL")


def _safe_join(base_path, *paths):
    base_path = os.path.realpath(os.path.abspath(os.path.normpath(base_path)))
    final_path = os.path.realpath(
        os.path.abspath(
            os.path.normpath(os.path.join(base_path, *[p or "" for p in paths]))
        )
    )
    if os.path.commonpath([base_path, final_path]) != base_path:
        raise ValueError("Invalid sub_path")
    return final_path


_session = requests.Session()
channel_layer = get_channel_layer()


BATCH_UPLOAD_MODES = ["processing", "training"]

# Required to load robot modules from external scripts folder
sys.path.append("/scripts")

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)

PROJECT_TO_BATCH_TYPE = {
    "customsdeclaration(b)": "booking",
    "dgfcw1customsdeclaration(b)": "booking",
    "vv_customs_project_b_job": "booking",
    "extractinvoice (civ)": "commercial-invoice",
    "usacustoms": "usacustoms",
    "customsdeclaration(b+civ)": [
        "commercial-invoice",
        "booking",
    ],  # Mixed: depends on batch type
    "customsentryupdate": "customs-entry",
    "shipmentcreate": "shipment-create",
    "dgfcw1shipmentcreate": "shipment-create",
    "shipmentupdate": "shipment-update",
    "dgfcw1shipmentupdate": "shipment-update",
    "dsc_wms": "dsc-wms",
    "military_flag": "Military_Flag",
    "inspection reports": "shipment-update",
    "freight": "freight",
}


def get_hardcoded_project_type(project):
    """
    This is a legacy strategy that Almas implemented in 2022, where we didn't have lots of projects or any concept of projects.
    Since, API calls were different based on the project being processed, the hard-coding was implemented for ease of use.
    I decided to keep it here, as there are many dependency on this hard code mapping in various places in the codebase.

    Docstring for get_hardcoded_project_type

    :param project: Description
    """
    batch_type = project
    try:
        batch_type = PROJECT_TO_BATCH_TYPE.get(project.lower(), project)
        if "customsdeclaration" in project.lower():
            batch_type = "booking"
        elif "shipmentcreate" in project.lower():
            batch_type = "shipment-create"
        elif "shipmentupdate" in project.lower():
            batch_type = "shipment-update"
        elif "freight" in project.lower():
            batch_type = "freight"
        elif "usacustoms" in project.lower():
            batch_type = "usacustoms"
        elif "hg_bol" in project.lower():
            batch_type = "hillebrand-gori"
    except:
        pass

    return batch_type


def strip_extra_spaces(text):
    """
    Replace two or more spaces with a single space
    """
    return re.sub(r"\s{2,}", " ", text)


"""
Listen to Batch Status model changes and send websocket notifications
"""


@receiver(post_save, sender=BatchStatus, dispatch_uid="send_batch_status_update")
def send_batch_status_update(sender, instance, **kwargs):
    data = dict(BatchStatusSerializer(instance).data)
    send_to_group(f"batch_status_{data['batch_id']}", "batch_status", data)


def reduce_ra_json_for_document(ra_json, document_id):
    """
    Remove childerns for not required documents
    """
    ra_json = deepcopy(ra_json)
    for doc in ra_json["nodes"]:
        if doc["id"] != document_id:
            doc["children"] = []

    return ra_json


def reduce_definitions_for_table(definitions, table_unique_id):
    """Remove not required tables from definitions."""
    definitions = deepcopy(definitions)
    for definition in definitions:
        definition_table = []
        for table in definition["table"]:
            if table["table_unique_id"] == table_unique_id:
                definition_table.append(table)

        definition["table"] = definition_table

    return definitions


def reduce_final_definitions_for_docbuilder(definitions, batch_type):
    """Update type of definitions"""

    definitions = deepcopy(definitions)
    for definition in definitions:
        try:
            if batch_type:
                definition["type"] = batch_type
            definition["table"] = [
                i
                for i in definition["table"]
                if i.get("table_definition_data", {})
                .get("models", {})
                .get("type", None)
                != "auto"
            ]
        except:
            pass
    return definitions


def get_response_messages(response_json):
    """Helper function to process response messages"""
    messages = response_json["messages"]
    status = "inprogress"

    # Find messages status
    # if any message has 400 code, status will be warning
    for message in messages:
        code = message["code"]
        if code == 400:
            status = "warning"
            break

    messages = json.dumps(messages)

    return status, messages


def job_id_cleanup(job_id):
    """
    Perform cleanup of Redis data for a given job_id.
    Handles all edge cases: connection errors, missing keys, and verification.
    """
    logger = logging.getLogger(__name__)

    if not job_id:
        logger.warning("job_id_cleanup called with empty job_id")
        return False

    try:
        # Check if key exists before attempting deletion
        exists = redis_instance.exists(job_id)

        if exists:
            # Attempt to delete the key
            deleted_count = redis_instance.delete(job_id)

            if deleted_count > 0:
                logger.info(f"Successfully cleaned up Redis data for job_id: {job_id}")
                return True
            else:
                logger.warning(
                    f"Failed to delete Redis key for job_id: {job_id} (delete returned 0)"
                )
                return False
        else:
            # Key doesn't exist - this is fine, cleanup already done or never created
            logger.debug(
                f"Redis key does not exist for job_id: {job_id} (already cleaned or never created)"
            )
            return True

    except redis.ConnectionError as e:
        logger.error(
            f"Redis connection error during cleanup for job_id {job_id}: {str(e)}"
        )
        return False
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout during cleanup for job_id {job_id}: {str(e)}")
        return False
    except redis.RedisError as e:
        logger.error(f"Redis error during cleanup for job_id {job_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during cleanup for job_id {job_id}: {str(e)}",
            exc_info=True,
        )
        return False


def test_batch_cleanup(job_id):
    """
    Perform cleanup of Redis data for a given job_id.
    Handles all edge cases: connection errors, missing keys, and verification.
    """
    logger = logging.getLogger(__name__)

    if not job_id:
        logger.warning("test_batch_cleanup called with empty job_id")
        return False

    try:
        # Check if key exists before attempting deletion
        exists = redis_instance.exists(job_id)

        if exists:
            # Attempt to delete the key
            deleted_count = redis_instance.delete(job_id)

            if deleted_count > 0:
                logger.info(f"Successfully cleaned up Redis data for job_id: {job_id}")
                return True
            else:
                logger.warning(
                    f"Failed to delete Redis key for job_id: {job_id} (delete returned 0)"
                )
                return False
        else:
            # Key doesn't exist - this is fine, cleanup already done or never created
            logger.debug(
                f"Redis key does not exist for job_id: {job_id} (already cleaned or never created)"
            )
            return True

    except redis.ConnectionError as e:
        logger.error(
            f"Redis connection error during cleanup for job_id {job_id}: {str(e)}"
        )
        return False
    except redis.TimeoutError as e:
        logger.error(f"Redis timeout during cleanup for job_id {job_id}: {str(e)}")
        return False
    except redis.RedisError as e:
        logger.error(f"Redis error during cleanup for job_id {job_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during cleanup for job_id {job_id}: {str(e)}",
            exc_info=True,
        )
        return False


def get_batch_id_from_job_id(job_id):
    batch_id = job_id[15:]
    return batch_id


def handle_service_failure(job_id):
    """Handle service failure"""
    print(traceback.print_exc())
    batch_id = get_batch_id_from_job_id(job_id)
    error = str(traceback.format_exc())
    write_failed_log(
        batch_id=batch_id,
        status="failed",
        message="Error occured during batch processing",
        remarks=error,
    )
    test_batch_cleanup(job_id)


def convert_profile_keys_to_camel_case(profile_keys):
    for key in profile_keys:
        try:
            key["label"] = to_camel_case(key["label"])
        except:
            pass
    return profile_keys


def test_batch_p1(request_data):
    """
    batch_id: ID of batch to be processed.
    document_id: if document_id is provided, system will only process provided document otherwise process all docs inside batch.
    skip_post_processor: Flag for skipping post processing.
    skip_table_processing: Flag for skipping table processing.
    skip_key_processing: Flag for skipping key processing.
    definition_version : which version of definition to be used for processing docs
    new_upload: Flag to identify if batch is newly uploaded or user is testing existing batch.
    """

    batch_id = request_data["batch_id"]
    document_id = request_data.get("document_id", None)
    template = request_data.get("template", None)
    table_unique_id = request_data.get("table_unique_id", None)
    skip_post_processor = request_data.get("skip_post_processor", False)
    skip_table_processing = request_data.get("skip_table_processing", False)
    skip_key_processing = request_data.get("skip_key_processing", False)
    definition_version = request_data.get(
        "definition_version", settings.DEFAULT_DEFINITION_VERSION
    )
    new_upload = request_data.get("new_upload", False)
    _, __, parent_batch, *tail = get_instance_classes(batch_id)

    if parent_batch:
        AiAgentConversation.objects.filter(transaction_id=parent_batch.id).delete()

    if document_id:
        document_id = fix_string_format(document_id)

    job_id = gerenate_job_id_for_batch(batch_id)
    print(f"Processing batch {batch_id}")
    print(f"{job_id=}")

    job_details = {
        "template": template,
        "table_unique_id": table_unique_id,
        "skip_post_processor": skip_post_processor,
        "skip_post_processor": skip_post_processor,
        "skip_table_processing": skip_table_processing,
        "skip_key_processing": skip_key_processing,
        "definition_version": definition_version,
        "new_upload": new_upload,
        "batch_id": batch_id,
        "document_id": document_id,
    }
    redis_instance.set(job_id, json.dumps(job_details))

    write_batch_log(
        batch_id=batch_id,
        status="inprogress",
        message=f"Batch Processing Started. Definition Version: {definition_version}",
    )

    try:
        ###
        # Reset data json
        ###

        write_batch_log(
            batch_id=batch_id, status="inprogress", message="Clearning Data Json"
        )

        batch_instance = Batch.objects.get(id=batch_id)
        profile_name = batch_instance.definition_id
        original_data_json = batch_instance.data_json

        try:
            # Send profile_keys to use in utility
            matched_profile = Profile.objects.get(name=batch_instance.definition_id)
            profile_keys = convert_profile_keys_to_camel_case(matched_profile.keys)
            profile_customers = matched_profile.customers.all().values(
                "id",
                "name",
                "account_number",
                "address_line1",
                "address_line2",
                "address_id",
                "org_name",
                "short_code",
                "city",
                "country_code",
                "postal_code",
                "phone",
            )
            dictionaries = matched_profile.dictionaries
            job_details = {
                **job_details,
                "profile_keys": profile_keys,
                "profile_customers": list(profile_customers),
                "dictionaries": dictionaries,
            }
            redis_instance.set(job_id, json.dumps(job_details))
        except:
            print("Error sending profile_keys", traceback.print_exc())
            pass
        ra_json = batch_instance.ra_json
        if document_id:
            ra_json = reduce_ra_json_for_document(ra_json, document_id)

        ###
        # Generating layout_id
        ###
        if not batch_instance.layout_ids:
            documents = ra_json.get("nodes", [])

            if documents:
                layout_ids = []
                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Generating Layout ID",
                )

                for document in documents:
                    layout_id = get_layout_id(batch_instance, document)
                    document["layout_id"] = layout_id
                    layout_ids.append(
                        {"document_id": document["id"], "layout_id": layout_id}
                    )

                batch_instance.layout_ids = layout_ids
                batch_instance.ra_json = ra_json
                batch_instance.save()

                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Layout ID Generation completed",
                    action="display_json",
                    remarks=json.dumps(layout_ids),
                )

        # Generate the initial data_json
        data_json = DataJson(ra_json).process()

        # add dafination version at root level
        data_json["definition_version"] = definition_version

        batch_instance.data_json = data_json
        batch_instance.save()

        batch_type = ra_json.get("batch_type", ".pdf")

        master_dictionaries_qs = MasterDictionary.objects.all()
        master_dictionaries = MasterDictionarySerializer(
            master_dictionaries_qs, many=True
        ).data

        master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}

        if batch_type == ".xlsx":
            ###
            # ExcelTable Process no auto extraction needed
            ###

            ###
            # Fetch Definitions
            ###
            sub_path = batch_instance.sub_path
            batch_path = os.path.join(BATCH_INPUT_PATH, sub_path)

            if batch_instance.is_dataset_batch and ".U" not in batch_id:
                batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path)

            batch_mode = batch_instance.mode
            project = batch_instance.project
            definitions = get_definitions_for_batch(
                batch_instance,
                definition_version=definition_version,
                template=template,
            )

            if table_unique_id:
                definitions = reduce_definitions_for_table(definitions, table_unique_id)
            definition_ids = []
            if not template:
                definition_ids = [i["id"] for i in definitions]

            translation_codes = get_translation_codes_for_definitions(definition_ids)

            definition_settings = get_merged_definition_settings(project)

            defined_keys = list(
                DefinedKey.objects.all().values_list("label", flat=True)
            )

            job_details = {
                **job_details,
                "ra_json": ra_json,
                "definitions": definitions,
                "defined_keys_data": defined_keys,
                "master_dictionaries": master_dictionaries,
                "data_json": batch_instance.data_json,
                "definition_settings": definition_settings,
                "translation_codes": translation_codes,
                "batch_path": batch_path,
                "batch_mode": batch_mode,
                "batch_type": batch_type,
                "project": project,
            }
            redis_instance.set(job_id, json.dumps(job_details))
            request_body = {
                "job_id": job_id,
            }
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Initiating ExcelTable process",
            )

            publish("excel_table_process", "to_utility", request_body)
            return
        # Only call auto extraction for .pdf or .docx file
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiating Auto Extraction process",
        )

        keys, mappedKeys = get_extraction_payload(batch_instance)

        sub_path = batch_instance.sub_path
        batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, batch_id)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path, batch_id)

        filenames = [
            os.path.join(batch_path, i)
            for i in os.listdir(batch_path)
            if i.lower().endswith(".tif")
        ]

        tif_files = []

        for fpath in filenames:
            with open(fpath, "rb") as f:
                encoded_content = base64.b64encode(f.read()).decode("utf-8")
                tif_files.append(
                    {"filename": os.path.basename(fpath), "content": encoded_content}
                )

        exception_data = get_exception_data(batch_instance, document_id)
        address_parser_example = master_dictionaries.get(
            "address_parser_example", {}
        ).get("data", {})

        # Store original_data_json in Redis job_details before sending to extraction service
        if document_id:
            job_details["original_data_json"] = original_data_json or {}
            redis_instance.set(job_id, json.dumps(job_details))

            # Remove documents with empty children arrays
            if ra_json and "nodes" in ra_json:
                ra_json["nodes"] = [
                    doc
                    for doc in ra_json["nodes"]
                    if isinstance(doc.get("children"), list)
                    and len(doc.get("children", [])) > 0
                ]

        payload = {
            "batch_id": batch_instance.id,
            "ra_json": ra_json,
            "keys": keys,
            "mappedKeys": mappedKeys,
            "exception_data": exception_data,
            "job_id": job_id,
            "app_version_name": "v7-clone",
            "tif_files": tif_files,
            "address_parser_example": address_parser_example,
            "profile_name": profile_name,
            "process_uid": str(matched_profile.process_uid),
        }

        # Send extraction request via RabbitMQ
        print("Send request to extraction rabbitmq")
        publish("extraction", "to_extraction", payload)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p2_extraction_response(response_json):
    batch_id = response_json["batch_id"]
    try:
        job_id = response_json.get("job_id")

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="Auto Extraction process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            if job_id:
                test_batch_cleanup(job_id)
            return

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Auto Extraction process completed",
            action="display_json",
            remarks=json.dumps(response_json),
        )

        job_id = response_json["job_id"]
        job_info = json.loads(redis_instance.get(job_id))
        definition_version = job_info.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )
        batch = Batch.objects.get(id=batch_id)
        data_json = fix_id_auto_extraction(response_json.pop("data_json", {}))
        data_json["definition_version"] = definition_version
        ra_json = update_ra_json_from_auto_extraction(data_json, batch.ra_json)
        # Update RA JSON
        batch.ra_json = ra_json
        batch.vendor = data_json.get("Vendor", None)
        batch.raw_data_json = response_json.get("raw_data_json", {})
        batch.save()
        # Check response status

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Normalized Auto Extraction response",
            action="display_json",
            remarks=json.dumps(data_json),
        )

        batch.refresh_from_db()
        request_data = {"job_id": job_id, "auto_extraction_data_json": data_json}
        publish("post_extraction_process", "to_pipeline", request_data)
    except:
        print(traceback.print_exc())
        error = str(traceback.format_exc())
        write_failed_log(
            batch_id=batch_id,
            status="failed",
            message="Error occured during batch processing",
            remarks=error,
        )
        try:
            test_batch_cleanup(job_id)
        except:
            pass


def start_label_mapping_process(request_data):
    try:
        batch_id = request_data["batch_id"]
        document_id = request_data["document_id"]
        template = request_data.get("template", None)
        table_unique_id = request_data.get("table_unique_id", None)
        skip_post_processor = request_data.get("skip_post_processor", False)
        skip_table_processing = request_data.get("skip_table_processing", False)
        skip_key_processing = request_data.get("skip_key_processing", False)
        definition_version = request_data.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiating Label Mapping process",
        )

        job_id = gerenate_job_id_for_batch(batch_id)
        print(f"Processing batch {batch_id}")
        print(f"{job_id=}")

        job_details = {
            "template": template,
            "table_unique_id": table_unique_id,
            "skip_post_processor": skip_post_processor,
            "skip_post_processor": skip_post_processor,
            "skip_table_processing": skip_table_processing,
            "skip_key_processing": skip_key_processing,
            "definition_version": definition_version,
            "batch_id": batch_id,
            "document_id": document_id,
        }
        redis_instance.set(job_id, json.dumps(job_details))

        batch_instance = Batch.objects.get(id=batch_id)

        keys, mappedKeys = get_extraction_payload(batch_instance)

        sub_path = batch_instance.sub_path
        batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, batch_id)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path, batch_id)

        filenames = [
            os.path.join(batch_path, i)
            for i in os.listdir(batch_path)
            if i.lower().endswith(".tif")
        ]

        tif_files = []

        for fpath in filenames:
            with open(fpath, "rb") as f:
                encoded_content = base64.b64encode(f.read()).decode("utf-8")
                tif_files.append(
                    {"filename": os.path.basename(fpath), "content": encoded_content}
                )

        exception_data = get_exception_data(batch_instance, document_id)

        master_dictionaries_qs = MasterDictionary.objects.all()
        master_dictionaries = MasterDictionarySerializer(
            master_dictionaries_qs, many=True
        ).data

        master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}
        address_parser_example = master_dictionaries.get(
            "address_parser_example", {}
        ).get("data", {})

        address_parser_example = master_dictionaries.get(
            "address_parser_example", {}
        ).get("data", {})
        payload = {
            "batch_id": batch_instance.id,
            "ra_json": batch_instance.ra_json,
            "keys": keys,
            "mappedKeys": mappedKeys,
            "exception_data": exception_data,
            "job_id": job_id,
            "app_version_name": "v7-clone",
            "tif_files": tif_files,
            "address_parser_example": address_parser_example,
            "raw_data_json": batch_instance.raw_data_json,
        }
        # Label mapping API Call
        print("Send request to label_mapping rabbitmq")
        publish("label_mapping", "label_mapping", payload)

    except Exception:
        print(traceback.print_exc())


def label_mapping_response(response_json):
    batch_id = response_json["batch_id"]
    try:
        job_id = response_json.get("job_id")
        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="Label Mapping process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            if job_id:
                test_batch_cleanup(job_id)
            return

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Label Mapping process completed",
            action="display_json",
            remarks=json.dumps(response_json),
        )

        job_id = response_json["job_id"]
        job_info = json.loads(redis_instance.get(job_id))
        definition_version = job_info.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )
        batch = Batch.objects.get(id=batch_id)
        data_json = fix_id_auto_extraction(response_json.pop("data_json", {}))
        data_json["definition_version"] = definition_version
        ra_json = update_ra_json_from_auto_extraction(data_json, batch.ra_json)
        # Update RA JSON
        batch.ra_json = ra_json
        batch.vendor = data_json.get("Vendor", None)
        batch.raw_data_json = response_json.get("raw_data_json", {})
        batch.save()
        # Check response status

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Normalized Label Mapping response",
            action="display_json",
            remarks=json.dumps(data_json),
        )

        batch.refresh_from_db()
        request_data = {"job_id": job_id, "auto_extraction_data_json": data_json}
        publish("post_extraction_process", "to_pipeline", request_data)
    except:
        print(traceback.print_exc())
        error = str(traceback.format_exc())
        write_failed_log(
            batch_id=batch_id,
            status="failed",
            message="Error occured during batch processing",
            remarks=error,
        )
        try:
            test_batch_cleanup(job_id)
        except:
            pass


def test_batch_p2_batch_type(response_json):
    try:
        job_id = response_json.get("job_id", None)
        auto_extraction_data_json = response_json.get("auto_extraction_data_json", None)
        job_info = json.loads(redis_instance.get(job_id))
        batch_id = job_info["batch_id"]
        template = job_info.get("template", None)
        table_unique_id = job_info.get("table_unique_id", None)
        skip_post_processor = job_info.get("skip_post_processor", False)
        skip_table_processing = job_info.get("skip_table_processing", False)
        skip_key_processing = job_info.get("skip_key_processing", False)
        definition_version = job_info.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )
        profile_keys = job_info.get("profile_keys", None)
        profile_customers = job_info.get("profile_customers", None)
        dictionaries = job_info.get("dictionaries", None)
        new_upload = job_info.get("new_upload", False)
        document_id = job_info.get("document_id", False)

        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        sub_path = batch_instance.sub_path
        batch_path = os.path.join(BATCH_INPUT_PATH, sub_path)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path)

        batch_mode = batch_instance.mode
        project = batch_instance.project
        if document_id:
            ra_json = reduce_ra_json_for_document(ra_json, document_id)
        new_data_json = DataJson(ra_json).process()

        ###
        # Fetch Definitions
        ###

        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        if table_unique_id:
            definitions = reduce_definitions_for_table(definitions, table_unique_id)
        if trigger_manual_extraction(definitions):
            definitions = reduce_final_definitions_for_docbuilder(
                definitions, batch_instance.type
            )
        definition_ids = []
        if not template:
            definition_ids = [i["id"] for i in definitions]

        translation_codes = get_translation_codes_for_definitions(definition_ids)

        definition_settings = get_merged_definition_settings(project)

        defined_keys = list(DefinedKey.objects.all().values_list("label", flat=True))

        master_dictionaries_qs = MasterDictionary.objects.all()
        master_dictionaries = MasterDictionarySerializer(
            master_dictionaries_qs, many=True
        ).data
        master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}
        batch_type = ra_json.get(
            "batch_type", ".pdf"
        )  # .pdf is fallback type for old batches
        # Save all info in global jobs
        # Preserve original_data_json from previous job_details if it exists
        existing_original_data_json = job_info.get("original_data_json", None)
        job_details = {
            "batch_id": batch_id,
            "document_id": document_id,
            "skip_post_processor": skip_post_processor,
            "skip_table_processing": skip_table_processing,
            "skip_key_processing": skip_key_processing,
            "definition_version": definition_version,
            "new_upload": new_upload,
            "ra_json": ra_json,
            "definitions": definitions,
            "defined_keys_data": defined_keys,
            "master_dictionaries": master_dictionaries,
            "data_json": new_data_json,
            "definition_settings": definition_settings,
            "translation_codes": translation_codes,
            "batch_path": batch_path,
            "batch_mode": batch_mode,
            "batch_type": batch_type,
            "project": project,
            "template": template,
            "auto_extraction_data_json": auto_extraction_data_json,
            "profile_keys": profile_keys,
            "profile_customers": profile_customers,
            "dictionaries": dictionaries,
        }
        # Preserve original_data_json if it was stored earlier
        if existing_original_data_json is not None:
            job_details["original_data_json"] = existing_original_data_json
        redis_instance.set(job_id, json.dumps(job_details))
        if trigger_manual_extraction(definitions):
            if batch_type in [".pdf", ".docx"]:
                ###
                # DocBuilder Process
                ###

                request_body = {
                    "job_id": job_id,
                }

                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Initiating Docbuilder process",
                )

                publish("start_process", "to_docbuilder", request_body)
        else:
            # If all keys are auto Skip docbuilder and utility extraction and directly call utility central
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Skip Manual extraction from docbuilder and utility.",
            )
            if auto_extraction_data_json:
                batch_instance.data_json = auto_extraction_data_json
                batch_instance.save()
            # Pass auto extraction data json
            job_details = {**job_details, "data_json": auto_extraction_data_json}
            redis_instance.set(job_id, json.dumps(job_details))
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Initiated data parsing and enrichment with key extraction, rules, normalization, and validation.",
            )
            request_body = {"job_id": job_id}

            publish("keyval_extractor", "to_utility", request_body)
    except:
        print(traceback.print_exc())
        if job_id:
            handle_service_failure(job_id)
        else:
            error = str(traceback.format_exc())
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Error occured during batch processing",
                remarks=error,
            )


def test_batch_p2(response_json):
    """
    Listen for input from docbuilder and push batch further
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="Docbuilder response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Docbuilder response received",
                remarks="Error parsing docbuilder log messages",
            )

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="Docbuilder process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            test_batch_cleanup(job_id)
            return

        ###
        # TableKeys Process
        ###
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiating TableKeys process",
        )

        request_body = {
            "job_id": job_id,
        }

        publish("process_table_keys", "to_utility", request_body)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p3(response_json):
    """
    Listen for input from utility and push batch further
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)
        auto_extraction_data_json = job_info.get("auto_extraction_data_json", {})
        manual_extraction_data_json = job_info.get("data_json", {})
        original_data_json = job_info.get("original_data_json", {})

        batch_id = job_info["batch_id"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="TableKeys-Processing response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="TableKeys-Processing response received",
            )
        if response_json["status_code"] != 200:
            # Only record and display user readable message.
            try:
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Batch execution failed",
                    remarks=response_json["error"],
                )

            except:
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Batch execution failed",
                    sub_message="TableKeys process did not send valid response",
                    action="display_json",
                    remarks=json.dumps(response_json),
                )

            test_batch_cleanup(job_id)
            return

        ###
        # Key extraction
        ###

        # Pass original_data_json directly in message for guaranteed delivery
        request_body = {"job_id": job_id, "original_data_json": original_data_json}

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Merging Data Json.",
            action="display_json",
            remarks=json.dumps(
                {
                    "auto_extraction_data_json": auto_extraction_data_json,
                    "manual_extraction_data_json": manual_extraction_data_json,
                }
            ),
        )

        # publish("keyval_extractor", "to_utility", request_body)
        publish("merge_data_json_from_auto_extraction", "to_pipeline", request_body)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p3_merge_data_json(response_json):
    try:

        job_id = response_json["job_id"]
        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)
        batch_id = job_info["batch_id"]
        auto_extraction_data_json = job_info.get("auto_extraction_data_json", {})
        manual_extraction_data_json = job_info.get("data_json", {})
        definitions = job_info.get("definitions", [])

        try:
            data_json = merge_data_json(
                auto_extraction_data_json, manual_extraction_data_json, definitions
            )
            data_json = normalize_merged_data(data_json, definitions)
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Merging Auto extraction and Manual data json completed.",
                action="display_json",
                remarks=json.dumps(data_json),
            )
        except Exception as error:
            print(traceback.print_exc())
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Merging process failed.",
                remarks=str(error),
            )
            return
        batch_instance = Batch.objects.get(id=batch_id)
        batch_instance.data_json = data_json
        batch_instance.save()
        template = job_info.get("template", None)
        table_unique_id = job_info.get("table_unique_id", None)
        definition_version = job_info.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )
        ###
        # Fetch Definitions
        ###

        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        if table_unique_id:
            definitions = reduce_definitions_for_table(definitions, table_unique_id)
        definition_ids = []
        if not template:
            definition_ids = [i["id"] for i in definitions]

        translation_codes = get_translation_codes_for_definitions(definition_ids)
        job_details = {
            **job_info,
            "data_json": batch_instance.data_json,
            "definitions": definitions,
            "translation_codes": translation_codes,
        }
        redis_instance.set(job_id, json.dumps(job_details))
        request_body = {"job_id": job_id}
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiated data parsing and enrichment with key extraction, rules, normalization, and validation.",
        )
        publish("keyval_extractor", "to_utility", request_body)
    except Exception as error:
        print(traceback.print_exc())
        try:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="An error occurred while merging auto extraction and manual data json",
                action="display_json",
                remarks=str(error),
            )
        except:
            pass


def test_batch_p3b(response_json):
    """
    Listen for input from utility and push batch further (for excel)
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="ExcelTable Process response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="ExcelTable Process response received",
                remarks="Error parsing ExcelTable Process log messages",
            )

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="ExcelTable process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            test_batch_cleanup(job_id)
            return

        ###
        # ExcelTableKeys Process
        ###

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiating ExcelTableKeys process",
        )

        request_body = {
            "job_id": job_id,
        }
        publish("excel_table_keys_process", "to_utility", request_body)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p3c(response_json):
    """
    Listen for input from utility and push batch further (for excel)
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="ExcelTableKeys Process response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="ExcelTableKeys Process response received",
                remarks="Error parsing ExcelTableKeys Process log messages",
            )

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="ExcelTableKeys process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            test_batch_cleanup(job_id)
            return

        ###
        # Key extraction
        ###
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Initiated data parsing and enrichment with key extraction, rules, normalization, and validation.",
        )
        request_body = {"job_id": job_id}
        publish("keyval_extractor", "to_utility", request_body)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p4(response_json):
    """
    Utility response receive and initiate post-processing
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]
        skip_post_processor = job_info["skip_post_processor"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="Utility response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Utility response received",
            )

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="Utility process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            test_batch_cleanup(job_id)
            return

        ###
        # Post-Processing
        ###

        if skip_post_processor is True:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Skipped Post-Processing",
            )

            test_batch_p6(job_id, job_info)
        else:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Initiating Post-Processing",
            )

            request_body = {"job_id": job_id}

            publish("post_processing", "to_utility", request_body)

    except Exception:
        handle_service_failure(job_id)


def test_batch_p5(response_json):
    """
    Post-Processing response receive and call test_batch_p6
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]
        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="Post-Processing response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Post-Processing response received",
                remarks="Error parsing post-processing log messages",
            )

        if response_json["status_code"] != 200:
            # Only record and display user readable message.
            try:
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Batch execution failed",
                    remarks=response_json["error"],
                )
            except:
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Batch execution failed",
                    sub_message="Post-Processing did not send valid response",
                    action="display_json",
                    remarks=json.dumps(response_json),
                )
            test_batch_cleanup(job_id)
            return
        test_batch_p6(job_id, job_info)

    except Exception:
        handle_service_failure(job_id)


def merge_auto_extraction_into_original_data_json(
    batch_instance, auto_extraction_data_json, original_data_json, document_id
):
    for document_data in original_data_json["nodes"]:
        if document_data["id"] == document_id:
            for idx, document_data_json in enumerate(original_data_json["nodes"]):
                if document_data_json["id"] == document_id:
                    # Replace the entire document node with the merged document data
                    original_data_json["nodes"][idx]["children"] = (
                        auto_extraction_data_json["nodes"][0]["children"]
                    )
                    break
    batch_instance.data_json = original_data_json


def test_batch_p6(job_id, job_info):
    """
    Update database
    """
    try:
        batch_id = job_info["batch_id"]
        data_json = job_info["data_json"]
        batch_mode = job_info["batch_mode"]
        template = job_info.get("template", None)
        project = job_info.get("project", None)
        ###
        # Updating Batch data in Database
        ###

        batch_instance = Batch.objects.get(id=batch_id)
        document_id = job_info.get("document_id", None)
        auto_extraction_data_json = job_info.get("auto_extraction_data_json", {})
        original_data_json = job_info.get("original_data_json", {})
        if document_id:
            merge_auto_extraction_into_original_data_json(
                batch_instance,
                auto_extraction_data_json,
                original_data_json,
                document_id,
            )
            # Ensure job_id is saved when document_id is provided
            batch_instance.job_id = job_id
            batch_instance.save()
        else:
            batch_instance.data_json = data_json
            batch_instance.job_id = job_id
            batch_instance.save()

        validation_required = False
        if batch_mode == "processing" and not template:
            # Check if transaction requires manual validation
            email_batch = EmailToBatchLink.objects.get(batch_id=batch_id).email
            email_id = email_batch.id
            matched_profile = Profile.objects.get(name=email_batch.matched_profile_name)
            validation_required = matched_profile.manual_validation

        if not validation_required:
            active_agents = get_active_agents_by_project(project)
            if active_agents:
                initiate_ai_agent_message(batch_id, active_agents)
                return

            ###
            # Output JSON API call
            ###
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Initiating OutputJSON process",
            )

            request_body = {"job_id": job_id}

            publish("output_json", "to_utility", request_body)
            return

        write_batch_log(
            batch_id=batch_id,
            status="waiting",
            message="Batch awaiting transaction review",
        )

        # Stop repeated message due to child batch reprocess
        if email_batch.status == "waiting":
            return

        # Check if all batches for a transactions are ready for review or not.
        # if yes, then update status of transaction to "waiting"
        linked_batches = list(
            EmailToBatchLink.objects.filter(
                email_id=email_id, uploaded=True
            ).values_list("batch_id", flat=True)
        )
        linked_batches_count = len(linked_batches)

        waiting_batches_qs = Batch.objects.filter(
            id__in=linked_batches, status="waiting"
        )

        waiting_batches_count = waiting_batches_qs.count()

        if linked_batches_count != waiting_batches_count:
            return

        save_analyzer_log_time(
            batch_id=email_id, field_name="transaction_awaiting_time"
        )
        write_parent_batch_log(
            batch_id=email_id,
            status="waiting",
            message="Transaction review awaited",
        )

        # Save Transaction ready to review status in DB.
        # Based on this Verification hyperlink will be enabled
        email_batch = EmailBatch.objects.get(id=email_id)
        email_batch.verification_status = "ready"
        email_batch.save()
    except Exception:
        handle_service_failure(job_id)


def test_batch_p6b(request_data):
    """
    If verification enabled, resume pending operations after user validation.
    """
    try:
        email_batch_id = request_data["email_batch_id"]
        write_parent_batch_log(
            batch_id=email_batch_id,
            status="inprogress",
            message="Transaction review completed",
        )

        # Once review has been completed, save staus in DB
        # So, when user re-visits the verification page, proper options can be displayed
        email_batch = EmailBatch.objects.get(id=email_batch_id)
        email_batch.verification_status = "submitted"
        email_batch.save()

        linked_batches = list(
            EmailToBatchLink.objects.filter(
                email_id=email_batch_id, uploaded=True
            ).values_list("batch_id", flat=True)
        )

        project = linked_batches[0].project if linked_batches else None

        active_agents = get_active_agents_by_project(project)

        if active_agents:
            initiate_ai_agent_message(batch_id, active_agents)
            return

        for batch_id in linked_batches:
            try:
                ###
                # Output JSON API call
                ###

                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Initiating OutputJSON process",
                )

                # Get job_id from batch_id
                batch_instance = Batch.objects.get(id=batch_id)

                if batch_instance.mode == "supporting":
                    write_batch_log(
                        batch_id=batch_id,
                        status="completed",
                        message="OutputJSON process bypassed",
                    )
                    continue

                job_id = batch_instance.job_id

                # retrive the job_id from redis
                job_info = redis_instance.get(job_id)
                job_info = json.loads(job_info)

                # Update the redis payload with latest data_json
                job_info["data_json"] = batch_instance.data_json
                redis_instance.set(job_id, json.dumps(job_info))

                request_body = {"job_id": job_id}

                publish("output_json", "to_utility", request_body)

            except Exception:
                error = str(traceback.format_exc())
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Error occured during batch processing",
                    remarks=error,
                )

    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during Transaction processing"
        remarks = {
            "message": f"The following error occured in 'test_batch_p6b' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=email_batch_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )
        send_failure_notification(email_batch_id, remarks["message"])


def test_batch_p6c(current_batch_id):
    """
    Initializing JSON output generation..
    """
    try:
        batch_instance = Batch.objects.get(id=current_batch_id)
        try:
            job_info = redis_instance.get(batch_instance.job_id)
            job_info = json.loads(job_info)
        except:
            print(f"Error parsing job_info for job_id: {batch_instance.job_id}")
            return

        definition_version = job_info.get("definition_version")
        profile_keys = job_info.get("profile_keys", [])
        profile_customers = job_info.get("profile_customers", [])
        dictionaries = job_info.get("dictionaries", [])
        master_dictionaries = job_info.get("master_dictionaries", {})
        definition_settings = job_info.get("definition_settings", {})
        definitions = job_info.get("definitions", [])

        (
            instanceToBatchLink,
            _,
            parent_batch,
            parent_batch_kwarg,
            *tail,
        ) = get_instance_classes(current_batch_id)

        linked_batches = list(
            instanceToBatchLink.objects.filter(
                **parent_batch_kwarg, uploaded=True
            ).values_list("batch_id", flat=True)
        )

        for batch_id in linked_batches:
            try:
                ###
                # Output JSON API call
                ###
                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Initiating OutputJSON process",
                )

                batch_instance = Batch.objects.get(id=batch_id)

                if batch_instance.mode == "supporting":
                    write_batch_log(
                        batch_id=batch_id,
                        status="completed",
                        message="OutputJSON process bypassed",
                    )
                    continue

                job_id = batch_instance.job_id

                try:
                    job_info = redis_instance.get(job_id)
                    job_info = json.loads(job_info)

                    # Update the redis payload with latest data_json
                    job_info["data_json"] = batch_instance.data_json
                    redis_instance.set(job_id, json.dumps(job_info))
                except:
                    batch_path = os.path.join(BATCH_INPUT_PATH, batch_instance.sub_path)

                    job_details = {
                        "batch_id": batch_id,
                        "definition_version": definition_version,
                        "ra_json": batch_instance.ra_json,
                        "definitions": definitions,
                        "master_dictionaries": master_dictionaries,
                        "data_json": batch_instance.data_json,
                        "definition_settings": definition_settings,
                        "batch_mode": batch_instance.mode,
                        "project": batch_instance.project,
                        "batch_path": batch_path,
                        "new_upload": False,
                        "profile_keys": profile_keys,
                        "profile_customers": list(profile_customers),
                        "dictionaries": dictionaries,
                    }

                    redis_instance.set(job_id, json.dumps(job_details))

                request_body = {"job_id": job_id}

                publish("output_json", "to_utility", request_body)
            except Exception:
                error = str(traceback.format_exc())
                write_failed_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Error occured during batch processing",
                    remarks=error,
                )
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during Transaction processing"
        remarks = {
            "message": f"The following error occured in 'test_batch_p6c' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )
        send_failure_notification(parent_batch.id, remarks["message"])


def test_batch_p7(response_json):
    """
    Receive and save output json and excel
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        # Get job info from redis
        try:
            job_info = redis_instance.get(job_id)
            job_info = json.loads(job_info)
        except:
            print(f"Error parsing job_info for job_id: {job_id}")
            return

        batch_id = job_info["batch_id"]
        batch_path = job_info["batch_path"]
        data_json = job_info["data_json"]
        ra_json = job_info["ra_json"]
        new_upload = job_info["new_upload"]
        batch_mode = job_info["batch_mode"]
        template = job_info.get("template", None)

        # Remove job information from redis
        redis_instance.delete(job_id)

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="OutputJSON response received",
                remarks=messages,
                action="display_subprocess_messages",
            )

        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="OutputJSON response received",
            )

        if response_json["status_code"] != 200:
            write_failed_log(
                batch_id=batch_id,
                status="failed",
                message="Batch execution failed",
                sub_message="OutputJSON process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            test_batch_cleanup(job_id)
            return

        output_json = job_info["output_json"]

        ###
        # Save Output JSON on disk
        ###

        output_json_path = os.path.join(batch_path, batch_id, "output.json")
        with open(output_json_path, "w") as f:
            json.dump(output_json, f)

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Output json stored in batch folder",
            action="download_output_json",
        )

        ###
        # Save DataJson excel on disk
        ###
        DJsonToExcel(data_json, batch_path, batch_id).process()

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="DataJson Excel stored in batch folder",
            action="download_djson_excel",
        )

        # If Test is for new uploaded batch, send ICAP calls
        if new_upload:
            ###
            # Send output JSON via API Call (only in processing mode)
            ###

            if batch_mode == "processing":
                # Saving OutputJSON to DB
                output_json_qs = OutputJson.objects.filter(batch_id=batch_id)

                if output_json_qs.exists():
                    output_json_instance = output_json_qs.first()
                    output_json_instance.output_json = output_json
                    output_json_instance.save()
                else:
                    OutputJson.objects.create(
                        output_json=output_json, batch_id=batch_id
                    )

                write_batch_log(
                    batch_id=batch_id,
                    status="completed",
                    message="Batch is ready to assemble",
                )

                request_data = {"batch_id": batch_id}

                publish("assembly_queued", "to_pipeline", request_data)

        write_batch_log(
            batch_id=batch_id, status="completed", message="Batch Completed - Success"
        )

        if batch_mode == "training" and not template:
            train_batch = TrainToBatchLink.objects.get(batch_id=batch_id).train_batch

            # Stop repeated message due to batch processing
            if train_batch.status == "completed":
                return

            linked_batches = list(
                TrainToBatchLink.objects.filter(
                    train_batch_id=train_batch.id, uploaded=True
                ).values_list("batch_id", flat=True)
            )
            linked_batches_count = len(linked_batches)

            completed_batches_qs = Batch.objects.filter(
                id__in=linked_batches, status="completed"
            )

            completed_batches_count = completed_batches_qs.count()

            if linked_batches_count != completed_batches_count:
                return

            write_parent_batch_log(
                batch_id=train_batch.id,
                status="completed",
                message="Training process completed",
                train_batch_log=True,
            )
    except Exception:
        handle_service_failure(job_id)


def initiate_ai_agent_message(batch_id, active_agents):
    write_batch_log(
        batch_id=batch_id,
        status="awaiting_agent",
        message="Pending agent trigger",
    )
    instanceToBatchLink, _, parent_batch, parent_batch_kwarg, *tail = (
        get_instance_classes(batch_id)
    )
    if parent_batch:
        AiAgentConversation.objects.filter(transaction_id=parent_batch.id).delete()

    linked_batches = list(
        instanceToBatchLink.objects.filter(
            **parent_batch_kwarg, uploaded=True
        ).values_list("batch_id", flat=True)
    )

    with transaction.atomic():
        # Lock all linked batch rows — second caller blocks here until first finishes
        locked_batches = (
            Batch.objects.filter(
                id__in=linked_batches, mode__in=["processing", "training"]
            )
            .exclude(id=batch_id)
            .select_for_update()
        )

        other_ready_batches = list(locked_batches.values_list("status", flat=True))

        if any(
            item not in ["completed", "failed", "awaiting_agent"]
            for item in other_ready_batches
        ):
            return

    # Re-query without select_for_update() for safe use outside the transaction
    other_batches = Batch.objects.filter(
        id__in=linked_batches, mode__in=["processing", "training"]
    ).exclude(id=batch_id)

    batch_instance = Batch.objects.get(id=batch_id)
    keys, _ = get_extraction_payload(batch_instance)

    send_message_to_ai_agent(
        active_agents,
        batch_id,
        parent_batch.id,
        other_batches,
        process_keys=keys,
    )


def send_message_to_ai_agent(
    active_agents, batch_id, parent_batch_id, other_batches, process_keys=[]
):
    try:
        batch_instance = Batch.objects.get(id=batch_id)
        project_name = batch_instance.project
        process_name = batch_instance.definition_id
        ra_json = batch_instance.ra_json
        data_json = batch_instance.data_json

        other_data_jsons = list(other_batches.values_list("data_json", flat=True))
        other_ra_jsons = list(other_batches.values_list("ra_json", flat=True))

        combined_ra_json = [ra_json] + other_ra_jsons
        combined_data_json = [data_json] + other_data_jsons

        payload = {
            "batch_id": batch_id,
            "transaction_id": parent_batch_id,
            "message_type": "timeline",
            "rabbitmq_message_type": "ai_agent_response",
            "active_agents": active_agents,
            "combined_ra_json": combined_ra_json,
            "combined_data_json": combined_data_json,
            "project_name": project_name,
            "process_name": process_name,
            "process_keys": process_keys,
        }

        # Add timeline logging at the batch level
        if any(agent in ["hbl_mbl", "dynamic_content_creation", "shipment_table"] for agent in active_agents):
            for d_json in combined_data_json:   
                linked_batch_id = d_json.get("id")
                write_batch_log(
                    batch_id=linked_batch_id,
                    status="awaiting_agent",
                    message="Awaiting agent response",
                    action="display_json",
                    remarks=json.dumps(d_json),
                )

        for agent_name in active_agents:
            message = {
                "batch_id": batch_id,
                "transaction_id": parent_batch_id,
                "message_type": "timeline",
                "message": "Requesting service from AI agent",
                "agent_name": convert_to_title(agent_name),
                "status_code": 200,
                "remarks": [],
            }

            ai_agent_message_instance = AiAgentConversation.objects.create(
                transaction_id=parent_batch_id,
                batch_id=batch_id,
                type="timeline",
                message=message,
            )

            serialize_message = AiAgentConversationSerializer(ai_agent_message_instance)

            async_to_sync(channel_layer.group_send)(
                f"ai_agent_response_{batch_id}",
                {
                    "type": "ai_agent_response",
                    "data": serialize_message.data,
                },
            )

        # Send AI Agent request via RabbitMQ
        print("Send request to ai_agent rabbitmq")
        publish("ai_agent", "to_ai_agent", payload)
    except Exception as error:
        print(f"{error=}")
        message = {
            "batch_id": batch_id,
            "message_type": "timeline",
            "message": "Service request to agent failed",
            "color_code": "red",
            "agent_name": convert_to_title(agent_name),
            "status_code": 500,
        }

        ai_agent_message_instance = AiAgentConversation.objects.create(
            transaction_id=parent_batch_id,
            batch_id=batch_id,
            type="timeline",
            message=message,
        )

        serialize_message = AiAgentConversationSerializer(ai_agent_message_instance)

        async_to_sync(channel_layer.group_send)(
            f"ai_agent_response_{batch_id}",
            {"type": "ai_agent_response", "data": serialize_message.data},
        )


def test_batch_p8(request_data):
    """
    Assembly Process
    """
    try:
        print(f"test_batch_p8 | {request_data=}")
        batch_id = request_data["batch_id"]

        try:
            # Check if all batches in email are processed or not.
            email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        except:
            # If error occurs, while fetching email from batch,
            # Transaction has been already removed, so no need to process further
            print(f"Exception occured while fetching email from batch {batch_id}")
            return

        # If assembly is already triggered for transaction, do not re-trigger it.
        if email_instance.assembly_triggered:
            return

        email_id = email_instance.id

        linked_batches = list(
            EmailToBatchLink.objects.filter(
                email_id=email_id, uploaded=True
            ).values_list("batch_id", flat=True)
        )
        linked_batches_count = len(linked_batches)

        output_json_qs = OutputJson.objects.filter(batch_id__in=linked_batches)
        output_json_count = output_json_qs.count()

        if linked_batches_count != output_json_count:
            return

        linked_batches_qs = Batch.objects.filter(id__in=linked_batches)

        if not any([i.mode == "processing" for i in linked_batches_qs]):
            return

        # Ensure the assembly hasn’t already been triggered due to concurrency issues before proceeding
        sleep_duration = random.uniform(0.01, 0.02)
        time.sleep(sleep_duration)
        email_instance.refresh_from_db()
        if email_instance.assembly_triggered:
            return

        email_instance.assembly_triggered = True
        email_instance.save()
        save_analyzer_log_time(batch_id=email_id, field_name="assembly_process_s")
        write_parent_batch_log(
            batch_id=email_id,
            status="inprogress",
            message="Assembly process initiated",
        )

        batches_data = []

        output_json_data = output_json_qs.all().values(
            "batch__id", "output_json", "batch__type"
        )

        for i in output_json_data:
            item = {
                "id": i["batch__id"],
                "data": i["output_json"],
                "type": i["batch__type"],
            }
            batches_data.append(item)

        batch_id = linked_batches[0]
        batch_instance = Batch.objects.get(id=batch_id)
        other_batches = Batch.objects.filter(
            id__in=linked_batches, mode__in=["processing", "training"]
        ).exclude(id=batch_id)

        keys, _ = get_extraction_payload(batch_instance)

        send_message_to_ai_agent(
            ["data_modification"],
            batch_id,
            email_id,
            other_batches,
            process_keys=keys,
        )
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"AIDB-106: The following error occured - '{str(error.args[0])}' ",
            "traceback": trace,
            "code": "AIDB-106",
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])


def test_batch_p8b(transaction_id, ai_agent_response):
    """
    Resume Assembly Process
    """

    try:
        # print(f"test_batch_p8b | {request_data=}")
        email_id = transaction_id

        ai_agent_result = ai_agent_response.get(
            "result", [{"data": {"batch": email_id}}]
        )

        write_parent_batch_log(
            batch_id=email_id,
            status="inprogress",
            message="AI agent response received",
            action="display_json",
            remarks=json.dumps(ai_agent_result, indent=4),
        )

        email_instance = EmailBatch.objects.get(id=email_id)

        linked_batches = list(
            EmailToBatchLink.objects.filter(
                email_id=email_id, uploaded=True
            ).values_list("batch_id", flat=True)
        )

        matched_profile_instance = Profile.objects.get(
            name=email_instance.matched_profile_name
        )

        project = matched_profile_instance.project
        profile_name = matched_profile_instance.name
        multi_shipment = matched_profile_instance.multi_shipment
        error_from_ai_agent = ai_agent_response.get("error")
        assembled_results = ai_agent_result

        # FOR DEBUGGING PURPOSES ONLY
        # assembled_results_path = os.path.join(
        #     BATCH_INPUT_PATH, "email-batches", email_id, "assembled_results_check.json"
        # )
        # ai_agent_response_path = os.path.join(
        #     BATCH_INPUT_PATH, "email-batches", email_id, "ai_agent_response.json"
        # )
        # with open(ai_agent_response_path, "w") as f:
        #     json.dump(ai_agent_response, f, indent=4)
        # with open(assembled_results_path, "w") as f:
        #     json.dump(assembled_results, f, indent=4)

        assembled_results = duplicate_shipment_id_checker(
            write_parent_batch_log, assembled_results, profile_name, email_id
        )

        # Ensure assembly results haven’t been already generated due to concurrency issues
        if len(email_instance.assembled_results) != 0:
            return

        is_validation_errors = False

        email_batch_type = get_hardcoded_project_type(project)
        final_output_jsons = []
        # Raise validations errors
        for result in assembled_results:
            result["validation_errors"] = []
            if result.get("data"):
                result["data"]["batchid"] = email_id

            batch_type = result.get("type", "")
            if batch_type:
                email_batch_type = batch_type

            deflattening_payload = {
                "input_json": result.get("data", {}),
                "project": project,
                "profile_name": profile_name,
                "main_table": result.get("main_table", []),
                "batch_type": batch_type,
            }

            result["data"] = central_output_handler(deflattening_payload)

            result["type"] = email_batch_type
            result["batches"] = linked_batches
            result.pop("main_table", None)
            result_data = result["data"]
            final_output_jsons.append(result["data"])

            # Check if result_data is empty or only contains batchid
            is_empty = len(result_data) == 0
            only_has_batchid = len(result_data) == 1 and "batchid" in result_data

            if is_empty or only_has_batchid:
                error_message = "Output Json is empty"
                if error_from_ai_agent:
                    error_message = (
                        "Error in AI Agent Processing final output json. Process Couldn't be completed due to: "
                        + error_from_ai_agent
                    )
                result["validation_errors"].insert(0, error_message)

            validation_errors = result["validation_errors"]
            if validation_errors:
                is_validation_errors = True

        email_instance.assembled_results = assembled_results
        email_instance.save()

        if len(assembled_results) == 0:
            # is_validation_errors = True
            # assembled_results = ["Assembly Result is Empty"]
            write_parent_batch_log(
                message="Assembly Result is Empty",
                batch_id=email_id,
                status="inprogress",
            )
            write_parent_batch_log(
                message="Transaction process completed.",
                batch_id=email_id,
                status="completed",
            )
            return

        save_analyzer_log_time(
            batch_id=email_id, field_name="transaction_result_generated_time"
        )

        # If Mock API is enabled, validation errors should be ignored
        mock_api = get_developer_settings("Mock API")
        if mock_api:
            is_validation_errors = False

        if is_validation_errors:
            message = "Transaction result(s) generated with validation errors"
            status = "failed"

        else:
            message = "Transaction result(s) generated without validation errors"
            status = "inprogress"

        if multi_shipment:
            message += f" ({len(assembled_results)})"

        write_parent_batch_log(
            message=message,
            batch_id=email_id,
            remarks="" if multi_shipment else json.dumps(assembled_results),
            status=status,
            action="display_paginated_json" if multi_shipment else "display_json",
        )

        if is_validation_errors:
            send_failure_notification(email_id, message)
            return

        # Initiating Post Processing
        request_body = {
            "batch_id": linked_batches[0],
            "process_name": profile_name,
            "final_output_jsons": final_output_jsons,
        }

        write_batch_log(
            batch_id=email_id,
            status="inprogress",
            message="Initiating Post Processing",
            action="display_json",
            remarks=json.dumps(request_body, indent=4),
        )

        publish("postprocess_output_json", "to_postprocess", request_body)

    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"AIDB-106: The following error occured - '{str(error.args[0])}' ",
            "traceback": trace,
            "code": "AIDB-106",
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])


def test_batch_p8c(request_data):
    """
    Handle Post Processing Response
    """
    email_id = None
    batch_id = None
    try:
        print(f"test_batch_p8c | {request_data=}")
        batch_id = request_data["batch_id"]
        status_code = request_data["status_code"]
        email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        email_id = email_instance.id

        if status_code == 200:
            message = "Post Processing Success"
            status = "inprogress"

            final_output_jsons = request_data.get("final_output_jsons", [])

            for index, item in enumerate(email_instance.assembled_results):
                if index >= len(final_output_jsons):
                    continue
                item["data"] = final_output_jsons[index]
            email_instance.save()

            remarks = {
                "status_code": status_code,
                "final_output_jsons": final_output_jsons,
            }
        else:
            message = "Post Processing Skipped"
            status = "warning"
            error = request_data.get("error", "")
            remarks = {"status_code": status_code, "error": error}

        write_parent_batch_log(
            batch_id=email_id,
            status=status,
            message=message,
            action="display_json",
            remarks=json.dumps(remarks, indent=4),
        )

        test_batch_p9({"batch_id": batch_id})
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"AIDB-106: The following error occured - '{str(error.args[0])}' ",
            "traceback": trace,
            "code": "AIDB-106",
        }

        # Use batch_id if email_id is not available
        log_batch_id = email_id if email_id is not None else batch_id
        if log_batch_id:
            write_parent_batch_log(
                batch_id=log_batch_id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
            )
            send_failure_notification(log_batch_id, remarks["message"])


def test_batch_p9(request_data):
    """
    Handle API calls
    """
    try:
        print(f"test_batch_p9 | {request_data=}")
        batch_id = request_data["batch_id"]

        try:
            # Check if all batches in email are processed or not.
            email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        except Exception as error:
            # If error occurs, while fetching email from batch,
            # Transaction has been already removed, so no need to process further
            print(
                f"Exception occured while fetching email from batch {batch_id} | {error=}"
            )
            return
        if email_instance.api_triggered:
            return

        email_instance.api_triggered = True
        email_instance.save()

        email_id = email_instance.id
        matched_profile_instance = Profile.objects.get(
            name=email_instance.matched_profile_name
        )

        all_passed, is_retrying = process_output_channel(
            write_parent_batch_log, email_instance, matched_profile_instance
        )

        if is_retrying:
            email_instance.api_triggered = False
            email_instance.doc_upload_triggered = False
            email_instance.save()

            schedule_delayed_publish_to_rabbitmq(
                "api_call_queued", "to_pipeline", request_data, RETRY_INTERVAL
            )
            return

        if not all_passed:
            api_responses = email_instance.api_response
            resp_data = []
            has_product_code = False

            for response in api_responses:
                if not has_product_code:
                    has_product_code = response.get("response_json", {}).get("productCode")

                if response.get("status_code", 0) != 200:
                    resp_data.append(response["response_json"])

            message = "Assembly process aborted due to failed APIs"

            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="failed",
            )

            email_message = f"{message} \n    response json: {resp_data}"

            send_failure_notification(email_id, email_message)
            return

        test_batch_p10(request_data)
    except Exception as error:
        print(traceback.print_exc())
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"The following error occured in 'test_batch_p9' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])


def test_batch_p10(request_data):
    """
    Assembly process end here and send email notification
    """
    try:
        print("test batch 10")
        print(f"{request_data=}")
        batch_id = request_data["batch_id"]

        try:
            # Check if all batches in email are processed or not.
            email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        except:
            # If error occurs, while fetching email from batch,
            # Transaction has been already removed, so no need to process further
            print(f"Exception occured while fetching email from batch {batch_id}")
            return

        if email_instance.doc_upload_triggered:
            return

        email_id = email_instance.id
        email_instance.doc_upload_triggered = True
        email_instance.save()

        matched_profile_instance = Profile.objects.get(
            name=email_instance.matched_profile_name
        )
        multi_shipment = matched_profile_instance.multi_shipment

        # Once response has fcmID not call CW1 document upload API
        identifiers = []
        failed_identifiers = []
        fcm_id = []
        shipment_id = []
        housebill_number = []
        failed_api_call_count = 0
        failed_doc_upload_count = 0
        api_responses = email_instance.api_response

        for item in api_responses:
            response_json = item["response_json"]
            if response_json.get("fcmID"):
                identifiers.append(response_json.get("identifier"))
                fcm_id.append(response_json["fcmID"])
                if response_json.get("housebillNumber"):
                    housebill_number.append(response_json.get("housebillNumber"))

            if multi_shipment:
                if item["status_code"] != 200:
                    failed_api_call_count += 1
                    failed_identifiers.append(response_json.get("identifier"))
            res_shipment_id = response_json.get("shipmentID")
            # If shipment ID does not exists create one in system
            if res_shipment_id:

                def _create_new_shipment_record_if_not_exists(s_id):
                    shipment_record_kwargs = {
                        "shipment_id": s_id,
                    }
                    if not ShipmentRecord.objects.filter(
                        **shipment_record_kwargs
                    ).exists():
                        ShipmentRecord.objects.create(**shipment_record_kwargs)

                if item["status_code"] == 200:
                    if isinstance(res_shipment_id, list):
                        for i in res_shipment_id:
                            _create_new_shipment_record_if_not_exists(i)
                    elif isinstance(res_shipment_id, str):
                        _create_new_shipment_record_if_not_exists(res_shipment_id)

        identifiers = identifiers + failed_identifiers

        (
            edm_upload_error,
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            failed_doc_upload_count,
        ) = handle_output_doc_upload(
            write_parent_batch_log, email_instance, matched_profile_instance, fcm_id
        )

        if is_retrying:
            email_instance.doc_upload_triggered = False
            email_instance.save()

            schedule_delayed_publish_to_rabbitmq(
                "doc_upload_queued", "to_pipeline", request_data, RETRY_INTERVAL
            )
            return

        if not edm_upload_error:
            save_analyzer_log_time(batch_id=email_id, field_name="assembly_process_e")

            # Send success notifications
            context, message = prepare_email_context(
                email_instance,
                multi_shipment,
                identifiers,
                shipment_id,
                fcm_id,
                housebill_number,
                failed_api_call_count,
                failed_doc_upload_count,
            )
            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="completed",
            )

            send_success_notification(email_id, context)
        else:
            message = "Assembly process ended with doc upload failures"
            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="failed",
            )

            if multi_shipment:
                message += f". None of the {len(api_responses)} shipments were created"

            send_failure_notification(email_id, message)
        save_analyzer_log_time(
            batch_id=email_id, field_name="re_process_email_batches_e"
        )
        save_analyzer_log_time(batch_id=email_id, field_name="transaction_process_e")
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"The following error occured in 'test_batch_p10' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])
        save_analyzer_log_time(
            batch_id=email_id, field_name="re_process_email_batches_e"
        )
        save_analyzer_log_time(batch_id=email_id, field_name="transaction_process_e")


def test_batch_p9_old(request_data):
    """
    Handle API calls
    """
    try:
        print(f"test_batch_p9 | {request_data=}")
        batch_id = request_data["batch_id"]

        try:
            # Check if all batches in email are processed or not.
            email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        except:
            # If error occurs, while fetching email from batch,
            # Transaction has been already removed, so no need to process further
            print(f"Exception occured while fetching email from batch {batch_id}")
            return
        if email_instance.api_triggered:
            return

        email_instance.api_triggered = True
        email_instance.save()

        email_id = email_instance.id
        matched_profile_instance = Profile.objects.get(
            name=email_instance.matched_profile_name
        )
        multi_shipment = matched_profile_instance.multi_shipment

        all_passed, is_retrying = handle_api_call(
            write_parent_batch_log, email_instance, matched_profile_instance
        )

        if is_retrying:
            email_instance.api_triggered = False
            email_instance.doc_upload_triggered = False
            email_instance.save()

            schedule_delayed_publish_to_rabbitmq(
                "api_call_queued", "to_pipeline", request_data, RETRY_INTERVAL
            )
            return

        if not all_passed:
            api_responses = email_instance.api_response
            resp_data = []
            has_product_code = False

            for response in api_responses:
                if not has_product_code:
                    has_product_code = response["response_json"].get("productCode")

                if response.get("status_code", 0) != 200:
                    resp_data.append(response["response_json"])

            if has_product_code:
                message = "Assembly process aborted due to failed APIs"
            else:
                message = "CW1 edoc Upload proccess aborted due to failed APIs"

            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="failed",
            )

            email_message = f"{message} \n    response json: {resp_data}"

            if multi_shipment:
                email_message = f"{message}. None of the {len(api_responses)} shipments were created."

            send_failure_notification(email_id, email_message)
            return

        test_batch_p10(request_data)
    except Exception as error:
        print(traceback.print_exc())
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"The following error occured in 'test_batch_p9' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])


def test_batch_p10_old(request_data):
    """
    Assembly process end here and send email notification
    """
    try:
        print("test batch 10")
        print(f"{request_data=}")
        batch_id = request_data["batch_id"]

        try:
            # Check if all batches in email are processed or not.
            email_instance = EmailToBatchLink.objects.get(batch_id=batch_id).email
        except:
            # If error occurs, while fetching email from batch,
            # Transaction has been already removed, so no need to process further
            print(f"Exception occured while fetching email from batch {batch_id}")
            return

        if email_instance.doc_upload_triggered:
            return

        email_id = email_instance.id
        email_instance.doc_upload_triggered = True
        email_instance.save()

        matched_profile_instance = Profile.objects.get(
            name=email_instance.matched_profile_name
        )
        multi_shipment = matched_profile_instance.multi_shipment

        # Once response has fcmID not call CW1 document upload API
        identifiers = []
        failed_identifiers = []
        fcm_id = []
        shipment_id = []
        housebill_number = []
        failed_api_call_count = 0
        failed_doc_upload_count = 0
        is_retrying = False
        edm_upload_error = False
        api_responses = email_instance.api_response

        for item in api_responses:
            response_json = item["response_json"]
            if response_json.get("fcmID"):
                identifiers.append(response_json.get("identifier"))
                fcm_id.append(response_json["fcmID"])
                if response_json.get("housebillNumber"):
                    housebill_number.append(response_json.get("housebillNumber"))

            if multi_shipment:
                if item["status_code"] != 200:
                    failed_api_call_count += 1
                    failed_identifiers.append(response_json.get("identifier"))
            res_shipment_id = response_json.get("shipmentID")
            # If shipment ID does not exists create one in system
            if res_shipment_id:

                def _create_new_shipment_record_if_not_exists(s_id):
                    shipment_record_kwargs = {
                        "shipment_id": s_id,
                    }
                    if not ShipmentRecord.objects.filter(
                        **shipment_record_kwargs
                    ).exists():
                        ShipmentRecord.objects.create(**shipment_record_kwargs)

                if item["status_code"] == 200:
                    if isinstance(res_shipment_id, list):
                        for i in res_shipment_id:
                            _create_new_shipment_record_if_not_exists(i)
                    elif isinstance(res_shipment_id, str):
                        _create_new_shipment_record_if_not_exists(res_shipment_id)

        identifiers = identifiers + failed_identifiers

        (
            edm_upload_error,
            identifiers,
            shipment_id,
            housebill_number,
            is_retrying,
            failed_doc_upload_count,
        ) = handle_doc_upload(
            write_parent_batch_log, email_instance, matched_profile_instance, fcm_id
        )

        if is_retrying:
            email_instance.doc_upload_triggered = False
            email_instance.save()

            schedule_delayed_publish_to_rabbitmq(
                "doc_upload_queued", "to_pipeline", request_data, RETRY_INTERVAL
            )
            return

        if not edm_upload_error:
            save_analyzer_log_time(batch_id=email_id, field_name="assembly_process_e")

            # Send success notifications
            context, message = prepare_email_context(
                email_instance,
                multi_shipment,
                identifiers,
                shipment_id,
                fcm_id,
                housebill_number,
                failed_api_call_count,
                failed_doc_upload_count,
            )
            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="completed",
            )

            send_success_notification(email_id, context)
        else:
            message = "Assembly process ended with doc upload failures"
            write_parent_batch_log(
                message=message,
                batch_id=email_id,
                status="failed",
            )

            if multi_shipment:
                message += f". None of the {len(api_responses)} shipments were created"

            send_failure_notification(email_id, message)
        save_analyzer_log_time(
            batch_id=email_id, field_name="re_process_email_batches_e"
        )
        save_analyzer_log_time(batch_id=email_id, field_name="transaction_process_e")
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during assembly process"
        remarks = {
            "message": f"The following error occured in 'test_batch_p10' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=email_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )

        send_failure_notification(email_id, remarks["message"])
        save_analyzer_log_time(
            batch_id=email_id, field_name="re_process_email_batches_e"
        )
        save_analyzer_log_time(batch_id=email_id, field_name="transaction_process_e")


def atm_process_p1(request_data):
    """
    definition_id: ID of profile to be processed.
    definition_type: type of profile to be processed.
    batch_id: ID of batch.
    user_selected_patterns: Patterns selected by user.
    extended_user_selected_patterns: Patterns selected by user.
    multiple_line_record: multiple table row process activition flag.
    user_selected_ob: Open Blocks selected by user.
    record_line: Number of lines in a table row.
    digit_threshold: Digit Threshold.
    text_threshold: Text Threshold.
    definition_version : Which version of definition to be used for processing docs
    """

    batch_id = request_data["batch_id"]
    definition_id = request_data["definition_id"]
    definition_type = request_data["definition_type"]
    name_matching_text = request_data["name_matching_text"]
    table_unique_id = request_data["table_unique_id"]
    user_selected_patterns = request_data["user_selected_patterns"]
    extended_user_selected_patterns = request_data["extended_user_selected_patterns"]
    multiple_line_record = request_data["multiple_line_record"]
    user_selected_ob = request_data["user_selected_ob"]
    record_line = request_data["record_line"]
    digit_threshold = request_data["digit_threshold"]
    text_threshold = request_data["text_threshold"]
    definition_version = request_data["definition_version"]
    template = request_data.get("template", None)
    job_id = gerenate_job_id_for_batch(batch_id)
    print(f"Processing Automated Table Model {batch_id}")
    print(f"{job_id=}")

    write_batch_log(
        batch_id=batch_id,
        status="inprogress",
        message="Automated Table Model Processing Started",
    )

    write_batch_log(
        batch_id=batch_id,
        status="inprogress",
        message=f"Definition Version: {definition_version}",
    )

    try:
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Combining ra_json for batches",
        )
        batch_instance = Batch.objects.get(id=batch_id)

        ###
        # Reset data json
        ###
        batches = []

        batch_ids_by_definition_type = list(
            Batch.objects.filter(vendor=batch_instance.vendor).values_list(
                "id", flat=True
            )
        )

        for item_id in batch_ids_by_definition_type:
            ra_json = Batch.objects.get(id=item_id).ra_json

            batches.append(
                {
                    "id": item_id,
                    "ra_json": ra_json,
                }
            )

        sub_path = batch_instance.sub_path

        batch_path = os.path.join(BATCH_INPUT_PATH, sub_path)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path)

        ###
        # Fetch Definitions
        ###

        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        if table_unique_id:
            definitions = reduce_definitions_for_table(definitions, table_unique_id)

        batch_type = ra_json.get(
            "batch_type", ".pdf"
        )  # .pdf is fallback type for old batches

        # Save all info in global jobs
        job_details = {
            "batches": batches,
            "batch_id": batch_id,
            "batch_path": batch_path,
            "batch_type": batch_type,
            "atm_data": {},
            "definitions": definitions,
            "definition_version": definition_version,
            "user_selected_patterns": user_selected_patterns,
            "extended_user_selected_patterns": extended_user_selected_patterns,
            "multiple_line_record": multiple_line_record,
            "user_selected_ob": user_selected_ob,
            "record_line": record_line,
            "digit_threshold": digit_threshold,
            "text_threshold": text_threshold,
            "template": template,
        }

        redis_instance.set(job_id, json.dumps(job_details))

        if batch_type in [".pdf", ".docx"]:
            ###
            # AutomatedTableModel Process
            ###

            request_body = {
                "job_id": job_id,
            }

            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Initiating AutomatedTableModel process",
            )

            publish("atm_process", "to_docbuilder", request_body)

    except Exception:
        handle_service_failure(job_id)


def atm_process_p2(response_json):
    """
    Listen for input from docbuilder and push batch further
    """
    try:
        print(f"{response_json=}")
        job_id = response_json["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]
        batch_path = job_info["batch_path"]
        atm_data = job_info["atm_data"]

        try:
            status, messages = get_response_messages(response_json)

            write_batch_log(
                batch_id=batch_id,
                status=status,
                message="Automated Table Model response received",
                remarks=messages,
                action="display_subprocess_messages",
            )
        except:
            write_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Automated Table Model response received",
                remarks="Error parsing Automated Table Model log messages",
            )

        if response_json["status_code"] != 200:
            write_batch_log(
                batch_id=batch_id,
                status="failed",
                message="Automated Table Model request execution failed",
                sub_message="AutomatedTableModel process did not send valid response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            job_id_cleanup(job_id)
            return

        ###
        # Save Automated Table Model JSON on disk
        ###
        batch_dir_path = os.path.join(batch_path, batch_id)

        if not os.path.isdir(batch_dir_path):
            os.makedirs(batch_dir_path)

        automated_table_model_json_path = os.path.join(
            batch_dir_path, "automated_table_model.json"
        )

        with open(automated_table_model_json_path, "w") as f:
            json.dump(atm_data, f)

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Automated Table Model Json stored in batch folder",
            action="download_automated_table_model_json",
        )

        ###
        # AutomatedTableModel Post Process
        ###
        atm_process_p3(job_id, job_info)
    except Exception:
        handle_service_failure(job_id)


def atm_process_p3(job_id, job_info):
    """
    Post-Processing for Automated Table Model JSON
    """
    batch_id = job_info["batch_id"]
    atm_data = job_info["atm_data"]
    record_line = job_info["record_line"]
    digit_threshold = job_info["digit_threshold"]
    text_threshold = job_info["text_threshold"]

    # Remove job information from redis
    try:
        redis_instance.delete(job_id)
    except Exception as e:
        print(f"Error deleting Redis key {job_id}: {str(e)}")

    try:
        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Post-Processing Started for Automated Table Model",
        )

        atm_data = post_process_atm_data(
            atm_data, digit_threshold, text_threshold, record_line
        )

        ###
        # Updating Batch data in Database
        ###
        batch_instance = Batch.objects.get(id=batch_id)
        batch_instance.atm_data = atm_data
        batch_instance.save()

        write_batch_log(
            batch_id=batch_id,
            status="completed",
            message="Automated Table Model job successful",
        )
    except Exception as e:
        write_batch_log(
            batch_id=batch_id,
            status="failed",
            message="Automated Table Model Json processing failed",
            remarks=str(e),
        )


####
# Functions
####


def get_info_holder_for_batch(batch_path, batch_id):
    """
    Iterates over each config object and returns matched object.
    """
    try:
        info_holder_options = []
        valid_page_types = []

        if ApplicationSettings.objects.exists():
            def_settings = ApplicationSettings.objects.first().data

            try:
                page_type_items = def_settings["options"]["options-page-type"]["items"]
                valid_page_types = [i["pageType"] for i in page_type_items]
            except:
                pass

            try:
                info_holder_options = def_settings["options"]["options-info-holder"][
                    "items"
                ]
            except:
                pass

        for option in info_holder_options:
            layout_file_name = option["name"]

            if os.path.exists(os.path.join(batch_path, batch_id, layout_file_name)):
                return option, valid_page_types
    except:
        raise ValueError("Error parsing InfoHolderOptions")

    raise ValueError(
        "Layout File could not be found on input location, Please check inputs and Info Holder options"
    )


def get_definitions_for_batch(
    batch_instance,
    definition_version=settings.DEFAULT_DEFINITION_VERSION,
    template=None,
):
    """
    Fetch Defintions from Database for given batch
    """
    definitions = []
    if template:
        qs = Template.objects.filter(template_name=template)
        template = qs.first()
        filtered_data = template.definition[definition_version]
        definition_data = {
            "definition_id": template.template_name,
            "type": template.doc_type,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }
        definition_data.update(filtered_data)
        definitions.append(definition_data)
    else:
        layout_ids = [
            item.get("layout_id")
            for item in batch_instance.layout_ids
            if item.get("layout_id")
        ]
        qs = Definition.objects.filter(
            definition_id__iexact=batch_instance.definition_id,
            layout_id__in=layout_ids,
        )
        if qs.exists():
            for definition in qs:
                def_data = DefinitionSerializer(definition).data

                if not (definition_version in def_data["data"].keys()):
                    raise ValueError(
                        f"Definition not found for version {definition_version}"
                    )

                # Filter definition version
                filtered_data = def_data["data"][definition_version]
                # TODO: Remove this comment static assign camel case to definition data.
                # for k in filtered_data.get("key",{}).get("items",[]):
                #     k["keyLabel"] = to_camel_case(k["keyLabel"])
                del def_data["data"]
                def_data.update(filtered_data)

                definitions.append(def_data)
        else:
            # Generate default definition when no definition is found
            default_definitions_class = DefaultDefinitions(ApplicationSettings)
            default_data = default_definitions_class.default_definition()

            # Extract batch type for appropriate defaults
            batch_type = getattr(batch_instance, "batch_type", ".pdf")
            if hasattr(batch_instance, "ra_json") and batch_instance.ra_json:
                batch_type = batch_instance.ra_json.get("batch_type", ".pdf")

            # Get version-specific default data
            version_data = default_data.get(definition_version, {})
            if version_data.get("key") == {}:
                version_data["key"] = {
                    "items": [],
                    "models": [],
                    "ruleItems": [],
                    "sampleBlocks": [],
                    "notInUseItems": [],
                    "cell_range_permission": "",
                }
            # Format to match expected DefinitionSerializer structure
            definition_data = {
                "id": None,
                "definition_id": batch_instance.definition_id,
                "vendor": batch_instance.vendor,
                "type": getattr(batch_instance, "doc_type", ""),
                "name_matching_text": "",
                "cw1": True,
                "created_at": timezone.now().isoformat(),
                "updated_at": timezone.now().isoformat(),
            }
            definition_data.update(version_data)

            definitions.append(definition_data)
    return definitions


def get_translation_codes_for_definitions(definition_ids):
    """
    Fetch Translation Codes from Database for given definition_ids
    """
    translation_codes = list(
        TranslationCode.objects.filter(definition_id__in=definition_ids).values(
            "id",
            "definition_id",
            "original_value",
            "translated_value",
            "type",
            "method",
        )
    )

    return translation_codes


def get_default_table_data(batch_type):
    """Returns Table field data with default values set in definition settings"""

    dafault_table_data = [
        {
            "table_id": 0,
            "table_name": "Main Table",
            "table_unique_id": str(uuid.uuid4()),
            "table_definition_data": {
                "columns": [],
                "keyItems": [],
                "models": {},
                "normalizerItems": [],
                "ruleItems": [],
            },
        }
    ]

    if batch_type == ".xlsx":
        return dafault_table_data

    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data
        model_fields = application_settings["tableSettings"]["model"]["fields"]

        model = {}
        for i in model_fields:
            key = i["key"]
            value = ""
            if "defaultValue" in i.keys():
                value = i["defaultValue"]
            model.update({key: value})

        dafault_table_data[0]["table_definition_data"]["models"] = model

        column_fields = application_settings["tableSettings"]["column"]["fields"]

        # Filter columns based on batch_type:
        if batch_type in [".pdf", ".docx"]:
            identifier = "pdf"
        column_fields = [i for i in column_fields if identifier in i["applicableFor"]]

        column = {}
        predefined = {
            "colLabel": "notInUse",
            "colName": "None",
            "startPos": "0",
            "endPos": "0",
        }

        for i in column_fields:
            key = i["key"]
            value = predefined.get(key, "")
            if value == "":
                if "defaultValue" in i.keys():
                    value = i["defaultValue"]
            column.update({key: value})

        dafault_table_data[0]["table_definition_data"]["columns"].append(column)

    return dafault_table_data


def process_ai_agent_response(response_json):
    try:
        print("✓ AI agent response received")
        transaction_id = response_json["transaction_id"]
        batch_id = response_json["batch_id"]
        message_type = response_json.get("message_type", "")
        active_agents = response_json.get("active_agents", [])
        status_code = response_json.get("status_code", {})

        if status_code.get("all") == 400:
            write_batch_log(
                batch_id=batch_id,
                status="failed",
                message="AI Agent did not send Response",
                action="display_json",
                remarks=json.dumps(response_json),
            )
            return
            

        if any(agent in ["hbl_mbl", "dynamic_content_creation", "shipment_table"] for agent in active_agents):
            combined_data_json = response_json.pop("combined_data_json", [])

            if not combined_data_json:
                write_batch_log(
                    batch_id=batch_id,
                    status="inprogress",
                    message="Processing AI Agent Response",
                    action="display_json",
                    remarks=json.dumps(combined_data_json),
                )

            for data_json in combined_data_json:
                current_batch_id = data_json.get("id")

                if not current_batch_id:
                    continue

                try:
                    write_batch_log(
                        batch_id=current_batch_id,
                        status="inprogress",
                        message="Processing AI Agent Response",
                        action="display_json",
                        remarks=json.dumps(data_json),
                    )

                    batch_instance = Batch.objects.get(id=current_batch_id)
                    batch_instance.data_json = data_json
                    batch_instance.save(update_fields=["data_json", "updated_at"])

                    # Update sub doc class
                    sub_doc_class_mapping = data_json.get("sub_doc_class_mapping", [])
                    for item in sub_doc_class_mapping:
                        file_path = item.get("file_path")
                        doc_code = item.get("doc_code")

                        if not file_path:
                            continue

                        file_name = os.path.basename(file_path)

                        parsed_document = EmailParsedDocument.objects.filter(
                            batch_id=current_batch_id, name=file_name
                        ).first()

                        if parsed_document:
                            parsed_document.doc_code = doc_code
                            parsed_document.save()
                except Batch.DoesNotExist as e:
                    print(f"Batch not found for id: {current_batch_id}. Error: {e}")

            # Initializing JSON output generation..
            test_batch_p6c(batch_id)
        
        elif "data_modification" in active_agents:
            test_batch_p8b(transaction_id, response_json)

        # Send AI agent messages
        ai_agent_message = response_json.get("message", {})
        ai_agent_sub_message = response_json.get("sub_message", {})
        ai_agent_color_code = response_json.get("color_code", {})

        for agent_name in active_agents:
            message = {
                "transaction_id": transaction_id,
                "batch_id": batch_id,
                "agent_name": convert_to_title(agent_name),
                "message": ai_agent_message.get(agent_name),
                "sub_message": ai_agent_sub_message.get(agent_name),
                "remarks": response_json.get("remarks", []),
                "color_code": ai_agent_color_code.get(agent_name),
                "error": response_json.get("error", ""),
            }

            ai_agent_message_instance = AiAgentConversation.objects.create(
                transaction_id=transaction_id,
                batch_id=batch_id,
                type=message_type,
                message=message,
            )

            serialize_message = AiAgentConversationSerializer(ai_agent_message_instance)

            async_to_sync(channel_layer.group_send)(
                f"ai_agent_response_{batch_id}",
                {"type": "ai_agent_response", "data": serialize_message.data},
            )
    except:
        print(traceback.print_exc())
        error = str(traceback.format_exc())

        write_failed_log(
            batch_id=batch_id,
            status="failed",
            message="Error Processing AI Agent Response",
            remarks=error,
        )


def process_atm_chunk_data(data, batch_id):
    """Takes atm_chunk_daat response object and
    returns a list of all chunk lines"""

    chunk_line_records = []

    for document_id, document in data["data"].items():
        for page in document.values():
            for line in page.values():
                pos = {
                    "leftPos": None,
                    "topPos": None,
                    "rightPos": None,
                    "bottomPos": None,
                    "pageId": None,
                    "documentId": document_id,
                    "batchId": batch_id,
                    "posRef": "",
                    "status": "blank",
                    "pattern": "",
                }

                for segment in line:
                    if not pos["pageId"]:
                        pos["pageId"] = segment[2].upper()

                    if pos["pattern"] == "":
                        pos["pattern"] = segment[0]
                    else:
                        pos["pattern"] = pos["pattern"] + " " + segment[0]

                    pos = generate_pos(segment, pos)

                    pos["posRef"] = "|".join(list(pos.values())[:7])

                    pos["pattern"] = pos["pattern"].replace(",", "*comma*")

                chunk_line_records.append(",".join(pos.values()))

    return chunk_line_records


def post_process_atm_data(data, digit_threshold, text_threshold, record_line):
    """Takes AutomatedTableModel response object and returns a object with
    atm_patterns & autoPatternRecords fields"""

    atm_patterns = []
    atm_pattern_records = []

    for pattern_info in data["pattern_info"]:
        all_pos = calculate_all_pos(pattern_info, data)

        item = {
            "pattern": pattern_info["pattern"],
            "openBlock": pattern_info["openBlock"],
            "confidenceScore": pattern_info["confidence_score"],
            "total_pattern_found": pattern_info["total_pattern_found"],
            "digit_threshold": digit_threshold,
            "text_threshold": text_threshold,
            "n": record_line,
            "pos": all_pos[0].split(","),
        }

        atm_patterns.append(item)

        atm_pattern_records = atm_pattern_records + all_pos

    return {"atm_patterns": atm_patterns, "atm_pattern_records": atm_pattern_records}


def calculate_all_pos(pattern_info, atm_patterns):
    """Calculates all positions for given chunk indexes"""

    all_pos = []
    pos_ref = ""

    for chunk_index in pattern_info["chunk_indexes"]:
        hashed_chunk_index = {}

        for item in chunk_index:
            _, __, document_id, page_id, *tail = item.values()

            hashed_chunk_index.setdefault(f"{document_id}_{page_id}", [])

            hashed_chunk_index[f"{document_id}_{page_id}"].append(item)

        for hashed_item in hashed_chunk_index:
            pos = {
                "leftPos": None,
                "topPos": None,
                "rightPos": None,
                "bottomPos": None,
                "pageId": None,
                "documentId": None,
                "batchId": None,
                "posRef": pos_ref,
                "status": pattern_info.get("status", "blank"),
                "refStatus": pattern_info.get("status", "blank"),
            }

            for item in hashed_chunk_index[hashed_item]:
                _, batch_id, document_id, page_id, line_id, *tail = item.values()

                pos_array = atm_patterns[batch_id][document_id]["chunking_data"][
                    page_id
                ][line_id]

                pos["batchId"] = batch_id
                pos["pageId"] = pos_array[0][2].upper()
                pos["documentId"] = document_id

                for i in pos_array:
                    pos = generate_pos(i, pos)

            if not len(all_pos):
                pos_ref = "|".join(list(pos.values())[:7])
                pos["posRef"] = pos_ref

            all_pos.append(",".join(pos.values()))

    return all_pos


def generate_pos(item, pos):
    """Generates position for given item"""

    left_pos, top_pos, right_pos, bottom_pos, *tail = pos.values()

    left, top, right, bottom, *tail = item[1].split(",")

    if not left_pos or int(left_pos) > int(left):
        left_pos = left

    if not top_pos or int(top_pos) > int(top):
        top_pos = top

    if not right_pos or int(right_pos) < int(right):
        right_pos = right

    if not bottom_pos or int(bottom_pos) < int(bottom):
        bottom_pos = bottom

    return {
        **pos,
        "leftPos": left_pos,
        "topPos": top_pos,
        "rightPos": right_pos,
        "bottomPos": bottom_pos,
    }


####
# Pipeline API Endpoints
####


def handle_pre_upload_log(batch_id, message, remarks):
    """Handle batch creation and write batch log"""
    batch_upload_mode = "uploading"

    # Create the batch only if it doesn't exist
    Batch.objects.get_or_create(
        id=batch_id, defaults={"mode": batch_upload_mode, "visible": False}
    )

    write_batch_log(
        batch_id=batch_id,
        status="inprogress",
        message=message,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def pre_upload_batch_status(request):
    """Check pre-upload batch status"""
    batch_id = request.query_params.get("batch_id")
    message = request.query_params.get("message") or ""
    remarks = request.query_params.get("remarks") or ""

    if not batch_id or not message:
        return Response(
            {"detail": "invalid payload (batch_id, message)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    handle_pre_upload_log(batch_id, message, remarks)

    return Response({"detail": "Batch Status Updated"})


def upload_batch_process(
    batch_id, batch_upload_mode, sub_path, re_process=False, template=None
):
    """Wrapper function to upload_batch in system"""

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json

        if re_process:
            write_batch_log(
                batch_id=batch_id,
                status="upload",
                message="Re-uploading existing Batch",
            )
        else:
            write_batch_log(
                batch_id=batch_id, status="upload", message="Uploading New Batch"
            )

        excluded_keys = ["nodes", "id", "bvFilePath", "bvSelectedDocTypes"]
        bv_info = {k: ra_json[k] for k in ra_json.keys() if k not in excluded_keys}
        bv_info = json.dumps(bv_info)

        write_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Batch Variables",
            remarks=bv_info,
            action="display_key_values",
        )

        # Get Batch Level Properties
        definition_id = ra_json.get("DefinitionID")
        doc_type = ra_json.get("DocumentType")
        batch_vendor = ra_json.get("Vendor")
        batch_type = ra_json.get(
            "batch_type", ".pdf"
        )  # .pdf is fallback type for old batches
        project = ra_json.get("Project")
        name_matching_text = ra_json.get("NameMatchingText")

        if project is None:
            raise ValueError("Project Name can not be empty.")

        if definition_id:
            batch_instance.definition_id = definition_id

        if batch_vendor:
            batch_instance.vendor = batch_vendor

        if doc_type:
            batch_instance.type = doc_type

        if name_matching_text:
            batch_instance.name_matching_text = name_matching_text

        batch_instance.project = project
        batch_instance.extension = batch_type

        # If it’s a linked batch of a training batch, update the file extension accordingly
        train_to_batch_link_qs = TrainToBatchLink.objects.filter(batch_id=batch_id)

        if train_to_batch_link_qs.exists() and batch_type:
            train_to_batch_link_instance = train_to_batch_link_qs.first()

            if train_to_batch_link_instance:
                train_batch = train_to_batch_link_instance.train_batch
                train_batch.file_ext_list.append(batch_type)
                train_batch.file_ext_list = list(set(train_batch.file_ext_list))
                train_batch.save()

        write_batch_log(
            batch_id=batch_id, status="inprogress", message="Generating Data JSON"
        )
        data_json = DataJson(ra_json).process()
        batch_instance.data_json = data_json
        batch_instance.visible = True
        batch_instance.save()

        write_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Batch added to queue for processing",
        )

        # Add task in queue
        if re_process:
            new_upload = False
        else:
            new_upload = True

        request_data = {
            "batch_id": batch_id,
            "new_upload": new_upload,
            "template": template,
        }

        publish("batch_queued", "to_pipeline", request_data)
    except ValueError as error:
        error_args = error.args
        checkbox_error_message = "Checkbox should have exactly one value checked"
        if error_args[0] == checkbox_error_message:
            raise ValueError(checkbox_error_message)
        raise ValueError(
            f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}."
        )
    except Exception as error:
        raise ValueError(
            f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}."
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def classify_batch(request):
    """
    Processes a batch classification request.

    This view expects a POST request with the following parameter:

    - `batch_id`: An unique identifier for batch.
    """
    try:
        batch_id = request.query_params.get("batch_id")

        print(f"Request received for classifying batch... {batch_id=}")

        if batch_id is None:
            print("400 RESPONSE WILL BE SENT as batch_id is not valid")
            raise ValueError("invalid batch_id")

        sub_path = request.query_params.get("sub_path", "")
        print(f"{sub_path=}")

        try:
            batch_path = _safe_join(BATCH_INPUT_PATH, sub_path, batch_id)
        except ValueError:
            return Response(
                {"detail": "Invalid sub_path"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        print(f"{batch_path=}")

        if not os.path.exists(batch_path):
            print("400 RESPONSE WILL BE SENT as system can not read batch_path")
            raise ValueError(f"Batch not found at path {batch_path}")

        request_data = {
            "batch_id": batch_id,
            "batch_path": batch_path,
            "sub_path": sub_path,
        }

        _, __, parent_batch, *tail = get_instance_classes(batch_id)

        if parent_batch:
            # Stop repeated message due to datacap batch recreate
            timeline_data = BatchStatus.objects.filter(
                batch_id=parent_batch.id
            ).order_by("-event_time")[:1]

            if timeline_data.exists():
                latest_status = timeline_data.first()
                # If the message changed from other places it may not work
                previous_message = (
                    "Awaiting Datacap API Callback to Initiate Classification Process"
                )

                if latest_status.message == previous_message:
                    save_analyzer_log_time(
                        batch_id=parent_batch.id,
                        field_name="classification_process_queued_time",
                    )
                    write_parent_batch_log(
                        batch_id=parent_batch.id,
                        status="inprogress",
                        message="Classification Process Queued",
                    )
        publish("pre_classification_process_queued", "to_pipeline", request_data)
        print(f"added to pre_classification_process_queued {batch_id=}")

        return Response(
            {
                "detail": "Batch added to queue for classification",
            }
        )
    except Exception as error:
        print(traceback.print_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def pre_classification_process_p1(request_data):
    """
    Pre-classifies a Datacap batch to generate ra_json.
    """

    try:
        print("Classify batch process...")

        batch_id = request_data["batch_id"]
        print(f"{batch_id=}")
        # gets eitehr training or email batch instance using the batch ID
        _, instanceParsedDocument, parent_batch, parent_batch_kwarg, *tail = (
            get_instance_classes(batch_id)
        )

        batch_path = request_data["batch_path"]
        sub_path = request_data["sub_path"]

        info_holder_data, valid_page_types = get_info_holder_for_batch(
            "/".join(batch_path.split("/")[:-1]), batch_id
        )

        layout_file_name = info_holder_data["name"]

        print(f"{layout_file_name=}")

        copy_batches_xml_path = os.path.join(batch_path, layout_file_name)

        if not os.path.exists(copy_batches_xml_path):
            print(
                "400 RESPONSE WILL BE SENT as system can not read Copy Batch XML file"
            )
            raise ValueError(
                f"Copy Batch XML file not found at path {copy_batches_xml_path}"
            )

        organize_docs_inside_copy_batches_xml(copy_batches_xml_path)

        (
            root_status,
            profile_name,
            batch_upload_mode,
            file_paths,
        ) = get_info_from_copy_batches_xml(copy_batches_xml_path)

        print(f"{batch_upload_mode=}")

        if root_status:
            handle_template_batch_upload(
                profile_name, batch_id, batch_upload_mode, sub_path
            )

            return

        if not parent_batch:
            print("400 RESPONSE WILL BE SENT as system can not find parent_batch")
            raise ValueError(f"Parent Batch not found for this '{batch_id}' batch")

        if profile_name == "None":
            print("400 RESPONSE WILL BE SENT as profile name not found in XML")
            raise ValueError("Profile name not found in XML")

        batch_instance = Batch.objects.get(id=batch_id)

        # Generate RAJson
        OrganizeFiles(
            batch_id, "/".join(batch_path.split("/")[:-1]), batch_instance
        ).process()
        excel_read_only = is_excel_read_only(batch_id)
        ra_json = RAJson(
            batch_id,
            "/".join(batch_path.split("/")[:-1]),
            info_holder_data,
            valid_page_types,
            excel_read_only,
        ).process()

        ra_json = add_file_path_to_ra_json(ra_json, file_paths)

        batch_instance.ra_json = ra_json
        batch_instance.sub_path = sub_path
        batch_instance.save()

        if ra_json.get("DocumentType") and ra_json["DocumentType"] != "None":
            pre_classification_process_p2(batch_id)
            return

        if batch_upload_mode == "training":
            selected_doc_types = parent_batch.selected_doc_types
        else:
            selected_doc_types = []

        job_id = gerenate_job_id_for_batch(batch_id)

        job_details = {
            "job_id": job_id,
            "profile_name": profile_name,
            "parent_batch_id": parent_batch.id,
            "batch_id": batch_instance.id,
            "batch_path": batch_path,
            "sub_path": sub_path,
            "selected_doc_types": selected_doc_types,
            "batch_upload_mode": batch_upload_mode,
        }

        # Save job_details to Redis
        redis_instance.set(job_id, json.dumps(job_details))

        matched_profile = Profile.objects.get(name=profile_name)
        _, profile_documents = get_profile_doc_info(matched_profile)

        if len(profile_documents.get("auto_match", [])):
            _, file_identifiers, *tail = get_doc_info(parent_batch, batch_instance)
            publish_to_classifier(
                write_parent_batch_log,
                job_id,
                parent_batch,
                batch_instance,
                matched_profile,
                file_identifiers,
                batch_upload_mode,
                message_type="ocr_mismatch",
            )
            return
        request_data = {"job_id": job_id}
        handle_ocr_mismatch(request_data)
    except ValueError as ve:
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch pre-classification"

        ve_message = str(ve)
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": "AIDB-105",
            }
        try:
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                remarks=json.dumps(remarks, indent=4),
                action="display_error",
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch pre-classification"

        try:
            test_batch_cleanup(job_id)
            remarks = {
                "message": f"AIDB-105: The following error occured -'{str(error.args[0])}' ",
                "traceback": trace,
                "code": "AIDB-105",
            }
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass


def pre_classification_process_p2(batch_id):
    """
    Pre-classifies a Datacap batch to generate ra_json.
    """

    try:
        _, instanceParsedDocument, parent_batch, parent_batch_kwarg, *tail = (
            get_instance_classes(batch_id)
        )

        # Update parsed documents
        instanceParsedDocument.objects.filter(batch_id=batch_id).update(
            ra_json_created=True
        )

        pd_qs = instanceParsedDocument.objects.filter(**parent_batch_kwarg)

        if pd_qs.exclude(ra_json_created=True).exists():
            return

        request_data = {
            "batch_id": batch_id,
        }

        publish("classify_batch_queued", "to_pipeline", request_data)
    except ValueError as ve:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch pre-classification"

        ve_message = str(ve)
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": "AIDB-105",
            }
        try:
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                remarks=json.dumps(remarks, indent=4),
                action="display_error",
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch pre-classification"

        try:
            remarks = {
                "message": f"AIDB-105: The following error occured -'{str(error.args[0])}' ",
                "traceback": trace,
                "code": "AIDB-105",
            }
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass


def process_classify_batch_p1(request_data):
    try:
        batch_id = request_data["batch_id"]

        (
            instanceToBatchLink,
            instanceParsedDocument,
            parent_batch,
            parent_batch_kwarg,
            _,
            batch_upload_mode,
        ) = get_instance_classes(batch_id)

        pd_qs = instanceParsedDocument.objects.filter(**parent_batch_kwarg)

        if pd_qs.exclude(ra_json_created=True).exists():
            return

        save_analyzer_log_time(
            batch_id=parent_batch.id, field_name="classification_process_s"
        )
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Classification process initiated",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        # Find matched profile
        try:
            matched_profile = Profile.objects.get(
                name=parent_batch.matched_profile_name
            )
        except:
            print("400 RESPONSE WILL BE SENT as no matching profile found")
            raise ValueError(
                "Batch classification aborted as no matching profile found"
            )
        # loops through every document and removes null character from doc_type
        for document in matched_profile.documents.all():
            document.doc_type = remove_null_characters(document.doc_type, "")
            document.save()

        save_analyzer_log_time(
            batch_id=parent_batch.id, field_name="document_matching_s"
        )
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Document matching initiated",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        merged_batch, linked_batches_to_delete = get_merged_batch(
            write_parent_batch_log, get_new_batch_id, batch_id
        )

        # Reorders documents in the ra_json to ensure email body documents appear at the end
        merged_batch = update_ra_json_doc_order(merged_batch)

        # Delete all linked batches
        instanceToBatchLink.objects.filter(
            **parent_batch_kwarg, batch_id__in=linked_batches_to_delete
        ).exclude(mode="supporting").delete()

        instanceToBatchLink.objects.create(
            **parent_batch_kwarg,
            batch_id=merged_batch.id,
            classified=True,
            mode=batch_upload_mode,
        )

        pd_qs = instanceParsedDocument.objects.filter(
            **parent_batch_kwarg, batch_id__in=linked_batches_to_delete
        )

        # Update parsed documents batch id
        for pd_instance in pd_qs:
            if not pd_instance.batch_id:
                continue
            pd_instance.batch_id = merged_batch.id
            pd_instance.save()

        job_id = gerenate_job_id_for_batch(merged_batch.id)

        # Retrieve Selected Doc Ids
        selected_doc_ids = (
            parent_batch.selected_doc_ids if batch_upload_mode == "training" else []
        )
        if selected_doc_ids:
            selected_doc_types = list(
                ProfileDocument.objects.filter(id__in=selected_doc_ids).values_list(
                    "doc_type", flat=True
                )
            )
        else:
            selected_doc_types = []

        batch_path = os.path.join(
            BATCH_INPUT_PATH, merged_batch.sub_path, merged_batch.id
        )

        job_info = {
            "batch_id": merged_batch.id,
            "batch_path": batch_path,
            "sub_path": merged_batch.sub_path,
            "matched_profile": matched_profile.to_dict(),
            "batch_upload_mode": batch_upload_mode,
            "document_type": merged_batch.ra_json.get("DocumentType"),
            "selected_doc_types": selected_doc_types,
        }

        redis_instance.set(job_id, json.dumps(job_info))

        document_matching_p1(
            write_parent_batch_log,
            job_id,
            parent_batch,
            matched_profile,
            merged_batch,
            batch_upload_mode,
            selected_doc_types,
        )
    except ValueError as ve:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch classification"

        ve_message = str(ve)
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {
                "message": f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}.",
                "traceback": trace,
                "code": "AIDB-105",
            }
        try:
            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                remarks=json.dumps(remarks, indent=4),
                action="display_error",
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch classification"

        try:
            test_batch_cleanup(job_id)
            remarks = {
                "message": f"AIDB-105: The following error occured -'{str(error.args[0])}' ",
                "traceback": trace,
                "code": "AIDB-105",
            }
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass


def process_classify_batch_p2(request_data):
    """
    Classifies a batch, recreates batches if needed, and uploads batches.
    """

    try:
        print(f"{request_data=}")
        job_id = request_data["job_id"]

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]
        batch_path = job_info["batch_path"]
        sub_path = job_info["sub_path"]
        matched_profile = Profile.from_dict(job_info["matched_profile"])
        batch_upload_mode = job_info["batch_upload_mode"]
        document_type = job_info["document_type"]
        matched_doc = job_info.get("matched_doc")
        doc_info = job_info.get("doc_info")

        matched_doc = load_doc_instance_from_dict(matched_doc)
        upload_batch = True

        # Clean up Redis data as it's no longer needed
        try:
            redis_instance.delete(job_id)
        except Exception as e:
            print(f"Error deleting Redis key {job_id}: {str(e)}")

        instanceToBatchLink, _, parent_batch, *tail = get_instance_classes(batch_id)

        if matched_doc:
            # Handle multiple matching doc_types
            if len(matched_doc) > 1:
                handle_multiple_matching_doc_types(
                    write_parent_batch_log,
                    upload_batch_process,
                    matched_profile,
                    matched_doc,
                    doc_info,
                    batch_path,
                    sub_path,
                    batch_id,
                    batch_upload_mode,
                )
            elif matched_doc[0]["matched_doc"]:
                upload_batch = handle_single_matching_doc_type(
                    batch_id,
                    matched_profile,
                    matched_doc[0]["matched_doc"],
                    doc_info,
                    batch_upload_mode,
                )

        post_classification_process(
            write_parent_batch_log,
            parent_batch,
            batch_upload_mode,
            matched_profile,
        )

        # Calling batch upload API
        if not upload_batch:
            return
        instanceToBatchLink.objects.filter(batch_id=batch_id).update(uploaded=True)
        save_analyzer_log_time(
            batch_id=parent_batch.id, field_name="upload_batch_process_time"
        )
        print(f"{batch_id}: upload_batch_process called")
        upload_batch_process(batch_id, batch_upload_mode, sub_path)
    except ValueError as ve:
        message = "Error occured during Batch classification"
        ve_message = str(ve)
        trace = traceback.format_exc()
        # added error code directly to args because I don't know the error could be raised.
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"{code['code']}: {ve.args[1]}",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {"message": ve.args[0], "traceback": trace, "code": "AIDB-105"}
        try:
            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True if batch_upload_mode == "training" else False,
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        message = "Error occured during Batch classification"

        try:
            test_batch_cleanup(job_id)
            remarks = {
                "message": f"AIDB-105: The following error occured - '{str(error.args[0])}' ",
                "traceback": trace,
                "code": "AIDB-105",
            }
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
            )

            if batch_upload_mode == "processing":
                send_failure_notification(parent_batch.id, remarks["message"])
        except:
            pass


def handle_template_batch_upload(template_name, batch_id, batch_upload_mode, sub_path):
    status = "failed"
    message = f"Batch upload failed ({batch_id})"
    remarks = {}

    try:
        print(f"{batch_id}: upload_batch_process called")
        batch_instance = Batch.objects.create(
            id=batch_id, mode=batch_upload_mode, visible=False
        )

        batch_path = os.path.join(BATCH_INPUT_PATH, sub_path)
        excel_read_only = is_excel_read_only(batch_id)
        info_holder_data, valid_page_types = get_info_holder_for_batch(
            batch_path, batch_id
        )

        # Generate RAJson
        OrganizeFiles(batch_id, batch_path, batch_instance).process()

        ra_json = RAJson(
            batch_id,
            batch_path,
            info_holder_data,
            valid_page_types,
            excel_read_only,
        ).process()

        batch_instance.ra_json = ra_json
        batch_instance.save()

        upload_batch_process(
            batch_id, batch_upload_mode, sub_path, template=template_name
        )

        status = "completed"
        message = "Batch uploaded successfully"
        remarks = {"batch_id": batch_id}
    except ValueError as ve:
        trace = traceback.format_exc()
        print(trace)
        remarks = {"message": ve.args[0], "traceback": trace}
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        remarks = {
            "message": f"The following error occured in 'handle_template_batch_upload' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }

    template = Template.objects.filter(template_name=template_name).first()

    if template:
        action = "display_key_values" if status == "completed" else "display_error"
        write_timeline_log(
            timeline_id=template.template_name,
            status=status,
            message=message,
            action=action,
            remarks=json.dumps(remarks, indent=4),
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_batch(request):
    """
    Upload a batch to Batches for processing or training but default upload mode is processing
    """
    print("Request received for uploading batch...")

    batch_id = request.query_params.get("batch_id")
    print(f"{batch_id=}")
    if batch_id is None:
        print("400 RESPONSE WILL BE SENT as batch_id is not valid")
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    sub_path = request.query_params.get("sub_path", "")
    print(f"{sub_path=}")
    batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, batch_id)
    print(f"{batch_path=}")

    if not os.path.exists(batch_path):
        print("400 RESPONSE WILL BE SENT as system can not read batch_path")
        return Response(
            {"detail": f"Batch not found at path {batch_path}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # default upload mode is processing (production)
    batch_upload_mode = "processing"

    mode = request.query_params.get("mode")
    print(f"{mode=}")
    if mode:
        if mode in BATCH_UPLOAD_MODES:
            batch_upload_mode = mode
        else:
            print("400 RESPONSE WILL BE SENT as mode is not correct")
            return Response(
                {
                    "detail": f"invalid mode. it should be one of the following: {BATCH_UPLOAD_MODES} "
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        upload_batch_process(batch_id, batch_upload_mode, sub_path)
    except Exception as error:
        try:
            write_batch_log(
                batch_id=batch_id,
                status="failed",
                message="Batch upload failed",
                remarks=str(error),
            )
        except:
            pass
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    print("Batch uploaded successfully and queued for processing")
    return Response({"detail": "Batch uploaded successfully and queued for processing"})


@api_view(["POST"])
def process_batch(request):
    """
    Start processing a batch with necessary data
    """
    batch_id = request.query_params.get("batch_id")
    document_id = request.query_params.get("document_id")
    batch_ids_list = request.query_params.get("batch_ids", [])
    table_unique_id = request.query_params.get("table_unique_id")
    template = request.query_params.get("template")
    skip_post_processor = request.query_params.get("skip_post_processor", "")
    skip_post_processor = True if skip_post_processor == "true" else False
    skip_table_processing = request.query_params.get("skip_table_processing", "")
    skip_table_processing = True if skip_table_processing == "true" else False
    skip_key_processing = request.query_params.get("skip_key_processing", "")
    skip_key_processing = True if skip_key_processing == "true" else False

    definition_version = request.query_params.get(
        "definition_version", settings.DEFAULT_DEFINITION_VERSION
    )
    if batch_ids_list:
        batch_ids_list = json.loads(batch_ids_list)
    # Parse batch_ids - support both single batch_id and comma-separated batch_ids
    if not batch_ids_list:
        batch_ids_list = [batch_id]

    if not batch_ids_list:
        return Response(
            {"detail": "invalid batch_id or batch_ids"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    processed_batches = []

    try:
        for current_batch_id in batch_ids_list:
            try:
                batch_status = Batch.objects.get(id=current_batch_id).status
                batch_running = batch_status not in ["", "failed", "completed"]
            except Batch.DoesNotExist:
                processed_batches.append(
                    {
                        "batch_id": current_batch_id,
                        "status": "error",
                        "message": "Batch not found",
                    }
                )
                continue

            if batch_running:
                processed_batches.append(
                    {
                        "batch_id": current_batch_id,
                        "status": "skipped",
                        "message": "Batch execution already in progress",
                    }
                )
                continue

            write_batch_log(
                batch_id=current_batch_id,
                status="retest",
                message="Request Received for Processing Batch: {}".format(
                    current_batch_id
                ),
            )

            write_batch_log(
                batch_id=current_batch_id,
                status="queued",
                message="Batch added to queue for processing: {}".format(
                    current_batch_id
                ),
            )

            request_data = {
                "batch_id": current_batch_id,
                "document_id": document_id,
                "batch_ids": batch_ids_list,
                "table_unique_id": table_unique_id,
                "definition_version": definition_version,
                "skip_post_processor": skip_post_processor,
                "skip_table_processing": skip_table_processing,
                "skip_key_processing": skip_key_processing,
                "template": template,
            }

            publish("batch_queued", "to_pipeline", request_data)
            processed_batches.append({"batch_id": current_batch_id, "status": "queued"})
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if document_id:
        return Response({"detail": "Document added to the processing queue."})
    elif len(processed_batches) == 1:
        return Response({"detail": "Sub-batch added to the processing queue."})
    else:
        return Response(
            {
                "detail": f"Successfully added {len(processed_batches)} sub-batches to the queue",
                "processed_batches": processed_batches,
            }
        )


@api_view(["POST"])
def process_atm_data(request):
    """
    Takes definition_id, definition_type, batch_id, table_unique_id, user_selected_patterns, extended_user_selected_patterns, multiple_line_record, user_selected_ob, record_line, digit_threshold & text_threshold  as arguments
    and process atm_data for all the documents of the batch.
    """

    request_data = request.data

    try:
        definition_id = request_data["definition_id"]
        definition_type = request_data["definition_type"]
        name_matching_text = request_data["name_matching_text"]
        batch_id = request_data["batch_id"]
        table_unique_id = request_data["table_unique_id"]
        user_selected_patterns = request_data["user_selected_patterns"]
        extended_user_selected_patterns = request_data[
            "extended_user_selected_patterns"
        ]
        multiple_line_record = request_data["multiple_line_record"]
        user_selected_ob = request_data["user_selected_ob"]
        record_line = request_data["record_line"]
        digit_threshold = request_data["digit_threshold"]
        text_threshold = request_data["text_threshold"]

        definition_version = request_data.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )

    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'definition_id', 'definition_type', 'name_matching_text', 'batch_id', 'record_line', 'digit_threshold', 'text_threshold', 'user_selected_patterns, extended_user_selected_patterns, multiple_line_record, and user_selected_ob'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    write_batch_log(
        batch_id=batch_id,
        status="retest",
        message="Request received for processing Automated Table Model",
    )

    write_batch_log(
        batch_id=batch_id,
        status="queued",
        message="Batch added to queue for processing Automated Table Model",
    )

    try:
        request_data = {
            "definition_id": definition_id,
            "definition_type": definition_type,
            "name_matching_text": name_matching_text,
            "batch_id": batch_id,
            "table_unique_id": table_unique_id,
            "user_selected_patterns": user_selected_patterns,
            "extended_user_selected_patterns": extended_user_selected_patterns,
            "multiple_line_record": multiple_line_record,
            "user_selected_ob": user_selected_ob,
            "definition_version": definition_version,
            "record_line": record_line,
            "digit_threshold": digit_threshold,
            "text_threshold": text_threshold,
        }

        publish("atm_process_queue", "to_pipeline", request_data)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"detail": "Request queued for processing"})


def upload_email_batch_process(
    batch_id, batch_path, profile_name, upload_type, re_process=False
):
    """
    Transaction uploading process
    """
    save_analyzer_log_time(batch_id=batch_id, field_name="transaction_uploading_s")
    if re_process:
        email_batch = EmailBatch.objects.get(id=batch_id)
        force_ocr_engine = email_batch.force_ocr_engine
        shipment_status_url = email_batch.shipment_status_url
        profile_name = email_batch.matched_profile_name
        api_response = None

        try:
            matched_profile = Profile.objects.get(name=profile_name)
            if matched_profile.multi_shipment:
                api_response = email_batch.api_response
        except:
            profile_name = ""

        email_batch.delete()

    # Create Email Batch (Transaction)
    try:
        email_batch = EmailBatch.objects.create(id=batch_id)
        email_batch.email_from = "Manual Upload"
        email_batch.email_subject = "Manual Upload"
        email_batch.save()
        if re_process:
            # Retain shipment_status_url to prevent multiple shipment creations
            email_batch.force_ocr_engine = force_ocr_engine
            email_batch.shipment_status_url = shipment_status_url
            if api_response:
                email_batch.api_response = api_response

            email_batch.save()
    except IntegrityError:
        return Response(
            {"detail": "Transaction with provided ID already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if re_process:
        write_parent_batch_log(
            batch_id=batch_id,
            status="upload",
            message="Re-uploading Existing Transaction",
        )
    else:
        write_parent_batch_log(
            batch_id=batch_id,
            status="upload",
            message="Uploading new Transaction",
        )

    request_data = {
        "batch_id": batch_id,
        "batch_path": batch_path,
        "profile_name": profile_name,
        "upload_type": upload_type,
    }

    publish("email_batch_queued", "to_pipeline", request_data)
    save_analyzer_log_time(batch_id=batch_id, field_name="time_to_queued")
    write_parent_batch_log(
        batch_id=batch_id,
        status="queued",
        message="Transaction Added to Queue for Processing",
    )
    save_analyzer_log_time(batch_id=batch_id, field_name="transaction_uploading_e")


def get_email_file_name_from_batch_path(batch_path):
    """return email file name from batch path"""
    files = os.listdir(batch_path)
    files = [
        i for i in files if i.lower().endswith(".eml") or i.lower().endswith(".msg")
    ]
    try:
        email_file_name = files[0]
    except:
        raise ValueError("Email File not found in email batch (Transaction) folder")

    return email_file_name


def get_path_for_parent_batch(parent_batch_id, sub_path):
    """Return parent batch path"""
    batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, parent_batch_id)
    return batch_path


def prepare_extraction_path(email_batch_path, email_file_name=None):
    """prepare extraction output path"""
    output_path = os.path.join(email_batch_path, "extraction")

    if email_file_name:
        filename, extension = os.path.splitext(email_file_name)
        output_path = os.path.join(output_path, filename)

    # Remove and create folder again if exists
    if os.path.exists(output_path):
        shutil.rmtree(output_path)
    os.makedirs(output_path)

    return output_path


def ignore_dense_pages_p1(
    job_id, attachments_folder, batch_id=None, train_batch_log=False
):
    """
    Handle to ignore dense pages from pdf document
    """
    try:
        images_path = os.path.join(attachments_folder, "images")
        attachments = os.listdir(attachments_folder)
        image_dir_paths = []
        pdf_file_paths = []

        for file in attachments:
            file_base_name = os.path.basename(file)
            [file_name, file_extension] = os.path.splitext(file_base_name)

            if file_extension != ".pdf":
                continue

            images_dir_path = os.path.join(images_path, file_name)

            file_path = os.path.join(attachments_folder, file)

            extract_pages_from_pdf(file_path, images_dir_path)

            image_dir_paths.append(images_dir_path)
            pdf_file_paths.append(file_path)

        if not pdf_file_paths:
            return False

        # Publish message to preprocess queue
        payload = {
            "job_id": job_id,
            "attachments_folder": attachments_folder,
            "batch_id": batch_id,
            "train_batch_log": train_batch_log,
            "image_dir_paths": image_dir_paths,
        }

        try:
            publish("ignore_dense_pages", "to_preprocess", payload)
            print(f"Ignore Dense Pages message published for batch_id: {batch_id}")

            write_parent_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Dense Page Detection Queued",
                remarks=json.dumps(payload),
                action="display_json",
                train_batch_log=train_batch_log,
            )
        except Exception as e:
            print(
                f"Ignore Dense Pages message publishing error for batch_id: {batch_id}: {str(e)}"
            )
            remarks = {
                "error": str(e),
                "payload": payload,
            }
            write_parent_batch_log(
                batch_id=batch_id,
                status="failed",
                message="Dense Page Detection Failed",
                remarks=json.dumps(remarks),
                action="display_json",
                train_batch_log=train_batch_log,
            )

        return True
    except Exception:
        print(traceback.format_exc())
        return False


def ignore_dense_pages_p2(response_json):
    """
    Handle to ignore dense pages from pdf document
    """
    try:
        batch_id = response_json.get("batch_id")
        status_code = response_json.get("status_code")
        train_batch_log = response_json.get("train_batch_log")

        if status_code != 200:
            job_id = response_json.get("job_id")
            if job_id:
                test_batch_cleanup(job_id)
            if batch_id:
                write_parent_batch_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Dense Page Detection Failed",
                    remarks=json.dumps(response_json),
                    action="display_json",
                    train_batch_log=train_batch_log,
                )
            print(
                f"Ignore Dense Page Detection failed with status {status_code} for batch_id: {batch_id}"
            )
            return

        write_parent_batch_log(
            batch_id=batch_id,
            status="inprogress",
            message="Dense Page Detection Completed",
            remarks=json.dumps(response_json),
            action="display_json",
            train_batch_log=train_batch_log,
        )

        job_id = response_json["job_id"]
        attachments_folder = response_json["attachments_folder"]
        is_training_batch = True if train_batch_log else False

        # Normalize response_json to generate dense pages dict
        pages_to_remove_dict = {}

        for key, value in response_json["dense_pages_list"].items():
            file_base_name = key.split("/")[-1]
            page_num = file_base_name.split(".")[0]
            image_dir_path = key.split(file_base_name)[0]
            image_dir_name = image_dir_path.split("/")[-2]

            if image_dir_name not in pages_to_remove_dict:
                pages_to_remove_dict[image_dir_name] = []

            if value is not None:
                pages_to_remove_dict[image_dir_name].append(int(page_num))

        # Remove dense pages from pdf(s)
        details = []

        for image_dir_name, pages_to_remove in pages_to_remove_dict.items():
            if not pages_to_remove:
                continue

            pdf_file_path = os.path.join(attachments_folder, f"{image_dir_name}.pdf")

            remove_pages_from_pdf(pdf_file_path, pdf_file_path, pages_to_remove)

            pages_to_remove = [i + 1 for i in pages_to_remove]

            details.append(
                {
                    "file_path": pdf_file_path,
                    "page_numbers_to_remove": pages_to_remove,
                }
            )

        if batch_id and details:
            write_parent_batch_log(
                batch_id=batch_id,
                status="inprogress",
                message="Dense Page(s) Removed",
                remarks=json.dumps(details),
                action="display_json",
                train_batch_log=train_batch_log,
            )

        if os.path.exists(attachments_folder):
            images_path = os.path.join(attachments_folder, "images")
            if os.path.exists(images_path):
                shutil.rmtree(images_path)

        request_data = {"job_id": job_id}
        if is_training_batch:
            publish("process_train_batch_p2_queued", "to_pipeline", request_data)
        else:
            publish("process_email_batch_p2_queued", "to_pipeline", request_data)
    except Exception:
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        print(traceback.format_exc())


def extract_pages_from_pdf(pdf_path, output_folder):
    """
    Save all pdf pages separate image file
    """
    # Constants
    dpi = 400

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Scale factor: 72 dpi is default in PyMuPDF
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    # Loop through each page
    for page_num, page in enumerate(pdf_document, start=0):
        pix = page.get_pixmap(matrix=mat)  # Render page to an image

        # Define the image file name
        image_filename = f"{output_folder}/{page_num}.png"

        # Save the image
        pix.save(image_filename)


def remove_pages_from_pdf(input_pdf_path, output_pdf_path, pages_to_remove):
    """
    Remove specific pages from pdf
    """
    # Open the original PDF file
    with open(input_pdf_path, "rb") as input_pdf_file:
        reader = PyPDF2.PdfReader(input_pdf_file)
        writer = PyPDF2.PdfWriter()

        pages_added = 0

        for page_num in range(len(reader.pages)):
            if page_num not in pages_to_remove:
                page = reader.pages[page_num]
                writer.add_page(page)
                pages_added += 1

        if pages_added > 0:
            with open(output_pdf_path, "wb") as output_pdf_file:
                writer.write(output_pdf_file)
        else:
            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)
            print("No pages left to write. Output PDF not created.")


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_email_batch(request):
    """
    Upload email batch in transactionn
    set new batch ID and prepare batch path for it
    """
    try:
        print("Request received for uploading file in transaction...")

        files = request.FILES.getlist("files")
        upload_type = request.POST.get("file_type")
        profile_name = request.POST.get("profile_name")
        assert upload_type.lower() in [
            "email",
            "pdf",
            "excel",
            "word",
        ], "Invalid Upload type"

        if not files and not upload_type:
            print("400 RESPONSE WILL BE SENT as file and upload_type is not valid")
            return Response(
                {"detail": "invalid files"}, status=status.HTTP_400_BAD_REQUEST
            )

        if upload_type == "email" and len(files) > 1:
            return Response(
                {"detail": "More than one email file found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch_id = get_new_email_batch_id()
        batch_path = prepare_parent_batch_path(batch_id)
        save_analyzer_log_time(batch_id=batch_id, field_name="transaction_process_s")

        for index, file in enumerate(files):
            if index != 0 and upload_type == "email":
                break

            file_name = file.name
            file_name = remove_null_characters(file_name)
            file_base_name, extension = os.path.splitext(file_name)

            if upload_type == "email":
                file_name = f"email_file{extension}"

            file_path = os.path.join(batch_path, file_name)

            # save file to disk
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            if extension.lower() == "xls":
                # Convert xls file to xlsx
                if validate_xls_file(file_path):
                    xlsx_filename = file_base_name + ".xlsx"
                    xlsx_filepath = os.path.join(batch_path, xlsx_filename)

                    convert_xls_to_xlsx(file_path, xlsx_filepath)

                    if os.path.exists(file_path):
                        os.remove(file_path)
                else:
                    print(f"Error: {file_name} is not a valid XLS file.")

        upload_email_batch_process(batch_id, batch_path, profile_name, upload_type)

        return Response(
            {
                "detail": "Transaction uploaded successfully and queued for processing",
                "batch_id": batch_id,
            }
        )

    except Exception as error:
        print(error)
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def train_documents(request):
    """
    Upload new documents to training batch from profile management.
    """
    try:
        upload_type = request.POST.get("upload_type")
        email_files = request.FILES.getlist("email_files")
        other_files = request.FILES.getlist(f"{upload_type}_files")
        doc_ids = request.POST.get("doc_ids")
        customer = request.POST.get("customer", "")
        custom_data = request.POST.get("custom_data", "")
        assert upload_type in ["email", "pdf", "excel", "word"], "Invalid Upload type"

        if not doc_ids:
            return Response(
                {"detail": "doc_ids is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            doc_ids = json.loads(doc_ids)
        except:
            return Response(
                {"detail": "Invalid doc_ids, it should be string representing array"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not doc_ids:
            return Response(
                {"detail": "atleast one doc_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_docs = ProfileDocument.objects.filter(id__in=doc_ids)
        if not profile_docs.exists():
            return Response(
                {
                    "detail": "Profile Documents with provided id(s) doesn't exist ",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        files = email_files if upload_type == "email" else other_files
        if len(files) == 0:
            return Response(
                {"detail": f"{upload_type}_files not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parent_batch_id = get_new_email_batch_id(training=True)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="upload",
            message="Uploading new Training batch",
            train_batch_log=True,
        )

        batch_path = prepare_parent_batch_path(parent_batch_id, "train-batches")

        save_file_to_parent_folder(files, batch_path, upload_type)

        request_data = {
            "parent_batch_id": parent_batch_id,
            "upload_type": upload_type,
            "batch_path": batch_path,
            "doc_ids": doc_ids,
            "customer": customer,
            "custom_data": custom_data,
        }

        TrainBatch.objects.create(
            id=parent_batch_id,
            customer=customer,
            custom_data=custom_data,
        )

        publish("train_batch_queued", "to_pipeline", request_data)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="queued",
            message="Training batch added to queue for processing",
            train_batch_log=True,
        )

        return Response(
            {
                "detail": "Training Batch created",
                "train_batch_id": parent_batch_id,
            }
        )
    except IntegrityError as e:
        print(traceback.format_exc())
        return Response(
            {"detail": f"Database integrity error: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as error:
        print(traceback.format_exc())
        response = {"detail": str(error)}

        return Response(
            response,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def save_file_to_parent_folder(files, path, upload_type):
    """Save files to parent path folder"""
    email_file_count = 0

    for file in files:
        file_name = file.name
        file_name = remove_null_characters(file_name)
        print(f"{file.name=}\n{file_name=}")
        if upload_type == "email":
            extenstion = file.name[-4:]
            file_name = f"email_file_{email_file_count}{extenstion}"
            email_file_count += 1

        file_path = os.path.join(path, file_name)
        # save file to disk
        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)


def get_custom_profiles(application_settings, setting):
    custom_profiles = application_settings["profileSettings"].get(setting)
    if not custom_profiles:
        raise ValueError(f"{setting} could not be found in Application Settings")
    return custom_profiles


def process_train_batch_p1(request_data):
    """
    Start processing training batch from upload document to datacap batch creation
    """
    try:
        parent_batch_id = request_data["parent_batch_id"]
        upload_type = request_data["upload_type"]
        batch_path = request_data["batch_path"]
        doc_ids = request_data["doc_ids"]

        print(f"{request_data=}")

        profile_docs = ProfileDocument.objects.filter(id__in=doc_ids)
        if not profile_docs:
            doc_types = request_data["doc_types"]
            profile = request_data["profile_name"]
            profile_docs = ProfileDocument.objects.filter(
                profile__name=profile, doc_type__in=doc_types
            )
            if not profile_docs:
                raise ValueError(
                    "Process document doesn't exist. Please re-upload the document."
                )

        profile = profile_docs[0].profile
        selected_doc_ids = [i.id for i in profile_docs]
        selected_doc_types = [i.doc_type for i in profile_docs]

        train_batch = TrainBatch.objects.get(id=parent_batch_id)

        train_batch.matched_profile_name = profile.name
        train_batch.selected_doc_ids = selected_doc_ids
        train_batch.selected_doc_types = selected_doc_types
        train_batch.parsed_file_type = upload_type
        train_batch.save()

        # Delete previous parsed documents and linked batches
        TrainParsedDocument.objects.filter(train_batch=train_batch).delete()
        TrainToBatchLink.objects.filter(train_batch=train_batch).delete()

        # logs which documents user has selected when uploading in training.
        write_parent_batch_log(
            batch_id=parent_batch_id,
            message="Selected Doc Types",
            remarks=json.dumps(selected_doc_types),
            status="inprogress",
            action="display_json",
        )

        all_files = os.listdir(batch_path)
        attachments_folder = None
        unsupported_file_type = []

        if upload_type == "email":
            email_body_files_data = []
            attachments_files_data = []

            email_body_document_qs = profile_docs.filter(
                content_location="Email Body"
            ).filter(category="Processing")

            show_embedded_img = False
            jap_eng_convert = False
            zoom_value = "1"  # Default Zoom value
            email_body_exists = email_body_document_qs.exists()

            if email_body_exists:
                application_settings = ApplicationSettings.objects.first().data
                jap_eng_convert_profiles = get_custom_profiles(
                    application_settings, "jap_eng_convert_profiles"
                )
                custom_zoom_profiles = get_custom_profiles(
                    application_settings, "email_body_custom_zoom_profiles"
                )
                if profile.name in jap_eng_convert_profiles:
                    jap_eng_convert = True
                zoom_value = next(
                    (
                        i["value"]
                        for i in custom_zoom_profiles
                        if i["name"] == profile.name
                    ),
                    "1",
                )
            for doc in email_body_document_qs:
                if doc.show_embedded_img == True:
                    show_embedded_img = True
                    break
            email_files = [
                file
                for file in all_files
                if (file.lower().endswith(".eml") or file.lower().endswith(".msg"))
            ]

            for email_file_name in email_files:
                email_file_path = os.path.join(batch_path, email_file_name)
                # Prepare a folder to hold processed files
                output_path = prepare_extraction_path(batch_path, email_file_name)
                (
                    pdf_path,
                    attachments_folder,
                    unsupported_file_type,
                    garbled_all_error,
                ) = parse_email(
                    email_file_path,
                    email_file_name,
                    output_path,
                    show_embedded_img,
                    email_body_exists,
                    jap_eng_convert,
                    zoom_value,
                )
                if garbled_all_error:
                    for error in garbled_all_error:
                        write_parent_batch_log(
                            message=error,
                            batch_id=parent_batch_id,
                            status="warning",
                        )
                # Load Files Data in Memory
                email_body_files_data.append(
                    {
                        "file_name": os.path.basename(pdf_path),
                        "file_path": pdf_path,
                        "type": "email_body",
                        "matched_doc": None,
                        "page_file": None,
                    }
                )

                attachments = os.listdir(attachments_folder)

                for file in attachments:
                    path = os.path.join(attachments_folder, file)
                    result = {
                        "file_name": file,
                        "file_path": path,
                        "type": "attachment",
                        "matched_doc": None,
                        "page_file": None,
                    }
                    attachments_files_data.append(result)

            # Fetch Details for Email Body
            if email_body_document_qs.exists():
                email_body_document = email_body_document_qs.first()
                for item in email_body_files_data:
                    item["matched_doc"] = email_body_document

            email_body_files_data = [
                i for i in email_body_files_data if i["matched_doc"] is not None
            ]

            files_data = email_body_files_data + attachments_files_data

        elif upload_type in ["pdf", "excel", "word"]:
            files_data = process_other_files(profile, parent_batch_id, batch_path)
            attachments_folder = batch_path

        job_id = gerenate_job_id_for_batch(parent_batch_id)

        # Convert ProfileDocument instances to dict for JSON serialization
        files_data_for_redis = convert_doc_instance_to_dict(files_data)

        job_details = {
            "job_id": job_id,
            "upload_type": upload_type,
            "files_data": files_data_for_redis,
            "parent_batch_id": parent_batch_id,
            "profile_name": profile.name,
            "unsupported_file_type": unsupported_file_type,
        }

        redis_instance.set(job_id, json.dumps(job_details))

        # Send dense page detection request via RabbitMQ
        if is_dense_page_check_enabled(profile.project):
            is_ignore_dense_pages_api_called = ignore_dense_pages_p1(
                job_id, attachments_folder, parent_batch_id, True
            )

            if is_ignore_dense_pages_api_called:
                return

        request_data = {"job_id": job_id}
        process_train_batch_p2(request_data)
    except ValueError as ve:
        message = "Error occured during Training processing"
        ve_message = str(ve)
        trace = traceback.format_exc()
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"{code['code']}: {ve.args[1]}",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {"message": ve.args[0], "traceback": trace}

        try:
            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True,
            )
        except:
            pass
    except Exception as error:
        print(traceback.format_exc())
        trace = traceback.format_exc()
        message = "Error occured during Training processing"
        remarks = {
            "message": f"The following error occured in 'process_train_batch_p1' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        try:
            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
                train_batch_log=True,
            )
        except:
            pass


def process_train_batch_p2(request_data):
    """
    Process training batch from parsed documents to datacap batch creation
    """
    try:
        job_id = request_data["job_id"]
        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        upload_type = job_info["upload_type"]
        files_data = job_info["files_data"]
        parent_batch_id = job_info["parent_batch_id"]
        profile_name = job_info["profile_name"]
        unsupported_file_type = job_info.get("unsupported_file_type", [])

        # Convert matched_doc dicts back to ProfileDocument instances
        files_data = load_doc_instance_from_dict(files_data)

        # Clean up Redis data as it's no longer needed
        try:
            redis_instance.delete(job_id)
        except Exception as e:
            print(f"Error deleting Redis key {job_id}: {str(e)}")

        # Filter out items where file_path doesn't exist
        files_data = [
            item for item in files_data if os.path.exists(item.get("file_path", ""))
        ]

        train_batch = TrainBatch.objects.get(id=parent_batch_id)

        profile = Profile.objects.get(name=profile_name)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message=f"{upload_type.title()} Parsing Completed",
            train_batch_log=True,
        )

        # Save files data to DB
        for i in files_data:
            parsed_doc_instance = TrainParsedDocument.objects.create(
                train_batch=train_batch,
                name=i["file_name"],
                path=i["file_path"],
                type=i["type"],
                matched_profile_doc=i["matched_doc"],
            )
            i["parsed_doc_instance"] = parsed_doc_instance

        # Filtering supporting document
        files_data = supporting_document_matching(
            train_batch, profile, files_data, True
        )

        supporting_files = [
            i["file_path"] for i in files_data if i.get("supporting_file")
        ]

        try:
            if unsupported_file_type:
                write_parent_batch_log(
                    message="Unsupported Files Ignored",
                    batch_id=parent_batch_id,
                    remarks=json.dumps(unsupported_file_type),
                    status="warning",
                    action="display_json",
                )
        except:
            pass

        if supporting_files:
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="warning",
                message="Supporting Document(s) Ignored",
                remarks=json.dumps(supporting_files),
                action="display_json",
            )
        save_analyzer_log_time(
            batch_id=parent_batch_id, field_name="datacap_batch_creating_s"
        )
        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message="Creating Batches",
            train_batch_log=True,
        )

        files_data = [
            i
            for i in files_data
            if (i["matched_doc"] is None or i["type"] == "email_body")
            and i.get("supporting_file") is None
        ]

        if len(files_data) == 0:
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message="No batches to create. (Attachments not matched with Profile Document Type(s))",
                train_batch_log=True,
            )
            return

        files_data = sorted(
            files_data,
            key=lambda d: (
                1 if Path(d["file_name"]).suffix.lower() in EXCEL_FORMATS else 0,
                d["file_name"],
            ),
        )

        # process_excels(
        #     upload_batch_process,
        #     get_info_holder_for_batch,
        #     train_batch,
        #     profile,
        #     files_data,
        #     "training",
        # )

        files_data = convert_excel_files_to_pdf(train_batch, files_data, "training")

        process_pdfs_and_docs_p1(train_batch, profile, files_data, "training")
    except ValueError as ve:
        message = "Error occured during Training processing"
        ve_message = str(ve)
        trace = traceback.format_exc()
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"{code['code']}: {ve.args[1]}",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {"message": ve.args[0], "traceback": trace}

        try:
            test_batch_cleanup(job_id)
        except:
            pass

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
            train_batch_log=True,
        )
    except Exception as error:
        print(traceback.format_exc())
        trace = traceback.format_exc()
        message = "Error occured during Training processing"
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        remarks = {
            "message": f"The following error occured in 'process_train_batch_p2' function : '{str(error.args[0])}' ",
            "traceback": trace,
        }
        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
            train_batch_log=True,
        )


def process_other_files(profile, parent_batch_id, batch_path):
    files_data = []
    attachments_folder = batch_path

    all_files = os.listdir(attachments_folder)
    all_files = [
        file
        for file in all_files
        if Path(file).suffix.lower() in (EXCEL_FORMATS | {".doc", ".docx", ".pdf"})
    ]

    attachments = [
        file
        for file in all_files
        if not (file.lower().endswith(".eml") or file.lower().endswith(".msg"))
    ]

    for file in attachments:
        path = os.path.join(attachments_folder, file)

        if file.lower().endswith(".xls"):
            # Convert xls file to xlsx
            if validate_xls_file(path):
                xls_filename = file
                xls_path = path
                file = file.rsplit(".", 1)[0] + ".xlsx"
                path = os.path.join(attachments_folder, file)
                convert_xls_to_xlsx(xls_path, path)
                if os.path.exists(xls_path):
                    os.remove(xls_path)
            else:
                print(f"Error: {xls_filename} is not a valid XLS file.")

        result = {
            "file_name": file,
            "file_path": path,
            "type": "attachment",
            "matched_doc": None,
            "page_file": None,
        }
        files_data.append(result)

    return files_data


def cleanup_xlsx_related_pdfs(base_path):
    """
    Find all .xlsx files in the given path and delete their corresponding PDF files.
    Handles case-insensitive file extensions (e.g., .xlsx, .XLSX, .Xlsx, .pdf, .PDF, .Pdf).

    For each .xlsx file:
    1. If a PDF with the same name but with '_0' suffix exists (e.g., filename_0.pdf), delete the '_0' version
    2. Otherwise, if a PDF with the exact same name exists (e.g., filename.pdf), delete it

    Args:
        base_path: The directory path to search for .xlsx files
    """
    try:
        if not os.path.exists(base_path):
            print(f"Path does not exist: {base_path}")
            return

        # Find all .xlsx files (case-insensitive) by checking all files
        all_files = os.listdir(base_path)
        xlsx_files = [f for f in all_files if f.lower().endswith(".xlsx")]

        for xlsx_filename in xlsx_files:
            # Get the base name without extension
            base_name = os.path.splitext(xlsx_filename)[0]

            # Find matching PDFs: prioritize _0.pdf variant, otherwise delete exact match
            pdf_with_zero = None
            pdf_exact_match = None

            for filename in all_files:
                if not filename.lower().endswith(".pdf"):
                    continue

                file_base = os.path.splitext(filename)[0]

                if file_base == f"{base_name}_0":
                    pdf_with_zero = filename
                    break  # Found _0 variant, no need to continue
                elif file_base == base_name:
                    pdf_exact_match = filename

            # Delete the appropriate PDF file
            if pdf_with_zero:
                pdf_path = os.path.join(base_path, pdf_with_zero)
                os.remove(pdf_path)
                print(f"Deleted: {pdf_path}")
            elif pdf_exact_match:
                pdf_path = os.path.join(base_path, pdf_exact_match)
                os.remove(pdf_path)
                print(f"Deleted: {pdf_path}")

    except Exception as error:
        print(f"Error during PDF cleanup in {base_path}: {error}")


def cleanup_splitted_pdfs(base_path):
    """
    Find and delete all PDF files that contain '_splitted_' pattern (e.g., filename_splitted_1.pdf, filename_splitted_2.pdf).
    Handles case-insensitive file extensions (e.g., .pdf, .PDF, .Pdf).

    Args:
        base_path: The directory path to search for splitted PDF files
    """
    try:
        if not os.path.exists(base_path):
            print(f"Path does not exist: {base_path}")
            return

        # Find all files in the directory
        all_files = os.listdir(base_path)

        deleted_count = 0
        for filename in all_files:
            # Check if file is a PDF and contains '_splitted_' pattern
            if filename.lower().endswith(".pdf") and "_splitted_" in filename:
                pdf_path = os.path.join(base_path, filename)
                os.remove(pdf_path)
                print(f"Deleted: {pdf_path}")
                deleted_count += 1

        if deleted_count > 0:
            print(f"Total splitted PDFs deleted: {deleted_count}")
        else:
            print(f"No splitted PDFs found in {base_path}")

    except Exception as error:
        print(f"Error during splitted PDF cleanup in {base_path}: {error}")


@api_view(["POST"])
def re_process_email_batches(request):
    """Re-upload existing email batches"""
    request_data = request.data

    try:
        ids = request_data["ids"]
        reprocess_type = request_data["reprocess_type"]
        force_ocr_engine = request_data.get("force_ocr_engine", False)
        print(f"{reprocess_type=}")
        waiting = batch_awaiting_datacap(ids)
        if waiting:
            return Response(
                waiting,
                status=status.HTTP_400_BAD_REQUEST,
            )
    except:
        print(traceback.format_exc())
        return Response(
            {"detail": "Invalid payload. It must include ('ids', 'reprocess_type')."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        for email_batch_id in ids:
            try:
                batch_path = get_path_for_parent_batch(email_batch_id, "email-batches")
                email_batch = EmailBatch.objects.get(id=email_batch_id)
                email_batch.force_ocr_engine = force_ocr_engine
                email_batch.save()

                save_analyzer_log_time(
                    batch_id=email_batch.id, field_name="transaction_process_s"
                )
                save_analyzer_log_time(
                    batch_id=email_batch.id, field_name="re_process_email_batches_s"
                )
                linked_batches = list(
                    EmailToBatchLink.objects.filter(
                        email_id=email_batch_id, uploaded=True
                    ).values_list("batch_id", flat=True)
                )

                profile_name = email_batch.matched_profile_name
                upload_type = email_batch.parsed_file_type

                matched_profile = None

                matched_profile_qs = Profile.objects.filter(name=profile_name)

                if matched_profile_qs.exists():
                    matched_profile = matched_profile_qs.first()

                if reprocess_type == "all":
                    # Clean up PDF files related to .xlsx files
                    cleanup_xlsx_related_pdfs(batch_path)
                    cleanup_splitted_pdfs(batch_path)

                    upload_email_batch_process(
                        email_batch_id,
                        batch_path,
                        profile_name,
                        upload_type,
                        re_process=True,
                    )
                elif reprocess_type == "extraction":
                    save_analyzer_log_time(
                        batch_id=email_batch.id, field_name="re_process_extraction_s"
                    )
                    email_batch.assembly_triggered = False
                    email_batch.assembled_results = []
                    email_batch.api_triggered = False
                    # Even if the api_response is made empty, the presence of shipment_status_urls ensures that already created shipments will not be created again.
                    if not (matched_profile and matched_profile.multi_shipment):
                        email_batch.api_response = []
                    email_batch.api_retry_count = 0
                    email_batch.doc_upload_triggered = False

                    for item in email_batch.additional_docs_to_upload:
                        item["uploaded"] = False

                    email_batch.save()

                    write_parent_batch_log(
                        batch_id=email_batch_id,
                        status="inprogress",
                        message="Re-process extraction initiated",
                    )

                    if not linked_batches:
                        raise ValueError("Re-process extraction is not applicable")

                    for batch_id in linked_batches:
                        batch_instance = Batch.objects.get(id=batch_id)

                        if batch_instance.mode == "processing":
                            print(f"{batch_id}: upload_batch_process called")
                            Batch.objects.filter(id=batch_id).update(
                                status="inprogress"
                            )
                            OutputJson.objects.filter(batch__id=batch_id).delete()
                            request_data = {
                                "batch_id": batch_id,
                                "new_upload": True,
                            }

                            publish("batch_queued", "to_pipeline", request_data)
                        elif batch_instance.mode == "supporting":
                            status_ = (
                                "waiting"
                                if matched_profile.manual_validation
                                else "completed"
                            )
                            Batch.objects.filter(id=batch_id).update(status=status_)
                            request_data = {"batch_id": batch_id}

                            publish("assembly_queued", "to_pipeline", request_data)
                    save_analyzer_log_time(
                        batch_id=email_batch.id, field_name="re_process_extraction_e"
                    )
                elif reprocess_type == "api":
                    save_analyzer_log_time(
                        batch_id=email_batch.id, field_name="re_process_api_s"
                    )
                    if (
                        not email_batch.api_triggered
                        or not email_batch.assembled_results
                    ):
                        raise ValueError(
                            "Re-process API is not applicable. Please use 'Extraction' once, then try again."
                        )
                    email_batch.api_triggered = False

                    # Even if the api_response is made empty, the presence of shipment_status_urls ensures that already created shipments will not be created again.
                    if not (matched_profile and matched_profile.multi_shipment):
                        email_batch.api_response = []
                    email_batch.doc_upload_triggered = False

                    for item in email_batch.additional_docs_to_upload:
                        item["uploaded"] = False

                    email_batch.api_retry_count = 0
                    email_batch.save()

                    write_parent_batch_log(
                        batch_id=email_batch_id,
                        status="inprogress",
                        message="Re-process API initiated.",
                    )

                    if linked_batches:
                        request_data = {"batch_id": linked_batches[0]}

                        publish("api_call_queued", "to_pipeline", request_data)
                elif reprocess_type == "uploadDoc":
                    save_analyzer_log_time(
                        batch_id=email_batch.id, field_name="re_process_upload_doc_s"
                    )
                    if (
                        not email_batch.doc_upload_triggered
                        or not email_batch.assembled_results
                    ):
                        raise ValueError(
                            "Re-upload document to CW1 edoc is not applicable. Please use 'Extraction' once, then try again."
                        )

                    email_batch.doc_upload_triggered = False

                    for item in email_batch.api_response:
                        if item.get("uploaded_doc_names"):
                            item["uploaded_doc_names"] = []

                        if matched_profile and matched_profile.multi_shipment:
                            continue

                        if item.get("uploaded_doc_status_code"):
                            item["uploaded_doc_status_code"] = None

                        if item.get("uploaded_doc_response_json"):
                            item["uploaded_doc_response_json"] = {}

                    for item in email_batch.additional_docs_to_upload:
                        item["uploaded"] = False

                    email_batch.api_retry_count = 0
                    email_batch.save()

                    write_parent_batch_log(
                        batch_id=email_batch_id,
                        status="inprogress",
                        message="Re-upload document initiated",
                    )

                    if linked_batches:
                        request_data = {"batch_id": linked_batches[0]}

                        publish("doc_upload_queued", "to_pipeline", request_data)
                    save_analyzer_log_time(
                        batch_id=email_batch.id, field_name="re_process_upload_doc_e"
                    )
            except Exception as error:
                try:
                    write_parent_batch_log(
                        batch_id=email_batch_id,
                        status="failed",
                        message="Transaction upload failed",
                        remarks=str(error),
                    )
                except:
                    pass

        return Response({"detail": "Transactions Queued for re-processing"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def project_validation(request):
    """Validate a project with name and email_box"""
    projects = Project.objects.exclude(email_box__isnull=True)
    data = []
    for project in projects:
        data.append({"name": project.name, "email_box": project.email_box})

    return Response(data)


@api_view(["GET"])
def automatic_classifiable_doc_types(request):
    """Reads Master Dictionary to get automatic classifiable doc types data"""

    master_dictionaries_qs = MasterDictionary.objects.all()
    master_dictionaries = MasterDictionarySerializer(
        master_dictionaries_qs, many=True
    ).data

    master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}

    auto_classifiable_doc_types = []

    try:
        priority_direction = master_dictionaries.get(
            "matrix_title_classification_priority_directions", {}
        ).get("data")
        auto_classifiable_doc_types = priority_direction.get("category", [])
    except Exception as e:
        print(e)

    if not auto_classifiable_doc_types:
        category = master_dictionaries.get(
            "matrix_title_classification_category", {}
        ).get("data")

        auto_classifiable_doc_types = category.keys()

    return Response(auto_classifiable_doc_types)


def profile_matching(email_batch, profile_name=None):
    """
    Profile matching based on different criteria
    """
    save_analyzer_log_time(batch_id=email_batch.id, field_name="profile_matching_s")
    write_parent_batch_log(
        batch_id=email_batch.id,
        status="inprogress",
        message="Process matching initiated",
    )

    matched_profile = apply_v7_matching_logic(profile_name, email_batch)

    if not matched_profile:
        matched_profile = apply_v6_matching_logic(email_batch)

    remarks = f"Matched process: {matched_profile.name}"

    email_batch.matched_profile_name = matched_profile.name
    email_batch.save()

    # Check if project name is CustomsEntry, Then save CustomsJobNumber in DB
    # It will be required to make assmebly API calls
    if matched_profile.project == "CustomsEntryUpdate":
        email_batch.customs_number = get_customs_number_from_subject(
            email_batch.email_subject
        )
        email_batch.save()

    write_parent_batch_log(
        batch_id=email_batch.id,
        status="inprogress",
        message="Process Matching Completed",
        remarks=json.dumps(remarks),
    )
    save_analyzer_log_time(batch_id=email_batch.id, field_name="profile_matching_e")
    return matched_profile


def apply_v7_matching_logic(profile_name, email_batch):
    """
    Find a matching profile using multiple fallback strategies.

    Args:
        profile_name: Primary profile name to search for
        email_batch: Email batch object with email_subject attribute

    Returns:
        Profile object if found, None otherwise
    """
    # Strategy 1: Direct name match
    try:
        return Profile.objects.get(name=profile_name)
    except Profile.DoesNotExist:
        pass

    # Strategy 2: Match by email subject
    try:
        return Profile.objects.get(name=email_batch.email_subject.strip())
    except Profile.DoesNotExist:
        pass

    # Strategy 3: Extract process_id from email subject
    if email_batch.email_subject:
        try:
            process_id = email_batch.email_subject.split("_")[0]
            return Profile.objects.get(process_id=process_id.strip())
        except (Profile.DoesNotExist, IndexError):
            pass

    return None


def apply_v6_matching_logic(email_batch):
    email_from = email_batch.email_from.lower()
    email_domain = email_from.split("@")[-1].lower()
    email_subject = email_batch.email_subject
    # email_to = email_batch.email_to.lower()
    # email_cc = email_batch.email_cc.lower()

    garbled_subject = detect_garbled_text(email_subject)
    if garbled_subject:
        write_parent_batch_log(
            batch_id=email_batch.id,
            status="warning",
            message=f"Encoding Error: Detected garbled text in subject. The text contains unusual {''.join(garbled_subject)} characters (possible decoding failure) ",
        )
    # project_qs = Project.objects.filter(email_box__icontains=email_to)

    # """"when multiple email contains in email_to"""
    # if "," in email_to:
    #     list_email_to = email_to.split(",")
    #     for recipient in list_email_to:
    #         project_qs = Project.objects.filter(email_box__icontains=recipient)
    #         if project_qs.exists():
    #             email_batch.email_to = recipient
    #             email_batch.save()
    #             break

    #     if project_qs.exists():
    #         additional_email_to = [
    #             email for email in list_email_to if email != email_batch.email_to
    #         ]
    #         if email_cc:
    #             additional_email_to.append(email_cc)
    #         email_batch.email_cc = ",".join(additional_email_to)
    #         email_batch.save()

    # if not project_qs.exists():
    #     message = "Your Ebooking request did not match any process. Please validate the email request."
    #     code = {"code": "AIDB-102"}
    #     raise ValueError(
    #         code,
    #         "Email processing aborted as no matching project found.",
    #         message,
    #     )

    # projects = project_qs.values_list("name", flat=True)
    priority_order_case_matching = Case(
        When(email_subject_match_option="StartsWith", then=Value(1)),
        When(email_subject_match_option="EndsWith", then=Value(2)),
        When(email_subject_match_option="Regex", then=Value(3)),
        When(email_subject_match_option="Contains", then=Value(4)),
        default=Value(5),
        output_field=IntegerField(),
    )

    # Profile Matching based on project, email_domain and email_from
    base_profiles = (
        Profile.objects.filter(
            Q(email_domains__icontains=email_domain)
            | Q(email_from__icontains=email_from)
        )
        .annotate(
            domain_length=Length("email_domains"), priority=priority_order_case_matching
        )
        .order_by("priority")
        .values(
            "name",
            "email_from",
            "email_domains",
            "email_subject_match_option",
            "email_subject_match_text",
        )
    )

    normal_profiles = base_profiles.filter(domain_length__lte=1000)
    special_profiles = base_profiles.filter(domain_length__gt=1000)

    def get_matched_profiles(profile_qs):
        """Iterate through profiles to find exact match"""
        matched_profile_names = list()

        for profile in profile_qs:
            skip_condition1 = (
                profile["email_from"]
                and email_from
                and email_from not in profile["email_from"].lower()
            )

            skip_condition2 = (
                profile["email_domains"]
                and email_domain
                and not any(
                    d.lower().strip() in {email_domain, f"@{email_domain}"}
                    for d in profile["email_domains"].split(",")
                )
            )

            if skip_condition1 or skip_condition2:
                continue

            match_option = profile["email_subject_match_option"]
            match_text = profile["email_subject_match_text"].lower().strip()
            match_text = strip_extra_spaces(match_text)

            email_subject_lower = email_subject.lower().strip()
            email_subject_lower = strip_extra_spaces(email_subject_lower)

            if match_option == "StartsWith":
                if email_subject_lower.startswith(match_text):
                    matched_profile_names.append(profile["name"])
                    break
            elif match_option == "EndsWith":
                if email_subject_lower.endswith(match_text):
                    matched_profile_names.append(profile["name"])
                    break
            elif match_option == "Contains":
                if match_text in email_subject_lower:
                    matched_profile_names.append(profile["name"])
            elif match_option == "Regex":
                matches = re.findall(profile["email_subject_match_text"], email_subject)
                if matches:
                    matched_profile_names.append(profile["name"])
                    break
        return matched_profile_names

    matched_profile_names = get_matched_profiles(normal_profiles)

    if not matched_profile_names:
        matched_profile_names = get_matched_profiles(special_profiles)

    if not matched_profile_names:
        message = "Your Ebooking request did not match any process. Please validate the email request."
        code = {"code": "AIDB-103"}
        raise ValueError(
            code,
            "Email processing aborted as no matching process found.",
            message,
        )

    elif len(matched_profile_names) > 1:
        message = "Multiple processes matched. Please validate the email request."
        code = {"code": "AIDB-103"}
        raise ValueError(
            code,
            "Email processing aborted as multiple processes matched.",
            message,
        )

    matched_profile_name = matched_profile_names[0]
    matched_profile = Profile.objects.get(name=matched_profile_name)

    return matched_profile


def supporting_document_matching(
    parent_batch, matched_profile, files_data, is_training=False
):
    """
    Matching supporting document from Application Settings
    Create batch for supporting type document
    """
    supporting_attachment_documents = matched_profile.documents.filter(
        content_location="Email Attachment"
    ).filter(category="Supporting")

    other_settings = get_other_settings()

    processing_mime_types = other_settings.get("processing_mime_types")

    if not processing_mime_types:
        raise ValueError(
            "processing_mime_types could not be found in Applicaiotn Settings"
        )

    if len(supporting_attachment_documents) == 0 or matched_profile.multi_shipment:
        for item in files_data:
            create_additional_doc(
                parent_batch, matched_profile, item, processing_mime_types, is_training
            )
        return files_data

    index = 0
    for item in files_data:
        matched_doc = match_attachment(
            supporting_attachment_documents,
            None,
            item["file_path"],
        )

        if not matched_doc:
            create_additional_doc(
                parent_batch, matched_profile, item, processing_mime_types, is_training
            )
            continue

        item["supporting_file"] = True
        pd_instance = item["parsed_doc_instance"]
        pd_instance.ra_json_created = True

        if is_training:
            pd_instance.save()
            continue

        item["matched_doc"] = matched_doc

        if index == 0:
            save_analyzer_log_time(
                batch_id=parent_batch.id, field_name="supporting_batch_creation_time"
            )
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="inprogress",
                message="Creating supporting batches",
            )

        batch_id = f"{parent_batch.id.split('.')[0]}.T{index + 1}{parent_batch.id.split('.')[-1]}"

        create_supporting_batch(
            batch_id, matched_profile, matched_doc, item["file_path"]
        )

        item["supporting_batch_id"] = batch_id

        pd_instance.matched_profile_doc = matched_doc
        pd_instance.batch_id = batch_id
        pd_instance.save()

        EmailToBatchLink.objects.create(
            email=pd_instance.email,
            batch_id=batch_id,
            classified=True,
            uploaded=True,
            mode="supporting",
        )

        details = {
            "batch_id": batch_id,
            "file": item["file_path"],
        }
        save_analyzer_log_time(
            batch_id=parent_batch.id, field_name="supporting_batch_creation_time"
        )
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Supporting Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
        )

        index += 1

    return files_data


def get_customs_number_from_subject(subject):
    """
    Get customs number from subject
    """
    customs_number = subject.split("-")[0]
    if re.match(r"^(S|B)[a-zA-Z0-9]{1,20}$", customs_number):
        return customs_number
    else:
        raise ValueError("Customs Job Number not found in email subject.")


def process_email_batch_p1(request_data):
    """
    Process Email and create batches
    """
    try:
        parent_batch_id = request_data["batch_id"]
        batch_path = request_data["batch_path"]
        upload_type = request_data["upload_type"]
        profile_name = request_data["profile_name"]

        email_batch = EmailBatch.objects.get(id=parent_batch_id)
        email_batch.matched_profile_name = profile_name
        email_batch.parsed_file_type = upload_type
        email_batch.save()

        # Delete previous parsed documents and linked batches
        EmailParsedDocument.objects.filter(email=email_batch).delete()
        EmailToBatchLink.objects.filter(email=email_batch).delete()

        save_analyzer_log_time(batch_id=parent_batch_id, field_name="email_parsing_s")

        attachments_folder = None
        unsupported_file_type = []

        if upload_type == "email":
            email_file_name = get_email_file_name_from_batch_path(batch_path)
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="inprogress",
                message="Initiating Email Parsing",
            )

            # Prepare a folder to hold processed files
            output_path = prepare_extraction_path(batch_path)

            # Process email and separate attachments
            email_file_path = os.path.join(batch_path, email_file_name)
            meta_info = parse_email_metadata(email_file_path, email_file_name)

            email_batch = EmailBatch.objects.get(id=parent_batch_id)
            email_batch.email_from = meta_info["email_from"]
            email_batch.email_to = meta_info["email_to"]
            email_batch.email_cc = meta_info["email_cc"]
            email_batch.email_subject = meta_info["email_subject"]
            email_batch.save()

            matched_profile = profile_matching(email_batch, profile_name)

            profile_name = matched_profile.name

            # Fetch Details for Email Body
            email_body_document_qs = matched_profile.documents.filter(
                content_location="Email Body"
            ).filter(category="Processing")

            show_embedded_img = False
            jap_eng_convert = False
            zoom_value = "1"  # Default Zoom value
            email_body_exists = email_body_document_qs.exists()

            if email_body_exists:
                application_settings = ApplicationSettings.objects.first().data
                jap_eng_convert_profiles = get_custom_profiles(
                    application_settings, "jap_eng_convert_profiles"
                )
                custom_zoom_profiles = get_custom_profiles(
                    application_settings, "email_body_custom_zoom_profiles"
                )
                if matched_profile.name in jap_eng_convert_profiles:
                    jap_eng_convert = True
                zoom_value = next(
                    (
                        i["value"]
                        for i in custom_zoom_profiles
                        if i["name"] == matched_profile.name
                    ),
                    "1",
                )

            for doc in email_body_document_qs:
                if doc.show_embedded_img == True:
                    show_embedded_img = True
                    break

            pdf_path, attachments_folder, unsupported_file_type, garbled_all_error = (
                parse_email(
                    email_file_path,
                    email_file_name,
                    output_path,
                    show_embedded_img,
                    email_body_exists,
                    jap_eng_convert,
                    zoom_value,
                )
            )
            if garbled_all_error:
                for error in garbled_all_error:
                    print(error)
                    write_parent_batch_log(
                        batch_id=parent_batch_id,
                        status="warning",
                        message=error,
                    )
            # Load Files Data in Memory
            files_data = []

            email_body_file_data = {
                "file_name": os.path.basename(pdf_path),
                "file_path": pdf_path,
                "type": "email_body",
                "matched_doc": None,
                "page_file": None,
            }

            # Match Documents for email body
            if email_body_document_qs.exists():
                email_body_document = email_body_document_qs.first()
                email_body_file_data["matched_doc"] = email_body_document
                files_data.append(email_body_file_data)

            attachments = os.listdir(attachments_folder)

            for file in attachments:
                path = os.path.join(attachments_folder, file)
                result = {
                    "file_name": file,
                    "file_path": path,
                    "type": "attachment",
                    "matched_doc": None,
                    "page_file": None,
                }
                files_data.append(result)

        elif upload_type in ["pdf", "excel", "word"]:
            matched_profile = Profile.objects.get(name=profile_name)
            files_data = process_other_files(
                matched_profile, parent_batch_id, batch_path
            )

        job_id = gerenate_job_id_for_batch(parent_batch_id)

        # Convert ProfileDocument instances to dict for JSON serialization
        files_data_for_redis = convert_doc_instance_to_dict(files_data)

        job_details = {
            "job_id": job_id,
            "upload_type": upload_type,
            "files_data": files_data_for_redis,
            "parent_batch_id": parent_batch_id,
            "profile_name": profile_name,
            "unsupported_file_type": unsupported_file_type,
        }

        redis_instance.set(job_id, json.dumps(job_details))

        # Send dense page detection request via RabbitMQ
        if is_dense_page_check_enabled(matched_profile.project):
            is_ignore_dense_pages_api_called = ignore_dense_pages_p1(
                job_id, attachments_folder, parent_batch_id, False
            )

            if is_ignore_dense_pages_api_called:
                return

        request_data = {"job_id": job_id}
        process_email_batch_p2(request_data)

    except ValueError as ve:
        message = "Error occured during Transaction processing"
        ve_message = str(ve)
        trace = traceback.format_exc()
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"{code['code']}: {ve.args[1]}",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {"message": ve.args[0], "traceback": trace, "code": "AIDB-101"}

        try:
            test_batch_cleanup(job_id)
            print(f"{ve_message=}")
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
            )
            if len(ve.args) > 1:
                send_failure_notification(parent_batch_id, ve.args[1])
            save_analyzer_log_time(
                batch_id=parent_batch_id, field_name="email_parsing_e"
            )
        except:
            pass
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during Transaction processing"
        remarks = {
            "message": f"AIDB-101: The following error occured - '{str(error.args[0])}'",
            "traceback": trace,
            "code": "AIDB-101",
        }
        try:
            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message=message,
                action="display_error",
                remarks=json.dumps(remarks, indent=4),
            )
            send_failure_notification(parent_batch_id, remarks["message"])
            save_analyzer_log_time(
                batch_id=parent_batch_id, field_name="email_parsing_e"
            )
        except:
            pass


def process_email_batch_p2(request_data):
    """
    Process email batch from parsed documents to datacap batch creation
    """
    try:
        job_id = request_data["job_id"]
        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        upload_type = job_info["upload_type"]
        files_data = job_info["files_data"]
        parent_batch_id = job_info["parent_batch_id"]
        profile_name = job_info["profile_name"]
        unsupported_file_type = job_info.get("unsupported_file_type", [])

        # Clean up Redis data as it's no longer needed
        try:
            redis_instance.delete(job_id)
        except Exception as e:
            print(f"Error deleting Redis key {job_id}: {str(e)}")

        # Convert matched_doc dicts back to ProfileDocument instances
        files_data = load_doc_instance_from_dict(files_data)

        # Filter out items where file_path doesn't exist
        files_data = [
            item for item in files_data if os.path.exists(item.get("file_path", ""))
        ]

        email_batch = EmailBatch.objects.get(id=parent_batch_id)
        matched_profile = Profile.objects.get(name=profile_name)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message=f"{upload_type.title()} Parsing Completed",
        )

        # Save files data to DB
        for i in files_data:
            parsed_doc_instance = EmailParsedDocument.objects.create(
                email=email_batch,
                name=i["file_name"],
                path=i["file_path"],
                type=i["type"],
                matched_profile_doc=i["matched_doc"],
            )
            i["parsed_doc_instance"] = parsed_doc_instance

        # Matching supporting document
        files_data = supporting_document_matching(
            email_batch, matched_profile, files_data
        )

        supporting_files_data = [i for i in files_data if i.get("supporting_batch_id")]

        try:
            if unsupported_file_type:
                write_parent_batch_log(
                    message=f"Unsupported Files Ignored",
                    batch_id=parent_batch_id,
                    remarks=json.dumps(unsupported_file_type),
                    status="warning",
                    action="display_json",
                )
        except:
            pass

        files_data = [
            i
            for i in files_data
            if (i["matched_doc"] is None or i["type"] == "email_body")
            and i.get("supporting_file") is None
        ]

        if len(files_data) == 0:
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="warning",
                message="No Batches Created",
            )

            email_batch.verification_status = "disabled"
            email_batch.save()

            for i in supporting_files_data:
                Batch.objects.filter(id=i["supporting_batch_id"]).update(
                    status="completed"
                )

            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message="Transaction execution failed due to no processing documents",
            )
            return

        files_data = sorted(
            files_data,
            key=lambda d: (
                1 if Path(d["file_name"]).suffix.lower() in EXCEL_FORMATS else 0,
                d["file_name"],
            ),
        )
        # process_excels(
        #     upload_batch_process,
        #     get_info_holder_for_batch,
        #     email_batch,
        #     matched_profile,
        #     files_data,
        #     "processing",
        # )

        files_data = convert_excel_files_to_pdf(email_batch, files_data, "processing")

        process_pdfs_and_docs_p1(email_batch, matched_profile, files_data, "processing")

        save_analyzer_log_time(batch_id=parent_batch_id, field_name="email_parsing_e")
    except ValueError as ve:
        message = "Error occured during Transaction processing"
        ve_message = str(ve)
        trace = traceback.format_exc()
        code = ve.args[0]
        if isinstance(code, dict) and "code" in code:
            remarks = {
                "message": f"{code['code']}: {ve.args[1]}",
                "traceback": trace,
                "code": code["code"],
            }
        else:
            remarks = {"message": ve.args[0], "traceback": trace, "code": "AIDB-101"}

        try:
            test_batch_cleanup(job_id)
        except:
            pass

        print(f"{ve_message=}")
        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )
        if len(ve.args) > 1:
            send_failure_notification(parent_batch_id, ve.args[1])
        save_analyzer_log_time(batch_id=parent_batch_id, field_name="email_parsing_e")
    except Exception as error:
        trace = traceback.format_exc()
        message = "Error occured during Transaction processing"
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        remarks = {
            "message": f"AIDB-101: The following error occured - '{str(error.args[0])}'",
            "traceback": trace,
            "code": "AIDB-101",
        }
        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="failed",
            message=message,
            action="display_error",
            remarks=json.dumps(remarks, indent=4),
        )
        send_failure_notification(parent_batch_id, remarks["message"])
        save_analyzer_log_time(batch_id=parent_batch_id, field_name="email_parsing_e")


@api_view(["GET"])
def download_email_batch(request):
    """
    Download a email batch zip file from batch path [not used]
    """
    try:
        email_batch_id = request.GET.get("email_batch_id")
        if email_batch_id is None or email_batch_id == "":
            return Response(
                {"detail": "email_batch_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch_path = get_path_for_parent_batch(email_batch_id, "email-batches")
        if not os.path.isdir(batch_path):
            return Response(
                {"detail": "email_batch_path doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_subdir = email_batch_id
        zip_filename = f"{email_batch_id}.zip"
        filenames = [
            os.path.join(batch_path, i)
            for i in os.listdir(batch_path)
            if "linked_batches" not in i
        ]

        # Open BytesIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_subdir, fname)

            # Add file, at correct path
            zf.write(fpath, zip_path)

        # Must close zip for all contents to be written
        zf.close()

        # Grab ZIP file from in-memory
        resp = HttpResponse(s.getvalue())
        resp["Content-Type"] = "application/x-zip-compressed"
        resp["Content-Disposition"] = f"attachment; filename={zip_filename}"

        return resp

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def download_transaction(request):
    """
    Download a email batch zip file from transaction.
    """
    try:
        email_batch_id = request.GET.get("email_batch_id")

        if email_batch_id is None or email_batch_id == "":
            return Response(
                {"detail": "email_batch_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_batch_path = get_path_for_parent_batch(email_batch_id, "email-batches")

        if not os.path.isdir(email_batch_path):
            return Response(
                {"detail": "email_batch_path doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_batch = EmailBatch.objects.get(id=email_batch_id)

        # Include profile data inside the transaction batch
        profile_name = email_batch.matched_profile_name
        profile_id = (
            Profile.objects.filter(name=profile_name)
            .values_list("id", flat=True)
            .first()
        )
        if profile_id:
            profile_data = get_profiles_data_by_ids([profile_id])
            profile_file_path = os.path.join(
                email_batch_path, f"Profile-{profile_name}.json"
            )

            with open(profile_file_path, "w") as f:
                json.dump(profile_data, f, indent=4)

        zip_subdir = email_batch_id

        if not zip_subdir.split(".")[1].startswith("U"):
            zip_subdir = f"{zip_subdir.split('.')[0]}.U{zip_subdir.split('.')[1]}"

        zip_filename = f"{zip_subdir}.zip"

        # Listing email batch files
        files = []
        for file_path in glob.glob(
            os.path.join(email_batch_path, "**"), recursive=True
        ):
            if os.path.isfile(file_path) and "linked_batches" not in file_path:
                sub_dir = os.path.relpath(os.path.dirname(file_path), email_batch_path)

                files.append(
                    {
                        "file_path": file_path,
                        "file_data": None,
                        "sub_dir": sub_dir if sub_dir != "." else None,
                    }
                )
        # Get email batch DB info
        email_batch_data = dict()

        try:
            email_batch.id = zip_subdir
            email_batch_data = dict(EmailBatchSerializer(email_batch).data)
            email_batch_data["shipment_status_url"] = []

            # Get timeline data
            timeline_data = BatchStatus.objects.filter(
                batch_id=email_batch_id
            ).order_by("-event_time")[:100]

            timeline_data = BatchStatusSerializer(timeline_data, many=True).data
            timeline_data = [{**i, "batch_id": zip_subdir} for i in timeline_data]
            email_batch_data["timeline_data"] = timeline_data

            # Add parsed documents information
            parsed_documents = EmailParsedDocument.objects.filter(email=email_batch_id)
            if parsed_documents:
                parsed_documents_data = EmailParsedDocumentSerializer(
                    parsed_documents, many=True
                ).data

                for i in parsed_documents_data:
                    i["email"] = zip_subdir

                    batch_id = i.get("batch_id", None)
                    if batch_id and not batch_id.split(".")[1].startswith("U"):
                        modified_batch_id = (
                            f"{batch_id.split('.')[0]}.U{batch_id.split('.')[1]}"
                        )
                        i["batch_id"] = modified_batch_id

                    path = i.get("path", None)
                    if path:
                        modified_path = path.replace(email_batch_id, zip_subdir)
                        i["path"] = modified_path

                email_batch_data["parsed_documents"] = parsed_documents_data

            email_batch_data["batch_mode"] = "Processing"
            email_batch_data = json.dumps(email_batch_data, indent=4)
        except:
            pass

        # Listing email batch DB info as a json file
        files.append(
            {
                "file_path": None,
                "file_data": email_batch_data,
                "sub_dir": None,
            }
        )

        linked_batches = EmailToBatchLink.objects.filter(email_id=email_batch_id)
        if linked_batches:
            for linked_batch in linked_batches:
                # collecting linked batch data
                batch_id = linked_batch.batch_id
                batch_mode = linked_batch.mode
                classified = linked_batch.classified
                uploaded = linked_batch.uploaded

                batch_qs = Batch.objects.filter(id=batch_id)

                if batch_qs.exists():
                    # Get batch DB info
                    try:
                        batch_instance = batch_qs.first()
                        batch_path = os.path.join(
                            BATCH_INPUT_PATH, batch_instance.sub_path, batch_instance.id
                        )

                        # Get timeline data
                        timeline_data = BatchStatus.objects.filter(
                            batch_id=batch_id
                        ).order_by("-event_time")[:100]
                        timeline_data = BatchStatusSerializer(
                            timeline_data, many=True
                        ).data

                        # Get agent conversation data
                        agent_data = AiAgentConversation.objects.filter(
                            batch_id=batch_id
                        ).order_by("-event_time")
                        agent_data = AiAgentConversationSerializer(
                            agent_data, many=True
                        ).data

                        # Update linked batch ID
                        uploaded_batch = batch_id.split(".")[1].startswith("U")
                        if uploaded_batch:
                            modified_batch_id = batch_id
                        else:
                            modified_batch_id = (
                                f"{batch_id.split('.')[0]}.U{batch_id.split('.')[1]}"
                            )
                        batch_instance.id = modified_batch_id
                        batch_instance.sub_path = os.path.join(
                            "email-batches", zip_subdir, "linked_batches"
                        )

                        if batch_mode == "processing":
                            data_json = batch_instance.data_json
                            data_json["id"] = modified_batch_id

                            # Update modified batch id to data json
                            for node in data_json.get("nodes", []):
                                node["id"] = (
                                    f"{modified_batch_id}{node['id'].split(batch_id)[-1]}"
                                )

                                if node.get("children", None):
                                    for child in node["children"]:
                                        child["id"] = (
                                            f"{modified_batch_id}{child['id'].split(batch_id)[-1]}"
                                        )

                                        if child.get("children", None):
                                            for grand_child in child["children"]:
                                                grand_child["id"] = (
                                                    f"{modified_batch_id}{grand_child['id'].split(batch_id)[-1]}"
                                                )

                                                if grand_child.get("children", None):
                                                    for (
                                                        great_grand_child
                                                    ) in grand_child["children"]:
                                                        great_grand_child["id"] = (
                                                            f"{modified_batch_id}{great_grand_child['id'].split(batch_id)[-1]}"
                                                        )
                            batch_instance.data_json = data_json

                            batch_id = modified_batch_id
                            batch_files = []
                            existing_batch_files = os.listdir(batch_path)

                            batch_ra_json_file_path = os.path.join(
                                batch_path, "ra_json.json"
                            )

                            for i in existing_batch_files:
                                if i == "ra_json.json":
                                    if os.path.isfile(batch_ra_json_file_path):
                                        os.remove(batch_ra_json_file_path)
                                    break

                            with open(batch_ra_json_file_path, "w") as f:
                                json.dump(batch_instance.ra_json, f, indent=4)

                            for i in os.listdir(batch_path):
                                batch_files.append(
                                    {
                                        "file_path": os.path.join(batch_path, i),
                                        "file_data": None,
                                        "sub_dir": os.path.join(
                                            "linked_batches", batch_id
                                        ),
                                    }
                                )
                        else:
                            batch_id = modified_batch_id
                            batch_files = []

                        # Update modified batch id to timeline and agent data
                        timeline_data = [
                            {**i, "batch_id": modified_batch_id} for i in timeline_data
                        ]
                        agent_data = [
                            {**i, "batch_id": modified_batch_id} for i in agent_data
                        ]

                        batch_instance_data = dict(BatchSerializer(batch_instance).data)
                        batch_instance_data["timeline_data"] = timeline_data
                        batch_instance_data["agent_conversation"] = agent_data
                        batch_instance_data["classified"] = classified
                        batch_instance_data["uploaded"] = uploaded
                        batch_instance_data = json.dumps(batch_instance_data, indent=4)

                        # Listing batch DB info as a json file
                        batch_files.append(
                            {
                                "file_path": None,
                                "file_data": batch_instance_data,
                                "sub_dir": os.path.join("linked_batches", batch_id),
                            }
                        )

                        files = files + batch_files
                    except Exception:
                        break

        # Open BytesIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        for file in files:
            fname = "db_data.json"

            if file["file_path"]:
                fdir, fname = os.path.split(file["file_path"])

            if file["sub_dir"]:
                zip_path = os.path.join(zip_subdir, file["sub_dir"], fname)
            else:
                zip_path = os.path.join(zip_subdir, fname)

            if file["file_data"]:
                zf.writestr(zip_path, file["file_data"])

            if file["file_path"]:
                zf.write(file["file_path"], zip_path)

        # Must close zip for all contents to be written
        zf.close()

        # Grab ZIP file from in-memory
        resp = HttpResponse(s.getvalue())
        resp["Content-Type"] = "application/x-zip-compressed"
        resp["Content-Disposition"] = f"attachment; filename={zip_filename}"

        return resp

    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def download_training_batch(request):
    """
    Download a batch zip file from training.
    """
    try:
        train_batch_id = request.GET.get("train_batch_id")

        if train_batch_id is None or train_batch_id == "":
            return Response(
                {"detail": "train_batch_id parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        train_batch_path = get_path_for_parent_batch(train_batch_id, "train-batches")

        if not os.path.isdir(train_batch_path):
            return Response(
                {"detail": "train_batch_path doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        train_batch = TrainBatch.objects.get(id=train_batch_id)

        # Include profile data inside the training batch
        profile_name = train_batch.matched_profile_name
        profile_id = (
            Profile.objects.filter(name=profile_name)
            .values_list("id", flat=True)
            .first()
        )
        if profile_id:
            profile_data = get_profiles_data_by_ids([profile_id])
            profile_file_path = os.path.join(
                train_batch_path, f"Profile-{profile_name}.json"
            )

            with open(profile_file_path, "w") as f:
                json.dump(profile_data, f, indent=4)

        zip_subdir = train_batch_id

        if not zip_subdir.split(".")[1].startswith("U"):
            zip_subdir = f"{zip_subdir.split('.')[0]}.U{zip_subdir.split('.')[1]}"

        zip_filename = f"{zip_subdir}.zip"

        files = []

        for file_path in glob.glob(
            os.path.join(train_batch_path, "**"), recursive=True
        ):
            if os.path.isfile(file_path):
                sub_dir = os.path.relpath(os.path.dirname(file_path), train_batch_path)

                files.append(
                    {
                        "file_path": file_path,
                        "file_data": None,
                        "sub_dir": sub_dir if sub_dir != "." else None,
                    }
                )

        # Get email batch DB info
        train_batch_data = dict()

        try:
            train_batch.id = zip_subdir

            manual_classification_data = [
                {
                    **i,
                    "image_path": i["image_path"].replace(train_batch_id, zip_subdir),
                    "layout_file_path": (
                        i["layout_file_path"].replace(train_batch_id, zip_subdir)
                        if i["layout_file_path"]
                        else None
                    ),
                }
                for i in train_batch.manual_classification_data
            ]

            train_batch.manual_classification_data = manual_classification_data
            train_batch_data = dict(TrainBatchSerializerAll(train_batch).data)

            # Get timeline data
            timeline_data = BatchStatus.objects.filter(
                batch_id=train_batch_id
            ).order_by("-event_time")[:100]

            timeline_data = BatchStatusSerializer(timeline_data, many=True).data
            timeline_data = [{**i, "batch_id": zip_subdir} for i in timeline_data]
            train_batch_data["timeline_data"] = timeline_data

            # # Add parsed documents information
            parsed_documents = TrainParsedDocument.objects.filter(
                train_batch=train_batch_id
            )
            if parsed_documents:
                parsed_documents_data = TrainParsedDocumentSerializer(
                    parsed_documents, many=True
                ).data

                for doc in parsed_documents_data:
                    doc["train_batch"] = zip_subdir

                    batch_id = doc.get("batch_id", None)
                    if batch_id and not batch_id.split(".")[1].startswith("U"):
                        modified_batch_id = (
                            f"{batch_id.split('.')[0]}.U{batch_id.split('.')[1]}"
                        )
                        doc["batch_id"] = modified_batch_id

                    path = doc.get("path", None)
                    if path:
                        modified_path = path.replace(train_batch_id, zip_subdir)
                        doc["path"] = modified_path

                train_batch_data["parsed_documents"] = parsed_documents_data

            train_batch_data["batch_mode"] = "Training"
            train_batch_data = json.dumps(train_batch_data, indent=4)
        except:
            pass

        # Listing email batch DB info as a json file
        files.append(
            {
                "file_path": None,
                "file_data": train_batch_data,
                "sub_dir": None,
            }
        )

        # Listing linked batches files
        linked_batches = TrainToBatchLink.objects.filter(train_batch_id=train_batch_id)
        if linked_batches:
            for linked_batch in linked_batches:
                # collecting linked batch data
                batch_id = linked_batch.batch_id
                classified = linked_batch.classified
                uploaded = linked_batch.uploaded

                batch_qs = Batch.objects.filter(id=batch_id)

                if batch_qs.exists():
                    # Get batch DB info
                    try:
                        batch_instance = batch_qs.first()
                        batch_path = os.path.join(
                            BATCH_INPUT_PATH, batch_instance.sub_path, batch_instance.id
                        )

                        if batch_instance.is_dataset_batch and ".U" not in batch_id:
                            batch_path = os.path.join(
                                DATASET_BATCH_INPUT_PATH,
                                batch_instance.sub_path,
                                batch_instance.id,
                            )

                        # Get timeline data
                        timeline_data = BatchStatus.objects.filter(
                            batch_id=batch_id
                        ).order_by("-event_time")[:100]
                        timeline_data = BatchStatusSerializer(
                            timeline_data, many=True
                        ).data

                        # Get agent conversation data
                        agent_data = AiAgentConversation.objects.filter(
                            batch_id=batch_id
                        ).order_by("-event_time")
                        agent_data = AiAgentConversationSerializer(
                            agent_data, many=True
                        ).data

                        # Update linked batch ID
                        uploaded_batch = batch_id.split(".")[1].startswith("U")
                        if uploaded_batch:
                            modified_batch_id = batch_id
                        else:
                            modified_batch_id = (
                                f"{batch_id.split('.')[0]}.U{batch_id.split('.')[1]}"
                            )
                        batch_instance.id = modified_batch_id
                        batch_instance.sub_path = os.path.join(
                            "train-batches", zip_subdir, "linked_batches"
                        )

                        data_json = batch_instance.data_json
                        data_json["id"] = modified_batch_id

                        # Update modified batch id to data json
                        for node in data_json.get("nodes", []):
                            node["id"] = (
                                f"{modified_batch_id}{node['id'].split(batch_id)[-1]}"
                            )

                            if node.get("children", None):
                                for child in node["children"]:
                                    child["id"] = (
                                        f"{modified_batch_id}{child['id'].split(batch_id)[-1]}"
                                    )

                                    if child.get("children", None):
                                        for grand_child in child["children"]:
                                            grand_child["id"] = (
                                                f"{modified_batch_id}{grand_child['id'].split(batch_id)[-1]}"
                                            )

                                            if grand_child.get("children", None):
                                                for great_grand_child in grand_child[
                                                    "children"
                                                ]:
                                                    great_grand_child["id"] = (
                                                        f"{modified_batch_id}{great_grand_child['id'].split(batch_id)[-1]}"
                                                    )

                        filepath = data_json.get("bvFilePath", None)
                        if filepath:
                            modified_filepath = filepath.replace(
                                train_batch_id, zip_subdir
                            )
                            data_json["bvFilePath"] = modified_filepath

                        batch_instance.data_json = data_json

                        # Update modified batch id to timeline and agent data
                        timeline_data = [
                            {**i, "batch_id": modified_batch_id} for i in timeline_data
                        ]
                        agent_data = [
                            {**i, "batch_id": modified_batch_id} for i in agent_data
                        ]

                        batch_id = modified_batch_id
                        existing_batch_files = os.listdir(batch_path)

                        batch_ra_json_file_path = os.path.join(
                            batch_path, "ra_json.json"
                        )

                        for i in existing_batch_files:
                            if i == "ra_json.json":
                                if os.path.isfile(batch_ra_json_file_path):
                                    os.remove(batch_ra_json_file_path)
                                break

                        with open(batch_ra_json_file_path, "w") as f:
                            json.dump(batch_instance.ra_json, f, indent=4)

                        # Listing batch files
                        batch_files = []
                        for i in os.listdir(batch_path):
                            batch_files.append(
                                {
                                    "file_path": os.path.join(batch_path, i),
                                    "file_data": None,
                                    "sub_dir": os.path.join("linked_batches", batch_id),
                                }
                            )

                        batch_instance_data = dict(BatchSerializer(batch_instance).data)
                        batch_instance_data["timeline_data"] = timeline_data
                        batch_instance_data["agent_conversation"] = agent_data
                        batch_instance_data["classified"] = classified
                        batch_instance_data["uploaded"] = uploaded
                        batch_instance_data = json.dumps(batch_instance_data, indent=4)

                        # Listing batch DB info as a json file
                        batch_files.append(
                            {
                                "file_path": None,
                                "file_data": batch_instance_data,
                                "sub_dir": os.path.join("linked_batches", batch_id),
                            }
                        )

                        files = files + batch_files
                    except Exception:
                        break

        # Open BytesIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        for file in files:
            fname = "db_data.json"

            if file["file_path"]:
                fdir, fname = os.path.split(file["file_path"])

            if file["sub_dir"]:
                zip_path = os.path.join(zip_subdir, file["sub_dir"], fname)
            else:
                zip_path = os.path.join(zip_subdir, fname)

            if file["file_data"]:
                zf.writestr(zip_path, file["file_data"])

            if file["file_path"]:
                zf.write(file["file_path"], zip_path)

        # Must close zip for all contents to be written
        zf.close()

        print("------------zip_filename after zip made----------", zip_filename)

        # Grab ZIP file from in-memory
        resp = HttpResponse(s.getvalue())
        resp["Content-Type"] = "application/x-zip-compressed"
        resp["Content-Disposition"] = f"attachment; filename={zip_filename}"

        return resp

    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def upload_training_batch(request):
    """
    Upload a batch zip file in training.
    """
    try:
        replace_if_exists = request.POST.get("replace_if_exists")
        ignore_fields = request.POST.get("ignore_fields", False)
        if ignore_fields != bool and ignore_fields == "true":
            ignore_fields = True
        elif ignore_fields != bool and ignore_fields == "false":
            ignore_fields = False
        replace_if_exists = True if replace_if_exists == "true" else False

        try:
            zip_file = request.FILES["zip_file"]
        except:
            return Response(
                {"detail": "batch_path should be valid dictionary."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_file_name = zip_file.name
        assert zip_file_name.endswith(".zip"), "zip file should be of zip format"

        train_batch_path = os.path.join(BATCH_INPUT_PATH, "train-batches")

        # create if train-batches not exists
        if not os.path.exists(train_batch_path):
            os.mkdir(train_batch_path)

        with zipfile.ZipFile(zip_file, "r") as zip:
            zip_items = zip.namelist()

            # File name can not have "/"
            valid_files = ["/" in i for i in zip_items]
            if False in valid_files:
                return Response(
                    {
                        "detail": "Invalid Zip file. Zip should contain folders at root level not files."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            train_batch_id = zip_items[0].split("/")[0] if zip_items else None
            print(f"{train_batch_id=}")

            db_data_json = "db_data.json"
            ra_json_file_name = "ra_json.json"
            root_db_data_json_path = os.path.join(train_batch_id, db_data_json)

            if root_db_data_json_path not in zip_items:
                return Response(
                    {
                        "detail": "Invalid Zip file. Zip should contain db_data.json file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if train batch already exists:
            if train_batch_id in os.listdir(train_batch_path):
                if replace_if_exists:
                    shutil.rmtree(os.path.join(train_batch_path, train_batch_id))
                else:
                    return Response(
                        {
                            "detail": f"Batch {train_batch_id} already exists at sub_path train-batches."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            zip.extractall(train_batch_path)

            # Update Database for train batch and linked batches
            # Create train batch in database
            with zip.open(root_db_data_json_path) as json_file:
                # Load the JSON content into a Python object
                train_batch_data = json.load(json_file)

                # Check batch mode Training or Processing
                batch_mode = train_batch_data.pop("batch_mode", [])
                if batch_mode == "Processing":
                    return Response(
                        {"detail": f"{train_batch_id}: This is an Email Batch."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if ignore_fields:
                    train_batch_data = transaction_filter(
                        train_batch_data, "train_batch"
                    )

                train_batch_data.pop("created_at", None)
                train_batch_data.pop("updated_at", None)
                timeline_data = train_batch_data.pop("timeline_data", [])
                parsed_documents_data = train_batch_data.pop("parsed_documents", [])

                try:
                    TrainBatch.objects.get(id=train_batch_data["id"]).delete()
                except:
                    pass

                train_batch = TrainBatch.objects.create(**train_batch_data)

                # Update train Batch Status
                BatchStatus.objects.filter(batch_id=train_batch_id).delete()

                for item in timeline_data[::-1]:
                    item.pop("id", None)
                    BatchStatus.objects.create(**item)

                # Update parsed documents
                TrainParsedDocument.objects.filter(batch_id=train_batch).delete()

                for item in parsed_documents_data:
                    item["train_batch"] = train_batch
                    item.pop("matched_profile_doc", None)
                    TrainParsedDocument.objects.create(**item)

                os.remove(os.path.join(train_batch_path, train_batch_id, db_data_json))

            # Listing db_data_json files for linked batches
            db_data_json_files = [
                item
                for item in zip_items
                if item.endswith(db_data_json) and item != root_db_data_json_path
            ]

            # Create batches in database for linked batches
            for db_data_json_file in db_data_json_files:
                try:
                    with zip.open(db_data_json_file) as json_file:

                        batch_data = json.load(json_file)
                        if ignore_fields:
                            batch_data = transaction_filter(batch_data, "batch")
                        batch_data.pop("created_at", None)
                        batch_data.pop("updated_at", None)
                        timeline_data = batch_data.pop("timeline_data", [])
                        agent_data = batch_data.pop("agent_conversation", [])

                        batch_id = batch_data["id"]
                        batch_mode = batch_data["mode"]
                        classified = batch_data.pop("classified", [])
                        uploaded = batch_data.pop("uploaded", [])

                        try:
                            Batch.objects.get(id=batch_id).delete()
                        except:
                            pass

                        # Create batch
                        batch_instance = Batch.objects.create(**batch_data)

                        batch_path = os.path.join(
                            BATCH_INPUT_PATH, batch_data["sub_path"]
                        )

                        ra_json_zip_file_path = db_data_json_file.replace(
                            db_data_json, ra_json_file_name
                        )

                        ra_json = None
                        # Update RA JSON
                        with zip.open(ra_json_zip_file_path) as ra_json_file:
                            ra_json = json.load(ra_json_file)

                        OrganizeFiles(batch_id, batch_path, batch_instance).process()

                        ra_json["id"] = batch_id

                        for node in ra_json["nodes"]:
                            node["id"] = f"{batch_id}.{node['id'].split('.')[-1]}"

                        batch_instance.ra_json = ra_json
                        batch_instance.save()

                        TrainToBatchLink.objects.create(
                            train_batch=train_batch,
                            batch_id=batch_id,
                            mode=batch_mode,
                            classified=classified,
                            uploaded=uploaded,
                        )

                        # Update Batch Status
                        BatchStatus.objects.filter(batch_id=batch_id).delete()

                        for item in timeline_data[::-1]:
                            item.pop("id", None)
                            BatchStatus.objects.create(**item)

                        # Update Agent Conversation
                        AiAgentConversation.objects.filter(batch_id=batch_id).delete()

                        for item in agent_data[::-1]:
                            item.pop("id", None)
                            AiAgentConversation.objects.create(**item)

                        os.remove(os.path.join(batch_path, batch_id, db_data_json))
                except Exception:
                    break
        return Response({"detail": "Transaction saved to disk"})
    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def transaction_filter(data, model_filter):
    """Filter transaction emailbatch"""

    def timeline_filter(timeline):
        """Filter timeline data"""
        batch_status_fields = [field.name for field in BatchStatus._meta.fields]
        filtered_list = []
        for entry in timeline:
            filtered_timeline = {
                key: value for key, value in entry.items() if key in batch_status_fields
            }
            filtered_list.append(filtered_timeline)
        return filtered_list

    if model_filter == "email_batch":
        email_batch_fields = [field.name for field in EmailBatch._meta.fields]
        timeline = data.pop("timeline_data")
        filtered_data = {
            key: value for key, value in data.items() if key in email_batch_fields
        }

        filtered_data["timeline_data"] = timeline_filter(timeline)

    elif model_filter == "batch":
        batch_fields = [field.name for field in Batch._meta.fields]
        timeline = data.pop("timeline_data")
        filtered_data = {
            key: value for key, value in data.items() if key in batch_fields
        }
        filtered_data["timeline_data"] = timeline_filter(timeline)

    return filtered_data


@api_view(["POST"])
def upload_transaction(request):
    """
    Upload a email batch zip file in transaction.
    """
    try:
        replace_if_exists = request.POST.get("replace_if_exists")
        ignore_fields = request.POST.get("ignore_fields", False)
        if ignore_fields != bool and ignore_fields == "true":
            ignore_fields = True
        elif ignore_fields != bool and ignore_fields == "false":
            ignore_fields = False
        replace_if_exists = True if replace_if_exists == "true" else False

        try:
            zip_file = request.FILES["zip_file"]
        except:
            return Response(
                {"detail": "batch_path should be valid dictionary."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_file_name = zip_file.name
        assert zip_file_name.endswith(".zip"), "zip file should be of zip format"

        email_batch_path = os.path.join(BATCH_INPUT_PATH, "email-batches")

        # create if email-batches not exists
        if not os.path.exists(email_batch_path):
            os.mkdir(email_batch_path)

        with zipfile.ZipFile(zip_file, "r") as zip:
            zip_items = zip.namelist()

            # File name can not have "/"
            valid_files = ["/" in i for i in zip_items]
            if False in valid_files:
                return Response(
                    {
                        "detail": "Invalid Zip file. Zip should contain folders at root level not files."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            email_batch_id = zip_items[0].split("/")[0] if zip_items else None
            print(f"{email_batch_id=}")

            db_data_json = "db_data.json"
            ra_json_file_name = "ra_json.json"
            root_db_data_json_path = os.path.join(email_batch_id, db_data_json)

            if root_db_data_json_path not in zip_items:
                return Response(
                    {
                        "detail": "Invalid Zip file. Zip should contain db_data.json file."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if email batch already exists:
            if email_batch_id in os.listdir(email_batch_path):
                if replace_if_exists:
                    shutil.rmtree(os.path.join(email_batch_path, email_batch_id))
                else:
                    return Response(
                        {
                            "detail": f"Batch {email_batch_id} already exists at sub_path email-batches."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            zip.extractall(email_batch_path)

            # Update Database for email batch and linked batches
            # Create email batch in database
            with zip.open(root_db_data_json_path) as json_file:
                # Load the JSON content into a Python object
                email_batch_data = json.load(json_file)

                # Check batch mode Training or Processing
                batch_mode = email_batch_data.pop("batch_mode", [])
                if batch_mode == "Training":
                    return Response(
                        {"detail": f"{email_batch_id}: This is a Training Batch."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if ignore_fields:
                    email_batch_data = transaction_filter(
                        email_batch_data, "email_batch"
                    )

                # Update Null shipment_status_url field
                shipment_status_url = email_batch_data.get("shipment_status_url")
                if not shipment_status_url:
                    email_batch_data["shipment_status_url"] = []

                email_batch_data.pop("created_at", None)
                email_batch_data.pop("updated_at", None)
                timeline_data = email_batch_data.pop("timeline_data", [])
                parsed_documents_data = email_batch_data.pop("parsed_documents", [])

                try:
                    EmailBatch.objects.get(id=email_batch_data["id"]).delete()
                except:
                    pass

                email_batch = EmailBatch.objects.create(**email_batch_data)

                # Update Email Batch Status
                BatchStatus.objects.filter(batch_id=email_batch_id).delete()

                for item in timeline_data[::-1]:
                    item.pop("id", None)
                    BatchStatus.objects.create(**item)

                # Update parsed documents
                EmailParsedDocument.objects.filter(batch_id=email_batch).delete()

                for item in parsed_documents_data:
                    item["email"] = email_batch
                    item.pop("matched_profile_doc", None)
                    EmailParsedDocument.objects.create(**item)

                os.remove(os.path.join(email_batch_path, email_batch_id, db_data_json))

            # Listing db_data_json files for linked batches
            db_data_json_files = [
                item
                for item in zip_items
                if item.endswith(db_data_json) and item != root_db_data_json_path
            ]

            # Create batches in database for linked batches
            for db_data_json_file in db_data_json_files:
                try:
                    with zip.open(db_data_json_file) as json_file:

                        batch_data = json.load(json_file)
                        if ignore_fields:
                            batch_data = transaction_filter(batch_data, "batch")
                        batch_data.pop("created_at", None)
                        batch_data.pop("updated_at", None)
                        timeline_data = batch_data.pop("timeline_data", [])
                        agent_data = batch_data.pop("agent_conversation", [])

                        batch_id = batch_data["id"]
                        batch_mode = batch_data["mode"]
                        classified = batch_data.pop("classified", [])
                        uploaded = batch_data.pop("uploaded", [])

                        try:
                            Batch.objects.get(id=batch_id).delete()
                        except:
                            pass

                        # Create batch
                        batch_instance = Batch.objects.create(**batch_data)

                        batch_path = os.path.join(
                            BATCH_INPUT_PATH, batch_data["sub_path"]
                        )

                        if batch_mode == "processing":
                            ra_json_zip_file_path = db_data_json_file.replace(
                                db_data_json, ra_json_file_name
                            )
                            ra_json = None
                            # Update RA JSON
                            with zip.open(ra_json_zip_file_path) as ra_json_file:
                                ra_json = json.load(ra_json_file)

                            OrganizeFiles(
                                batch_id, batch_path, batch_instance
                            ).process()

                            ra_json["id"] = batch_id

                            for node in ra_json["nodes"]:
                                node["id"] = f"{batch_id}.{node['id'].split('.')[-1]}"

                            batch_instance.ra_json = ra_json
                            batch_instance.save()

                        EmailToBatchLink.objects.create(
                            email=email_batch,
                            batch_id=batch_id,
                            mode=batch_mode,
                            classified=classified,
                            uploaded=uploaded,
                        )

                        # Update Batch Status
                        BatchStatus.objects.filter(batch_id=batch_id).delete()

                        for item in timeline_data[::-1]:
                            item.pop("id", None)
                            BatchStatus.objects.create(**item)

                        # Update Agent Conversation
                        AiAgentConversation.objects.filter(batch_id=batch_id).delete()

                        for item in agent_data[::-1]:
                            item.pop("id", None)
                            AiAgentConversation.objects.create(**item)

                        os.remove(os.path.join(batch_path, batch_id, db_data_json))
                except Exception:
                    break
        return Response({"detail": "Transaction saved to disk"})
    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def test_models(request):
    """
    Test a table model its found table boundary or not
    """
    request_data = request.data
    try:
        batch_id = request_data["batch_id"]
        batch_instance = Batch.objects.get(id=batch_id)
        definition = reduce_final_definitions_for_docbuilder(
            [request_data["definition"]], batch_instance.type
        )
    except:
        return Response(
            {"detail": "Invalid payload. It must include 'batch_id', 'definition'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json

        request_body = {
            "batch_id": batch_id,
            "ra_json": ra_json,
            "definitions": definition,
        }

        response = requests.post(
            f"{DOCBUILDER_API_URL}/validation_process", json=request_body
        )

        if response.status_code != 200:
            return Response(
                {"detail": "Test models request execution failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_json = response.json()

        return Response(
            {
                "detail": "Test models request execution completed.",
                "data": response_json,
            }
        )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def chunk_data(request):
    """
    Get chunk data from docbuilder upon request and return it
    """
    print(request.data)
    request_data = request.data
    try:
        batch_id = request_data["batch_id"]
        definition_version = request_data["definition_version"]
        template = request_data.get("template", None)
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'batch_id' and 'definition_version'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        request_body = {
            "batch_id": batch_id,
            "ra_json": ra_json,
            "definitions": reduce_final_definitions_for_docbuilder(
                definitions, batch_instance.type
            ),
        }

        response = requests.post(
            f"{DOCBUILDER_API_URL}/validation_process", json=request_body
        )

        if response.status_code != 200:
            return Response(
                {"detail": "Chunk data request execution failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_json = response.json()

        return Response(
            {"detail": "Chunk data request execution completed.", "data": response_json}
        )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def chunk_data_plain_text(request):
    """
    Get chunk data from docbuilder upon request and return it
    """
    request_data = request.data
    print(request.data)

    try:
        batch_id = request_data["batch_id"]
        document_id = request_data["document_id"]
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'batch_id' and 'definition_version'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:

        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json

        # find the doc node inside ra_json["nodes"]
        document = next(
            (doc for doc in ra_json.get("nodes", []) if doc.get("id") == document_id),
            None,
        )

        if document is None:
            return Response(
                {"detail": f"Document with id '{document_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # get pages from dthe doc
        pages = document.get("children", [])
        if not pages:
            return Response(
                {"detail": f"No pages found in document '{document_id}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        all_page_texts = [
            f"\n########################\nPAGE {idx+1}\n########################\n{get_ra_json_to_txt(page)}"
            for idx, page in enumerate(pages)
        ]
        complete_text = "\n\n".join(all_page_texts)

        return Response(
            {
                "detail": "Plain text extraction completed.",
                "data": complete_text,
            }
        )

    except Exception as error:
        return Response(
            {"detail": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def atm_chunk_data(request):
    """
    Get ATM chunk data from docbuilder upon request and return it
    """
    request_data = request.data

    try:
        batch_id = request_data["batch_id"]
        definition_version = request_data["definition_version"]
        template = request_data.get("template", None)
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'batch_id' and 'definition_version'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        request_body = {
            "batch_id": batch_id,
            "ra_json": ra_json,
            "definitions": definitions,
        }

        response = requests.post(
            f"{DOCBUILDER_API_URL}/get_chunk_data", json=request_body
        )

        if response.status_code != 200:
            return Response(
                {"detail": "Atm chunk data request execution failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_json = response.json()

        chunk_line_records = process_atm_chunk_data(response_json, batch_id)

        return Response(
            {
                "detail": "Atm chunk data request execution completed.",
                "data": chunk_line_records,
            }
        )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def position_shift_data(request):
    """Takes batch_id, definition_version & table_unique_id and
    returns position_shift_data for all documents of the batch"""

    request_data = request.data

    try:
        batch_id = request_data["batch_id"]
        definition_version = request_data["definition_version"]
        table_unique_id = request_data["table_unique_id"]
        template = request_data.get("template", None)
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'batch_id', 'table_unique_id' and 'definition_version'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        if table_unique_id:
            definitions = reduce_definitions_for_table(definitions, table_unique_id)

        request_body = {
            "batch_id": batch_id,
            "ra_json": ra_json,
            "definitions": definitions,
        }

        response = requests.post(
            f"{DOCBUILDER_API_URL}/get_position_shift_data", json=request_body
        )

        if response.status_code != 200:
            error = response.json()["error"]

            return Response(
                {"detail": f"Position shift calculation failed: '{str(error)}'"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_json = response.json()

        return Response(
            {
                "detail": "Position shift calculation completed.",
                "data": response_json["data"],
            }
        )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def remove_not_in_use_batches(request):
    """
    Remove batch folders from BATCH_INPUT_PATH that are not referenced
    by any Batch, EmailBatch, or TrainBatch records.

    Folders like train-batches, templates, reports, and email-batches
    must NEVER be deleted by this cleanup.
    """

    try:
        # Only consider child batch IDs under BATCH_INPUT_PATH
        # EmailBatch and TrainBatch live inside 'email-batches' and 'train-batches'
        # which are protected separately, so their IDs are not needed here.
        used_batches = list(Batch.objects.all().values_list("id", flat=True))

        # Folders that must never be deleted by this cleanup
        protected_folders = {
            "train-batches",
            "templates",
            "reports",
            "email-batches",
            "AIDBLogs",
            "AIDBDataBackup",
        }

        disk_content = os.listdir(BATCH_INPUT_PATH)
        for folder in disk_content:
            # Skip known system / special-purpose folders
            if folder in protected_folders:
                continue

            # Delete only folders that look like batch IDs and are not referenced anywhere
            if (
                (folder not in used_batches)
                and (len(folder) == 20)
                and (folder.replace(".", "").isnumeric())
            ):
                shutil.rmtree(os.path.join(BATCH_INPUT_PATH, folder))
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"detail": "Not in Use Batches removed successfully"})


@api_view(["POST"])
@permission_classes([AllowAny])
def upload_batch_to_datacap(request):
    """This view triggers invokes multiple APIs to Datacap server"""

    files = request.FILES.getlist("files")
    page_file = request.POST.get("page_file")
    # Inputs Validation

    invaild_inputs = []
    if len(files) == 0:
        invaild_inputs.append("files")

    invalid_string = ", ".join(invaild_inputs)
    if invaild_inputs:
        return Response(
            {"detail": f"Following inputs are missing: {invalid_string}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Class initialization will execute the data workflow
        datacap = DataCap()
        details = datacap.create_batch(files=files, page_file=page_file)

        # Record activity as pre_upload batch status
        batch_id = details["batch_id"]
        message = "Batch Uploaded to Datacap"
        remarks = ""
        handle_pre_upload_log(batch_id, message, remarks)

        return Response(
            {"detail": "Documents uploaded successfully", "batch_details": details}
        )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def re_process_training_batches(request):
    """Re-process existing train batches"""
    request_data = request.data

    try:
        ids = request_data["ids"]
        reprocess_type = request_data["reprocess_type"]
    except:
        return Response(
            {"detail": "Invalid payload. It must include ('ids', 'reprocess_type')."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        for train_batch_id in ids:
            try:
                existing_train_batch_instance = TrainBatch.objects.get(
                    id=train_batch_id
                )

                if reprocess_type == "all":
                    selected_doc_ids = existing_train_batch_instance.selected_doc_ids
                    selected_doc_types = (
                        existing_train_batch_instance.selected_doc_types
                    )
                    matched_profile_name = (
                        existing_train_batch_instance.matched_profile_name
                    )
                    parsed_file_type = existing_train_batch_instance.parsed_file_type
                    TrainBatch.objects.get(id=train_batch_id).delete()

                    # Clean unnecessary files
                    try:
                        batch_path = get_path_for_parent_batch(
                            train_batch_id, "train-batches"
                        )

                        # Clean up PDF files related to .xlsx files
                        cleanup_xlsx_related_pdfs(batch_path)
                        cleanup_splitted_pdfs(batch_path)

                        images_path = os.path.join(batch_path, "images")
                        layout_xml_files_path = os.path.join(
                            batch_path, "layout_xml_files"
                        )
                        shutil.rmtree(images_path)
                        shutil.rmtree(layout_xml_files_path)
                    except Exception as error:
                        print(
                            f"Failed to clean the training batch during reprocessing: {error}"
                        )

                    write_parent_batch_log(
                        batch_id=train_batch_id,
                        status="upload",
                        message="Re-uploading Existing Training Batch",
                        train_batch_log=True,
                    )

                    request_data = {
                        "parent_batch_id": train_batch_id,
                        "upload_type": parsed_file_type,
                        "batch_path": batch_path,
                        "doc_ids": selected_doc_ids,
                        "doc_types": selected_doc_types,
                        "profile_name": matched_profile_name,
                    }

                    TrainBatch.objects.create(id=train_batch_id)

                    publish("train_batch_queued", "to_pipeline", request_data)

                    write_parent_batch_log(
                        batch_id=train_batch_id,
                        status="queued",
                        message="Training batch added to queue for processing",
                        train_batch_log=True,
                    )
                elif reprocess_type == "extraction":
                    linked_batches = list(
                        TrainToBatchLink.objects.filter(
                            train_batch_id=train_batch_id, uploaded=True
                        ).values_list("batch_id", flat=True)
                    )
                    existing_train_batch_instance.status = "inprogress"
                    existing_train_batch_instance.save()

                    write_parent_batch_log(
                        batch_id=train_batch_id,
                        status="inprogress",
                        message="Re-process extraction initiated",
                    )

                    if not linked_batches:
                        raise ValueError("Re-process extraction is not applicable")

                    for batch_id in linked_batches:
                        batch_instance = Batch.objects.get(id=batch_id)

                        if batch_instance.mode != "training":
                            continue

                        print(f"{batch_id}: upload_batch_process called")
                        Batch.objects.filter(id=batch_id).update(status="inprogress")
                        OutputJson.objects.filter(batch__id=batch_id).delete()
                        request_data = {
                            "batch_id": batch_id,
                            "new_upload": False,
                        }

                        publish("batch_queued", "to_pipeline", request_data)
            except Exception as error:
                try:
                    write_parent_batch_log(
                        batch_id=batch_id,
                        status="failed",
                        message="Training batch re-process failed",
                        remarks=str(error),
                        train_batch_log=True,
                    )
                except:
                    pass

        return Response({"detail": "Train Batch Queued for re-processing"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def re_process_extraction(request):
    """Re-process a batch for extraction data"""
    request_data = request.data

    try:
        ids = request_data["ids"]
        template = request_data.get("template_name", None)
        if not ids:
            return Response(
                {"detail": "invalid ids"}, status=status.HTTP_400_BAD_REQUEST
            )

        for batch_id in ids:
            try:
                batch_upload_mode = Batch.objects.get(id=batch_id).mode
                sub_path = Batch.objects.get(id=batch_id).sub_path
                upload_batch_process(
                    batch_id,
                    batch_upload_mode,
                    sub_path,
                    re_process=True,
                    template=template,
                )
            except ValueError as ve:
                trace = traceback.format_exc()
                print(trace)
                error_message = ve.args[0]
                raise ValueError(error_message)
            except Exception as error:
                try:
                    write_failed_log(
                        batch_id=batch_id,
                        status="failed",
                        message="Batch upload failed",
                        remarks=str(error),
                    )
                except:
                    pass
        return Response({"detail": "Batches Queued for re-processing"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_docbuilder_payload(request):
    """
    Get docbuilder API Call payload.
    Can be used to Debug issues.
    """
    batch_id = request.query_params.get("batch_id")
    document_id = request.query_params.get("document_id")
    template = request.query_params.get("template", None)
    definition_version = request.query_params.get(
        "definition_version", settings.DEFAULT_DEFINITION_VERSION
    )

    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        if document_id:
            ra_json = reduce_ra_json_for_document(ra_json, document_id)

        data_json = DataJson(ra_json).process()
        data_json["definition_version"] = definition_version

        definitions = get_definitions_for_batch(
            batch_instance,
            definition_version=definition_version,
            template=template,
        )

        defined_keys = list(DefinedKey.objects.all().values_list("label", flat=True))

        docbuilder_payload = {
            "id": batch_instance.id,
            "document_id": document_id,
            "ra_json": ra_json,
            "data_json": data_json,
            "definitions": definitions,
            "defined_keys_data": defined_keys,
        }

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"docbuilder_payload": docbuilder_payload})


@api_view(["POST"])
@permission_classes([AllowAny])
def get_chars_from_xml(request):
    """
    Returns character level data for given node.
    """

    request_data = request.data
    try:
        batch_id = request_data["batch_id"]
        page_id = request_data["page_id"]
        pos = request_data["pos"]
        v = request_data["v"]
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'batch_id', 'page_id', 'pos' and 'v'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        sub_path = Batch.objects.get(id=batch_id).sub_path
    except Batch.DoesNotExist:
        return Response(
            {"detail": f"Batch {batch_id} doesn't exist"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        xml_file_path = os.path.join(
            BATCH_INPUT_PATH, sub_path, batch_id, f"{page_id}_layout.xml"
        )
        if not os.path.exists(xml_file_path):
            return Response(
                {"detail": f"XML file '{xml_file_path}' doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tree = ET.parse(xml_file_path)
        PAGE = tree.getroot()

        node = PAGE.find(f".//*[@pos='{pos}'][@v='{v}']")
        if node is not None:
            char_nodes = node.findall("C")
            result = [c.attrib for c in char_nodes]
            return Response(result)
        else:
            return Response(
                {"detail": "Node with provided 'pos' and 'v' doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def get_text_by_pos(request):
    """Return text for the corresponding position"""
    request_data = request.data
    try:
        document_index = request_data["document_index"]
        page_index = request_data["page_index"]
        positions = request_data["positions"]
        batch_id = request_data["batch_id"]
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'document_index', 'page_index', 'positions' and 'batch_id'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json

        request_body = {"ra_json": ra_json}
        params = {
            "document_index": document_index,
            "page_index": page_index,
            "positions": positions,
        }

        response = requests.post(
            f"{DOCBUILDER_API_URL}/get_text_by_pos", json=request_body, params=params
        )

        if response.status_code != 200:
            # error = f'Docbuilder did not send valid response: \n {response.text}'
            return Response(
                {"detail": "Docbuilder API didn't send valid response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_json = response.json()

        return Response({"text": response_json["text"]})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def batch_path_content(request):
    """
    Return file items in a batch path
    """
    batch_content = get_developer_settings("BatchPathContent")
    if not batch_content:
        return Response({"items": [], "count": 0})

    try:
        sub_path = request.GET.get("sub_path", "")
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))
        search = request.GET.get("search", "").lower()
        sort_by = request.GET.get("sort_by", "name")
        sort_desc = request.GET.get("sort_desc", "false") == "true"

        try:
            request_path = _safe_join(BATCH_INPUT_PATH, sub_path)
        except ValueError:
            return Response(
                {"detail": "Invalid sub_path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with os.scandir(request_path) as entries:
            items = [
                {
                    "name": entry.name,
                    "is_folder": entry.is_dir(),
                    "date_modified": datetime.utcfromtimestamp(entry.stat().st_mtime),
                }
                for entry in entries
                if not search or search in entry.name.lower()
            ]

        # Sorting and pagination
        items.sort(key=itemgetter(sort_by), reverse=sort_desc)
        paginator = Paginator(items, page_size)
        page_obj = paginator.page(page)
        items = page_obj.object_list
        count = paginator.count

        # Fetch batch details from DB
        batch_ids = [item["name"] for item in items]
        batch_detail = Batch.objects.filter(id__in=batch_ids, sub_path=sub_path).values(
            "id", "mode"
        )
        batch_dict = {batch["id"]: batch["mode"] for batch in batch_detail}

        for item in items:
            item["is_uploaded"] = item["name"] in batch_dict
            item["mode"] = batch_dict.get(item["name"], "")

        return Response({"items": items, "count": count})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def download_batch_zip(request):
    """
    Download a emailbatch zip file from Batches (storage)
    """
    try:
        batch_path = request.GET.get("batch_path")
        if batch_path is None or batch_path == "":
            return Response(
                {"detail": "batch_path parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            batch_path = _safe_join(BATCH_INPUT_PATH, batch_path)
        except ValueError:
            return Response(
                {"detail": "Invalid batch_path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not os.path.isdir(batch_path):
            return Response(
                {"detail": "batch_path should be valid dictionary."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        filenames = [os.path.join(batch_path, i) for i in os.listdir(batch_path)]
        batch_id = os.path.basename(batch_path)

        # There sould be atleast one xml or json file inside batch path
        xml_files_count = len([i for i in filenames if i.endswith(".xml")])
        json_files_count = len([i for i in filenames if i.endswith(".json")])
        if xml_files_count == 0 and json_files_count == 0:
            return Response(
                {"detail": "No xml or json files found inside batch_path."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_subdir = batch_id
        zip_filename = f"{zip_subdir}.zip"

        # Open BytesIO to grab in-memory ZIP contents
        s = io.BytesIO()

        # The zip compressor
        zf = zipfile.ZipFile(s, "w")

        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_subdir, fname)

            # Add file, at correct path
            zf.write(fpath, zip_path)

        # Must close zip for all contents to be written
        zf.close()

        # Grab ZIP file from in-memory
        resp = HttpResponse(s.getvalue())
        resp["Content-Type"] = "application/x-zip-compressed"
        resp["Content-Disposition"] = f"attachment; filename={zip_filename}"

        return resp

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def upload_batch_zip(request):
    """
    Upload emailbatch zip file to Batches (storage)
    """
    try:
        sub_path = request.POST.get("sub_path")
        replace_if_exists = request.POST.get("replace_if_exists")

        replace_if_exists = True if replace_if_exists == "true" else False

        try:
            zip_file = request.FILES["zip_file"]
        except:
            return Response(
                {"detail": "batch_path should be valid dictionary."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        zip_file_name = zip_file.name
        assert zip_file_name.endswith(".zip"), "zip file should be of zip format"

        batch_id = zip_file_name.replace(".zip", "")

        try:
            request_path = _safe_join(BATCH_INPUT_PATH, sub_path or "")
        except ValueError:
            return Response(
                {"detail": "Invalid sub_path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if batch already exists:
        if batch_id in os.listdir(request_path):
            if replace_if_exists:
                shutil.rmtree(os.path.join(request_path, batch_id))
            else:
                return Response(
                    {
                        "detail": f"Batch {batch_id} already exists at sub_path {sub_path}."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with zipfile.ZipFile(zip_file, "r") as zip:
            zip_items = zip.namelist()
            # File name can not have "/"
            valid_files = ["/" in i for i in zip_items]
            if False in valid_files:
                return Response(
                    {
                        "detail": "Invalid Zip file. Zip should contain folders at root level not files."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for item in zip_items:
                try:
                    _safe_join(request_path, item)
                except ValueError:
                    return Response(
                        {"detail": "Invalid Zip file. Zip contains invalid paths."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            zip.extractall(request_path)
            email_batch_id = zip_items[0].split("/")[0] if zip_items else None
            print(f"{email_batch_id=}")

            db_data_json = "db_data.json"
            root_db_data_json_path = os.path.join(email_batch_id, db_data_json)

            if root_db_data_json_path in zip_items:
                return Response(
                    {
                        "detail": "Invalid Zip file. The zip file you uploaded seems to be a Transaction not a Batch."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response({"detail": "Batch saved to disk"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def check_definitions_exist(request):
    """
    Check the definition exist in system or not.
    """
    try:
        try:
            definitions = request.data["definitions"]
        except:
            return Response(
                {"detail": "definitions is required field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exist = []
        doesnt_exist = []

        for d in definitions:
            if (
                Definition.objects.filter(definition_id__iexact=d["definition_id"])
                .filter(layout_id__iexact=d["layout_id"])
                .exists()
            ):
                exist.append(d)
            else:
                doesnt_exist.append(d)

        result = {"exist": exist, "doesnt_exist": doesnt_exist}

        return Response(result)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def import_definitions(request):
    """
    Import definitions.
    New definitions will be created.
    Existing definitions will be partially/fully updated based on user's selection
    """
    try:
        try:
            profile_name = request.data["profile_name"]
            vendors_to_update = request.data["vendors_to_update"]
            vendor_data = request.data["vendor_data"]
            update_settings = request.data["update_settings"]
        except:
            return Response(
                {
                    "detail": "Invalid payload. It must include, 'profile_name', 'vendors_to_update','vendor_data' and 'update_settings'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        definitions = [
            definition
            for definition in vendor_data
            if definition.get("vendor") in vendors_to_update
        ]

        for d in definitions:
            qs = Definition.objects.filter(
                definition_id__iexact=d["definition_id"]
            ).filter(layout_id__iexact=d["layout_id"])

            if qs.exists():
                # Update existing definitions
                instance = qs.first()

                # Update data field
                new_data = d["definition"].pop("data")
                instance_data = instance.data

                for i in update_settings:
                    version = i["version"]
                    if i["key"] is True and new_data.get(version, {}).get("key"):
                        instance_data.setdefault(version, {})
                        instance_data[version]["key"] = new_data[version]["key"]
                    if i["table"] is True and new_data.get(version, {}).get("table"):
                        instance_data.setdefault(version, {})
                        instance_data[version]["table"] = new_data[version]["table"]

                instance.data = instance_data

                # Update other fields
                # for attr, val in d.items():
                #     setattr(instance, attr, val)

                instance.save()

            else:
                d["data"] = d["definition"]
                d.pop("definition")
                # Create new definitions
                Definition.objects.create(**d)

        return Response({"detail": "Definitions imported"})

    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def export_definitions(request):
    """
    Export definitions using DefinitionResource
    """
    try:
        try:
            profile_name = request.data["profile_name"]
            vendors = request.data["vendors"]
        except:
            return Response(
                {
                    "detail": "Invalid payload. It must include, 'profile_name' and 'doc_types'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Definition.objects.filter(
            definition_id__iexact=profile_name, vendor__in=vendors
        ).order_by("created_at")

        exported_data = DefinitionSerializer(queryset, many=True).data
        definition_data = [
            {
                "definition_id": doc["definition_id"],
                "vendor": doc["vendor"],
                "type": doc["type"],
                "name_matching_text": doc["name_matching_text"],
                "created_at": doc["created_at"],
                "definition": {"data": doc["data"]},
                "cw1": doc["cw1"],
            }
            for doc in exported_data
        ]
        return Response({"vendor_data": definition_data, "profile_name": profile_name})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_verification_details(request, email_batch_id):
    """
    Get Data JSON details for selected email_batch for user verification
    """
    try:
        # Check if verification status is ready or submitted.
        email_batch = EmailBatch.objects.get(id=email_batch_id)
        verification_status = email_batch.verification_status
        profile = Profile.objects.get(name=email_batch.matched_profile_name)
        manual_validation = profile.manual_validation

        condition1 = manual_validation is True and verification_status in [
            "ready",
            "submitted",
        ]
        condition2 = (
            manual_validation is False and email_batch.assembly_triggered is True
        )

        if not (condition1 or condition2):
            return Response(
                {"detail": "Transaction is not available for review."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email_batches = list(
            EmailToBatchLink.objects.filter(email_id=email_batch_id).values_list(
                "batch_id", flat=True
            )
        )
        print(f"{email_batches=}")
        details = list(
            Batch.objects.filter(id__in=email_batches).values(
                "id", "data_json", "sub_path"
            )
        )

        details = [d for d in details if len(d["data_json"].keys()) != 0]

        response = {
            "verification_status": verification_status,
            "manual_validation": manual_validation,
            "batches_info": details,
        }
        return Response(response)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def save_verification_details(request, email_batch_id):
    """
    Save User Verified/Updated Data JSON details in DB.
    """
    try:
        request_data = request.data
        data = request_data["data"]

        for batch_item in data:
            batch_instance = Batch.objects.get(id=batch_item["id"])
            batch_instance.data_json = batch_item["data_json"]
            batch_instance.save(update_fields=["data_json"])

        return Response({"detail": "Transaction data updated."})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def release_transaction(request, email_batch_id):
    """
    Release user verified transaction for further processing.
    """
    try:
        request_data = {"email_batch_id": email_batch_id}
        publish("email_batch_validation_released", "to_pipeline", request_data)
        return Response({"detail": "Transaction validation completed."})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_manual_classification_data(request):
    """
    Release user verified transaction for further processing.
    """
    try:
        train_batch_id = request.GET.get("train_batch_id")
        train_batch_instance = TrainBatch.objects.get(id=train_batch_id)

        if train_batch_instance.manual_classification_status not in [
            "ready",
            "submitted",
        ]:
            return Response(
                {"detail": "Manual classification is not available for review."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile_instance = Profile.objects.get(
            name=train_batch_instance.matched_profile_name
        )

        profile_documents = profile_instance.documents.all()
        translated_doc_types = [
            td["doc_type"] for td in profile_instance.translated_documents
        ]
        filtered_doc_type = [
            doc.doc_type
            for doc in profile_documents
            if doc.category == "Processing" and doc.doc_type not in translated_doc_types
        ]

        data = {
            "manual_classification_status": train_batch_instance.manual_classification_status,
            "profile": train_batch_instance.matched_profile_name,
            "doc_types": filtered_doc_type,
            "data": train_batch_instance.manual_classification_data,
        }

        return Response(data)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_project_by_profile(profile_name):
    """
    Retrieves a project name based on the given profile name

    Args:
        profile_name (str): Profile Name

    Returns:
        project (str): Project Name

    Update History:
        Last Updated By: Nayem
        Last Updated At: 2024-11-27
    """
    project = None

    profile_qs = Profile.objects.filter(name=profile_name)
    if profile_qs.exists():
        project = profile_qs.first().project

    return project


@api_view(["POST"])
def test_manual_classification(request):
    """
    Release user verified transaction for further processing.
    """
    try:
        train_batch_id = request.data["train_batch_id"]
        profile = request.data["profile"]
        manual_classification_data = request.data["manual_classification_data"]
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'train_batch_id', 'profile' and 'manual_classification_data'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        train_batch = TrainBatch.objects.get(id=train_batch_id)
        file_identifiers = train_batch.file_identifiers
        category, memory_points, page_directions = (
            get_master_dictionaries_for_classifier()
        )

        # Add a new parameter project to request_body
        # Author: Nayem
        # Date: November 27, 2024
        project = get_project_by_profile(profile)
        ra_json_path = generate_ra_json_file_path(
            train_batch, manual_classification=True
        )

        # API call to Classifier
        URL = f"{CLASSIFIER_API_URL}/api/manual_classification/"

        request_body = {
            "profile": profile,
            "ra_json_paths": [ra_json_path],
            "project": project,
            "manual_classification_data": manual_classification_data,
            "file_identifiers": file_identifiers,
            "category": category,
            "memory_points": memory_points,
            "page_directions": page_directions,
            "test": True,
        }

        response = requests.post(URL, json=request_body)

        if response.status_code == 200:
            data = response.json()["data"]
            return Response(data)

        return Response(
            {"detail": "Classifier didn't send valid response"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def verify_manual_classification(request):
    """
    Release user verified transaction for further processing.
    """
    try:
        train_batch_id = request.data["train_batch_id"]
        profile = request.data["profile"]
        manual_classification_data = request.data.get(
            "manual_classification_data", None
        )
    except:
        return Response(
            {
                "detail": "Invalid payload. It must include 'train_batch_id' and 'profile'."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        train_batch = TrainBatch.objects.get(id=train_batch_id)
        if not manual_classification_data:
            manual_classification_data = train_batch.manual_classification_data
        file_identifiers = train_batch.file_identifiers
        category, memory_points, page_directions = (
            get_master_dictionaries_for_classifier()
        )

        # Add a new parameter project to request_body
        # Author: Nayem
        # Date: November 27, 2024
        project = get_project_by_profile(profile)
        ra_json_path = generate_ra_json_file_path(
            train_batch, manual_classification=True
        )

        # API call to Classifier
        URL = f"{CLASSIFIER_API_URL}/api/manual_classification/"

        request_body = {
            "profile": profile,
            "ra_json_paths": [ra_json_path],
            "project": project,
            "manual_classification_data": manual_classification_data,
            "file_identifiers": file_identifiers,
            "category": category,
            "memory_points": memory_points,
            "page_directions": page_directions,
        }

        response = requests.post(URL, json=request_body)

        if response.status_code == 200:
            data = response.json()["data"]
            train_batch.manual_classification_data = data
            train_batch.manual_classification_status = "submitted"

            train_batch.save()

            profile_qs = Profile.objects.filter(name=profile)

            if profile_qs.exists():
                profile_documents_dict, *tail = get_profile_doc_info(profile_qs.first())

                matched_docs = []
                doc_type_index_dict = {}
                prev_doc_type = None

                for item in data:
                    doc_type = item["auto_classified_doc_type"]
                    image_file = item["image_file"]

                    if item["name_matching_doc_type"]:
                        doc_type = item["name_matching_doc_type"]

                    if item["user_classified_doc_type"]:
                        doc_type = item["user_classified_doc_type"]

                    if doc_type_index_dict.get(doc_type):
                        doc_type_index = doc_type_index_dict[doc_type]
                    else:
                        doc_type_index_dict[doc_type] = 1
                        doc_type_index = 1

                    if (prev_doc_type is not None and prev_doc_type != doc_type) or (
                        item.get("start_index") and item.get("start_index") == 1
                    ):
                        doc_type_index += 1
                        doc_type_index_dict[doc_type] = doc_type_index

                    matched_doc = profile_documents_dict.get(doc_type, None)

                    matched_docs.append(
                        {
                            "doc_type": doc_type,
                            "doc_type_index": doc_type_index,
                            "matched_doc": matched_doc,
                            "image_file": image_file,
                            "name_matching_text": (
                                matched_doc.name_matching_text if matched_doc else ""
                            ),
                        }
                    )

                    prev_doc_type = doc_type

                matched_docs = convert_doc_instance_to_dict(matched_docs)

                job_id = train_batch.job_id

                job_info = redis_instance.get(job_id)
                job_info = json.loads(job_info)
                job_info["matched_doc"] = matched_docs

                redis_instance.set(job_id, json.dumps(job_info))

                request_data = {"job_id": job_id}
                publish(
                    "continue_classification_process_queued",
                    "to_pipeline",
                    request_data,
                )

                return Response(
                    {
                        "detail": "Manual classification completed",
                    }
                )

        return Response(
            {"detail": "Classifier didn't send valid response"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as error:
        trace = traceback.format_exc()
        print(f"{trace=}")
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def restructure_ra_json_and_extract_file_identifiers(ra_json_path):
    """Extract file identifiers from ra_json"""
    try:
        with open(ra_json_path, "r") as file:
            ra_json = json.load(file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    nodes = ra_json.get("nodes", [])

    if nodes:
        pages = nodes[0].get("children", [])
        file_identifiers = [(1, len(pages))]

        return file_identifiers

    pages = ra_json.get("pages", [])

    file_identifiers = [(1, len(pages))]

    ra_json = {
        "nodes": [
            {
                "ext": ".pdf",
                "type": "document",
                "children": pages,
                "file_path": "",
            }
        ]
    }

    with open(ra_json_path, "w") as file:
        json.dump(ra_json, file)

    return file_identifiers


def get_auto_classified_doc_types_custom(ra_json_path):
    """
    Automatically classifies the doc type with the help of a matrix classifier.
    """
    file_identifiers = restructure_ra_json_and_extract_file_identifiers(ra_json_path)
    category, memory_points, page_directions = get_master_dictionaries_for_classifier()
    # API call to Classifier
    URL = f"{CLASSIFIER_API_URL}/api/title_classification/"
    request_body = {
        "layout_xml_paths": [ra_json_path],
        "page_directions": page_directions,
        "profile": "",
        "project": "",
        "category": category,
        "memory_points": memory_points,
        "file_identifiers": file_identifiers,
        "automatic_splitting": True,
    }
    print("Calling classifier API...")
    response = requests.post(URL, json=request_body)
    if response.status_code == 200:
        response_json = response.json()
        return response_json
    return {}


@api_view(["POST"])
def classify_batch_sync(request):
    """Handle batch classification request"""
    print("Request received for classifying batch...")
    try:
        batch_id = request.data.get("batch_id")
        if batch_id is None:
            return Response(
                {"detail": "Invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
            )
        sub_path = request.data.get("sub_path", "")
        try:
            batch_path = _safe_join(BATCH_INPUT_PATH, sub_path, batch_id)
        except ValueError:
            return Response(
                {"detail": "Invalid sub_path"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ra_json_path = os.path.join(batch_path, "ra_json.json")
        if not os.path.exists(batch_path) or not os.path.exists(ra_json_path):
            return Response(
                {"detail": f"Batch or ra_json not found at path {batch_path}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        files = sorted(os.listdir(batch_path))
        classifier_api_response = get_auto_classified_doc_types_custom(ra_json_path)
        # Process the results
        result = {}
        for key, value in classifier_api_response["doctypes"].items():
            for v in value:
                for i in range(v[0], v[1] + 1):
                    result[i] = key
        tiff_file_names = [i for i in files if i.endswith(".tif")]
        classification_result = []
        for index, file_name in enumerate(tiff_file_names):
            try:
                classified_type = result[index + 1]
            except KeyError:
                classified_type = ""

            classification_result.append(
                {"tiff_image": file_name, "classified_type": classified_type}
            )

        # Remove the batch after classification
        remove_batch = request.data.get("remove_batch", False)
        if classification_result and remove_batch:
            shutil.rmtree(batch_path)

        return Response({"data": classification_result})

    except Exception as error:
        traceback.print_exc()
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_transaction_batches(request):
    transaction_id = request.GET.get("transaction_id")
    is_training = request.GET.get("is_training", "false").lower() == "true"
    batch_id = request.GET.get("batch_id")

    if not transaction_id:
        return Response(
            {"detail": "Missing 'transaction_id' parameter."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        if is_training:
            transaction = TrainBatch.objects.get(id=transaction_id)
            profile_name = transaction.matched_profile_name
            batch_ids = TrainToBatchLink.objects.filter(
                train_batch=transaction, mode="training", uploaded=True
            ).values_list("batch_id", flat=True)
        else:
            transaction = EmailBatch.objects.get(id=transaction_id)
            profile_name = transaction.matched_profile_name
            batch_ids = EmailToBatchLink.objects.filter(
                email=transaction, mode="processing", uploaded=True
            ).values_list("batch_id", flat=True)
    except (TrainBatch.DoesNotExist, EmailBatch.DoesNotExist):
        return Response(
            {"detail": f"Transaction with ID '{transaction_id}' doesn't exist."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    filtered_batch_ids = deepcopy(batch_ids)

    if batch_id:
        filtered_batch_ids = [batch_id] if batch_id in batch_ids else []
    elif transaction_id.startswith("multi_"):
        filtered_batch_ids = [batch_ids[0]] if len(batch_ids) else []

    batches = Batch.objects.filter(id__in=filtered_batch_ids)

    batches_results = []
    for batch in batches:
        batches_results.append(
            {
                "id": batch.id,
                "profile": profile_name,
                "sub_path": batch.sub_path,
                "vendor": batch.vendor,
                "status": batch.status,
                "document_types": batch.type,
                "data_json": batch.data_json,
                "project": batch.project,
                "is_dataset_batch": batch.is_dataset_batch,
                "layout_ids": batch.layout_ids,
            }
        )
    return Response(
        {
            "transaction_id": transaction_id,
            "profile": profile_name,
            "batches": batches_results,
            "batch_ids": batch_ids,
        }
    )


@api_view(["PUT"])
def update_batch(request):
    data = request.data
    batch_id = data.get("batch_id")
    data_json = data.get("data_json")
    if not batch_id:
        return Response(
            {"detail": "Missing payload `batch_id`."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if data_json is None:
        return Response(
            {"detail": "Missing payload `data_json`."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        batch_instance = Batch.objects.get(id=batch_id)
    except Batch.DoesNotExist as _e:
        return Response({"detail": str(_e)}, status=status.HTTP_404_NOT_FOUND)

    try:
        batch_instance.data_json = data.get("data_json")
        batch_instance.save()
        response = {
            "id": batch_instance.id,
            "data_json": batch_instance.data_json,
        }
        return Response({"data": response}, status=status.HTTP_200_OK)
    except Exception as _e:
        return Response(
            {"detail": str(_e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# @api_view(["POST"])
# def get_ra_json_from_pdf(request):
#     file = request.data.get("file", None)
#     if file is None:
#         return Response(
#             {"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
#         )

#     if file.content_type != "application/pdf" and not file.name.lower().endswith(
#         ".pdf"
#     ):
#         return Response(
#             {"error": "The uploaded file must be a PDF."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
#     is_electronic = is_electronic_pdf(file, False)
#     if not is_electronic:
#         return Response(
#             {"error": "The uploaded file must be an Electronic PDF."},
#             status=status.HTTP_400_BAD_REQUEST,
#         )
#     ra_json = extract_ra_json_from_pdf(file)
#     return Response({"data": ra_json})


@api_view(["POST"])
def semantic_address_match(request):
    try:
        request_data = request.data
        token = get_ddh_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        search_url = f"{DDH_BASE_URL}/api/semantic-address-match"

        response = requests.post(search_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def process_dataset_batches(response_json):
    print("Trigger process_dataset_batches")
    job_id = response_json["job_id"]
    job_info = redis_instance.get(job_id)
    job_info = json.loads(job_info)

    train_batch_id = job_info["train_batch_id"]
    linked_batches = job_info["linked_batches"]

    train_batch = TrainBatch.objects.get(id=train_batch_id)

    write_parent_batch_log(
        batch_id=train_batch_id,
        status="inprogress",
        message="Creation of linked batches initiated.",
        train_batch_log=True,
    )

    project = None

    if train_batch:
        project = get_project_by_profile(train_batch.matched_profile_name)

        if not project:
            project = Project.objects.first()

    selected_dataset_batches, selected_dataset_batches_path = (
        get_selected_dataset_batches_info()
    )

    for linked_batch in linked_batches:
        linked_batch_id = linked_batch["id"]
        sub_path = linked_batch.get("sub_path", "")
        vendor = linked_batch.get("vendor", "")
        # project = linked_batch.get("project", "")
        process = linked_batch.get("process", "")
        document_types = linked_batch.get("document_types", [])
        document_types = document_types[0] if document_types else ""

        batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, sub_path, linked_batch_id)

        ra_json = load_json_file(os.path.join(batch_path, "ra_json.json"))
        data_json = load_json_file(os.path.join(batch_path, "data_json.json"))
        ra_json = restructure_ra_json(
            ra_json, linked_batch_id, process, project, vendor, document_types
        )
        data_json = restructure_data_json(
            data_json, linked_batch_id, process, project, vendor, document_types
        )

        Batch.objects.filter(id=linked_batch_id).delete()
        TrainToBatchLink.objects.filter(batch_id=linked_batch_id).delete()

        Batch.objects.create(
            id=linked_batch_id,
            is_dataset_batch=True,
            type=document_types,
            mode="training",
            vendor=vendor,
            sub_path=sub_path,
            extension=".pdf",
            definition_id=process,
            project=project,
            ra_json=ra_json,
            data_json=data_json,
            visible=True,
            status="completed",
        )

        details = {
            "batch_id": linked_batch_id,
            "parent_batch_id": train_batch_id,
        }

        write_parent_batch_log(
            batch_id=train_batch_id,
            status="inprogress",
            message="Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
            train_batch_log=True,
        )

        TrainToBatchLink.objects.create(
            train_batch=train_batch,
            batch_id=linked_batch_id,
            mode="training",
            uploaded=True,
            classified=True,
        )
        selected_dataset_batches.append(linked_batch_id)

        request_data = {"batch_id": linked_batch_id}

        write_batch_log(
            batch_id=linked_batch_id,
            status="queued",
            message="Batch added to queue for processing",
        )

        publish("batch_queued", "to_pipeline", request_data)

    with open(selected_dataset_batches_path, "w") as json_file:
        json.dump(selected_dataset_batches, json_file, indent=2)

    write_parent_batch_log(
        batch_id=train_batch_id,
        status="inprogress",
        message="Creation of linked batches completed",
        train_batch_log=True,
    )

    write_parent_batch_log(
        batch_id=train_batch_id,
        status="inprogress",
        message="Creating training dataset batch completed",
        train_batch_log=True,
    )


@api_view(["POST"])
def create_training_dataset_batch(request):
    try:
        request_data = request.data

        linked_batches = request_data.get("linked_batches", [])
        process_name = request_data.get("process_name")

        if len(linked_batches) == 0:
            return Response(
                {"error": "linked_batches cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        parent_batch_id = get_new_email_batch_id(training=True, manual=True)

        prepare_parent_batch_path(parent_batch_id, "train-batches")

        if not process_name:
            process_name = linked_batches[0]["process"] if len(linked_batches) else ""

            if not process_name:
                latest_profile = Profile.objects.order_by("-created_at").first()
                process_name = latest_profile.name if latest_profile else ""

        train_batch = TrainBatch.objects.create(
            id=parent_batch_id, status="inprogress", matched_profile_name=process_name
        )

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message="Creating Training Dataset Batch",
            train_batch_log=True,
        )

        job_id = gerenate_job_id_for_batch(train_batch.id)

        job_details = {
            "train_batch_id": train_batch.id,
            "linked_batches": linked_batches,
        }

        redis_instance.set(job_id, json.dumps(job_details))

        request_body = {"job_id": job_id}

        publish("process_dataset_batches", "to_pipeline", request_body)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message="Message published to create linked batches",
            remarks=json.dumps(job_details),
            action="display_json",
            train_batch_log=True,
        )

        return Response({"train_batch_id": parent_batch_id}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_annotation_batches(request):
    try:
        page_size = request.query_params.get("page_size")
        page = request.query_params.get("page")
        sort_by = request.query_params.get("sort_by")
        sort_desc = request.query_params.get("sort_desc")
        id = request.query_params.get("id")
        vendor = request.query_params.get("vendor")
        process = request.query_params.get("process")
        document_types = request.query_params.get("document_types")
        entities = request.query_params.get("entities")
        language = request.query_params.get("language")
        notes = request.query_params.get("notes")

        params = {
            "page_size": page_size,
            "page": page,
            "sort_by": sort_by,
            "sort_desc": sort_desc,
            "id": id,
            "vendor": vendor,
            "process": process,
            "document_types": document_types,
            "entities": entities,
            "language": language,
            "notes": notes,
            "selected_dataset_list_file": SELECTED_DATASET_LIST_FILE,
        }

        token = get_annotation_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{ANNOTATION_BASE_URL}/api/batches"

        response = requests.get(url, headers=headers, params=params)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def start_transaction_process(request_data):
    """This function is responsible for starting the transaction process via input channel"""
    try:
        file_path = request_data["file_path"]
        input_channel = request_data["input_channel"]
        project = request_data["project"]
        job_id = request_data["job_id"]

        input_file_path = os.path.join(INPUT_FILES_PATH, file_path)

        batch_id = get_new_email_batch_id()
        batch_path = prepare_parent_batch_path(batch_id)
        profile_name = ""

        batch_instance = EmailBatch.objects.create(id=batch_id)
        save_analyzer_log_time(batch_id=batch_id, field_name="transaction_uploading_s")

        remarks = {"Source": input_channel.capitalize(), "Project": project}
        write_parent_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Received file from input channel",
            remarks=json.dumps(remarks),
            action="display_key_values",
        )
        input_data = {"job_id": job_id, "batch_id": batch_id}
        publish("input_process_started", "to_input_channel", input_data)

        file_name = os.path.basename(input_file_path)
        file_name = remove_null_characters(file_name)
        file_base_name, extension = os.path.splitext(file_name)

        if extension.lower() in [".eml", ".msg"]:
            upload_type = "email"
            file_name = f"email_file{extension}"
            file_path = os.path.join(batch_path, file_name)
            shutil.move(input_file_path, file_path)
        else:
            batch_instance.email_from = "Input Channel"
            batch_instance.email_subject = input_channel.capitalize()
            batch_instance.save()

            file_path = os.path.join(batch_path, file_name)
            shutil.move(input_file_path, file_path)

            if extension.lower() in [".doc", ".docx"]:
                upload_type = "word"
            elif extension.lower() in [".xls", ".xlsx"]:
                upload_type = "excel"
                if extension.lower() == ".xls":
                    # Convert xls file to xlsx
                    if validate_xls_file(file_path):
                        xlsx_filename = file_base_name + ".xlsx"
                        xlsx_filepath = os.path.join(batch_path, xlsx_filename)

                        convert_xls_to_xlsx(file_path, xlsx_filepath)

                        if os.path.exists(file_path):
                            os.remove(file_path)
                    else:
                        print(f"Error: {file_name} is not a valid XLS file.")

            elif extension.lower() == ".pdf":
                upload_type = "pdf"

            process_id = file_base_name.split("_")[0]
            profile_instance = Profile.objects.filter(process_id=process_id)
            if not profile_instance.exists():
                remarks = {"File Name": file_name, "Process ID": process_id}
                write_parent_batch_log(
                    batch_id=batch_id,
                    status="failed",
                    message="Process ID doesn't exist",
                    remarks=json.dumps(remarks),
                    action="display_key_values",
                )
                return

            profile_name = profile_instance.first().name

        write_parent_batch_log(
            batch_id=batch_id,
            status="upload",
            message="Uploading new Transaction",
        )
        request_data = {
            "batch_id": batch_id,
            "batch_path": batch_path,
            "profile_name": profile_name,
            "upload_type": upload_type,
        }
        publish("email_batch_queued", "to_pipeline", request_data)

        save_analyzer_log_time(batch_id=batch_id, field_name="time_to_queued")
        write_parent_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Transaction Added to Queue for Processing",
        )
        save_analyzer_log_time(batch_id=batch_id, field_name="transaction_uploading_e")

    except Exception as error:
        print(error)
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def start_training_process(request_data):
    """This function is responsible for starting the training process via input channel"""
    try:
        file_path = request_data["file_path"]
        input_channel = request_data["input_channel"]
        project = request_data["project"]
        job_id = request_data["job_id"]

        input_file_path = os.path.join(INPUT_FILES_PATH, file_path)

        parent_batch_id = get_new_email_batch_id(training=True)
        batch_path = prepare_parent_batch_path(parent_batch_id, "train-batches")

        TrainBatch.objects.create(id=parent_batch_id)

        remarks = {"Source": input_channel.capitalize(), "Project": project}
        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="queued",
            message="Received file from input channel",
            remarks=json.dumps(remarks),
            action="display_key_values",
            train_batch_log=True,
        )
        input_data = {"job_id": job_id, "batch_id": parent_batch_id}
        publish("input_process_started", "to_input_channel", input_data)

        file_name = os.path.basename(input_file_path)
        file_name = remove_null_characters(file_name)
        file_path = os.path.join(batch_path, file_name)

        shutil.move(input_file_path, file_path)

        file_base_name, extension = os.path.splitext(file_name)
        process_id = file_base_name.split("_")[0]
        profile_instance = Profile.objects.filter(process_id=process_id)

        if not profile_instance.exists():
            remarks = {"File Name": file_name, "Process ID": process_id}
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message="Process ID doesn't exist",
                remarks=json.dumps(remarks),
                action="display_key_values",
                train_batch_log=True,
            )
            return

        profile_name = profile_instance.first().name
        profile_docs = ProfileDocument.objects.filter(profile__name=profile_name)

        if not profile_docs.exists():
            remarks = {"Process": profile_name}
            write_parent_batch_log(
                batch_id=parent_batch_id,
                status="failed",
                message="No documents found in the process",
                remarks=json.dumps(remarks),
                action="display_key_values",
                train_batch_log=True,
            )
            return

        doc_ids = list(profile_docs.values_list("id", flat=True))

        if extension.lower() in [".eml", ".msg"]:
            upload_type = "email"
        elif extension.lower() in [".doc", ".docx"]:
            upload_type = "word"
        elif extension.lower() in [".xls", ".xlsx"]:
            upload_type = "excel"
        elif extension.lower() == ".pdf":
            upload_type = "pdf"

        request_data = {
            "parent_batch_id": parent_batch_id,
            "upload_type": upload_type,
            "batch_path": batch_path,
            "doc_ids": doc_ids,
        }

        publish("train_batch_queued", "to_pipeline", request_data)

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="queued",
            message="Training batch added to queue for processing",
            train_batch_log=True,
        )

    except Exception as error:
        print(error)
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def test_graph_config(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/test_graph_config/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def test_imap_config(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/test_imap_config/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_service_logs(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/get_service_logs/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_sharepoint_sites(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/get_sharepoint_sites/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_sharepoint_drive(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/get_sharepoint_drive/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_onedrive_folder(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/get_onedrive_folder/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_drive_folder(request):
    try:
        request_data = request.data
        token = get_input_channel_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        test_url = f"{INPUT_CHANNEL_BASE_URL}/api/get_drive_folder/"

        response = requests.post(test_url, headers=headers, json=request_data)

        return Response(response.json(), status=response.status_code)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def process_transaction(request):
    """
    Send files to start the Transaction process
    Set new batch ID and prepare batch path for it
    """
    try:
        print("Request received for uploading file in transaction...")

        testing = request.POST.get("testing", False)
        if testing:
            batch_id = get_new_email_batch_id()
            return Response(
                {
                    "detail": "Transaction uploaded successfully and queued for processing",
                    "transaction_batch_id": batch_id,
                }
            )

        files = request.FILES.getlist("files")
        process_id = request.POST.get("process_id").strip()

        if not files:
            print("400 RESPONSE WILL BE SENT as file is not valid")
            return Response(
                {"detail": "invalid files"}, status=status.HTTP_400_BAD_REQUEST
            )

        upload_types = []
        for file in files:
            file_name = file.name
            file_base_name, extension = os.path.splitext(file_name)

            if extension.lower() in [".eml", ".msg"]:
                if "email" not in upload_types:
                    upload_types.append("email")
            elif extension.lower() in [".doc", ".docx"]:
                if "word" not in upload_types:
                    upload_types.append("word")
            elif extension.lower() in [".xls", ".xlsx"]:
                if "excel" not in upload_types:
                    upload_types.append("excel")
            elif extension.lower() == ".pdf":
                if "pdf" not in upload_types:
                    upload_types.append("pdf")

        if not upload_types:
            return Response(
                {"detail": "No valid file type found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(upload_types) > 1:
            return Response(
                {"detail": "More than one file type found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload_type = upload_types[0]

        if upload_type == "email" and len(files) > 1:
            return Response(
                {"detail": "More than one email file found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        batch_id = get_new_email_batch_id()
        save_analyzer_log_time(batch_id=batch_id, field_name="transaction_process_s")

        batch_path = prepare_parent_batch_path(batch_id)
        batch_instance = EmailBatch.objects.create(id=batch_id)

        batch_instance.email_from = "API Upload"
        batch_instance.email_subject = "API Upload"
        batch_instance.save()

        process_name = ""
        if upload_type != "email":
            process_instance = Profile.objects.filter(process_id=process_id)
            if not process_instance.exists():
                message = "Process ID doesn't exist"
                remarks = {"Process ID": process_id}
                write_parent_batch_log(
                    batch_id=batch_id,
                    status="failed",
                    message=message,
                    remarks=json.dumps(remarks),
                    action="display_key_values",
                )
                return Response(
                    {"detail": message},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            process_name = process_instance.first().name

        for index, file in enumerate(files):
            if index != 0 and upload_type == "email":
                break

            file_name = file.name
            file_name = remove_null_characters(file_name)
            file_base_name, extension = os.path.splitext(file_name)

            if upload_type == "email":
                file_name = f"email_file{extension}"

            file_path = os.path.join(batch_path, file_name)

            # save file to disk
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            if extension.lower() == "xls":
                # Convert xls file to xlsx
                if validate_xls_file(file_path):
                    xlsx_filename = file_base_name + ".xlsx"
                    xlsx_filepath = os.path.join(batch_path, xlsx_filename)

                    convert_xls_to_xlsx(file_path, xlsx_filepath)

                    if os.path.exists(file_path):
                        os.remove(file_path)
                else:
                    print(f"Error: {file_name} is not a valid XLS file.")

        write_parent_batch_log(
            batch_id=batch_id,
            status="upload",
            message="Uploading new Transaction",
        )
        request_data = {
            "batch_id": batch_id,
            "batch_path": batch_path,
            "profile_name": process_name,
            "upload_type": upload_type,
        }
        publish("email_batch_queued", "to_pipeline", request_data)

        save_analyzer_log_time(batch_id=batch_id, field_name="time_to_queued")
        write_parent_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Transaction Added to Queue for Processing",
        )
        save_analyzer_log_time(batch_id=batch_id, field_name="transaction_uploading_e")

        return Response(
            {
                "detail": "Transaction uploaded successfully and queued for processing",
                "transaction_batch_id": batch_id,
            }
        )

    except Exception as error:
        print(str(error))
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def process_training(request):
    """
    Send files to start the Training process
    Set new batch ID and prepare batch path for it
    """
    try:
        testing = request.POST.get("testing", False)
        if testing:
            batch_id = get_new_email_batch_id(training=True)
            return Response(
                {
                    "detail": "Training batch added to queue for processing",
                    "train_batch_id": batch_id,
                }
            )

        files = request.FILES.getlist("files")
        process_id = request.POST.get("process_id").strip()

        if not files:
            print("400 RESPONSE WILL BE SENT as file is not valid")
            return Response(
                {"detail": "invalid files"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not process_id:
            return Response(
                {"detail": "'process_id' required"}, status=status.HTTP_400_BAD_REQUEST
            )

        upload_types = []
        for file in files:
            file_name = file.name
            file_base_name, extension = os.path.splitext(file_name)

            if extension.lower() in [".eml", ".msg"]:
                if "email" not in upload_types:
                    upload_types.append("email")
            elif extension.lower() in [".doc", ".docx"]:
                if "word" not in upload_types:
                    upload_types.append("word")
            elif extension.lower() in [".xls", ".xlsx"]:
                if "excel" not in upload_types:
                    upload_types.append("excel")
            elif extension.lower() == ".pdf":
                if "pdf" not in upload_types:
                    upload_types.append("pdf")

        if not upload_types:
            return Response(
                {"detail": "No valid file type found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(upload_types) > 1:
            return Response(
                {"detail": "More than one file type found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        upload_type = upload_types[0]
        batch_id = get_new_email_batch_id(training=True)

        write_parent_batch_log(
            batch_id=batch_id,
            status="upload",
            message="Uploading new Training batch",
            train_batch_log=True,
        )

        process_name = ""
        process_instance = Profile.objects.filter(process_id=process_id)
        if not process_instance.exists():
            message = "Process ID doesn't exist"
            write_parent_batch_log(batch_id=batch_id, status="failed", message=message)
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        process_name = process_instance.first().name
        process_docs = ProfileDocument.objects.filter(profile__name=process_name)

        if not process_docs.exists():
            message = ("No documents found in the process",)
            remarks = {"Process": process_name}
            write_parent_batch_log(
                batch_id=batch_id,
                status="failed",
                message=message,
                remarks=json.dumps(remarks),
                action="display_key_values",
                train_batch_log=True,
            )
            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doc_ids = list(process_docs.values_list("id", flat=True))
        batch_path = prepare_parent_batch_path(batch_id, "train-batches")

        save_file_to_parent_folder(files, batch_path, upload_type)

        request_data = {
            "parent_batch_id": batch_id,
            "upload_type": upload_type,
            "batch_path": batch_path,
            "doc_ids": doc_ids,
        }

        TrainBatch.objects.create(id=batch_id)

        publish("train_batch_queued", "to_pipeline", request_data)

        write_parent_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Training batch added to queue for processing",
            train_batch_log=True,
        )

        return Response(
            {
                "detail": "Training batch added to queue for processing",
                "train_batch_id": batch_id,
            }
        )
    except IntegrityError:
        print(traceback.format_exc())
        return Response(
            {"detail": "Training batch with provided ID already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as error:
        print(str(error))
        return Response(
            {"detail": str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def get_test_json(request):
    try:
        project = request.data.get("project")
        if not project:
            return Response(
                {"detail": "Missing payload 'project'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project_qs = Project.objects.filter(name=project)
        if not project_qs.exists():
            return Response(
                {"detail": "Project not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project_settings = project_qs.first().settings
        key_items = (
            project_settings.get("options", {}).get("options-keys", {}).get("items", [])
        )
        compound_items = project_settings.get("compoundKeys", [])

        test_json = {}
        if key_items:
            table_keys = {}
            for key in key_items:
                if key.get("required"):
                    key_value = key["keyValue"]

                    example = key.get("example")
                    if not example:
                        max_length = key.get("maxLength")
                        if max_length:
                            example = "".join(
                                random.choices(string.ascii_uppercase, k=max_length)
                            )

                    if key["type"] == "key":
                        test_json[key_value] = example
                    elif key["type"] == "table":
                        table_keys[key_value] = example
                    elif key["type"] == "addressBlock":
                        test_json[key_value] = {}

                    elif key["type"] == "compound":
                        key_label = key["keyLabel"]
                        compound_key = {}
                        for c_key in compound_items:
                            if c_key["name"] == key_label:
                                ckey_items = c_key["keyItems"]

                                for child in ckey_items:
                                    if child["type"] == "key":
                                        child_key = child["keyValue"]
                                        example = child.get("example")

                                        if not example:
                                            max_length = child.get("maxLength")
                                            if max_length:
                                                example = "".join(
                                                    random.choices(
                                                        string.ascii_uppercase,
                                                        k=max_length,
                                                    )
                                                )
                                        compound_key[child_key] = example

                        test_json[key_value] = compound_key

            if table_keys:
                test_json["goodsLines"] = [table_keys]

        return Response({"test_json": test_json}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def test_output_connection(request):
    """Test Output API connection"""
    try:
        request_data = request.data
        test_json = request_data.get("test_json")
        auth_type = request_data.get("auth_type")

        if auth_type == "oauth2":
            request_data["token"] = ""
            request_data["token_expires_at"] = ""

        channel_obj = type("channel", (), request_data)()
        response = OutputChannels(channel_obj).send_json(final_json=test_json)

        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("application/json"):
            try:
                response_message = response.json()
            except ValueError:
                response_message = response.text
            if response.status_code in [200, 400]:
                return Response(
                    {
                        "success": True,
                        "message": "Connected successfully!",
                        "response": response_message,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            response_message = response.text

        return Response(
            {
                "success": False,
                "message": "Connection failed!",
                "response": response_message,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as ex:
        return Response(
            {
                "success": False,
                "message": "Request failed!",
                "error": str(ex),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def qdrant_vector_db(request):
    try:
        request_data = request.data
        endpoint = request.query_params.get("endpoint")
        request_type = request.query_params.get("request_type", "").upper()
        party_table = request.query_params.get("party_table", False)
        process_name = request.query_params.get("process_name", "")

        ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        if request_type not in ALLOWED_METHODS:
            return Response(
                {"detail": "Invalid request_type"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not endpoint:
            return Response(
                {"detail": "endpoint is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if party_table:
            party_table_config = MasterDictionary.objects.get(
                name="partyTableConfig"
            ).data
            if not party_table_config:
                raise ValueError(f" MasterDictionary is not updated!")

            process_columns = {}
            process_instance = Profile.objects.filter(name=process_name).first()
            if process_instance:
                parties_config = process_instance.parties_config
                for config in parties_config:
                    table = config["table"]
                    process_columns[table] = config["columns"]

            party_table_config["processColumns"] = process_columns
            request_data["party_table_config"] = party_table_config

        endpoint_url = f"{QDRANT_VECTOR_DB_BASE_URL}/{endpoint}"
        print("Calling:", request_type, endpoint_url)

        # Check if the request contains file uploads
        has_files = bool(request.FILES)

        if has_files:
            # Handle file upload - send as multipart/form-data
            files = {}
            for key, file_obj in request.FILES.items():
                files[key] = (file_obj.name, file_obj.read(), file_obj.content_type)

            form_data = {}
            if hasattr(request, "POST"):
                for key in request.POST:
                    values = request.POST.getlist(key)
                    if len(values) == 1:
                        form_data[key] = values[0]
                    else:
                        form_data[key] = values
            else:
                for key, value in request_data.items():
                    if key in request.FILES:
                        continue
                    form_data[key] = value
            for key, value in list(form_data.items()):
                if isinstance(value, (dict, list)):
                    form_data[key] = json.dumps(value)
                elif value is None:
                    form_data[key] = ""

            response = _session.request(
                method=request_type,
                url=endpoint_url,
                files=files,
                data=form_data,
                timeout=300,
            )
        else:
            # Handle regular JSON data
            headers = {"Content-Type": "application/json"}
            json_data = request_data if request_type != "DELETE" else None

            response = _session.request(
                method=request_type,
                url=endpoint_url,
                json=json_data,
                headers=headers,
                timeout=300,
            )

        # Check if response is a file download (CSV, Excel, etc.)
        content_type = response.headers.get("content-type", "")
        is_file_download = any(
            ct in content_type.lower()
            for ct in [
                "text/csv",
                "application/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/octet-stream",
            ]
        )

        if is_file_download:
            # Return raw file content without JSON serialization
            django_response = HttpResponse(
                response.content, status=response.status_code, content_type=content_type
            )
            # Copy headers like content-disposition
            if "content-disposition" in response.headers:
                django_response["Content-Disposition"] = response.headers[
                    "content-disposition"
                ]
            return django_response
        else:
            # Handle regular JSON responses
            try:
                response_data = response.json()
            except:
                response_data = response.text

            return Response(response_data, status=response.status_code)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_spreadjs_license(request):
    """
    Returns the GrapeCity SpreadJS license key.
    This endpoint is used by the frontend to initialize the SpreadJS library.
    """
    return Response({"license_key": settings.GRAPECITY_SPREADJS_LICENSE})
