from django.contrib import admin
from import_export.admin import (
    ImportExportActionModelAdmin,
    ImportExportModelAdmin,
)
from import_export.resources import ModelResource

from core.models import CustomCategory

admin.site.site_header = "Classifier Backend Administration"


class CustomCategoryResource(ModelResource):
    class Meta:
        model = CustomCategory


@admin.register(CustomCategory)
class CustomCategoryAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = CustomCategoryResource
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["profile", "data", "updated_at"]
    search_fields = ["profile", "data"]
