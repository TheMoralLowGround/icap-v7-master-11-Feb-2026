"""
Organization: AIDocbuilder Inc.
File: utils/classification_utils.py
Version: 6.0

Authors:
    - Nayem - Initial implementation
    - Sunny - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This file contain necessary functions to execution the classification process.

Dependencies:
    - os, re, glob, shutil, requests, traceback, PyPDF2
    - xml.etree.ElementTree as ET
    - deepcopy from copy
    - ProfileDocument from dashboard.models
    - remove_null_characters from utils.utils
    - settings from django.conf
    - MasterDictionarySerializer from core.serializers
    - EmailParsedDocument, EmailToBatchLink, MasterDictionary, TrainParsedDocument,
      TrainToBatchLink from core.models

Main Features:
    - Retrive necessary information from copybatch.xml file.
    - Handle document types based on different criteria.
    - Split PDF if the document type is different.
    - Create batches for different document types.
    - Handle manual classification details.
"""

import os
import re
import json
import glob
import redis
import shutil
import traceback
from typing import Callable
import xml.etree.ElementTree as ET
from copy import deepcopy
from rabbitmq_producer import publish
from core.models import (
    Batch,
    EmailBatch,
    TrainBatch,
    EmailParsedDocument,
    EmailToBatchLink,
    MasterDictionary,
    TrainParsedDocument,
    TrainToBatchLink,
    OutputJson,
)
from core.serializers import (
    MasterDictionarySerializer,
)
from dashboard.models import ProfileDocument, Profile, Template
from utils.utils import (
    save_analyzer_log_time,
    get_additional_doc_type,
    is_imd_enabled_for_project,
    link_additional_batch,
    generate_datacap_page_file,
    create_inmemory_file,
)
from pipeline.scripts.DataCap import DataCap


import PyPDF2
from django.conf import settings

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
CLASSIFIER_API_URL = settings.CLASSIFIER_API_URL

# Connect to our Redis instance
redis_instance = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name="backend"
)


def get_project_by_profile(profile_name):
    """
    Retrieves a project name based on the given profile name

    Args:
        profile_name (str): Profile Name

    Returns:
        project (str): Project Name
    """
    project = None

    profile_qs = Profile.objects.filter(name=profile_name)
    if profile_qs.exists():
        project = profile_qs.first().project

    return project


def handle_auto_classifier_response(
    write_parent_batch_log: Callable,
    request_data,
    status_code,
    parent_batch,
    page_wise_doc_types,
    profile_documents,
    profile_documents_dict,
    selected_doc_types,
    doc_type_index_dict,
    message_type="title_classification_response",
):
    """
    Handle auto-classifier response and return normalized page_wise_doc_types and doc_type_index_dict
    """
    if not status_code:
        return page_wise_doc_types, doc_type_index_dict

    auto_classified_doc_types = request_data.get("doctypes", {})

    if status_code != 200:
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="warning",
            message=f"Auto Classifier did not send valid response with {status_code} status code",
            action="display_json",
            remarks=json.dumps(request_data, indent=4),
        )
    else:
        remarks = []

        for key, value in auto_classified_doc_types.items():
            detail_item = {
                "doc_type": key,
                "page_range": value,
            }
            remarks.append(detail_item)

        remarks = sorted(remarks, key=lambda item: item["doc_type"])
        message = "Auto Classifier response"

        if message_type == "ocr_mismatch_response":
            message = f"Checking {message} for OCR Mismatches"

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message=message,
            remarks=json.dumps(remarks),
            action="display_table",
        )

    print(f"Auto Classified Doc Types: {auto_classified_doc_types}")

    page_wise_doc_types, doc_type_index_dict = normalize_auto_classified_doc_types(
        page_wise_doc_types,
        auto_classified_doc_types,
        profile_documents,
        profile_documents_dict,
        selected_doc_types,
        doc_type_index_dict,
    )
    print(
        f"Normalized Auto Classified Doc Types: {[i['doc_type'] for i in page_wise_doc_types]}"
    )

    return page_wise_doc_types, doc_type_index_dict


def handle_ocr_mismatch(request_data):
    """
    Handles OCR mismatch response from classifier and processes the batch accordingly.

    Args:
        request_data (dict): Dictionary containing job_id, status_code, and doctypes from classifier response

    Returns:
        None: Processes the batch and calls pre_classification_process_p2
    """
    from pipeline.utils.process_batch_utils import write_parent_batch_log
    from pipeline.views import pre_classification_process_p2, test_batch_cleanup

    print(f"{request_data=}")
    job_id = request_data.get("job_id")
    status_code = request_data.get("status_code")

    job_info = redis_instance.get(job_id)
    job_info = json.loads(job_info)

    profile_name = job_info["profile_name"]
    parent_batch_id = job_info["parent_batch_id"]
    batch_id = job_info.get("batch_id")
    batch_path = job_info.get("batch_path")
    sub_path = job_info.get("sub_path")
    selected_doc_types = job_info.get("selected_doc_types")
    batch_upload_mode = job_info.get("batch_upload_mode")

    # Get parent batch instance
    if batch_upload_mode == "processing":
        parent_batch = EmailBatch.objects.get(id=parent_batch_id)
    else:
        parent_batch = TrainBatch.objects.get(id=parent_batch_id)

    batch_instance = Batch.objects.get(id=batch_id)
    matched_profile = Profile.objects.get(name=profile_name)
    profile_documents_dict, profile_documents = get_profile_doc_info(matched_profile)

    doc_info, _, page_wise_doc_types = get_doc_info(parent_batch, batch_instance)

    doc_type_index_dict = {}

    page_wise_doc_types, doc_type_index_dict = handle_auto_classifier_response(
        write_parent_batch_log,
        request_data,
        status_code,
        parent_batch,
        page_wise_doc_types,
        profile_documents,
        profile_documents_dict,
        selected_doc_types,
        doc_type_index_dict,
        message_type="ocr_mismatch_response",
    )

    page_wise_doc_types, exts = get_name_matching_doc_types(
        page_wise_doc_types,
        doc_info,
        profile_documents,
        selected_doc_types,
        doc_type_index_dict,
    )

    page_wise_doc_types, doc_type_index_dict = translate_matched_doc_types(
        write_parent_batch_log,
        parent_batch,
        batch_upload_mode,
        page_wise_doc_types,
        matched_profile,
        profile_documents_dict,
        selected_doc_types,
        doc_type_index_dict,
        message_type="ocr_mismatch_response",
    )

    # Checking if no pages are available
    if not len(page_wise_doc_types):
        test_batch_cleanup(job_id)
        pre_classification_process_p2(batch_id)
        return

    # Checking if nothing matched
    if all(x["doc_type"] == None for x in page_wise_doc_types):
        test_batch_cleanup(job_id)
        pre_classification_process_p2(batch_id)
        return

    current_ocr_info = get_ocr_info_from_ra_json(batch_instance.ra_json)

    # Checking if all doc types are matched with current ocr
    if all(
        get_ocr_info_from_matched_doc(x["matched_doc"]) == current_ocr_info
        for x in page_wise_doc_types
        if x.get("matched_doc")
    ):
        test_batch_cleanup(job_id)
        pre_classification_process_p2(batch_id)
        return

    (
        instanceToBatchLink,
        instanceParsedDocument,
        parent_batch,
        parent_batch_kwarg,
        *tail,
    ) = get_instance_classes(batch_instance.id)

    # Checking if all doc types are not matched with current ocr
    first_doc_ocr_info = next(
        (
            ocr_info
            for x in page_wise_doc_types
            if x.get("matched_doc")
            and (ocr_info := get_ocr_info_from_matched_doc(x["matched_doc"]))
            is not None
        ),
        None,
    )

    if first_doc_ocr_info is None:
        test_batch_cleanup(job_id)
        pre_classification_process_p2(batch_id)
        return

    if first_doc_ocr_info != current_ocr_info and all(
        get_ocr_info_from_matched_doc(x["matched_doc"]) == first_doc_ocr_info
        for x in page_wise_doc_types
        if x.get("matched_doc")
    ):
        matched_doc = page_wise_doc_types[0]
        file_paths = batch_instance.ra_json.get("bvFilePath")
        file_paths = (
            split_with_escaped_commas(file_paths)
            if file_paths and file_paths != "None"
            else []
        )

        recreate_datacap_batch(
            write_parent_batch_log,
            matched_profile=matched_profile,
            matched_doc=matched_doc["matched_doc"],
            batch_id=batch_instance.id,
            file_paths=file_paths,
            extension=exts[0],
            selected_doc_types=selected_doc_types,
            batch_type=("Process" if batch_upload_mode == "processing" else "Train"),
        )

        instanceToBatchLink.objects.get(batch_id=batch_instance.id).delete()
        test_batch_cleanup(job_id)
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Awaiting datacap API callback for the re-created batches",
        )
        return

    # Handle Recreation on splitted batch
    instanceToBatchLink.objects.get(batch_id=batch_instance.id).delete()
    instanceParsedDocument.objects.filter(batch_id=batch_instance.id).delete()
    matched_docs = update_matched_docs(page_wise_doc_types, doc_info)
    pages_by_doc_type = get_pages_by_doc_type(matched_docs)

    split_index = 0
    for element in pages_by_doc_type.values():
        for item in element.values():
            new_batch_id = create_split_batch(
                batch_path,
                split_index,
                item,
                batch_instance.id,
                batch_upload_mode,
                sub_path,
                item["ext"],
            )

            split_index += 1

            for index, file_path in enumerate(item["file_paths"]):
                file_name = os.path.basename(file_path)
                if index == 0:
                    instanceToBatchLink.objects.create(
                        **parent_batch_kwarg,
                        batch_id=new_batch_id,
                        classified=True,
                        mode=batch_upload_mode,
                    )
                instanceParsedDocument.objects.create(
                    **parent_batch_kwarg,
                    batch_id=new_batch_id,
                    name=file_name,
                    path=file_path,
                    type="attachment",
                    matched_profile_doc=item["matched_doc"],
                    splitted=item["splitted"][index],
                    ra_json_created=True,
                )

            if (
                item["matched_doc"]
                and get_ocr_info_from_matched_doc(item["matched_doc"])
                != current_ocr_info
            ):
                recreate_datacap_batch(
                    write_parent_batch_log,
                    matched_profile=matched_profile,
                    matched_doc=item["matched_doc"],
                    batch_id=new_batch_id,
                    file_paths=item["file_paths"],
                    extension=item["ext"],
                    selected_doc_types=selected_doc_types,
                    batch_type=(
                        "Process" if batch_upload_mode == "processing" else "Train"
                    ),
                )
                instanceToBatchLink.objects.get(batch_id=new_batch_id).delete()

    test_batch_cleanup(job_id)
    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message="Awaiting datacap API callback for the re-created batches",
    )


def get_ocr_info_from_ra_json(ra_json):
    joined_ocr_info = ""

    ocr_engine = ra_json.get("bvOCR", "S")
    language = ra_json.get("Language", "English")
    page_rotate = ra_json.get("bvPageRotate", "N")
    barcode = ra_json.get("bvBarcodeRead", "N")

    joined_ocr_info = f"{ocr_engine}_{language}_{page_rotate}_{barcode}"

    return joined_ocr_info


def get_ocr_info_from_matched_doc(matched_doc):
    joined_ocr_info = ""

    ocr_engine = matched_doc.ocr_engine or "S"
    language = matched_doc.language or "English"
    page_rotate = "Y" if matched_doc.page_rotate else "N"
    barcode = "Y" if matched_doc.barcode else "N"

    joined_ocr_info = f"{ocr_engine}_{language}_{page_rotate}_{barcode}"

    return joined_ocr_info


def is_excel_read_only(batch_id, parent_batch=None):
    """Check if excel should be opened in read-only mode based on profile settings"""
    try:
        # Get parent batch info
        if not parent_batch:
            _, __, parent_batch, *tail = get_instance_classes(batch_id)

        # Get associated profile
        profile = Profile.objects.get(name=parent_batch.matched_profile_name)

        # Return read-only status based on exceptional_excel flag
        return not profile.exceptional_excel

    except (AttributeError, Profile.DoesNotExist):
        return True


def add_file_path_to_ra_json(ra_json, file_paths):
    for index, file_path in enumerate(file_paths):
        nodes = ra_json["nodes"]

        if index < len(nodes):
            nodes[index]["file_path"] = file_path

    return ra_json


def get_instance_classes(batch_id=None, batch_upload_mode=None, parent_batch=None):
    """
    Make instance classes, parent batch, and related data for a batch.

    Args:
        batch_id (str): ID of the batch.
        parent_batch (object): Predefined parent batch object.

    Returns:
        instanceToBatchLink (Model): Model linking batches to related data.
        instanceParsedDocument (Model): Model for parsed documents.
        parent_batch (object): Parent batch object.
        parent_batch_kwarg (dict): Query arguments with parent_batch.
        parent_batch_id_kwarg (dict): Query arguments with parent_batch_id.

    Process Details:
        - Check 'batch_upload_mode' then use Models to fetche parent batch data.

    Notes:
        - Return 'None' if no matching upload mode is found.
        - Raise error if database query fail or input is invalid.
    """

    MODE_CONFIGS = {
        "training": {
            "link_class": TrainToBatchLink,
            "doc_class": TrainParsedDocument,
            "parent_batch_field": "train_batch",
        },
        "processing": {
            "link_class": EmailToBatchLink,
            "doc_class": EmailParsedDocument,
            "parent_batch_field": "email",
        },
    }

    if (
        not batch_upload_mode
        and TrainToBatchLink.objects.filter(batch_id=batch_id).exists()
    ):
        batch_upload_mode = "training"
    elif (
        not batch_upload_mode
        and EmailToBatchLink.objects.filter(batch_id=batch_id).exists()
    ):
        batch_upload_mode = "processing"

    # Return early if mode not determined
    if not batch_upload_mode:
        return (None,) * 6

    # Get config for determined mode
    config = MODE_CONFIGS[batch_upload_mode]
    link_class = config["link_class"]
    doc_class = config["doc_class"]
    parent_batch_field = config["parent_batch_field"]

    # Get parent batch if not provided
    if not parent_batch and batch_id:
        parent_batch = link_class.objects.get(batch_id=batch_id).__getattribute__(
            parent_batch_field
        )

    # Create kwargs
    parent_batch_kwarg = {parent_batch_field: parent_batch}
    parent_batch_id_kwarg = {f"{parent_batch_field}_id": parent_batch.id}

    return (
        link_class,
        doc_class,
        parent_batch,
        parent_batch_kwarg,
        parent_batch_id_kwarg,
        batch_upload_mode,
    )


def contains_email_file_pattern(text: str) -> bool:
    """
    Patterns to match: email_file.pdf, email_file_0.pdf, email_file_1.pdf, etc.
    """
    pattern = r"email_file(?:_\d+)?\.pdf"
    return re.search(pattern, text) is not None


def update_ra_json_doc_order(merged_batch):
    """
    Reorder nodes in the ra_json to ensure email body documents appear at the end
    """
    if not merged_batch:
        return merged_batch

    nodes = merged_batch.ra_json.get("nodes", [])

    if len(nodes) == 0:
        return merged_batch

    nodes.sort(key=lambda node: contains_email_file_pattern(node.get("file_path", "")))

    merged_batch.ra_json["nodes"] = nodes
    merged_batch.save()

    return merged_batch


def convert_doc_instance_to_dict(matched_doc):
    """Convert matched documents to dict"""
    if matched_doc:
        matched_doc = [
            {
                **item,
                "matched_doc": (
                    item["matched_doc"].to_dict()
                    if item["matched_doc"]
                    else item["matched_doc"]
                ),
            }
            for item in matched_doc
        ]

    return matched_doc


def load_doc_instance_from_dict(matched_doc):
    """Load matched documents from dict"""
    if matched_doc:
        matched_doc = [
            {
                **item,
                "matched_doc": (
                    ProfileDocument.from_dict(item["matched_doc"])
                    if item["matched_doc"]
                    else item["matched_doc"]
                ),
            }
            for item in matched_doc
        ]

    return matched_doc


def save_manual_classification_data(train_batch, merged_batch, matched_doc, doc_info):
    """
    Save data for manual classification in training batch.

    Args:
        train_batch (object): Contain training batch metadata.
        batch_path (str): Path to the batch directory.
        batch_id (str): ID of the batch.
        sub_path (str): sub_path within the batch directory.
        matched_doc (list): Matched document metadata.
        doc_info (list): Document details.

    Process Details:
        - Organize files in parent directory and retrieve image and layout_xml paths.
        - Load matched documents into instance.
        - Generate 'file_identifiers_dict' to map page numbers to file index and name.
        - Iterate through layout XML paths and matched documents to generate manual classification data.
        - Handle unlisted Excel files by assigning default classification data.
        - Save the generated manual classification data.

    Notes:
        - Ensure all relevant files are included in the manual classification process.
    """
    batch_path = os.path.join(BATCH_INPUT_PATH, merged_batch.sub_path, merged_batch.id)
    image_paths = organize_files_inside_parent_dir(
        train_batch, batch_path, merged_batch.sub_path, merged_batch.id
    )
    matched_doc = load_doc_instance_from_dict(matched_doc)

    # Generate file_identifiers_dict
    file_identifiers = train_batch.file_identifiers

    # Generate data list
    data = []
    doc_type = matched_doc[0]["doc_type"]
    auto_classified = matched_doc[0]["auto_classified"]
    image_file = matched_doc[0]["image_file"]
    prev_end = 0

    for file_index, (start, end) in enumerate(file_identifiers):
        file_name = os.path.basename(doc_info[file_index]["file_path"])

        for index in range(start - 1, end):
            if len(matched_doc) > 1:
                doc_type = matched_doc[index]["doc_type"]
                auto_classified = matched_doc[index]["auto_classified"]
                image_file = matched_doc[index]["image_file"]

            page_index = index - prev_end
            if isinstance(image_file, str):
                image_path = image_paths.get(image_file.lower())
            else:
                image_path = None

            manual_classification_item = get_manual_classification_item(
                doc_type,
                image_path,
                file_index,
                page_index,
                file_name,
                auto_classified,
                image_file,
            )

            data.append(manual_classification_item)
        prev_end = end

    # Save manual classification data to DB
    train_batch.manual_classification_data = data
    train_batch.save()

    return


def organize_files_inside_parent_dir(train_batch, batch_path, sub_path, batch_id):
    """
    Organize and process files within the parent directory.

    Args:
        train_batch (object): Contain training batch data.
        batch_path (str): Path to the batch directory.
        sub_path (str): sub_path within the batch directory.
        batch_id (str): ID for the batch.

    Returns:
        image_paths (list): Paths to processed image files.
        layout_xml_paths (list): Paths to layout XML files.

    Process Details:
        - List and sort all items in the batch directory.
        - Filter and organize paths for images, layout_xml, excel files.
        - Copy files to designated directory within the parent batch folder.
        - Update file paths to reflect their new location in the parent directory.

    Notes:
        - Convert layout XML paths to absolute paths for further processing.
    """
    items = sorted(os.listdir(batch_path))

    image_paths = [
        os.path.join(sub_path, batch_id, os.path.basename(item))
        for item in items
        if item.endswith(".tif") and not item.endswith(".ocra.tif")
    ]

    excel_file_paths = [
        os.path.join(batch_path, item) for item in items if item.endswith(".xlsx")
    ]
    # Copy it files to parent batch dir and get the updated image paths
    image_paths = copy_files_to_parent_dir(
        train_batch, "train-batches", image_paths, "images"
    )
    excel_file_paths = copy_files_to_parent_dir(
        train_batch, "train-batches", excel_file_paths, "images"
    )
    image_paths.extend(excel_file_paths)

    # Build a filename-to-path lookup for the image paths, skipping non-string elements
    image_paths = {
        p.split("/")[-1].lower(): p for p in image_paths if isinstance(p, str)
    }

    return image_paths


def get_manual_classification_item(
    doc_type, image_path, file_index, page_index, file_name, auto_classified, image_file
):
    """Generate manual classification item detials"""
    manual_classification_item = {
        "user_classified_doc_type": "",
        "auto_classified_doc_type": "",
        "name_matching_doc_type": "",
        "trigger": [],
        "image_path": image_path,
        "score": "",
        "color": "yellow" if doc_type else "red",
        "file_index": file_index,
        "page_index": page_index,
        "file_name": file_name,
        "image_file": image_file,
    }

    if auto_classified:
        manual_classification_item["auto_classified_doc_type"] = (
            doc_type if doc_type else ""
        )
    else:
        manual_classification_item["name_matching_doc_type"] = (
            doc_type if doc_type else ""
        )

    return manual_classification_item


def copy_files_to_parent_dir(train_batch, sub_path, file_paths, destination_sub_dir):
    """
    Copy files to new parent directory and update path.

    Args:
        train_batch (object): Contain training batch data.
        sub_path (str): sub_path within the batch directory.
        file_paths (list): File paths to be copied.
        destination_sub_dir (str): Target sub directory name.

    Returns:
        new_file_paths (list): New file paths to the parent directory.

    Process Details:
        - Construct the target parent directory path using 'train_batch.id', 'sub_path' and 'destination_sub_dir'.
        - Create the destination directory if it does not already exist.
        - Iterate through each file in 'file_paths'then copy and update the file path.

    Notes:
        - Append updated paths to the new list and return it.
    """
    if not file_paths:
        return []

    parent_sub_dir = os.path.join(sub_path, train_batch.id, destination_sub_dir)
    destination_dir = os.path.join(BATCH_INPUT_PATH, parent_sub_dir)
    new_file_paths = []

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for file_path in file_paths:
        source_path = os.path.join(BATCH_INPUT_PATH, file_path)

        # Construct the full destination path
        base_name = os.path.basename(file_path)
        destination_path = os.path.join(destination_dir, base_name)

        # Copy the file to the destination
        shutil.copy2(source_path, destination_path)

        new_file_path = os.path.join(parent_sub_dir, base_name)
        new_file_paths.append(new_file_path)

    return new_file_paths


def organize_docs_inside_copy_batches_xml(copy_batches_xml_path):
    """
    Organize documents inside CopyBatches.xml file.

    Args:
        copy_batches_xml_path (str): Path of the CopyBatches.xml file.

    Process Details:
        - Parse the XML file.
        - Find and restructure <D> tags based on child element and attribute.
        - Adjust "ext" attribute for <D> tags depending on the parent image type.
        - Split <P> tags within <D> into new <D> tags.
        - Write the updated XML structure.

    Notes:
        - Use the "ParentImage" attribute to determine the file type for adjustment.
    """
    tree = ET.parse(copy_batches_xml_path)
    root = tree.getroot()

    new_d_tags = []

    D_tags = list(root.findall("D"))

    for D in D_tags:
        # Change `ext` value for <D> tags if fie_type `doc` or `docx`
        parent_image = ""

        for P in D.findall("./P"):
            if parent_image:
                break

            for V in P.findall(".//V"):
                if V.get("n") == "ParentImage":
                    parent_image = V.text
                    break

        ext_identifiers = ["ext", "EXT"]

        # Loop through ext identifiers and find the matching V tag
        for ext in ext_identifiers:
            v_tag = D.find(f'.//V[@n="{ext}"]')

            if v_tag is not None:
                if v_tag.text == ".tif":
                    continue

                if "docx" in parent_image.lower():
                    v_tag.text = ".docx"
                elif "doc" in parent_image.lower():
                    v_tag.text = ".doc"

        # Get all <P> tags and other elements within <D>
        P_tags = list(D.findall("P"))
        other_elements = [elem for elem in D if elem.tag != "P"]

        # Check if there's a <V> tag with n="ext" and text ".xlsx"
        target_v = next(
            (
                v.text
                for v in D.findall(".//V")
                if v.get("n") in ["ext", "EXT"] and v.text == ".xlsx"
            ),
            None,
        )

        if target_v and len(P_tags) > 0:
            # Parse the original id and prepare for incrementing
            original_id = D.get("id", "")
            id_parts = original_id.split(".")
            base_id = ".".join(id_parts[:-1])
            current_index = int(id_parts[-1])

            # Iterate over each <P> tag to create new <D> tags
            for i, P in enumerate(P_tags):
                new_D = ET.Element("D")

                # Copy attributes from the original <D> to the new <D> and increment the id
                new_D.attrib.update(D.attrib)
                new_D.set("id", f"{base_id}.{current_index + i:02}")

                new_D.append(deepcopy(P))
                for elem in other_elements:
                    new_D.append(deepcopy(elem))

                new_d_tags.append(new_D)

            # Remove the original <D> tag from <B>
            root.remove(D)

    # Add all newly created <D> tags to <B>
    for new_D in new_d_tags:
        root.append(new_D)

    # Save the modified XML back to the file
    tree.write(copy_batches_xml_path)


def get_info_from_copy_batches_xml(copy_batches_xml_path):
    """
    Get information from CopyBatches.xml file.

    Args:
        copy_batches_xml_path (str): Path of the CopyBatches.xml file.

    Returns:
        root_status (int): Current processing status.
        profile_name (str): Profile name from the XML file.
        batch_upload_mode (str): Batch upload mode can be training or processing .
        document_type (str): Document type defined in the XML.
        current_ocr (str): Combined OCR engine, language, page rotation, and barcode.
        doc_info (list): Document details.
        selected_doc_types (list): Selected document types.

    Process Details:
        - Parses the XML file.
        - Find v_tags then retrieve batch metadata.
        - Find and Process d_tags to extract specific attributes.
        - Update extensions based on document parent image type.
        - Split and process related paths and document types.

    Notes:
        - Return structured data for further processing and integration.
    """
    tree = ET.parse(copy_batches_xml_path)
    root = tree.getroot()
    v_tags = root.findall(".//V")

    root_status = None
    profile_name = None
    batch_upload_mode = None
    file_path = None

    for v_tag in v_tags:
        if all([profile_name, batch_upload_mode, file_path]):
            break

        if v_tag.get("n") == "bvICapProfile":
            profile_name = v_tag.text

        if v_tag.get("n") == "bvBatchType":
            batch_upload_mode = "processing" if v_tag.text == "Process" else "training"

        if v_tag.get("n") == "bvFilePath":
            file_path = v_tag.text

    file_paths = (
        split_with_escaped_commas(file_path)
        if file_path and file_path != "None"
        else []
    )

    v_tag_status = root.find("./V[@n='STATUS']")
    if v_tag_status is not None:
        root_status = v_tag_status.text

    print(f"{root_status=}")

    if root_status is None:
        root_status = 0

    return (
        int(root_status),
        profile_name,
        batch_upload_mode,
        file_paths,
    )


def split_with_escaped_commas(files):
    """Split string of file name by commas"""
    # Use regex to split by commas not preceded by a backslash
    file_list = re.split(r"(?<!\\),", files)

    # Replace escaped commas with real commas in file names
    file_list = [f.replace("\\,", ",").strip() for f in file_list]

    return file_list


def join_with_escaped_commas(file_list):
    """Join file_list into a string with commas just escaping commas in the file name."""
    # Replace any commas in the file names with '\,' and then join the list with ', '
    escaped_files = [file.replace(",", "\\,") for file in file_list]
    return ", ".join(escaped_files)


def document_matching_p1(
    write_parent_batch_log: Callable,
    job_id,
    parent_batch,
    matched_profile,
    merged_batch,
    batch_upload_mode,
    selected_doc_types=None,
):
    """
    Main function to document matching for batch files.

    Args:
        matched_profile (object): Document matching criteria.
        batch_id (str): ID for the current batch.
        batch_path (str): Path of batch files.
        batch_upload_mode (str): Batch upload mode can be training or processing .
        parent_batch (object): Additional data.
        selected_doc_types (list): Selected document types.

    Returns:
        page_wise_doc_types (list): Page wise document matching details.

    Process Details:
        - Retrieve document matching criteria 'matched_profile'.
        - For 'training' mode and only one document type is selected, matche specific document type directly.
        - List and sort all '_layout.xml' file paths from 'batch_path'.
        - Initialize 'page_wise_doc_types' to track document matching for each layout XML file.
        - Use predefined rules to auto-classify documents.
        - Matche document name against predefined patterns.
        - Handle unmatched case by applying fallback matching logic.
        - Normalize result and update 'page_wise_doc_types'.

    Notes:
        - Ensure consistency across matched document type and name.
        - Return consolidated result or individual page-wise matche.
    """
    profile_documents_dict, profile_documents = get_profile_doc_info(matched_profile)

    doc_info, file_identifiers, page_wise_doc_types = get_doc_info(
        parent_batch, merged_batch
    )

    job_info = redis_instance.get(job_id)
    job_info = json.loads(job_info)
    job_info = {
        **job_info,
        "doc_info": doc_info,
        "parent_batch_id": parent_batch.id,
        "profile_name": matched_profile.name,
        "page_wise_doc_types": page_wise_doc_types,
    }

    redis_instance.set(job_id, json.dumps(job_info))

    request_data = {"job_id": job_id}

    if batch_upload_mode == "training" and len(selected_doc_types) == 1:
        matched_doc = profile_documents_dict.get(selected_doc_types[0], None)

        if matched_doc:
            corresponding_doc = [
                {
                    "doc_type": matched_doc.doc_type,
                    "matched_doc": matched_doc,
                    "name_matching_text": matched_doc.name_matching_text,
                    "auto_classified": False,
                }
            ]
            corresponding_doc = convert_doc_instance_to_dict(corresponding_doc)
            job_info["matched_doc"] = corresponding_doc
            redis_instance.set(job_id, json.dumps(job_info))
            document_matching_p2(request_data)
            return

    if len(profile_documents.get("auto_match", [])):
        publish_to_classifier(
            write_parent_batch_log,
            job_id,
            parent_batch,
            merged_batch,
            matched_profile,
            file_identifiers,
            batch_upload_mode,
        )
        return
    document_matching_p2(request_data)


def document_matching_p2(request_data):
    """
    Main function to document matching for batch files.

    Args:
        matched_profile (object): Document matching criteria.
        batch_id (str): ID for the current batch.
        batch_path (str): Path of batch files.
        batch_upload_mode (str): Batch upload mode can be training or processing .
        parent_batch (object): Additional data.
        selected_doc_types (list): Selected document types.

    Returns:
        page_wise_doc_types (list): Page wise document matching details.

    Process Details:
        - Retrieve document matching criteria 'matched_profile'.
        - For 'training' mode and only one document type is selected, matche specific document type directly.
        - List and sort all '_layout.xml' file paths from 'batch_path'.
        - Initialize 'page_wise_doc_types' to track document matching for each layout XML file.
        - Use predefined rules to auto-classify documents.
        - Matche document name against predefined patterns.
        - Handle unmatched case by applying fallback matching logic.
        - Normalize result and update 'page_wise_doc_types'.

    Notes:
        - Ensure consistency across matched document type and name.
        - Return consolidated result or individual page-wise matche.
    """
    from pipeline.utils.process_batch_utils import write_parent_batch_log
    from pipeline.views import test_batch_cleanup

    print(f"{request_data=}")
    job_id = request_data.get("job_id")

    try:
        status_code = request_data.get("status_code")

        # Get job info from redis
        try:
            job_info = redis_instance.get(job_id)
            job_info = json.loads(job_info)
        except:
            print(f"Error parsing job_info for job_id: {job_id}")
            return
        
        # If matched doc is already available, continue classification process
        matched_doc = job_info.get("matched_doc")
        if matched_doc:
            request_data = {"job_id": job_id}

            publish(
                "continue_classification_process_queued", "to_pipeline", request_data
            )
            return

        doc_info = job_info["doc_info"]
        profile_name = job_info["profile_name"]
        parent_batch_id = job_info["parent_batch_id"]
        page_wise_doc_types = job_info["page_wise_doc_types"]
        selected_doc_types = job_info.get("selected_doc_types")
        batch_upload_mode = job_info.get("batch_upload_mode")
        doc_type_index_dict = {}

        matched_profile = Profile.objects.get(name=profile_name)
        profile_documents_dict, profile_documents = get_profile_doc_info(
            matched_profile
        )

        # Get parent batch instance
        if batch_upload_mode == "processing":
            parent_batch = EmailBatch.objects.get(id=parent_batch_id)
        else:
            parent_batch = TrainBatch.objects.get(id=parent_batch_id)

        page_wise_doc_types, doc_type_index_dict = handle_auto_classifier_response(
            write_parent_batch_log,
            request_data,
            status_code,
            parent_batch,
            page_wise_doc_types,
            profile_documents,
            profile_documents_dict,
            selected_doc_types,
            doc_type_index_dict,
        )

        page_wise_doc_types, exts = get_name_matching_doc_types(
            page_wise_doc_types,
            doc_info,
            profile_documents,
            selected_doc_types,
            doc_type_index_dict,
        )

        print(
            f"Name Matched Page Wise Doc Types: {[i['doc_type'] for i in page_wise_doc_types]}"
        )

        page_wise_doc_types, doc_type_index_dict = translate_matched_doc_types(
            write_parent_batch_log,
            parent_batch,
            batch_upload_mode,
            page_wise_doc_types,
            matched_profile,
            profile_documents_dict,
            selected_doc_types,
            doc_type_index_dict,
        )

        page_wise_doc_types = handle_none_doc_matching(
            matched_profile, page_wise_doc_types
        )

        print(
            f"Final Page Wise Doc Types: {[i['doc_type'] for i in page_wise_doc_types]}"
        )
        print(
            f"Final Matched Doc Types: {[i['matched_doc'].doc_type if i['matched_doc'] else None for i in page_wise_doc_types]}"
        )

        if not len(page_wise_doc_types):
            page_wise_doc_types = None

        # Checking if all classified document types are the same or not
        if (
            len(exts) == 1
            and all(
                x["doc_type"] == page_wise_doc_types[0]["doc_type"]
                for x in page_wise_doc_types
            )
            and all(
                x["name_matching_text"] == page_wise_doc_types[0]["name_matching_text"]
                for x in page_wise_doc_types
            )
            and doc_type_index_dict.get(page_wise_doc_types[0]["doc_type"]) == 0
        ):
            page_wise_doc_types = [page_wise_doc_types[0]]

        matched_doc = convert_doc_instance_to_dict(page_wise_doc_types)
        job_info.pop("page_wise_doc_types", None)
        job_info["matched_doc"] = matched_doc
        redis_instance.set(job_id, json.dumps(job_info))
        request_data = {"job_id": job_id}

        publish("continue_classification_process_queued", "to_pipeline", request_data)
    except Exception as e:
        print(f"Error in document_matching_p2: {str(e)}")
        print(traceback.format_exc())
        try:
            test_batch_cleanup(job_id)
        except:
            pass
        raise


def get_profile_doc_info(matched_profile):
    """Get document type list from matched profile"""
    profile_documents_qs = matched_profile.documents.all()

    profile_documents = {
        "auto_match": [],
        "name_match": [],
        "email_body": None,
    }
    profile_documents_dict = {}

    # Find email body document
    email_body_document_qs = profile_documents_qs.filter(
        content_location="Email Body"
    ).filter(category="Processing")

    if email_body_document_qs.exists():
        email_body_document = email_body_document_qs.first()

        profile_documents["email_body"] = email_body_document
        profile_documents_dict[email_body_document.doc_type] = email_body_document

    # Find attachment documents
    attachment_documents = profile_documents_qs.filter(
        content_location="Email Attachment"
    )

    for attachment_doc in attachment_documents:
        match_option = attachment_doc.name_matching_option

        if match_option == "Auto":
            profile_documents["auto_match"].append(attachment_doc)
        elif attachment_doc.category == "Processing":
            profile_documents["name_match"].append(attachment_doc)

        profile_documents_dict[attachment_doc.doc_type] = attachment_doc

    return profile_documents_dict, profile_documents


def get_doc_info(parent_batch, merged_batch):
    """File identifiers saved with parent batch"""
    ra_json = merged_batch.ra_json
    doc_info = []
    file_identifiers = []
    page_wise_doc_types = []

    start_index = 1

    for doc in ra_json["nodes"]:
        page_count = len(doc["children"])
        parent_image = None
        file_path = doc.get("file_path")
        end_index = start_index + page_count - 1

        if page_count:
            first_page = doc["children"][0]
            parent_image = first_page.get("ParentImage") or first_page.get("IMAGEFILE")

        doc_info.append(
            {
                "ext": doc.get("ext"),
                "page_count": page_count,
                "parent_image": parent_image,
                "file_path": file_path,
            }
        )

        file_identifiers.append((start_index, end_index))

        for page in doc["children"]:
            page_wise_doc_types.append(
                {
                    "doc_type": None,
                    "doc_type_index": 0,
                    "matched_doc": None,
                    "name_matching_text": "",
                    "image_file": page.get("IMAGEFILE"),
                    "auto_classified": False,
                }
            )

        start_index = end_index + 1

    try:
        parent_batch.file_identifiers = file_identifiers
        parent_batch.save()
    except:
        pass

    return doc_info, file_identifiers, page_wise_doc_types


def publish_to_classifier(
    write_parent_batch_log: Callable,
    job_id,
    parent_batch,
    merged_batch,
    matched_profile,
    file_identifiers,
    batch_upload_mode,
    message_type="title_classification",
):
    """
    Automatically classifies the doc type with the help of a matrix classifier.
    """
    ra_json_path = generate_ra_json_file_path(merged_batch)
    category, memory_points, page_directions = get_master_dictionaries_for_classifier()

    request_data = {
        "job_id": job_id,
        "transaction_id": parent_batch.id,
        "layout_xml_paths": [ra_json_path],
        "page_directions": page_directions,
        "profile": matched_profile.name,
        "project": matched_profile.project,
        "category": category,
        "memory_points": memory_points,
        "file_identifiers": file_identifiers,
        "automatic_splitting": matched_profile.automatic_splitting,
    }

    remarks = {
        k: v
        for k, v in request_data.items()
        if k not in {"category", "memory_points", "page_directions"}
    }

    message = "Auto Classification Request Queued" + (
        " for checking OCR Mismatch" if message_type == "ocr_mismatch" else ""
    )

    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message=message,
        remarks=json.dumps(remarks),
        action="display_json",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    publish(message_type, "to_classifier", request_data)


def generate_ra_json_file_path(merged_batch, manual_classification=False):
    sub_path = "train-batches" if manual_classification else merged_batch.sub_path
    batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, merged_batch.id)
    ra_json_path = os.path.join(batch_path, "ra_json.json")

    with open(ra_json_path, "w", encoding="utf-8") as f:
        json.dump(merged_batch.ra_json, f, indent=2, ensure_ascii=False)

    return ra_json_path


def get_master_dictionaries_for_classifier():
    """Get category & memory_points from master_dictionaries"""
    master_dictionaries_qs = MasterDictionary.objects.all()
    master_dictionaries = MasterDictionarySerializer(
        master_dictionaries_qs, many=True
    ).data

    master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}

    category = master_dictionaries.get("matrix_title_classification_category", {}).get(
        "data"
    )

    memory_points = master_dictionaries.get(
        "matrix_title_classification_memory_points", {}
    ).get("data")

    page_directions = master_dictionaries.get(
        "matrix_title_classification_priority_directions", {}
    ).get("data")

    return category, memory_points, page_directions


def normalize_auto_classified_doc_types(
    page_wise_doc_types,
    auto_classified_doc_types,
    profile_documents,
    profile_documents_dict,
    selected_doc_types,
    doc_type_index_dict,
):
    """
    Removes classified doc types that do not match with the automatically matchable doc types.
    """
    if not auto_classified_doc_types or not len(auto_classified_doc_types.keys()):
        return page_wise_doc_types, doc_type_index_dict

    auto_match_documents = [i.doc_type for i in profile_documents["auto_match"]]

    for key, value in auto_classified_doc_types.items():
        if (
            selected_doc_types and key not in selected_doc_types
        ) or key not in auto_match_documents:
            continue

        matched_doc = profile_documents_dict.get(key, None)

        for index, item in enumerate(value):
            for page_index in range(item[0] - 1, item[1]):
                try:
                    page_wise_doc_types[page_index] = {
                        **page_wise_doc_types[page_index],
                        "doc_type_index": index,
                        "doc_type": key,
                        "matched_doc": matched_doc,
                        "auto_classified": True,
                    }

                    doc_type_index_dict[key] = index
                except:
                    pass

    return page_wise_doc_types, doc_type_index_dict


def translate_matched_doc_types(
    write_parent_batch_log: Callable,
    parent_batch,
    batch_upload_mode,
    page_wise_doc_types,
    matched_profile,
    profile_documents_dict,
    selected_doc_types,
    doc_type_index_dict,
    message_type="title_classification_response",
):
    """
    Translate the doc types based on the translated_documents list.
    """
    translated_documents = matched_profile.translated_documents or []
    if not translated_documents:
        return page_wise_doc_types, doc_type_index_dict

    translated_page_wise_doc_types = [*page_wise_doc_types]
    remarks = []
    original_doc_types_in_remarks = set()

    for item in translated_page_wise_doc_types:
        doc_type = item.get("doc_type")
        if not doc_type:
            continue

        translated_doc_type, translated_matched_doc = get_translated_doc_type(
            doc_type, translated_documents, profile_documents_dict, selected_doc_types
        )

        if not translated_doc_type:
            continue

        item["doc_type"] = translated_doc_type
        item["matched_doc"] = translated_matched_doc

        # Update doc type index
        doc_type_index = 0

        if doc_type_index_dict.get(doc_type):
            doc_type_index = doc_type_index_dict[doc_type]
            del doc_type_index_dict[doc_type]

        doc_type_index_dict[translated_doc_type] = doc_type_index

        if doc_type in original_doc_types_in_remarks:
            continue

        detail_item = {
            "original_doc_type": doc_type,
            "translated_doc_type": translated_doc_type,
        }
        remarks.append(detail_item)
        original_doc_types_in_remarks.add(doc_type)

    if remarks:
        message = "Translated Doc Types"
        if message_type == "ocr_mismatch_response":
            message = "Checking Translated Doc Types for OCR Mismatches"
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message=message,
            remarks=json.dumps(remarks),
            action="display_table",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        print(
            f"Translated Page Wise Doc Types: {[i['doc_type'] for i in translated_page_wise_doc_types]}"
        )

    return translated_page_wise_doc_types, doc_type_index_dict


def get_translated_doc_type(
    doc_type, translated_documents, profile_documents_dict, selected_doc_types
):
    translated_documents_dict = {
        item["doc_type"]: item["translated_doc_type"] for item in translated_documents
    }

    translated_doc_type = None
    translated_matched_doc = None

    translated_doc_type = translated_documents_dict.get(doc_type)

    if selected_doc_types and translated_doc_type not in selected_doc_types:
        translated_doc_type = None

    if translated_doc_type:
        translated_matched_doc = profile_documents_dict.get(translated_doc_type)

    return translated_doc_type, translated_matched_doc


def get_name_matching_doc_types(
    page_wise_doc_types,
    doc_info,
    profile_documents,
    selected_doc_types,
    doc_type_index_dict,
):
    """
    Manually classify the doc types based on the name-matching criteria.
    """
    final_page_wise_doc_types = [*page_wise_doc_types]
    exts = []

    start_index = 0

    # Looping through each document
    for doc in doc_info:
        ext = doc.get("ext")

        if ext not in exts:
            exts.append(ext)

        end_index = start_index + doc["page_count"]

        # Finding matched_doc info
        updated_page_wise_doc_type, doc_type, doc_type_index = get_matched_doc_info(
            profile_documents,
            doc["file_path"],
            selected_doc_types,
            doc_type_index_dict,
        )

        # Looping through each pages of document to update doc_type
        for index in range(start_index, end_index):
            doc_type_index_dict[doc_type] = doc_type_index
            current_doc = final_page_wise_doc_types[index]
            updated_doc = updated_page_wise_doc_type

            if index >= len(page_wise_doc_types):
                updated_doc["layout_xml_file"] = None
                final_page_wise_doc_types.append(updated_doc)
                continue

            should_full_update = (
                # current_doc["doc_type"] is None and
                updated_doc["doc_type"]
                is not None
            )

            if should_full_update:
                current_doc.update(updated_doc)
            else:
                current_doc["file_name"] = updated_doc["file_name"]
        start_index = end_index

    return final_page_wise_doc_types, exts


def get_matched_doc_info(
    profile_documents, file_path, selected_doc_types, doc_type_index_dict
):
    file_name = os.path.basename(file_path)
    doc_type = None
    name_matching_text = ""

    matched_doc = match_attachment(
        profile_documents["name_match"],
        profile_documents["email_body"],
        file_path,
    )

    if matched_doc:
        doc_type = matched_doc.doc_type
        name_matching_text = matched_doc.name_matching_text

        if selected_doc_types and doc_type not in selected_doc_types:
            doc_type = None
            matched_doc = None
            name_matching_text = ""

    # find doc_type_index
    if doc_type_index_dict.get(doc_type) is not None:
        doc_type_index = doc_type_index_dict[doc_type] + 1
    else:
        doc_type_index = 0

    updated_page_wise_doc_type = {
        "file_name": file_name,
        "doc_type": doc_type,
        "doc_type_index": doc_type_index,
        "matched_doc": matched_doc,
        "name_matching_text": name_matching_text,
        "auto_classified": False,
    }

    return updated_page_wise_doc_type, doc_type, doc_type_index


def match_attachment(attachment_documents, email_body_document, file_path):
    """
    Match email attachment with Profile Document.

    Args:
        attachment_documents (list): Attachment documents metadata.
        email_body_document (object): Metadata of email body document.
        file_path (str): Path of the attachment file.

    Returns:
        matched_doc (object): Matched document object.

    Process Details:
        - Extract attachment name from the file path.
        - Check the attachment matche the email body document.
        - Iterate through attachment_doc and check matching criteria.
        - Return the first matched_doc or None.

    Notes:
        - Regex matching is used on the full attachment name.
    """
    matched_doc = None
    attachment_name = os.path.basename(file_path)
    attachment_name_lower = attachment_name.lower()

    if email_body_document and re.search(
        r"email_file(_\d+)?\.pdf$", attachment_name_lower
    ):
        return email_body_document

    for attachment_doc in attachment_documents:
        match_option = attachment_doc.name_matching_option
        match_text = attachment_doc.name_matching_text.lower()

        if match_option == "StartsWith":
            if attachment_name_lower.startswith(match_text):
                matched_doc = attachment_doc
                break
        elif match_option == "EndsWith":
            if attachment_name_lower.endswith(match_text):
                matched_doc = attachment_doc
                break
        elif match_option == "Contains":
            if match_text in attachment_name_lower:
                matched_doc = attachment_doc
                break
        elif match_option == "Regex":
            matches = re.findall(attachment_doc.name_matching_text, attachment_name)
            if matches:
                matched_doc = attachment_doc
                break

    return matched_doc


def handle_none_doc_matching(matched_profile, page_wise_doc_types):
    """
    Handle None type document matching with profile.

    Args:
        matched_profile (object): matched_profile contain documents data.
        page_wise_doc_types (list): Page wise document types.

    Returns:
        page_wise_doc_types (list): Updated page wise document types.

    Process Details:
        - Retrieve unmatched documents from page_wise_doc_types.
        - Find out unmatched processing document in the profile.
        - Assign to all unmatched entries in page_wise_doc_types.

    Notes:
        - Handle documents which content_location is 'Email Attachment'.
    """
    print(f"File Names: {[i['file_name'] for i in page_wise_doc_types]}")

    none_processing_doc_qs = matched_profile.documents.filter(
        content_location="Email Attachment",
        name_matching_option="",
        category="Processing",
    )

    if none_processing_doc_qs.count() != 1:
        return page_wise_doc_types

    matched_doc = none_processing_doc_qs.first()

    not_matched = [i for i in page_wise_doc_types if not i.get("matched_doc")]

    if all(x["file_name"] == not_matched[0]["file_name"] for x in not_matched):
        for i in page_wise_doc_types:
            if not i.get("matched_doc"):
                i["matched_doc"] = matched_doc

    return page_wise_doc_types


def update_matched_docs(matched_docs, doc_info):
    """
    Update matched documents and split pdf if needed.

    Args:
        matched_docs (list): Matched documents data.
        doc_info (list): Documents with information.

    Returns:
        matched_docs (list): Updated matched documents.

    Process Details:
        - Iterate through 'doc_info' and update 'matched_docs'.
        - Group pages by 'doc_type' and determine splitting.
        - Split pdf if pages belong to multiple document types.

    Notes:
        - Document with .doc or .docx extension are not split.
    """
    start_index = 0

    for doc in doc_info:
        file_path = doc["file_path"]
        parent_image = doc["parent_image"]
        ext = doc["ext"]

        end_index = start_index + doc["page_count"]

        page_indexes_by_doc_type = {}

        for index in range(start_index, end_index):
            matched_docs[index]["file_path"] = file_path
            matched_docs[index]["parent_image"] = parent_image
            matched_docs[index]["ext"] = ext
            matched_docs[index]["splitted"] = False

            doc_type = matched_docs[index]["doc_type"]
            try:
                if page_indexes_by_doc_type[doc_type]:
                    page_indexes_by_doc_type[doc_type].append(index - start_index)
            except:
                page_indexes_by_doc_type[doc_type] = [index - start_index]

        # Split pdf if needed
        if (
            len(page_indexes_by_doc_type) != 1
            and not file_path.lower().endswith((".doc", ".docx"))
            and not re.search(r"email_file_\d+\.pdf$", file_path.lower())
        ):
            page_indexes_list = list(page_indexes_by_doc_type.values())
            splitted_file_paths = split_pdf(file_path, page_indexes_list)

            for index, splitted_file_path in enumerate(splitted_file_paths):
                for page_index in page_indexes_list[index]:
                    matched_docs[page_index + start_index][
                        "file_path"
                    ] = splitted_file_path
                    matched_docs[page_index + start_index]["splitted"] = True
        start_index = end_index

    return matched_docs


def create_supporting_batch(
    batch_id, profile, matched_doc, file_path, publish_to_assembly=False
):
    """Create supporting document in the DB"""
    file_extension = os.path.splitext(file_path)[1]
    status = "waiting" if profile.manual_validation else "completed"

    # Remove the batch if already uploaded:
    try:
        Batch.objects.get(id=batch_id).delete()
    except Batch.DoesNotExist:
        pass

    Batch.objects.create(
        id=batch_id,
        type=matched_doc.doc_type,
        definition_id=profile.name,
        # vendor=profile.customer_name,
        project=profile.project,
        extension=file_extension,
        mode="supporting",
        status=status,
    )

    output_json = {}

    OutputJson.objects.create(output_json=output_json, batch_id=batch_id)

    if publish_to_assembly:
        request_data = {"batch_id": batch_id}

        publish("assembly_queued", "to_pipeline", request_data)


def handle_multiple_matching_doc_types(
    write_parent_batch_log: Callable,
    upload_batch_process: Callable,
    matched_profile,
    matched_docs,
    doc_info,
    batch_path,
    sub_path,
    batch_id,
    batch_upload_mode,
):
    try:
        (
            instanceToBatchLink,
            instanceParsedDocument,
            parent_batch,
            parent_batch_kwarg,
            *tail,
        ) = get_instance_classes(batch_id)

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Batch splitting initiated",
            remarks=json.dumps({"batch_id": batch_id}),
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        instanceToBatchLink.objects.get(batch_id=batch_id).delete()
        instanceParsedDocument.objects.filter(batch_id=batch_id).delete()
        save_analyzer_log_time(batch_id=parent_batch.id, field_name="batch_splitting_s")

        matched_docs = update_matched_docs(matched_docs, doc_info)

        pages_by_doc_type = get_pages_by_doc_type(matched_docs)

        batches_to_upload = []

        # Generate batch folder for splitted batches
        split_index = 0
        for element in pages_by_doc_type.values():
            for item in element.values():
                new_batch_id = create_split_batch(
                    batch_path,
                    split_index,
                    item,
                    batch_id,
                    batch_upload_mode,
                    sub_path,
                    item["ext"],
                )

                split_index += 1

                batches_to_upload.append(
                    {
                        "batch_id": new_batch_id,
                        "matched_doc": item["matched_doc"],
                        "file_paths": item["file_paths"],
                    }
                )

                instanceToBatchLink.objects.create(
                    **parent_batch_kwarg,
                    batch_id=new_batch_id,
                    classified=True,
                    mode=batch_upload_mode,
                )

                for index, file_path in enumerate(item["file_paths"]):
                    file_name = os.path.basename(file_path)
                    instanceParsedDocument.objects.create(
                        **parent_batch_kwarg,
                        batch_id=new_batch_id,
                        name=file_name,
                        path=file_path,
                        type="attachment",
                        matched_profile_doc=item["matched_doc"],
                        splitted=item["splitted"][index],
                        ra_json_created=True,
                    )

                details = {
                    "batch_id": new_batch_id,
                    "parent_batch_id": batch_id,
                    "file": join_with_escaped_commas(item["file_paths"]),
                }

                save_analyzer_log_time(
                    batch_id=parent_batch.id, field_name="batch_creation_time"
                )
                write_parent_batch_log(
                    batch_id=parent_batch.id,
                    status="inprogress",
                    message="Batch Created",
                    remarks=json.dumps(details),
                    action="display_key_values",
                    train_batch_log=True if batch_upload_mode == "training" else False,
                )

        # Upload batches
        for item in batches_to_upload:
            if not item["matched_doc"]:
                link_additional_batch(
                    matched_profile,
                    parent_batch,
                    is_training=True if batch_upload_mode == "training" else False
                )
                continue

            # Create a supporting batch if a supporting document exists
            if item["matched_doc"].category == "Supporting":
                create_supporting_batch(
                    item["batch_id"],
                    matched_profile,
                    item["matched_doc"],
                    doc_info[0]["file_path"],
                    publish_to_assembly=True,
                )
                instanceToBatchLink.objects.filter(batch_id=item["batch_id"]).update(
                    uploaded=True, mode="supporting"
                )
                continue

            instanceToBatchLink.objects.filter(batch_id=item["batch_id"]).update(
                uploaded=True
            )
            save_analyzer_log_time(
                batch_id=parent_batch.id, field_name="upload_batch_process_time"
            )
            print(f"{item['batch_id']}: upload_batch_process called")
            upload_batch_process(item["batch_id"], batch_upload_mode, sub_path)
        save_analyzer_log_time(batch_id=parent_batch.id, field_name="batch_splitting_e")
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Batch splitting completed",
            remarks=json.dumps({"batch_id": batch_id}),
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )
    except ValueError as ve:
        trace = traceback.format_exc()
        print(trace)
        error_message = ve.args[0]
        raise ValueError(error_message)
    except Exception as error:
        trace = traceback.format_exc()
        print(trace)
        raise ValueError(
            f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}."
        )


def recreate_datacap_batch(
    write_parent_batch_log: Callable,
    matched_profile,
    matched_doc,
    batch_id,
    file_paths,
    extension,
    selected_doc_types=None,
    batch_type="Process",
):
    """
    Recreate datacap batch
    """
    try:
        batch_upload_mode = "processing" if batch_type == "Process" else "training"
        datacap = DataCap()
        file_paths_str = join_with_escaped_commas(file_paths)

        page_file = generate_datacap_page_file(
            matched_profile,
            matched_doc,
            batch_type,
            file_paths_str,
            ",".join(selected_doc_types) if selected_doc_types else None,
        )

        files = [create_inmemory_file(file_path) for file_path in file_paths]
        try:
            details = datacap.create_batch(
                files=files,
                page_file=page_file,
                delayed_release=True,
            )
        except Exception as error:
            raise ValueError(
                f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}."
            )

        (
            instanceToBatchlink,
            instanceParsedDocument,
            parent_batch,
            parent_batch_kwarg,
            *tail,
        ) = get_instance_classes(batch_id, batch_upload_mode)

        datacap_batch_id = details["batch_id"]

        Batch.objects.create(
            id=datacap_batch_id,
            definition_id=parent_batch.matched_profile_name,
            extension=extension,
            visible=False,
        )

        instanceToBatchlink.objects.create(
            **parent_batch_kwarg,
            batch_id=datacap_batch_id,
            classified=True,
            mode=batch_upload_mode,
        )

        instanceParsedDocument.objects.filter(batch_id=batch_id).update(
            batch_id=datacap_batch_id, ra_json_created=False
        )

        details["previous_batch_id"] = batch_id
        details["file"] = join_with_escaped_commas(file_paths)
        details = json.dumps(details)

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Datacap Batch Recreated",
            remarks=details,
            action="display_key_values",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )
    except Exception as error:
        raise ValueError(
            f"Datacap batch was not created properly, please reprocess the {batch_upload_mode}."
        )


def split_pdf(file_path, page_indexes_list):
    """Split pdf based on page indexes list"""
    splitted_file_paths = []
    try:
        with open(file_path, "rb") as file:
            pdf = PyPDF2.PdfReader(file)

            # Save pdfs to disk
            for index, page_indexes in enumerate(page_indexes_list):
                splitted_file_path = file_path.split("/")
                file_name = splitted_file_path[-1]
                file_name = f"{file_name.split('.pdf')[0]}_splitted_{index + 1}.pdf"
                splitted_file_path[-1] = file_name
                splitted_file_path = "/".join(splitted_file_path)

                pdf_writer = PyPDF2.PdfWriter()

                for page_index in page_indexes:
                    try:
                        pdf_writer.add_page(pdf.pages[page_index])
                    except IndexError:
                        raise ValueError(
                            f"Page index {page_index} is out of range for '{file_name}'. "
                            "Check the document or reprocess it."
                        )

                with open(splitted_file_path, "wb") as output_file:
                    pdf_writer.write(output_file)

                splitted_file_paths.append(splitted_file_path)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"File '{file_path}' not found. Check the path or reprocess it."
        )

    return splitted_file_paths


def handle_single_matching_doc_type(
    batch_id,
    matched_profile,
    matched_doc,
    doc_info,
    batch_upload_mode,
):
    upload_batch = True

    _, instanceParsedDocument, *tail = get_instance_classes(batch_id)

    instanceParsedDocument.objects.filter(batch_id=batch_id).update(
        matched_profile_doc=matched_doc, ra_json_created=True
    )

    # Create a supporting batch if a supporting document exists.
    if matched_doc.category == "Supporting":
        create_supporting_batch(
            batch_id, matched_profile, matched_doc, doc_info[0]["file_path"]
        )

        upload_batch = False
    else:
        # Update Doc Type
        batch_instance = Batch.objects.get(id=batch_id)
        ra_json = batch_instance.ra_json
        ra_json["DocumentType"] = matched_doc.doc_type
        ra_json["DocType"] = matched_doc.doc_type  # Also set DocType for consistency

        # Update DocType in each node so auto-extraction can use it
        for node in ra_json.get("nodes", []):
            node["DocType"] = matched_doc.doc_type
            node["DocumentType"] = matched_doc.doc_type

        batch_instance.ra_json = ra_json
        batch_instance.save()

    return upload_batch


def get_pages_by_doc_type(matched_docs):
    """
    Separate pages based on their document type.

    Args:
        matched_docs (list): Matched document metadata.

    Returns:
        pages_by_doc_type (dict): Categorize pages by document type.

    Process Details:
        - Iterate through the matched_docs list.
        - Extract pages based on 'doc_type' and 'ext_with_name_matching'.
        - Populate pages with document metadata.

    Notes:
        - Create nested dictionaries for organizing data.
    """
    pages_by_doc_type = {}

    for matched_doc in matched_docs:
        doc_type = matched_doc.get("doc_type")
        ext = matched_doc.get("ext")
        name_matching_text = matched_doc.get("name_matching_text")
        ext_with_name_matching = f"{ext}_{name_matching_text}"

        try:
            pages_by_doc_type[doc_type][ext_with_name_matching][
                "doc_type_indexs"
            ].append(matched_doc.get("doc_type_index"))

            pages_by_doc_type[doc_type][ext_with_name_matching]["image_files"].append(
                matched_doc.get("image_file")
            )

            pages_by_doc_type[doc_type][ext_with_name_matching]["parent_images"].append(
                matched_doc.get("parent_image")
            )

            pages_by_doc_type[doc_type][ext_with_name_matching]["splitted"].append(
                matched_doc.get("splitted")
            )

            if (
                matched_doc.get("file_path")
                not in pages_by_doc_type[doc_type][ext_with_name_matching]["file_paths"]
            ):
                pages_by_doc_type[doc_type][ext_with_name_matching][
                    "file_paths"
                ].append(matched_doc.get("file_path"))
        except:
            ext_value = {
                "doc_type": matched_doc.get("doc_type"),
                "matched_doc": matched_doc.get("matched_doc"),
                "doc_type_indexs": [matched_doc.get("doc_type_index")],
                "image_files": [matched_doc.get("image_file")],
                "parent_images": [matched_doc.get("parent_image")],
                "file_paths": [matched_doc.get("file_path")],
                "ext": ext,
                "splitted": [matched_doc.get("splitted")],
            }

            try:
                pages_by_doc_type[doc_type][ext_with_name_matching] = ext_value
            except:
                pages_by_doc_type[doc_type] = {ext_with_name_matching: ext_value}

    return pages_by_doc_type


def create_split_batch(
    batch_path, index, item, batch_id, batch_upload_mode, sub_path, extension
):
    """
    Create new batch folder for specific document type.

    Args:
        batch_path (str): Path to the batch folder.
        index (int): Index for batch folders.
        item (dict): Contain document related information.

    Returns:
        tuple: Batch ID (str) and list of page IDs.
        batch_id (str):
        page_ids (list):

    Process Details:
        - Get batch_id using index.
        - Create new batch folder by copying the source_folder.
        - Extract page_ids and files from the layout XML.
        - Identify parent_images.
        - Clean up unnecessary files from the new batch folder.

    Notes:
        - Remove existing folder if it already exists.
    """
    # page_ids, page_files = get_page_info(item)

    page_ids, page_files = get_page_info(item)

    new_batch_id = create_destination_folder(batch_path, index, item, page_files)

    # Create batch to DB:
    try:
        Batch.objects.get(id=new_batch_id).delete()
    except Batch.DoesNotExist:
        pass

    batch_instance = Batch.objects.create(
        id=new_batch_id,
        mode=batch_upload_mode,
        sub_path=sub_path,
        extension=extension,
        visible=False,
    )

    new_ra_json = create_split_ra_json(item, batch_id, new_batch_id, page_ids)

    batch_instance.ra_json = new_ra_json
    batch_instance.save()

    return new_batch_id


def create_destination_folder(batch_path, index, item, page_files):
    source_folder = batch_path

    destination_folder = batch_path.split("/")
    batch_id = destination_folder[-1]
    batch_id = f"{batch_id.split('.')[0]}.S{index + 1}{batch_id.split('.')[-1]}"
    destination_folder[-1] = batch_id
    destination_folder = "/".join(destination_folder)

    try:
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)

        shutil.copytree(source_folder, destination_folder)
    except:
        print(traceback.print_exc())

    parent_images = []

    for parent_image in item["parent_images"]:
        parent_image_parts = parent_image.split(".")
        base_name = parent_image_parts[0]
        ext = parent_image_parts[-1]
        parent_image_upper = f"{base_name.upper()}.{ext}"
        parent_image_lower = f"{base_name.lower()}.{ext}"

        if parent_image_upper in parent_images:
            continue

        parent_images.append(parent_image_upper)
        parent_images.append(parent_image_lower)

    clean_destination_folder(destination_folder, page_files + parent_images)

    return batch_id


def get_page_info(item):
    """
    Get page_ids and files from layout xml file.

    Args:
        item (dict): Contain document information.

    Returns:
        page_ids_by_doc_index (dict): page_ids by document index.
        page_files (list): List of page files.

    Process Details:
        - Iterate over layout XML files.
        - Parse layout file name to extract page_id.
        - Collect associated files.

    Notes:
        - Generate uppercase and lowercase variants of page_ids and filenames.
    """
    page_ids_by_doc_index = {}
    page_files = []

    for index, image_file in enumerate(item["image_files"]):
        doc_type_index = item["doc_type_indexs"][index]

        page_id = os.path.splitext(image_file)[0]

        page_id_upper = page_id.upper()
        page_id_lower = page_id.lower()

        try:
            page_ids_by_doc_index[doc_type_index].append(page_id_upper)
            page_ids_by_doc_index[doc_type_index].append(page_id_lower)
        except:
            page_ids_by_doc_index[doc_type_index] = [page_id_upper, page_id_lower]

        page_files.append(f"{page_id_upper}.tif")
        page_files.append(f"{page_id_lower}.tif")
        page_files.append(f"{page_id_upper}.ocra.tif")
        page_files.append(f"{page_id_lower}.ocra.tif")
        page_files.append(f"{page_id_upper}.tio")
        page_files.append(f"{page_id_lower}.tio")
        page_files.append(f"{page_id_upper}.txt")
        page_files.append(f"{page_id_lower}.txt")

    return page_ids_by_doc_index, page_files


def clean_destination_folder(destination_folder, page_files):
    """Clean up batch folder by removing unnecessary files"""
    # List of file extensions to delete
    file_extensions = [
        ".tif",
        ".tio",
        ".txt",
        ".xml",
        ".pdf",
        ".doc",
        ".docx",
    ]

    # Construct a list of glob patterns for the files to be deleted
    glob_patterns = []

    for ext in file_extensions:
        # Add both lowercase and uppercase extensions to the pattern list
        glob_patterns.append(os.path.join(destination_folder, f"*{ext.lower()}"))
        glob_patterns.append(os.path.join(destination_folder, f"*{ext.upper()}"))

    # Iterate through each pattern, find matching files, and delete them
    for pattern in glob_patterns:
        for file_path in glob.glob(pattern):
            file_name = os.path.basename(file_path)

            if file_name in page_files:
                continue

            os.remove(file_path)


def create_split_ra_json(item, old_batch_id, new_batch_id, page_ids):
    original_ra_json = Batch.objects.get(id=old_batch_id).ra_json
    updated_ra_json = deepcopy(original_ra_json)
    updated_ra_json["id"] = new_batch_id
    doc_type = item["matched_doc"].doc_type if item["matched_doc"] else None
    updated_ra_json["DocumentType"] = doc_type
    updated_ra_json["DocType"] = doc_type  # Also set DocType for consistency
    updated_ra_json["nodes"] = []

    doc_counter = 0  # Use a counter for unique document IDs

    for doc in original_ra_json.get("nodes", []):
        if "children" not in doc or not isinstance(doc["children"], list):
            continue

        for page_id_list in page_ids.values():
            new_doc = deepcopy(doc)

            new_doc["children"] = [
                page for page in new_doc["children"] if page["id"] in page_id_list
            ]

            if new_doc["children"]:
                doc_counter += 1
                new_doc["id"] = f"{new_batch_id}.{doc_counter:02d}"
                # Set DocType in each node for auto-extraction
                new_doc["DocType"] = doc_type
                new_doc["DocumentType"] = doc_type
                updated_ra_json["nodes"].append(new_doc)

    return updated_ra_json


def post_classification_process(
    write_parent_batch_log: Callable,
    parent_batch,
    batch_upload_mode,
    matched_profile,
):
    """
    Post classification process and checking unmatched documents
    """
    (
        instanceToBatchLink,
        instanceParsedDocument,
        _,
        __,
        parent_batch_id_kwarg,
        *tail,
    ) = get_instance_classes(
        batch_upload_mode=batch_upload_mode, parent_batch=parent_batch
    )

    unclassified_batches = list(
        instanceToBatchLink.objects.filter(**parent_batch_id_kwarg, classified=False)
    )
    project = matched_profile.project

    if not len(unclassified_batches):
        linked_batches = list(
            instanceToBatchLink.objects.filter(**parent_batch_id_kwarg).values_list(
                "batch_id", flat=True
            )
        )

        linked_batches.append(f"AD{parent_batch.id}")

        files_list = list(
            instanceParsedDocument.objects.filter(batch_id__in=linked_batches).values(
                "name",
                "path",
                "type",
                "splitted",
                "matched_profile_doc__doc_type",
                "matched_profile_doc__category",
            )
        )

        is_processing_document_exists = any(
            i["matched_profile_doc__category"] == "Processing" for i in files_list
        )

        # Generate remarks table content
        remarks = []
        unmatched_attachments = 0

        for item in files_list:
            if item["matched_profile_doc__doc_type"]:
                doc_type = item["matched_profile_doc__doc_type"]
                match_details = f"Matched ({doc_type})"

            # Saifur - Additional document type based on project
            elif is_processing_document_exists and is_imd_enabled_for_project(project):
                additional_doc_type = get_additional_doc_type(project)

                match_details = f"Additional Document ({additional_doc_type})"

                if batch_upload_mode == "processing":
                    parent_batch.additional_docs_to_upload.append(
                        {"name": item["name"], "path": item["path"], "uploaded": False}
                    )
                    parent_batch.save()
            else:
                match_details = "Not Matched"
                unmatched_attachments += 1
            detail_item = {
                "file_name": item["name"],
                "status": match_details,
            }
            remarks.append(detail_item)

        remarks = sorted(remarks, key=lambda item: item["file_name"])
        save_analyzer_log_time(
            batch_id=parent_batch.id, field_name="document_matching_e"
        )
        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message="Document matching completed",
            remarks=json.dumps(remarks),
            action="display_table",
            train_batch_log=True if batch_upload_mode == "training" else False,
        )

        if unmatched_attachments:
            print(
                f"Process stopped due to {unmatched_attachments} unmatched attachments"
            )
            raise ValueError(
                f"Process stopped due to {unmatched_attachments} unmatched attachments"
            )

        if not is_processing_document_exists:
            print(f"Process stopped due to no processing documents")
            raise ValueError(f"Process stopped due to no processing documents")

        message = "Classification process completed"

        if batch_upload_mode == "processing":
            save_analyzer_log_time(
                batch_id=parent_batch.id, field_name="classification_process_e"
            )
            message = "Classification process completed. Awaiting assembly process."

        write_parent_batch_log(
            batch_id=parent_batch.id,
            status="inprogress",
            message=message,
            train_batch_log=True if batch_upload_mode == "training" else False,
        )


def get_merged_batch(
    write_parent_batch_log: Callable, get_new_batch_id: Callable, batch_id
):
    """
    Combine multiple batches into a single batch with renamed files and updated references.

    Args:
        batch_id: ID of the batch to be merged

    Returns:
        Batch: The merged batch instance
    """
    # Get instance classes for the batch
    (
        instanceToBatchLink,
        _,
        parent_batch,
        ___,
        parent_batch_id_kwarg,
        batch_upload_mode,
    ) = get_instance_classes(batch_id)

    # Get linked batches
    linked_batches = list(
        instanceToBatchLink.objects.filter(
            **parent_batch_id_kwarg, mode__in=["processing", "training"]
        ).values_list("batch_id", flat=True)
    )

    # Get batch queryset
    batch_qs = Batch.objects.filter(
        id__in=linked_batches, extension__in=(".pdf", ".docx")
    )
    if not batch_qs.exists():
        return None, []

    if batch_qs.count() == 1:
        return batch_qs.first(), [batch_qs.first().id]

    # Generate a new batch_id with the prefix M, indicating it’s a merged batch.
    merged_batch_id = get_new_batch_id(infix="M")

    # Combine RA JSON
    merged_ra_json = _combine_ra_json(batch_qs)

    # Process file renaming
    files_to_rename = _process_file_renaming(merged_ra_json, merged_batch_id)

    # Create and populate destination folder
    _create_merged_batch_folder(batch_qs, merged_batch_id, files_to_rename)

    # Update the first batch with merged data
    merged_batch = Batch.objects.create(id=merged_batch_id, visible=False)

    details = {
        "batch_id": merged_batch_id,
        "parent_batch_ids": [i.id for i in batch_qs],
    }

    write_parent_batch_log(
        batch_id=parent_batch.id,
        status="inprogress",
        message="Merged Batch Created",
        remarks=json.dumps(details),
        action="display_key_values",
        train_batch_log=True if batch_upload_mode == "training" else False,
    )

    field_names = [f.name for f in batch_qs.first()._meta.fields if f.name != "id"]

    for field in field_names:
        setattr(merged_batch, field, getattr(batch_qs.first(), field))

    merged_batch.ra_json = merged_ra_json
    merged_batch.save()

    linked_batches_to_delete = [batch.id for batch in batch_qs]
    # Reomve all existing batch
    batch_qs.delete()

    return merged_batch, linked_batches_to_delete


def _combine_ra_json(batch_qs):
    """Combine RA JSONs from multiple batches."""
    merged_ra_json = {}

    for batch_instance in batch_qs:
        if not merged_ra_json:
            merged_ra_json = batch_instance.ra_json
        else:
            merged_ra_json["nodes"].extend(batch_instance.ra_json["nodes"])

    return merged_ra_json


def _process_file_renaming(merged_ra_json, merged_batch_id):
    """Process file renaming for PDF files and page IDs."""
    tm_seq_no = 1
    files_to_rename = {}

    # Rename PDF files
    for doc in merged_ra_json["nodes"]:
        if not doc.get("children"):
            continue

        # Process PDF file renaming
        tm_seq_no = _rename_pdf_file(doc, tm_seq_no, files_to_rename)

    # Rename PAGE_IDs
    for doc in merged_ra_json["nodes"]:
        if not doc.get("children"):
            continue

        # Process page ID renaming
        tm_seq_no = _rename_page_ids(doc, tm_seq_no, files_to_rename)

    # Rename batch_id in ra_json
    project_name = get_project_by_profile(merged_ra_json["DefinitionID"])
    merged_ra_json["id"] = merged_batch_id
    merged_ra_json["Project"] = project_name

    for doc_index, doc in enumerate(merged_ra_json["nodes"], start=1):
        suffix = f"{doc_index:02d}"
        new_doc_id = f"{merged_batch_id}.{suffix}"
        doc["id"] = new_doc_id

    return files_to_rename


def _rename_pdf_file(doc, tm_seq_no, files_to_rename):
    """Rename PDF file for a document node."""
    if not doc["children"]:
        return tm_seq_no

    first_page = doc["children"][0]
    pdf_file = first_page.get("ParentImage")
    if not pdf_file:
        return tm_seq_no

    next_pdf_file = f"tm{str(tm_seq_no).zfill(6)}.pdf"

    # Skip if already correctly named
    if pdf_file.lower() == next_pdf_file:
        return tm_seq_no + 1

    # Update rename list
    batch_id = doc["id"].rsplit(".", 1)[0]

    if batch_id not in files_to_rename:
        files_to_rename[batch_id] = {}

    files_to_rename[batch_id][pdf_file] = next_pdf_file

    # Update ParentImage in all pages
    for page in doc["children"]:
        page["ParentImage"] = next_pdf_file

    return tm_seq_no + 1


def _rename_page_ids(doc, tm_seq_no, files_to_rename):
    """Rename page IDs for a document node."""
    batch_id = doc["id"].rsplit(".", 1)[0]

    for page in doc["children"]:
        page_id = page.get("id")
        if not page_id:
            continue

        next_page_id = f"tm{str(tm_seq_no).zfill(6)}"

        # Skip if already correctly named
        if page_id.lower() == next_page_id:
            tm_seq_no += 1
            continue

        # Update page_id rename list
        if batch_id not in files_to_rename:
            files_to_rename[batch_id] = {}

        old_name = f"{page_id}.tif".lower()
        new_name = f"{next_page_id}.tif"

        files_to_rename[batch_id][old_name] = new_name

        # Update page ids
        page["id"] = next_page_id.upper()
        page["IMAGEFILE"] = new_name
        page["layout"] = f"{next_page_id.upper()}_layout.xml"
        page["DATAFILE"] = f"{next_page_id}.xml"

        # Update children if they exist
        if len(page.get("children")):
            update_page_id_for_children(page["children"], next_page_id.upper())

        tm_seq_no += 1

    return tm_seq_no


def _create_merged_batch_folder(batch_qs, merged_batch_id, files_to_rename):
    """Create merged batch files by copying and renaming from source batches."""
    file_types = ["tif", "pdf"]
    destination_folder = os.path.join(
        BATCH_INPUT_PATH, batch_qs.first().sub_path, merged_batch_id
    )

    # Remove destination folder if it exists
    if os.path.exists(destination_folder):
        shutil.rmtree(destination_folder)

    # Create destination folder
    os.makedirs(destination_folder, exist_ok=True)

    # Process each batch
    for batch_instance in batch_qs:
        source_folder = os.path.join(
            BATCH_INPUT_PATH, batch_instance.sub_path, batch_instance.id
        )
        if not os.path.isdir(source_folder):
            continue

        files_to_rename_dict = files_to_rename.get(batch_instance.id, {})

        # Process each file type
        for file_type in file_types:
            pattern_lower = os.path.join(source_folder, f"*.{file_type}")
            pattern_upper = os.path.join(source_folder, f"*.{file_type.upper()}")
            files = glob.glob(pattern_lower) + glob.glob(pattern_upper)

            # Move each file to the target directory
            for file_path in files:
                base_name = os.path.basename(file_path)

                if base_name.lower() in files_to_rename_dict.keys():
                    base_name = files_to_rename_dict[base_name.lower()]

                target_file_path = os.path.join(destination_folder, base_name)

                # Copy the file
                shutil.copy2(file_path, target_file_path)
                print(f"Copied: {file_path} -> {target_file_path}")

    return merged_batch_id


def update_page_id_for_children(children, next_page_id):
    for child in children:
        original_id = child.get("id")

        if original_id:
            parts = original_id.split(".")
            parts[0] = next_page_id
            new_id = ".".join(parts)
            child["id"] = new_id

        if len(child.get("children", [])):
            update_page_id_for_children(child["children"], next_page_id)
