"""
Organization: AIDocbuilder Inc.
File: export_data.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script helps to export all necessary data from adminpanel.

Dependencies:
    - os, json, argparse, django
    - path from pathlib
    - MasterDictionaryRescource, ApplicationSettingsResource from core.admin
    - Project from dashboard.models
    - ProjectSerializer from dashboard.serializers

Main Features:
    - Export master dictionary.
    - Export application settings.
    - Export projects.
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

from core.admin import MasterDictionaryRescource, ApplicationSettingsResource
from dashboard.models import Project
from dashboard.serializers import ProjectSerializer

# ANSI escape codes for colored text
GREEN = "\033[92m"
RESET = "\033[0m"


def export_master_dictionary(output_dir):
    """Export MasterDictionary data"""
    print("Exporting MasterDictionary... ", end="")
    resource = MasterDictionaryRescource()
    dataset = resource.export()
    json_data = json.loads(dataset.json)
    
    file_path = output_dir / "MasterDictionary.json"
    with open(file_path, "w") as f:
        json.dump(json_data, f)
    
    print(GREEN + "Completed" + RESET)

def export_application_settings(output_dir):
    """Export ApplicationSettings data"""
    print("Exporting ApplicationSettings... ", end="")
    resource = ApplicationSettingsResource()
    dataset = resource.export()
    json_data = json.loads(dataset.json)
    
    file_path = output_dir / "ApplicationSettings.json"
    with open(file_path, "w") as f:
        json.dump(json_data, f)
    
    print(GREEN + "Completed" + RESET)

def export_projects(output_dir):
    """Export Projects data"""
    print("Exporting Projects... ", end="")
    projects = Project.objects.all()
    projects_data = ProjectSerializer(projects, many=True).data
    
    file_path = output_dir / "Projects.json"
    with open(file_path, "w") as f:
        json.dump(projects_data, f)
    
    print(GREEN + "Completed" + RESET)

def main():
    """Main function to export data"""
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Export data from the system')
    # Note: when git bash is used on windows use //app/media instead of /app/media
    parser.add_argument('-o', '--output-dir', type=str, default='/app/media',
                      help='Directory to export data (default: /app/media)')
    parser.add_argument('-m', '--master-dict', action='store_true',
                      help='Export master dictionary')
    parser.add_argument('-s', '--settings', action='store_true',
                      help='Export application settings')
    parser.add_argument('-p', '--projects', action='store_true',
                      help='Export projects')

    args = parser.parse_args()

    print("Exporting data at path: ", args.output_dir)

    # If no specific exports are selected, export all
    export_all = not (args.master_dict or args.settings or args.projects)

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with transaction.atomic():
        # Export selected data
        if args.master_dict or export_all:
            export_master_dictionary(output_dir)

        if args.settings or export_all:
            export_application_settings(output_dir)

        if args.projects or export_all:
            export_projects(output_dir)

if __name__ == "__main__":
    main()
