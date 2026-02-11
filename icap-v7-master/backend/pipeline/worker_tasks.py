import sys
import os
import json
import traceback
import redis
from typing import Callable
from pathlib import Path

import requests
from django.conf import settings

from pipeline.utils.process_batch_utils import (
    gerenate_job_id_for_batch,
    get_new_batch_id,
    write_batch_log,
    write_parent_batch_log,
    write_failed_log,
    prepare_parent_batch_path,
    get_ocr_engine_type,
)
from pipeline.utils.convert_excel_or_doc_to_pdf import (
    convert_excel_or_doc_to_pdf,
    EXCEL_FORMATS,
)
from pipeline.utils.electronic_pdf import process_files

# from pipeline.utils.detect_pdf import is_electronic_pdf
from pipeline.scripts.DataCap import DataCap
from pipeline.scripts.RAJson import RAJson
from utils.classification_utils import (
    get_instance_classes,
    join_with_escaped_commas,
    get_project_by_profile,
    match_attachment,
    get_profile_doc_info,
    is_excel_read_only,
    post_classification_process,
    convert_doc_instance_to_dict,
    load_doc_instance_from_dict,
)
from utils.utils import (
    get_default_barcode,
    get_default_page_rotate,
    get_default_language,
    get_default_ocr,
    create_inmemory_file,
    generate_datacap_page_file,
    generate_copy_batches_xml,
)
from rabbitmq_producer import publish
from core.models import (
    Batch,
    EmailBatch,
    EmailParsedDocument,
    TrainBatch,
    TrainParsedDocument,
)
from dashboard.models import Profile

# Settings
BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
CLASSIFIER_API_URL = settings.CLASSIFIER_API_URL

SELECTED_DATASET_LIST_FILE = os.getenv("SELECTED_DATASET_LIST_FILE")

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)


def process_pdfs_and_docs_p1(
    parent_batch, matched_profile, files_data, batch_upload_mode
):
    """
    Process PDFs and documents - Phase 1: Categorize PDFs via API
    """
    batch_id = None
    file_paths = [i["file_path"] for i in files_data]
    pdf_files = [
        file_path for file_path in file_paths if file_path.lower().endswith(".pdf")
    ]
    files_for_ocr = [
        file_path
        for file_path in file_paths
        if file_path.lower().endswith((".doc", ".docx"))
    ]
    # Generate job ID for tracking
    job_id = gerenate_job_id_for_batch(parent_batch.id)

    # Convert ProfileDocument instances to dict for JSON serialization
    files_data_for_redis = convert_doc_instance_to_dict(files_data)

    # Store job details in Redis
    job_details = {
        "job_id": job_id,
        "parent_batch_id": parent_batch.id,
        "matched_profile_name": matched_profile.name,
        "project": matched_profile.project,
        "files_data": files_data_for_redis,
        "batch_upload_mode": batch_upload_mode,
        "pdf_paths": pdf_files,
        "files_for_ocr": files_for_ocr,
        "force_ocr_engine": parent_batch.force_ocr_engine,
    }

    # Serialize parsed document instances for JSON storage
    for item in job_details["files_data"]:
        if "parsed_doc_instance" in item and item["parsed_doc_instance"]:
            item["parsed_doc_instance"] = item["parsed_doc_instance"].to_dict()

    redis_instance.set(job_id, json.dumps(job_details))

    if not pdf_files:
        response_data = {
            "job_id": job_id,
            "categorization_results": {
                file_path: {"is_electronic": False} for file_path in files_for_ocr
            },
        }
        process_pdfs_and_docs_p2(response_data)

        return

    # Publish message to preprocess queue
    payload = {
        "job_id": job_id,
        "pdf_paths": pdf_files,
    }

    try:
        publish("categorize_pdfs", "to_preprocess", payload)
        print(f"PDF categorization message published for batch_id: {parent_batch.id}")
    except Exception as e:
        print(
            f"PDF categorization message publishing error for batch_id: {parent_batch.id}: {str(e)}"
        )
        try:
            from pipeline.views import test_batch_cleanup

            test_batch_cleanup(job_id)
            write_parent_batch_log(
                batch_id=parent_batch.id,
                status="failed",
                message="Failed to Publish PDF Categorization Message",
                remarks=json.dumps({"error": str(e)}),
                action="display_json",
            )
        except:
            pass


def process_pdfs_and_docs_p2(response_data):
    """
    Process PDFs and documents - Phase 2: Handle categorization response and continue processing
    """
    try:
        from pipeline.views import test_batch_cleanup

        # Called from API callback
        job_id = response_data["job_id"]
        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        parent_batch_id = job_info["parent_batch_id"]
        matched_profile_name = job_info["matched_profile_name"]
        files_data = job_info["files_data"]
        batch_upload_mode = job_info["batch_upload_mode"]
        pdf_paths = job_info["pdf_paths"]
        files_for_ocr = job_info["files_for_ocr"]
        project = job_info["project"]

        # Convert matched_doc dicts back to ProfileDocument instances
        files_data = load_doc_instance_from_dict(files_data)

        # Deserialize parsed document instances
        for item in files_data:
            if "parsed_doc_instance" in item and item["parsed_doc_instance"]:
                # Determine the model class based on batch_upload_mode
                model_class = (
                    EmailParsedDocument
                    if batch_upload_mode == "processing"
                    else TrainParsedDocument
                )
                item["parsed_doc_instance"] = model_class.from_dict(
                    item["parsed_doc_instance"]
                )

        # Get categorization results from response
        categorization_results = response_data.get("categorization_results", {})

        # Get batch objects
        parent_batch = (
            EmailBatch.objects.get(id=parent_batch_id)
            if batch_upload_mode == "processing"
            else TrainBatch.objects.get(id=parent_batch_id)
        )
        matched_profile = Profile.objects.get(name=matched_profile_name)

        batch_id = None
        electronic_pdfs = []
        remarks = []

        # Process categorization results
        for file_path in pdf_paths:
            file_name = os.path.basename(file_path)
            # Get categorization from API response
            is_electronic = categorization_results[file_path].get(
                "is_electronic", False
            )

            if is_electronic:
                electronic_pdfs.append(file_path)
            else:
                files_for_ocr.append(file_path)

            detail_item = {
                "file_name": file_name,
                "is_electronic": is_electronic,
            }
            remarks.append(detail_item)

        remarks = sorted(remarks, key=lambda item: item["file_name"])

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="PDF Categorization has been Completed",
            remarks=json.dumps(remarks),
            action="display_table",
        )

        # Clean up Redis data before passing to next function
        test_batch_cleanup(job_id)

        # Processing electronic pdfs
        if len(electronic_pdfs):
            process_electronic_pdfs_p1(
                files_data,
                electronic_pdfs,
                files_for_ocr,
                parent_batch,
                matched_profile,
                batch_upload_mode,
                project,
            )
            return

        if len(files_for_ocr):
            process_files_for_ocr(
                files_for_ocr,
                batch_id,
                parent_batch,
                matched_profile,
                files_data,
                batch_upload_mode,
            )
    except Exception as e:
        print(f"Error in process_pdfs_and_docs_p2: {str(e)}")
        print(traceback.format_exc())
        try:
            test_batch_cleanup(job_id)
        except:
            pass


def process_electronic_pdfs_p1(
    files_data,
    file_paths,
    files_for_ocr,
    parent_batch,
    matched_profile,
    batch_upload_mode,
    project,
):
    """
    Process electronic PDFs - Phase 1: Call API to process files
    """
    (
        instanceToBatchLink,
        _,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
    )

    transaction_id = parent_batch.id
    extension = ".pdf"
    details = {"file_paths": file_paths}

    write_parent_batch_log(
        batch_id=transaction_id,
        status="inprogress",
        message="Processing electronic PDF files",
        remarks=json.dumps(details),
        action="display_json",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    batch_id = get_new_batch_id()

    Batch.objects.create(
        id=batch_id,
        visible=False,
        definition_id=parent_batch.matched_profile_name,
        extension=extension,
        mode=batch_upload_mode,
    )

    batch_path = prepare_parent_batch_path(batch_id, sub_path="")

    instanceToBatchLink.objects.create(
        **parent_batch_kwarg, batch_id=batch_id, mode=batch_upload_mode
    )

    # Generate job ID for tracking
    job_id = gerenate_job_id_for_batch(parent_batch.id)

    # Convert ProfileDocument instances to dict for JSON serialization
    files_data_for_redis = convert_doc_instance_to_dict(files_data)

    # Store job details in Redis
    job_details = {
        "parent_batch_id": parent_batch.id,
        "batch_id": batch_id,
        "batch_upload_mode": batch_upload_mode,
        "file_paths": file_paths,
        "output_folder": batch_path,
        "files_for_ocr": files_for_ocr,
        "profile_name": matched_profile.name,
        "project": project,
        "files_data": files_data_for_redis,
    }

    # Serialize parsed document instances for JSON storage
    for item in job_details["files_data"]:
        if "parsed_doc_instance" in item and item["parsed_doc_instance"]:
            item["parsed_doc_instance"] = item["parsed_doc_instance"].to_dict()

    redis_instance.set(job_id, json.dumps(job_details))

    # Publish message to preprocess queue
    payload = {
        "job_id": job_id,
        "parent_batch_id": parent_batch.id,
        "batch_upload_mode": batch_upload_mode,
    }

    try:
        publish("process_files", "to_preprocess", payload)
        print(f"Electronic PDF processing message published for job_id: {job_id}")
        return True
    except Exception as e:
        print(
            f"Electronic PDF processing message publishing error for job_id: {job_id}: {str(e)}"
        )
        try:
            from pipeline.views import test_batch_cleanup

            test_batch_cleanup(job_id)
        except:
            pass
        return False


def process_electronic_pdfs_p2(response_data):
    """
    Process electronic PDFs - Phase 2: Handle API response and continue processing
    """
    try:
        from pipeline.views import test_batch_cleanup

        # Check for error response
        job_id = response_data.get("job_id")
        status_code = response_data.get("status_code")
        parent_batch_id = response_data.get("parent_batch_id")
        batch_upload_mode = response_data.get("batch_upload_mode")

        if status_code != 200:
            error_msg = response_data.get("error", "Unknown error")
            print(f"Error in electronic PDF processing: {error_msg}")

            try:
                from pipeline.views import test_batch_cleanup

                test_batch_cleanup(job_id)
                write_parent_batch_log(
                    batch_id=parent_batch_id,
                    status="failed",
                    message="Electronic PDF Batch Creation Failed",
                    remarks=json.dumps(response_data),
                    action="display_json",
                    train_batch_log=True if batch_upload_mode == "training" else False,
                )
            except:
                pass
            return

        job_info = redis_instance.get(job_id)
        job_info = json.loads(job_info)

        batch_id = job_info["batch_id"]
        ra_json = job_info["ra_json"]
        batch_upload_mode = job_info["batch_upload_mode"]
        file_paths = job_info["file_paths"]
        files_for_ocr = job_info["files_for_ocr"]
        profile_name = job_info["profile_name"]
        files_data = job_info["files_data"]

        # Convert matched_doc dicts back to ProfileDocument instances
        files_data = load_doc_instance_from_dict(files_data)

        # Deserialize parsed document instances
        for item in files_data:
            if "parsed_doc_instance" in item and item["parsed_doc_instance"]:
                # Determine the model class based on batch_upload_mode
                model_class = (
                    EmailParsedDocument
                    if batch_upload_mode == "processing"
                    else TrainParsedDocument
                )
                item["parsed_doc_instance"] = model_class.from_dict(
                    item["parsed_doc_instance"]
                )

        # Get batch objects
        if batch_upload_mode == "processing":
            parent_batch = EmailBatch.objects.get(id=parent_batch_id)
        else:
            parent_batch = TrainBatch.objects.get(id=parent_batch_id)

        batch = Batch.objects.get(id=batch_id)

        matched_profile = Profile.objects.get(name=profile_name)

        # Get instance classes
        (
            _,
            instanceParsedDocument,
            parent_batch,
            parent_batch_kwarg,
            *tail,
        ) = get_instance_classes(
            batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
        )

        batch.ra_json = ra_json
        batch.save()

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            parsed_doc = instanceParsedDocument.objects.get(
                **parent_batch_kwarg, name=file_name
            )
            parsed_doc.ra_json_created = True
            parsed_doc.batch_id = batch_id
            parsed_doc.save()

        details = {
            "batch_id": batch_id,
            "file": join_with_escaped_commas(file_paths),
        }

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Electronic PDF Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        # Clean up Redis data before terminal operations
        test_batch_cleanup(job_id)

        if len(files_for_ocr):
            process_files_for_ocr(
                files_for_ocr,
                batch_id,
                parent_batch,
                matched_profile,
                files_data,
                batch_upload_mode,
            )
            return

        request_data = {
            "batch_id": batch_id,
        }

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Initiated classification process",
        )

        publish("classify_batch_queued", "to_pipeline", request_data)

    except Exception as e:
        print(f"Error in process_electronic_pdfs_p2: {str(e)}")
        print(traceback.format_exc())
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        return None


def process_electronic_pdfs_backup(
    file_paths, parent_batch, matched_profile, batch_upload_mode
):
    """
    Workflow for processing single PDF file irrespective of input channel of file.
    """
    (
        instanceToBatchLink,
        instanceParsedDocument,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
    )

    transaction_id = parent_batch.id
    extension = ".pdf"
    details = {"file_paths": file_paths}

    write_parent_batch_log(
        batch_id=transaction_id,
        status="inprogress",
        message="Processing electronic PDF files",
        remarks=json.dumps(details),
        action="display_json",
    )

    batch_id = get_new_batch_id()

    batch = Batch.objects.create(
        id=batch_id,
        visible=False,
        definition_id=parent_batch.matched_profile_name,
        extension=extension,
        mode=batch_upload_mode,
    )

    batch_path = prepare_parent_batch_path(batch_id, sub_path="")

    instanceToBatchLink.objects.create(
        **parent_batch_kwarg, batch_id=batch_id, mode=batch_upload_mode
    )

    # # Copy PDF file into batch folder
    # destination = os.path.join(batch_path, file_name)
    # shutil.copyfile(file_path, destination)

    # Create RAJSON and XML
    ra_json = process_files(
        file_paths=file_paths,
        output_folder=batch_path,
        batch_id=batch_id,
        profile_name=matched_profile.name,
    )

    batch.ra_json = ra_json
    batch.save()

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        parsed_doc = instanceParsedDocument.objects.get(
            **parent_batch_kwarg, name=file_name
        )
        parsed_doc.ra_json_created = True
        parsed_doc.batch_id = batch_id
        parsed_doc.save()

    details = {
        "batch_id": batch_id,
        "file": join_with_escaped_commas(file_paths),
    }

    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message="Electronic PDF Batch Created",
        remarks=json.dumps(details),
        action="display_key_values",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    return batch_id


def process_files_for_ocr(
    file_paths,
    electronic_batch_id,
    parent_batch,
    matched_profile,
    files_data,
    batch_upload_mode,
):
    """
    Workflow for processing single PDF file irrespective of input channel of file.
    """
    if not len(file_paths):
        return

    pdf_files = [
        file_path for file_path in file_paths if file_path.lower().endswith(".pdf")
    ]
    doc_files = [
        file_path
        for file_path in file_paths
        if file_path.lower().endswith((".doc", ".docx"))
    ]

    (
        instanceToBatchLink,
        instanceParsedDocument,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
    )

    transaction_id = parent_batch.id
    extension = ".pdf"

    details = {"file_paths": file_paths}

    write_parent_batch_log(
        batch_id=transaction_id,
        status="inprogress",
        message="Processing Files for OCR",
        remarks=json.dumps(details),
        action="display_json",
    )

    # if Document is not electronic, find OCR engine type and process it via OCR engine
    # External or Internal
    ocr_engine_type = get_ocr_engine_type(parent_batch)

    project = get_project_by_profile(parent_batch.matched_profile_name)

    if ocr_engine_type == "internal":
        if len(doc_files):
            # Delete parsed document instance for doc_files
            for doc_file_path in doc_files:
                doc_file_name = os.path.basename(doc_file_path)
                parsed_doc = instanceParsedDocument.objects.filter(
                    **parent_batch_kwarg, name=doc_file_name
                ).delete()

            files_data = [i for i in files_data if i["file_path"] not in doc_files]
            write_parent_batch_log(
                message=f"Doc Files Ignored. Please select external OCR engine to process Doc files",
                batch_id=transaction_id,
                remarks=json.dumps(doc_files),
                status="warning",
                action="display_json",
            )

        if not len(files_data):
            write_parent_batch_log(
                batch_id=transaction_id,
                status="failed",
                message="Transaction execution failed due to no processing documents",
            )
            return

        if not len(pdf_files):
            excel_files = [
                i for i in files_data if i["file_path"].lower().endswith(".xlsx")
            ]

            if len(excel_files) == len(files_data):
                write_parent_batch_log(
                    batch_id=parent_batch.id,
                    status="inprogress",
                    message="Classification process initiated",
                    train_batch_log=True if batch_upload_mode == "training" else False,
                )

                write_parent_batch_log(
                    batch_id=parent_batch.id,
                    status="inprogress",
                    message="Document matching initiated",
                    train_batch_log=True if batch_upload_mode == "training" else False,
                )

                post_classification_process(
                    write_parent_batch_log,
                    parent_batch,
                    batch_upload_mode,
                    matched_profile,
                )
            else:
                request_data = {
                    "batch_id": electronic_batch_id,
                }

                write_parent_batch_log(
                    batch_id=parent_batch.id,
                    status="inprogress",
                    message="Initiated classification process",
                )

                publish("classify_batch_queued", "to_pipeline", request_data)

            return

        batch_id = get_new_batch_id()

        Batch.objects.create(
            id=batch_id,
            definition_id=parent_batch.matched_profile_name,
            extension=extension,
            mode=batch_upload_mode,
            visible=False,
        )

        instanceToBatchLink.objects.create(
            **parent_batch_kwarg, batch_id=batch_id, mode=batch_upload_mode
        )

        for file_path in pdf_files:
            file_name = os.path.basename(file_path)
            parsed_doc = instanceParsedDocument.objects.get(
                **parent_batch_kwarg, name=file_name
            )
            parsed_doc.batch_id = batch_id
            parsed_doc.save()

        # OCR Engine call
        request_body = {
            "files": pdf_files,
            "batch_id": batch_id,
            "profile_name": parent_batch.matched_profile_name,
            "project": project,
        }
        publish("create_batch_ocr", "to_ocr_engine", request_body)

        details = {
            "batch_id": batch_id,
            "file": join_with_escaped_commas(pdf_files),
        }

        write_parent_batch_log(
            batch_id=transaction_id,
            status="inprogress",
            message="Scanned PDF Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        write_parent_batch_log(
            batch_id=transaction_id,
            status="inprogress",
            message="Awaiting OCR Engine API respone",
        )
    else:
        # Trigger flow for External OCR Engine (Datacap)
        write_parent_batch_log(
            batch_id=transaction_id,
            status="inprogress",
            message="Uploading PDF to Datacap",
        )

        datacap = DataCap(project)
        profile_instance = Profile.objects.get(name=parent_batch.matched_profile_name)
        file_paths_str = join_with_escaped_commas(file_paths)

        attachment_documents = matched_profile.documents.filter(
            content_location="Email Attachment"
        ).filter(category="Processing")

        default_ocr = get_default_ocr(attachment_documents)
        default_language = get_default_language(attachment_documents)
        default_page_rotate = get_default_page_rotate(attachment_documents)
        default_barcode = get_default_barcode(attachment_documents)

        page_file = generate_datacap_page_file(
            profile_instance=profile_instance,
            batch_type="Train" if batch_upload_mode == "training" else "Process",
            file_paths=file_paths_str,
            default_ocr=default_ocr,
            default_language=default_language,
            default_page_rotate=default_page_rotate,
            default_barcode=default_barcode,
        )
        files = [create_inmemory_file(file_path) for file_path in file_paths]

        details = datacap.create_batch(
            files=files, page_file=page_file, delayed_release=True
        )

        datacap_batch_id = details["batch_id"]
        details["file"] = join_with_escaped_commas(file_paths)

        Batch.objects.create(
            id=datacap_batch_id,
            definition_id=parent_batch.matched_profile_name,
            extension=extension,
            mode=batch_upload_mode,
            visible=False,
        )

        instanceToBatchLink.objects.create(
            **parent_batch_kwarg,
            batch_id=datacap_batch_id,
            mode=batch_upload_mode,
        )

        # Update batch id to parsed documents
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            parsed_doc = instanceParsedDocument.objects.get(
                **parent_batch_kwarg, name=file_name
            )
            parsed_doc.batch_id = datacap_batch_id
            parsed_doc.save()

        write_parent_batch_log(
            batch_id=transaction_id,
            status="inprogress",
            message="Datacap Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
        )

        write_parent_batch_log(
            batch_id=transaction_id,
            status="inprogress",
            message="Awaiting Datacap API Callback to Initiate Classification Process",
        )


def handle_ocr_completed(request_data):
    batch_id = None
    parent_batch = None

    try:
        batch_id = request_data["batch_id"]
        status_code = request_data["status_code"]

        print(f"{batch_id=}")

        (_, instanceParsedDocument, parent_batch, parent_batch_kwarg, *tail) = (
            get_instance_classes(batch_id)
        )

        # Check if we got valid instances
        if not parent_batch:
            print(
                f"ERROR: Could not get parent_batch for batch_id: {batch_id}",
                file=sys.stderr,
            )
            return

        # Check Status Code
        if status_code != 200:
            write_failed_log(
                batch_id=parent_batch.id,
                status="failed",
                message="OCR Engine did not send valid response",
                action="display_json",
                remarks=json.dumps(request_data),
            )
            return

        batch = Batch.objects.get(id=batch_id)
        sub_path = batch.sub_path

        if sub_path:
            batch_path = os.path.join(BATCH_INPUT_PATH, sub_path)
        else:
            batch_path = BATCH_INPUT_PATH

        batch_directory = os.path.join(batch_path, batch_id)
        ra_json_file_path = os.path.join(batch_directory, "ra_json.json")

        with open(ra_json_file_path, "r") as f:
            ra_json = json.load(f)

        batch.ra_json = ra_json
        batch.save()

        pd_qs = instanceParsedDocument.objects.filter(**parent_batch_kwarg)

        # Update parsed documents batch id
        for pd_instance in pd_qs:
            pd_instance.ra_json_created = True
            pd_instance.save()

        request_data = {
            "batch_id": batch_id,
        }

        publish("classify_batch_queued", "to_pipeline", request_data)

    except Exception as e:
        error = traceback.format_exc()
        print(f"{error=}")

        remarks = {"error": error}

        if parent_batch:
            try:
                write_failed_log(
                    batch_id=parent_batch.id,
                    status="failed",
                    message="Error occurred during OCR Engine response processing",
                    action="display_error",
                    remarks=json.dumps(remarks, indent=4),
                )
            except Exception as log_error:
                print(f"Failed to write batch log: {log_error}", file=sys.stderr)
                print(f"Original error: {e}", file=sys.stderr)
        else:
            print(
                f"Cannot write batch log - parent_batch is None for batch_id: {batch_id}",
                file=sys.stderr,
            )


def upload_batches_for_processing(batch_ids, email_batch_id):
    for batch_id in batch_ids:
        request_data = {"batch_id": batch_id}

        write_batch_log(
            batch_id=batch_id,
            status="queued",
            message="Batch added to queue for processing",
        )

        publish("batch_queued", "to_pipeline", request_data)


def convert_excel_files_to_pdf(parent_batch, files_data, batch_upload_mode):
    file_paths = [file_data["file_path"] for file_data in files_data]

    excel_files = [
        file_path
        for file_path in file_paths
        if Path(file_path).suffix.lower() in EXCEL_FORMATS
    ]

    if not excel_files:
        return files_data

    parent_batch_id = parent_batch.id
    details = {"file_paths": excel_files}

    write_parent_batch_log(
        batch_id=parent_batch_id,
        status="inprogress",
        message="Converting Excel Files to PDF",
        remarks=json.dumps(details),
        action="display_json",
    )

    conversion_result = convert_excel_or_doc_to_pdf(excel_files)

    write_parent_batch_log(
        batch_id=parent_batch_id,
        status="inprogress",
        message="Excel File Conversion Completed",
        remarks=json.dumps(conversion_result),
        action="display_json",
    )

    # Update files_data with successful conversion result
    successful_conversion_result = conversion_result.get("successful", [])

    (
        _,
        instanceParsedDocument,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode,
        parent_batch=parent_batch,
    )

    for file_path in successful_conversion_result:
        file_name = os.path.basename(file_path)

        parsed_doc_instance = instanceParsedDocument.objects.create(
            **parent_batch_kwarg,
            name=file_name,
            path=file_path,
            type="attachment",
            matched_profile_doc=None,
        )

        files_data.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "type": "attachment",
                "matched_doc": None,
                "page_file": None,
                "parsed_doc_instance": parsed_doc_instance,
            }
        )

    # Delete excel files from parsed document
    excel_file_names = [os.path.basename(p) for p in excel_files]
    instanceParsedDocument.objects.filter(name__in=excel_file_names).delete()

    return files_data


def process_excels(
    upload_batch_process: Callable,
    get_info_holder_for_batch: Callable,
    email_batch,
    matched_profile,
    files_data,
    batch_upload_mode,
):
    parent_batch = email_batch
    file_paths = [i["file_path"] for i in files_data]
    excel_files = [
        file_path
        for file_path in file_paths
        if Path(file_path).suffix.lower() in EXCEL_FORMATS
    ]

    if not excel_files:
        return

    (
        instanceToBatchLink,
        instanceParsedDocument,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
    )

    parent_batch_id = parent_batch.id
    extension = Path(excel_files[0]).suffix.lower()
    details = {"file_paths": excel_files}

    write_parent_batch_log(
        batch_id=parent_batch_id,
        status="inprogress",
        message="Processing excel files",
        remarks=json.dumps(details),
        action="display_json",
    )

    # Generate excel_files_by_doc_types dict
    _, profile_documents = get_profile_doc_info(matched_profile)
    excel_files_by_doc_types = {}

    for file_path in excel_files:
        matched_doc = match_attachment(
            profile_documents["name_match"],
            None,
            file_path,
        )

        key = "None"

        if matched_doc:
            key = f"{matched_doc.doc_type}_{matched_doc.name_matching_text}"

        if key in excel_files_by_doc_types:
            excel_files_by_doc_types[key]["files"].append(file_path)
        else:
            excel_files_by_doc_types[key] = {
                "files": [file_path],
                "matched_doc": matched_doc,
            }

    # Create excel batch folder and generate ra_json
    uploadable_batches = []

    for item in excel_files_by_doc_types.values():
        excel_file_paths = item["files"]
        matched_doc = item["matched_doc"]
        batch_id = get_new_batch_id()

        batch_instance = Batch.objects.create(
            id=batch_id,
            visible=False,
            definition_id=parent_batch.matched_profile_name,
            extension=extension,
            mode=batch_upload_mode,
        )

        batch_path = prepare_parent_batch_path(batch_id, sub_path="")

        linked_batch_instance = instanceToBatchLink.objects.create(
            **parent_batch_kwarg,
            batch_id=batch_id,
            mode=batch_upload_mode,
            uploaded=False,
            classified=True,
        )

        # copy batches xml with dynamic file name
        copy_batches_xml_content = generate_copy_batches_xml(
            profile_instance=matched_profile,
            doc_instance=matched_doc,
            file_paths=excel_file_paths,
            batch_id=batch_id,
            output_folder=batch_path,
        )

        copy_batches_xml_file_path = os.path.join(batch_path, "CopyBatches.xml")

        with open(copy_batches_xml_file_path, "w") as f:
            f.write(copy_batches_xml_content)

        # if it's an exceptional excel file, read_only will be False to generate RA_Json properly.
        excel_read_only = is_excel_read_only(batch_id, parent_batch)

        info_holder_data, valid_page_types = get_info_holder_for_batch(
            "/".join(batch_path.split("/")[:-1]), batch_id
        )

        # Produce RAJson
        ra_json = RAJson(
            batch_id,
            "/".join(batch_path.split("/")[:-1]),
            info_holder_data,
            valid_page_types,
            excel_read_only,
        ).process()

        batch_instance.ra_json = ra_json
        batch_instance.save()

        for file in excel_file_paths:
            file_name = os.path.basename(file)
            parsed_doc = instanceParsedDocument.objects.get(
                **parent_batch_kwarg, name=file_name
            )
            parsed_doc.ra_json_created = True
            parsed_doc.matched_profile_doc = matched_doc
            parsed_doc.batch_id = batch_id
            parsed_doc.save()

        details = {
            "batch_id": batch_id,
            "file": join_with_escaped_commas(excel_file_paths),
        }

        write_parent_batch_log(
            batch_id=parent_batch_id,
            status="inprogress",
            message="Excel Batch Created",
            remarks=json.dumps(details),
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        if matched_doc:
            linked_batch_instance.uploaded = True
            linked_batch_instance.save()
            uploadable_batches.append(batch_id)

    # Return if all uploaded files are Excel files
    if len(file_paths) != len(excel_files):
        for batch_id in uploadable_batches:
            upload_batch_process(batch_id, batch_upload_mode, "")
        return

    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message="Classification process initiated",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message="Document matching initiated",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    post_classification_process(
        write_parent_batch_log,
        parent_batch,
        batch_upload_mode,
        matched_profile,
    )

    for batch_id in uploadable_batches:
        upload_batch_process(batch_id, batch_upload_mode, "")
