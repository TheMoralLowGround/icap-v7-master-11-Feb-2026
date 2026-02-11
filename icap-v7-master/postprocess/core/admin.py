from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin, ImportExportModelAdmin
from core.models import PostProcess, PromptDictionary


class PostProcessResource(resources.ModelResource):
    class Meta:
        model = PostProcess
        fields = ('process', 'prompt', 'code', 'unique_hash', 'created_at', 'updated_at')


class PromptDictionaryResource(resources.ModelResource):
    class Meta:
        model = PromptDictionary
        fields = ('name', 'prompt', 'unique_hash', 'created_at', 'updated_at')


class PostProcessAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    list_display = ["process", "unique_hash", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at", "process"]
    readonly_fields = ["unique_hash", "created_at", "updated_at"]
    search_fields = ["process", "prompt"]
    resource_classes = [PostProcessResource]
    ordering = ["-created_at"]
    
    class Meta:
        model = PostProcess


class PromptDictionaryAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    list_display = ["name", "unique_hash", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at", "name"]
    readonly_fields = ["unique_hash", "created_at", "updated_at"]
    search_fields = ["name", "prompt"]
    resource_classes = [PromptDictionaryResource]
    ordering = ["-created_at"]
    
    class Meta:
        model = PromptDictionary


admin.site.register(PostProcess, PostProcessAdmin)
admin.site.register(PromptDictionary, PromptDictionaryAdmin)
