import json
from core.models import ProcessLog
from rabbitmq_publisher import publish
from core.utils.utils import save_eml_file, normalized_error
from utils.redis_utils import redis_instance, get_redis_data, gerenate_job_id
from core.service.outlook import OutlookService
from utils.logger_config import get_logger

logger = get_logger(__name__)


def process_outlook(data):
    try:
        job_id = data["job_id"]
        project = data["project"]

        config = get_redis_data(job_id)
        redis_instance.delete(job_id)

        client = OutlookService(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            tenant_id=config["tenant_id"]
        )
        mailboxes = config["mailbox_ids"]

        for mailbox in mailboxes:
            logger.info(f"Process mailbox - {mailbox}")
            process_mailbox(client, project, mailbox)

        logger.info(f"Processing completed for '{project}'")

    except Exception as ex:
        message = normalized_error(ex)
        logger.error(message)
        ProcessLog.objects.create(
            project=data["project"],
            service="OAuth",
            status="error",
            message=message,
            remarks=str(ex)
        )


def process_mailbox(client, project, mailbox):
    """This function parse email from mailbox and process mailbox"""
    try:
        messages = client.get_unread_emails(mailbox)

        logger.info(f"{len(messages)} unread emails found")

        for msg in messages:
            msg_id = msg["id"]

            previous_log = ProcessLog.objects.filter(queue_id=msg_id).first()
            if previous_log and previous_log.status != "error":
                logger.warning(f"Email already queued in processing. Queue_id: {msg_id}")
                continue

            log_instance = ProcessLog.objects.create(
                project=project,
                service="OAuth",
                mailbox=mailbox,
                queue_id=msg_id,
                status="queued"
            )
            try:
                eml_content = client.fetch_email(mailbox, msg_id)
                email_path = save_eml_file(mailbox, eml_content)

                log_instance.status = "downloaded"
                log_instance.path = email_path
                log_instance.save(update_fields=["status", "path"])

                job_id = gerenate_job_id()
                data = {
                    "client": client.to_dict(),
                    "log_id": log_instance.id,
                    "mailbox": mailbox,
                    "msg_id": msg_id,
                    "input_channel": "outlook"
                }
                redis_instance.set(job_id, json.dumps(data))

                request_data = {
                    "job_id": job_id,
                    "file_path": email_path,
                    "input_channel": "email",
                    "project": project
                }
                publish("start_transaction_process", "to_pipeline", request_data)

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
            mailbox=mailbox,
            service="OAuth",
            status="error",
            message=message,
            remarks=str(ex)
        )
