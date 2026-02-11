"""
Organization: AIDocbuilder Inc.
File: utils/create_default_definitions.py
Version: 6.0

Authors:
    - Nayem - Initial implementation
    - Sunny - Code optimization

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This script helps to set default definitions.

Dependencies:
    - uuid
    - settings from django.conf
    - apps from django.apps
    - connection from django.db

Main Features:
    - Set default definitions.
"""
import uuid
from django.conf import settings
from django.apps import apps
from django.db import connection


class DefaultDefinitions:
    def __init__(self, ApplicationSettings):
        """Initialize the DefaultDefinitions class instance"""
        self.dafault_table_data = [
            {
                "table_id": 0,
                "table_name": "Main Table",
                "table_unique_id": str(uuid.uuid4()),
                "table_definition_data": {
                    "columns": [],
                    "keyItems": [],
                    "models": {},
                    "normalizerItems": [],
                    "ruleItems": [],
                    "lookupItems": [],
                },
            }
        ]
        self.applicationsettings = ApplicationSettings

    def get_migrated_models(self):
        """Get a list of all tables that currently exist in the database"""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}

        # Filter models based on the existence of their table name in the existing tables
        migrated_models = []
        for model in apps.get_models():
            if model._meta.db_table in existing_tables:
                migrated_models.append(model._meta.object_name)

        return migrated_models

    def get_default_table_data(self, batch_type=None):
        """
        Returns Table field data with default values set in definition settings.

        Args:
            batch_type (str): The type of batch to filter data.

        Returns:
            dafault_table_data (list): Contain the default table field data.

        Process Details:
            - If the batch type is '.xlsx' then return 'dafault_table_data'.
            - Fetch and process model field data if ApplicationSettings object exists.
            - Update the 'models' section of the first item in 'dafault_table_data'.
            - If batch type is '.pdf' then filter and process column fields with their default value.

        Notes:
            - Use the 'applicableFor' key to filter columns for specific batch type.
        """
        if batch_type == ".xlsx":
            return self.dafault_table_data
        if self.applicationsettings.objects.exists():
            application_settings = self.applicationsettings.objects.first().data
            model_fields = application_settings["tableSettings"]["model"]["fields"]

            table_models = {}
            for i in model_fields:
                key = i["key"]
                value = ""
                if "defaultValue" in i.keys():
                    value = i["defaultValue"]
                table_models.update({key: value})

            self.dafault_table_data[0]["table_definition_data"]["models"] = table_models
            if batch_type:
                column_fields = application_settings["tableSettings"]["column"]["fields"]

                # Filter columns based on batch_type:
                if batch_type == ".pdf":
                    identifier = "pdf"
                column_fields = [
                    i for i in column_fields if identifier in i["applicableFor"]
                ]

                column = {}
                predefined = {
                    "colLabel": "notInUse",
                    "colName": "None",
                    "startPos": "0",
                    "endPos": "0",
                }

                for i in column_fields:
                    key = i["key"]
                    value = predefined.get(key, "")
                    if value == "":
                        if "defaultValue" in i.keys():
                            value = i["defaultValue"]
                    column.update({key: value})

                self.dafault_table_data[0]["table_definition_data"]["columns"].append(
                    column
                )

        return self.dafault_table_data

    def default_definition(self):
        """helper function to create empty definition structure"""
        if "ApplicationSettings" not in self.get_migrated_models():
            return self.dafault_table_data
        result = {}
        for v in settings.DEFINITION_VERSIONS:
            result[v] = {"table": self.get_default_table_data(), "key": {}}
        return result
