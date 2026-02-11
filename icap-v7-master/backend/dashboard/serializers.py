"""
Organization: AIDocbuilder Inc.
File: dashboard/serializer.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Update serializer

Last Updated By: Nayem
Last Updated At: 2024-08-23

Description:
    This file contains serializers for different models such as ProfileSerializer, ProfileListSerializer,
    TimelineSerializer, ProfileDocumentSerializer, TemplateListSerializer, TemplateSerializer, ProjectSerializer, ProjectListSerializer

Dependencies:
    - re
    - DefaultDefinitions from utils.create_default_definitions
    - ApplicationSettings, Definition from core.models
    - DefinitionSerializer from core.serializers
    - serializers from rest_framework
    - models from dashboard
    - Batch from core.models
    - receiver from django.dispatch
    - post_save, post_delete from django.db.models.signals

Main Features:
    - Convert database data into JSON.
"""

import yaml
import json
from utils.create_default_definitions import DefaultDefinitions
from utils.encryption_utils import encrypt_value
from core.models import ApplicationSettings, Definition
from core.serializers import DefinitionSerializer
from rest_framework import serializers
from dashboard import models
from core.models import Batch
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import re
from dashboard.utils.yaml_utils import check_yaml_syntax


@receiver(post_save, sender=models.Template, dispatch_uid="update_batch_definition_id")
def update_batch_definition_id(sender, instance, created, **kwargs):
    """Update existing batch definition ID"""
    if not created:
        for batch_id in instance.linked_batches:
            qs = Batch.objects.filter(id=batch_id)
            if not qs.exists():
                continue
            batch = qs.first()
            batch.definition_id = instance.template_name
            batch.save()
        return


class ProfileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = [
            "id",
            "process_id",
            "process_uid",
            "name",
            "country",
            "email_subject_match_text",
            #"mode_of_transport",
            "project",
            "updated_at",
        ]
        read_only_fields = ["id", "name"]


class TimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Timeline
        fields = "__all__"
        read_only_fields = [f.name for f in models.Timeline._meta.get_fields()]


class ProfileCustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow for updating existing items

    class Meta:
        model = models.ProfileCustomer
        fields = "__all__"
        read_only_fields = ["profile"]


class ProcessCustomerSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow for updating existing items

    class Meta:
        model = models.ProcessCustomer
        fields = "__all__"
        read_only_fields = ["profile"]


class ProfileDocumentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow for updating existing items
    template = serializers.CharField(default=None, allow_null=True, required=False)

    class Meta:
        model = models.ProfileDocument
        fields = "__all__"
        read_only_fields = ["profile"]


class TemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Template
        fields = [
            "id",
            "template_name",
            "name",
            "project",
            "doc_type",
            "country",
            "file_type",
            "ocr_engine",
            "page_rotate",
            "barcode",
            "linked_profiles",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "template_name"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["linked_profiles"] = len(data["linked_profiles"])
        return data


class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Template
        fields = "__all__"
        read_only_fields = ["id", "template_name", "created_at", "updated_at"]

    def validate(self, data):
        try:
            pk = self.instance.id
            request_type = "update"
        except Exception:
            pk = self.instance
            request_type = "create"

        if request_type == "update":
            # Update request data in case of update, as all values might not be
            # available in request data.
            data_keys = data.keys()
            if "name" not in data_keys:
                data["name"] = self.instance.name
            if "project" not in data_keys:
                data["project"] = self.instance.project

        data["name"] = data["name"].upper()
        template_name = (
            f"{data['country']}_{data['name']}_{data['project']}_{data['doc_type']}"
        )
        data["template_name"] = template_name

        if (
            models.Template.objects.filter(template_name=data["template_name"])
            .exclude(pk=pk)
            .exists()
        ):
            raise serializers.ValidationError("Template with same name already exists.")

        return data

    def update(self, instance, validated_data):
        definition_id = validated_data.get("existing_profile_name", "")
        if definition_id and definition_id != "":
            serial_no = validated_data["existing_document"].split(" ")[-1]

            try:
                serial_no = int(serial_no)
                type = " ".join(validated_data["existing_document"].split(" ")[:-1])
            except:
                serial_no = 1
                type = validated_data["existing_document"]

            qs = (
                Definition.objects.filter(definition_id__iexact=definition_id)
                .filter(type__iexact=type)
                .order_by("created_at")
            )

            if qs.count() >= serial_no:
                qs = qs[serial_no - 1]

            definition = DefinitionSerializer(qs).data
            validated_data["definition"] = definition["data"]
        elif definition_id is None:
            # creates a blank definition
            default_definitions_class = DefaultDefinitions(
                ApplicationSettings=ApplicationSettings
            )
            definition = default_definitions_class.default_definition()
            validated_data["definition"] = definition

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class ProfileSerializer(serializers.ModelSerializer):
    customers = ProfileCustomerSerializer(many=True)
    documents = ProfileDocumentSerializer(many=True)
    process_customers = ProcessCustomerSerializer(many=True, required=False)

    class Meta:
        model = models.Profile
        fields = "__all__"
        read_only_fields = ["id", "name", "process_uid", "created_at", "updated_at"]

    def validate(self, data):
        try:
            pk = self.instance.id
            request_type = "update"
        except:
            pk = self.instance
            request_type = "create"

        if request_type == "update":
            # Update request data in case of update, as all values might not be
            # available in request data.
            data_keys = data.keys()
            if "country" not in data_keys:
                data["country"] = self.instance.country
            if "free_name" not in data_keys:
                data["free_name"] = self.instance.free_name
            # if "mode_of_transport" not in data_keys:
                # data["mode_of_transport"] = self.instance.mode_of_transport
            if "project" not in data_keys:
                data["project"] = self.instance.project
            if "documents" not in data_keys:
                data["documents"] = self.instance.documents
            if "customers" not in data_keys:
                data["customers"] = self.instance.customers
            if "process_customers" not in data_keys:
                data["process_customers"] = list(self.instance.process_customers.values())

        data["free_name"] = data["free_name"].upper()
        name = f"{data['country']}_{data['free_name']}_{data['project']}"
        data["name"] = name

        if models.Profile.objects.filter(name=data["name"]).exclude(pk=pk).exists():
            raise serializers.ValidationError("Process with same name already exists.")

        validation_errors = {}
        profile_documents_dict = {}
        documents_validation_errors = [{} for _ in range(len(data["documents"]))]

        for index, d in enumerate(data["documents"]):
            # Validate one Email Body Document per profile
            if d["content_location"] == "Email Body":
                if profile_documents_dict.get("Email Body"):
                    documents_validation_errors[index][
                        "content_location"
                    ] = "Only one 'Email Body' document is allowed per profile."
                else:
                    profile_documents_dict["Email Body"] = "Email Body"

            # Validate one Additional Document per profile
            if d["content_location"] == "Additional Document":
                if profile_documents_dict.get("Additional Document"):
                    documents_validation_errors[index][
                        "content_location"
                    ] = "Only one 'Additional Document' allowed per profile."
                else:
                    profile_documents_dict["Additional Document"] = (
                        "Additional Document"
                    )

            # Validate Auto name_matching_option for same doc type
            if profile_documents_dict.get(f"{d['doc_type']}"):
                profile_documents_dict[f"{d['doc_type']}"].append(
                    d["name_matching_option"]
                )

                if "Auto" in profile_documents_dict.get(f"{d['doc_type']}"):
                    documents_validation_errors[index][
                        "name_matching_option"
                    ] = "'Auto' name matching doc types cannot be repeated."
            else:
                profile_documents_dict[f"{d['doc_type']}"] = [d["name_matching_option"]]

            # Validate None name_matching_option for same doc type
            if d["name_matching_option"] == "":
                if profile_documents_dict.get("None"):
                    documents_validation_errors[index][
                        "name_matching_option"
                    ] = "Only one 'None' name matching document allowed per profile."
                else:
                    profile_documents_dict["None"] = "None"

            # Validate 'Additional Document' and 'None' name matching documents are not allowed together
            if (
                profile_documents_dict.get("None")
                and profile_documents_dict.get("Additional Document")
            ) and (
                d["name_matching_option"] == ""
                or d["content_location"] == "Additional Document"
            ):
                field = (
                    "content_location"
                    if d["content_location"] == "Additional Document"
                    else "name_matching_option"
                )
                documents_validation_errors[index][
                    field
                ] = "'Additional Document' and 'None' name matching documents are not allowed together."

            # Validate unique name_matching_text
            if d["name_matching_text"]:
                name_matching_text = d["name_matching_text"].lower()
            else:
                name_matching_text = d["name_matching_text"]
            if profile_documents_dict.get(name_matching_text):
                documents_validation_errors[index][
                    "name_matching_text"
                ] = "Name matching texts should be unique per profile."
            else:
                profile_documents_dict[name_matching_text] = name_matching_text

            # Validate supporting documents are not allowed in multi shipment profile
            if d["category"] == "Supporting" and data["multi_shipment"]:
                documents_validation_errors[index][
                    "category"
                ] = "Supporting documents are not allowed in multi shipment profile."

        if not all(i == {} for i in documents_validation_errors):
            validation_errors["documents"] = documents_validation_errors

        # Validate regex input
        if data.get("email_subject_match_option") == "Regex":
            input_value = data.get("email_subject_match_text")
            try:
                re.compile(input_value)
            except re.error:
                validation_errors["email_subject_match_text"] = ["Invalid regex input"]

        # Validate email fields are valid.
        email_from = data.get("email_from")
        email_subject_match_text = data.get("email_subject_match_text")

        if email_from:
            if not ("@" in email_from):
                validation_errors["email_from"] = [
                    "Must be valid email address and should contain '@'"
                ]

        self.validates_email_subject_match_text(data, pk, validation_errors)

        # Validate Customers
        customer_names = []
        customers_validation_errors = [{} for _ in range(len(data["customers"]))]

        for index, d in enumerate(data["customers"]):
            customer_name = d["name"]

            if customer_name in customer_names:
                customers_validation_errors[index][
                    "name"
                ] = "Duplicate customer name is not allowed."
            else:
                customer_names.append(customer_name)

        if not all(i == {} for i in customers_validation_errors):
            validation_errors["customers"] = customers_validation_errors

        # optional_email_fields = [
        #     "success_notify_additional_emails",
        #     "failure_notify_additional_emails",
        # ]
        # for field in optional_email_fields:
        #     value = data.get(field)
        #     if value:
        #         emails = value.split(",")
        #         emails = [i.strip() for i in emails if i]  # Remove extra spaces
        #         invalid_emails = [i for i in emails if "@" not in i]
        #         if invalid_emails:
        #             validation_errors[field] = [
        #                 "Must be comma separated list of valid email address and should contain '@'"
        #             ]

        if validation_errors:
            raise serializers.ValidationError(validation_errors)

        return data

    def validates_email_subject_match_text(self, data, pk, validation_errors):
        email_subject_match_text = data.get("email_subject_match_text")
        email_subject_match_option = data.get("email_subject_match_option")

        if not email_subject_match_text:
            return

        if (
            models.Profile.objects.filter(
                email_subject_match_text__iexact=email_subject_match_text
            )
            .exclude(pk=pk)
            .exists()
        ):
            validation_errors["email_subject_match_text"] = [
                "Email Subject should be unique"
            ]

        if email_subject_match_option != "Contains":
            return

        existing_profiles = (
            models.Profile.objects.filter(
                email_subject_match_option=email_subject_match_option
            )
            .exclude(pk=pk)
            .values_list("email_subject_match_text", flat=True)
        )

        for existing_text in existing_profiles:
            if (
                email_subject_match_text.lower() in existing_text.lower()
                or existing_text.lower() in email_subject_match_text.lower()
            ):
                validation_errors["email_subject_match_text"] = [
                    "Email Subject must not partially conflict with existing profiles"
                ]
                break

    def create(self, validated_data):
        documents = validated_data.pop("documents")
        customers = validated_data.pop("customers")
        process_customers = validated_data.pop("process_customers", [])

        profile_instance = models.Profile.objects.create(**validated_data)
        
        # Initialize profile.keys with project keys if not already set
        if not profile_instance.keys or not isinstance(profile_instance.keys, list):
            try:
                project = models.Project.objects.get(name=profile_instance.project)
                project_settings = project.settings
                project_keys = project_settings.get("options", {}).get("options-keys", {})
                project_key_items = project_keys.get("items", [])
                
                # Initialize keys with project keys, using project prompt as default process prompt
                profile_instance.keys = [
                    {"keyValue": item["keyValue"], "prompt": item.get("prompt", "")}
                    for item in project_key_items if item.get("addToProcess", False)
                ]
                profile_instance.save()
            except (models.Project.DoesNotExist, KeyError, AttributeError):
                pass
        
        template_list = [doc.get("template", None) for doc in documents]
        update_template_profile_count(
            profile=profile_instance, template_list=template_list, create=True
        )
        # Create documents
        for document in documents:
            models.ProfileDocument.objects.create(profile=profile_instance, **document)

        # Create customers
        for customer in customers:
            models.ProfileCustomer.objects.create(profile=profile_instance, **customer)

        # Create process customers
        for process_customer in process_customers:
            models.ProcessCustomer.objects.create(profile=profile_instance, **process_customer)

        return profile_instance

    def update(self, instance, validated_data):
        documents = validated_data.pop("documents", None)
        customers = validated_data.pop("customers", None)
        process_customers = validated_data.pop("process_customers", None)

        # Update all profile fields at once (excluding relations)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle customers
        if isinstance(customers, list):
            self._handle_customers(instance, customers)

        # Handle process customers
        if isinstance(process_customers, list):
            self._handle_process_customers(instance, process_customers)

        # Handle documents
        if isinstance(documents, list):
            self._handle_documents(instance, documents)

        return instance

    def _handle_documents(self, instance, documents):
        existing_profile_documents = models.ProfileDocument.objects.filter(
            profile=instance.pk
        ).values_list("id", flat=True)

        new_documents_ids = []
        template_list = [doc.get("template", None) for doc in documents]

        update_template_profile_count(profile=instance, template_list=template_list)

        for document in documents:
            if "id" in document.keys():
                if models.ProfileDocument.objects.filter(id=document["id"]).exists():
                    document_instance = models.ProfileDocument.objects.get(
                        id=document["id"]
                    )

                    process_documents = models.ProfileDocument.objects.filter(
                        profile=instance,
                        doc_type=document.get("doc_type"),
                        name_matching_text=document.get("name_matching_text"),
                    ).exclude(id=document_instance.id)

                    # If exists then skip
                    if process_documents.exists():
                        new_documents_ids.append(document_instance.id)
                        continue

                    for k, v in document.items():
                        setattr(document_instance, k, v)
                    document_instance.save()
                    new_documents_ids.append(document_instance.id)
            else:
                existing_document = models.ProfileDocument.objects.filter(
                    profile=instance,
                    doc_type=document.get("doc_type"),
                    name_matching_text=document.get("name_matching_text"),
                ).first()

                if existing_document:
                    new_documents_ids.append(existing_document.id)
                    continue

                document_instance = models.ProfileDocument.objects.create(
                    profile=instance, **document
                )
                new_documents_ids.append(document_instance.id)

        for doc_id in existing_profile_documents:
            if doc_id not in new_documents_ids:
                models.ProfileDocument.objects.filter(pk=doc_id).delete()

    def _handle_customers(self, profile, customers_data):
        # Get current ids to track what to keep, update, or delete
        current_ids = set(profile.customers.values_list("id", flat=True))
        keep_ids = set()

        # Create or update customers
        for customer_data in customers_data:
            customer_id = customer_data.get("id")

            if customer_id:
                # Update existing customer
                customer_qs = models.ProfileCustomer.objects.filter(
                    id=customer_id, profile=profile
                )

                if not customer_qs.exists():
                    continue

                keep_ids.add(customer_id)

                customer = customer_qs.first()
                for attr, value in customer_data.items():
                    if attr != "id":
                        setattr(customer, attr, value)
                customer.save()
            else:
                # Create new customer
                new_customer = models.ProfileCustomer.objects.create(
                    profile=profile, **customer_data
                )
                keep_ids.add(new_customer.id)

        # Delete customers not in the updated data
        delete_ids = current_ids - keep_ids
        profile.customers.filter(id__in=delete_ids).delete()

    def _handle_process_customers(self, profile, process_customers_data):
        # Get current ids to track what to keep, update, or delete
        current_ids = set(profile.process_customers.values_list("id", flat=True))
        keep_ids = set()

        # Create or update process customers
        for customer_data in process_customers_data:
            customer_id = customer_data.get("id")

            if customer_id:
                # Update existing process customer
                customer_qs = models.ProcessCustomer.objects.filter(
                    id=customer_id, profile=profile
                )

                if not customer_qs.exists():
                    continue

                keep_ids.add(customer_id)

                customer = customer_qs.first()
                for attr, value in customer_data.items():
                    if attr != "id":
                        setattr(customer, attr, value)
                customer.save()
            else:
                # Create new process customer
                new_customer = models.ProcessCustomer.objects.create(
                    profile=profile, **customer_data
                )
                keep_ids.add(new_customer.id)

        # Delete process customers not in the updated data
        delete_ids = current_ids - keep_ids
        profile.process_customers.filter(id__in=delete_ids).delete()


def update_template_profile_count(profile, template_list, create=False):
    """Count how many profile use the template"""
    documents = models.ProfileDocument.objects.filter(profile=profile)
    documents = [doc.template for doc in documents]
    new = [_ for _ in template_list if _ not in documents]  # add
    old = [_ for _ in documents if _ not in template_list]  # delete

    # for delete
    for template in old:
        if not template or template in new:
            continue
        instance = models.Template.objects.filter(template_name=template)
        if not instance.exists():
            continue
        instance = instance.first()
        linked_profiles = instance.linked_profiles
        if profile.name in linked_profiles:
            linked_profiles.remove(profile.name)
            instance.save()

    # for add
    for template in new:
        if not template or template in old:
            continue

        instance = models.Template.objects.filter(template_name=template)
        if not instance.exists():
            continue
        instance = instance.first()
        linked_profiles = instance.linked_profiles
        if profile.name not in linked_profiles:
            linked_profiles.append(profile.name)
            instance.save()


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = [
            "id",
            "project_id",
            "name",
            "updated_at",
        ]
        read_only_fields = ["id", "project_id", "updated_at"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = "__all__"
        read_only_fields = ["id", "project_id", "created_at", "updated_at"]

    def validate_settings(self, value):
        self._validate_options_keys(value)
        self._validate_meta_root_types(value)
        self._validate_key_qualifiers(value)
        self._validate_compound_keys(value)
        return value

    def find_duplicates(self, items, label):
        seen = set()
        duplicates = set()

        for item in items:
            value = item.get(label).lower() if item.get(label) else None
            if value in seen:
                if value is not None:
                    duplicates.add(value)
            else:
                seen.add(value)
        return list(duplicates)

    def find_duplicate_pairs(self, items, key, value, type_key):

        seen = set()
        duplicates = []
        for item in items:

            pair = (
                item.get(key).lower() if item.get(key) else None,
                item.get(value).lower() if item.get(value) else None,
                item.get(type_key).lower() if item.get(type_key) else None,
            )
            if pair in seen:
                cleaned_pair = tuple(entry for entry in pair if entry is not None)
                if cleaned_pair:
                    duplicates.append(cleaned_pair)
            else:
                seen.add(pair)
        return duplicates

    def find_duplicate_pairs_in_nested(self, items, parent_key, key, value, type_key):
        for item in items:
            dups = self.find_duplicate_pairs(item[parent_key], key, value, type_key)
            if dups:
                return dups
        return None
    
    # ---------------------------------------------
    # 1) Validate options-keys duplicates
    # ---------------------------------------------
    def _validate_options_keys(self, value):
        options = value.get("options", {}) or {}
        items = options.get("options-keys", {}).get("items", [])
        dups = self.find_duplicate_pairs(items, 'keyLabel', 'keyValue', 'type')
        if dups:
            raise serializers.ValidationError(
                 f"Importing aborted due to discovery of Duplicate Entry in keys: {dups}"
            )


    # ---------------------------------------------
    # 2) Validate meta-root-type duplicates
    # ---------------------------------------------
    def _validate_meta_root_types(self, value):
        options = value.get("options", {}) or {}
        items = options.get("options-meta-root-type", {}).get("items", [])
        dups = self.find_duplicate_pairs(items, 'docType', 'docCode', 'type')
        if dups:
            raise serializers.ValidationError(
                f"Importing aborted due to discovery of Duplicate Entry in docTypes: {dups}"
            )

    # ---------------------------------------------
    # 3) Validate keyQualifiers duplicates
    # ---------------------------------------------
    def _validate_key_qualifiers(self, value):
        key_qualifiers = value.get("keyQualifiers", [])
        
        dups = self.find_duplicates(key_qualifiers, 'name')
        if dups:
            raise serializers.ValidationError(
                f"Importing aborted due to discovery of Duplicate Entry in keyQualifiers: {dups}"
                )
        
        nested_dups = self.find_duplicate_pairs_in_nested(key_qualifiers, 'options', 'label', 'value', 'type')
        if nested_dups:
            raise serializers.ValidationError(
                f"Importing aborted due to discovery of Duplicate Entry in keyqualifiers: {nested_dups}"
            )
        
        if dups:
            raise serializers.ValidationError(
                f"Importing aborted due to discovery of Duplicate Entry in keyQualifiers: {dups}"
            )

    # ---------------------------------------------
    # 5) Validate compound keys
    # ---------------------------------------------
    def _validate_compound_keys(self, value):
        compound_keys = value.get("compoundKeys", [])
        dups = self.find_duplicates(compound_keys, 'name')
        if dups:
            raise serializers.ValidationError(
                    f"Duplicate entry found: {dups}"
                )
        nested_dups = self.find_duplicate_pairs_in_nested(compound_keys, 'keyItems', 'keyLabel', 'keyValue', 'type')
        if nested_dups:
            raise serializers.ValidationError(
                f"Importing aborted due to discovery of Duplicate Entry in compoundKeys: {nested_dups}"
            )


class DeveloperSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.DeveloperSettings
        fields = ["data"]


class YamlSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    replace_data = serializers.BooleanField(required=False, default=False)

    def validate_file(self, value):
        filename = value.name
        # if not filename.endswith((".yaml", ".yml")):
        #     raise serializers.ValidationError("Only .yaml or .yml files are allowed.")
        has_error = check_yaml_syntax(value)
        if has_error:
            raise serializers.ValidationError("Uploaded file is not valid YAML.")
        value.seek(0)  # Rewind again before reading content
        content = yaml.safe_load(value.read())
        value.seek(0)
        self._parsed_yaml = content
        return value

    def get_parsed_yaml(self):
        return getattr(self, "_parsed_yaml", None)


class YamlJsonParserSerializer(serializers.Serializer):
    """Serializer for parsing both YAML and JSON files and extracting keys."""
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        filename = value.name.lower()
        content = None

        if filename.endswith((".yaml", ".yml")):
            # Validate and parse YAML
            has_error = check_yaml_syntax(value)
            if has_error:
                raise serializers.ValidationError("Uploaded file is not valid YAML.")
            value.seek(0)
            content = yaml.safe_load(value.read())
        elif filename.endswith(".json"):
            # Parse JSON
            try:
                value.seek(0)
                content = json.load(value)
            except json.JSONDecodeError as e:
                raise serializers.ValidationError(f"Uploaded file is not valid JSON: {str(e)}")
        else:
            raise serializers.ValidationError("Only .yaml, .yml, or .json files are allowed.")

        value.seek(0)
        self._parsed_content = content
        self._file_type = "yaml" if filename.endswith((".yaml", ".yml")) else "json"
        return value

    def get_parsed_content(self):
        return getattr(self, "_parsed_content", None)

    def get_file_type(self):
        return getattr(self, "_file_type", None)


class OutputChannelSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(required=False, allow_blank=True)
    token = serializers.CharField(required=False, allow_blank=True)
    api_key_value = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(required=False, allow_blank=True)
    client_secret = serializers.CharField(required=False, allow_blank=True)

    ENCRYPTED_FIELDS = ["username", "password", "token", "api_key_value", "client_id", "client_secret"]

    class Meta:
        model = models.OutputChannel
        fields = [
            "id", "project", "is_active", "output_id", "output_type", "auth_type",
            "endpoint_url", "request_type", "username", "password", "token",
            "api_key_name", "api_key_value", "client_id", "client_secret", "token_url",
            "token_expires_at", "grant_type", "scope", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at"]

    def _clean_value(self, data, field):
        value = data.get(field)
        if value in [None, "null", "None"]:
            data[field] = ""

    def _process_encrypted_fields(self, data):
        for field in self.ENCRYPTED_FIELDS:
            self._clean_value(data, field)
            if field in data:
                # data[f"_{field}"] = encrypt_value(data.pop(field))
                data[f"_{field}"] = data.pop(field)

    def create(self, validated_data):
        self._process_encrypted_fields(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._process_encrypted_fields(validated_data)
        return super().update(instance, validated_data)
