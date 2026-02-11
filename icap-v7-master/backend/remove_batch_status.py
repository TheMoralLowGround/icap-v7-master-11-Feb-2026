"""
Organization: AIDocbuilder Inc.
File: remove_batch_status.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script removes batch status from database conditionally.
    The removed batch status items will be saved to batch path in csv format.
 
Dependencies:
    - os, csv, datetime, sys, django
    - settings from django.conf
    - Batch, BatchStatus from core.models
    - DataCleanupConfig from settings.models
 
Main Features:
    - Deleted batch status records.
    - If executed with aditional command line argument "all": all batch status records will be deleted.
    - If no command line arguments provided: records older than 5 days will be removed.
"""
import csv
import datetime
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()
from django.conf import settings

from core.models import Batch, BatchStatus
from settings.models import DataCleanupConfig

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER


def dump_records(qs, date_today):
    """Dump to be deleted records as csv inside batch folder"""
    print("CSV files will be saved to batch folder")

    batches = list(qs.values_list("batch_id", flat=True).distinct())

    today_string = str(date_today).replace(":", ".")

    for batch in batches:
        try:
            sub_path = Batch.objects.get(id=batch).sub_path
            csv_file_name = os.path.join(
                BATCH_INPUT_PATH,
                sub_path,
                batch,
                f"batchstatus_data_{today_string}.csv",
            )

            with open(csv_file_name, "w", newline="") as csvfile:
                fieldnames = [
                    "id",
                    "batch_id",
                    "status",
                    "message",
                    "remarks",
                    "action",
                    "event_time",
                    "deleted_at",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                records = qs.filter(batch_id=batch).values()
                # Add deleted_at column
                for i in records:
                    i["deleted_at"] = date_today
                writer.writerows(records)

        except (Batch.DoesNotExist, FileNotFoundError):
            pass


def main_process(mode="general"):
    """This is the main function to remove batch status"""
    print("Removing Batch Status...")
    print(f'Executing script in "{mode}" mode')

    date_today = datetime.datetime.now(datetime.timezone.utc)

    if mode == "all":
        qs = BatchStatus.objects.all()
        print(f"All records '({len(qs)})' will be deleted")
        dump_records(qs, date_today)
        qs.delete()
        print("Batch status deleted successfully")

    else:
        if DataCleanupConfig.objects.exists():
            user_config = DataCleanupConfig.objects.first()
            days = user_config.persist_batch_status_for_days
            print(f"Finding Batch Status records created before {days} days.")
            delta = datetime.timedelta(days=days)
            keep_after = date_today - delta
            qs = BatchStatus.objects.filter(event_time__lt=keep_after)
            qs_length = len(qs)
            if qs_length > 0:
                print(
                    f"Records created before timestamp {keep_after} '({qs_length})' will be deleted"
                )

                dump = user_config.dump_batch_status_csv
                if dump:
                    dump_records(qs, date_today)

                # Remove batch status items
                qs.delete()
                print("Batch status records deleted successfully.")
            else:
                print("No Batch Status records to delete.")

        else:
            print("Can not find DataCleanupConfig to Delete batch status records.")
            print("Please set DataCleanupConfig from Admin panel.")


if __name__ == "__main__":
    mode = "general"
    if (len(sys.argv)) > 1:
        mode = sys.argv[1]
    main_process(mode=mode)
