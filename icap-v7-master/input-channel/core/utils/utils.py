import os
import json
from datetime import datetime
from django.conf import settings
from core.models import ProcessLog
from core.service.outlook import OutlookService
from core.service.sharepoint import SharePointService
from core.service.onedrive import OneDriveService
from utils.redis_utils import redis_instance, get_redis_data
from utils.logger_config import get_logger

logger = get_logger(__name__)

INPUT_FILES_PATH = settings.INPUT_FILES_PATH


def get_config_data(input_type):
    """Fetch input channel configuration data based on input channel type"""
    projects_data = redis_instance.get("projects_data")
    projects_data = json.loads(projects_data)

    config = {}
    for project in projects_data:
        project_name = project.get("name")
        settings = project.get("settings")
        input_channels = settings.get("inputChannels")
        if input_channels:
            input_data = input_channels.get(input_type)
            if input_data:
                check_enable = input_data.get("enabled")
                if check_enable:
                    config_data = input_data.get("config")
                    config[project_name] = config_data
    return config


def save_file(name, content, folder):
    """Helper function to save any file"""
    file_dir = os.path.join(INPUT_FILES_PATH, folder)
    os.makedirs(file_dir, exist_ok=True)

    base, ext = os.path.splitext(name)
    path = os.path.join(file_dir, name)

    counter = 1
    while os.path.exists(path):
        new_name = f"{base}_{counter}{ext}"
        path = os.path.join(file_dir, new_name)
        counter += 1

    with open(path, "wb") as f:
        f.write(content)
    return path


def save_eml_file(email, content):
    """Helper function to save eml file"""
    eml_dir = os.path.join(INPUT_FILES_PATH, "Email")
    os.makedirs(eml_dir, exist_ok=True)

    safe_email = email.replace("@", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(eml_dir, f"{timestamp}_{safe_email}.eml")
    with open(path, "wb") as f:
        f.write(content)
    return path


def normalized_error(ex):
    """error convert error to valid string"""
    error = str(ex)
    error_json = {}
    if isinstance(ex, RuntimeError) and ex.args:
        if isinstance(ex.args[0], dict):
            error_json = ex.args[0]
        elif isinstance(ex.args[0], str):
            try:
                error_json = json.loads(ex.args[0])
            except Exception:
                pass

    error_code = error_json.get("error", "")
    error_desc = error_json.get("error_description", "")

    if error_code == "unauthorized_client":
        if "was not found in the directory" in error_desc:
            error_message = "Invalid Tenant ID or Client ID"
        else:
            error_message = "Unauthorized client."
    elif error_code == "invalid_client":
        if "Invalid client secret" in error_desc:
            error_message = "Invalid Client Secret"
        else:
            error_message = "Invalid Client Credentials"
    elif "double check your tenant name" in error:
        error_message = "Invalid Tenant ID"
    elif "Name or service not known" in error:
        error_message = "Invalid Server"
    elif "wrong version number" in error:
        error_message = "Invalid Port"
    elif "Invalid credentials" in error:
        error_message = "Invalid Email Address or Password"
    else:
        error_message = "Something Went Wrong"

    return error_message


def update_status(request_data):
    """
    This function handle input channel post-processing work.
    Marked mail unread and moved email or files to archive then updated log status.
    """
    job_id = request_data["job_id"]
    batch_id = request_data["batch_id"]

    logger.info(f"{batch_id=}: start updating status")

    data = get_redis_data(job_id)
    redis_instance.delete(job_id)

    log_instance = ProcessLog.objects.get(id=data["log_id"])
    log_instance.batch_id = batch_id
    log_instance.save(update_fields=["batch_id"])

    try:
        if data["input_channel"] == "outlook":
            mailbox = data["mailbox"]
            msg_id = data["msg_id"]
            config = data["client"]

            client = OutlookService(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                tenant_id=config["tenant_id"]
            )
            client.mark_read(mailbox, msg_id)
            log_instance.status = "processed"
            log_instance.save(update_fields=["status"])

            client.move_to_archive(mailbox, msg_id)
            log_instance.status = "archived"
            log_instance.queue_id = ""
            log_instance.save(update_fields=["status", "queue_id"])

            logger.info(f"Email archived successfully")

        elif data["input_channel"] == "sharepoint":
            folder_path = data["folder_path"]
            site_id = data["site_id"]
            file = data["file"]
            config = data["client"]

            client = SharePointService(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                tenant_id=config["tenant_id"]
            )

            log_instance.status = "processed"
            log_instance.save(update_fields=["status"])

            archive_folder_path = f"Archive/{folder_path}"
            client.move_file(site_id=site_id, file=file, archive_folder_path=archive_folder_path)
            log_instance.status = "archived"
            log_instance.queue_id = ""
            log_instance.save(update_fields=["status", "queue_id"])

            logger.info(f"File archived to: {archive_folder_path}")

        elif data["input_channel"] == "onedrive":
            folder_path = data["folder_path"]
            user_email = data["user_email"]
            file = data["file"]
            config = data["client"]

            client = OneDriveService(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                tenant_id=config["tenant_id"]
            )

            log_instance.status = "processed"
            log_instance.save(update_fields=["status"])

            archive_folder_path = f"Archive/{folder_path}"
            client.move_file(user_email=user_email, file=file, archive_folder_path=archive_folder_path)
            log_instance.status = "archived"
            log_instance.queue_id = ""
            log_instance.save(update_fields=["status", "queue_id"])

            logger.info(f"File archived to: {archive_folder_path}")

    except Exception as ex:
        log_instance.status = "error"
        log_instance.message="Somethings Went Wrong"
        log_instance.remarks=str(ex)
        log_instance.save(update_fields=["status", "message", "remarks"])

    logger.info(f"{batch_id=}: status updated")
