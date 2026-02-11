"""
Organization: AIDocbuilder Inc.
File: utils/utils.py
Version: 6.0

Authors:
    - Nayem - Initial implementation
    - Sunny - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This file contains different function including timeline logging, delete grabled text and others.

Dependencies:
    - os, re
    - settings from django.conf
    - cache from django.core.cache
    - now from django.utils.timezone
    - transaction from django.db
    - Timeline from dashboard.models
    - TransactionLog, BatchStatus, TrainBatch, EmailBatch from core.models

Main Features:
    - Save Status for batch.
    - Detects garbled text by checking grabled characters.
    - Handle datacap awaiting messages.
    - Set additional document type.
"""

import io
import re
import os
import uuid
import json
import shutil
import traceback
import unicodedata
import mimetypes
from bs4 import BeautifulSoup
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.cache import cache
from django.conf import settings
from django.utils.timezone import now
from django.db import transaction

from core.models import (
    BatchStatus,
    ApplicationSettings,
    EmailBatch,
    EmailParsedDocument,
    EmailToBatchLink,
    TrainBatch,
    TrainToBatchLink,
    TransactionLog,
    MasterDictionary,
)
from dashboard.models import Timeline, Project, DeveloperSettings
from dashboard.serializers import ProjectSerializer
from core.serializers import MasterDictionarySerializer

DATACAP_CALLBACK_AWAITING = os.getenv("DATACAP_CALLBACK_AWAITING", None)
SELECTED_DATASET_LIST_FILE = os.getenv("SELECTED_DATASET_LIST_FILE")
SAVE_TRANSACTION_LOG = settings.SAVE_TRANSACTION_LOG
DATASET_BATCH_INPUT_PATH = settings.DATASET_BATCH_INPUT_PATH


def get_developer_settings(setting):
    """Get developer settings from the database"""
    developer_settings = DeveloperSettings.objects.first()
    if not developer_settings:
        return False
    for i in developer_settings.data["backend_settings"]:
        if i["name"].lower() == setting.lower():
            return i["value"]
    return False


def write_timeline_log(**kwargs):
    """Save Status for batch"""
    Timeline.objects.create(**kwargs)
    status = kwargs["status"]
    timeline_id = kwargs["timeline_id"]

    # Save latest status in memory and only process new status if its diffrent
    if cache.get(timeline_id, "") != status:
        cache.set(timeline_id, status, 60 * 5)
    return
    # Publish status to websocket channel
    # data = {"timeline_id": timeline_id, "status": status}
    # group = f"timeline_void_{convert_group_name(data['timeline_id'])}"
    # send_to_group(group, "timeline", data)


# List of common garbled characters that should trigger a warning
garbled_characters_list = [
    "�",
    "Ã",
    "Â",
    "¼",
    "½",
    "¾",
    "Ã©",
    "Ã",
    "Å",
    "Ô",
    "ä",
    "ü",
    "é",
    "â",
    "ê",
    "ë",
    "ï",
    "ì",
    "ò",
    "ó",
    "ö",
    "©",
    "®",
    "°",
    "±",
    "²",
    "³",
    "µ",
    "¥",
    "£",
    "€",
    "¢",
    "¤",
    "§",
    "¨",
    "¬",
    "Ð",
    "Ÿ",
    "Ñ",
    "æ",
    "ø",
    "å",
    "â€œ",
    "â€™",
    "â€¦",
    "â€“",
    "â€”",
    "ß",
    "í",
    "æµ",
    "ã",
    "ÐŸ",
    "Ñ€",
    "¡",
    "¿",
]


unsupported_characters = [
    "\xa0",
    "\x00",
    "\x01",
    "\x02",
    "\x03",
    "\x04",
    "\x05",
    "\x06",
    "\x07",
    "\x08",
    "\x09",
    "\x0a",
    "\x0b",
    "\x0c",
    "\x0d",
    "\x0e",
    "\x0f",
    "\x10",
    "\x11",
    "\x12",
    "\x13",
    "\x14",
    "\x15",
    "\x16",
    "\x17",
    "\x18",
    "\x19",
    "\x1a",
    "\x1b",
    "\x1c",
    "\x1d",
    "\x1e",
    "\x1f",
    "\u200b",
    "\ufeff",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "&",
    "|",
    "<",
    ">",
]
pattern = "[" + re.escape("".join(unsupported_characters)) + "]"

excluded_characters = [
    "/",
    "\\",
    "*",
    ":",
    "?",
]
excluded_characters_pattern = "[" + re.escape("".join(excluded_characters)) + "]"


def detect_garbled_text(text):
    """
    Detects garbled text by checking against a predefined list of common garbled characters
    and by detecting unusual '?' characters which may indicate decoding failures.

    Args:
        text (str): Input text to be analyzed for garbled content.

    Returns:
        combined_warnings (str): List of garbled parts if found, otherwise an empty list.

    Process Details:
        - Construct regular expression pattern to match predefined garbled characters.
        - Identify all occurrence of garbled characters in the input text.
        - Process detected characters to determine if they are printable or not.
        - Handle detection for the substring '???' in the text.
        - Combine all warnings into a single string.
        - Truncate the combined warning string if its length exceeds 10 characters.

    Notes:
        - The truncation append '......' to indicate omitted content.
    """
    # This statement constructs a regex pattern to detect the presence of any character from garbled_characters_list in a string.
    garbled_pattern = re.compile(
        f"[{''.join(re.escape(c) for c in garbled_characters_list)}]"
    )
    garbled_matches = garbled_pattern.findall(text)
    garbled_warnings = []

    if garbled_matches:
        garbled_str = "".join(garbled_matches)
        if garbled_str.isprintable():
            garbled_warnings.append(f"{garbled_str}")
        else:
            garbled_warnings.append("<Its not printable text>")

    if "???" in text:
        garbled_warnings.append(" '?' ")

    # Join the warnings into a single string
    combined_warnings = "".join(garbled_warnings)

    # If the length of combined_warnings is greater than 10, truncate and append '......'
    if len(combined_warnings) > 10:
        combined_warnings = combined_warnings[:10] + "......"

    return combined_warnings


def lowercase_extension(filename):
    """
    Takes a filename and returns it with the extension in lowercase.

    Args:
        filename (str): The filename to process

    Returns:
        str: Filename with lowercase extension
    """
    if "." not in filename:
        return filename

    name, extension = filename.rsplit(".", 1)
    return f"{name}.{extension.lower()}"


def remove_null_characters(input_text, replacer="-"):
    """replaces null character with - by default or replaces it with the given replacer"""
    text = re.sub(excluded_characters_pattern, "", input_text)
    return re.sub(pattern, replacer, text)


def replace_special_dot(input_text):
    """replaces dot like characters with actual dot"""
    return re.sub(r"[・｡。︒]", ".", input_text)


def normalize_unicode(text):
    """Normalize unicode characters"""
    normalize_text = unicodedata.normalize("NFKC", text)
    return normalize_text


def remove_extension_spacing(filename):
    """Remove unwanted space from file extension"""
    base, ext = os.path.splitext(filename)
    if not ext:
        return filename
    cleaned_ext = ext.strip().replace(" ", "")
    new_filename = base + cleaned_ext

    return new_filename


def clean_definition_settings(data):
    """This removes any null character from docType field and returns a cleaned up list."""

    doc_types_list = data["options"]["options-meta-root-type"]["items"]
    # loops through docTypes checking for null characters
    for item in doc_types_list:
        item["docType"] = remove_null_characters(
            input_text=item["docType"], replacer=""
        )
    data["options"]["options-meta-root-type"]["items"] = doc_types_list
    return data


@transaction.atomic
def save_analyzer_log_time(batch_id, field_name):
    """
    Saves the current time to a given field in the TransactionLog model.
    If the field is a list (JSONField), it appends the current time as a string in the format 'YYYY-MM-DD HH:MM:SS'.
    If it's a single occurrence field (DateTimeField), it overwrites the value.

    Args:
        batch_id (str):  Batch ID of the EmailBatch to find or create the related TransactionLog.
        field_name (str): The name of the field to update.

    Returns:
        analyzer_log: Updated TransactionLog instance.

    Process Details:
        - Check if 'SAVE_TRANSACTION_LOG' is enabled.
        - Fetche the existing 'TransactionLog' object for the given 'batch_id'.
        - If no TransactionLog record exists, a new one is created.
        - Validate the specified 'field_name' exists in the 'TransactionLog' model.
        - Update the field with the current time.
        - Save the updated 'TransactionLog' object to the database.

    Notes:
        - Raise 'AttributeError' if the 'field_name' does not exist in the model.
        - Use 'now()' to get the current time.
    """
    if SAVE_TRANSACTION_LOG:  # Ensure this is either True or False
        # Fetch or create the corresponding TransactionLog for the email_batch
        try:
            # Try to get the object with a SELECT FOR UPDATE lock
            analyzer_log = TransactionLog.objects.select_for_update().get(
                email_batch=batch_id
            )
            created = False  # Object already exists
        except TransactionLog.DoesNotExist:
            # If it doesn't exist, create it
            analyzer_log = TransactionLog.objects.create(email_batch=batch_id)
            created = True  # Object was created

        # Check if the field exists in the model
        if hasattr(analyzer_log, field_name):
            field_value = getattr(analyzer_log, field_name)

            # Get the current time formatted as 'YYYY-MM-DD HH:MM:SS'
            current_time = now().strftime("%Y-%m-%d %H:%M:%S")

            # If the field is a list (JSONField), append the formatted current time
            if isinstance(field_value, list):
                field_value.append(current_time)
                setattr(analyzer_log, field_name, field_value)
            else:
                # If it's a DateTimeField, overwrite the value with the current time (datetime format)
                setattr(analyzer_log, field_name, now())

            # Save the changes to the database
            analyzer_log.save()
            return analyzer_log
        else:
            raise AttributeError(
                f"Field '{field_name}' does not exist on TransactionLog model."
            )
    else:
        pass


def batch_awaiting_datacap(ids: list, training=False):
    """
    Handle datacap awaiting message for transaction batch timeline.

    Args:
        ids (list): List of batch IDs to be checked.
        training (bool): Flag the batches are for training purposes.

    Returns:
        data (list): Contain message and corresponding batch IDs.

    Process Details:
        - Check if the Datacap API callback feature is disabled.
        - Iterate through the given batch IDs to identify batches awaiting Datacap API callback and need recreation.
        - Use batch statuses and messages to determine the state of each batch.

    Notes:
        - Organize results into a structured format.
        - Handle for both training and email batches.
    """
    if DATACAP_CALLBACK_AWAITING == "0":
        return

    pending_batches = []
    recreate_batches = []

    PENDING_MSG = "Awaiting Datacap API Callback to Initiate Classification Process"
    ASSEMBLY_MSG = "Classification process completed. Awaiting assembly process."
    RECREATE_MSG = "Datacap Batch Recreated"

    for email_batch_id in ids:
        recent_statuses = BatchStatus.objects.filter(batch_id=email_batch_id).order_by(
            "-event_time"
        )[:5]

        last_status = recent_statuses.first()
        if not last_status:
            continue

        if last_status.message == PENDING_MSG:
            pending_batches.append(email_batch_id)
        else:
            try:
                if training:
                    batch_instance = TrainBatch.objects.get(id=email_batch_id)
                else:
                    batch_instance = EmailBatch.objects.get(id=email_batch_id)
                if (
                    batch_instance.status == "inprogress"
                    and last_status.message == ASSEMBLY_MSG
                    and any(
                        status.message == RECREATE_MSG for status in recent_statuses
                    )
                ):
                    recreate_batches.append(email_batch_id)
            except EmailBatch.DoesNotExist:
                continue

    data = []
    if pending_batches:
        data.append({"message": "Pending Datacap API Callback", "ids": pending_batches})
    if recreate_batches:
        data.append(
            {"message": "Awaiting Datacap Batch Recreation", "ids": recreate_batches}
        )

    return data


def get_merged_definition_settings(project_name):
    """
    Retrieve and update definition settings for a given project.

    Args:
        project_name (str): Name of the project that need to be retrieved.

    Returns:
        definition_settings (dict): Contain project specific definition settings.

    Process Details:
        - Retrieve application settings if available.
        - Query in database to find a project with the specified name.
        - Serialize the project data to extract its definition settings.
        - Extract and separate the 'options' from the project definition settings.
        - Merge application settings with project settings.
        - Handle the merging of 'options' separately to ensure proper integration.

    Notes:
        - Use try-except to handle where 'options' might not exist in the initial settings.
    """
    definition_settings = {}

    if ApplicationSettings.objects.exists():
        definition_settings = ApplicationSettings.objects.first().data

    qs = Project.objects.filter(name=project_name)

    if qs.exists():
        project = qs.first()
        serialize_data = ProjectSerializer(project).data

        project_definition_settings = serialize_data["settings"]

        project_definition_settings_options = project_definition_settings.pop("options")

        definition_settings.update(project_definition_settings)

        try:
            definition_settings["options"].update(project_definition_settings_options)
        except:
            definition_settings["options"] = project_definition_settings_options

    return definition_settings


def get_project_settings():
    """Get other settings data from Application Settings"""
    project_settings = {}
    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data

        project_settings = application_settings["projectSettings"]

    return project_settings

def get_other_settings():
    """Get other settings data from Application Settings"""
    other_settings = {}
    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data

        other_settings = application_settings["otherSettings"]

    return other_settings


def get_additional_doc_type(project):
    """Additional document type based on project from Application Settings"""
    document_type = None

    if is_imd_enabled_for_project(project):
        document_type = "Internal Miscellaneous Document"

        if project == "USACustoms":
            document_type = "Miscellaneous - Excluded"
    return document_type


def is_imd_enabled_for_project(project):
    """check Internal Miscellaneous Document enable or not"""
    project_settings = get_project_settings()
    projects_support_additional_doc = project_settings.get("projects_support_additional_doc")

    if project in projects_support_additional_doc:
        return True

    return False


def link_additional_batch(matched_profile, parent_batch, is_training=False):
    project_settings = get_project_settings()
    projects_support_additional_doc = project_settings.get("projects_support_additional_doc")

    if matched_profile.project in projects_support_additional_doc:
        return

    batch_id = f"AD{parent_batch.id}"

    instanceToBatchLink = EmailToBatchLink
    parent_batch_kwarg = {"email": parent_batch}

    if is_training:
        instanceToBatchLink = TrainToBatchLink
        parent_batch_kwarg = {"train_batch": parent_batch}

    if not instanceToBatchLink.objects.filter(batch_id=batch_id).exists():
        instanceToBatchLink.objects.create(
            **parent_batch_kwarg,
            batch_id=batch_id,
            uploaded=True,
            classified=True,
            mode="supporting",
        )


def create_additional_doc(
    parent_batch, matched_profile, item, processing_mime_types, is_training=False
):
    extension = item["file_name"].split(".")[-1].upper()
    if extension not in processing_mime_types:
        item["supporting_file"] = True
        pd_instance = item["parsed_doc_instance"]
        pd_instance.ra_json_created = True
        pd_instance.save()

        if is_training:
            return

        EmailParsedDocument.objects.create(
            email=parent_batch,
            name=item["file_name"],
            path=item["file_path"],
            type=item["type"],
            batch_id=f"AD{parent_batch.id}",
            ra_json_created=True,
        )

        link_additional_batch(matched_profile, parent_batch, is_training)


def escape_xml_chars(inuput):
    """
    Specific characters replace
    """
    result = inuput.replace("&", "&amp;")
    result = result.replace("<", "&lt;")
    result = result.replace(">", "&gt;")
    result = result.replace("'", "&apos;")
    result = result.replace('"', "&quot;")

    return result


def get_default_barcode(attachment_documents):
    """Set 'N' as default Barcode if no barcode option found"""
    default_barcode = "N"
    default_barcode_dict = {}

    for attachment_doc in attachment_documents:
        barcode = attachment_doc.barcode

        try:
            default_barcode_dict[barcode] += 1
        except:
            default_barcode_dict[barcode] = 1

    if len(default_barcode_dict.keys()):
        sorted_barcode_dict = dict(
            sorted(default_barcode_dict.items(), key=lambda item: item[1], reverse=True)
        )

        default_barcode = list(sorted_barcode_dict.keys())[0]

    default_barcode = "Y" if default_barcode else "N"

    print(f"{default_barcode=}")

    return default_barcode


def get_default_page_rotate(attachment_documents):
    """Set 'N' as default Page Rotate if no page rotate option found"""
    default_page_rotate = "N"
    page_rotate_dict = {}

    for attachment_doc in attachment_documents:
        page_rotate = attachment_doc.page_rotate

        try:
            page_rotate_dict[page_rotate] += 1
        except:
            page_rotate_dict[page_rotate] = 1

    if len(page_rotate_dict.keys()):
        sorted_page_rotate_dict = dict(
            sorted(page_rotate_dict.items(), key=lambda item: item[1], reverse=True)
        )

        default_page_rotate = list(sorted_page_rotate_dict.keys())[0]

    default_page_rotate = "Y" if default_page_rotate else "N"

    print(f"{default_page_rotate=}")

    return default_page_rotate


def get_default_language(attachment_documents):
    """Set 'English' as default Language if no language option found"""
    default_language = "English"
    language_dict = {}

    for attachment_doc in attachment_documents:
        language = attachment_doc.language

        try:
            language_dict[language] += 1
        except:
            language_dict[language] = 1

    if len(language_dict.keys()):
        sorted_language_dict = dict(
            sorted(language_dict.items(), key=lambda item: item[1], reverse=True)
        )

        default_language = list(sorted_language_dict.keys())[0]

    print(f"{default_language=}")

    return default_language


def get_default_ocr(attachment_documents):
    """Set 'S' as default OCR engine if no ocr engine option found"""
    default_ocr = "S"
    ocr_engine_dict = {}

    for attachment_doc in attachment_documents:
        ocr_engine = attachment_doc.ocr_engine

        try:
            ocr_engine_dict[ocr_engine] += 1
        except:
            ocr_engine_dict[ocr_engine] = 1

    if len(ocr_engine_dict.keys()):
        sorted_ocr_engine_dict = dict(
            sorted(ocr_engine_dict.items(), key=lambda item: item[1], reverse=True)
        )

        default_ocr = list(sorted_ocr_engine_dict.keys())[0]

    print(f"{default_ocr=}")

    return default_ocr


def generate_datacap_page_file(
    profile_instance=None,
    doc_instance=None,
    batch_type="Process",
    file_paths=None,
    selected_doc_types=None,
    default_ocr="S",
    default_language="English",
    default_page_rotate="N",
    default_barcode="N",
):
    """
    Return a string of batch arrtibutes in XML format
    """

    server_ip = os.getenv("SERVER_IP", None)

    # Default profile values
    profile_name = None
    customer = None
    project_name = None

    # Default document values
    document_type = None
    ocr = default_ocr
    language = default_language
    page_rotate = default_page_rotate
    barcode = default_barcode

    name_matching_text = ""

    if profile_instance:
        profile_name = escape_xml_chars(profile_instance.name)
        # customer = escape_xml_chars(profile_instance.customer_name)
        project_name = profile_instance.project

    if doc_instance:
        document_type = doc_instance.doc_type
        name_matching_text = (
            doc_instance.name_matching_text if doc_instance.name_matching_text else ""
        )
        language = doc_instance.language
        ocr = doc_instance.ocr_engine
        page_rotate = "Y" if doc_instance.page_rotate else "N"
        barcode = "Y" if doc_instance.barcode else "N"

    page_file = (
        '<B id="">'
        '<V n="STATUS">0</V>'
        f'<V n="aidbServerIP">{server_ip}</V>'
        f'<V n="bvFilePath">{file_paths}</V>'
        f'<V n="bvSelectedDocTypes">{selected_doc_types}</V>'
        f'<V n="bvBatchType">{batch_type}</V>'
        f'<V n="bvICapProfile">{profile_name}</V>'
        f'<V n="bvCustomer">{customer}</V>'
        f'<V n="bvDocumentType">{document_type}</V>'
        f'<V n="bvNameMatchingText">{name_matching_text}</V>'
        f'<V n="bvLanguage">{language}</V>'
        f'<V n="bvOCR">{ocr}</V>'
        f'<V n="bvPageRotate">{page_rotate}</V>'
        f'<V n="bvBarcodeRead">{barcode}</V>'
        f'<V n="bvProjectName">{project_name}</V>'
        "</B>"
    )
    return page_file


def create_inmemory_file(file_path):
    """
    Create InMemoryUploadedFile from a file path.
    
    Args:
        file_path (str): Absolute path to the file to load into memory.
    
    Returns:
        InMemoryUploadedFile: File object ready for upload.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is empty (0 bytes).
        IOError: If there's an error reading the file.
    """
    # Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    file_name = os.path.basename(file_path)
    
    try:
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"File is empty (0 bytes): {file_name}")
        
        # Read file into memory
        stream = io.BytesIO()
        with open(file_path, "rb") as f:
            content = f.read()
        
        stream.write(content)
        actual_size = stream.tell()
        
        # Verify size matches
        if actual_size != file_size:
            raise IOError(
                f"File size mismatch for {file_name}: "
                f"expected {file_size} bytes, read {actual_size} bytes"
            )
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"
        
        stream.seek(0)
        
        inmemory_file = InMemoryUploadedFile(
            file=stream,
            field_name=None,
            name=file_name,
            content_type=content_type,
            size=actual_size,
            charset=None
        )
        
        # Post-creation validation: verify the InMemoryUploadedFile has correct size
        # This catches potential memory allocation or stream issues
        inmemory_file.seek(0, 2)  # Seek to end
        final_size = inmemory_file.tell()
        inmemory_file.seek(0)  # Reset to beginning
        
        if final_size != actual_size:
            print(
                f"InMemoryUploadedFile size mismatch for {file_name}: "
                f"expected {actual_size} bytes, but file object has {final_size} bytes. "
                f"This indicates a memory or stream issue."
            )
            raise IOError(
                f"InMemoryUploadedFile corrupted for {file_name}: "
                f"expected {actual_size}, got {final_size}"
            )
        
        if final_size == 0:
            print(
                f"InMemoryUploadedFile created with 0 bytes for {file_name}. "
                f"This should not happen as we validated file_size={file_size} earlier."
            )
            raise IOError(f"InMemoryUploadedFile is 0 bytes for {file_name}")
        
        print(f"Created InMemoryUploadedFile for {file_name}: {final_size} bytes")
        return inmemory_file
        
    except (FileNotFoundError, ValueError):
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        print(f"Error creating InMemoryUploadedFile for {file_name}: {e}")
        print(traceback.format_exc())
        raise IOError(f"Failed to read file {file_name}: {str(e)}") from e


def extend_list_to_index(arr, index, value=None):
    # Expand the array if the index is out of bounds
    while len(arr) <= index:
        arr.append(value)

    return arr


def convert_jap_eng(html_content):
    """Replace Japanese characters to English from given HTML content"""
    for font_tag in html_content.find_all("font"):
        font_tag.unwrap()

    for p_tag in html_content.find_all("p"):
        cleaned_content = "".join(str(c).replace("\n", "") for c in p_tag.contents)
        p_tag.clear()
        p_tag.append(BeautifulSoup(cleaned_content, "html.parser"))

    master_dictionaries_qs = MasterDictionary.objects.all()
    master_dictionaries = MasterDictionarySerializer(
        master_dictionaries_qs, many=True
    ).data
    master_dictionaries = {item["name"]: dict(item) for item in master_dictionaries}
    jap_eng_dictionary = master_dictionaries.get("jap_eng_dictionary", {}).get("data")
    if not jap_eng_dictionary:
        raise ValueError("jap_eng_dictionary could not be found in Master Dictionary.")

    word_dictionary = {item["key"]: item["value"] for item in jap_eng_dictionary}

    for key, value in word_dictionary.items():
        tags = html_content.find_all(string=lambda text: text and key in text)
        for tag in tags:
            tag.replace_with(tag.replace(key, value))

    return html_content


def generate_copy_batches_xml(
    profile_instance=None,
    doc_instance=None,
    batch_id=None,
    batch_type="Process",
    file_paths=None,
    output_folder=None,
    default_ocr="S",
    default_language="English",
    default_page_rotate="N",
    default_barcode="N",
):
    """
    Return a string of batch arrtibutes in XML format
    """

    server_ip = os.getenv("SERVER_IP", None)

    # Default profile values
    profile_name = None
    customer = None
    project_name = None

    # Default document values
    document_type = None
    ocr = default_ocr
    language = default_language
    page_rotate = default_page_rotate
    barcode = default_barcode

    if profile_instance:
        profile_name = escape_xml_chars(profile_instance.name)
        project_name = profile_instance.project

    if doc_instance:
        document_type = doc_instance.doc_type
        language = doc_instance.language
        ocr = doc_instance.ocr_engine
        page_rotate = "Y" if doc_instance.page_rotate else "N"
        barcode = "Y" if doc_instance.barcode else "N"

    renamed_files, tm_no = rename_batch_files(file_paths, output_folder)

    document_nodes = ""
    for index, file_path in enumerate(renamed_files.keys(), 1):

        document_id = f"{batch_id}.{index:02d}"
        file_name, original_file_path = renamed_files[file_path]

        file_base_name, extension = os.path.splitext(file_name)

        node = (
            f'<D id="{document_id}">'
            f'<P id="{file_base_name.upper()}">'
            f'<V n="TYPE">GenericDoc</V>'
            f'<V n="STATUS">1</V>'
            f'<V n="IMAGEFILE">{file_name}</V>'
            f'<V n="root">C:\</V>'
            f'<V n="path">{output_folder}</V>'
            f'<V n="sourceFileName">{file_base_name.upper()}</V>'
            f'<V n="ext">{extension}</V>'
            f'<V n="processingSettings" />'
            f'<V n="s_lg">0</V>'
            f'<V n="y_lg">English</V>'
            f'<V n="s_srbatchdir">{output_folder}</V>'
            f'<V n="RecogStatus">10</V>'
            f'<V n="layout">{file_base_name.upper()}_layout.xml</V>'
            f'<V n="NewSourceDoc">True</V>'
            f"</P>"
            f'<V n="TYPE">GenericDocument</V>'
            f'<V n="STATUS">0</V>'
            f'<V n="ext">{extension}</V>'
            f"</D>"
        )
        document_nodes += node

    copy_batches_xml_content = (
        f'<B id="{batch_id}">'
        f'<V n="STATUS">0</V>'
        f'<V n="aidbServerIP">{server_ip}</V>'
        f'<V n="bvBatchType">{batch_type}</V>'
        f'<V n="bvICapProfile">{profile_name}</V>'
        f'<V n="bvCustomer">{customer}</V>'
        f'<V n="bvDocumentType">{document_type}</V>'
        f'<V n="bvLanguage">{language}</V>'
        f'<V n="bvOCR">{ocr}</V>'
        f'<V n="bvPageRotate">{page_rotate}</V>'
        f'<V n="bvBarcodeRead">{barcode}</V>'
        f'<V n="bvProjectName">{project_name}</V>'
        f'<V n="TYPE">{project_name}</V>'
        f"{document_nodes}"
        f"</B>"
    )

    return copy_batches_xml_content


def rename_batch_files(file_paths, output_folder):
    """files with sequential tm numbers and copy to output folder"""
    renamed_files = {}
    tm_no = 1

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"WARNING: File not found: {file_path}")
            continue

        extension = os.path.splitext(file_path)[1]
        new_file_name = f"tm{str(tm_no).zfill(6)}{extension}"
        new_file_path = os.path.join(output_folder, new_file_name)
        shutil.copy(file_path, new_file_path)
        renamed_files[new_file_path] = (new_file_name, file_path)
        tm_no += 1

    return renamed_files, tm_no


def is_camel_case(text: str) -> bool:
    """
    Returns True if the string is in camelCase format.
    """
    return bool(re.fullmatch(r"[a-z]+(?:[A-Z][a-z0-9]*)*", text))


def to_camel_case(text, key_value=None):
    """Convert text to lower camel case, preserving special characters"""

    if key_value:
        return key_value
    
    try:
        def replace_word(match):
            word = match.group(0)
            if match.start() == 0:
                return word.lower()
            else:
                return word.capitalize()

        result = re.sub(r"\b\w+\b", replace_word, text)
        return re.sub(r"\s+", "", result)
    except Exception as e:
        print(f"Error in to_camel_case: {e}")
        return text


def convert_to_title(text):
    return text.replace("_", " ").title()


def load_json_file(file_path):
    """Load JSON file if it exists, return empty dict otherwise."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def restructure_ra_json(ra_json, batch_id, process, project, vendor, document_types):
    """Extract file identifiers from ra_json"""
    pages = ra_json.get("pages", [])
    pages = [{**i, "type": "page"} for i in pages]

    restructured_ra_json = {
        "id": batch_id,
        "TYPE": "AIDBSERVICE",
        "bvOCR": "S",
        "nodes": [
            {
                "id": f"{batch_id}.01",
                "ext": ".pdf",
                "type": "document",
                "Vendor": vendor,
                "DocType": document_types,
                "Project": project,
                "Language": "English",
                "children": pages,
                "DefinitionID": process,
                "NameMatchingText": None
            }
        ],
        "STATUS": "0",
        "Vendor": vendor,
        "DocType": document_types,
        "Project": project,
        "Customer": vendor,
        "Language": "English",
        "batch_type": ".pdf",
        "bvFilePath": "",
        "bvBatchType": "Process",
        "DefinitionID": process,
        "DocumentType": document_types,
        "aidbServerIP": "None",
        "bvPageRotate": "N",
        "bvAIDBProfile": "noAIDBprofile",
        "bvBarcodeRead": "N",
        "NameMatchingText": None,
        "bvSelectedDocTypes": "None"
    }

    return restructured_ra_json


def restructure_data_json(data_json, batch_id, process, project, vendor, document_types):
    restructured_data_json = {
        "id": batch_id,
        "TYPE": "DGF",
        "bvOCR": "S",
        "nodes": [
            {
                "id": f"{batch_id}.01",
                "ext": ".pdf",
                "type": "document",
                "Vendor": vendor,
                "DocType": document_types,
                "Project": project,
                "Language": "German",
                "children": [],
                "file_path": "",
                "DefinitionID": process,
                "NameMatchingText": None
            }
        ],
        "STATUS": "0",
        "Vendor": vendor,
        "DocType": document_types,
        "Project": project,
        "Language": "English",
        "batch_type": ".pdf",
        "bvFilePath": "",
        "bvBatchType": "Process",
        "DefinitionID": process,
        "DocumentType": document_types,
        "aidbServerIP": "None",
        "bvPageRotate": "N",
        "bvBarcodeRead": "N",
        "NameMatchingText": None,
        "bvSelectedDocTypes": "None"
    }

    # Restructure key node
    reformed_key_node = {
        "id": f"{batch_id}.01.001",
        "pos": "",
        "type": "key",
        "STATUS": 0,
        "pageId": "",
        "children": []
    }

    for index, key_item in enumerate(data_json.get("key_data", [])):
        if reformed_key_node["pageId"] == "" and key_item.get("page_id", ""):
            reformed_key_node["pageId"] = key_item["page_id"]
        
        reformed_key_item = {
            "v": key_item.get("value", ""),
            "id": f"{batch_id}.01.001.00{index + 1}",
            "pos": key_item.get("key_position", ""),
            "type": "key_detail",
            "label": key_item.get("key", ""),
            "STATUS": 111,
            "export": False,
            "is_auto_extracted": True,
            "is_profile_key_found": False,
            "is_pure_autoextraction": True,
            "pageId": key_item.get("page_id", ""),
            "children": [],
            "unique_id": str(uuid.uuid4())
        }

        reformed_key_node["children"].append(reformed_key_item)
    restructured_data_json["nodes"][0]["children"].append(reformed_key_node)

    # Restructure table node
    for index, table_item in enumerate(data_json.get("table_data", [])):
        reformed_table_node = {
          "id": f"{batch_id}.01.00{index + 2}",
          "pos": "",
          "type": "table",
          "STATUS": 0,
          "pageId": "",
          "children": [],
          "table_id": 0,
          "table_name": table_item.get("table_name", ""),
          "table_unique_id": str(uuid.uuid4()),
        }

        for row_index, row in enumerate(table_item.get("table_data", {}).get("rows", [])):
            reformed_row = {
                "id": f"{batch_id}.01.00{index + 2}.00{row_index + 1}",
                "pos": "",
                "type": "row",
                "STATUS": 0,
                "pageId": "",
                "children": [],
            }

            for cell_index, cell in enumerate(row.get("row_data", [])):
                reformed_cell = {
                    "id": f"{batch_id}.01.00{index + 2}.00{row_index + 1}.00{cell_index + 1}",
                    "label": cell.get("label", ""),
                    "v": cell.get("value", ""),
                    "pos": cell.get("page_id", ""),
                    "type": "cell",
                    "STATUS": 0,
                    "pageId": cell.get("page_id", ""),
                }
                reformed_row["children"].append(reformed_cell)
            reformed_table_node["children"].append(reformed_row)
        restructured_data_json["nodes"][0]["children"].append(reformed_table_node)

    return restructured_data_json


def get_selected_dataset_batches_info():
    selected_dataset_batches = []
    selected_dataset_batches_path = (
        f"{DATASET_BATCH_INPUT_PATH}/selected-batches/{SELECTED_DATASET_LIST_FILE}.json"
    )

    if not os.path.exists(selected_dataset_batches_path):
        os.makedirs(os.path.dirname(selected_dataset_batches_path), exist_ok=True)
        with open(selected_dataset_batches_path, "w") as file:
            json.dump([], file)

    with open(selected_dataset_batches_path, "r") as file:
        selected_dataset_batches = json.load(file)
    
    return selected_dataset_batches, selected_dataset_batches_path


def is_dense_page_check_enabled(project):
    try:
        project_obj = Project.objects.get(name=project)
        other_settings = project_obj.settings.get("otherSettings", {})
        preprocess_settings = other_settings.get("preprocess_settings", {})
        ignore_dense_page = preprocess_settings.get("ignore_dense_page", False)
  
        return ignore_dense_page
    except Project.DoesNotExist:
        return False


def get_active_agents_by_project(project):
    other_settings = get_project_settings()
    active_agents_by_project = other_settings.get("active_agents_by_project", {})

    active_agents = active_agents_by_project.get(project, [])

    return active_agents
    
def _normalize_text(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value.lower()
    return value


def find_duplicate_pairs(items, key, value, type_key=None):
    seen = {}
    duplicates = []
    for index, item in enumerate(items):
        item_key = _normalize_text(item.get(key))
        item_value = _normalize_text(item.get(value))
        item_type_key = _normalize_text(item.get(type_key)) if type_key else None
        pair = (item_key, item_value, item_type_key) if type_key else (item_key, item_value)
        if pair in seen:
            pair_payload = {
                key: item_key,
                value: item_value,
            }
            if type_key:
                pair_payload[type_key] = item_type_key
            duplicates.append(
                {
                    "duplicate_key": key,
                    "pair": pair_payload,
                    "first_index": seen[pair],
                    "duplicate_index": index,
                }
            )
        else:
            seen[pair] = index
    if duplicates:
        return duplicates
    return None


def find_duplicate_pairs_in_nested(
    items, parent_key, key, value, type_key=None, parent_label_key="name"
):
    duplicate_pairs = []
    seen = {}
    for item_index, item in enumerate(items):
        parent_label = (
            _normalize_text(item.get(parent_label_key)) if parent_label_key else None
        )
        nested_items = item.get(parent_key, []) or []
        for nested_index, key_item in enumerate(nested_items):
            item_key = _normalize_text(key_item.get(key))
            item_value = _normalize_text(key_item.get(value))
            item_type_key = _normalize_text(key_item.get(type_key)) if type_key else None
            pair = (parent_label, item_key, item_value, item_type_key) if type_key else (
                parent_label,
                item_key,
                item_value,
            )
            if pair in seen:
                pair_payload = {
                    "parent": parent_label,
                    "key": item_key,
                    "value": item_value,
                }
                if type_key:
                    pair_payload[type_key] = item_type_key
                duplicate_pairs.append(
                    {
                        "duplicate_key": key,
                        "pair": pair_payload,
                    }
                )
            else:
                seen[pair] = {
                    "item_index": item_index,
                    "nested_index": nested_index,
                    "parent": parent_label,
                }
    if duplicate_pairs:
        return duplicate_pairs
    return None


def find_duplicates(items, label):
    seen = set()
    duplicates = set()

    for item in items:
        value = _normalize_text(item.get(label))
        if value is None:
            continue
        if value in seen:
            duplicates.add(value)
        else:
            seen.add(value)

    return list(duplicates)


# ---------------------------------------------
# 1) Validate options-keys duplicates
# ---------------------------------------------
def validate_options_keys(value):
    options = value.get("options", {}) or {}
    items = options.get("options-keys", {}).get("items", [])
    dups = find_duplicate_pairs(items, "keyLabel", "keyValue", "type")
    if dups:
        return dups


# ---------------------------------------------
# 2) Validate meta-root-type duplicates
# ---------------------------------------------
def validate_meta_root_types(value):
    options = value.get("options", {}) or {}
    items = options.get("options-meta-root-type", {}).get("items", [])
    dups = find_duplicate_pairs(items, "docType", "docCode")
    if dups:
        return dups

# ---------------------------------------------
# 3) Validate keyQualifiers duplicates
# ---------------------------------------------
def validate_key_qualifiers(value):
    key_qualifiers = value.get("keyQualifiers", [])
    dups = find_duplicates(key_qualifiers, "name")
    if dups:
        return dups
    option_dups = find_duplicate_pairs_in_nested(
        key_qualifiers, "options", "label", "value"
    )
    if option_dups:
        return option_dups

# ---------------------------------------------
# 5) Validate compound keys
# ---------------------------------------------
def validate_compound_keys(value):
    compound_keys = value.get("compoundKeys", [])
    dups = find_duplicates(compound_keys, "name")
    if dups:
        return dups
    nested_dups = find_duplicate_pairs_in_nested(
        compound_keys, "keyItems", "keyLabel", "keyValue", "type"
    )
    if nested_dups:
        return nested_dups
