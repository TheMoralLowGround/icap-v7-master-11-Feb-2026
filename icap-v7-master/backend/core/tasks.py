"""
Organization: AIDocbuilder Inc.
File: core/tasks.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add feaure

Last Updated By: Nayem
Last Updated At: 2024-09-22

Description:
    This file contain functions for handling various database operations, managing inactive users, and scheduling messages.

Dependencies:
    - shared_task from celery
    - main_process as backup_data_process from backup_data
    - main_process as remove_batch_process from remove_batch
    - main_process as remove_batch_status_process from remove_batch_status
    - main_process as remove_email_batch_sequences_process from remove_email_batch_sequences
    - main_process as disable_inactive_users_process from disable_inactive_users
    - publish from rabbitmq_producer

Main Features:
    - Remove Batch, BatchStatus from database.
    - Backup definitions from database.
    - Publish messages to Rabbitmq.
"""

from celery import shared_task

from backup_data import main_process as backup_data_process
from remove_batch import main_process as remove_batch_process
from remove_batch_status import main_process as remove_batch_status_process
from remove_email_batch_sequences import (
    main_process as remove_email_batch_sequences_process,
)
from disable_inactive_users import main_process as disable_inactive_users_process
from rabbitmq_producer import publish
from core.models import ShipmentRecord


@shared_task
def remove_batch_status():
    """Remove BatchStatus entries from DB"""
    remove_batch_status_process()
    return


@shared_task
def remove_batch():
    """Remove Batch entries from DB"""
    remove_batch_process()
    return


@shared_task
def backup_data():
    """Backup Definition and Definition Settings from DB"""
    backup_data_process()
    return


@shared_task
def remove_email_batch_sequences():
    """Remove Email Batch Sequence from DB"""
    remove_email_batch_sequences_process()
    return


@shared_task
def disable_inactive_users():
    """Disable inactive users after 120 days of inactivity."""
    disable_inactive_users_process()
    return


@shared_task
def delayed_publish_to_rabbitmq(method, queue_name, body):
    """Function to publish delayed message"""
    publish(method, queue_name, body)


def schedule_delayed_publish_to_rabbitmq(method, queue_name, body, delay_seconds):
    """Function to schedule delayed message"""
    delayed_publish_to_rabbitmq.apply_async(
        args=[method, queue_name, body], countdown=delay_seconds
    )


@shared_task
def perform_shipment_record_create(data):
    def _create_shipment_record(value: str) -> None:
        if value:
            if value == "0":
                return
            shipment_record_kwargs = {
                "shipment_id": value.strip(),
            }
            shipment_record_q = ShipmentRecord.objects.filter(**shipment_record_kwargs)
            if not shipment_record_q.exists():
                ShipmentRecord.objects.create(**shipment_record_kwargs)

    for i in data:
        if isinstance(i, list):
            i = i[0]
            if i.lower() != "source_shipment_ref" and i != "0":
                _create_shipment_record(i)
    return "Successfull"
