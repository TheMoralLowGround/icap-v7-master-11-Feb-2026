"""
Organization: AIDocbuilder Inc.
File: core/apps.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vinay
Last Updated At: 2023-11-01

Description:
    This file configures the app settings, including its name and ready method.

Dependencies:
    - AppConfig from django.apps

Main Features:
    - Register the 'core' app in backpanel.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from core import signals
