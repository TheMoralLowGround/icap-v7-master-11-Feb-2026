"""
Organization: AIDocbuilder Inc.
File: dashboard/models.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add models
    - Saifur - Update models

Last Updated By: Saifur
Last Updated At: 2024-10-08

Description:
    This file define the database models for the dashboard app, structure of 
    the database tables, their fields, and relationships between them.

Dependencies:
    - ValidationError from django.core.exceptions
    - models from django.db
    - UniqueConstraint from django.db.models
    - model_to_dict from django.forms.models
    - Lower from django.db.models.functions

Main Features:
    - Database structure and schema for 'dashboard' app.
"""

import uuid

from django.core.exceptions import ValidationError
from django.db import models, connection, transaction, IntegrityError
from django.db.models import UniqueConstraint
from django.forms.models import model_to_dict
from django.db.models.functions import Lower
from utils.encryption_utils import encrypt_value, decrypt_value

import time
import random

PROFILE_FIELDS_OPTIONS = {
    #"mode_of_transport": ["AIR", "COU", "SEA", "RAI", "ROA", "ALL"],
    "language": [
        "English",
        "Arabic",
        "ChinesePRC",
        "ChineseTaiwan",
        "Czech",
        "Dutch",
        "French",
        "German",
        "Greek",
        "Italian",
        "Japanese",
        "Korean",
        "Norwegian",
        "Polish",
        "PortugueseBrazilian",
        "PortugueseStandard",
        "Russian",
        "Slovak",
        "Slovenian",
        "Spanish",
        "Swedish",
        "Turkish",
        "None",
    ],
}

DEFAULT_DEFINITION_SETTINGS = {
    "options": {
        "options-keys": {
            "items": [],
            "title": "keys",
            "fields": [
                {"key": "keyLabel", "type": "text"},
                {"key": "keyValue", "type": "text"},
                {"key": "type", "type": "select", "optionsId": "options-col-type"},
                {"key": "qualifier", "type": "qualifier"},
                {
                    "key": "modType",
                    "type": "select",
                    "optionsId": "options-col-modType",
                },
                {"key": "compoundKeys", "type": "compoundKeys"},
                {"key": "export", "type": "checkbox"},
            ],
            "sortBy": "keyLabel",
            "lableKey": "keyLabel",
            "valueKey": "keyValue",
        },
        "options-col-type": {
            "items": [
                {
                    "type": "table",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": False,
                    "applicableForTable": True,
                },
                {
                    "type": "key",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": True,
                    "applicableForTable": False,
                },
                {
                    "type": "lookupCode",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": True,
                    "applicableForTable": True,
                },
                {
                    "type": "addressBlock",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": True,
                    "applicableForTable": False,
                },
                {
                    "type": "addressBlockPartial",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": True,
                    "applicableForTable": False,
                },
                {
                    "type": "compound",
                    "mandatory": False,
                    "description": "",
                    "applicableForKeys": True,
                    "applicableForTable": False,
                },
            ],
            "title": "type",
            "fields": [
                {"key": "mandatory", "type": "checkbox"},
                {"key": "type", "type": "text"},
                {"key": "applicableForKeys", "type": "checkbox"},
                {"key": "applicableForTable", "type": "checkbox"},
                {"key": "description", "type": "text"},
            ],
            "lableKey": "type",
            "valueKey": "type",
        },
        "options-col-modType": {
            "items": [
                {
                    "modType": "hazardousMaterial",
                    "mandatory": False,
                    "description": "",
                },
                {
                    "modType": "Financial Value",
                    "mandatory": False,
                    "description": "",
                },
            ],
            "title": "modType",
            "fields": [
                {"key": "mandatory", "type": "checkbox"},
                {"key": "modType", "type": "text"},
                {"key": "description", "type": "text"},
            ],
            "lableKey": "modType",
            "valueKey": "modType",
        },
        "options-meta-root-type": {
            "items": [],
            "title": "docType",
            "fields": [
                {"key": "docType", "type": "text"},
                {"key": "docCode", "type": "text"},
            ],
            "lableKey": "docType",
            "valueKey": "docType",
        },
    },
    "compoundKeys": [],
    "keyQualifiers": [],
    "editableOptions": [
        "options-col-type",
        "options-col-modType",
        "options-keys",
        "options-meta-root-type",
    ],
}
PREDEFINED_DEV_SETTINGS = {
        "frontend_settings": [{"name": "Profile Training", "value": True, "description":"Toggle on or off Profile Training view. Turn off to disable Profile Training view."}],
        "backend_settings": [{"name": "Mock API", "value": True, "description":"Use Assembly test API or use mock API. Turn off to use Assembly test API."}]
    }

def get_default_definition_settings():
    return DEFAULT_DEFINITION_SETTINGS

def get_predefined_dev_settings():
    return PREDEFINED_DEV_SETTINGS

class DeveloperSettings(models.Model):
    data = models.JSONField(default=dict)
    default_settings = models.JSONField(default=get_predefined_dev_settings)

    class Meta:
        verbose_name_plural = "Developer Settings"

class Template(models.Model):
    LANGUAGE_OPTIONS = [(i, i) for i in PROFILE_FIELDS_OPTIONS["language"]]
    OCR_CHOICES = [("S", "S"), ("P", "P"), ("A", "A")]
    FILE_TYPE_CHOICES = [(".xlsx", ".xlsx"), (".xls", ".xls")]

    template_name = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    project = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=255)
    country = models.CharField(max_length=2)
    file_type = models.CharField(max_length=30, choices=FILE_TYPE_CHOICES)
    language = models.CharField(max_length=50, choices=LANGUAGE_OPTIONS)
    category = models.CharField(max_length=50, default="Processing")
    ocr_engine = models.CharField(max_length=30, choices=OCR_CHOICES)
    page_rotate = models.BooleanField()
    barcode = models.BooleanField()
    use_existing_definition = models.BooleanField()
    existing_profile_name = models.CharField(max_length=255, default="", null=True)
    existing_document = models.CharField(max_length=255, default="", null=True)
    definition = models.JSONField(blank=True, default=dict)
    linked_batches = models.JSONField(blank=True, default=list)
    linked_profiles = models.JSONField(blank=True, default=list)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Templates"

    def clean(self):
        self.name = self.name.upper()
        template_name = f"{self.country}_{self.name}_{self.project}_{self.doc_type}"

        if (
            Template.objects.filter(template_name=template_name)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError("Template with same name already exists.")

        self.template_name = template_name

    def __str__(self):
        return f"{self.template_name}"


class Profile(models.Model):
    #MODE_CHOICES = [(i, i) for i in PROFILE_FIELDS_OPTIONS["mode_of_transport"]]

    EMAIL_SUBJECT_MATCH_OPTIONS = [
        ("ProcessId", "ProcessId"),
        ("StartsWith", "StartsWith"),
        ("EndsWith", "EndsWith"),
        ("Contains", "Contains"),
        ("Regex", "Regex"),
    ]

    process_uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Immutable unique identifier for Qdrant and internal references"
    )
    process_id = models.CharField(
        max_length=14,
        blank=False,
        unique=True,
        help_text="Auto-generated ID in format COUNTRY-PROJECT_ID-NUMBER (e.g., AF-AA1-0000001)"
    )
    name = models.CharField(max_length=300, unique=True)
    free_name = models.CharField(max_length=255)
    country = models.CharField(max_length=2)

    #mode_of_transport = models.CharField(max_length=5, choices=MODE_CHOICES)
    project = models.CharField(max_length=255)
    manual_validation = models.BooleanField()
    multi_shipment = models.BooleanField(default=False)
    send_time_stamp = models.BooleanField(default=False)
    automatic_splitting = models.BooleanField(default=False)
    ignore_dense_pages = models.BooleanField(default=False)
    exceptional_excel = models.BooleanField(default=False)

    email_domains = models.CharField(max_length=8000, blank=True, null=True)
    email_from = models.CharField(max_length=8000, blank=True, null=True)
    email_subject_match_option = models.CharField(
        max_length=50, choices=EMAIL_SUBJECT_MATCH_OPTIONS
    )
    email_subject_match_text = models.CharField(max_length=255)

    keys = models.JSONField(default=dict, blank=True)
    parties_config = models.JSONField(default=list, blank=True)
    translated_documents = models.JSONField(default=list, blank=True)
    dictionaries = models.JSONField(default=list, blank=True)

    success_notify_email_sender = models.BooleanField(default=False)
    success_notify_email_recipients = models.BooleanField(default=False)
    success_notify_additional_emails = models.CharField(
        max_length=500, null=True, blank=True
    )
    success_notify_exclude_emails = models.CharField(
        max_length=500, null=True, blank=True
    )

    failure_notify_email_sender = models.BooleanField(default=False)
    failure_notify_email_recipients = models.BooleanField(default=False)
    failure_notify_additional_emails = models.CharField(
        max_length=500, null=True, blank=True
    )
    failure_notify_exclude_emails = models.CharField(
        max_length=500, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name}"

    def clean(self):
        self.free_name = self.free_name.upper()
        name = f"{self.country}_{self.free_name}_{self.project}"

        if Profile.objects.filter(name=name).exclude(pk=self.pk).exists():
            raise ValidationError("Process with same name already exists.")

        self.name = name

    def to_dict(self):
        return model_to_dict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ProfileCustomer(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="customers"
    )
    name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, null=True, blank=True)
    address_id = models.CharField(max_length=40, null=True, blank=True)
    org_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=14, null=True, blank=True)
    short_code = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)

    success_notification_with_same_subject = models.BooleanField(default=True)
    success_notification_subject = models.CharField(
        max_length=255, null=True, blank=True
    )
    success_notify_email_sender = models.BooleanField(default=False)
    success_notify_email_recipients = models.BooleanField(default=False)
    success_notify_cc_users = models.BooleanField(default=False)
    success_notify_additional_emails = models.CharField(
        max_length=500, null=True, blank=True
    )

    failure_notification_with_same_subject = models.BooleanField(default=True)
    failure_notification_subject = models.CharField(
        max_length=255, null=True, blank=True
    )
    failure_notify_email_sender = models.BooleanField(default=False)
    failure_notify_email_recipients = models.BooleanField(default=False)
    failure_notify_cc_users = models.BooleanField(default=False)
    failure_notify_additional_emails = models.CharField(
        max_length=500, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -> {self.profile.name}"


class ProcessCustomer(models.Model):
    """Simple customer model for V7 process customer tab - separate from ProfileCustomer"""
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="process_customers"
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} -> {self.profile.name}"


class Timeline(models.Model):
    timeline_id = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    message = models.CharField(max_length=255, blank=True, null=True)
    sub_message = models.CharField(max_length=255, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=100, blank=True, null=True)
    event_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.timeline_id} Status"


class ProfileDocument(models.Model):
    NAME_MATCH_OPTIONS = [
        ("StartsWith", "StartsWith"),
        ("EndsWith", "EndsWith"),
        ("Contains", "Contains"),
        ("Regex", "Regex"),
        ("Auto", "Auto"),
    ]
    CONTENT_LOCATION_OPTIONS = [
        ("Email Body", "Email Body"),
        ("Email Attachment", "Email Attachment"),
        ("Additional Document", "Additional Document"),
    ]
    CATEGORY_OPTIONS = [
        ("Processing", "Processing"),
        ("Supporting", "Supporting"),
        ("Ignoring", "Ignoring"),
    ]

    LANGUAGE_OPTIONS = [(i, i) for i in PROFILE_FIELDS_OPTIONS["language"]]

    OCR_CHOICES = [("S", "S"), ("P", "P"), ("A", "A"), ("None", "None")]

    profile = models.ForeignKey(
        Profile, related_name="documents", on_delete=models.CASCADE
    )
    doc_type = models.CharField(max_length=255)
    content_location = models.CharField(max_length=50, choices=CONTENT_LOCATION_OPTIONS)
    name_matching_option = models.CharField(
        max_length=50, choices=NAME_MATCH_OPTIONS, null=True, blank=True
    )
    name_matching_text = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_OPTIONS)
    language = models.CharField(max_length=50, choices=LANGUAGE_OPTIONS)
    ocr_engine = models.CharField(max_length=30, choices=OCR_CHOICES)
    page_rotate = models.BooleanField()
    barcode = models.BooleanField()
    show_embedded_img = models.BooleanField(default=False)
    template = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                "profile",
                Lower("doc_type"),
                Lower("name_matching_text"),
                name="unique_profile_doc_type_and_name_matching",
            ),
        ]

    def clean(self):
        if (
            ProfileDocument.objects.filter(profile=self.profile)
            .filter(doc_type__iexact=self.doc_type)
            .filter(name_matching_text__iexact=self.name_matching_text)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                "Provided Profile ID, doc_type and name_matching_text combination already exists."
            )

    def to_dict(self):
        return model_to_dict(self)

    @property
    def activity_log_module(self):
        return "Profile"
    
    @property
    def activity_log_module_field(self):
        return self.profile
    

    @classmethod
    def from_dict(cls, data):
        # Extract ForeignKey ID and other fields
        profile_id = data.pop("profile")
        profile = Profile.objects.get(id=profile_id)

        return cls(profile=profile, **data)


def increment_project_id(current_id):
    """Increment project ID following AA1-AA9, BB1-BB9, ..., ZZ9 pattern"""
    if not current_id:
        return 'AA1'
    
    letters = current_id[:2]
    number = int(current_id[2:])
    
    if number < 9:
        return f"{letters}{number + 1}"
    
    # Need to increment letters
    first_char, second_char = letters[0], letters[1]
    
    if second_char < 'Z':
        return f"{first_char}{chr(ord(second_char) + 1)}1"
    
    if first_char < 'Z':
        return f"{chr(ord(first_char) + 1)}A1"
    
    raise ValidationError("Maximum project ID reached (ZZ9)")

def get_next_project_id():
    """Get next project ID with proper locking for production"""
    with connection.cursor() as cursor:
        # Use ORDER BY instead of MAX() with FOR UPDATE
        cursor.execute("""
            SELECT project_id 
            FROM dashboard_project 
            ORDER BY project_id DESC 
            LIMIT 1 
            FOR UPDATE
        """)
        result = cursor.fetchone()
        
        if not result or result[0] is None:
            return 'AA1'
        
        return increment_project_id(result[0])

class Project(models.Model):
    project_id = models.CharField(
        max_length=3,
        blank=False,
        unique=True,
        help_text="Auto-generated ID in format AA1-ZZ9"
    )
    name = models.CharField(max_length=255, unique=True)
    settings = models.JSONField(default=get_default_definition_settings, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['project_id']
    
    def __str__(self):
        return f"{self.project_id} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.project_id:
            # Retry logic for production safety
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    with transaction.atomic():
                        self.project_id = get_next_project_id()
                        super().save(*args, **kwargs)
                        return
                        
                except IntegrityError as e:
                    if 'unique constraint' in str(e).lower() and 'project_id' in str(e).lower():
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise ValidationError(f"Failed to generate unique project_id after {max_retries} attempts")
                        
                        # Small random delay to reduce collision probability
                        time.sleep(random.uniform(0.01, 0.05))
                        continue
                    else:
                        # Different integrity error, re-raise
                        raise
                except Exception:
                    # Any other exception, re-raise
                    raise
            
        else:
            # project_id already set, normal save
            super().save(*args, **kwargs)


class OutputChannel(models.Model):
    AUTH_CHOICES = [
        ("none", "No Auth"),
        ("basic", "Basic Auth"),
        ("token", "Token Auth"),
        ("api_key", "API Key in Header"),
        ("oauth2", "OAuth2 Bearer Token"),
    ]
    GRANT_TYPE = [
        ("password", "Password"),
        ("client_credentials", "Client Credentials"),
    ]
    OUTPUT_CHOICES = [
        ("json", "JSON"),
        ("document", "DOCUMENT")
    ]
    project = models.ForeignKey(
        'Project', on_delete=models.CASCADE, related_name="output_channels"
    )
    output_id = models.CharField(max_length = 255, unique=True, blank=True, null=True)
    output_type = models.CharField(max_length=20, choices=OUTPUT_CHOICES, default="json")

    is_active = models.BooleanField(default=True)
    auth_type = models.CharField(max_length=20, choices=AUTH_CHOICES, default="none")
    endpoint_url = models.CharField(max_length=500, blank=True, null=True)
    request_type = models.CharField(max_length=12, default="POST")

    grant_type = models.CharField(max_length=100, choices=GRANT_TYPE, default="client_credentials")
    scope = models.CharField(max_length=100, blank=True, null=True)

    _username = models.TextField(blank=True, null=True)
    _password = models.TextField(blank=True, null=True)
    _token = models.TextField(blank=True, null=True)
    api_key_name = models.CharField(max_length=100, blank=True, null=True)
    _api_key_value = models.TextField(blank=True, null=True)
    _client_id = models.CharField(max_length=255, blank=True, null=True)
    _client_secret = models.TextField(blank=True, null=True)
    token_url = models.CharField(max_length=500, blank=True, null=True)
    token_expires_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ENCRYPTED_FIELDS = ["username", "password", "token", "api_key_value", "client_id", "client_secret"]

    def __str__(self):
        return f"{self.project} ({self.auth_type})"

    def __getattr__(self, name):
        """Decrypt values"""
        if name in self.ENCRYPTED_FIELDS:
            raw = super().__getattribute__(f"_{name}")
            # return decrypt_value(raw) if raw else ""
            return raw
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """Encrypt values"""
        if name in self.ENCRYPTED_FIELDS:
            # super().__setattr__(f"_{name}", encrypt_value(value) if value else "")
            super().__setattr__(f"_{name}", value)
        else:
            super().__setattr__(name, value)
