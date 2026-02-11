"""
Organization: AIDocbuilder Inc.
File: dashboard/admin.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Update code

Last Updated By: Nayem
Last Updated At: 2024-07-04

Description:
    This file customize admin interface by registering models and defining 
    their display, search, and filter options for better management.

Dependencies:
    - forms from django
    - apps from django.apps
    - Profile, ProfileDocument, Project, Template, Timeline from dashboard.models
    - admin from django.contrib
    - resources from import_export
    - ExportActionModelAdmin from import_export.admin

Main Features:
    - Customized admin user dashboard interface and functionality.
"""
from django import forms
from django.apps import apps
from dashboard.models import Profile, ProfileDocument, Project, Template, Timeline, DeveloperSettings, ProfileCustomer, ProcessCustomer, OutputChannel
from django.contrib import admin
from import_export import resources
from import_export.admin import (
    ImportExportActionModelAdmin,
    ImportExportModelAdmin,
    ExportActionModelAdmin,
)


def get_country_choices():
    """Country list with country code"""
    Country = apps.get_model("core", "Country")
    country_qs = Country.objects.all()
    country_code = [country.code for country in country_qs]

    country_choices = [(i, i) for i in country_code]

    return country_choices


class ProfileForm(forms.ModelForm):
    country = forms.ChoiceField(choices=[])

    class Meta:
        model = Profile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["country"].choices = get_country_choices()


class ProfileDocumentAdmin(admin.TabularInline):
    model = ProfileDocument


class ProfileCustomerAdmin(admin.TabularInline):
    model = ProfileCustomer


class ProfileAdmin(admin.ModelAdmin):
    form = ProfileForm
    inlines = [ProfileDocumentAdmin, ProfileCustomerAdmin]
    list_display = ["process_id", "name", "updated_at"]
    readonly_fields = [ "process_id", "name", "created_at", "updated_at"]
    search_fields = ["name", "process_id"]


admin.site.register(Profile, ProfileAdmin)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ["project_id", "name", "updated_at"]
    readonly_fields = ["project_id", "created_at", "updated_at"]
    search_fields = ["name", "project_id"]


admin.site.register(Project, ProjectAdmin)


class TemplateAdmin(admin.ModelAdmin):
    list_display = ["template_name", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


admin.site.register(Template, TemplateAdmin)


class TimelineResource(resources.ModelResource):
    class Meta:
        model = Timeline


class TimelineAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = TimelineResource

    readonly_fields = [
        "timeline_id",
        "event_time",
        "status",
        "message",
        "remarks",
        "action",
    ]
    list_display = ["timeline_id", "event_time", "status", "message"]
    search_fields = ["timeline_id", "message"]

    def has_add_permission(self, request):
        return False


admin.site.register(Timeline, TimelineAdmin)


class DeveloperSettingsResource(resources.ModelResource):
    def dehydrate_id(self, definitionsetting):
        """Export ID as None"""
        return None

    def before_import_row(self, row, **kwargs):
        """Check if instance exists, update same instance by updating ID in uploading data"""

        qs = DeveloperSettings.objects.all()
        if qs.exists():
            row["id"] = qs.first().id

        return super(DeveloperSettingsResource, self).before_import_row(row, **kwargs)

    class Meta:
        model = DeveloperSettings
        
class ApplicationSettingsAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = DeveloperSettingsResource

    def has_add_permission(self, *args, **kwargs):
        return not DeveloperSettings.objects.exists()


admin.site.register(DeveloperSettings, ApplicationSettingsAdmin)


class OutputChannelAdmin(admin.ModelAdmin):
    list_display = ["project", "output_type", "output_id", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]

admin.site.register(OutputChannel, OutputChannelAdmin)


class ProcessCustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "profile", "created_at"]
    search_fields = ["name", "profile__name"]
    list_filter = ["profile"]
    readonly_fields = ["created_at", "updated_at"]

admin.site.register(ProcessCustomer, ProcessCustomerAdmin)
