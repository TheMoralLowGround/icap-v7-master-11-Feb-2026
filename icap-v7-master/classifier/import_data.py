"""
Organization: AIDocbuilder Inc.
File: import_data.py

Description:
    This script helps to import all necessary data to adminpanel.

Main Features:
    - Import CustomCategory.
"""

print("Importing data...")

import json
import os
import argparse
from pathlib import Path

# Initialize Django first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
import django

django.setup()


from django.db import transaction

from tablib import Dataset

from core.admin import CustomCategoryResource


# ANSI escape codes for colored text
GREEN = "\033[92m"
RESET = "\033[0m"


def import_from_file(file_path, resource):
    """Handle importing specific file"""
    # Read JSON file
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    dataset = Dataset()
    headers = list(json_data[0].keys())
    dataset.headers = headers

    # Add data rows
    for item in json_data:
        row = [item.get(header) for header in headers]
        dataset.append(row)

    result = resource().import_data(
        dataset=dataset,
        raise_errors=True,
    )

    if result.has_validation_errors():
        print("\nValidation Errors:")
        for invalid_row in result.invalid_rows:
            print(f"Row {invalid_row.number}: {invalid_row.error}")

        return False

    print("\nImport Results:")
    print(f"Total rows: {len(json_data)}")
    print(f"New records: {result.totals['new']}")
    print(f"Updated records: {result.totals['update']}")

    assert result.totals["new"] + result.totals["update"] == len(
        json_data
    ), "Imported data does not match the number of rows in the JSON file."


def main():
    """This is the main function to import data"""
    parser = argparse.ArgumentParser(description="Import data into the system")
    # Note: when git bash is used on windows use //app/media instead of /app/media
    parser.add_argument(
        "-i",
        "--input-dir",
        type=str,
        default="/app/media",
        help="Directory containing import files (default: /app/media)",
    )
    parser.add_argument(
        "-c",
        "--custom-category",
        action="store_true",
        help="Import only Custom Category",
    )

    args = parser.parse_args()

    print("Importing data from path: ", args.input_dir)

    # If no specific exports are selected, export all
    import_all = not (args.custom_category)

    input_dir = Path(args.input_dir)

    with transaction.atomic():

        if args.custom_category or import_all:
            print("\nImporting CustomCategory... ")
            file_path = input_dir / "CustomCategory.json"
            import_from_file(file_path, CustomCategoryResource)
            print(GREEN + "Success" + RESET)


if __name__ == "__main__":
    main()
