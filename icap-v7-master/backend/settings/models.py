"""
Organization: AIDocbuilder Inc.
File: settings/models.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file define the database models for the settings app such as
    DataCleanupConfig, DataExportConfig, DataImportConfig.

Dependencies:
    - MaxValueValidator from django.core.validators
    - models from django.db

Main Features:
    - Database structure and schema for 'settings' app.
"""
from django.core.validators import MaxValueValidator
from django.db import models


class DataCleanupConfig(models.Model):
    persist_prod_batch_for_days = models.PositiveIntegerField(
        validators=[MaxValueValidator(90)],
        help_text="Persist Processing (Production) Batch for Number of days",
    )
    persist_batch_status_for_days = models.PositiveIntegerField(
        validators=[MaxValueValidator(90)],
        help_text="Persist Batch status for Number of days",
    )
    dump_batch_status_csv = models.BooleanField(
        default=True,
        help_text="if selected, To-be deleted batch status items will be saved as CSV to Batch Folder",
    )


class DataExportConfig(models.Model):
    export_system_name = models.CharField(max_length=100)
    export_system_url = models.CharField(
        max_length=250, help_text="Should not end with slash (/)"
    )
    export_system_auth_key = models.CharField(
        max_length=100, help_text="Copy Auth Key from Destination System"
    )


class DataImportConfig(models.Model):
    system_name = models.CharField(
        max_length=100,
        help_text="Name of the system which can send data to this system",
    )
    auth_key = models.CharField(
        max_length=100,
        help_text="This key is used to verify if request sender is valid.",
    )
