"""
Organization: AIDocbuilder Inc.
File: core/serializer.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Update serializer

Last Updated By: Nayem
Last Updated At: 2024-07-28

Description:
    This file contains serializers for different models such as Definition, ApplicationSettings,
    DefinedKey, Batch, EmailBatch, TrainBatch, MasterDictionary, BatchStatus and Country.

Dependencies:
    - from rest_framework import serializers
    - settings from django.conf
    - models from core

Main Features:
    - Convert database data into JSON.
"""
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth import get_user_model

from core import models


class DynamicModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)

        super(DynamicModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields.keys())

            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DefinitionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Definition
        fields = [
            "id",
            "definition_id",
            "vendor",
            "type",
            "cw1",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class DefinitionSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Definition
        fields = [
            "id",
            "definition_id",
            "layout_id",
            "hash_layout",
            "vendor",
            "type",
            "name_matching_text",
            "data",
            "cw1",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        try:
            pk = self.instance.id
            action_type = "update"
        except:
            pk = self.instance
            action_type = "create"

        if action_type == "update":
            # Update request data in case of update, as all required values to perform validations
            # might not be available in request data.
            data_keys = data.keys()
            if "definition_id" not in data_keys:
                data["definition_id"] = self.instance.definition_id
            if "type" not in data_keys:
                data["type"] = self.instance.type
            if "name_matching_text" not in data_keys:
                data["name_matching_text"] = self.instance.name_matching_text
            if "layout_id" not in data_keys:
                data["layout_id"] = self.instance.layout_id
            if "hash_layout" not in data_keys:
                data["hash_layout"] = self.instance.hash_layout


        if (
            models.Definition.objects.filter(
                definition_id__iexact=data["definition_id"]
            )
            .filter(layout_id__iexact=data["layout_id"])
            .exclude(pk=pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "Provided Definition ID (Profile ID) and layout_id combination already exists."
            )

        return data


class ApplicationSettingsSerializer(serializers.ModelSerializer):
    definition_versions = serializers.ReadOnlyField(
        default=settings.DEFINITION_VERSIONS
    )
    default_definition_version = serializers.ReadOnlyField(
        default=settings.DEFAULT_DEFINITION_VERSION
    )

    class Meta:
        model = models.ApplicationSettings
        fields = ["data", "definition_versions", "default_definition_version"]


class BatchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Batch
        fields = [
            "id",
            "definition_id",
            "vendor",
            "type",
            "mode",
            "extension",
            "project",
            "status",
            "confirmation_number",
            "is_dataset_batch",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class BatchSerializer(DynamicModelSerializer):
    class Meta:
        model = models.Batch
        exclude = ("ra_json",)
        read_only_fields = ["created_at", "updated_at"]


class EmailBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailBatch
        fields = [
            "id",
            "email_from",
            "email_subject",
            "email_to",
            "email_cc",
            "matched_profile_name",
            "parsed_file_type",
            "customs_number",
            "status",
            "verification_status",
            "assembly_triggered",
            "shipment_status_url",
            "confirmation_numbers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class EmailParsedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EmailParsedDocument
        fields = [
            "email",
            "name",
            "path",
            "type",
            "matched_profile_doc",
            "batch_id",
            "splitted",
        ]


class TrainParsedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrainParsedDocument
        fields = [
            "train_batch",
            "name",
            "path",
            "type",
            "matched_profile_doc",
            "batch_id",
            "splitted",
        ]


class TrainBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.TrainBatch
        fields = [
            "id",
            "matched_profile_name",
            "selected_doc_ids",
            "parsed_file_type",
            "status",
            "manual_classification_status",
            "customer",
            "custom_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class TrainBatchSerializerAll(serializers.ModelSerializer):
    class Meta:
        model = models.TrainBatch
        fields = "__all__"


class BatchStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BatchStatus
        fields = "__all__"
        read_only_fields = [f.name for f in models.BatchStatus._meta.get_fields()]


class DefinedKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DefinedKey
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class MasterDictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MasterDictionary
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Country
        fields = ["name", "code"]

class AiAgentConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AiAgentConversation
        fields = "__all__"
        read_only_fields = [f.name for f in models.AiAgentConversation._meta.get_fields()]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email']

class ChangeLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = models.ChangeLog
        fields = [
            "id",
            "user",
            "action",
            "module",
            "module_id",
            "change_category",
            "created_at",
            "updated_at",
        ]