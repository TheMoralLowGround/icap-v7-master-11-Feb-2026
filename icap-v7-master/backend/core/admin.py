"""
Organization: AIDocbuilder Inc.
File: core/admin.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Update code

Last Updated By: Nayem
Last Updated At: 2024-10-22

Description:
    This file customize admin interface by registering models and defining
    their display, search, and filter options for better management.

Dependencies:
    - dateutil.parser
    - admin from django.contrib
    - fields, resources from import_export
    - DateFormat from django.utils.dateformat
    - is_naive, make_aware from django.utils.timezone
    - ImportExportActionModelAdmin,ImportExportModelAdmin,
      ExportActionModelAdmin from import_export.admin

    - Batch, BatchStatus, DefinedKey, Definition, ApplicationSettings, EmailBatch, EmailParsedDocument,
      EmailToBatchLink, MasterDictionary, Country, TranslationCode, OutputJson, TrainBatch,
      TrainParsedDocument, TrainToBatchLink, TransactionLog from core.models

Main Features:
    - Customized admin user dashboard interface and functionality.
"""

from django.contrib import admin
from import_export import fields, resources
from import_export.admin import (
    ImportExportActionModelAdmin,
    ImportExportModelAdmin,
    ExportActionModelAdmin,
)

from django.utils.dateformat import DateFormat
from django.utils.timezone import is_naive, make_aware
import dateutil.parser
from django.shortcuts import redirect
from core.models import (
    Batch,
    BatchStatus,
    DefinedKey,
    Definition,
    ApplicationSettings,
    EmailBatch,
    EmailParsedDocument,
    EmailToBatchLink,
    MasterDictionary,
    Country,
    TranslationCode,
    OutputJson,
    TrainBatch,
    TrainParsedDocument,
    TrainToBatchLink,
    TransactionLog,
    ShipmentRecord,
    AiAgentConversation,
)
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from core.forms import ExcelUploadForm
from openpyxl import load_workbook
from django.contrib import messages

admin.site.site_header = "AIDB Platform Administration"


class DefinitionResource(resources.ModelResource):
    def dehydrate_id(self, definition):
        """Export ID as None"""
        return None

    def before_import_row(self, row, **kwargs):
        """Check if instance exists, update same instance by updating ID in uploading data"""
        definition_id = row["definition_id"]
        definition_layout_id = row["layout_id"]

        qs = Definition.objects.filter(definition_id__iexact=definition_id).filter(
            layout_id__iexact=definition_layout_id
        )
        if qs.exists():
            row["id"] = qs.first().id

        return super(DefinitionResource, self).before_import_row(row, **kwargs)

    class Meta:
        model = Definition
        exclude = ("created_at", "updated_at", "profile_doc")


class DefinitionReadOnlyAdmin(admin.ModelAdmin):
    search_fields = ["definition_id", "layout_id", "type", "name_matching_text"]
    list_display = [
        "definition_id",
        "layout_id",
        "type",
        "name_matching_text",
        "cw1",
        "updated_at",
    ]

    # def get_readonly_fields(self, request, obj=None):
    #     return (
    #         list(self.readonly_fields)
    #         + [field.name for field in obj._meta.fields]
    #         + [field.name for field in obj._meta.many_to_many]
    #     )

    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


admin.site.register(Definition, DefinitionReadOnlyAdmin)


class ApplicationSettingsResource(resources.ModelResource):
    def dehydrate_id(self, definitionsetting):
        """Export ID as None"""
        return None

    def before_import_row(self, row, **kwargs):
        """Check if instance exists, update same instance by updating ID in uploading data"""

        qs = ApplicationSettings.objects.all()
        if qs.exists():
            row["id"] = qs.first().id

        return super(ApplicationSettingsResource, self).before_import_row(row, **kwargs)

    class Meta:
        model = ApplicationSettings


class ApplicationSettingsAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = ApplicationSettingsResource

    def has_add_permission(self, *args, **kwargs):
        return not ApplicationSettings.objects.exists()


admin.site.register(ApplicationSettings, ApplicationSettingsAdmin)


class BatchAdmin(admin.ModelAdmin):
    model = Batch
    readonly_fields = ["created_at", "updated_at"]
    list_display = [
        "id",
        "mode",
        "vendor",
        "type",
        "extension",
        "project",
        "confirmation_number",
        "created_at",
    ]
    search_fields = ["id", "layout_ids", "vendor", "type"]
    list_filter = ["mode", "extension", "project"]


admin.site.register(Batch, BatchAdmin)


class EmailBatchAdmin(admin.ModelAdmin):
    model = EmailBatch
    readonly_fields = ["created_at", "updated_at"]
    list_display = [
        "id",
        "matched_profile_name",
        "email_subject",
        "created_at",
        "updated_at",
    ]
    search_fields = ["id", "matched_profile_name", "email_subject"]


admin.site.register(EmailBatch, EmailBatchAdmin)


class TrainBatchAdmin(admin.ModelAdmin):
    model = TrainBatch
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["id", "created_at", "updated_at"]
    search_fields = ["id"]


admin.site.register(TrainBatch, TrainBatchAdmin)


class EmailToBatchLinkAdmin(admin.ModelAdmin):
    search_fields = ["email__id", "batch_id", "mode", "classified", "uploaded"]
    list_display = ["email", "batch_id", "mode", "classified", "uploaded"]

    # def get_readonly_fields(self, request, obj=None):
    #     return list(self.readonly_fields) + \
    #         [field.name for field in obj._meta.fields] + \
    #         [field.name for field in obj._meta.many_to_many]

    # def has_add_permission(self, request):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


admin.site.register(EmailToBatchLink, EmailToBatchLinkAdmin)


class TrainToBatchLinkAdmin(admin.ModelAdmin):
    search_fields = ["train_batch__id", "batch_id", "mode", "classified", "uploaded"]
    list_display = ["train_batch", "batch_id", "mode", "classified", "uploaded"]


admin.site.register(TrainToBatchLink, TrainToBatchLinkAdmin)


class EmailParsedDocumentAdmin(admin.ModelAdmin):
    search_fields = ["email__id", "batch_id", "name", "type", "splitted"]
    list_display = [
        "name",
        "type",
        "email",
        "ra_json_created",
        "batch_id",
        "splitted",
        "matched_profile_doc",
    ]


admin.site.register(EmailParsedDocument, EmailParsedDocumentAdmin)


class TrainParsedDocumentAdmin(admin.ModelAdmin):
    search_fields = ["train_batch__id", "batch_id", "name", "type", "splitted"]
    list_display = [
        "name",
        "type",
        "train_batch",
        "ra_json_created",
        "batch_id",
        "splitted",
        "matched_profile_doc",
    ]


admin.site.register(TrainParsedDocument, TrainParsedDocumentAdmin)


class BatchStatusResource(resources.ModelResource):
    class Meta:
        model = BatchStatus


class BatchStatusAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = BatchStatusResource

    readonly_fields = [
        "batch_id",
        "event_time",
        "status",
        "message",
        "remarks",
        "action",
    ]
    list_display = ["batch_id", "event_time", "status", "message"]
    search_fields = ["batch_id", "message"]

    def has_add_permission(self, request):
        return False


admin.site.register(BatchStatus, BatchStatusAdmin)


class TranslationCodeResource(resources.ModelResource):
    """Translation Codes will be always imported as new objects"""

    definition_identifier = fields.Field()

    def dehydrate_definition_identifier(self, tcode):
        try:
            return f"{tcode.definition.definition_id} - {tcode.definition.type}"
        except:
            pass

    def dehydrate_id(self, tcode):
        return None

    def before_import_row(self, row, **kwargs):
        """Try to map definition automatically by reading definition_identifier"""
        definition_identifier = row["definition_identifier"]
        d_id, d_type = definition_identifier.split(" - ")

        qs = Definition.objects.filter(definition_id__iexact=d_id).filter(
            type__iexact=d_type
        )
        if qs.exists():
            row["definition"] = qs.first().id
        else:
            row["definition"] = None

        return super(TranslationCodeResource, self).before_import_row(row, **kwargs)

    class Meta:
        model = TranslationCode
        exclude = ("created_at", "updated_at")


class TranslationCodeAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = TranslationCodeResource
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["definition", "original_value", "translated_value"]


admin.site.register(TranslationCode, TranslationCodeAdmin)


class DefinedKeyResource(resources.ModelResource):
    definition_identifier = fields.Field()

    def dehydrate_definition_identifier(self, item):
        try:
            return f"{item.definition.definition_id} - {item.definition.type}"
        except:
            pass

    def dehydrate_id(self, tcode):
        return None

    def before_import_row(self, row, **kwargs):
        """Try to map definition automatically by reading definition_identifier"""
        definition_identifier = row["definition_identifier"]
        d_id, d_type = definition_identifier.split(" - ")

        qs = Definition.objects.filter(definition_id__iexact=d_id).filter(
            type__iexact=d_type
        )
        if qs.exists():
            row["definition"] = qs.first().id
        else:
            row["definition"] = None

        return super(DefinedKeyResource, self).before_import_row(row, **kwargs)

    class Meta:
        model = DefinedKey
        exclude = ("created_at", "updated_at")


class DefinedKeyAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = DefinedKeyResource
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["label", "definition"]
    search_fields = ["label"]


admin.site.register(DefinedKey, DefinedKeyAdmin)


class MasterDictionaryRescource(resources.ModelResource):

    class Meta:
        model = MasterDictionary


class MasterDictionaryAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    resource_class = MasterDictionaryRescource
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["name", "updated_at"]
    search_fields = ["name"]


admin.site.register(MasterDictionary, MasterDictionaryAdmin)


class CountryAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    readonly_fields = ["created_at"]
    list_display = ["name", "code", "updated_at"]
    search_fields = ["name", "code"]


admin.site.register(Country, CountryAdmin)


class OutputJsonAdmin(admin.ModelAdmin):
    model = OutputJson
    list_display = ["batch_id", "updated_at"]
    search_fields = ["batch_id"]

    def has_add_permission(self, request):
        return False


admin.site.register(OutputJson, OutputJsonAdmin)


# Define a resource class for TransactionLog for import/export functionality
class TransactionLogResource(resources.ModelResource):
    class Meta:
        model = TransactionLog
        fields = (
            "email_batch",
            "transaction_process_s",
            "transaction_uploading_s",
            "transaction_uploading_e",
            "re_process_email_batches_s",
            "time_to_queued",
            "email_parsing_s",
            "profile_matching_s",
            "profile_matching_e",
            "email_parsing_e",
            "supporting_batch_creation_time",
            "datacap_batch_creating_s",
            "datacap_batch_creating_e",
            "transaction_completion_time",
            "datacap_api_callback_time",
            "classification_process_s",
            "document_matching_s",
            "document_matching_e",
            "batch_splitting_s",
            "batch_splitting_e",
            "batch_creation_time",
            "classification_process_e",
            "assembly_process_s",
            "api_call_s",
            "each_api_call_s",
            "each_api_call_e",
            "api_call_e",
            "document_upload_s",
            "document_upload_e",
            "retry_document_upload_time",
            "upload_batch_process_time",
            "document_upload_s",
            "assembly_process_e",
            "re_process_extraction_s",
            "re_process_extraction_e",
            "re_process_api_s",
            "re_process_upload_doc_s",
            "re_process_upload_doc_e",
            "re_process_email_batches_e",
            "transaction_process_e",
        )


# Admin class for TransactionLog with import/export functionality
class TransactionLogAdmin(ImportExportModelAdmin):
    resource_class = TransactionLogResource

    list_display = (
        "email_batch",
        "transaction_process_s",
        "transaction_uploading_s",
        "transaction_uploading_e",
        "re_process_email_batches_s",
        "time_to_queued",
        "email_parsing_s",
        "profile_matching_s",
        "profile_matching_e",
        "email_parsing_e",
        "supporting_batch_creation_time",
        "datacap_batch_creating_s",
        "datacap_batch_creating_e",
        "transaction_completion_time",
        "datacap_api_callback_time",
        "classification_process_queued_time",
        "classification_process_s",
        "document_matching_s",
        "document_matching_e",
        "batch_splitting_s",
        "batch_splitting_e",
        "batch_creation_time",
        "upload_batch_process_time",
        "classification_process_e",
        "assembly_process_s",
        "transaction_result_generated_time",
        "api_call_s",
        "each_api_call_s",
        "retry_each_api_time",
        "each_api_call_e",
        "time_stamp_api_call_s",
        "time_stamp_api_call_e",
        "retry_time_stamp_api",
        "api_call_e",
        "transaction_awaiting_time",
        "document_upload_s",
        "each_document_upload_s",
        "retry_document_upload_time",
        "each_document_upload_e",
        "document_upload_e",
        "assembly_process_e",
        "re_process_extraction_s",
        "re_process_extraction_e",
        "re_process_api_s",
        "re_process_upload_doc_s",
        "re_process_upload_doc_e",
        "re_process_email_batches_e",
        "transaction_process_e",
    )

    search_fields = ("email_batch__id",)
    list_filter = (
        "transaction_uploading_s",
        "time_to_queued",
        "profile_matching_s",
    )

    # Custom methods to display time fields with seconds
    def transaction_process_s(self, obj):
        if obj.transaction_process_s:
            return obj.transaction_process_s.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def transaction_uploading_s(self, obj):
        if obj.transaction_uploading_start:
            return obj.transaction_uploading_start.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def transaction_uploading_e(self, obj):
        if obj.transaction_uploading_end:
            return obj.transaction_uploading_end.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def re_process_email_batches_s(self, obj):
        if obj.re_process_email_batches_start:
            return obj.re_process_email_batches_start.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def re_process_email_batches_e(self, obj):
        if obj.re_process_email_batches_end:
            return obj.re_process_email_batches_end.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def email_parsing_s(self, obj):
        if obj.email_parsing_start:
            return obj.email_parsing_start.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def email_parsing_e(self, obj):
        if obj.email_parsing_end:
            return obj.email_parsing_end.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def profile_matching_s(self, obj):
        if obj.profile_matching_start:
            return obj.profile_matching_start.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def profile_matching_e(self, obj):
        if obj.profile_matching_end:
            return obj.profile_matching_end.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def classification_process_s(self, obj):
        if obj.classification_process_start:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.classification_process_start
            ]
            return ", ".join(formatted_times)
        return None

    def classification_process_e(self, obj):
        if obj.classification_process_end:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.classification_process_end
            ]
            return ", ".join(formatted_times)
        return None

    def document_matching_s(self, obj):
        if obj.document_matching_start:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.document_matching_start
            ]
            return ", ".join(formatted_times)
        return None

    def document_matching_e(self, obj):
        if obj.document_matching_end:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.document_matching_end
            ]
            return ", ".join(formatted_times)
        return None

    def time_to_queued(self, obj):
        if obj.time_to_queued:
            return obj.time_to_queued.strftime("%Y-%m-%d %H:%M:%S")
        return None

    def datacap_batch_creating_s(self, obj):
        if obj.datacap_batch_creating_start:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.datacap_batch_creating_start
            ]
            return ", ".join(formatted_times)
        return None

    def datacap_batch_creating_e(self, obj):
        if obj.datacap_batch_creating_end:
            formatted_times = [
                self.format_json_datetime(dt) for dt in obj.datacap_batch_creating_end
            ]
            return ", ".join(formatted_times)
        return None

    # Helper method to convert ISO datetime strings to a more readable format
    def format_json_datetime(self, datetime_str):
        try:
            dt = dateutil.parser.isoparse(datetime_str)
            if is_naive(dt):
                dt = make_aware(dt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime_str  # If there's an error, return the original string


# Register the TransactionLog model
admin.site.register(TransactionLog, TransactionLogAdmin)


class ShipmentRecordAdmin(admin.ModelAdmin):
    list_display = ["shipment_id", "created_at"]
    actions = ["import_excel"]
    change_list_template = "admin/change_list.html"
    search_fields = ("shipment_id",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-shipment/",
                self.admin_site.admin_view(self.import_shipment),
                name="import-shipment",
            ),
        ]

        return custom_urls + urls

    def import_shipment(self, request):
        """Custom view to handle Excel file upload"""
        if request.method == "POST":
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file_path = request.FILES["excel_file"]
                wb = load_workbook(file_path)
                sheet = wb.active
                data = list(sheet.values)
                from core.tasks import perform_shipment_record_create

                perform_shipment_record_create.delay(data)
                messages.success(request, "Shipment records are being processed!")
                return redirect("..")

        return render(request, "admin/import_shipment_record.html")

    def import_button(self, request):
        """Add import button beside 'Add'"""

        return format_html(
            '<li><a class="add-link" href="import-shipment/">Import Shipments</a></li>'
        )

    def changelist_view(self, request, extra_context=None):
        """Pass extra context to render the button"""
        extra_context = extra_context or {}
        extra_context["import_button"] = self.import_button(request)
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(ShipmentRecord, ShipmentRecordAdmin)


class AiAgentConversationResource(resources.ModelResource):
    class Meta:
        model = AiAgentConversation


class AiAgentConversationAdmin(ExportActionModelAdmin, admin.ModelAdmin):
    resource_class = AiAgentConversationResource

    readonly_fields = [
        "event_time",
    ]
    list_display = ["transaction_id", "batch_id", "type", "event_time"]
    search_fields = ["transaction_id", "batch_id", "type"]


admin.site.register(AiAgentConversation, AiAgentConversationAdmin)
