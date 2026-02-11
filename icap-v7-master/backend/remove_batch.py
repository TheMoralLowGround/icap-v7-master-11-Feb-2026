"""
Organization: AIDocbuilder Inc.
File: remove_batch.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script removes batches from database conditionally if:
    Batch is uploaded in processing (production) mode and modified before 5 days.
 
Dependencies:
    - os, csv, datetime, django
    - settings from django.conf
    - Batch from core.models
    - DataCleanupConfig from settings.models
 
Main Features:
    - Deleted batches from database.
"""
import csv
import datetime
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()
from django.conf import settings

from core.models import Batch
from settings.models import DataCleanupConfig

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER


def main_process():
    """This is the main function to remove batch"""
    print("Removing Batches...")

    date_today = datetime.datetime.now(datetime.timezone.utc)

    # Prepare Log folder if doesn't exists
    log_folder = os.path.join(BATCH_INPUT_PATH, "AIDBLogs", "Batch Deletion Logs")
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    today_string = str(date_today).replace(":", ".")
    log_file = f"{log_folder}/{today_string}.csv"

    if DataCleanupConfig.objects.exists():
        user_config = DataCleanupConfig.objects.first()
        days = user_config.persist_prod_batch_for_days
        print(f"Finding batches updated before {days} days and in processing mode.")
        delta = datetime.timedelta(days=days)
        keep_after = date_today - delta
        qs = Batch.objects.filter(mode="processing", updated_at__lt=keep_after)
        qs_length = len(qs)
        if qs_length > 0:
            print(
                f"batches modified before {keep_after} '({qs_length})' will be deleted"
            )

            logs_data = qs.values(
                "id",
                "definition_id",
                "vendor",
                "type",
                "mode",
                "created_at",
                "updated_at",
            )
            # Add deleted_at column
            for i in logs_data:
                i["deleted_at"] = date_today

            with open(log_file, "w", newline="") as csvfile:
                fieldnames = [
                    "id",
                    "definition_id",
                    "vendor",
                    "type",
                    "mode",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(logs_data)

            qs.delete()
            print("Batches deleted successfully.")
        else:
            print("No Batches to delete.")

    else:
        print("Can not find DataCleanupConfig to Delete batches.")
        print("Please set DataCleanupConfig from Admin panel.")


if __name__ == "__main__":
    main_process()
