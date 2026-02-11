"""
Organization: AIDocbuilder Inc.
File: access_control/apps.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-12-04

Description:
    This file configure the app settings.

Dependencies:
    - AppConfig from django.apps

Main Features:
    - Register the 'access_control' app in backpanel.
"""
from django.apps import AppConfig


class AccessControlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "access_control"
    verbose_name = "ACCESS CONTROL"
