"""
Organization: AIDocbuilder Inc.
File: pipeline/apps.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file configure the app settings.

Dependencies:
    - AppConfig from django.apps

Main Features:
    - Configure the 'pipeline' app.
"""
from django.apps import AppConfig


class PipelineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pipeline"
