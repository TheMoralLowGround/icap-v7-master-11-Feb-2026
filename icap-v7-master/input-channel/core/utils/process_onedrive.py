import json
from core.models import ProcessLog
from rabbitmq_publisher import publish
from core.utils.utils import save_file, normalized_error
from .process_sharepoint import get_encoded_url
from core.service.onedrive import OneDriveService
from utils.redis_utils import redis_instance, get_redis_data, gerenate_job_id
from utils.logger_config import get_logger

logger = get_logger(__name__)


def process_onedrive(data):
    """This function process every onedrive account"""
    try:
        job_id = data["job_id"]
        project = data["project"]

        config = get_redis_data(job_id)
        redis_instance.delete(job_id)

        transaction_folder_url = config["transaction_folder_url"]
        training_folder_url = config["training_folder_url"]
        extensions = config["extensions"]

        client = OneDriveService(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            tenant_id=config["tenant_id"]
        )
        if transaction_folder_url:
            logger.info("Processing transaction folder")
            process_folder(
                client,
                project,
                transaction_folder_url,
                extensions
            )
        if training_folder_url:
            logger.info("Processing training folder")
            process_folder(
                client,
                project,
                training_folder_url,
                extensions,
                training=True
            )

        logger.info(f"Processing completed for '{project}'")

    except Exception as ex:
        message = normalized_error(ex)
        logger.error(message)
        ProcessLog.objects.create(
            project=data["project"],
            service="OneDrive",
            status="error",
            message=message,
            remarks=str(ex)
        )


def process_folder(client, project, folder_url, extensions, training=False):
    """This function process onedrive folder and parsing files"""
    try:
        (
            file_count, 
            user_email, 
            folder_path
        ) = parse_graph_item(client, project, folder_url)

        if file_count and file_count > 0:
            files = client.list_files(user_email=user_email, folder_path=folder_path, extensions=extensions)

            logger.info(f"{len(files)} files found")

            for file in files:
                file_id = file.get("id")
                file_name = file.get("name")

                previous_log = ProcessLog.objects.filter(queue_id=file_id).first()
                if previous_log and previous_log.status != "error":
                    logger.warning(f"File already queued in processing. Queue_id: {file_id}")
                    continue

                log_instance = ProcessLog.objects.create(
                    project=project,
                    service="OneDrive",
                    mailbox=user_email,
                    file_name=file_name,
                    queue_id=file_id,
                    status="queued"
                )
                try:
                    file_content = client.download_file(user_email=user_email, file_id=file_id)
                    file_path = save_file(file_name, file_content, "OneDrive")
                    log_instance.status = "downloaded"
                    log_instance.path = file_path
                    log_instance.save(update_fields=["status", "path"])

                    job_id = gerenate_job_id()
                    data = {
                        "client": client.to_dict(),
                        "log_id": log_instance.id,
                        "folder_path": folder_path,
                        "user_email": user_email,
                        "file": file,
                        "input_channel": "onedrive"
                    }
                    redis_instance.set(job_id, json.dumps(data))

                    request_data = {
                        "job_id": job_id,
                        "file_path": file_path,
                        "input_channel": "onedrive",
                        "project": project
                    }
                    if not training:
                        publish("start_transaction_process", "to_pipeline", request_data)
                    else:
                        publish("start_training_process", "to_pipeline", request_data)

                except Exception as ex:
                    logger.error(str(ex))
                    log_instance.status = "error"
                    log_instance.message = "Somethings Went Wrong"
                    log_instance.remarks = str(ex)
                    log_instance.save(update_fields=["status", "message", "remarks"])

    except Exception as ex:
        message = normalized_error(ex)
        logger.error(message)
        ProcessLog.objects.create(
            project=project,
            service="OneDrive",
            status="error",
            message=message,
            remarks=str(ex)
        )

def parse_graph_item(client, project, folder_url):
    encoded_url = get_encoded_url(folder_url)
    folder_data = client.folder_details(encoded_url)

    if folder_data.get("error"):
        ProcessLog.objects.create(
            project=project,
            service="OneDrive",
            status="error",
            message="Invalid Folder URL",
            remarks = folder_data.get("error")
        )
        return None, None, None

    file_count = folder_data.get("folder", {}).get("childCount")
    user_email = folder_data.get("createdBy", {}).get("user", {}).get("email")

    parent_path = folder_data.get("parentReference", {}).get("path", "")

    if parent_path.startswith("/drives/") and "/root:" in parent_path:
        parent_path = parent_path.split("/root:")[-1]
    parent_path = parent_path.strip("/")

    item_name = folder_data.get("name", "")
    folder_path = f"{parent_path}/{item_name}" if parent_path else item_name

    return file_count, user_email, folder_path

