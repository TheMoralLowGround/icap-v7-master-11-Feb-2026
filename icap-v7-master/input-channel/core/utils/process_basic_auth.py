import json
import imaplib
from core.models import ProcessLog
from rabbitmq_publisher import publish
from core.utils.utils import save_eml_file
from utils.redis_utils import redis_instance, get_redis_data, gerenate_job_id
from utils.logger_config import get_logger

logger = get_logger(__name__)

def process_basic_auth(data):
    try:
        job_id = data["job_id"]
        project = data["project"]

        config = get_redis_data(job_id)
        redis_instance.delete(job_id)

        mailbox = config["email"]
        mail = imaplib.IMAP4_SSL(config["server"], config["port"])
        mail.login(config["email"], config["password"])
        mail.select("inbox")

        _, response = mail.search(None, 'UNSEEN')
        messages = response[0].split()

        logger.info(f"{len(messages)} unread emails found")

        for msg in messages:
            log_instance = ProcessLog.objects.create(
                project=project,
                service="BasicAuth",
                mailbox=mailbox,
                status="queued",
            )
            try:
                _, email_data = mail.fetch(msg, '(RFC822)')

                for data in email_data:
                    if isinstance(data, tuple):
                        eml_content = data[1]

                email_path = save_eml_file(mailbox, eml_content)
                log_instance.status = "downloaded"
                log_instance.path = email_path
                log_instance.save(update_fields=["status", "path"])

                job_id = gerenate_job_id()
                data = {
                    "log_id": log_instance.id,
                    "input_channel": "basicauth"
                }
                redis_instance.set(job_id, json.dumps(data))

                request_data = {
                    "job_id": job_id,
                    "file_path": email_path,
                    "input_channel": "email",
                    "project": project
                }
                publish("start_transaction_process", "to_pipeline", request_data)

                mail.store(msg, "+FLAGS", "\\Seen")
                log_instance.status = "processed"
                log_instance.save(update_fields=["status"])

                # mail.copy(msg, "[Gmail]/All Mail")
                # mail.store(msg, '+FLAGS', '\\Deleted')
                # log_instance.status = "archived"
                # log_instance.save(update_fields=["status"])

            except Exception as ex:
                logger.error(str(ex))
                log_instance.status = "error"
                log_instance.message="Somethings Went Wrong"
                log_instance.remarks=str(ex)
                log_instance.save(update_fields=["status", "message", "remarks"])

        mail.logout()
        logger.info(f"Processing completed for '{project}'")

    except Exception as ex:
        logger.error(str(ex))
        ProcessLog.objects.create(
            project=data["project"],
            service="BasicAuth",
            status="error",
            message="Authentication Failed",
            remarks=str(ex)
        )