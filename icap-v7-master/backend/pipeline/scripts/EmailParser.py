"""
Organization: AIDocbuilder Inc.
File: scripts/RAJson.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Emon - Feature update
    - Nayem - Feature update
    - Sunny - Feature update
    - Seamul - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script processes '.eml' and '.msg' email files to extract metadata, attachments, and email body content.
    It can convert email content to HTML and PDF, handle garbled text, and flag unsupported file types.

Dependencies:
    - os, re, json, traceback
    - pdfkit, extract_msg
    - BeautifulSoup from bs4
    - ApplicationSettings from core.models
    - detect_garbled_text, remove_null_characters from utils.utils
    - policy from email
    - BytesParser from email.parser

Main Features:
    - Extract metadata (to, from, cc, subject) from email files.
    - Parse email body to HTML with proper formatting.
    - Save attachments while filtering unsupported file types.
    - Convert email content to PDF.
    - Replace embedded image references with local paths.
"""

import json
import os
from email import policy, errors, _header_value_parser
from email import utils as email_utils
from email._parseaddr import _parsedate_tz
from email.headerregistry import DateHeader
from email.parser import BytesParser
from email.header import decode_header
import extract_msg
from extract_msg.enums import ErrorBehavior
import pdfkit
from bs4 import BeautifulSoup
from bs4.element import Tag
from contextlib import contextmanager
import traceback
import re
import time
import sys

from pipeline.utils.excel_utils import convert_xls_to_xlsx, validate_xls_file

from utils.utils import (
    detect_garbled_text,
    lowercase_extension,
    remove_null_characters,
    replace_special_dot,
    normalize_unicode,
    remove_extension_spacing,
    convert_jap_eng,
)

from core.models import ApplicationSettings

IMG_FILE_TYPES = ["PNG", "JPEG", "JPG"]


def clean_emails(input_string):
    """
    separate email addresses from a string

    Args:
        input_string (str): Contain one or more email addresses.

    Returns:
        str: Comma separated string of unique, lowercase email addresses.

    Process Details:
        - Use regex to identify email addresses in the input string.
        - Convert all extracted email addresses to lowercase.
        - Remove duplicate email addresses.
        - Combine email addresses into a single string separated by comma.

    Notes:
        - Regex is designed to match common email address formats.
    """
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_regex, input_string)
    # Convert to lowercase and remove duplicates while maintaining order
    unique_emails = list(dict.fromkeys(email.lower() for email in emails))
    return ",".join(unique_emails)


def parse_msg_metadata(mail):
    """
    Parse metadata from msg file type

    Args:
        mail (str): File path to the .msg email file.

    Returns:
        - 'email_to' (str): Email addresses from the "To" field.
        - 'email_from' (str): Email address of the sender.
        - 'email_cc' (str): Email addresses from the "CC" field.
        - 'email_subject' (str): Subject line of the email.

    Process Details:
        - Open the .msg file using the 'extract_msg' library.
        - Extract and clean the "To" field using the 'clean_emails'.
        - Extract the sender and "CC" field email addresses using 'extract_email_from_cc'.
        - Remove null characters from the email subject.
        - Close the .msg file after processing.

    Notes:
        - Assume the 'mail' parameter is a valid path to a .msg file.
    """
    msg = extract_msg.Message(mail, errorBehavior=ErrorBehavior.OLE_DEFECT_INCORRECT)

    email_to = clean_emails(msg.to)
    email_from, email_cc = extract_email_from_cc(msg.sender, msg.cc)
    # clean once again to remove any duplicates within cc

    email_subject = remove_null_characters(msg.subject, "")

    msg.close()

    return email_to, email_from, email_cc, email_subject


def extract_email_from_cc(email_from, email_cc):
    """
    Use msg object to return email cc and email from

    Args:
        email_from (str): "From" email field.
        email_cc (str): "CC" email field.

    Returns:
        - 'email_from' (str): Primary sender email address.
        - 'email_cc' (str): Email addresses from the "CC" field and additional "From" beyond the primary.

    Process Details:
        - Clean the 'email_from' field using 'clean_emails'.
        - Split 'email_from' to handle cases.
        - Assign the first email address as the primary 'email_from'.
        - Append additional "From" addresses to the 'email_cc' field.
        - Clean the updated 'email_cc' field.

    Notes:
        - Assume the inputs are string and handle empty or null 'email_cc' values.
    """
    email_from = clean_emails(email_from)
    email_cc = email_cc if email_cc else ""
    split_email_from = email_from.split(",")
    if len(split_email_from) > 1:
        email_from = split_email_from[0]
        additional_from = ",".join(email_from[1:])
        email_cc = f"{email_cc},{additional_from}" if email_cc else additional_from
    email_cc = clean_emails(email_cc)
    return email_from, email_cc


def handle_ol_tags(soup, blank_cells=False):
    """
    This function processes <ol> tags to remove leading numbers from <li> tags.
    It also maintains the original color and border color of the table and cells without adding new border styles.

    Args:
        soup (BeautifulSoup): BeautifulSoup object.

    Returns:
        soup (BeautifulSoup): Modified BeautifulSoup object.

    Process Details:
        - For '<ol>' tags, locate and process all '<li>' elements.
        - For '<table>' tags, ensure tables maintain their original layout.
        - For table cells ('<td>' and '<th>'), retain border color and apply default styles.
        - For '<tr>' tags, remove cells that contain whitespace.

    Notes:
        - Table style are preserved while standardizing layout attribute.
        - Empty or insignificant cells in rows are removed.
    """
    number_pattern = re.compile(r"^\d+\.\s+")

    # Process <ol> tags for list items
    for ol_tag in soup.find_all("ol"):
        for li_tag in ol_tag.find_all("li"):
            text = li_tag.get_text().strip()
            if number_pattern.match(text):
                new_text = number_pattern.sub("", text)
                li_tag.string = new_text

    # Ensure the table maintains its original layout
    for table in soup.find_all("table"):
        # Preserve any existing style attributes
        existing_style = table.get("style", "")
        table["style"] = (
            f"{existing_style} border-collapse: collapse; margin-left: 0; margin-top: 0;"
        )

    # Preserve only the border color of cells without modifying the border style
    for cell in soup.find_all(["td", "th"]):
        # Retrieve any existing style and check for border color
        existing_style = cell.get("style", "")

        # Check if the cell has a specified border color
        if "border-color" not in existing_style:
            # If no border color is specified, preserve the cell's style while ensuring no extra border style is added
            cell["style"] = f"{existing_style} padding: 2px; white-space: nowrap;"
        else:
            # Preserve the border color while keeping existing styling intact
            cell["style"] = existing_style

    # Remove cells that contain only minimal padding or whitespace in each row
    if not blank_cells:
        for row in soup.find_all("tr"):
            cells = row.find_all(["td", "th"])
            for cell in cells:
                # Check if cell is empty or only contains whitespace
                if cell.get_text(strip=True) == "":
                    cell.decompose()

    return soup


def get_highest_duplicate_counter_across_folders(
    attachments_folder, base_filename, extension
):
    """
    Find the highest duplicate counter for a filename across current and sibling email_file_* folders.

    This scans all email_file_* folders to find existing files like:
    - test.pdf (counter = 0)
    - test_1.pdf (counter = 1)
    - test_2.pdf (counter = 2)

    And returns the highest counter found, so the next file can be named with counter + 1.

    Args:
        attachments_folder (str): Current attachments folder path.
        base_filename (str): Filename without extension (e.g., "test").
        extension (str): File extension with dot (e.g., ".pdf").

    Returns:
        int: Highest counter found (-1 if no matching files exist, 0 if only base file exists).
    """
    highest_counter = -1  # -1 means no matching file found

    # Pattern to match files like "test.pdf", "test_1.pdf", "test_2.pdf"
    # Captures the counter number if present
    pattern = re.compile(
        rf"^{re.escape(base_filename)}(?:_(\d+))?{re.escape(extension)}$", re.IGNORECASE
    )

    # Get parent folders
    email_file_folder = os.path.dirname(attachments_folder)  # e.g., .../email_file_0
    extraction_folder = os.path.dirname(email_file_folder)  # e.g., .../extraction
    current_email_folder_name = os.path.basename(email_file_folder)

    # Collect all folders to check (current + siblings)
    folders_to_check = [attachments_folder]

    # Check if this follows the email_file_* pattern to add sibling folders
    if re.match(r"email_file_\d+", current_email_folder_name):
        try:
            for folder_name in os.listdir(extraction_folder):
                if folder_name == current_email_folder_name:
                    continue
                if re.match(r"email_file_\d+", folder_name):
                    sibling_attachments = os.path.join(
                        extraction_folder, folder_name, "attachments"
                    )
                    if os.path.isdir(sibling_attachments):
                        folders_to_check.append(sibling_attachments)
        except (OSError, FileNotFoundError):
            pass

    # Scan all folders for matching files
    for folder in folders_to_check:
        try:
            if not os.path.isdir(folder):
                continue
            for existing_file in os.listdir(folder):
                match = pattern.match(existing_file)
                if match:
                    counter_str = match.group(1)
                    if counter_str is None:
                        # Base file without counter (e.g., "test.pdf")
                        counter = 0
                    else:
                        counter = int(counter_str)
                    highest_counter = max(highest_counter, counter)
        except (OSError, FileNotFoundError):
            continue

    return highest_counter


def get_attachment_path(attachments_folder, filename, duplicate_filename_count):
    """
    Generate path for saving an attachment and handle duplicate filename.

    Args:
        attachments_folder (str): Folder where attachments will be saved.
        filename (str): Name of the attachment file.
        duplicate_filename_count (int): Counter to track duplicate filename (legacy, may be updated).

    Returns:
       attachment_path (str): Full path to save the attachment.
       duplicate_filename_count (str): Updated duplicate filename count.

    Process Details:
        - Construct the initial attachment path using the provided folder and filename.
        - Scan current and sibling email_file_* folders for existing duplicates.
        - Find the highest existing counter and use counter + 1 for new duplicates.
        - This ensures unique filenames across all email_file_* folders in a batch.

    Notes:
        - Ensures attachments are saved with unique names across sibling folders.
        - Handles patterns: test.pdf, test_1.pdf, test_2.pdf, etc.
    """
    os.makedirs(attachments_folder, exist_ok=True)

    filename_without_extension, extension = os.path.splitext(filename)

    # Find the highest existing counter across all relevant folders
    highest_counter = get_highest_duplicate_counter_across_folders(
        attachments_folder, filename_without_extension, extension
    )

    if highest_counter == -1:
        # No existing file found, use original filename
        attachment_path = os.path.join(attachments_folder, filename)
    else:
        # Duplicate exists, use highest_counter + 1
        new_counter = highest_counter + 1
        duplicate_filename_count = max(duplicate_filename_count, new_counter)
        new_filename = f"{filename_without_extension}_{new_counter}{extension.lower()}"
        attachment_path = os.path.join(attachments_folder, new_filename)

    return attachment_path, duplicate_filename_count


def get_html_body_safe_from_msg(msg, garbled_error):
    html = None
    error_message = "Email parsing error: Failed to extract HTML body. Please try increasing the recursion limit."
    original_limit = sys.getrecursionlimit()
    limits_to_try, garbled_error = get_recursion_limit_list(garbled_error)

    try:
        for limit in limits_to_try:
            try:
                sys.setrecursionlimit(limit)
                html = msg.htmlBody
                break
            except RecursionError:
                continue
            except Exception as e:
                error_message = f"Non-recursion error during HTML extraction: {e}"
                print(error_message)
                break
    finally:
        sys.setrecursionlimit(original_limit)

    if not html:
        raise ValueError(error_message)

    return html, garbled_error


def parse_msg(mail, show_embedded_img, email_body=False, jap_eng_convert=False):
    """
    Parse email body and find out the grabled error from msg file type.

    Args:
        mail (str): Path to the .msg file to be parsed.
        show_embedded_img (bool): Flag to embedded images should be retained.
        email_body (bool): Flag to parse and return the email body.

    Returns:
        soup: HTML formatted email body with metadata if 'email_body' is True, or 'None'.
        garbled_error: List of errors related to garbled text detection.

    Process Details:
        - Load the .msg file using the 'extract_msg' library.
        - Parse the email subject and check for garbled text.
        - If 'email_body' is True extract and process the email's HTML body using BeautifulSoup.
        - Insert email metadata (From, Sent, To, Subject) at the top of the body.
        - Process '<ol>' tags to clean numbered list items using 'handle_ol_tags'.
        - Remove embedded images and '<embed>' tags if 'show_embedded_img' is False.
        - Detect garbled text in the email body.

    Notes:
        - Ensure the extracted email content is well-formatted.
        - Garbled text detection in both the subject and body.
    """
    msg = extract_msg.Message(mail, errorBehavior=ErrorBehavior.OLE_DEFECT_INCORRECT)

    garbled_error = []
    email_subject = msg.subject
    email_subject = remove_null_characters(email_subject, "")
    garbled_subject = detect_garbled_text(email_subject)
    if garbled_subject:
        garbled_error.append(
            f"Encoding Error: Detected garbled text in subject. The text contains unusual {''.join(garbled_subject)} characters (possible decoding failure) "
        )

    if email_body:
        html, garbled_error = get_html_body_safe_from_msg(msg, garbled_error)
        msg.close()
        html = "" if html is None else html
        soup = BeautifulSoup(html, "html.parser")

        try:
            header = f"""
                    <div> <b>From:</b> {msg.sender.replace("<", "&lt;").replace(">", "&gt;")}</div>
                    <div> <b>Sent:</b> {msg.date.strftime('%a, %d %b %Y %H:%M:%S +0000')}</div>
                    <div> <b>To:</b> {msg.to.replace("<", "&lt;").replace(">", "&gt;")}</div>
                    <div> <b>Subject:</b> {msg.subject}</div>
                    """
            soup.body.insert(0, BeautifulSoup(header, "html.parser"))
        except:
            pass

        soup = handle_ol_tags(soup)
        if jap_eng_convert:
            soup = convert_jap_eng(soup)

        if not show_embedded_img:
            for tag in soup.find_all(["img", "embed"]):
                tag.extract()

        head_tag = soup.head
        if not head_tag:
            head_tag = soup.new_tag("head")
            soup.insert(0, head_tag)
        meta_tag = soup.new_tag("meta", charset="UTF-8")
        soup.head.insert(0, meta_tag)

        body_text = soup.get_text()
        garbled_body = detect_garbled_text(body_text)
        if garbled_body:
            garbled_error.append(
                f"Encoding Error: Detected garbled text in body. The text contains unusual {''.join(garbled_body)} characters (possible decoding failure) "
            )

        return soup.prettify(), garbled_error

    return None, garbled_error


def get_key_ignoring_case(dictionary, desired_key):
    """Retrieves value associated with a key, ignoring case sensitivity"""
    for key in dictionary:
        if key.lower() == desired_key.lower():
            value = dictionary[key]
            if "=?iso-2022-jp?B?" in value:
                value = decoded_iso_jp_text(value)
            return value
    return None


def get_safe_email_field(msg, field_name, escape_html=True):
    value = get_key_ignoring_case(msg, field_name) or "Not Found"
    if escape_html:
        value = value.replace("<", "&lt;").replace(">", "&gt;")
    return value


def parse_eml_metadata(eml_file):
    """
    Parse metadata from eml file type

    Args:
        eml_file (str): File path to the .eml email file.

    Returns:
        - 'email_to' (str): Email addresses from the "To" field.
        - 'email_from' (str): Email address of the sender.
        - 'email_cc' (str): Email addresses from the "CC" field.
        - 'email_subject' (str): Subject line of the email.

    Process Details:
        - Open the .eml file using the 'BytesParser' library.
        - Extract and clean the "To" field using the 'clean_emails'.
        - Extract the sender and "CC" field email addresses using 'extract_email_from_cc'.
        - Remove null characters from the email subject.

    Notes:
        - Assume the 'eml_file' parameter is a valid path to a .eml file.
    """
    with open(eml_file, "rb") as file:
        msg = BytesParser(policy=policy.default).parse(file)
        email_to = get_key_ignoring_case(msg, "to")
        email_to = clean_emails(email_to)
        email_from = get_key_ignoring_case(msg, "from")
        email_cc = get_key_ignoring_case(msg, "cc")

        email_from, email_cc = extract_email_from_cc(email_from, email_cc)

        email_subject = get_key_ignoring_case(msg, "subject")

    return email_to, email_from, email_cc, email_subject


def parse_eml(eml_file, show_embedded_img, email_body=False, jap_eng_convert=False):
    """
    Parse email body and find out the grabled error from eml file type.

    Args:
        eml_file (str): Path to the .eml file to be parsed.
        show_embedded_img (bool): Flag to embedded images should be retained.
        email_body (bool): Flag to parse and return the email body.

    Returns:
        soup: HTML formatted email body with metadata if 'email_body' is True, or 'None'.
        garbled_error: List of errors related to garbled text detection.

    Process Details:
        - Load the .eml file using the 'BytesParser' library.
        - Parse the email subject and check for garbled text.
        - If 'email_body' is True extract and process the email's HTML body using BeautifulSoup.
        - Insert email metadata (From, Sent, To, Subject) at the top of the body.
        - Process '<ol>' tags to clean numbered list items using 'handle_ol_tags'.
        - Remove embedded images and '<embed>' tags if 'show_embedded_img' is False.
        - Detect garbled text in the email body.

    Notes:
        - Ensure the extracted email content is well-formatted.
        - Garbled text detection in both the subject and body.
    """
    with open(eml_file, "rb") as file:
        msg = BytesParser(policy=policy.default).parse(file)

    garbled_error = []
    email_subject = get_key_ignoring_case(msg, "subject")
    garbled_subject = detect_garbled_text(email_subject)
    if garbled_subject:
        garbled_error.append(
            f"Encoding Error: Detected garbled text in subject. The text contains unusual {''.join(garbled_subject)} characters (possible decoding failure) "
        )

    if email_body:
        html_content = ""

        for part in msg.walk():
            content_type = part.get_content_type()
            charset = part.get_content_charset()

            if content_type == "text/html":
                if charset:
                    if charset.lower() == "windows-874":
                        charset = "tis-620"
                        content = part.get_payload(decode=True)
                        if content:
                            html_content = content.decode(charset, errors="replace")
                            break
                    else:
                        html_content = part.get_content()
                        break

            elif content_type == "text/plain":
                if charset and charset.lower() in [
                    "iso-2022-jp",
                    "iso-8859-1",
                    "utf-8",
                ]:
                    content = part.get_payload(decode=True)
                    plain_text = (
                        content.decode(charset, errors="replace")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    html_content = f'<html lang="en"><head><meta charset="UTF-8"></head><body><pre>{plain_text}</pre></body></html>'

        soup = BeautifulSoup(html_content, "html.parser")

        header = f"""
            <div> <b>From:</b> {get_safe_email_field(msg, "from")}</div>
            <div> <b>Sent:</b> {get_safe_email_field(msg, "date")}</div>
            <div> <b>To:</b> {get_safe_email_field(msg, "to")}</div>
            <div> <b>Subject:</b> {get_safe_email_field(msg, "subject")}</div>
        """

        soup.body.insert(0, BeautifulSoup(header, "html.parser"))
        soup = handle_ol_tags(soup, blank_cells=True)
        if jap_eng_convert:
            soup = convert_jap_eng(soup)

        if not show_embedded_img:
            for tag in soup.find_all(["img", "embed"]):
                tag.extract()

        body_text = soup.get_text()
        garbled_body = detect_garbled_text(body_text)
        if garbled_body:
            garbled_error.append(
                f"Encoding Error: Detected garbled text in body. The text contains unusual {''.join(garbled_body)} characters (possible decoding failure) "
            )

        return soup.prettify(), garbled_error

    return None, garbled_error


# Manage attachment files and embedded images
def write_attachment_to_file(
    attachment_data,
    attachments_folder,
    filename,
    duplicate_filename_count,
    show_embedded_img,
    garbled_error,
):
    """
    Process and save email attachments and handle unsupported file types, duplicate filenames.

    Args:
        attachment_data (str): Data of the attachment to be saved.
        attachments_folder (str): Directory where attachments will be saved.
        filename (str): Name of the attachment file.
        show_embedded_img (bool): Flag to embedded image files are allowed.
        unsupported_files (list): List to filename of unsupported file types.
        garbled_error (list): List of error related to garbled text detection.

    Returns:
        duplicate_filename_count (int): Updated count of duplicate filenames.
        garbled_error (list): Updated list of errors related to garbled text detection.

    Process Details:
        - Check if the file is unsupported type, it is skipped.
        - In case of filename being too long or containing null characters added to 'garbled_error'.
        - Duplicate filename is handled by appending a counter to the filename.
        - If the attachment is an Excel file .xls converted to '.xlsx' and saved accordingly.

    Notes:
        - Handle unsupported file types.
        - Handle error related to the file-saving process.
    """
    global IMG_FILE_TYPES

    unsupported_mime_types = get_unsupported_mime_types()
    invalid_file_types = unsupported_mime_types

    if not show_embedded_img:
        invalid_file_types = unsupported_mime_types + IMG_FILE_TYPES

    filename = normalize_unicode(filename)
    filename = remove_extension_spacing(filename)

    # Split filename and extension
    extension = filename.split(".")[-1].upper()

    if extension in invalid_file_types:
        return duplicate_filename_count, garbled_error

    # Check if the file has no extension
    if "." not in filename or extension == filename.upper():
        garbled_error.append(
            f"Error: Failed to save attachment '{filename}' due to error: File is not a valid format."
        )
        return duplicate_filename_count, garbled_error

    # Handle duplicate filenames
    attachment_path, duplicate_filename_count = get_attachment_path(
        attachments_folder, filename, duplicate_filename_count
    )

    try:
        # Save attachment data to file
        if extension == "XLS":
            # Write XLS data to temporary file
            temp_xls = os.path.join(attachments_folder, f"temp_{int(time.time())}.xls")
            with open(temp_xls, "wb") as f:
                f.write(attachment_data)

            try:
                # Validate XLS first
                if not validate_xls_file(temp_xls):
                    if os.path.exists(temp_xls):  # Cleanup before returning
                        os.remove(temp_xls)
                    garbled_error.append(f"Error: {filename} is not a valid XLS file.")
                    return duplicate_filename_count, garbled_error

                xlsx_filename = filename.rsplit(".", 1)[0] + ".xlsx"
                xlsx_path, duplicate_filename_count = get_attachment_path(
                    attachments_folder, xlsx_filename, duplicate_filename_count
                )
                convert_xls_to_xlsx(temp_xls, xlsx_path)

                # Cleanup after successful execution
                if os.path.exists(temp_xls):
                    os.remove(temp_xls)
                return duplicate_filename_count, garbled_error

            except Exception as e:
                print(traceback.format_exc())
                # Cleanup in case of exception
                if os.path.exists(temp_xls):
                    os.remove(temp_xls)
                garbled_error.append(f"Error: {filename} is not a valid XLS file.")
                return duplicate_filename_count, garbled_error

        if isinstance(attachment_data, str):
            with open(attachment_path, "w") as attachment_file:
                attachment_file.write(attachment_data)
        else:
            with open(attachment_path, "wb") as attachment_file:
                attachment_file.write(attachment_data)

    except OSError as e:
        if e.errno == 36:  # Filename too long error
            garbled_error.append(
                f"Error: Filename too long for attachment '{filename}'. Please rename the file."
            )
        else:
            garbled_error.append(
                f"OS error occurred while saving the file: {e.strerror}"
            )
    except Exception as e:
        # Append a proper error message if saving fails
        garbled_error.append(
            f"Error: Failed to save attachment '{filename}' due to error: {str(e)}"
        )
        print(traceback.format_exc())

    return duplicate_filename_count, garbled_error


def get_recursion_limit_list(garbled_error):
    """Retrieve recursion limit list from application settings"""
    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data
        recursion_limit_list = application_settings["otherSettings"].get(
            "recursion_limit_list"
        )
        if not recursion_limit_list:
            garbled_error.append(
                f"recursion_limit_list could not be found in Application Settings"
            )

            recursion_limit_list = [1000, 2000, 4000, 6000, 8000, 10000]

    return recursion_limit_list, garbled_error


def get_unsupported_mime_types():
    """Retrieve unsupported MIME types from application settings"""
    if ApplicationSettings.objects.exists():
        application_settings = ApplicationSettings.objects.first().data
        unsupported_mime_types = application_settings["otherSettings"].get(
            "unsupported_mime_types"
        )
        if not unsupported_mime_types:
            raise ValueError(
                "unsupported_mime_types could not be found in Application Settings"
            )
    return unsupported_mime_types


def collect_unsupported_files(show_embedded_img, file_list, filename):
    """
    Manage unsupported files which is present in the Application Settings.

    Args:
        show_embedded_img (bool): Flag to embedded image files are allowed.
        file_list (list): List to store the names of unsupported files.
        filename (str): Name of the file to be checked.

    Process Details:
        - Retrieve unsupported MIME types using 'get_unsupported_mime_types'.
        - If 'show_embedded_img' is 'False', include both unsupported MIME types and 'IMG_FILE_TYPES'.
        - Extract the file extension from the given 'filename'.
        - If the file's extension matche any invalid file type, append the 'filename' to 'file_list'.

    Notes:
        - Ensure 'IMG_FILE_TYPES' defined to avoid logic error.
        - Assume 'file_list' is passed as a mutable object to collect result.
    """
    global IMG_FILE_TYPES

    unsupported_mime_types = get_unsupported_mime_types()

    if not show_embedded_img:
        invalid_file_types = unsupported_mime_types + IMG_FILE_TYPES
    else:
        invalid_file_types = unsupported_mime_types

    extension = filename.split(".")[-1].upper()

    if extension in invalid_file_types:
        file_list.append(filename)


def process_email_part(
    part,
    attachments_folder,
    duplicate_filename_count,
    show_embedded_img,
    unsupported_files,
    garbled_error,
):
    """
    Recursively processes email parts to extract, validate, and save attachments.

    Args:
        part (email.message.Message): Email part to be processed. Can be multipart or non-multipart.
        attachments_folder (str): Directory where attachments will be saved.
        duplicate_filename_count (int): Counter to track duplicate filename.
        show_embedded_img (bool): Flag to embedded image files are allowed.
        unsupported_files (list): List to filename of unsupported file types.
        garbled_error (list): List of error related to garbled text detection.

    Returns:
        duplicate_filename_count (int): Updated count of duplicate filenames.
        garbled_error (list): Updated list of errors related to garbled text detection.

    Process Details:
        - If the email part is multipart, it recursively process each subpart.
        - For each non-multipart part, the filename is validated and checked for null characters.
        - Unsupported file types are logged into the 'unsupported_files' list.
        - Attachments are saved to the specified folder.

    Notes:
        - If filename contain garbled text are logged in 'garbled_error'.
        - If duplicate file exists then increase 'duplicate_filename_count'.
    """
    if part.is_multipart():
        # Recursively process each subpart
        for subpart in part.iter_parts():
            duplicate_filename_count, garbled_error = process_email_part(
                subpart,
                attachments_folder,
                duplicate_filename_count,
                show_embedded_img,
                unsupported_files,
                garbled_error,
            )
    else:
        # Process single part (non-multipart)
        filename = part.get_filename()
        if filename:
            filename = remove_null_characters(filename)
            filename = lowercase_extension(filename)
            attachment_data = part.get_content()
            collect_unsupported_files(show_embedded_img, unsupported_files, filename)

            # Save the attachment to a file and handle errors
            duplicate_filename_count, garbled_error = write_attachment_to_file(
                attachment_data,
                attachments_folder,
                filename,
                duplicate_filename_count,
                show_embedded_img,
                garbled_error,
            )

            # Check for garbled text in the filename
            garbled_attachment = detect_garbled_text(filename)
            if garbled_attachment:
                garbled_error.append(
                    f"Encoding Error: Detected garbled text in attachment name. The text contains unusual {''.join(garbled_attachment)} characters (possible decoding failure)"
                )

    return duplicate_filename_count, garbled_error


def extract_message_data(msg_object):
    """Extract data from Message object using various possible attributes"""
    if hasattr(msg_object, "data"):
        return msg_object.data
    elif hasattr(msg_object, "content"):
        return msg_object.content
    elif hasattr(msg_object, "blob"):
        return msg_object.blob

    # Try raw bytes conversion as last resort
    return bytes(msg_object)


def decoded_iso_jp_text(full_text):
    """Decode an encoded part from the string"""
    pattern = r"=\?iso-2022-jp\?B\?(.*?)==\?="

    def decode_match(match):
        encoded_part = match.group(1)
        encoded_part = f"=?iso-2022-jp?B?{encoded_part}==?="
        decoded_bytes = decode_header(encoded_part)
        for decoded_part, encoding in decoded_bytes:
            decoded_part = decoded_part.decode(
                encoding if encoding else "utf-8", errors="replace"
            )
        return decoded_part

    decoded_text = re.sub(pattern, decode_match, full_text)
    return decoded_text


def save_msg_attachment(
    duplicate_filename_count, attachment_data, attachments_folder=".", filename=None
):
    """
    Save .msg email attachment data to the specified directory.

    Args:
        duplicate_filename_count (int): Counter to track duplicate filename.
        attachment_data (str): Data of the attachment to be saved.
        attachments_folder (str): Directory where attachments will be saved.
        filename (str): Name of the attachment file.

    Returns:
        duplicate_filename_count (int): Updated duplicate filename counter.

    Process Details:
        - Check the type of 'attachment_data'.
        - If the data is in bytes or bytearray format, it directly save the data.
        - If the data is an 'extract_msg.Message' object then extract the message data and save it.

    Notes:
        - If the attachment type is unsupported then logs it.
    """

    output_path, duplicate_filename_count = get_attachment_path(
        attachments_folder, filename, duplicate_filename_count
    )

    # Handle different types of attachment data
    if isinstance(attachment_data, (bytes, bytearray)):
        with open(output_path, "wb") as f:
            f.write(attachment_data)
        print(f"Saved bytes attachment: {filename}")

    elif isinstance(attachment_data, extract_msg.Message):
        try:
            msg_data = extract_message_data(attachment_data)

            with open(output_path, "wb") as f:
                f.write(msg_data)

            print(f"Saved message attachment: {filename}")
        except Exception as e:
            print(f"Failed to extract message data for {filename}: {str(e)}")

    else:
        print(f"Unsupported attachment type: {type(attachment_data)}")

    return duplicate_filename_count


def save_attachments(email_file, attachments_folder, show_embedded_img):
    """
    Process email (.msg and .eml) file, extract and save attachments to the specified folder.

    Args:
        email_file (str): Path to the email file.
        attachments_folder (str): Directory where attachments will be saved.
        show_embedded_img (bool): Flag to embedded image files are allowed.

    Returns:
        unsupported_files (list): List of unsupported files that could not be saved.
        garbled_error (list): List of errors related to garbled issue during processing.

    Process Details:
        - Check whether the email file is in '.msg' or '.eml' format.
        - If the email is in '.msg' format, it extract attachments and process them.
        - If the email is in `.eml` format, it parse the email, iterate through attachments, and process them.

    Notes:
        - For each attachment, it validate, remove unsupported characters and check for embedded image file.
        - If filename contain garbled text then it added to the 'garbled_error' list.
    """
    unsupported_files = []
    garbled_error = []  # renamed from garbled_error

    try:
        duplicate_filename_count = 0

        if email_file.lower().endswith(".msg"):
            msg = extract_msg.Message(
                email_file, errorBehavior=ErrorBehavior.OLE_DEFECT_INCORRECT
            )

            for attachment in msg.attachments:
                filename = (
                    attachment.longFilename or attachment.name
                )  # longFilename might contain the full original name

                if not filename:
                    continue

                filename = remove_null_characters(filename, "")
                filename = lowercase_extension(filename)
                # removing unsupported dot with "."
                filename = replace_special_dot(filename)

                collect_unsupported_files(
                    show_embedded_img, unsupported_files, filename
                )
                attachment_data = attachment.data

                try:
                    if filename.lower().endswith(".msg"):
                        duplicate_filename_count = save_msg_attachment(
                            duplicate_filename_count,
                            attachment_data,
                            attachments_folder,
                            filename,
                        )
                        continue

                    duplicate_filename_count, garbled_error = write_attachment_to_file(
                        attachment_data,
                        attachments_folder,
                        filename,
                        duplicate_filename_count,
                        show_embedded_img,
                        garbled_error,
                    )
                except Exception as e:
                    print(f"Error saving attachment '{filename}': {str(e)}")
                    traceback.print_exc()

                garbled_attachment = detect_garbled_text(filename)
                if garbled_attachment:
                    garbled_error.append(
                        f"Encoding Error: Detected garbled text in attachment name. The text contains unusual {''.join(garbled_attachment)} characters (possible decoding failure)"
                    )
            msg.close()
        elif email_file.lower().endswith(".eml"):
            with open(email_file, "rb") as file:
                msg = BytesParser(policy=policy.default).parse(file)

            for part in msg.iter_attachments():
                # Check if the part needs further processing
                if part.is_multipart():
                    if part.get_content_type() == "message/rfc822":
                        filename, attachment_data = get_attached_eml_subject(part)
                        if filename:
                            filename = remove_null_characters(filename)
                            filename = lowercase_extension(filename)

                            # removing unsupported dot with "."
                            filename = replace_special_dot(filename)
                            collect_unsupported_files(
                                show_embedded_img, unsupported_files, filename
                            )
                            try:
                                duplicate_filename_count, garbled_error = (
                                    write_attachment_to_file(
                                        attachment_data,
                                        attachments_folder,
                                        filename,
                                        duplicate_filename_count,
                                        show_embedded_img,
                                        garbled_error,
                                    )
                                )
                            except Exception as e:
                                print(f"Error saving attachment '{filename}': {str(e)}")
                                traceback.print_exc()
                        else:
                            print(f"Attachment filename not found.")
                    else:
                        duplicate_filename_count, garbled_error = process_email_part(
                            part,
                            attachments_folder,
                            duplicate_filename_count,
                            show_embedded_img,
                            unsupported_files,
                            garbled_error,
                        )
                else:
                    # Handle non-multipart parts directly
                    filename = part.get_filename()
                    # Check filename has JP encoded part
                    if "=?iso-2022-jp?B?" in filename:
                        filename = decoded_iso_jp_text(filename)
                    # removing unsupported dot with "."
                    filename = replace_special_dot(filename)
                    attachment_data = part.get_content()
                    collect_unsupported_files(
                        show_embedded_img, unsupported_files, filename
                    )
                    if filename:
                        filename = remove_null_characters(filename)
                        filename = lowercase_extension(filename)
                        try:
                            duplicate_filename_count, garbled_error = (
                                write_attachment_to_file(
                                    attachment_data,
                                    attachments_folder,
                                    filename,
                                    duplicate_filename_count,
                                    show_embedded_img,
                                    garbled_error,
                                )
                            )
                        except Exception as e:
                            print(f"Error saving attachment '{filename}': {str(e)}")
                            traceback.print_exc()

                        garbled_attachment = detect_garbled_text(filename)
                        if garbled_attachment:
                            garbled_error.append(
                                f"Encoding Error: Detected garbled text in attachment name. The text contains unusual {''.join(garbled_attachment)} characters (possible decoding failure)"
                            )

    except Exception as e:
        print(traceback.print_exc())

    return unsupported_files, garbled_error


def get_attached_eml_subject(part):
    """Set filename as eml subject"""
    filename = None
    attachment_data = None
    embedded_msg = part.get_payload(0)  # Get the embedded message
    if embedded_msg:
        subject = embedded_msg["subject"] if embedded_msg["subject"] else "No Subject"
        filename = f"{subject}.eml"
        attachment_data = embedded_msg.as_bytes()

    return filename, attachment_data


def parse_email_metadata(email_file_path, email_file_name):
    """
    This is the main function to parse metadata from email file.

    Args:
        email_file_path (str): File path of the email file.
        email_file_name (str): Name of the email file.

    Returns:
        meta_info (dict): Contain parsed email metadata such as email_to, email_from, email_cc and email_subject.

    Process Details:
        - Check the file extension '.eml' or '.msg'.
        - If the file is '.eml', call 'parse_eml_metadata' to extract the email metadata.
        - If the file is '.msg', call 'parse_msg_metadata' to extract the email metadata.

    Notes:
        - Assume that the email file is either '.eml' or '.msg' format.
    """
    if email_file_name.lower().endswith(".eml"):
        email_to, email_from, email_cc, email_subject = parse_eml_metadata(
            email_file_path
        )
    if email_file_name.lower().endswith(".msg"):
        email_to, email_from, email_cc, email_subject = parse_msg_metadata(
            email_file_path
        )
    meta_info = {
        "email_to": email_to,
        "email_from": email_from,
        "email_cc": email_cc,
        "email_subject": email_subject,
    }
    return meta_info


def replace_img_src(html_content, attachments_folder):
    """Update image source with attachments folder"""
    soup = BeautifulSoup(html_content, "html.parser")

    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if src.startswith("cid:"):
            image_filename = src.split(":")[1].split("@")[0]
            for attachment in os.listdir(attachments_folder):
                if attachment.lower() == image_filename.lower():
                    attachment_path = os.path.join(attachments_folder, attachment)
                    img_tag["src"] = f"{attachment_path}"
                    break

    return soup.prettify()


# Monkeypatch for recursive equality only
@contextmanager
def safe_tag_eq():
    _original_eq = Tag.__eq__

    def safe_eq(self, other):
        try:
            return _original_eq(self, other)
        except RecursionError:
            return False

    Tag.__eq__ = safe_eq
    try:
        yield
    finally:
        Tag.__eq__ = _original_eq


def parse_email(
    email_file_path,
    email_file_name,
    output_folder,
    show_embedded_img,
    email_body_exists,
    jap_eng_convert,
    zoom_value,
):
    """
    This is the main function to parse an email file to extract metadata, email body, and
    attachments, then converts the email body to HTML and PDF formats.

    Args:
        email_file_path (str): File path of the email file.
        email_file_name (str): Name of the email file.
        output_folder (str): Directory where output files will be saved.
        show_embedded_img (bool): Flag to embedded image files are allowed.
        email_body_exists (bool): Flag to parse and return the email body.

    Returns:
        - pdf_path (str): Full path to the generated PDF file.
        - attachments_folder (str): Path to the folder where attachments are saved.
        - unsupported_files (list): List of files with unsupported formats that were not saved.
        - garbled_all_error (list): List of errors related to garbled text or processing issues.

    Process Details:
        - Check the email file type '.eml' or '.msg' and process it accordingly.
        - For '.eml' files, it calls the 'parse_eml' function.
        - For '.msg' files, it calls the 'parse_msg' function.
        - It extract the email body as HTML and save it to a specified output folder.
        - It save attachments to a separate folder, handle unsupported files and detect garbled text.
        - HTML is converted to PDF using 'pdfkit' with specific options.

    Notes:
        - Errors are logged in the 'garbled_all_error' list for further inspection.
        - Embedded images are handled depending on the 'show_embedded_img' flag and the folder is cleaned up after conversion.
    """
    garbled_all_error = []
    print(show_embedded_img)
    print(type(show_embedded_img))

    # Open Email and extract Meta info
    if email_file_name.lower().endswith(".eml"):
        with safe_tag_eq():
            html_output, garbled_error = parse_eml(
                email_file_path, show_embedded_img, email_body_exists, jap_eng_convert
            )
        if garbled_error:
            garbled_all_error.extend(garbled_error)

    if email_file_name.lower().endswith(".msg"):
        with safe_tag_eq():
            html_output, garbled_error = parse_msg(
                email_file_path, show_embedded_img, email_body_exists, jap_eng_convert
            )
        if garbled_error:
            garbled_all_error.extend(garbled_error)

    email_file_name_without_extension = os.path.splitext(email_file_name)[0]
    html_filename = email_file_name_without_extension + ".html"
    html_path = os.path.join(output_folder, html_filename)

    pdf_filename = email_file_name_without_extension + ".pdf"
    pdf_path = os.path.join(output_folder, pdf_filename)

    # Convert HTML to PDF with slightly adjusted options
    options = {
        "orientation": "Landscape",
        "--page-size": "Legal",
        "enable-local-file-access": True,
        "--disable-javascript": "",  # Temporarily disable JavaScript to test
        "--no-images": "",  # Temporarily disable images to test
        "zoom": zoom_value,
    }

    # Save attachments as separate files
    attachments_folder = os.path.join(output_folder, "attachments")
    os.makedirs(attachments_folder, exist_ok=True)

    # save_attachments returns any unsupported files it is unable to save
    unsupported_files, garbled_error = save_attachments(
        email_file_path, attachments_folder, show_embedded_img
    )
    if garbled_error:
        garbled_all_error.extend(garbled_error)

    if show_embedded_img:
        html_output = replace_img_src(html_output, attachments_folder)

    # Write the HTML content to file
    if html_output:
        with open(html_path, "w") as file:
            file.write(html_output)

        pdfkit.from_file(html_path, pdf_path, options=options)

    try:
        if show_embedded_img:
            # Delete the embedded images inside the attachment folder after conversion to PDF
            for file_name in (
                f
                for f in os.listdir(attachments_folder)
                if f.endswith(tuple(IMG_FILE_TYPES))
            ):
                file_path = os.path.join(attachments_folder, file_name)
                os.remove(file_path)

    except Exception as ex:
        print(f"Error during cleanup: {str(ex)}")
        print(traceback.format_exc())

    return (pdf_path, attachments_folder, unsupported_files, garbled_all_error)


# Here we applied Monkey Patching to modify the Email library
def custom_parse(cls, value, kwds):
    """This is the modified 'parse' method of the 'DateHeader' class in the Email library."""
    if not value:
        kwds["defects"].append(errors.HeaderMissingRequiredValue())
        kwds["datetime"] = None
        kwds["decoded"] = ""
        kwds["parse_tree"] = _header_value_parser.TokenList()
        return
    if isinstance(value, str):
        kwds["decoded"] = value
        try:
            value = patched_parsedate_to_datetime(value)
        except ValueError:
            kwds["datetime"] = None
            kwds["parse_tree"] = _header_value_parser.TokenList()
            return
    kwds["datetime"] = value
    kwds["decoded"] = email_utils.format_datetime(kwds["datetime"])
    kwds["parse_tree"] = cls.value_parser(kwds["decoded"])
    print(kwds["decoded"])


DateHeader.parse = classmethod(custom_parse)


def patched_parsedate_to_datetime(data):
    """This function modify the original 'parsedate_to_datetime' function in the Email library"""
    parsedate_to_datetime = email_utils.parsedate_to_datetime
    parsed_date_tz = _parsedate_tz(data)
    if parsed_date_tz is None:
        raise ValueError(f"Invalid date value or format: {data!r}")
    return parsedate_to_datetime(data)
