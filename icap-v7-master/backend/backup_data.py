"""
Organization: AIDocbuilder Inc.
File: backup_data.py
Version: 6.0
 
Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
 
Last Updated By: Nayem
Last Updated At: 2024-12-04
 
Description:
    This script helps to Backup database data.
 
Dependencies:
    - json, os, re, shutil, traceback, django
    - settings from django.conf
    - ApplicationSettings from core.models
    - DefinitionSerializer from core.serializers
    - Project, Profile, ProfileDocument from dashboard.models
    - ProfileSerializer from dashboard.serializers
 
Main Features:
    - Backup application settings.
    - Backup projects.
    - Backup profiles.
"""
import json
import os
import re
import shutil
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

import django

django.setup()
from django.conf import settings

from core.models import ApplicationSettings
from core.serializers import DefinitionSerializer
from dashboard.models import Project, Profile, ProfileDocument
from dashboard.serializers import ProfileSerializer

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
UNNECESSARY_DIRS = ["Definitions", "DefinitionSettings"]
ERROR = 0

# ANSI escape code for colored text
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"


def get_dir_path(dir_name):
    """
    return dir_path after recreating it.
    """

    # Create Backup Folder structre if doesn't exists:
    path = os.path.join(BATCH_INPUT_PATH, "AIDBDataBackup", dir_name)

    # if path already exists, remove it to dump another data
    if os.path.exists(path):
        shutil.rmtree(path)

    # create folders for new dump
    os.makedirs(path)

    return path


def clean_unnecesarry_dirs():
    """
    Clean the dirs, which are not needed anymore.
    """
    global UNNECESSARY_DIRS

    for dir_name in UNNECESSARY_DIRS:
        path = os.path.join(BATCH_INPUT_PATH, "AIDBDataBackup", dir_name)

        # if path already exists, remove it
        if os.path.exists(path):
            shutil.rmtree(path)


def clean_file_name(file_name):
    """
    Clean file name by removing unsupported chars in file name.
    """
    file_name = re.sub(r'[\\/:*?"<>|]', "", file_name, 0)
    return file_name


def write_to_file(file_path, export_data):
    """
    Write the provided data to the provided file path.
    """
    file_content = json.dumps(export_data)
    with open(file_path, "w") as f:
        f.write(file_content)


def get_file_path(path, name):
    """
    Clean file name & return the file path.
    """
    file_name = f"{name}.json"
    file_name = clean_file_name(file_name)
    file_path = f"{path}/{file_name}"

    return file_path


def backup_application_settings():
    """
    Backup Application Settings.
    """
    global ERROR

    try:
        application_settings_path = get_dir_path("ApplicationSettings")

        fields = ["id", "data"]
        application_settings = list(ApplicationSettings.objects.all().values(*fields))

        for i in application_settings:
            i["id"] = None

            # always dump it in array to make it imprtable via admin
            export_data = i["data"]

            file_path = get_file_path(application_settings_path, "application_settings")

            write_to_file(file_path, export_data)
    except:
        ERROR = 1
        print(RED + "APPLICATION SETTINGS BACKUP FAILED" + RESET)
        tarceback = str(traceback.format_exc())
        print(tarceback)


def backup_projects():
    """
    Backup Projects.
    """
    global ERROR

    projects_path = get_dir_path("Projects")

    fields = ["id", "name", "settings"]
    projects = list(Project.objects.all().values(*fields))

    all_projects = []

    for project in projects:
        try:
            project["id"] = None

            export_data = [project]

            all_projects.append(project)

            file_path = get_file_path(projects_path, project["name"])

            write_to_file(file_path, export_data)
        except:
            ERROR = 1
            print(RED + f"PROJECTS {project['name']} BACKUP FAILED" + RESET)
            tarceback = str(traceback.format_exc())
            print(tarceback)

    # dump all projects
    file_path = get_file_path(projects_path, "all_projects")

    write_to_file(file_path, all_projects)


def backup_profiles():
    """
    Backup Profiles.
    """
    global ERROR
    profiles_path = get_dir_path("Profiles")

    profile_query = Profile.objects.all()
    profiles_data = ProfileSerializer(profile_query, many=True).data

    all_profiles = []

    for profile in profiles_data:
        try:
            profile["id"] = None

            for doc in profile["documents"]:
                definition = ProfileDocument.objects.get(id=doc["id"]).definition
                def_data = DefinitionSerializer(definition).data
                doc["definition"] = {"data": def_data["data"]}

            export_data = [profile]

            all_profiles.append(profile)

            file_path = get_file_path(profiles_path, profile["name"])

            write_to_file(file_path, export_data)
        except:
            ERROR = 1
            print(RED + f"PROFILE {profile['name']} BACKUP FAILED" + RESET)
            tarceback = str(traceback.format_exc())
            print(tarceback)

    # dumps all profiles
    file_path = get_file_path(profiles_path, "all_profiles")

    write_to_file(file_path, all_profiles)


def main_process():
    """
    Backup DB Data.
    """
    global ERROR

    print("DB Data Backup Statred...\n")

    print("Cleaning Unnecessary Dirs Initiated...\n")
    clean_unnecesarry_dirs()

    print("Application Settings Backup Initiated...\n")
    backup_application_settings()

    print("Projects Backup Initiated...\n")
    backup_projects()

    print("Profiles Backup Initiated...\n")
    backup_profiles()

    if ERROR:
        print(RED + "DB Data Backup script ended with errors." + RESET)
    else:
        print(GREEN + "DB Data Backup Completed Successfully." + RESET)


if __name__ == "__main__":
    main_process()
