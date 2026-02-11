"""
Organization: AIDocbuilder Inc.
File: export_data.py

Description:
    This script helps to export all necessary data from adminpanel.

Main Features:
    - Export CustomCategory.
"""

print("Exporting data...")

import json
import os
import argparse
from pathlib import Path

# Initialize Django first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
import django

django.setup()

from django.db import transaction

from core.admin import CustomCategoryResource

# ANSI escape codes for colored text
GREEN = "\033[92m"
RESET = "\033[0m"


def export_custom_category(output_dir):
    """Export custom_category data"""
    print("Exporting custom_category... ", end="")
    resource = CustomCategoryResource()
    dataset = resource.export()
    json_data = json.loads(dataset.json)

    file_path = output_dir / "CustomCategory.json"
    with open(file_path, "w") as f:
        json.dump(json_data, f)

    print(GREEN + "Completed" + RESET)


def main():
    """Main function to export data"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Export data from the system")
    # Note: when git bash is used on windows use //app/media instead of /app/media
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="/app/media",
        help="Directory to export data (default: /app/media)",
    )
    parser.add_argument(
        "-c",
        "--custom-category",
        action="store_true",
        help="Export Custom Category",
    )

    args = parser.parse_args()

    print("Exporting data at path: ", args.output_dir)

    # If no specific exports are selected, export all
    export_all = not (args.custom_category)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with transaction.atomic():
        # Export selected data
        if args.custom_category or export_all:
            export_custom_category(output_dir)


if __name__ == "__main__":
    main()
