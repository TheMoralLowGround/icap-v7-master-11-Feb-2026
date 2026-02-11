from django.contrib import admin
from .models import ProcessLog

@admin.register(ProcessLog)
class EmailIngestLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "service",
        "status",
        "file_name",
        "batch_id",
        "message",
        "created_at",
        "updated_at",
    )