"""
Organization: AIDocbuilder Inc.
File: remove_email_batch_sequences.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script removes email batch sequences from database conditionally.
 
Dependencies:
    - os, django
    - connection from django.db
    - timezone from django.utils
 
Main Features:
    - Remove email batches.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()

from django.db import connection
from django.utils import timezone


def remove_email_batch_sequences():
    """This function remove email batch"""
    date_part = timezone.now().date().strftime("%Y%m%d")
    current_sequence_name = f"emailbatch{date_part}"

    with connection.cursor() as cursor:
        query = """SELECT sequence_name FROM information_schema.sequences;"""
        cursor.execute(query)
        results = cursor.fetchall()
        seq_list = [i[0] for i in results if i[0].startswith("emailbatch")]
        if current_sequence_name in seq_list:
            seq_list.remove(current_sequence_name)

        for seq_name in seq_list:
            query = f"""DROP SEQUENCE {seq_name}"""
            cursor.execute(query)
            print(f"SEQUENCE REMOVED: {seq_name}")
        else:
            print("No sequences to remove")


def main_process():
    """This is the main function to remove email batch"""
    print("Removing emailbatch sequences...")
    remove_email_batch_sequences()


if __name__ == "__main__":
    main_process()
