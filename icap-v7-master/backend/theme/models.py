"""
Organization: AIDocbuilder Inc.
File: theme/models.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file define the database model for the theme app.

Dependencies:
    - ColorField from colorfield.fields
    - models from django.db

Main Features:
    - Database structure and schema for 'theme' app.
"""
from colorfield.fields import ColorField
from django.db import models


class ThemeSetting(models.Model):
    app_title = models.CharField(max_length=100, blank=True)
    app_title_color_light_mode = ColorField(blank=True, null=True)
    app_title_color_dark_mode = ColorField(blank=True, null=True)
    logo_light_mode = models.ImageField(upload_to="theme/logo", blank=True, null=True)
    logo_dark_mode = models.ImageField(upload_to="theme/logo", blank=True, null=True)
    favicon = models.ImageField(upload_to="theme/favicon", blank=True, null=True)
    header_color_light_mode = ColorField(blank=True, null=True)
    header_color_dark_mode = ColorField(blank=True, null=True)
    header_text_color_light_mode = ColorField(blank=True, null=True)
    header_text_color_dark_mode = ColorField(blank=True, null=True)
