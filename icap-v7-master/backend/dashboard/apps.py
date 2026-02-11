"""
Organization: AIDocbuilder Inc.
File: dashboard/apps.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file configures the app settings, including its name.

Dependencies:
    - AppConfig from django.apps

Main Features:
    - Register the 'dashboard' app in backpanel.
"""
from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        from dashboard import signals
