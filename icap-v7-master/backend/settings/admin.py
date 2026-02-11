"""
Organization: AIDocbuilder Inc.
File: settings/admin.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file customize admin interface by registering models.

Dependencies:
    - admin from django.contrib
    - DataCleanupConfig, DataExportConfig, DataImportConfig from settings.models

Main Features:
    - Customized admin user dashboard interface and features.
"""
from django.contrib import admin

from settings.models import DataCleanupConfig, DataExportConfig, DataImportConfig


class DataCleanupConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return not DataCleanupConfig.objects.exists()


admin.site.register(DataCleanupConfig, DataCleanupConfigAdmin)


class DataExportConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return not DataExportConfig.objects.exists()


admin.site.register(DataExportConfig, DataExportConfigAdmin)


class DataImportConfigAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return not DataImportConfig.objects.exists()


admin.site.register(DataImportConfig, DataImportConfigAdmin)
