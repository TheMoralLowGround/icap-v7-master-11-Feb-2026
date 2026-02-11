"""
Organization: AIDocbuilder Inc.
File: import_data.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script helps to import all necessary data to adminpanel.

Dependencies:
    - os, json, argparse, django
    - path from pathlib
    - transaction from django.db
    - Dataset from tablib
    - MasterDictionaryRescource, ApplicationSettingsResource from core.admin
    - import_projects_handler from dashboard.views

Main Features:
    - Import master dictionary.
    - Import application settings.
    - Import projects.
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

from core.admin import MasterDictionaryRescource, ApplicationSettingsResource
from dashboard.views import import_projects_handler

# ANSI escape codes for colored text
GREEN = "\033[92m"
RESET = "\033[0m"

def import_from_file(file_path, resource):
    """Handle importing specific file"""
    # Read JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
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

    assert result.totals["new"] + result.totals["update"] == len(json_data), "Imported data does not match the number of rows in the JSON file."

def main():
    """This is the main function to import data"""
    parser = argparse.ArgumentParser(description='Import data into the system')
    # Note: when git bash is used on windows use //app/media instead of /app/media
    parser.add_argument('-i', '--input-dir', type=str, default='/app/media',
                      help='Directory containing import files (default: /app/media)')
    parser.add_argument('-m','--master-dict', action='store_true',
                      help='Import only master dictionary')
    parser.add_argument('-s','--settings', action='store_true',
                      help='Import only application settings')
    parser.add_argument('-p', '--projects', action='store_true',
                      help='Import only projects')
    
    args = parser.parse_args()

    print("Importing data from path: ", args.input_dir)

    # If no specific exports are selected, export all
    import_all = not (args.master_dict or args.settings or args.projects)
    
    input_dir = Path(args.input_dir)

    with transaction.atomic():

        if args.master_dict or import_all:
            print("\nImporting MasterDictionary... ")
            file_path = input_dir / "MasterDictionary.json"
            import_from_file(file_path, MasterDictionaryRescource)
            print(GREEN + "Success" + RESET)

        if args.settings or import_all:
            print("\nImporting ApplicationSettings... ")
            file_path = input_dir / "ApplicationSettings.json"
            import_from_file(file_path, ApplicationSettingsResource)
            print(GREEN + "Success" + RESET)

        if args.projects or import_all:
            print("\nImporting Projects... ")
            file_path = input_dir / "Projects.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            print("\nImport Results:")
            print(f"Total rows: {len(json_data)}")
            result = import_projects_handler(json_data, ignore_fields=True)
            print("New records:", result["created_count"])
            print("Updated records:", result["updated_count"])

            print(GREEN + "Success" + RESET)

if __name__ == "__main__":
    main()
