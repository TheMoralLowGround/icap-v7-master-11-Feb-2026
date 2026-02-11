"""
Organization: AIDocbuilder Inc.
File: theme/admin.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file customize admin interface by registering models.

Dependencies:
    - admin from django.contrib
    - ThemeSetting from theme.models

Main Features:
    - Customize admin interface.
"""
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from theme.models import ThemeSetting


class ThemeSettingAdmin(ImportExportModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return not ThemeSetting.objects.exists()


admin.site.register(ThemeSetting, ThemeSettingAdmin)
