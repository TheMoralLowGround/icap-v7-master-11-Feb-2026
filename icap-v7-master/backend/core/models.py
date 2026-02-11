"""
Organization: AIDocbuilder Inc.
File: core/models.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Update models

Last Updated By: Nayem
Last Updated At: 2024-07-28

Description:
    This file define the database models for the core app, structure of
    the database tables, their fields, and relationships between them.

Dependencies:
    - re, uuid
    - settings from django.conf
    - ValidationError from django.core.exceptions
    - apps from django.apps
    - models, connection from django.db
    - UniqueConstraint from django.db.models
    - Lower from django.db.models.functions
    - caches, cache from django.core.cache
    - ProfileDocument from dashboard.models
    - post_save from django.db.models.signals
    - receiver from django.dispatch
    - DefaultDefinitions from utils.create_default_definitions
    - ArrayField from django.contrib.postgres.fields

Main Features:
    - Database structure and schema for 'core' app.
"""

from django.utils import timezone
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.core.cache import cache
from django.conf import settings
from dashboard.models import ProfileDocument
from django.db.models.signals import post_save
from django.dispatch import receiver
from utils.create_default_definitions import DefaultDefinitions
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class ApplicationSettings(models.Model):
    data = models.JSONField(default=dict)

    class Meta:
        verbose_name_plural = "Application Settings"


def default_definition():
    return DefaultDefinitions(ApplicationSettings).default_definition()


class Definition(models.Model):
    definition_id = models.CharField(max_length=254, help_text='Profile Name')
    layout_id = models.CharField(max_length=100, blank=True, null=True)
    hash_layout = models.JSONField(default=list, blank=True)
    vendor = models.CharField(max_length=100)
    type = models.CharField(max_length=100, blank=True, null=True, help_text='Profile Document Type')
    name_matching_text = models.CharField(max_length=100, default="", blank=True, null=True, help_text="Profile Document Name Mathcing text")
    data = models.JSONField(default=default_definition, blank=True)
    cw1 = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_doc = models.OneToOneField(
        ProfileDocument, blank=True, null=True, on_delete=models.CASCADE
    )
    # Performance optimization: Store pre-computed embeddings
    embedding = models.BinaryField(null=True, blank=True, help_text='Pickled numpy embedding array for layout matching')
    embedding_model_version = models.CharField(max_length=100, null=True, blank=True, help_text='Model version used to generate embedding')

    class Meta:
        constraints = [
            UniqueConstraint(
                Lower("definition_id"),
                Lower("layout_id"),
                name="unique_definition_id_and_layout_id",
            ),
        ]

    def clean(self):
        if (
            Definition.objects.filter(definition_id__iexact=self.definition_id)
            .filter(layout_id__iexact=self.layout_id)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                "Provided Definition ID (Profile ID) and layout_id combination already exists."
            )

    def __str__(self):
        return f"{self.definition_id} - {self.vendor} - {self.type} - {self.name_matching_text}"


# # Possible Values for Status field:
# ''
# 'waiting'
# 'failed'
# 'retest'
# 'queued'
# 'inprogress'
# 'completed'
# 'pre_upload'
# 'upload'
# 'warning'
# 'awaiting_agent'


class Batch(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    layout_ids = models.JSONField(default=list, blank=True)
    visible = models.BooleanField(default=True)
    is_dataset_batch = models.BooleanField(default=False)
    project = models.CharField(max_length=254, blank=True, null=True)
    definition_id = models.CharField(max_length=254, blank=True, null=True, help_text='Profile Name')
    vendor = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=100, blank=True, null=True, help_text='Profile Document Type')
    name_matching_text = models.CharField(max_length=100, default="", help_text="Profile Document Name Mathcing text",blank=True)
    mode = models.CharField(max_length=100, default="processing")
    extension = models.CharField(max_length=20)
    sub_path = models.CharField(max_length=250, default="", blank=True)
    ra_json = models.JSONField(default=dict, blank=True)
    data_json = models.JSONField(default=dict, blank=True)
    raw_data_json = models.JSONField(default=dict, blank=True)
    atm_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(default="", blank=True, null=True, max_length=25)
    confirmation_number = models.CharField(max_length=30, blank=True, null=True)
    job_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Batches"

    def __str__(self):
        return f"{self.id}"


class OutputJson(models.Model):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, null=True, blank=True)
    output_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Output JSON"


class EmailBatch(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    email_from = models.CharField(max_length=1000, default="")
    email_subject = models.CharField(max_length=255, default="")
    email_to = models.TextField(default="", null=True, blank=True)
    email_cc = models.TextField(default="", null=True, blank=True)
    matched_profile_name = models.CharField(
        max_length=100, default="", null=True, blank=True
    )
    parsed_file_type = models.CharField(
        default="", max_length=10, blank=True, null=True
    )
    customs_number = models.CharField(null=True, blank=True, max_length=25)
    status = models.CharField(default="", blank=True, null=True, max_length=10)
    verification_status = models.CharField(
        default="", null=True, blank=True, max_length=10
    )
    assembly_triggered = models.BooleanField(default=False)
    assembled_results = models.JSONField(blank=True, default=list)
    api_triggered = models.BooleanField(default=False)
    api_response = models.JSONField(blank=True, default=list)
    api_retry_count = models.IntegerField(default=0)
    shipment_status_url = models.JSONField(blank=True, default=list)
    doc_upload_triggered = models.BooleanField(default=False)
    additional_docs_to_upload = models.JSONField(blank=True, default=list)
    confirmation_numbers = models.JSONField(blank=True, default=list)
    force_ocr_engine = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    customer = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name_plural = "Email Batches"

    def __str__(self):
        return f"{self.id}"


class EmailToBatchLink(models.Model):
    email = models.ForeignKey(
        EmailBatch, on_delete=models.CASCADE, related_name="batch_links"
    )
    batch_id = models.CharField(max_length=30)
    classified = models.BooleanField(default=False)
    uploaded = models.BooleanField(default=False)
    mode = models.CharField(max_length=30, default="")


class EmailParsedDocument(models.Model):
    email = models.ForeignKey(
        EmailBatch, on_delete=models.CASCADE, related_name="parsed_documents"
    )
    name = models.CharField(max_length=250)
    path = models.CharField(max_length=1000)
    type = models.CharField(max_length=20)
    matched_profile_doc = models.ForeignKey(
        ProfileDocument, on_delete=models.SET_NULL, null=True, blank=True
    )
    batch_id = models.CharField(max_length=30, blank=True, null=True)
    splitted = models.BooleanField(default=False)
    ra_json_created = models.BooleanField(default=False)
    doc_code = models.CharField(max_length=20, blank=True, null=True)

    def to_dict(self):
        from django.forms.models import model_to_dict
        return model_to_dict(self)

    @classmethod
    def from_dict(cls, data):
        # Handle foreign key fields by fetching the actual instances
        if 'email' in data and data['email']:
            data['email'] = EmailBatch.objects.get(id=data['email'])
        if 'matched_profile_doc' in data and data['matched_profile_doc']:
            from dashboard.models import ProfileDocument
            data['matched_profile_doc'] = ProfileDocument.objects.get(id=data['matched_profile_doc'])
        return cls(**data)


class TrainBatch(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    matched_profile_name = models.CharField(
        max_length=255, default="", null=True, blank=True
    )
    job_id = models.CharField(max_length=50, blank=True, null=True)
    selected_doc_ids = models.JSONField(default=list, blank=True)
    selected_doc_types = models.JSONField(default=list, blank=True)
    parsed_file_type = models.CharField(
        default="", max_length=10, blank=True, null=True
    )
    ra_json = models.JSONField(default=dict, blank=True)
    status = models.CharField(default="", blank=True, null=True, max_length=25)
    manual_classification_status = models.CharField(
        default="", null=True, blank=True, max_length=10
    )
    manual_classification_data = models.JSONField(default=list, blank=True)
    file_identifiers = models.JSONField(default=list, blank=True)
    file_ext_list = models.JSONField(default=list, blank=True)
    force_ocr_engine = models.BooleanField(default=False)
    customer = models.CharField(max_length=255, default="", blank=True, null=True)
    custom_data = models.CharField(max_length=255, default="", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Train Batches"

    def __str__(self):
        return f"{self.id}"


class TrainToBatchLink(models.Model):
    train_batch = models.ForeignKey(
        TrainBatch, on_delete=models.CASCADE, related_name="batch_links"
    )
    batch_id = models.CharField(max_length=30)
    classified = models.BooleanField(default=False)
    uploaded = models.BooleanField(default=False)
    mode = models.CharField(max_length=30, default="")


class TrainParsedDocument(models.Model):
    train_batch = models.ForeignKey(
        TrainBatch, on_delete=models.CASCADE, related_name="parsed_documents"
    )
    name = models.CharField(max_length=250)
    path = models.CharField(max_length=1000)
    type = models.CharField(max_length=20)
    matched_profile_doc = models.ForeignKey(
        ProfileDocument, on_delete=models.SET_NULL, null=True, blank=True
    )
    batch_id = models.CharField(max_length=30, blank=True, null=True)
    splitted = models.BooleanField(default=False)
    ra_json_created = models.BooleanField(default=False)

    def to_dict(self):
        from django.forms.models import model_to_dict
        return model_to_dict(self)

    @classmethod
    def from_dict(cls, data):
        # Handle foreign key fields by fetching the actual instances
        if 'train_batch' in data and data['train_batch']:
            data['train_batch'] = TrainBatch.objects.get(id=data['train_batch'])
        if 'matched_profile_doc' in data and data['matched_profile_doc']:
            from dashboard.models import ProfileDocument
            data['matched_profile_doc'] = ProfileDocument.objects.get(id=data['matched_profile_doc'])
        return cls(**data)


class BatchStatus(models.Model):
    batch_id = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    message = models.CharField(max_length=255, blank=True, null=True)
    sub_message = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=100, blank=True, null=True)
    event_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Batch Status"

    def __str__(self):
        return f"{self.batch_id} Status"


class TranslationCode(models.Model):
    definition = models.ForeignKey(
        Definition, on_delete=models.SET_NULL, null=True, blank=True
    )
    original_value = models.CharField(max_length=100)
    translated_value = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    method = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class DefinedKey(models.Model):
    definition = models.ForeignKey(
        Definition, on_delete=models.SET_NULL, null=True, blank=True
    )
    label = models.CharField(max_length=250)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.label


class MasterDictionary(models.Model):
    name = models.CharField(max_length=50, unique=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Master Dictionaries"


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


@receiver(post_save, sender=MasterDictionary)
def update_port_dict_cache(sender, instance, **kwargs):
    patterns = [r"airport_dict_part(\d+)", r"seaport_dict_part(\d+)"]
    for pattern in patterns:
        match = re.match(pattern, instance.name)
        if match:
            cache.set(instance.name, instance.data, timeout=None)
            break
        else:
            print("No match found for any pattern.")


class TransactionLog(models.Model):
    email_batch = models.CharField(max_length=100, null=True, blank=True)

    transaction_process_s = models.DateTimeField(null=True, blank=True)
    transaction_uploading_s = models.DateTimeField(null=True, blank=True)
    transaction_uploading_e = models.DateTimeField(null=True, blank=True)
    re_process_email_batches_s = models.DateTimeField(null=True, blank=True)
    time_to_queued = models.DateTimeField(null=True, blank=True)
    email_parsing_s = models.DateTimeField(null=True, blank=True)
    profile_matching_s = models.DateTimeField(null=True, blank=True)
    profile_matching_e = models.DateTimeField(null=True, blank=True)
    email_parsing_e = models.DateTimeField(null=True, blank=True)
    supporting_batch_creation_time = models.JSONField(default=list, blank=True)
    datacap_batch_creating_s = models.JSONField(default=list, blank=True)
    datacap_batch_creating_e = models.JSONField(default=list, blank=True)
    transaction_completion_time = models.DateTimeField(null=True, blank=True)
    datacap_api_callback_time = models.DateTimeField(null=True, blank=True)
    classification_process_queued_time = models.DateTimeField(null=True, blank=True)
    classification_process_s = models.JSONField(default=list, blank=True)
    document_matching_s = models.JSONField(default=list, blank=True)
    document_matching_e = models.JSONField(default=list, blank=True)
    batch_splitting_s = models.JSONField(default=list, blank=True)
    batch_splitting_e = models.JSONField(default=list, blank=True)
    batch_creation_time = models.JSONField(default=list, blank=True)
    upload_batch_process_time = models.JSONField(default=list, blank=True)
    classification_process_e = models.JSONField(default=list, blank=True)
    assembly_process_s = models.DateTimeField(null=True, blank=True)
    transaction_result_generated_time = models.DateTimeField(null=True, blank=True)
    api_call_s = models.DateTimeField(null=True, blank=True)
    each_api_call_s = models.JSONField(default=list, blank=True)
    retry_each_api_time = models.JSONField(default=list, blank=True)
    retry_each_api_time = models.JSONField(default=list, blank=True)
    each_api_call_e = models.JSONField(default=list, blank=True)
    time_stamp_api_call_s = models.JSONField(default=list, blank=True)
    time_stamp_api_call_e = models.JSONField(default=list, blank=True)
    retry_time_stamp_api = models.JSONField(default=list, blank=True)
    api_call_e = models.DateTimeField(null=True, blank=True)
    transaction_awaiting_time = models.DateTimeField(null=True, blank=True)
    document_upload_s = models.JSONField(default=list, blank=True)
    each_document_upload_s = models.JSONField(default=list, blank=True)
    each_document_upload_e = models.JSONField(default=list, blank=True)
    document_upload_e = models.JSONField(default=list, blank=True)
    retry_document_upload_time = models.JSONField(default=list, blank=True)
    assembly_process_e = models.DateTimeField(null=True, blank=True)
    re_process_extraction_s = models.DateTimeField(null=True, blank=True)
    re_process_extraction_e = models.DateTimeField(null=True, blank=True)
    re_process_api_s = models.DateTimeField(null=True, blank=True)
    re_process_upload_doc_s = models.DateTimeField(null=True, blank=True)
    re_process_upload_doc_e = models.DateTimeField(null=True, blank=True)
    re_process_email_batches_e = models.DateTimeField(null=True, blank=True)
    transaction_process_e = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TransactionLog for {self.email_batch if self.email_batch else 'No EmailBatch'}"

    class Meta:
        verbose_name_plural = "Transaction Logs"


class ShipmentRecord(models.Model):
    shipment_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shipment_id}"


class AiAgentConversation(models.Model):
    TIMELINE = 'timeline'
    USER = 'user'
    AGENT = 'agent'
    REASONING = 'reasoning'

    TYPE_CHOICES = [
        (TIMELINE, 'timeline'),
        (USER, 'user'),
        (AGENT, 'agent'),
        (REASONING, 'reasoning'),
    ]

    transaction_id = models.CharField(max_length=100, default="")
    batch_id = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    message = models.JSONField(default=dict)
    event_time = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "AI Agent Conversations"

    def __str__(self):
        return f"{self.batch_id} - {self.type} at {self.event_time}"

class ChangeLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    MODULE_CHOICES = [
        ('PROJECT', 'Project'),
        ('PROFILE', 'Profile'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='change_logs'
    )
    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    module = models.CharField(max_length=100, choices=MODULE_CHOICES)
    module_id = models.CharField(max_length=100, null=True, blank=True)
    module_object_name = models.CharField(max_length=255, null=True, blank=True)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_name = models.CharField(max_length=255, null=True, blank=True)
    change_category = models.CharField(max_length=100, null=True, blank=True)
    
    # Old values
    old_data_path = models.CharField(max_length=255, blank=True, null=True)

    # New values
    new_data_path = models.CharField(max_length=255, blank=True, null=True)
    
    # IP address and user agent
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    description = models.TextField(null=True, blank=True)
    is_reverted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['module', 'module_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.module}"