import json
import redis
from celery import shared_task
from django.conf import settings
from rabbitmq_publisher import publish
from core.utils.utils import get_config_data
from utils.redis_utils import gerenate_job_id
from utils.logger_config import get_logger

logger = get_logger(__name__)


def get_redis(client_name):
    redis_instance = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, client_name=client_name
    )
    return redis_instance


@shared_task()
def read_outlook():
    logger.info("Start parsing outlook...")

    redis_instance = get_redis("read_outlook_1")

    lock_key = "lock:read_outlook_1"
    lock_set = redis_instance.set(lock_key, "locked", nx=True, ex=300)

    if not lock_set:
        logger.warning("read_outlook_1 already running, skipping...")
        return

    try:
        auth_config = get_config_data(input_type="email")
        for project, config in auth_config.items():
            logger.info(f"Processing outlook for '{project}'")

            auth_method = config.get("authMethod")
            if auth_method == "OAuth":
                job_id = gerenate_job_id()
                redis_instance.set(job_id, json.dumps(config))

                request_data = {
                    "job_id": job_id,
                    "project": project
                }
                publish("process_outlook", "to_input_channel", request_data)

    finally:
        redis_instance.delete(lock_key)


@shared_task()
def read_basic_email():
    logger.info("Start parsing basic email...")

    redis_instance = get_redis("read_basic_email_1")

    lock_key = "lock:read_basic_email_1"
    lock_set = redis_instance.set(lock_key, "locked", nx=True, ex=300)

    if not lock_set:
        logger.warning("read_basic_email_1 already running, skipping...")
        return

    try:
        auth_config = get_config_data(input_type="email")
        for project, config in auth_config.items():
            logger.info(f"Processing email for '{project}'")

            auth_method = config.get("authMethod")
            if auth_method == "BasicAuth":
                job_id = gerenate_job_id()
                redis_instance.set(job_id, json.dumps(config))

                request_data = {
                    "job_id": job_id,
                    "project": project
                }
                publish("process_basic_auth", "to_input_channel", request_data)

    finally:
        redis_instance.delete(lock_key)


@shared_task()
def read_sharepoint():
    logger.info("Start parsing sharepoint...")

    redis_instance = get_redis("read_sharepoint_1")

    lock_key = "lock:read_sharepoint_1"
    lock_set = redis_instance.set(lock_key, "locked", nx=True, ex=300)

    if not lock_set:
        logger.warning("read_sharepoint_1 already running, skipping...")
        return

    try:
        sharepoint_config = get_config_data(input_type="sharepoint")
        for project, config in sharepoint_config.items():
            logger.info(f"Processing sharepoint for '{project}'")

            job_id = gerenate_job_id()
            redis_instance.set(job_id, json.dumps(config))

            request_data = {
                "job_id": job_id,
                "project": project
            }
            publish("process_sharepoint", "to_input_channel", request_data)

    finally:
        redis_instance.delete(lock_key)


@shared_task()
def read_onedrive():
    logger.info("Start parsing onedrive..")

    redis_instance = get_redis("read_onedrive_1")

    lock_key = "lock:read_onedrive_1"
    lock_set = redis_instance.set(lock_key, "locked", nx=True, ex=300)

    if not lock_set:
        logger.warning("read_onedrive_1 already running, skipping...")
        return

    try:
        onedrive_config = get_config_data(input_type="onedrive")
        for project, config in onedrive_config.items():
            logger.info(f"Processing onedrive for '{project}'")

            job_id = gerenate_job_id()
            redis_instance.set(job_id, json.dumps(config))

            request_data = {
                "job_id": job_id,
                "project": project
            }
            publish("process_onedrive", "to_input_channel", request_data)

    finally:
        redis_instance.delete(lock_key)

