"""
Organization: AIDocBuilder Inc.
File: dashboard/views.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature updates
    - Sunny - Feature updates

Last Updated By: Nayem
Last Updated At: 2024-11-30

Description:
    This file defines the application's features for managing profiles, projects, and templates.
    Profiles can be exported and imported to and from external system, cloned for duplication, and sent or received from remote system.
    Projects support export and import functionalities. Templates support the same functionalities as profiles.

Dependencies:
    - settings from django.conf
    - timezone from django.utils
    - receiver from django.dispatch
    - transaction from django.db
    - Q from django.db.models
    - post_save from django.db.models.signals
    - status, viewsets from rest_framework
    - action, api_view, permission_classes from rest_framework.decorators
    - Response from rest_framework.response
    - AllowAny from rest_framework.permissions
    - models, serializers from dashboard
    - DataExportConfig, DataImportConfig from settings.models
    - async_to_sync from asgiref.sync
    - get_channel_layer from channels.layers
    - DataCap from pipeline.scripts.DataCap
    - escape_xml_chars, create_inmemory_file from pipeline.views
    - PaginationMeta from core.pagination
    - Batch, Definition from core.models
    - Country, ApplicationSettings from core.models
    - CountrySerializer, DefinitionSerializer from core.serializers
    - write_timeline_log from utils.utils
    - DefaultDefinitions from utils.create_default_definitions

Main Features:
    - Operations for Profiles via ProfileViewSet
    - Clone Profile for duplication
    - Export and import Profiles to/from external system
    - Send and receive Profiles to/from remote system
    - Operations for Projects via ProjectViewSet
    - Export and import Projects to/from external system
    - Operations for Templates via TemplateViewSet
    - Clone Template for duplication
    - Export and import Templates to/from external system
    - Send and receive Templates to/from remote system

"""

import requests
import uuid
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from utils.change_logger import ChangeLogger
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.permissions import IsAdminUser

from core.pagination import PaginationMeta
from dashboard import models, serializers
from core.models import Country, ApplicationSettings
from core.serializers import CountrySerializer, DefinitionSerializer
from settings.models import DataExportConfig, DataImportConfig
import traceback
import re
import json
import os
import shutil
import pickle
from django.conf import settings
from django.utils import timezone

from django.dispatch import receiver
from asgiref.sync import async_to_sync
from pipeline.scripts.DataCap import DataCap
from channels.layers import get_channel_layer
from django.db.models.signals import post_save

from pipeline.utils.excel_utils import convert_xls_to_xlsx, validate_xls_file
from pipeline.utils.generate_layout_id_utils import (
    mask_variable_content,
    _get_embedding_from_db,
    _save_embedding_to_db,
    _get_model_version
)
import numpy as np
from core.models import Batch, Definition
from utils.utils import (
    write_timeline_log,
    clean_definition_settings,
    escape_xml_chars,
    create_inmemory_file,
    find_duplicate_pairs,
    find_duplicate_pairs_in_nested,
    find_duplicates,
    validate_options_keys,
    validate_meta_root_types,
    validate_key_qualifiers,
    validate_compound_keys
)
from utils.create_default_definitions import DefaultDefinitions
from dashboard.utils import yaml_utils

channel_layer = get_channel_layer()
BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
CLASSIFIER_API_URL = settings.CLASSIFIER_API_URL
QDRANT_VECTOR_DB_BASE_URL = os.getenv("QDRANT_VECTOR_DB_BASE_URL")



@api_view(["GET"])
def profile_fields_options(request):
    """Update profile fields options with country"""
    profile_fields_options = models.PROFILE_FIELDS_OPTIONS
    country_qs = Country.objects.all().order_by("name")
    profile_fields_options["country_code"] = CountrySerializer(
        country_qs, many=True
    ).data

    return Response(profile_fields_options)


class TemplateViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'Template' model, providing CRUD operations
    integrating with TemplateSerializer and TemplateListSerializer for data validation and response
    """

    lookup_value_regex = "[^/]+"
    queryset = models.Template.objects.all().order_by("id")
    list_serializer_class = serializers.TemplateListSerializer
    serializer_class = serializers.TemplateSerializer
    pagination_class = PaginationMeta
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        request.data["created_by"] = request.user.username
        # if definition is not given generate default definition
        if request.data.get("existing_profile_name") is None:
            default_definitions_class = DefaultDefinitions(
                ApplicationSettings=ApplicationSettings
            )
            definition = default_definitions_class.default_definition()
            request.data["definition"] = definition
        else:
            definition_id = request.data["existing_profile_name"]
            serial_no = request.data["existing_document"].split(" ")[-1]

            try:
                serial_no = int(serial_no)
                type = " ".join(request.data["existing_document"].split(" ")[:-1])
            except:
                serial_no = 1
                type = request.data["existing_document"]

            qs = (
                Definition.objects.filter(definition_id__iexact=definition_id)
                .filter(type__iexact=type)
                .order_by("created_at")
            )

            if qs.count() >= serial_no:
                qs = qs[serial_no - 1]

            definition = DefinitionSerializer(qs).data
            request.data["definition"] = definition["data"]

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Template created successfully."})

    def delete(self, request):
        ids_to_delete = request.data.get("ids", [])

        # If no ids are provided, return a bad request response
        if not ids_to_delete:
            return Response(
                {"detail": "Please provide ids to delete"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Filter objects by the provided ids
            queryset = self.queryset.filter(id__in=ids_to_delete)

            # Delete the filtered queryset
            queryset.delete()

            return Response({"detail": "Templates deleted successfully"})

        except Exception as e:
            return Response(
                {"detail": f"Failed to delete Templates. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action == "list":
            name = self.request.query_params.get("name", None)
            doc_type = self.request.query_params.get("doc_type", None)
            template_name = self.request.query_params.get("template_name", None)
            category = self.request.query_params.get("category", None)
            project = self.request.query_params.get("project", None)
            language = self.request.query_params.get("language", None)
            ocr_engine = self.request.query_params.get("ocr_engine", None)
            page_rotate = self.request.query_params.get("page_rotate", None)
            barcode = self.request.query_params.get("barcode", None)

            if name:
                queryset = queryset.filter(name__icontains=name)
            if doc_type:
                queryset = queryset.filter(doc_type__icontains=doc_type)
            if template_name:
                queryset = queryset.filter(template_name__icontains=template_name)
            if category:
                queryset = queryset.filter(category__icontains=category)
            if project:
                queryset = queryset.filter(project__icontains=project)
            if ocr_engine:
                queryset = queryset.filter(ocr_engine__icontains=ocr_engine)
            if page_rotate:
                queryset = queryset.filter(page_rotate__icontains=page_rotate)
            if barcode:
                queryset = queryset.filter(barcode__icontains=barcode)
            if language:
                queryset = queryset.filter(language__icontains=language)

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(TemplateViewSet, self).get_serializer_class()


class ProfileViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'Profile' model, providing CRUD operations
    integrating with the ProfileSerializer and ProfileListSerializer for data validation and response
    """

    lookup_value_regex = "[^/]+"
    queryset = models.Profile.objects.all().order_by("id")
    list_serializer_class = serializers.ProfileListSerializer
    serializer_class = serializers.ProfileSerializer
    pagination_class = PaginationMeta

    def destroy(self, request, *args, **kwargs):
        profile_instance = self.get_object()
        profile_name = profile_instance.name
        profile_instance.delete()

        # Delete profile associate vendors
        Definition.objects.filter(definition_id=profile_name).delete()

        return Response(
            {"detail": f"Profile deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_name = old_instance.name
        old_process_id = old_instance.process_id
        old_data = serializers.ProfileSerializer(old_instance).data
        new_instance = serializer.save()
        new_data = serializers.ProfileSerializer(new_instance).data
        ChangeLogger.log_model_changes(
            new_instance, old_instance, new_data, old_data, self.request.user
        )
        if new_instance.process_uid and (
            old_name != new_instance.name or old_process_id != new_instance.process_id
        ):
            update_process_metadata_in_qdrant(
                new_instance.process_uid,
                new_instance.process_id,
                new_instance.name,
            )

    def get_next_sequence(
        self, country=None, project_name=None, *, use_select_for_update=False
    ):
        """
        Core logic to get the next sequence number for a given country and project.
        Returns a dictionary with sequence data or raises an exception.
        """
        if not country or not project_name:
            raise ValueError("Both country and project_name parameters are required")

        # Get the project instance
        try:
            project = models.Project.objects.get(name=project_name)
            project_id = project.project_id
        except models.Project.DoesNotExist:
            raise ValueError(f'Project "{project_name}" not found')

        # Create the country-project prefix
        country_project_prefix = f"{country.upper()}-{project_id}"

        # Find the highest existing sequence number for this prefix
        existing_profiles = models.Profile.objects.filter(
            process_id__startswith=country_project_prefix
        ).exclude(process_id="")
        # if use_select_for_update:
        #     existing_profiles = existing_profiles.select_for_update()

        if existing_profiles.exists():
            max_number = 0
            for profile in existing_profiles:
                if profile.process_id:
                    parts = profile.process_id.split("-")
                    if len(parts) >= 3:
                        try:
                            number = int(parts[-1])
                            max_number = max(max_number, number)
                        except ValueError:
                            continue
            next_number = max_number + 1
        else:
            next_number = 1

        next_process_id = f"{country_project_prefix}-{next_number:07d}"

        return {
            "country": country.upper(),
            "project_name": project_name,
            "project_id": project_id,
            "next_sequence": next_number,
            "next_process_id": next_process_id,
            "prefix": country_project_prefix,
        }

    @action(detail=False, methods=["get"], url_path="get_process_prompt_keys")
    def get_process_prompt_keys(self, request):
        process_name = request.query_params.get("process_name")

        if not process_name:
            return Response(
                {"success": False, "error": "process_name required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = self.get_queryset().get(name=process_name)
            process_keys = profile.keys or []
            process_keys = [i for i in process_keys if i.get("prompt", {})]
            return Response(process_keys, status=status.HTTP_200_OK)
        except models.Profile.DoesNotExist:
            return Response(
                {"success": False, "error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["patch"], url_path="update_process_prompt_keys")
    def update_process_prompt_keys(self, request):
        process_name = request.data.get("process_name")
        keys = request.data.get("keys")

        # Validate required fields
        if not process_name:
            return Response(
                {"success": False, "error": "process_name required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if keys is None:
            return Response(
                {"success": False, "error": "keys field required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate keys is a list
        if not isinstance(keys, list):
            return Response(
                {"success": False, "error": "keys must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for duplicates
        seen_keys = {}
        duplicates = []

        for idx, item in enumerate(keys):
            if not isinstance(item, dict):
                return Response(
                    {
                        "success": False,
                        "error": f"Item at index {idx} is not a dictionary",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            key_value = item.get("keyValue")

            if key_value is None or (
                isinstance(key_value, str) and not key_value.strip()
            ):
                return Response(
                    {
                        "success": False,
                        "error": f"Item at index {idx} has missing or empty keyValue",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Normalize for comparison (strip whitespace)
            if isinstance(key_value, str):
                key_value = key_value.strip()

            if key_value in seen_keys:
                duplicates.append(
                    {"key_value": key_value, "indices": [seen_keys[key_value], idx]}
                )
            else:
                seen_keys[key_value] = idx

        # If duplicates found, return error with details
        if duplicates:
            return Response(
                {
                    "success": False,
                    "error": "Duplicate keys found",
                    "duplicates": duplicates,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = self.get_queryset().get(name=process_name)

            # Get existing keys
            existing_keys = profile.keys or []
            if not isinstance(existing_keys, list):
                existing_keys = []

            # Create a mapping of incoming updates by key identifier
            updates_map = {
                item.get("keyValue"): item.get("prompt")
                for item in keys
                if item.get("keyValue") is not None
            }

            # Update prompts for matching keys
            updated_count = 0
            for existing_item in existing_keys:
                if not isinstance(existing_item, dict):
                    continue

                key_value = existing_item.get("keyValue")
                if not key_value:
                    continue

                if key_value in updates_map:
                    existing_item["prompt"] = updates_map[key_value]
                    updated_count += 1
                else:
                    existing_item["prompt"] = {}

            # Save updated keys
            profile.keys = existing_keys
            profile.save()

            return Response(
                {
                    "success": True,
                    "message": f"Keys updated successfully. {updated_count} prompt key(s) updated.",
                    "updated_count": updated_count,
                },
                status=status.HTTP_200_OK,
            )
        except models.Profile.DoesNotExist:
            return Response(
                {"success": False, "error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"], url_path="next_sequence")
    def next_sequence(self, request):
        """
        Get the next sequence number for a given country and project.
        URL: GET /api/dashboard/profiles/next_sequence/?countryCode=AF&project=ProjectName
        """
        country = request.query_params.get("country")
        project_name = request.query_params.get("project")

        try:
            result = self.get_next_sequence(country=country, project_name=project_name)
            return Response({"success": True, **result}, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle validation errors (missing params, project not found)
            if "not found" in str(e):
                return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="create_with_process_id")
    def create_with_process_id(self, request):
        """
        Create a new profile. Auto-generates process_id if not provided.
        URL: POST /api/dashboard/profiles/create_with_process_id/

        If process_id is provided, tries to use it.
        If not provided or conflicts, generates a new one.
        """
        country = request.data.get("country")
        project_name = request.data.get("project")
        provided_process_id = request.data.get("process_id")

        if not country or not project_name:
            return Response(
                {"error": "Both country and project_name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                try:
                    project = models.Project.objects.get(name=project_name)
                    project_id = project.project_id
                except models.Project.DoesNotExist:
                    return Response(
                        {"error": f'Project "{project_name}" not found'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                country_project_prefix = f"{country.upper()}-{project_id}"
                final_process_id = None
                process_id_changed = False

                # If process_id was provided (from GUI preview), try to use it
                if provided_process_id:
                    # Check if it's still available
                    if not models.Profile.objects.filter(
                        process_id=provided_process_id
                    ).exists():
                        final_process_id = provided_process_id
                    else:
                        process_id_changed = True

                # If no process_id provided or it's taken, generate new one
                if not final_process_id:
                    existing_profiles = (
                        self.get_queryset()
                        .filter(process_id__startswith=country_project_prefix)
                        .exclude(process_id="")
                        .select_for_update()
                    )

                    if existing_profiles.exists():
                        max_number = 0
                        for profile in existing_profiles:
                            if profile.process_id:
                                parts = profile.process_id.split("-")
                                if len(parts) >= 3:
                                    try:
                                        number = int(parts[-1])
                                        max_number = max(max_number, number)
                                    except ValueError:
                                        continue
                        next_number = max_number + 1
                    else:
                        next_number = 1

                    final_process_id = f"{country_project_prefix}-{next_number:07d}"

                # Prepare data for serializer
                profile_data = request.data.copy()
                profile_data["process_id"] = final_process_id
                profile_data["country"] = country.upper()
                profile_data["project"] = project_name

                # Use serializer for validation and creation
                serializer = self.get_serializer(data=profile_data)
                serializer.is_valid(raise_exception=True)
                profile = serializer.save()

                response_data = {
                    "success": True,
                    "profile": serializer.data,
                    "final_process_id": final_process_id,
                }

                # Inform client if process_id changed from what they expected
                if process_id_changed:
                    response_data["process_id_changed"] = True
                    response_data["original_process_id"] = provided_process_id
                    response_data["message"] = (
                        "The process_id you expected was taken, assigned a new one."
                    )

                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], name="List with POST")
    def filter_list(self, request, *args, **kwargs):
        """
        Handle list retrieval with POST request. This utilizes the overridden
        'get_queryset' method for filtering based on POST data.
        """
        queryset = self.filter_queryset(self.get_queryset())

        paginate = request.query_params.get("paginate", "true").lower()
        if paginate == "false":
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="import")
    def import_profiles(self, request):
        """
        Bulk import profiles from JSON.
        POST /api/dashboard/profiles/import/
        """
        try:
            try:
                profiles_data = request.data["profiles"]
                ignore_fields = request.data.get("ignore_fields", False)
                if ignore_fields != bool and ignore_fields == "true":
                    ignore_fields = True
                elif ignore_fields != bool and ignore_fields == "false":
                    ignore_fields = False
            except:
                return Response(
                    {"detail": "profiles field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            import_profiles_handler(profiles_data, ignore_fields=ignore_fields)

            return Response({"detail": "Profiles imported"})

        except Exception as error:
            print(traceback.format_exc())
            return Response(
                {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="export")
    def export_profiles(self, request):
        """
        Bulk export all profiles or filtered projects.
        POST /api/dashboard/profiles/export/
        """
        try:
            try:
                ids = request.data.get("ids")
                export_all = request.data.get("export_all", False)
                if ids is None and export_all is False:
                    raise ValueError(
                        "Missing fields, endpoint requires 'ids' or 'export_all'."
                    )
            except ValueError as err:
                return Response(
                    {"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST
                )

            profiles_data = get_profiles_data_by_ids(ids, export_all)
            return Response(profiles_data)

        except Exception as error:
            return Response(
                {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="migrate-process-uid-to-qdrant")
    @permission_classes([IsAdminUser])
    def migrate_process_uid_to_qdrant(self, request):
        """
        Push profiles to Qdrant to trigger process_uid migration.
        POST /api/dashboard/profiles/migrate-process-uid-to-qdrant/
        """
        if not QDRANT_VECTOR_DB_BASE_URL:
            return Response(
                {"detail": "QDRANT_VECTOR_DB_BASE_URL is not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ids = request.data.get("ids")
        export_all = _parse_bool(request.data.get("export_all", False))
        if ids is None and not export_all:
            return Response(
                {"detail": "Missing fields, endpoint requires 'ids' or 'export_all'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if export_all:
            profile_query = models.Profile.objects.all()
        else:
            profile_query = models.Profile.objects.filter(id__in=ids)

        if not profile_query.exists():
            return Response(
                {"detail": "No profiles found for migration."},
                status=status.HTTP_404_NOT_FOUND,
            )

        profiles_payload = []
        for profile in profile_query.only("process_uid", "name", "free_name", "process_id"):
            profiles_payload.append(
                {
                    "process_uid": str(profile.process_uid),
                    "name": profile.name,
                    "free_name": profile.free_name,
                    "process_id": profile.process_id,
                }
            )

        dry_run = _parse_bool(request.data.get("dry_run", False))
        delete_legacy = _parse_bool(request.data.get("delete_legacy", True))
        overwrite_existing = _parse_bool(request.data.get("overwrite_existing", False))

        batch_size_raw = request.data.get("batch_size", 200)
        try:
            batch_size = int(batch_size_raw)
        except (TypeError, ValueError):
            return Response(
                {"detail": "batch_size must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if batch_size < 1:
            return Response(
                {"detail": "batch_size must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        databases = request.data.get("databases")
        if isinstance(databases, str):
            databases = [db.strip() for db in databases.split(",") if db.strip()]
        if databases is not None and not isinstance(databases, list):
            return Response(
                {"detail": "databases must be a list or comma-separated string."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = push_process_uid_migration_to_qdrant(
            profiles_payload,
            databases=databases,
            dry_run=dry_run,
            delete_legacy=delete_legacy,
            overwrite_existing=overwrite_existing,
            batch_size=batch_size,
        )

        status_code = (
            status.HTTP_200_OK
            if summary.get("success")
            else status.HTTP_502_BAD_GATEWAY
        )
        return Response(summary, status=status_code)

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action == "list" or self.action == "filter_list":
            name = self.request.query_params.get("name", None)
            country = self.request.query_params.get("country", None)
            free_name = self.request.query_params.get("free_name", None)
            email_subject_match_text = self.request.query_params.get(
                "email_subject_match_text", None
            )
            # mode_of_transport = self.request.query_params.get("mode_of_transport", None)
            project = self.request.query_params.get("project", None)
            process_id = self.request.query_params.get("process_id", None)

            if self.action == "list":
                project_countries = self.request.query_params.get(
                    "project_countries", None
                )
            elif self.action == "filter_list":
                project_countries = self.request.data.get("project_countries", None)

            if process_id:
                queryset = queryset.filter(process_id__icontains=process_id)
            if name:
                queryset = queryset.filter(name__icontains=name)
            if country:
                queryset = queryset.filter(country__icontains=country)
            if free_name:
                queryset = queryset.filter(free_name__icontains=free_name)
            if email_subject_match_text:
                queryset = queryset.filter(
                    email_subject_match_text__icontains=email_subject_match_text
                )
            # if mode_of_transport:
            #     queryset = queryset.filter(
            #         mode_of_transport__icontains=mode_of_transport
            #     )
            if project:
                queryset = queryset.filter(project__icontains=project)

            if project_countries:
                query = Q()
                for country_code, project_list in project_countries.items():
                    if not project_list:
                        continue

                    project_query = Q()
                    for project in project_list:
                        project_query |= Q(name__icontains=project)
                    query |= project_query & Q(name__startswith=country_code)
                if query:
                    queryset = queryset.filter(query)
                else:
                    queryset = queryset.none()

            # if not project_countries:
            #     queryset = queryset.model.objects.none()

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    @action(detail=True, methods=["post"], url_path="import_documents")
    def import_documents(self, request, pk=None):
        """
        Import profile documents from Excel file (.xlsx or .xls).
        Validates data and replaces existing documents.
        Validation rules match the frontend form exactly.
        """
        import openpyxl
        import io

        profile = self.get_object()

        if 'file' not in request.FILES:
            return Response(
                {"detail": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name.lower()

        # Check file type
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            return Response(
                {"detail": "Invalid file format. Please upload an Excel file (.xlsx or .xls)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Handle Excel files
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
            worksheet = workbook.active

            # Get header row
            headers = []
            for cell in worksheet[1]:
                if cell.value:
                    # Normalize header names
                    header = str(cell.value).strip().lower().replace(' ', '')
                    headers.append(header)

            # Parse data rows
            rows = []
            for row in worksheet.iter_rows(min_row=2, values_only=True):
                if any(cell for cell in row):  # Skip empty rows
                    row_dict = {}
                    for idx, value in enumerate(row):
                        if idx < len(headers):
                            row_dict[headers[idx]] = value
                    rows.append(row_dict)

            # Validate required columns
            if not rows:
                return Response(
                    {"detail": "No data found in file"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Normalize keys for the first row to check required fields
            first_row_keys = set(key.lower().replace(' ', '') for key in rows[0].keys())

            # Define all expected columns in the Excel template
            # These columns must be present in the header even if values can be empty
            expected_columns = {
                'doctype': 'Doc Type',
                'contentlocation': 'Content Location',
                'category': 'Category',
                'namematchingoption': 'Name Matching Option',
                'namematchingtext': 'Name Matching Text',
                'language': 'Language',
                'ocrengine': 'OCR Engine',
                'template': 'Template',
                'translateddoctype': 'Translated Doc Type',
                'pagerotate': 'Page Rotate',
                'barcode': 'Barcode',
                'showembeddedimg': 'Show Embedded Img'
            }

            # Check for missing columns
            missing_columns = set(expected_columns.keys()) - first_row_keys
            if missing_columns:
                missing_display = [expected_columns[col] for col in sorted(missing_columns)]
                return Response(
                    {"detail": f"Missing required column(s) in Excel header: {', '.join(missing_display)}. Please use the correct template with all column headers."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get valid document types for the profile's project
            valid_doc_types = []
            try:
                project = models.Project.objects.get(name=profile.project)
                project_settings = project.settings.get('options', {}).get('options-meta-root-type', {})
                valid_doc_types = [item.get('docType') for item in project_settings.get('items', [])]
            except models.Project.DoesNotExist:
                # If project doesn't exist, skip project-based doc type validation
                pass

            # Validate and parse documents
            parsed_documents = []
            validation_errors = []
            # Track unique combinations for duplicate detection
            seen_combinations = set()
            # Track profile-level validations
            profile_documents_dict = {}
            # Track translation mappings to prevent circular/chained translations
            translation_sources = {}  # {doc_type: row_number}
            translation_targets = {}  # {translated_doc_type: row_number}

            # First pass: collect all doc_types from the import list
            import_doc_types = set()
            for row in rows:
                normalized_row = {k.lower().replace(' ', ''): v for k, v in row.items()}
                doc_type = normalized_row.get('doctype', '').strip() if normalized_row.get('doctype') else ''
                if doc_type:
                    import_doc_types.add(doc_type)

            for idx, row in enumerate(rows, start=2):  # Start from 2 (header is row 1)
                # Normalize row keys
                normalized_row = {k.lower().replace(' ', ''): v for k, v in row.items()}

                doc_type = normalized_row.get('doctype', '').strip() if normalized_row.get('doctype') else ''
                content_location = normalized_row.get('contentlocation', '').strip() if normalized_row.get('contentlocation') else ''
                category = normalized_row.get('category', '').strip() if normalized_row.get('category') else ''

                # Validate required fields
                missing_fields = []
                if not doc_type:
                    missing_fields.append('Doc Type')
                if not content_location:
                    missing_fields.append('Content Location')
                if not category:
                    missing_fields.append('Category')

                if missing_fields:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Missing required field(s): {', '.join(missing_fields)}"
                    })
                    continue

                # Validate content_location
                valid_content_locations = [choice[0] for choice in models.ProfileDocument.CONTENT_LOCATION_OPTIONS]
                if content_location not in valid_content_locations:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Invalid Content Location '{content_location}'. Must be one of: {', '.join(valid_content_locations)}"
                    })
                    continue

                # Block Additional Document content location (no longer supported)
                if content_location == 'Additional Document':
                    validation_errors.append({
                        'row': idx,
                        'message': "'Additional Document' content location is no longer supported. Please use 'Email Attachment' or 'Email Body'."
                    })
                    continue

                # Validate category
                valid_categories = [choice[0] for choice in models.ProfileDocument.CATEGORY_OPTIONS]
                if category not in valid_categories:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Invalid Category '{category}'. Must be one of: {', '.join(valid_categories)}"
                    })
                    continue

                # Validate category based on content_location
                if content_location in ['Email Attachment', 'Email Body'] and category == 'Ignoring':
                    validation_errors.append({
                        'row': idx,
                        'message': f"Category 'Ignoring' is not allowed for {content_location}. Only 'Processing' or 'Supporting' categories are allowed."
                    })
                    continue

                # Parse optional fields
                template = normalized_row.get('template', '').strip() if normalized_row.get('template') else None
                name_matching_option = normalized_row.get('namematchingoption', '').strip() if normalized_row.get('namematchingoption') else ''
                name_matching_text = (normalized_row.get('namematchingtext') or '').strip()
                language = normalized_row.get('language', '').strip() if normalized_row.get('language') else ''
                ocr_engine = normalized_row.get('ocrengine', '').strip() if normalized_row.get('ocrengine') else ''

                # Validate Name Matching fields are not allowed for Email Body
                if content_location == 'Email Body':
                    if name_matching_option:
                        validation_errors.append({
                            'row': idx,
                            'message': "Name Matching Option is not allowed for Email Body"
                        })
                        continue
                    if name_matching_text:
                        validation_errors.append({
                            'row': idx,
                            'message': "Name Matching Text is not allowed for Email Body"
                        })
                        continue

                # Parse boolean fields with defaults
                page_rotate_value = normalized_row.get('pagerotate', '')
                page_rotate = self._parse_boolean(page_rotate_value) if page_rotate_value else False

                barcode_value = normalized_row.get('barcode', '')
                barcode = self._parse_boolean(barcode_value) if barcode_value else False

                show_embedded_img_value = normalized_row.get('showembeddedimg', '')
                show_embedded_img = self._parse_boolean(show_embedded_img_value) if show_embedded_img_value else False

                # Parse translated doc type
                translated_doc_type = normalized_row.get('translateddoctype', '').strip() if normalized_row.get('translateddoctype') else ''

                # Validate translated_doc_type if provided
                if translated_doc_type:
                    # Validate that translated_doc_type is not the same as doc_type
                    if translated_doc_type.lower() == doc_type.lower():
                        validation_errors.append({
                            'row': idx,
                            'message': f"Translated Doc Type cannot be the same as Doc Type '{doc_type}'"
                        })
                        continue

                    # Validate that translated_doc_type exists in the import list
                    if translated_doc_type not in import_doc_types:
                        validation_errors.append({
                            'row': idx,
                            'message': f"Translated Doc Type '{translated_doc_type}' must exist as a Doc Type in the import list."
                        })
                        continue

                    # Validate that a doc_type being used as translation source is not already a translation target
                    doc_type_lower = doc_type.lower()
                    if doc_type_lower in translation_targets:
                        validation_errors.append({
                            'row': idx,
                            'message': f"Doc Type '{doc_type}' cannot be translated because it is already used as a Translated Doc Type in row {translation_targets[doc_type_lower]}"
                        })
                        continue

                    # Validate that a translated_doc_type is not already being used as a translation source
                    translated_doc_type_lower = translated_doc_type.lower()
                    if translated_doc_type_lower in translation_sources:
                        validation_errors.append({
                            'row': idx,
                            'message': f"Translated Doc Type '{translated_doc_type}' cannot be used because '{translated_doc_type}' is already a source Doc Type with translation in row {translation_sources[translated_doc_type_lower]}"
                        })
                        continue

                    # Track this translation mapping
                    translation_sources[doc_type_lower] = idx
                    translation_targets[translated_doc_type_lower] = idx

                # Validate name_matching_option is required for Email Attachment
                if content_location == 'Email Attachment':
                    if not name_matching_option or name_matching_option == 'None':
                        validation_errors.append({
                            'row': idx,
                            'message': "Name Matching Option is required for Email Attachment. Please use 'Auto', 'StartsWith', 'EndsWith', 'Contains', or 'Regex'."
                        })
                        continue

                # Validate name_matching_option if provided
                if name_matching_option and name_matching_option != 'None':
                    valid_name_matching_options = [choice[0] for choice in models.ProfileDocument.NAME_MATCH_OPTIONS]
                    if name_matching_option not in valid_name_matching_options:
                        validation_errors.append({
                            'row': idx,
                            'message': f"Invalid Name Matching Option '{name_matching_option}'. Must be one of: {', '.join(valid_name_matching_options)}"
                        })
                        continue

                # Conditional validation: name_matching_text should NOT be provided when option is 'Auto'
                if name_matching_option == 'Auto' and name_matching_text:
                    validation_errors.append({
                        'row': idx,
                        'message': "Name Matching Text is not allowed when Name Matching Option is 'Auto'"
                    })
                    continue

                # Conditional validation: name_matching_text is required if name_matching_option is NOT 'Auto'
                if content_location == 'Email Attachment' and name_matching_option and name_matching_option != 'Auto' and not name_matching_text:
                    validation_errors.append({
                        'row': idx,
                        'message': 'Name Matching Text is required when Name Matching Option is not Auto'
                    })
                    continue

                # Validate language is required for all documents
                if not language:
                    validation_errors.append({
                        'row': idx,
                        'message': 'Language is required'
                    })
                    continue

                # Validate language value
                valid_languages = [choice[0] for choice in models.ProfileDocument.LANGUAGE_OPTIONS]
                if language not in valid_languages:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Invalid Language '{language}'. Must be one of: {', '.join(valid_languages)}"
                    })
                    continue

                # Validate OCR Engine is required for all documents
                if not ocr_engine:
                    validation_errors.append({
                        'row': idx,
                        'message': 'OCR Engine is required'
                    })
                    continue

                # Validate ocr_engine value
                valid_ocr_engines = [choice[0] for choice in models.ProfileDocument.OCR_CHOICES]
                if ocr_engine not in valid_ocr_engines:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Invalid OCR Engine '{ocr_engine}'. Must be one of: {', '.join(valid_ocr_engines)}"
                    })
                    continue

                # Validate template if provided
                if template:
                    template_exists = models.Template.objects.filter(template_name=template).exists()
                    if not template_exists:
                        validation_errors.append({
                            'row': idx,
                            'message': f"Template '{template}' does not exist in the system"
                        })
                        continue

                # Validate doc_type against project settings
                if valid_doc_types and doc_type not in valid_doc_types:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Document Type '{doc_type}' is not valid for project '{profile.project}'."
                    })
                    continue

                # Check for duplicate combinations within the file
                # The unique constraint is on: profile + doc_type (lower) + name_matching_text (lower)
                unique_key = (doc_type.lower(), name_matching_text.lower())
                if unique_key in seen_combinations:
                    validation_errors.append({
                        'row': idx,
                        'message': f"Duplicate combination: Doc Type '{doc_type}' with Name Matching Text '{name_matching_text}' already exists in this file"
                    })
                    continue
                seen_combinations.add(unique_key)

                # PROFILE-LEVEL VALIDATIONS (matching ProfileSerializer)

                # Validate one Email Body Document per profile
                if content_location == 'Email Body':
                    if profile_documents_dict.get('Email Body'):
                        validation_errors.append({
                            'row': idx,
                            'message': "Only one 'Email Body' document is allowed per profile."
                        })
                        continue
                    profile_documents_dict['Email Body'] = True

                # Validate Auto name_matching_option for same doc type
                if profile_documents_dict.get(f'doctype_{doc_type}'):
                    # Check if current row is Auto and Auto already exists for this doc_type
                    if name_matching_option == 'Auto' and 'Auto' in profile_documents_dict[f'doctype_{doc_type}']:
                        validation_errors.append({
                            'row': idx,
                            'message': "'Auto' name matching option cannot be repeated for the same Document Type."
                        })
                        continue
                    # Only append after validation passes
                    profile_documents_dict[f'doctype_{doc_type}'].append(name_matching_option)
                else:
                    profile_documents_dict[f'doctype_{doc_type}'] = [name_matching_option]

                # Validate unique name_matching_text (case-insensitive)
                if name_matching_text:
                    name_matching_text_key = name_matching_text.lower()
                else:
                    name_matching_text_key = name_matching_text  # None or empty string

                if profile_documents_dict.get(name_matching_text_key):
                    validation_errors.append({
                        'row': idx,
                        'message': "Name matching texts should be unique per profile."
                    })
                    continue
                profile_documents_dict[name_matching_text_key] = name_matching_text_key

                # Validate supporting documents are not allowed in multi shipment profile
                if category == 'Supporting' and profile.multi_shipment:
                    validation_errors.append({
                        'row': idx,
                        'message': "Supporting documents are not allowed in multi shipment profile."
                    })
                    continue

                parsed_documents.append({
                    'doc_type': doc_type,
                    'content_location': content_location,
                    'template': template,
                    'name_matching_option': name_matching_option,
                    'name_matching_text': name_matching_text,
                    'category': category,
                    'language': language,
                    'ocr_engine': ocr_engine,
                    'page_rotate': page_rotate,
                    'barcode': barcode,
                    'show_embedded_img': show_embedded_img,
                    'translated_doc_type': translated_doc_type,  # Store for later processing
                })

            # Return validation errors if any
            if validation_errors:
                return Response(
                    {
                        "detail": "Validation errors found",
                        "validation_errors": validation_errors,
                        "valid_count": len(parsed_documents),
                        "error_count": len(validation_errors)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # If validation passed, import the documents
            with transaction.atomic():
                # Delete existing documents
                models.ProfileDocument.objects.filter(profile=profile).delete()

                # Collect translated doc type mappings
                translated_documents = []
                for doc_data in parsed_documents:
                    translated_doc_type = doc_data.get('translated_doc_type', '').strip()
                    if translated_doc_type:
                        # Add to translated_documents mapping
                        translated_documents.append({
                            'doc_type': doc_data['doc_type'],
                            'translated_doc_type': translated_doc_type
                        })

                # Replace profile's translated_documents field (just like we replace documents)
                # This ensures imported data completely replaces existing translations
                profile.translated_documents = translated_documents
                profile.save(update_fields=['translated_documents'])

                # Create new documents (remove translated_doc_type as it's not a model field)
                for doc_data in parsed_documents:
                    # Remove translated_doc_type before creating document
                    doc_data_copy = {k: v for k, v in doc_data.items() if k != 'translated_doc_type'}
                    models.ProfileDocument.objects.create(
                        profile=profile,
                        **doc_data_copy
                    )

            return Response(
                {
                    "detail": f"Successfully imported {len(parsed_documents)} document(s)",
                    "imported_count": len(parsed_documents)
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"detail": f"Error processing file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_boolean(self, value):
        """Helper method to parse boolean values from Excel/CSV"""
        if value is None or value == '':
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value == 1
        str_value = str(value).lower().strip()
        return str_value in ['true', '1', 'yes', 'y']

    def get_serializer_class(self):
        if self.action == "list" or self.action == "filter_list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(ProfileViewSet, self).get_serializer_class()


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    str_value = str(value).lower().strip()
    return str_value in ["true", "1", "yes", "y"]


def _chunk_list(items, size):
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def push_process_uid_migration_to_qdrant(
    profiles,
    *,
    databases=None,
    dry_run=False,
    delete_legacy=True,
    overwrite_existing=False,
    batch_size=200,
):
    if not QDRANT_VECTOR_DB_BASE_URL:
        return {
            "success": False,
            "detail": "QDRANT_VECTOR_DB_BASE_URL is not configured.",
        }

    if batch_size < 1:
        return {
            "success": False,
            "detail": "batch_size must be a positive integer.",
        }

    url = f"{QDRANT_VECTOR_DB_BASE_URL}/migrations/process-uid/from-profiles"

    summary = {
        "success": True,
        "batch_size": batch_size,
        "batches_total": 0,
        "batches_completed": 0,
        "profiles_sent": len(profiles),
        "dry_run": dry_run,
        "delete_legacy": delete_legacy,
        "databases": databases,
        "profiles_total": 0,
        "profiles_skipped": 0,
        "process_metadata_created": 0,
        "process_metadata_updated": 0,
        "tables_migrated": 0,
        "table_points_migrated": 0,
        "tables_skipped_existing": 0,
        "process_data_collections_migrated": 0,
        "process_data_points_migrated": 0,
        "process_data_skipped_existing": 0,
        "legacy_collections_deleted": 0,
        "legacy_metadata_deleted": 0,
        "warnings": [],
        "errors": [],
    }

    sum_fields = {
        "profiles_total",
        "profiles_skipped",
        "process_metadata_created",
        "process_metadata_updated",
        "tables_migrated",
        "table_points_migrated",
        "tables_skipped_existing",
        "process_data_collections_migrated",
        "process_data_points_migrated",
        "process_data_skipped_existing",
        "legacy_collections_deleted",
        "legacy_metadata_deleted",
    }

    batches = list(_chunk_list(profiles, batch_size))
    summary["batches_total"] = len(batches)

    for batch_index, batch in enumerate(batches, start=1):
        payload = {
            "profiles": batch,
            "dry_run": dry_run,
            "delete_legacy": delete_legacy,
            "overwrite_existing": overwrite_existing,
        }
        if databases:
            payload["databases"] = databases

        try:
            response = requests.post(url, json=payload, timeout=300)
        except requests.exceptions.Timeout:
            summary["success"] = False
            summary["errors"].append(
                f"Timeout while calling Qdrant migration endpoint (batch {batch_index}/{summary['batches_total']})."
            )
            continue
        except Exception as exc:
            summary["success"] = False
            summary["errors"].append(
                f"Error calling Qdrant migration endpoint (batch {batch_index}/{summary['batches_total']}): {str(exc)}"
            )
            continue

        if response.status_code not in (200, 201):
            summary["success"] = False
            summary["errors"].append(
                "Qdrant migration failed "
                f"(batch {batch_index}/{summary['batches_total']}): "
                f"Status {response.status_code}, Response: {response.text}"
            )
            continue

        try:
            batch_summary = response.json()
        except ValueError:
            summary["success"] = False
            summary["errors"].append(
                f"Invalid JSON response from Qdrant (batch {batch_index}/{summary['batches_total']})."
            )
            continue

        for field in sum_fields:
            summary[field] += int(batch_summary.get(field, 0))
        summary["warnings"].extend(batch_summary.get("warnings", []))
        summary["errors"].extend(batch_summary.get("errors", []))
        summary["batches_completed"] += 1

    if summary["errors"]:
        summary["success"] = False

    return summary


def get_parties_and_dictionaries_from_qdrant(process_uid):
    """Export parties and dictionaries data from Qdrant for a process"""
    if not QDRANT_VECTOR_DB_BASE_URL:
        print(f"Warning: QDRANT_VECTOR_DB_BASE_URL is not configured. Skipping parties and dictionaries export for {process_uid}")
        return None
    
    try:
        url = f"{QDRANT_VECTOR_DB_BASE_URL}/combined/processes/{process_uid}/export-json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            print(f"No parties and dictionaries found for process: {process_uid}")
            return None
        else:
            print(f"Failed to export parties and dictionaries for {process_uid}. Status: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout while exporting parties and dictionaries for {process_uid}")
        return None
    except Exception as e:
        print(f"Error exporting parties and dictionaries for {process_uid}: {str(e)}")
        return None


def import_parties_and_dictionaries_to_qdrant(process_uid, parties_and_dictionaries_data):
    """Import parties and dictionaries data to Qdrant for a process"""
    if not QDRANT_VECTOR_DB_BASE_URL:
        print(f"Warning: QDRANT_VECTOR_DB_BASE_URL is not configured. Skipping parties and dictionaries import for {process_uid}")
        return False
    
    if not parties_and_dictionaries_data:
        print(f"No parties and dictionaries data to import for {process_uid}")
        return False
    
    try:
        url = f"{QDRANT_VECTOR_DB_BASE_URL}/combined/processes/{process_uid}/import-json"
        response = requests.post(url, json=parties_and_dictionaries_data, timeout=60)
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"Successfully imported parties and dictionaries for {process_uid}")
            return True
        else:
            print(f"Failed to import parties and dictionaries for {process_uid}. Status: {response.status_code}, Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"Timeout while importing parties and dictionaries for {process_uid}")
        return False
    except Exception as e:
        print(f"Error importing parties and dictionaries for {process_uid}: {str(e)}")
        return False


def update_process_metadata_in_qdrant(process_uid, process_id, display_name, description=None):
    """Push process metadata updates to Qdrant (display_name/process_id)."""
    if not QDRANT_VECTOR_DB_BASE_URL:
        print(
            "Warning: QDRANT_VECTOR_DB_BASE_URL is not configured. "
            f"Skipping process metadata update for {process_uid}"
        )
        return False

    if not process_uid or not display_name:
        print("Warning: Missing process_uid or display_name. Skipping process metadata update.")
        return False

    payload = {
        "process_uid": str(process_uid),
        "display_name": display_name,
        "process_id": process_id,
    }
    if description is not None:
        payload["description"] = description

    try:
        url = f"{QDRANT_VECTOR_DB_BASE_URL}/admin/process-metadata"
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code in (200, 201):
            return True
        print(
            "Failed to update process metadata in Qdrant. "
            f"Status: {response.status_code}, Response: {response.text}"
        )
    except requests.exceptions.Timeout:
        print(f"Timeout while updating process metadata for {process_uid}")
    except Exception as exc:
        print(f"Error updating process metadata for {process_uid}: {str(exc)}")
    return False


def get_profiles_data_by_ids(ids, export_all=False):
    """Make profiles data ready to export"""
    if export_all:
        profile_query = models.Profile.objects.all()
    else:
        profile_query = models.Profile.objects.filter(id__in=ids)

    profiles_data = serializers.ProfileSerializer(profile_query, many=True).data

    for profile in profiles_data:
        profile["vendors"] = list()
        profile_name = profile["name"]
        profile_uid = profile.get("process_uid")
        vendors = Definition.objects.filter(definition_id=profile_name)
        for vendor in vendors:
            vendor_data = DefinitionSerializer(vendor).data
            profile["vendors"].append(vendor_data)
        
        # Export parties and dictionaries from Qdrant
        if profile_uid:
            parties_and_dictionaries = get_parties_and_dictionaries_from_qdrant(profile_uid)
        else:
            parties_and_dictionaries = None
        if parties_and_dictionaries:
            profile["parties_and_dictionaries"] = parties_and_dictionaries

    return profiles_data


@api_view(["POST"])
@permission_classes([AllowAny])
def send_profile_to_remote_system(request, profile_id):
    """Send a profile from one server to another remote server"""
    try:
        print("Request received for exporting profile")
        print(f"{profile_id=}")
        if not DataExportConfig.objects.exists():
            return Response(
                {"detail": "Data export config is not defined, Please set it first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print("Collecting data...")

        profiles_data = get_profiles_data_by_ids([profile_id])

        if len(profiles_data) == 0:
            return Response(
                {"detail": "No Profiles to send"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Added custom_category data from classifier
        URL = f"{CLASSIFIER_API_URL}/api/get_custom_category/"

        request_body = {
            "profile": profiles_data[0]["name"],
        }

        response = requests.get(URL, json=request_body)
        custom_category_data = {}
        if response.status_code == 200:
            custom_category_data = response.json()
            if custom_category_data:
                custom_category_data.pop("id")

        # Export Profile to remote system
        config = DataExportConfig.objects.first()
        url = f"{config.export_system_url}/api/dashboard/receive_profile_from_remote_system/"

        print(url)
        request_data = {
            "profiles": profiles_data,
            "custom_category": custom_category_data,
            "auth_key": config.export_system_auth_key,
        }

        response = requests.post(
            url, json=request_data, timeout=300
        )  # 5 Minutes timeout

        if response.status_code != 200:
            error = f"Profile export to '{config.export_system_name}' failed: \n {response.text}"
            return Response(
                {"detail": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"detail": f"Profile sent to {config.export_system_name} successfully"}
        )

    except Exception as error:
        print(error)
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def import_profile_filter(profiles_data):
    profile_field_names = [field.name for field in models.Profile._meta.fields]
    doc_field_names = [field.name for field in models.ProfileDocument._meta.fields]
    customer_field_names = [field.name for field in models.ProfileCustomer._meta.fields]
    process_customer_field_names = [field.name for field in models.ProcessCustomer._meta.fields]
    vendor_field_names = [field.name for field in Definition._meta.fields]
    data = []
    for profile in profiles_data:
        profile_docs = profile.pop("documents")
        profile_customers = profile.pop("customers")
        process_customers_data = profile.pop("process_customers", [])
        vendors_data = profile.pop("vendors")
        parties_and_dictionaries = profile.pop("parties_and_dictionaries", None)
        filtered_profile = {
            key: value for key, value in profile.items() if key in profile_field_names
        }
        docs = [
            {key: value for key, value in doc.items() if key in doc_field_names}
            for doc in profile_docs
        ]
        customers = [
            {
                key: value
                for key, value in customer.items()
                if key in customer_field_names
            }
            for customer in profile_customers
        ]
        process_customers = [
            {
                key: value
                for key, value in pc.items()
                if key in process_customer_field_names
            }
            for pc in process_customers_data
        ]
        vendors = [
            {key: value for key, value in vendor.items() if key in vendor_field_names}
            for vendor in vendors_data
        ]

        filtered_profile["documents"] = docs
        filtered_profile["customers"] = customers
        filtered_profile["process_customers"] = process_customers
        filtered_profile["vendors"] = vendors

        if parties_and_dictionaries:
            filtered_profile["parties_and_dictionaries"] = parties_and_dictionaries
        data.append(filtered_profile)
    return data


def prod_replace(profiles_data):
    """For special cases replace prod with incoming uat version"""
    for profile in profiles_data:
        profile_docs = profile["documents"]

        for profile_doc in profile_docs:
            definition_data = profile_doc["definition"]
            uat_data = definition_data["data"].get("uat")

            if uat_data:
                definition_data["data"]["prod"] = uat_data

    return profiles_data


def _layout_id_exists(definition_id, layout_id):
    """Check if a definition with the given layout_id exists for the definition_id."""
    return Definition.objects.filter(
        definition_id__iexact=definition_id,
        layout_id=layout_id
    ).exists()


def _generate_unique_layout_id(definition_id):
    """Generate a unique layout_id for the given definition_id."""
    while True:
        new_layout_id = str(uuid.uuid4())
        if not _layout_id_exists(definition_id, new_layout_id):
            return new_layout_id


def _prepare_vendor_data_for_creation(definition_id, vendor_data):
    """Prepare vendor data for creating a new definition."""
    # Create a copy to avoid modifying the original dict
    data = vendor_data.copy()
    
    # Remove fields that shouldn't be set manually
    data.pop("id", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)
    
    data["definition_id"] = definition_id
    
    # Handle layout_id
    current_layout_id = data.get("layout_id")
    if not current_layout_id or _layout_id_exists(definition_id, current_layout_id):
        data["layout_id"] = _generate_unique_layout_id(definition_id)
        if current_layout_id:
             print(f"Layout ID {current_layout_id} exists. Generated new layout_id: {data['layout_id']}")
        else:
             print(f"Generated new layout_id: {data['layout_id']}")
    
    return data


def _create_definition(definition_id, vendor_data, reason="", embedding=None, model_version=None):
    """Create a new definition with unique layout_id and optionally save embedding.
    
    Args:
        definition_id: The profile name
        vendor_data: Dictionary with definition data
        reason: Optional reason string for logging
        embedding: Optional pre-computed embedding to save
        model_version: Model version string (required if embedding is provided)
    """
    try:
        data = _prepare_vendor_data_for_creation(definition_id, vendor_data)
        new_definition = Definition.objects.create(**data)
        print(f"{reason}Created new definition with layout_id: {data['layout_id']}")
        
        # Save embedding if provided
        if embedding is not None and model_version:
            _save_embedding_to_db(new_definition, embedding, model_version, save_now=True)
    except Exception as e:
        print(f"Error creating definition: {e}")
        traceback.print_exc()


def _update_existing_definition(definition, vendor_data, similarity):
    """Update an existing definition."""
    print(f"Match found! Updating existing layout_id: {definition.layout_id} (similarity: {similarity:.4f})")
    try:
        data = vendor_data.get("data", {})
        definition.data = data
        definition.save()
        print(f"Successfully updated definition with layout_id: {definition.layout_id}")
    except Exception as e:
        print(f"Error updating definition: {e}")
        traceback.print_exc()


def _prepare_definition_for_bulk_create(definition_id, vendor_data, embedding=None, model_version=None):
    """
    Prepare a Definition instance for bulk_create (not saved yet).
    
    Returns:
        Definition instance ready for bulk_create, or None on error
    """
    try:
        data = _prepare_vendor_data_for_creation(definition_id, vendor_data)
        
        # Create Definition instance without saving
        definition = Definition(**data)
        
        # Set embedding fields if provided
        if embedding is not None and model_version:
            definition.embedding = pickle.dumps(embedding)
            definition.embedding_model_version = model_version
        
        return definition
    except Exception as e:
        print(f"Error preparing definition for bulk create: {e}")
        traceback.print_exc()
        return None


def update_or_create_definitions(definition_id, vendors_data):
    """
    Update existing definitions or create new ones based on hash_layout pattern matching.
    
    Args:
        definition_id: The profile name (definition_id)
        vendors_data: List of vendor dictionaries with definition data
        
    Logic:
        1. For each incoming vendor, check if hash_layout exists and has a pattern
        2. Loop through existing definitions to find matching patterns
        3. If match found (similarity >= threshold), update the existing definition
        4. If no match found, create new definition with a new layout_id
        5. Generate new layout_id for new definitions if existing one conflicts
    
    Performance optimizations:
        - Fetch existing definitions once (outside loop)
        - Pre-compute embeddings for all stored patterns once
        - Batch encode incoming patterns
        - Use vectorized similarity computation
        - Use bulk_create for new definitions (single DB operation)
        - Use bulk_update for existing definitions (single DB operation)
    """
    # Validate inputs
    if not vendors_data or not isinstance(vendors_data, list):
        if settings.DEBUG:
            print(f"No vendors data to process for definition_id: {definition_id}")
        return
    
    if not definition_id:
        if settings.DEBUG:
            print("Error: definition_id is None or empty")
        return
    
    # Fetch existing definitions ONCE (outside the loop)
    # Include embedding fields for database-stored embeddings optimization
    existing_definitions = list(Definition.objects.filter(
        definition_id__iexact=definition_id
    ).exclude(
        hash_layout=[]
    ).exclude(
        hash_layout__isnull=True
    ).only('id', 'layout_id', 'hash_layout', 'data', 'embedding', 'embedding_model_version'))
    
    # Get current model version for cache invalidation
    current_model_version = _get_model_version()
    
    # Load embeddings from database
    # Only compute mask when embedding is NOT in database (optimization)
    valid_definitions = []
    stored_embeddings_list = []
    patterns_to_encode = []
    definitions_needing_embedding = []  # Track definitions that need embedding updates
    
    for definition in existing_definitions:
        if definition.hash_layout and len(definition.hash_layout) > 0 and definition.hash_layout[0]:
            valid_definitions.append(definition)
            
            # Try to load embedding from database FIRST
            db_embedding = _get_embedding_from_db(definition, current_model_version)
            
            if db_embedding is not None:
                # Embedding exists - no need to mask! (faster path)
                stored_embeddings_list.append(db_embedding)
            else:
                # Embedding not in DB - need to mask and encode
                masked = mask_variable_content(definition.hash_layout[0])
                patterns_to_encode.append(masked)
                stored_embeddings_list.append(None)  # Placeholder
                definitions_needing_embedding.append(definition)
    
    # Pre-compute embeddings only for patterns not in database
    stored_embeddings = None
    if valid_definitions:
        try:
            model = settings.SENTENCE_TRANSFORMERS_MODEL
            
            # Encode only patterns not in database
            if patterns_to_encode:
                newly_encoded = model.encode(patterns_to_encode, convert_to_numpy=True, show_progress_bar=False)
                
                # Fill in the newly encoded embeddings (prepare for bulk update)
                encode_idx = 0
                for i, emb_data in enumerate(stored_embeddings_list):
                    if emb_data is None:
                        emb = newly_encoded[encode_idx]
                        stored_embeddings_list[i] = emb
                        
                        # Prepare embedding for bulk update (don't save yet)
                        if encode_idx < len(definitions_needing_embedding):
                            definition_to_update = definitions_needing_embedding[encode_idx]
                            _save_embedding_to_db(definition_to_update, emb, current_model_version, save_now=False)
                        encode_idx += 1
                
                # BATCH UPDATE: Save all embeddings in one DB operation
                if definitions_needing_embedding:
                    Definition.objects.bulk_update(
                        definitions_needing_embedding, 
                        ['embedding', 'embedding_model_version'],
                        batch_size=500
                    )
                    if settings.DEBUG:
                        print(f"Batch updated {len(definitions_needing_embedding)} definition embeddings")
            
            # Convert to numpy array
            stored_embeddings = np.array(stored_embeddings_list)
            
            # Normalize stored embeddings for cosine similarity
            stored_norms = np.linalg.norm(stored_embeddings, axis=1, keepdims=True)
            stored_norms[stored_norms == 0] = 1  # Avoid division by zero
            stored_embeddings = stored_embeddings / stored_norms
        except Exception as e:
            if settings.DEBUG:
                print(f"Error pre-computing stored embeddings: {e}")
            stored_embeddings = None
    
    # Separate vendors into those with and without hash_layout
    # Collect vendors without patterns for batch creation
    vendors_with_pattern = []
    vendors_without_pattern = []
    
    for vendor_data in vendors_data:
        incoming_hash_layout = vendor_data.get("hash_layout", [])
        if not incoming_hash_layout or not isinstance(incoming_hash_layout, list) or len(incoming_hash_layout) == 0:
            vendors_without_pattern.append(vendor_data)
        else:
            vendors_with_pattern.append(vendor_data)
    
    # BATCH CREATE: Vendors without hash_layout
    if vendors_without_pattern:
        definitions_to_create = []
        for vendor_data in vendors_without_pattern:
            definition = _prepare_definition_for_bulk_create(definition_id, vendor_data)
            if definition:
                definitions_to_create.append(definition)
        
        if definitions_to_create:
            Definition.objects.bulk_create(definitions_to_create, batch_size=500)
            if settings.DEBUG:
                print(f"Batch created {len(definitions_to_create)} definitions (no hash_layout)")
    
    # If no vendors with patterns, we're done
    if not vendors_with_pattern:
        return
    
    if not valid_definitions or stored_embeddings is None:
        # No existing patterns to compare - batch create all new with embeddings
        try:
            model = settings.SENTENCE_TRANSFORMERS_MODEL
            patterns_masked = [mask_variable_content(v.get("hash_layout", [])[0]) for v in vendors_with_pattern]
            embeddings = model.encode(patterns_masked, convert_to_numpy=True, show_progress_bar=False)
            
            # BATCH CREATE: All vendors with embeddings
            definitions_to_create = []
            for idx, vendor_data in enumerate(vendors_with_pattern):
                definition = _prepare_definition_for_bulk_create(
                    definition_id, 
                    vendor_data, 
                    embedding=embeddings[idx],
                    model_version=current_model_version
                )
                if definition:
                    definitions_to_create.append(definition)
            
            if definitions_to_create:
                Definition.objects.bulk_create(definitions_to_create, batch_size=500)
                if settings.DEBUG:
                    print(f"Batch created {len(definitions_to_create)} definitions (no existing patterns)")
        except Exception as e:
            if settings.DEBUG:
                print(f"Error encoding patterns: {e}")
            # Fallback: batch create without embeddings
            definitions_to_create = []
            for vendor_data in vendors_with_pattern:
                definition = _prepare_definition_for_bulk_create(definition_id, vendor_data)
                if definition:
                    definitions_to_create.append(definition)
            if definitions_to_create:
                Definition.objects.bulk_create(definitions_to_create, batch_size=500)
        return
    
    # Batch encode incoming patterns
    incoming_patterns_masked = [mask_variable_content(v.get("hash_layout", [])[0]) for v in vendors_with_pattern]
    
    try:
        model = settings.SENTENCE_TRANSFORMERS_MODEL
        
        # Encode all incoming patterns
        incoming_embeddings_raw = model.encode(incoming_patterns_masked, convert_to_numpy=True, show_progress_bar=False)
        
        # Normalize for similarity computation (keep raw for DB storage)
        incoming_norms = np.linalg.norm(incoming_embeddings_raw, axis=1, keepdims=True)
        incoming_norms[incoming_norms == 0] = 1
        incoming_embeddings_normalized = incoming_embeddings_raw / incoming_norms
    except Exception as e:
        if settings.DEBUG:
            print(f"Error encoding incoming patterns: {e}")
        # Fallback: batch create all as new (without embeddings)
        definitions_to_create = []
        for vendor_data in vendors_with_pattern:
            definition = _prepare_definition_for_bulk_create(definition_id, vendor_data)
            if definition:
                definitions_to_create.append(definition)
        if definitions_to_create:
            Definition.objects.bulk_create(definitions_to_create, batch_size=500)
        return
    
    # Compute similarity matrix: (num_incoming x num_stored)
    similarity_matrix = np.dot(incoming_embeddings_normalized, stored_embeddings.T)
    
    threshold = settings.LAYOUT_SIMILARITY_THRESHOLD
    
    # Collect updates and creates for batch operations
    definitions_to_update = []  # (definition, new_data)
    definitions_to_create = []  # Definition instances
    
    # Process each vendor with pattern
    for idx, vendor_data in enumerate(vendors_with_pattern):
        similarities = similarity_matrix[idx]
        best_idx = np.argmax(similarities)
        best_similarity = float(similarities[best_idx])
        
        if best_similarity >= threshold:
            # Match found - prepare for batch update
            matched_definition = valid_definitions[best_idx]
            data = vendor_data.get("data", {})
            matched_definition.data = data
            definitions_to_update.append(matched_definition)
            if settings.DEBUG:
                print(f"Match found! Will update layout_id: {matched_definition.layout_id} (similarity: {best_similarity:.4f})")
        else:
            # No match - prepare for batch create
            definition = _prepare_definition_for_bulk_create(
                definition_id, 
                vendor_data, 
                embedding=incoming_embeddings_raw[idx],
                model_version=current_model_version
            )
            if definition:
                definitions_to_create.append(definition)
                if settings.DEBUG:
                    print(f"(no match, best sim: {best_similarity:.4f}) Will create new definition with layout_id: {definition.layout_id}")
    
    # BATCH UPDATE: Update all matched definitions in one DB operation
    if definitions_to_update:
        Definition.objects.bulk_update(definitions_to_update, ['data'], batch_size=500)
        if settings.DEBUG:
            print(f"Batch updated {len(definitions_to_update)} matched definitions")
    
    # BATCH CREATE: Create all new definitions in one DB operation
    if definitions_to_create:
        Definition.objects.bulk_create(definitions_to_create, batch_size=500)
        if settings.DEBUG:
            print(f"Batch created {len(definitions_to_create)} new definitions")


def import_profiles_handler(profiles_data, ignore_fields=None, remote_import=False):
    """Manage import profiles"""
    with transaction.atomic():
        if ignore_fields:
            data = import_profile_filter(profiles_data=profiles_data)
        else:
            data = profiles_data
        for profile in data:
            # Extract parties_and_dictionaries before processing
            parties_and_dictionaries = profile.pop("parties_and_dictionaries", None)
            
            # Remove ID fields
            profile.pop("id")
            profile.pop("process_uid", None)
            profile.pop("process_id")
            for i in profile["documents"]:
                del i["id"]
                del i["profile"]

            for i in profile["customers"]:
                del i["id"]
                del i["profile"]

            for i in profile["vendors"]:
                del i["id"]

            profile_docs = profile.pop("documents")
            profile_customers = profile.pop("customers")
            vendors_data = profile.pop("vendors")
            process_customers_data = profile.pop("process_customers", [])

            # If Profile exists, update, it
            profile_qs = models.Profile.objects.filter(name=profile["name"])
            if profile_qs.exists():
                # Remove existing documents
                profile_instance = profile_qs.first()
                profile_instance.documents.all().delete()

                # Remove existing customers
                profile_instance.customers.all().delete()

                # Remove existing process_customers
                profile_instance.process_customers.all().delete()

                # Update other information
                for key, value in profile.items():
                    setattr(profile_instance, key, value)

                if profile_instance.email_subject_match_option == "ProcessId":
                    profile_instance.email_subject_match_text = (
                        profile_instance.process_id
                    )

                profile_instance.save()

                # Note: Definitions will be updated or created based on hash_layout matching
                # This is handled below after profile_instance is ready
            else:
                # Get process Id
                country = profile.get("country")
                project = profile.get("project")
                profile_viewset = ProfileViewSet()
                next_sequence = profile_viewset.get_next_sequence(
                    country=country, project_name=project
                )
                profile["process_id"] = next_sequence["next_process_id"]

                if profile["email_subject_match_option"] == "ProcessId":
                    profile["email_subject_match_text"] = profile["process_id"]

                # Create profile
                profile_instance = models.Profile.objects.create(**profile)

            # Create profile docs and customers data
            for profile_doc in profile_docs:
                models.ProfileDocument.objects.create(
                    profile=profile_instance, **profile_doc
                )
            for customer in profile_customers:
                models.ProfileCustomer.objects.create(
                    profile=profile_instance, **customer
                )
            for process_customer in process_customers_data:
                # Remove id and profile fields if present
                process_customer.pop("id", None)
                process_customer.pop("profile", None)
                models.ProcessCustomer.objects.create(
                    profile=profile_instance, **process_customer
                )

            # Update or create definitions based on hash_layout pattern matching
            update_or_create_definitions(profile_instance.name, vendors_data)
            
            # Import parties and dictionaries to Qdrant
            if parties_and_dictionaries:
                import_parties_and_dictionaries_to_qdrant(
                    profile_instance.process_uid,
                    parties_and_dictionaries
                )


@api_view(["POST"])
@permission_classes([AllowAny])
def receive_profile_from_remote_system(request):
    """Receive profile from external system"""
    try:
        payload = request.data
        profiles = payload["profiles"]
        custom_category = payload["custom_category"]
        request_auth_key = payload["auth_key"]

        # Vefiry Auth key
        if not DataImportConfig.objects.exists():
            return Response(
                {
                    "detail": "Data import config on reciever system is not defined, Please set it first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        local_auth_key = DataImportConfig.objects.first().auth_key
        if not (local_auth_key == request_auth_key):
            return Response(
                {"detail": "Sender and reciever auth key doesn't match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_profiles_handler(profiles, ignore_fields=True, remote_import=True)

        if custom_category:
            URL = f"{CLASSIFIER_API_URL}/api/create_custom_category/"
            requests.post(URL, json=custom_category)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"detail": "Definition imported successfully"})


@api_view(["POST"])
@permission_classes([AllowAny])
def send_template_to_remote_system(request, template_id):
    """Send a template from one server to another remote system"""
    try:
        print(f"{template_id=}")
        if not DataExportConfig.objects.exists():
            return Response(
                {"detail": "Data export config is not defined, Please set it first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        template_data = get_templates_data_by_ids([template_id])

        if len(template_data) == 0:
            return Response(
                {"detail": "No Template to send"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Export Profile to remote system
        config = DataExportConfig.objects.first()
        url = f"{config.export_system_url}/api/dashboard/receive_template_from_remote_system/"

        print(url)
        request_data = {
            "template": template_data["templates"],
            "auth_key": config.export_system_auth_key,
        }

        response = requests.post(
            url, json=request_data, timeout=100
        )  # 10 Seconds timeout

        if response.status_code != 200:
            error = f"Template export to '{config.export_system_name}' failed: \n {response.text}"
            return Response(
                {"detail": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"detail": f"Template sent to {config.export_system_name} successfully"}
        )

    except Exception as error:
        print(error)
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def receive_template_from_remote_system(request):
    """Receive template from external system"""
    try:
        payload = request.data
        template = payload["template"]
        request_auth_key = payload["auth_key"]

        # Vefiry Auth key
        if not DataImportConfig.objects.exists():
            return Response(
                {
                    "detail": "Data import config on reciever system is not defined, Please set it first."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        local_auth_key = DataImportConfig.objects.first().auth_key
        if not (local_auth_key == request_auth_key):
            return Response(
                {"detail": "Sender and reciever auth key doesn't match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_templates_handler(template)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"detail": "Definition imported successfully"})


def create_documents_handler(project_name):
    """Create documents for process"""
    default_document_structure = {
        "barcode": False,
        "category": "Processing",
        "doc_type": None,
        "language": "English",
        "content_location": "Email Attachment",
        "name_matching_option": "Auto",
        "name_matching_text": "",
        "ocr_engine": "S",
        "page_rotate": False,
        "show_embedded_img": False,
        "template": None
    }
    project_docs = models.Project.objects.get(name=project_name).settings.get("options", {}).get(
        "options-meta-root-type", {}
    ).get("items", [])
    process_doc_types = [doc for doc in project_docs if doc.get("addToProcess", False)]

    process_docs = []
    for doc_type in process_doc_types:
        document = default_document_structure.copy()
        document["doc_type"] = doc_type["docType"]
        process_docs.append(document)
    return process_docs


@api_view(["POST"])
def clone_profile(request):
    """
    Clone a profile with custom options
    profile name and email subject must be different from existing one
    """
    try:
        request_data = request.data
        try:
            source_profile_id = request_data["source_profile_id"]
            country = request_data["country"]
            free_name = request_data["free_name"]
            # mode_of_transport = request_data["mode_of_transport"]
            project = request_data["project"]
            fill_documents = request_data["fill_documents"]
            email_domains = request_data["email_domains"]
            email_from = request_data["email_from"]
            email_subject_match_option = request_data["email_subject_match_option"]
            email_subject_match_text = request_data["email_subject_match_text"]
            # include_customers = request_data["include_customers"]
            include_keys = request_data["include_keys"]
            # include_vendors = request_data["include_vendors"]

        except KeyError as e:
            return Response(
                {"detail": f"Missing required field: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            source_profile = models.Profile.objects.get(id=source_profile_id)
        except models.Profile.DoesNotExist:
            return Response(
                {"detail": f"Invalid source_profile_id: {source_profile_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Copy Data from source profile
        new_profile_data = serializers.ProfileSerializer(instance=source_profile).data

        # Update the fields
        del new_profile_data["id"]
        del new_profile_data["process_id"]  # Remove old process_id to avoid unique constraint error
        new_profile_data.pop("process_uid", None)
        documents = new_profile_data["documents"]
        new_profile_data["documents"] = [
            doc
            for doc in documents
            if f"{doc['doc_type']}_{doc['name_matching_text']}" in fill_documents
        ]
        for document in new_profile_data["documents"]:
            del document["id"]
            del document["profile"]

        for customer in new_profile_data["customers"]:
            del customer["id"]
            del customer["profile"]

        # if not include_customers:
        #     new_profile_data["customers"] = []

        if not fill_documents:
            new_profile_data["documents"] = create_documents_handler(project)

        if not include_keys:
            project_keys = models.Project.objects.get(name=project).settings.get("options", {}).get(
                "options-keys", {}
            ).get("items", [])
            process_keys = [key for key in project_keys if key.get("addToProcess", False)]
            new_profile_data["keys"] = process_keys

        new_profile_data["country"] = country
        new_profile_data["free_name"] = free_name
        # new_profile_data["mode_of_transport"] = mode_of_transport
        new_profile_data["project"] = project
        new_profile_data["email_domains"] = email_domains
        new_profile_data["email_from"] = email_from
        new_profile_data["email_subject_match_option"] = email_subject_match_option
        new_profile_data["email_subject_match_text"] = email_subject_match_text

        # Check if new_profile has unique name.
        free_name = free_name.upper()
        name = f"{country}_{free_name}_{project}"

        if models.Profile.objects.filter(name=name).exists():
            raise ValueError(
                "Process name already exists. It can be changed by updating one or more of the following fields: Name, Country Code."
            )
        if models.Profile.objects.filter(
            email_subject_match_text=email_subject_match_text
        ).exists():
            raise ValueError(
                "Description of the new Process is not unique. Please update and try again."
            )

        with transaction.atomic():
            # Generate new unique process_id for cloned profile
            profile_viewset = ProfileViewSet()
            sequence_info = profile_viewset.get_next_sequence(
                country=country,
                project_name=project
            )
            new_profile_data["process_id"] = sequence_info["next_process_id"]
            
            # Create new profile and profile documents
            serializer = serializers.ProfileSerializer(data=new_profile_data)
            serializer.is_valid(raise_exception=True)
            new_profile = serializer.save()

            # if include_vendors:
            #     soruce_vendors = Definition.objects.filter(
            #         definition_id=source_profile.name
            #     )
            #     for item in soruce_vendors:
            #         item.pk = None
            #         item.profile_doc = None
            #         item.definition_id = new_profile.name
            #         item.save()

        return Response(
            {"detail": f"Profile cloned successfully. (ID {new_profile.id})"}
        )

    except Exception as error:
        print(traceback.format_exc())
        error_message = None
        
        # Handle ValidationError from serializer
        if hasattr(error, 'detail'):
            # Check for field-specific errors first
            if isinstance(error.detail, dict):
                # Extract field-specific errors
                field_errors = []
                for field, messages in error.detail.items():
                    if field != 'non_field_errors' and messages:
                        if isinstance(messages, list):
                            field_errors.extend(messages)
                        else:
                            field_errors.append(str(messages))
                
                if field_errors:
                    error_message = field_errors[0]
                else:
                    # Check for non_field_errors
                    non_field_errors = error.detail.get("non_field_errors", [])
                    if non_field_errors:
                        error_message = non_field_errors[0] if isinstance(non_field_errors, list) else str(non_field_errors)
            elif isinstance(error.detail, list):
                error_message = error.detail[0] if error.detail else None
        
        # If no specific error message found, use the string representation
        if not error_message:
            error_message = str(error)
        
        # Map common field names to user-friendly labels
        error_message = error_message.replace('email_from', 'Source')
        error_message = error_message.replace('email_domains', 'Email Domain(s)')
        
        return Response(
            {"detail": error_message},
            status=status.HTTP_400_BAD_REQUEST if hasattr(error, 'detail') else status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all().order_by("id")
    list_serializer_class = serializers.ProjectListSerializer
    serializer_class = serializers.ProjectSerializer
    pagination_class = PaginationMeta

    def perform_update(self, serializer):
        old_instance = self.get_object()
        old_data = serializers.ProjectSerializer(old_instance).data
        new_instance = serializer.save()
        new_data = serializers.ProjectSerializer(new_instance).data
        # If requirements comes
        # ChangeLogger.log_model_changes(new_instance, old_instance, new_data, old_data, self.request.user)

    @action(detail=True, methods=["patch"], url_path="sync_mapped_keys")
    def sync_mapped_keys(self, request, pk=None):
        try:
            key_label = request.data.get("key_label")
            mapped_key = request.data.get("mapped_key")
            batch_id = request.data.get("batch_id")
            data_json = request.data.get("data_json")
            undo = request.data.get("undo")
            batch = Batch.objects.get(id=batch_id)

            if not key_label or not mapped_key or not batch_id or not data_json:
                return Response(
                    {"detail": "Missing required fields."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            batch.data_json = data_json
            batch.save()

            project = self.get_object()
            settings = project.settings or {}
            mapped_keys = (
                settings.get("options", {})
                .get("options-mapped-keys", {})
                .get("items", [])
            )

            # Check if the key already exists
            exists = any(item["mappedKey"] == mapped_key for item in mapped_keys)

            if exists:
                if undo:
                    mapped_keys = [
                        i for i in mapped_keys if i["mappedKey"] != mapped_key
                    ]

                    settings.setdefault("options", {}).setdefault(
                        "options-mapped-keys", {}
                    )["items"] = mapped_keys
                    project.settings = settings
                    project.save()

                    return Response(
                        {"detail": f"Mapped Key '{mapped_key}' removed successfully."},
                        status=status.HTTP_200_OK,
                    )

                return Response(
                    {"detail": f"Mapped Key '{mapped_key}' already exists."},
                    status=status.HTTP_200_OK,
                )

            # Append new key
            mapped_keys.append({"mappedKey": mapped_key, "keyLabel": key_label})

            # Save back to settings
            settings.setdefault("options", {}).setdefault("options-mapped-keys", {})[
                "items"
            ] = mapped_keys
            project.settings = settings
            project.save()

            return Response(
                {"detail": f"Mapped key '{mapped_key}' added successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as error:
            return Response(
                {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="import")
    def import_projects(self, request):
        """
        Bulk import projects from JSON.
        POST /api/dashboard/projects/import/
        """
        try:
            try:
                projects_data = request.data["projects"]
                import_settings_item = request.data.get("import_settings_item", None)
                replace_settings = request.data.get("replace_settings", False)
            except:
                return Response(
                    {"detail": "projects field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # if import_settings_item and import_settings_item not in projects_data[
            #     0
            # ].get("settings", {}):
            #     return Response(
            #         {
            #             "detail": f"{import_settings_item} not found in the project settings."
            #         },
            #         status=status.HTTP_400_BAD_REQUEST,
            #     )

            import_projects_handler(
                projects_data, import_settings_item, replace_settings
            )

            return Response({"detail": "Projects imported"})

        except Exception as error:
            print(traceback.format_exc())
            return Response(
                {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="export")
    def export_projects(self, request):
        """
        Bulk export all projects or filtered projects.
        POST /api/dashboard/projects/export/
        """
        try:
            try:
                ids = request.data.get("ids")
                export_all = request.data.get("export_all", False)
                export_settings_item = request.data.get("export_settings_item", None)
                if ids is None and export_all is False:
                    raise ValueError(
                        "Missing fields, endpoint requires 'ids' or 'export_all'."
                    )
            except ValueError as err:
                return Response(
                    {"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST
                )

            projects_data = get_projects_data_by_ids(
                ids, export_settings_item, export_all
            )
            return Response(projects_data)

        except Exception as error:
            return Response(
                {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action == "list":
            name = self.request.query_params.get("name", None)
            project_id = self.request.query_params.get("project_id", None)

            if project_id:
                queryset = queryset.filter(project_id__icontains=project_id)
            if name:
                queryset = queryset.filter(name__icontains=name)

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def list(self, request, *args, **kwargs):
        no_pagination = request.query_params.get("no_pagination", "false").lower()

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if no_pagination == "false":
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == "list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(ProjectViewSet, self).get_serializer_class()


class AdminProjectViewSet(ProjectViewSet):
    """
    Admin-only wrapper for ProjectViewSet.
    This endpoint is used when Projects is accessed from Admin menu.
    Enforces IsAdminUser permission to prevent privilege escalation.
    """
    permission_classes = [IsAdminUser]
    
    # Inherits all functionality from ProjectViewSet
    # The only difference is the permission_classes


def get_projects_data_by_ids(ids, export_settings_item=None, export_all=False):
    """Make project export ready"""
    if export_all:
        project_query = models.Project.objects.all()
    else:
        project_query = models.Project.objects.filter(id__in=ids)
    projects_data = serializers.ProjectSerializer(project_query, many=True).data

    try:
        for project in projects_data:
            output_channel_qs = models.OutputChannel.objects.filter(project=project["id"])
            output_channel_data = serializers.OutputChannelSerializer(output_channel_qs, many=True).data
            if output_channel_data:
                settings = project["settings"]
                output_channels = settings["outputChannels"]
                output_channels["OutputChannelConfig"] = output_channel_data
    except:
        traceback.print_exc()

    if export_settings_item:
        for project in projects_data:
            if export_settings_item == "keys":
                project["settings"] = {
                    "options": {
                        "options-keys": project["settings"]
                        .get("options", {})
                        .get("options-keys", {})
                    }
                }

            elif export_settings_item == "mappedKeys":
                project["settings"] = {
                    "options": {
                        "options-mapped-keys": project["settings"]
                        .get("options", {})
                        .get("options-mapped-keys", {})
                    }
                }

            elif export_settings_item == "docTypes":
                project["settings"] = {
                    "options": {
                        "options-meta-root-type": project["settings"]
                        .get("options", {})
                        .get("options-meta-root-type", {})
                    }
                }

            else:
                project["settings"] = {
                    export_settings_item: project["settings"].get(export_settings_item)
                }

    return projects_data


def import_projects_handler(projects_data, import_settings_item, replace_settings):
    """Update imported projects data"""
    def _format_duplicate_message(section, dups):
        section_map = {
            "options-meta-root-type": "doctypes",
            "options-keys": "keys",
        }
        section_label = section_map.get(section, section)
        if not dups:
            return f"Importing aborted due to discovery of Duplicate Entry: {section_label}"

        # simple duplicate list (e.g., duplicate names)
        if isinstance(dups, list) and dups and isinstance(dups[0], str):
            value = next((v for v in dups if v not in (None, "")), None)
            return (
                f'Importing aborted due to discovery of Duplicate Entry : {section_label}, '
                f'Entries are as Follows: "{value}"'
            )

        if isinstance(dups, list):
            dup = next((item for item in dups if isinstance(item, dict)), {})
            pair = dup.get("pair", {}) if isinstance(dup, dict) else {}
            if "docType" in pair and "docCode" in pair:
                value = pair.get("docType")
            elif "key" in pair and "value" in pair:
                value = pair.get("key")
            else:
                value = ", ".join(str(v) for v in pair.values() if v not in (None, ""))
            return (
                f'Importing aborted due to discovery of Duplicate Entry: {section_label}, '
                f'Entries are as Follows: "{value}"'
            )

        return f"Importing aborted due to discovery of Duplicate Entry: {section_label}"

    dups = None
    try:
        dups = find_duplicate_pairs_in_nested(
            projects_data[0]["settings"]["compoundKeys"],
            "keyItems",
            "keyLabel",
            "keyValue",
            "type",
        )
        if dups:
            raise ValueError(_format_duplicate_message("compoundKeys", dups))
    except (KeyError, TypeError, IndexError):
        pass
    try:
        dups = find_duplicate_pairs_in_nested(
            projects_data[0]["settings"]["keyQualifiers"],
            "options",
            "label",
            "value",
        )
        if dups:
            raise ValueError(_format_duplicate_message("keyQualifiers", dups))
    except (KeyError, TypeError, IndexError):
        pass
    try:
        dups = find_duplicate_pairs(
            projects_data[0]["settings"]["options"]["options-keys"]["items"],
            "keyLabel",
            "keyValue",
            "type",
        )
        if dups:
            raise ValueError(_format_duplicate_message("options-keys", dups))
    except (KeyError, TypeError, IndexError):
        pass
    try:
        print("inside====1")
        print(projects_data[0]["settings"]["options"]["options-meta-root-type"]["items"])
        dups = find_duplicate_pairs(
            projects_data[0]["settings"]["options"]["options-meta-root-type"]["items"],
            "docType",
            "docCode",
        )
        print("dups====1", dups)
        if dups:
            raise ValueError(_format_duplicate_message("options-meta-root-type", dups))
    except (KeyError, TypeError, IndexError):
        pass
    try:
        for parent_key in projects_data[0]['settings'].keys():
            if parent_key == 'options':
                dups = validate_options_keys(projects_data[0]['settings'])
                if dups:
                    raise ValueError(_format_duplicate_message("options-keys", dups))
            elif parent_key == 'compoundKeys':
                dups = validate_compound_keys(projects_data[0]['settings'])
                if dups:
                    raise ValueError(_format_duplicate_message("compoundKeys", dups))
            elif parent_key == 'keyQualifiers':
                dups = validate_key_qualifiers(projects_data[0]['settings'])
                if dups:
                    raise ValueError(_format_duplicate_message("keyQualifiers", dups))
            elif parent_key == 'options-meta-root-type':
                dups = validate_meta_root_types(projects_data[0]['settings'])
                if dups:
                    raise ValueError(_format_duplicate_message("options-meta-root-type", dups))

    except (KeyError, TypeError, IndexError):
        pass

    if dups:
        raise ValueError(
                f"Can't import duplicate entry found 7: {dups}"
            )



    updated_count = 0
    created_count = 0

    with transaction.atomic():
        data = projects_data
        for project in data:
            # Remove ID fields
            project.pop("id", None)
            project.pop("project_id", None)
            output_channels_data = (
                project.get("settings")
                .get("outputChannels", {})
                .pop("OutputChannelConfig", [])
            )

            # disable input channels
            input_channels = project.get("settings", {}).get("inputChannels", {})
            for key, value in input_channels.items():
                value["enabled"] = False

            print("input_channels", input_channels)
            project["settings"]["inputChannels"] = input_channels

            # If Project exists, update, it
            qs = models.Project.objects.filter(name=project["name"])

            if qs.exists():
                project_instance = qs.first()
                project_settings = project.pop("settings", {})

                if not project_instance.settings or replace_settings:
                    project_instance.settings = project_settings
                elif import_settings_item:

                    if import_settings_item == "keys":
                        keys_data = project_settings.get("options", {}).get(
                            "options-keys"
                        )
                        if not keys_data:
                            raise ValueError("Keys data not found")
                        project_instance.settings["options"]["options-keys"] = keys_data

                    elif import_settings_item == "mappedKeys":
                        mapped_keys_data = project_settings.get("options", {}).get(
                            "options-mapped-keys"
                        )
                        if not mapped_keys_data:
                            raise ValueError("Mapped Keys data not found")
                        project_instance.settings["options"][
                            "options-mapped-keys"
                        ] = mapped_keys_data

                    elif import_settings_item == "docTypes":
                        doc_types_data = project_settings.get("options", {}).get(
                            "options-meta-root-type"
                        )
                        if not doc_types_data:
                            raise ValueError("Doc Types data not found")
                        project_instance.settings["options"][
                            "options-meta-root-type"
                        ] = doc_types_data

                    else:
                        project_instance.settings[import_settings_item] = (
                            project_settings[import_settings_item]
                        )
                else:
                    for key in project_settings:
                        project_instance.settings[key] = project_settings[key]

                for key, value in project.items():
                    setattr(project_instance, key, value)

                project_instance.save()
                updated_count += 1
            else:
                # Create project
                project_instance = models.Project.objects.create(**project)
                created_count += 1

            try:
                if output_channels_data:
                    project_name = project_instance.name
                    models.OutputChannel.objects.filter(project__name=project_name).delete()
                    for record in output_channels_data:
                        record.pop("id", None)
                        record["project"] = project_instance.id
                        serializer = serializers.OutputChannelSerializer(data=record)
                        if serializer.is_valid(raise_exception=True):
                            serializer.save()
            except:
                traceback.print_exc()

    return {"updated_count": updated_count, "created_count": created_count}


def get_templates_data_by_ids(ids, export_all=False):
    """Make templates export ready."""
    if export_all:
        template_query = models.Template.objects.all()
    else:
        template_query = models.Template.objects.filter(id__in=ids)
    templates_data = serializers.TemplateSerializer(template_query, many=True).data
    return {"templates": templates_data}


@api_view(["POST"])
@permission_classes([IsAdminUser])
def export_templates(request):
    """This function handle to export templates in JSON format by IDs"""
    try:
        try:
            ids = request.data.get("ids")
            export_all = request.data.get("export_all", False)
            if ids is None and export_all is False:
                raise ValueError(
                    "Missing fields, endpoint requires 'ids' or 'export_all'."
                )
        except ValueError as err:
            return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

        templates_data = get_templates_data_by_ids(ids, export_all)
        return Response(templates_data)

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def import_templates_handler(templates_data):
    """Update imported templates data"""
    try:
        with transaction.atomic():
            for template in templates_data:
                # Remove ID fields
                template.pop("id")
                linked_batches = template["linked_batches"]
                batches = []
                # if the template name doesn't match matching batch still wouldn't work.
                docs = models.ProfileDocument.objects.filter(
                    template=template["template_name"]
                )

                linked_profiles = []
                for doc in docs:
                    if doc.profile.name in linked_profiles:
                        continue
                    linked_profiles.append(doc.profile.name)
                template["linked_profiles"] = linked_profiles

                for batch_id in linked_batches:
                    batch = Batch.objects.filter(
                        definition_id=template["template_name"], id=batch_id
                    )
                    if not batch.exists():
                        continue
                    batches.append(batch_id)
                template["linked_batches"] = batches
                # If Template exists, update, it
                qs = models.Template.objects.filter(
                    template_name=template["template_name"]
                )
                if qs.exists():
                    template_instance = qs.first()
                    # Update template fields
                    for k, v in template.items():
                        template_instance.__setattr__(k, v)
                    template_instance.save()

                else:
                    # Create template
                    models.Template.objects.create(**template)
            return True
    except Exception:
        print(traceback.format_exc())
        return None


@api_view(["POST"])
@permission_classes([IsAdminUser])
def import_templates(request):
    """
    Existing profiles will be removed (if exists)
    New Profiles, Profile documents and Definitions will be created
    """
    try:
        try:
            templates_data = request.data["templates"]
        except:
            return Response(
                {"detail": "profiles field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_templates = import_templates_handler(templates_data)
        if not import_templates:
            return Response(
                {"detail": "Failed to Import Templates"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Templates imported"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def clone_template(request):
    """
    Clone a template with name, country, project and doc_type
    At least one variable must be different from existing one
    """
    try:
        request_data = request.data
        try:
            source_template_id = request_data["source_template_id"]
            name = request_data["name"]
            country = request_data["country"]
            project = request_data["project"]
            doc_type = request_data["doc_type"]
        except KeyError:
            return Response(
                {
                    "detail": (
                        "following fields are required: "
                        "'source_template_id', 'name', "
                        "'country', 'project', 'doc_type'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            source_template = models.Template.objects.get(id=source_template_id)
        except models.Profile.DoesNotExist:
            return Response(
                {"detail": f"Invalid source_template_id: {source_template_id}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Copy Data from source profile
        new_template_data = serializers.TemplateSerializer(
            instance=source_template
        ).data

        # Update the fields
        del new_template_data["id"]

        new_template_data["name"] = name
        new_template_data["project"] = project
        new_template_data["country"] = country
        new_template_data["doc_type"] = doc_type
        new_template_data["linked_batches"] = []
        new_template_data["linked_profiles"] = []
        if not source_template.existing_profile_name:
            new_template_data["existing_profile_name"] = None
            new_template_data["existing_document"] = None

        # Check if new_profile has unique name.
        template_name = name.upper()
        template_name = f"{country}_{name}_{project}_{doc_type}"

        if models.Template.objects.filter(template_name=template_name).exists():
            raise ValueError("Template with same name already exists.")

        with transaction.atomic():
            # Create new template
            serializer = serializers.TemplateSerializer(data=new_template_data)
            serializer.is_valid(raise_exception=True)
            new_template = serializer.save()

            # Update definitions data for selected definitions

        return Response(
            {"detail": f"Template cloned successfully. (ID {new_template.id})"}
        )

    except Exception as error:
        non_field_errors = []
        try:

            non_field_errors = [
                error_detail
                for error_detail in error.detail.get("non_field_errors", [""])
            ]
        except Exception:
            pass

        print(traceback.format_exc())
        return Response(
            {"detail": non_field_errors[0] if len(non_field_errors) else str(error)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def send_to_group(group, event_type, data):
    async_to_sync(channel_layer.group_send)(group, {"type": event_type, "data": data})


@api_view(["GET"])
def timeline(request, timeline_id):
    """Retrive timeline data by template ID."""
    queryset = models.Timeline.objects.filter(timeline_id=timeline_id).order_by(
        "-event_time"
    )[:100]
    serializer = serializers.TimelineSerializer(queryset, many=True)
    return Response(serializer.data)


@receiver(post_save, sender=models.Timeline, dispatch_uid="send_timeline_update")
def send_timeline_update(sender, instance, **kwargs):
    """Send timeline data update"""
    data = dict(serializers.TimelineSerializer(instance).data)
    send_to_group(
        f"timeline_{convert_group_name(data['timeline_id'])}", "timeline", data
    )


def convert_group_name(group_name):
    # Remove any characters that are not ASCII alphanumerics, hyphens, or periods
    cleaned_name = re.sub(r"[^\w.-]", "-", group_name)
    # Ensure that the resulting string is a valid Unicode string
    cleaned_name = cleaned_name.encode("ascii", "ignore").decode("ascii")
    return cleaned_name


def prepare_template_path(template_name):
    """Generate template batch path"""
    batch_path = os.path.join(BATCH_INPUT_PATH, "templates", template_name)
    if os.path.exists(batch_path):
        shutil.rmtree(batch_path)
    os.makedirs(batch_path)
    return batch_path


def generate_template_page_file(template, batch_type="process"):
    """
    Return a string of batch arrtibutes in XML format
    """
    server_ip = os.getenv("SERVER_IP", None)
    page_rotate = "Y" if template.page_rotate else "N"
    barcode = "Y" if template.barcode else "N"
    page_file = (
        '<B id="">'
        '<V n="STATUS">1</V>'
        f'<V n="aidbServerIP">{server_ip}</V>'
        f'<V n="bvBatchType">{batch_type}</V>'
        f'<V n="bvICapProfile">{escape_xml_chars(template.template_name)}</V>'
        f'<V n="bvCustomer">{escape_xml_chars(template.name)}</V>'
        f'<V n="bvDocumentType">{template.doc_type}</V>'
        f'<V n="bvLanguage">{template.language}</V>'
        f'<V n="bvOCR">{template.ocr_engine}</V>'
        f'<V n="bvPageRotate">{page_rotate}</V>'
        f'<V n="bvBarcodeRead">{barcode}</V>'
        f'<V n="bvProjectName">{template.project}</V>'
        "</B>"
    )
    return page_file


@api_view(["POST"])
@permission_classes([IsAdminUser])
def template_upload_document(request):
    """Manage upload document (excel file only) for template"""
    try:
        upload_type = request.POST.get("upload_type")
        excel_file = request.FILES.getlist("excel_file")
        template_name = request.POST.get("template_name")

        assert upload_type in ["excel"], "Invalid Upload type"

        template = models.Template.objects.get(template_name=template_name)

        if not template:
            return Response(
                {
                    "detail": "Provided Template was not found.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_type = template.file_type
        if len(excel_file) == 0:
            return Response(
                {"detail": "excel_file not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        write_timeline_log(
            timeline_id=template.template_name,
            status="upload",
            message="Uploading new Document",
        )
        attachments_files_data = []

        attachments_folder = prepare_template_path(template_name)

        for file in excel_file:
            file_path = os.path.join(attachments_folder, file.name)
            # save pdf file to disk
            with open(file_path, "wb+") as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            if not file_path.endswith(file_type):
                return Response(
                    {"detail": "File_type does not matched"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if file_path.endswith(".xls"):
                if validate_xls_file(file_path):
                    filename = file.name
                    xlsx_filename = filename.rsplit(".", 1)[0] + ".xlsx"
                    xlsx_path = os.path.join(attachments_folder, xlsx_filename)
                    convert_xls_to_xlsx(file_path, xlsx_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                else:
                    print(f"Error: {file.name} is not a valid XLS file.")
                    if os.path.exists(file_path):
                        os.remove(file_path)

        attachments = os.listdir(attachments_folder)
        for file in attachments:
            path = os.path.join(attachments_folder, file)
            result = {"file_path": path}
            attachments_files_data.append(result)

        files_data = attachments_files_data
        if len(files_data) == 0:
            return Response(
                {
                    "detail": "No Datacap batches to create. (Attachments not matched with Template Document Type(s))",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        batches_created = []

        page_file = generate_template_page_file(template, batch_type="Process")
        files = [create_inmemory_file(i["file_path"]) for i in files_data]
        write_timeline_log(
            timeline_id=template.template_name,
            status="inprogress",
            message="Creating batches in Datacap",
        )

        datacap = DataCap(template.project)
        details = datacap.create_batch(
            files=files, page_file=page_file, delayed_release=True
        )
        datacap_batch_id = details["batch_id"]
        batches_created.append(datacap_batch_id)
        template.linked_batches.append(datacap_batch_id)
        template.save()

        paths = [file["file_path"] for file in attachments_files_data]
        details["file"] = ", ".join(paths)
        details = json.dumps(details)
        write_timeline_log(
            timeline_id=template.template_name,
            status="completed",
            message=f"Datacap Batch Created.",
            remarks=details,
            action="display_key_values",
        )

        write_timeline_log(
            timeline_id=template.template_name,
            status="inprogress",
            message="Awaiting Batch Upload.",
            remarks=json.dumps({"batch_id": datacap_batch_id}),
            action="display_key_values",
        )
        return Response(
            {
                "detail": "Processing Batch(es) created in datacap",
                "created_batches": batches_created,
            }
        )

    except Exception as error:
        response = {"detail": str(error)}
        print(traceback.format_exc())
        try:
            response["created_batches"] = batches_created
        except Exception:
            pass
        template_name = request.POST.get("template_name", None)
        template = models.Template.objects.filter(template_name=template_name)
        if template and template_name:
            write_timeline_log(
                timeline_id=template.first().template_name,
                status="failed",
                message=f"Error: {str(error)[:240]} ...",
            )
        return Response(
            response,
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_template_definition(request):
    """Get template definition from Template models"""
    template_name = request.GET.get("template_name", None)
    definition_version = request.GET.get("definition_version")
    if not template_name:
        return Response(
            {"detail": "No 'template_name' was provided in the request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        template = models.Template.objects.get(template_name=template_name)
        return Response(template.definition[definition_version])
    except models.Template.DoesNotExist:
        return Response(
            {"detail": "No matching template was found, did someone delete it?"},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAdminUser])
def update_template_definition_by_version(request):
    """update table or key data of definition for given version"""

    template_name = request.data.get("template_name")
    definition_version = request.data.get("definition_version")
    table = request.data.get("table")
    key = request.data.get("key")

    if not template_name:
        return Response(
            {"detail": "invalid definition_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not type:
        return Response({"detail": "invalid type"}, status=status.HTTP_400_BAD_REQUEST)

    if not definition_version:
        return Response(
            {"detail": "invalid definition_version"}, status=status.HTTP_400_BAD_REQUEST
        )
    qs = models.Template.objects.filter(template_name=template_name)

    if not qs.exists():
        return Response(
            {"detail": "Definition not found"}, status=status.HTTP_404_NOT_FOUND
        )
    else:
        template = qs.first()
        data = template.definition

        if not (definition_version in data.keys()):
            return Response(
                {"detail": f"Definition not found for version '{definition_version}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if table is not None:
            data[definition_version]["table"] = table
        if key is not None:
            data[definition_version]["key"] = key

        template.definition = data
        template.save()

        definition = {
            "id": template.id,
            "template_name": template_name,
            "type": template.doc_type,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }
        definition.update(template.definition[definition_version])

        return Response(definition)


class DeveloperSettingsViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'ApplicationSettings' model, providing CRUD operations
    integrating with the ApplicationSettingsSerializer for data validation and response
    """

    queryset = models.DeveloperSettings.objects.all()
    serializer_class = serializers.DeveloperSettingsSerializer
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = models.DeveloperSettings.objects.first()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if models.DeveloperSettings.objects.exists():
            instance = models.DeveloperSettings.objects.first()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return super().create(request, *args, **kwargs)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def create_default_dev_settings(request):
    """Create default developer settings"""

    developer_settings = models.DeveloperSettings.objects.first()
    if not developer_settings:
        developer_settings = models.DeveloperSettings.objects.create()
    developer_settings.data = developer_settings.default_settings
    developer_settings.save()
    return Response({"detail": "Default developer settings created successfully."})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def import_developer_settings(request):
    """
    Import appication settings to AIDB system
    """
    try:
        developer_settings = request.data["developer_settings"]

        if not isinstance(developer_settings, dict):
            raise
    except:
        print(f"{request=}")
        print(f"{request.data=}")
        traceback.print_exc()
        return Response(
            {"detail": "invalid payload (developer_settings)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = models.DeveloperSettings.objects.all()

    if qs.exists():
        instance = qs.first()
        instance.data = developer_settings

        instance.save()
    else:
        instance = models.DeveloperSettings.objects.create(data=developer_settings)

    serialize_data = serializers.DeveloperSettingsSerializer(instance).data

    return Response(
        {
            "data": serialize_data,
            "detail": "Developer Settings imported",
        }
    )


@api_view(["POST"])
def upload_yaml_file(request: HttpRequest, project_id):
    try:
        project_instance = models.Project.objects.get(id=project_id)
    except models.Project.DoesNotExist as _e:
        return Response(str(_e), status=status.HTTP_404_NOT_FOUND)
    serializer = serializers.YamlSerializer(data=request.data)
    if serializer.is_valid():
        replace_data = serializer.data.get("replace_data", False)
        try:
            yaml_data = serializer.get_parsed_yaml()
            try:
                project_name = next(iter(yaml_data["components"]["schemas"]))
            except KeyError:
                project_name = next(
                    iter(
                        yaml_data["securityDefinitions"]["oAuth2Token"]["scopes"].keys()
                    )
                )
            if not project_name:
                # Project name undetected from YAML file taking from database
                project_name = project_instance.name
            try:
                schemas = yaml_data["components"]["schemas"]
            except KeyError:
                schemas = yaml_data["definitions"]
            try:
                required_items = schemas[project_name].get("required", [])
            except:
                print("Required ITEMS not found in schema")
                print(traceback.print_exc())
            normal_key_list = yaml_utils.extract_normal_keys(schemas, project_name)
            compound_keys_list, key_qualifier_list, nk_list = (
                yaml_utils.extract_other_keys(
                    schemas[project_name]["properties"], yaml_data
                )
            )
            merged_keys = {
                "normal": normal_key_list + nk_list,
                "compound": compound_keys_list,
                "key_qualifiers": key_qualifier_list,
            }
            converted_data = yaml_utils.convert_yaml_format_to_def_settings(
                merged_keys, required_items
            )
            result = yaml_utils.convert_dict_to_settings(converted_data, project_name)
            definition_settings = result.get("settings")
            existing_settings = project_instance.settings
            key_items = (
                definition_settings.get("options", {})
                .get("options-keys", {})
                .get("items", [])
            )
            new_key_qualifiers = definition_settings.get("keyQualifiers", [])
            new_compound_keys = definition_settings.get("compoundKeys", [])
            if replace_data:
                existing_settings["options"]["options-keys"]["items"] = key_items
                existing_settings["compoundKeys"] = new_compound_keys
                existing_settings["keyQualifiers"] = new_key_qualifiers
            else:
                # Default strategy if replace false we will append data on top of existing settings
                # If replace data true only append option["items"],"compoundKeys" and "keyQualifiers"
                existing_key_items = existing_settings["options"]["options-keys"][
                    "items"
                ]
                unique_new_items = [
                    item for item in key_items if item not in existing_key_items
                ]
                existing_key_items.extend(unique_new_items)
                # Process for compound items
                updated_compound_keys = yaml_utils.merge_new_keys_with_existing_one(
                    existing_settings.get("compoundKeys", []), new_compound_keys
                )
                existing_settings["compoundKeys"] = updated_compound_keys
                # Process for key qualifiers
                updated_key_qualifiers = yaml_utils.merge_new_keys_with_existing_one(
                    existing_settings.get("keyQualifiers", []), new_key_qualifiers
                )
                existing_settings["keyQualifiers"] = updated_key_qualifiers
            project_instance.settings = existing_settings
            project_instance.save()
            print("Processed YAML File successfully")
            return Response(
                {
                    "data": {"project": result.get("project")},
                    "detail": "YAML file processed for project",
                }
            )
        except Exception as _e:
            print("Error while parsing YAML File", traceback.print_exc())
            return Response(
                {"detail": "Error parsing YAML File"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    errors = serializer.errors
    try:
        first_error = next(iter(errors.values()))[0]
    except Exception:
        first_error = "File is not valid"
    return Response({"detail": first_error}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def parse_yaml_json_keys(request: HttpRequest):
    """
    Parse YAML or JSON file and return a list of keys.
    Accepts both .yaml/.yml and .json files.
    """
    serializer = serializers.YamlJsonParserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            parsed_content = serializer.get_parsed_content()
            file_type = serializer.get_file_type()

            # Extract keys from the parsed content
            keys = yaml_utils.extract_keys_from_yaml_json(parsed_content)

            return Response(
                {
                    "data": {
                        "keys": keys,
                        "file_type": file_type,
                        "total_keys": len(keys),
                    },
                    "detail": f"Successfully parsed {file_type.upper()} file",
                }
            )
        except Exception as _e:
            print("Error while parsing file", traceback.print_exc())
            return Response(
                {"detail": "Error parsing file"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    errors = serializer.errors
    try:
        first_error = next(iter(errors.values()))[0]
    except Exception:
        first_error = "File is not valid"
    return Response({"detail": first_error}, status=status.HTTP_400_BAD_REQUEST)


class OutputChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing OutputChannels data
    """
    queryset = models.OutputChannel.objects.all().order_by("id")
    serializer_class = serializers.OutputChannelSerializer

    def get_queryset(self):
        queryset = self.queryset
        output_id = self.request.query_params.get("output_id")
        if output_id:
            queryset = queryset.filter(output_id=output_id)
        return queryset

    def delete(self, request, *args, **kwargs):
        output_id = self.request.query_params.get("output_id")
        if not output_id:
            return Response(
                {"detail": "output_id required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.queryset.filter(output_id=output_id).delete()

        return Response(
            {"detail": f"Output configuration deleted"}, status=status.HTTP_200_OK
        )


@api_view(["GET"])
def get_all_processes(request):
    try:
        # Get all items from the model
        items = models.Profile.objects.all()

        # Serialize the data
        serializer = serializers.ProfileListSerializer(items, many=True)

        return Response(
            {"success": True, "data": serializer.data, "count": len(serializer.data)},
            status=status.HTTP_200_OK,
        )
    except models.Profile.DoesNotExist:
        traceback.print_exc()
        return Response(
            {"success": False, "error": "No profiles found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ===== EDITOR PRESENCE ENDPOINTS =====

@api_view(["POST"])
def join_editor(request):
    """
    Register user presence when they start editing a resource.
    
    Request body:
        - resource_type: 'project' or 'process'
        - resource_id: ID or name of the resource
        - tab_id: Unique tab identifier
    
    Returns:
        - active_editors: List of users currently editing this resource
    """
    from utils.presence_utils import register_editor_presence, get_active_editors, cleanup_stale_presence_threshold
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        resource_type = request.data.get("resource_type")
        resource_id = request.data.get("resource_id")
        tab_id = request.data.get("tab_id")
        
        if not all([resource_type, resource_id, tab_id]):
            return Response(
                {"error": "resource_type, resource_id, and tab_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user

        # Opportunistically cleanup stale editors who stopped heartbeating
        try:
            cleanup_stale_presence_threshold(resource_type=str(resource_type), resource_id=str(resource_id), stale_seconds=40)
        except Exception:
            # best-effort
            pass

        # Register presence
        register_editor_presence(
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user.id,
            username=user.username,
            tab_id=tab_id
        )
        
        # Get other active editors (excluding current user+tab)
        active_editors = get_active_editors(
            resource_type=resource_type,
            resource_id=str(resource_id),
            exclude_user_id=user.id,
            exclude_tab_id=tab_id
        )
        
        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        group_name = f"presence_{resource_type}_{resource_id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "editor_joined",
                "user_id": user.id,
                "username": user.username,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "tab_id": tab_id
            }
        )
        
        return Response({
            "success": True,
            "active_editors": active_editors,
            "current_user_id": user.id,  # Include current user's ID
            "message": f"Joined editor session for {resource_type} {resource_id}"
        })
        
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def leave_editor(request):
    """
    Unregister user presence when they leave the editor.
    
    Request body:
        - resource_type: 'project' or 'process'
        - resource_id: ID or name of the resource
        - tab_id: Unique tab identifier
    
    Returns:
        - success: Boolean indicating if leave was successful
    """
    from utils.presence_utils import unregister_editor_presence
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        resource_type = request.data.get("resource_type")
        resource_id = request.data.get("resource_id")
        tab_id = request.data.get("tab_id")
        
        if not all([resource_type, resource_id, tab_id]):
            return Response(
                {"error": "resource_type, resource_id, and tab_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Unregister presence
        result = unregister_editor_presence(
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user.id,
            tab_id=tab_id
        )
        
        # Broadcast via WebSocket
        channel_layer = get_channel_layer()
        group_name = f"presence_{resource_type}_{resource_id}"
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "editor_left",
                "user_id": user.id,
                "username": user.username,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "tab_id": tab_id
            }
        )
        
        return Response({
            "success": result["success"],
            "message": f"Left editor session for {resource_type} {resource_id}"
        })
        
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def heartbeat_editor(request):
    """
    Update heartbeat for active editor presence.
    
    Request body:
        - resource_type: 'project' or 'process'
        - resource_id: ID or name of the resource
        - tab_id: Unique tab identifier
    
    Returns:
        - success: Boolean indicating if heartbeat was successful
    """
    from utils.presence_utils import heartbeat_presence
    
    try:
        resource_type = request.data.get("resource_type")
        resource_id = request.data.get("resource_id")
        tab_id = request.data.get("tab_id")
        
        if not all([resource_type, resource_id, tab_id]):
            return Response(
                {"error": "resource_type, resource_id, and tab_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        # Update heartbeat
        result = heartbeat_presence(
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user.id,
            tab_id=tab_id
        )
        
        return Response({
            "success": result["success"],
            "message": "Heartbeat updated" if result["success"] else result.get("error", "Failed")
        })
        
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def cleanup_reloaded_presence(request):
    """
    Force-remove presence entries for a resource matching a given tab_id.
    Intended to be called by a freshly-reloaded tab which previously set the
    sessionStorage reload flag. This ensures the old presence entry is removed
    and broadcasts an `editor_left` event so waiting users are freed immediately.

    Request body:
        - resource_type
        - resource_id
        - tab_id
    """
    from utils.presence_utils import unregister_editor_presence
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    try:
        resource_type = request.data.get("resource_type")
        resource_id = request.data.get("resource_id")
        tab_id = request.data.get("tab_id")

        if not all([resource_type, resource_id, tab_id]):
            return Response(
                {"error": "resource_type, resource_id, and tab_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        # Attempt to unregister any presence for this user+tab
        result = unregister_editor_presence(
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user.id,
            tab_id=tab_id,
        )

        # Broadcast editor_left so other clients update immediately
        channel_layer = get_channel_layer()
        group_name = f"presence_{resource_type}_{resource_id}"

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "editor_left",
                "user_id": user.id,
                "username": user.username,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "tab_id": tab_id,
            },
        )

        return Response({"success": result.get("success", False)})

    except Exception as e:
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def editor_status(request):
    """
    Get list of users currently editing a resource.
    
    Query params:
        - resource_type: 'project' or 'process'
        - resource_id: ID or name of the resource
    
    Returns:
        - active_editors: List of users currently editing this resource
    """
    from utils.presence_utils import get_active_editors
    
    try:
        resource_type = request.query_params.get("resource_type")
        resource_id = request.query_params.get("resource_id")
        
        if not all([resource_type, resource_id]):
            return Response(
                {"error": "resource_type and resource_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get active editors
        active_editors = get_active_editors(
            resource_type=resource_type,
            resource_id=str(resource_id)
        )
        
        return Response({
            "success": True,
            "active_editors": active_editors,
            "count": len(active_editors)
        })
        
    except Exception as e:
        traceback.print_exc()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
