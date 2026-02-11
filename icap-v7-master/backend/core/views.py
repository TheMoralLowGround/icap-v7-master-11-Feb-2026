"""
Organization: AIDocBuilder Inc.
File: core/views.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature updates
    - Sunny - Feature updates

Last Updated By: Nayem
Last Updated At: 2024-03-31

Description:
    This file defines viewsets such as DefinitionViewSet, BatchViewSet, EmailBatchViewSet, TrainBatchViewSet and ApplicationSettingsViewSet
    along with other core functions

Dependencies:
    - pandas as pd
    - deepcopy from copy
    - Q from django.db.models
    - settings from django.conf
    - HttpResponse from django.http
    - status, viewsets from rest_framework
    - action, api_view from rest_framework.decorators
    - Response from rest_framework.response
    - datetime from datetime
    - models, serializers from core
    - PaginationMeta from core.pagination
    - Profile, Project, Template from dashboard.models
    - ProjectSerializer from dashboard.serializers
    - batch_awaiting_datacap from utils.utils

Main Features:
    - Viewset for Definition, Batch, Email Batch, Train Batch and Application Settings.
    - Search, update, and manage definition by version and profile.
    - Retrive definition, batches and RA json data.
    - Download data json excel file from batch path.
    - Get batch status and latest batch info.
"""

import json
import os
import pytz
import shutil
import traceback
import pandas as pd
from copy import deepcopy

from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.conf import settings
from django.http import HttpResponse
from utils.change_logger import ChangeLogger
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from datetime import datetime

from core.permissions import IsAdminUser

from rabbitmq_producer import publish
from core import models, serializers
from core.pagination import PaginationMeta
from pipeline.utils.process_batch_utils import write_parent_batch_log

from django.db import transaction
from dashboard.models import Profile, Project, Template
from dashboard.serializers import ProfileSerializer, ProjectSerializer
from utils.utils import batch_awaiting_datacap, clean_definition_settings, to_camel_case

BATCH_INPUT_PATH = settings.BATCH_INPUT_PATH_DOCKER
DATASET_BATCH_INPUT_PATH = settings.DATASET_BATCH_INPUT_PATH


class DefinitionViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'Definition' model, providing CRUD operations
    integrating with DefinitionSerializer and DefinitionListSerializer for data validation and response
    """

    queryset = models.Definition.objects.all().order_by(
        "definition_id", "vendor", "type", "name_matching_text"
    )
    serializer_class = serializers.DefinitionSerializer
    list_serializer_class = serializers.DefinitionListSerializer
    pagination_class = PaginationMeta

    @action(detail=False, methods=["post"])
    def clone(self, request):
        request_data = request.data
        required_keys = [
            "reference_id",
            "definition_id",
            "vendor",
            "type",
            "name_matching_text",
        ]
        missing_keys = [key for key in required_keys if not request_data.get(key)]
        if missing_keys:
            message = {key: ["This field is required."] for key in missing_keys}
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        override = request_data.get("override", False)

        try:
            reference = models.Definition.objects.get(id=request_data["reference_id"])
        except:
            message = {"non_field_errors": ["Reference Definition not found."]}
            return Response(data=message, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "definition_id": request_data["definition_id"],
            "layout_id": request_data["layout_id"],
            "vendor": request_data["vendor"],
            "type": request_data["type"],
            "name_matching_text": request_data["name_matching_text"],
            "data": reference.data,
            "cw1": reference.cw1,
        }

        qs = models.Definition.objects.filter(
            definition_id__iexact=request_data["definition_id"]
        ).filter(layout_id__iexact=request_data["layout_id"])
        definition_exists = qs.exists()

        if not definition_exists:
            models.Definition.objects.create(**data)
        else:
            if not override:
                message = {
                    "non_field_errors": [
                        "Provided Definition ID (Profile ID and layout_id combination already exists."
                    ],
                    "definition_exists": True,
                }
                return Response(data=message, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Find a exiting definition and update it.
                definition = qs.first()

                definition.definition_id = request_data["definition_id"]
                definition.layout_id = request_data["layout_id"]
                definition.vendor = request_data["vendor"]
                definition.type = request_data["type"]
                definition.name_matching_text = request_data["name_matching_text"]
                definition.data = reference.data
                definition.cw1 = reference.cw1
                definition.save()

        return Response(
            data={"detail": "Definition Cloned Successfully"}, status=status.HTTP_200_OK
        )

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action == "list":
            definition_id = self.request.query_params.get("definition_id", None)
            vendor = self.request.query_params.get("vendor", None)
            type = self.request.query_params.get("type", None)
            name_matching_text = self.request.query_params.get(
                "name_matching_text", None
            )
            cw1 = self.request.query_params.get("cw1", None)

            if definition_id:
                queryset = queryset.filter(definition_id__icontains=definition_id)
            if vendor:
                queryset = queryset.filter(vendor__icontains=vendor)
            if type:
                queryset = queryset.filter(type__icontains=type)
            if name_matching_text:
                queryset = queryset.filter(
                    name_matching_text__icontains=name_matching_text
                )
            if cw1:
                cw1 = True if cw1 == "true" else False
                queryset = queryset.filter(cw1=cw1)

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(DefinitionViewSet, self).get_serializer_class()


@api_view(["POST"])
def update_definition_by_version(request):
    """update table or key data of definition for given version"""

    definition_id = request.data.get("definition_id")
    layout_id = request.data.get("layout_id")
    definition_version = request.data.get("definition_version")
    table = request.data.get("table")
    key = request.data.get("key")

    if not definition_id:
        return Response(
            {"detail": "invalid definition_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not definition_version:
        return Response(
            {"detail": "invalid definition_version"}, status=status.HTTP_400_BAD_REQUEST
        )

    qs = models.Definition.objects.filter(definition_id__iexact=definition_id).filter(
        layout_id__iexact=layout_id
    )
    if not qs.exists():
        return Response(
            {"detail": "Definition not found"}, status=status.HTTP_404_NOT_FOUND
        )
    else:
        definition = qs.first()
        data = definition.data

        if not (definition_version in data.keys()):
            return Response(
                {"detail": f"Definition not found for version '{definition_version}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if table is not None:
            data[definition_version]["table"] = table
        if key is not None:
            data[definition_version]["key"] = key

        definition.data = data
        definition.save()

        # Return updated definition
        definition = serializers.DefinitionSerializer(definition).data
        data = definition["data"][definition_version]
        del definition["data"]
        definition.update(data)

        # Add type_seq_no
        # qs = (
        #     models.Definition.objects.filter(definition_id__iexact=definition_id)
        #     .filter(type__iexact=type)
        #     .order_by("created_at")
        # )

        # if qs.count() > 1:
        #     type_seq_no = 0
        #     for i in qs:
        #         type_seq_no += 1
        #         if i.name_matching_text == definition["name_matching_text"]:
        #             break
        #     definition["type_seq_no"] = type_seq_no
        # else:
        #     definition["type_seq_no"] = 0

        return Response(definition)


class ApplicationSettingsViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'ApplicationSettings' model, providing CRUD operations
    integrating with the ApplicationSettingsSerializer for data validation and response
    """

    queryset = models.ApplicationSettings.objects.all()
    serializer_class = serializers.ApplicationSettingsSerializer
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        queryset = models.ApplicationSettings.objects.first()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if models.ApplicationSettings.objects.exists():
            instance = models.ApplicationSettings.objects.first()
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return super().create(request, *args, **kwargs)


class BatchViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'Batch' model, providing CRUD operations
    integrating with BatchSerializer and BatchListSerializer for data validation and response
    """

    lookup_value_regex = "[^/]+"
    queryset = models.Batch.objects.all().order_by("id")
    list_serializer_class = serializers.BatchListSerializer
    serializer_class = serializers.BatchSerializer
    pagination_class = PaginationMeta

    @action(detail=False, methods=["post"], name="List with POST")
    def filter_list(self, request, *args, **kwargs):
        """
        Handle list retrieval with POST request. This utilizes the overridden
        'get_queryset' method for filtering based on POST data.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["delete"])
    def delete_multiple(self, request):
        """
        Handle multiple batch items to delete
        """
        ids = request.data.get("ids")
        remove_from_disk = request.data.get("remove_from_disk")
        if not ids:
            return Response(
                {"detail": "invalid ids"}, status=status.HTTP_400_BAD_REQUEST
            )

        if remove_from_disk:
            for id in ids:
                try:
                    batch_instance = models.Batch.objects.get(id=id)
                    sub_path = batch_instance.sub_path
                    batch_path = os.path.join(BATCH_INPUT_PATH, sub_path, id)
                    if os.path.exists(batch_path):
                        shutil.rmtree(batch_path)
                except models.Batch.DoesNotExist:
                    pass

        queryset = models.Batch.objects.filter(id__in=ids)
        for batch in queryset:
            parent_batch_id = (
                models.TrainToBatchLink.objects.filter(batch_id=batch.id)
                .values_list("train_batch", flat=True)
                .first()
            )
            if parent_batch_id:
                write_parent_batch_log(
                    message=f"Batch {batch.id} was deleted successfully!",
                    batch_id=parent_batch_id,
                    status="incomplete",
                )
        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """
        Customize for viewset to filtering data
        """
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action == "list" or self.action == "filter_list":
            serializer_class = self.get_serializer_class()
            fields = serializer_class.Meta.fields
            id = self.request.query_params.get("id", None)
            queryset = queryset.only(*fields)
            queryset = queryset.filter(visible=True)

            definition_id = self.request.query_params.get("definition_id", None)
            vendor = self.request.query_params.get("vendor", None)
            type = self.request.query_params.get("type", None)
            mode = self.request.query_params.get("mode", None)
            extension = self.request.query_params.get("extension", None)
            project = self.request.query_params.get("project", None)
            status = self.request.query_params.get("status", None)
            email_batch_id = self.request.query_params.get("email_batch_id", None)
            train_batch_id = self.request.query_params.get("train_batch_id", None)
            template_name = self.request.query_params.get("template_name", None)
            profile_training = self.request.query_params.get("profile_training", None)

            if self.action == "list":
                project_countries = self.request.query_params.get(
                    "project_countries", None
                )
            elif self.action == "filter_list":
                project_countries = self.request.data.get("project_countries", None)

            if id:
                queryset = queryset.filter(id__icontains=id)
            if profile_training:
                queryset = queryset.filter(
                    id__in=models.TrainToBatchLink.objects.values_list(
                        "batch_id", flat=True
                    ),
                    mode="training",
                )
            if definition_id:
                queryset = queryset.filter(definition_id__icontains=definition_id)
            if vendor:
                queryset = queryset.filter(vendor__icontains=vendor)
            if type:
                queryset = queryset.filter(type__icontains=type)
            if mode:
                queryset = queryset.filter(mode__icontains=mode)
            if extension:
                queryset = queryset.filter(extension__icontains=extension)
            if project:
                queryset = queryset.filter(project__icontains=project)
            if status:
                queryset = queryset.filter(status__icontains=status)
            if email_batch_id:
                email_batches = list(
                    models.EmailToBatchLink.objects.filter(
                        email_id=email_batch_id
                    ).values_list("batch_id", flat=True)
                )
                queryset = queryset.filter(id__in=email_batches)
            if train_batch_id:
                train_batches = list(
                    models.TrainToBatchLink.objects.filter(
                        train_batch_id=train_batch_id
                    ).values_list("batch_id", flat=True)
                )
                queryset = queryset.filter(id__in=train_batches).order_by("-created_at")
            if template_name:
                template = Template.objects.get(template_name=template_name)
                linked = template.linked_batches
                queryset = queryset.filter(id__in=linked)

            # if project_countries:
            #     query = Q()
            #     for country_code, project_list in project_countries.items():
            #         if not project_list:
            #             continue

            #         project_query = Q()
            #         for project in project_list:
            #             project_query |= Q(definition_id__icontains=project)
            #         query |= project_query & Q(definition_id__startswith=country_code)
            #     if query:
            #         queryset = queryset.filter(query)
            #     else:
            #         queryset = queryset.none()

            # if not template_name and not project_countries:
            #     queryset = queryset.model.objects.none()

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def get_profile_information(self, response):
        """
        Append necessary profile information
        """
        batch = self.queryset.filter(id=self.kwargs.get("pk")).first()
        multi_shipment = False

        if batch and batch.definition_id:
            try:
                profile = Profile.objects.get(name=batch.definition_id)
                multi_shipment = profile.multi_shipment
            except Profile.DoesNotExist:
                pass

        response.data["profile_information"] = {"multi_shipment": multi_shipment}
        return response

    def retrieve(self, request, *args, **kwargs):
        """
        Handle the retrieval of a single object
        """
        response = super().retrieve(request, *args, **kwargs)
        return self.get_profile_information(response)

    def get_serializer_class(self):
        """
        select the serializer class to use based on the current request
        """
        if self.action == "list" or self.action == "filter_list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(BatchViewSet, self).get_serializer_class()


class EmailBatchViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'EmailBatch' model, providing CRUD operations
    integrating with the EmailBatchSerializer for data validation and response
    """

    lookup_value_regex = "[^/]+"
    queryset = models.EmailBatch.objects.all().order_by("id")
    list_serializer_class = serializers.EmailBatchSerializer
    serializer_class = serializers.EmailBatchSerializer
    pagination_class = PaginationMeta

    @action(detail=False, methods=["post"], name="List with POST")
    def filter_list(self, request, *args, **kwargs):
        """
        Handle list retrieval with POST request. This utilizes the overridden
        'get_queryset' method for filtering based on POST data.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["delete"])
    def delete_multiple(self, request):
        """
        Handle multiple emailbatch items to delete
        """
        ids = request.data.get("ids")
        if not ids:
            return Response(
                {"detail": "invalid ids"}, status=status.HTTP_400_BAD_REQUEST
            )
        waiting = batch_awaiting_datacap(ids)
        if waiting:
            return Response(
                waiting,
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = models.EmailBatch.objects.filter(id__in=ids)
        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def download_excel(self, request):
        """
        Handle transactions data to download in excel file
        """
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")
        user_timezone = self.request.query_params.get("user_timezone", "UTC")

        self.pagination_class.max_page_size = 100000
        ids = request.data.get("ids", [])
        if ids:
            queryset = self.queryset.filter(id__in=ids)
        else:
            queryset = self.filter_queryset(self.get_queryset())

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(queryset, many=True)

        export_data = []
        for data in serializer.data:
            created_at_utc = str(data["created_at"])
            local_time = self.convert_to_local_time(created_at_utc, user_timezone)
            data["created_at"] = local_time

            updated_at_utc = str(data["updated_at"])
            local_time = self.convert_to_local_time(updated_at_utc, user_timezone)
            data["updated_at"] = local_time

            confirmation_numbers = data["confirmation_numbers"]
            if not confirmation_numbers:
                data["confirmation_numbers"] = ""
                export_data.append(data)
            else:
                for confirmation_number in confirmation_numbers:
                    new_row = data.copy()
                    new_row["confirmation_numbers"] = confirmation_number
                    export_data.append(new_row)

        df = pd.DataFrame(export_data)
        file_name = f"transaction_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"

        response = HttpResponse(content_type="application/xlsx")
        response["Content-Disposition"] = f"attachment; filename={file_name}.xlsx"

        with pd.ExcelWriter(response) as writer:
            df.to_excel(writer, index=False)
        return response

    def convert_to_local_time(self, utc_time_str, user_timezone):
        """
        Convert utc time to local time
        """
        utc_time = datetime.fromisoformat(utc_time_str[:-1])

        if utc_time.tzinfo is None:
            utc_time = pytz.utc.localize(utc_time)

        local_tz = pytz.timezone(user_timezone)
        local_time = utc_time.astimezone(local_tz)
        formatted_time = local_time.strftime("%d/%m/%Y %I:%M:%S %p %z")
        formatted_time = formatted_time[:-2] + ":" + formatted_time[-2:]

        return formatted_time

    def get_queryset(self):
        """
        Customize for viewset to filtering data
        """
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset

        if self.action in ["list", "filter_list", "download_excel"]:
            serializer_class = self.get_serializer_class()
            fields = serializer_class.Meta.fields
            id = self.request.query_params.get("id", None)
            queryset = queryset.only(*fields)

            confirmation_number = self.request.query_params.get(
                "confirmation_number", None
            )
            email_from = self.request.query_params.get("email_from", None)
            email_subject = self.request.query_params.get("email_subject", None)
            matched_profile_name = self.request.query_params.get(
                "matched_profile_name", None
            )
            status = self.request.query_params.get("status", None)
            linked_batch_id = self.request.query_params.get("linked_batch_id", None)
            if self.action == "list":
                project_countries = self.request.query_params.get(
                    "project_countries", None
                )
            elif self.action == "filter_list" or self.action == "download_excel":
                project_countries = self.request.data.get("project_countries", None)
            empty_profiles = models.EmailBatch.objects.filter(
                matched_profile_name=""
            ).only(*fields)
            null_profiles = models.EmailBatch.objects.filter(
                matched_profile_name__isnull=True
            ).only(*fields)
            if id:
                queryset = queryset.filter(id__icontains=id)
                empty_profiles = empty_profiles.filter(id__icontains=id)
                null_profiles = null_profiles.filter(id__icontains=id)
            if confirmation_number:
                # Filter queryset based on partial match in confirmation numbers
                queryset = queryset.filter(
                    Q(confirmation_numbers__icontains=confirmation_number)
                )

                # Also filter empty_profiles and null_profiles similarly if they exist
                empty_profiles = empty_profiles.filter(
                    Q(confirmation_numbers__icontains=confirmation_number)
                )
                null_profiles = null_profiles.filter(
                    Q(confirmation_numbers__icontains=confirmation_number)
                )

            if email_from:
                queryset = queryset.filter(email_from__icontains=email_from)
                empty_profiles = empty_profiles.filter(email_from__icontains=email_from)
                null_profiles = null_profiles.filter(email_from__icontains=email_from)
            if email_subject:
                queryset = queryset.filter(email_subject__icontains=email_subject)
                empty_profiles = empty_profiles.filter(
                    email_subject__icontains=email_subject
                )
                null_profiles = null_profiles.filter(
                    email_subject__icontains=email_subject
                )
            if matched_profile_name:
                queryset = queryset.filter(
                    matched_profile_name__icontains=matched_profile_name
                )
                empty_profiles = empty_profiles.filter(
                    matched_profile_name__icontains=matched_profile_name
                )
                null_profiles = null_profiles.filter(
                    matched_profile_name__icontains=matched_profile_name
                )
            if status:
                queryset = queryset.filter(status__icontains=status)
                empty_profiles = empty_profiles.filter(status__icontains=status)
                null_profiles = null_profiles.filter(status__icontains=status)
            if linked_batch_id:
                ids = list(
                    set(
                        models.EmailToBatchLink.objects.filter(
                            batch_id__startswith=linked_batch_id.strip()
                        ).values_list("email_id", flat=True)
                    )
                )
                queryset = queryset.filter(id__in=ids)
                empty_profiles = empty_profiles.filter(id__in=ids)
                null_profiles = null_profiles.filter(id__in=ids)
            if project_countries:
                query = Q()
                for country_code, project_list in project_countries.items():
                    if not project_list:
                        continue

                    project_query = Q()
                    for project in project_list:
                        project_query |= Q(matched_profile_name__icontains=project)
                    query |= project_query & Q(
                        matched_profile_name__startswith=country_code
                    )
                if query:
                    queryset = queryset.filter(query)
                else:
                    queryset = queryset.none()

            if self.request.user.is_superuser:
                queryset = queryset.union(empty_profiles)
                queryset = queryset.union(null_profiles)
            elif id:
                specific_id = models.EmailBatch.objects.filter(
                    status="failed", id=id
                ).only(*fields)
                queryset = queryset.union(specific_id)

            if not project_countries:
                queryset = queryset.model.objects.none()
        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)
        return queryset

    def get_serializer_class(self):
        """
        select the serializer class to use based on the current request
        """
        actions = ["list", "filter_list", "download_excel"]
        if self.action in actions:
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(EmailBatchViewSet, self).get_serializer_class()


class TrainBatchViewSet(viewsets.ModelViewSet):
    """
    This viewSet for managing 'TrainBatch' model, providing CRUD operations
    integrating with the TrainBatchSerializer for data validation and response
    """

    lookup_value_regex = "[^/]+"
    queryset = models.TrainBatch.objects.all().order_by("id")
    list_serializer_class = serializers.TrainBatchSerializer
    serializer_class = serializers.TrainBatchSerializer
    pagination_class = PaginationMeta

    @action(detail=False, methods=["post"], name="List with POST")
    def filter_list(self, request, *args, **kwargs):
        """
        Handle list retrieval with POST request. This utilizes the overridden
        'get_queryset' method for filtering based on POST data.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["delete"])
    def delete_multiple(self, request):
        """
        Handle multiple trainbatch items to delete
        """
        ids = request.data.get("ids")
        if not ids:
            return Response(
                {"detail": "invalid ids"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Delete link batches then train batch
        link_batches = list(
            models.TrainToBatchLink.objects.filter(train_batch__in=ids).values_list(
                "batch_id", flat=True
            )
        )
        if link_batches:
            batches = models.Batch.objects.filter(id__in=link_batches)
            batches.delete()

        queryset = models.TrainBatch.objects.filter(id__in=ids)
        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """
        Customize for viewset to filtering data
        """
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")

        queryset = self.queryset
        if self.action == "list" or self.action == "filter_list":
            serializer_class = self.get_serializer_class()
            fields = serializer_class.Meta.fields
            id = self.request.query_params.get("id", None)
            queryset = queryset.only(*fields)

            extension_type = self.request.query_params.get("extension_type", None)
            linked_batch_id = self.request.query_params.get("linked_batch_id", None)
            status = self.request.query_params.get("status", None)
            manual_classification_status = self.request.query_params.get(
                "manual_classification_status", None
            )
            matched_profile_name = self.request.query_params.get(
                "matched_profile_name", None
            )

            if self.action == "list":
                project_countries = self.request.query_params.get(
                    "project_countries", None
                )
            elif self.action == "filter_list":
                project_countries = self.request.data.get("project_countries", None)
            empty_profiles = models.TrainBatch.objects.filter(
                matched_profile_name=""
            ).only(*fields)
            null_profiles = models.TrainBatch.objects.filter(
                matched_profile_name__isnull=True
            ).only(*fields)

            if extension_type and extension_type != "all":
                queryset = queryset.filter(Q(file_ext_list__icontains=extension_type))

            if linked_batch_id:
                ids = list(
                    set(
                        models.TrainToBatchLink.objects.filter(
                            batch_id__startswith=linked_batch_id.strip()
                        ).values_list("train_batch_id", flat=True)
                    )
                )
                queryset = queryset.filter(id__in=ids)
                empty_profiles = empty_profiles.filter(id__in=ids)
                null_profiles = null_profiles.filter(id__in=ids)

            if id:
                queryset = queryset.filter(id__icontains=id)
                empty_profiles = empty_profiles.filter(id__icontains=id)
                null_profiles = null_profiles.filter(id__icontains=id)
            if matched_profile_name:
                queryset = queryset.filter(
                    matched_profile_name__icontains=matched_profile_name
                )
                empty_profiles = empty_profiles.filter(
                    matched_profile_name__icontains=matched_profile_name
                )
                null_profiles = null_profiles.filter(
                    matched_profile_name__icontains=matched_profile_name
                )

            customer = self.request.query_params.get("customer", None)
            if customer and customer.strip() and customer.lower() != "null":
                customer_search = customer.strip()
                customer_filter = Q(customer__icontains=customer_search) | Q(custom_data__icontains=customer_search)
                queryset = queryset.filter(customer_filter)
                empty_profiles = empty_profiles.filter(customer_filter)
                null_profiles = null_profiles.filter(customer_filter)

            if status:
                queryset = queryset.filter(status__icontains=status)
                empty_profiles = empty_profiles.filter(status__icontains=status)
                null_profiles = null_profiles.filter(status__icontains=status)

            if manual_classification_status:
                queryset = queryset.filter(
                    manual_classification_status__icontains=manual_classification_status
                )

            if project_countries:
                query = Q()
                for country_code, project_list in project_countries.items():
                    if not project_list:
                        continue

                    project_query = Q()
                    for project in project_list:
                        project_query |= Q(matched_profile_name__icontains=project)
                    query |= project_query & Q(
                        matched_profile_name__startswith=country_code
                    )
                if query:
                    queryset = queryset.filter(query)
                else:
                    queryset = queryset.none()

            # Annotate for customer sorting before union (union doesn't support annotate)
            if sort_by == "customer":
                queryset = queryset.annotate(
                    customer_display=Coalesce("customer", "custom_data", Value(""))
                )
                empty_profiles = empty_profiles.annotate(
                    customer_display=Coalesce("customer", "custom_data", Value(""))
                )
                null_profiles = null_profiles.annotate(
                    customer_display=Coalesce("customer", "custom_data", Value(""))
                )

            if self.request.user.is_superuser and extension_type == "all":
                queryset = queryset.union(empty_profiles)
                queryset = queryset.union(null_profiles)

            if not project_countries:
                queryset = queryset.model.objects.none()
        else:
            # For non-list actions, annotate if sorting by customer
            if sort_by == "customer":
                queryset = queryset.annotate(
                    customer_display=Coalesce("customer", "custom_data", Value(""))
                )

        if sort_by:
            if sort_by == "customer":
                sort_keyword = "-customer_display" if sort_desc == "true" else "customer_display"
            else:
                sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def get_serializer_class(self):
        """
        select the serializer class to use based on the current request
        """
        if self.action == "list" or self.action == "filter_list":
            if hasattr(self, "list_serializer_class"):
                return self.list_serializer_class

        return super(TrainBatchViewSet, self).get_serializer_class()


def sync_options(options, current_options, value_key_dict, new_definition_settings):
    """
    Sync new definition settings with current one
    """
    for option_key in options.keys():
        try:
            value_key = value_key_dict[option_key]

            option_key_items = (
                current_options[option_key]["items"] + options[option_key]["items"]
            )

            new_definition_settings["options"][option_key]["items"] = []
            option_key_items_dict = {}

            for item in option_key_items:
                try:
                    if option_key_items_dict[item[value_key]]:
                        continue
                except:
                    option_key_items_dict[item[value_key]] = item

                    new_definition_settings["options"][option_key]["items"].append(item)
        except:
            pass

    return new_definition_settings


def sync_compound_keys_and_key_qualifiers(
    key, definition_settings, current_definition_settings
):
    """
    Sync compound keys and key qualifiers with current definition settings
    """
    key_value = []
    item_dict = {}

    option_key_dict = {
        "compoundKeys": {
            "option_key": "keyItems",
            "option_item_value_key": "keyValue",
        },
        "keyQualifiers": {
            "option_key": "options",
            "option_item_value_key": "value",
        },
    }

    option_key = option_key_dict[key]["option_key"]
    option_item_value_key = option_key_dict[key]["option_item_value_key"]

    for item in current_definition_settings[key]:
        item_dict[item["name"]] = item

    for item in definition_settings[key]:
        try:
            current_item = item_dict.pop(item["name"])
            item[option_key] = current_item[option_key] + item[option_key]

            option_key_item_dict = {}
            option_key_items = []

            for option_key_item in item[option_key]:
                try:
                    if option_key_item_dict[option_key_item[option_item_value_key]]:
                        continue
                except:
                    option_key_item_dict[option_key_item[option_item_value_key]] = (
                        option_key_item
                    )
                    option_key_items.append(option_key_item)
            item[option_key] = option_key_items
        except:
            pass

        key_value.append(item)

    for k in item_dict:
        key_value.append(item_dict[k])

    return key_value


def sync_definition_settings(project, definition_settings):
    """
    Sync new definition settings with the current one
    """
    current_definition_settings = project.definition_settings
    new_definition_settings = {**definition_settings}

    for key in definition_settings.keys():
        if key == "options":
            value_key_dict = {
                "options-keys": "keyValue",
                "options-col-type": "type",
                "options-col-modType": "modType",
                "options-meta-root-type": "docType",
            }

            new_definition_settings = sync_options(
                definition_settings[key],
                current_definition_settings[key],
                value_key_dict,
                new_definition_settings.copy(),
            )
        if key in ["compoundKeys", "keyQualifiers"]:
            new_definition_settings[key] = sync_compound_keys_and_key_qualifiers(
                key, definition_settings, current_definition_settings
            )

    return new_definition_settings


@api_view(["POST"])
def import_application_settings(request):
    """
    Import appication settings to AIDB system
    """
    try:
        application_settings = request.data["application_settings"]
        overwrite = request.data["overwrite"]

        if not isinstance(application_settings, dict):
            raise
    except:
        print(f"{request=}")
        print(f"{request.data=}")
        traceback.print_exc()
        return Response(
            {"detail": "invalid payload (project, application_settings)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = models.ApplicationSettings.objects.all()

    if qs.exists():
        instance = qs.first()

        if overwrite:
            new_application_settings = application_settings
        else:
            current_application_settings = instance.data
            new_application_settings = {**application_settings}

            for key in application_settings.keys():
                if key == "options":
                    value_key_dict = {
                        "options-page-type": "pageType",
                        "options-info-holder": "name",
                    }

                    new_application_settings = sync_options(
                        application_settings[key],
                        current_application_settings[key],
                        value_key_dict,
                        new_application_settings.copy(),
                    )

        instance.data = new_application_settings

        instance.save()
    else:
        instance = models.ApplicationSettings.objects.create(data=application_settings)

    serialize_data = serializers.ApplicationSettingsSerializer(instance).data

    return Response(
        {
            "data": serialize_data,
            "detail": "Application Settings imported",
        }
    )


@api_view(["GET"])
def get_definition_settings(request):
    """
    Get definition settings based on valid project
    """
    project_name = request.query_params.get("project")

    if not project_name:
        return Response(
            {"detail": "invalid project name"}, status=status.HTTP_400_BAD_REQUEST
        )

    qs = Project.objects.filter(name=project_name)

    if qs.exists():
        project = qs.first()
        serialize_data = ProjectSerializer(project).data

        return Response(serialize_data["settings"])
    else:
        return Response(
            {"detail": "Definition Settings not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
def update_definition_settings(request):
    """
    Update the definition settings with respect to the project
    """
    try:
        project_name = request.data["project"]
        # removes any null characters in incoming definition_settings
        definition_settings = clean_definition_settings(
            request.data["definition_settings"]
        )
    except:
        print(f"{request=}")
        print(f"{request.data=}")
        traceback.print_exc()
        return Response(
            {"detail": "invalid payload (project, definition_settings)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = Project.objects.filter(name=project_name)

    if qs.exists():
        project = qs.first()

        project.definition_settings = definition_settings

        project.save()

        serialize_data = ProjectSerializer(project).data

        return Response(
            {
                "data": serialize_data["definition_settings"],
                "detail": "Definition Settings updated",
            }
        )
    else:
        return Response(
            {"detail": "Definition Settings not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
def import_definition_settings(request):
    """
    Import definition settings to AIDB system
    """
    try:
        project_name = request.data["project"]
        # removes any null characters in incoming definition_settings
        definition_settings = clean_definition_settings(
            request.data["definition_settings"]
        )
        overwrite = request.data["overwrite"]
    except:
        print(f"{request=}")
        print(f"{request.data=}")
        traceback.print_exc()
        return Response(
            {"detail": "invalid payload (project, definition_settings)"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    qs = Project.objects.filter(name=project_name)

    if qs.exists():
        project = qs.first()

        if overwrite:
            new_definition_settings = definition_settings
        else:
            new_definition_settings = sync_definition_settings(
                project, definition_settings
            )

        project.definition_settings = new_definition_settings

        project.save()

        serialize_data = ProjectSerializer(project).data

        return Response(
            {
                "data": serialize_data["definition_settings"],
                "detail": "Definition Settings imported",
            }
        )
    else:
        return Response(
            {"detail": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
def batch_status(request, batch_id):
    """Get batch status for a specific batch ID"""
    queryset = models.BatchStatus.objects.filter(batch_id=batch_id).order_by(
        "-event_time"
    )[:100]
    serializer = serializers.BatchStatusSerializer(queryset, many=True)
    return Response(serializer.data)

def reduce_data_json_for_output_json(data_json):
    simplified_data = {}
    simplified_data["tables"] = []
    for document in data_json.get("nodes", []):
        simplified_data["Document Issuer"] = document.get("Vendor")
        for node in document.get("children", []):
            try:
                if node.get("type") == "key":
                    for key_object in node.get("children", []):
                        if key_object.get("notInUse"):
                            continue
                        try:
                            if key_object["v"]:
                                if key_object.get("children",[]):
                                    sub_key_data = []
                                    for sub_key in key_object["children"]:
                                        try: 
                                            if sub_key["v"]:
                                                sub_key_data.append({sub_key["label"]: sub_key["v"]})
                                        except:
                                            continue
                                    simplified_data[key_object["label"]] = sub_key_data
                                else:
                                    if key_object.get("qualifierParent"):
                                        qualifier = key_object.get("qualifierParent")
                                        if qualifier not in simplified_data.keys():
                                            simplified_data[qualifier] = []
                                        simplified_data[qualifier].append({key_object.get("label"):key_object.get("v")})
                                    else:
                                        simplified_data[key_object["label"]] = key_object["v"]
                        except:
                            continue

                elif node.get("type") == "table":
                    table_data = {}
                    table_data["table_name"] = node.get("table_name")
                    table_data["data"] = []
                    for row in node.get("children", []):
                        row_data = {}
                        for cell in row.get("children", []):
                            label = cell["label"]
                            if check_skipped_labels(label):
                                continue
                            try:
                                if cell.get("v"): row_data[cell["label"]] = cell["v"]
                            except: 
                                continue
                        table_data["data"].append(row_data)

                    if not table_data.get("data"):
                        continue
                    
                    if table_data not in simplified_data["tables"]:
                        simplified_data["tables"].append(table_data)
                else:
                    continue
            except:
                import traceback
                print(traceback.print_exc())
                continue

    return simplified_data

def check_skipped_labels(label):
    """Check if label is in skip labels"""
    if label and label.lower() in ["None", "notInUse", "", "filler"]:
        return True
    return False

def simplify_data_json(batch_id):
    """Simplify data json for output-aidb-model"""
    batch = models.Batch.objects.get(id=batch_id)
    data_json = batch.data_json
    simplified_data = reduce_data_json_for_output_json(data_json)
    return simplified_data

@api_view(["GET"])
def all_batches(request):
    """Returns all batches without pagination."""
    queryset = models.Batch.objects.all()
    serializer = serializers.BatchListSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def search_definition(request):
    """
    Search definition by definition ID, type, name matching text, definition version
    """
    definition_id = request.query_params.get("definition_id")
    if not definition_id:
        return Response(
            {"detail": "invalid definition_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    definition_version = request.query_params.get("definition_version")
    if not definition_version:
        return Response(
            {"detail": "invalid definition_version"}, status=status.HTTP_400_BAD_REQUEST
        )
    layout_id = request.query_params.get("layout_id", None)
    if not layout_id:
        return Response(
            {"detail": "invalid layout_id"}, status=status.HTTP_400_BAD_REQUEST
        )
    qs = models.Definition.objects.filter(definition_id__iexact=definition_id).filter(
        layout_id__iexact=layout_id
    )

    if qs.exists():
        definition = qs.first()
        definition = serializers.DefinitionSerializer(definition).data

        if not (definition_version in definition["data"].keys()):
            raise ValueError(f"Definition not found for version {definition_version}")

        # Filter definition version
        filtered_data = definition["data"][definition_version]
        del definition["data"]
        definition.update(filtered_data)

        # # Add type_seq_no
        # qs = (
        #     models.Definition.objects.filter(definition_id__iexact=definition_id)
        #     .filter(type__iexact=type)
        #     .order_by("created_at")
        # )

        # if qs.count() > 1:
        #     type_seq_no = 0
        #     for i in qs:
        #         type_seq_no += 1
        #         if i.name_matching_text == definition["name_matching_text"]:
        #             break
        #     definition["type_seq_no"] = type_seq_no
        # else:
        #     definition["type_seq_no"] = 0

        return Response(definition)
    else:
        return Response(
            {"detail": "Definition not found"}, status=status.HTTP_404_NOT_FOUND
        )


def get_max_column_length(data):
    """
    Findout the maximum length of a dictionary
    """
    max_length = 0
    for column in data.values():
        column_length = len(column)

        if column_length > max_length:
            max_length = column_length

    return int(max_length)


def get_cells_from_workbook(data, start: int, end: int):
    """
    Get cells from exel workbook
    """
    try:
        result = {}

        for column, cells in data.items():
            sorted_cells = sorted(cells.keys(), key=int)[start:end]
            result[column] = {cell: cells[cell] for cell in sorted_cells}
        return result

    except Exception:
        print(traceback.format_exc())


@api_view(["GET"])
def get_excel_workbook(request):
    """Get excel workbook based on batch ID, document ID, workbook ID"""
    try:
        batch_id = request.query_params.get("batch_id")
        document_id = request.query_params.get("document_id")
        workbook_id = request.query_params.get("workbook_id")
        page_size = int(request.query_params.get("page_size", 10))
        page_number = int(request.query_params.get("page_number", 1))
        if not batch_id:
            raise ValueError("batch_id is a required field.")
        if not document_id:
            raise ValueError("document_id is a required field.")
        if not workbook_id:
            raise ValueError("workbook_id is a required field.")

        start = ((page_number - 1) * page_size) if page_number > 1 else 0
        end = page_number * page_size

        ra_json = models.Batch.objects.get(id=batch_id).ra_json
        nodes = ra_json["nodes"]
        document = None
        for node in nodes:
            if node["id"] != document_id:
                continue
            document = node["children"]
            break

        if not document:
            raise ValueError(
                f"The document {document_id} does not exist in batch {batch_id}"
            )
        for _workbook in document:
            if _workbook["id"] == workbook_id:
                workbook = _workbook["cell_data"]
                break

        results = get_cells_from_workbook(data=workbook, start=start, end=end)
        max_column_size = get_max_column_length(data=workbook)
        max_pages = (max_column_size + page_size - 1) // page_size

        # if int(page_number) > int(max_pages):
        #     raise ValueError("Page number exceeds max page number.")

        return Response(
            {
                "max_pages": max_pages,
                "current_page": page_number,
                "results": results,
            }
        )
    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def prepare_excel_ra_json(doc):
    """
    Helper function to prepare excel for RA json
    """
    for child in doc["children"]:
        child["cell_data"] = {}

    return doc


def get_ra_json_data(ra_json, document_id):
    """Retrieve RA JSON data for a specified document ID."""
    try:
        if document_id:
            # Filter nodes to include only the node with the specified document_id
            filtered_nodes = []
            total_pages = 0
            for node in ra_json["nodes"]:
                # Check if the current node's id matches the document_id
                if node["id"] == document_id:
                    # If children exist, convert them to pages and clear children
                    if "children" in node and node["children"]:
                        pages = []
                        for child in node["children"]:
                            # Extract IMAGEFILE if it exists
                            imagefile = child.get("IMAGEFILE") or child.get("imageFile")
                            if imagefile:
                                pages.append(
                                    {"IMAGEFILE": imagefile, "id": child["id"]}
                                )
                        # Set the node's children to empty and add pages list
                        node["children"] = []
                        node["pages"] = pages
                        total_pages += len(pages)
                    # Append the node to filtered nodes
                    filtered_nodes.append(node)

            # Update the original ra_json with filtered nodes and total pages
            ra_json["nodes"] = filtered_nodes
            ra_json["total_pages"] = total_pages
        return ra_json
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        # Optionally print details to help locate the error
        print(f"Error at line {e.lineno}, column {e.colno}")


@api_view(["GET"])
def get_ra_json(request):
    """Retrieve RA JSON for a specified document ID from a valid batch."""
    batch_id = request.query_params.get("batch_id")
    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    document_id = request.query_params.get("document_id")
    try:
        ra_json = models.Batch.objects.get(id=batch_id).ra_json

        if document_id:
            # Filterout other (not required) document nodes.
            ra_json = deepcopy(ra_json)

            # Calculating total pages & Filtering ra_json for specific document
            total_pages = 0
            new_nodes = []
            for doc in ra_json["nodes"]:
                if doc["id"] == document_id:
                    if doc["ext"] == ".xlsx":
                        prepare_excel_ra_json(doc)
                    new_nodes.append(doc)

                for node in doc["children"]:
                    if node["type"] == "page":
                        total_pages += 1
            ra_json["total_pages"] = total_pages
            ra_json["nodes"] = new_nodes
        ra_json = get_ra_json_data(ra_json, document_id)

        return Response(ra_json)

    except:
        print(traceback.format_exc())
        return Response(
            {"detail": "Error Fetching RA Json"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def find_node_by_id(nodes, node_id):
    """
    Helper function to find a node by its ID.
    """
    for node in nodes:
        if node.get("id") == node_id:
            return node
    return None


def get_page_data(ra_json, document_id, page_id):
    """Fetches page data using RA JSON nodes based on the document_id and page_id."""
    try:
        # Validate input
        if not document_id:
            return {}

        # Find the document node
        document_node = find_node_by_id(ra_json.get("nodes", []), document_id)
        if not document_node or not page_id:
            return {}

        # Find the page within the document
        page_data = find_node_by_id(document_node.get("children", []), page_id)
        return page_data or {}

    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}. Line: {e.lineno}, Column: {e.colno}")
        return {}


@api_view(["GET"])
def get_ra_json_page_data(request):
    """Fetching RA json page data using batch ID, document ID and page ID."""
    batch_id = request.query_params.get("batch_id")
    # converting string to list
    page_ids = request.query_params.get("page_ids", []).split(",")
    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    document_id = request.query_params.get("document_id")

    page_data = []
    try:
        ra_json = models.Batch.objects.get(id=batch_id).ra_json
        for page_id in page_ids:
            page_data.append(get_page_data(ra_json, document_id, page_id))
        return Response(page_data)

    except:
        print(traceback.format_exc())
        return Response(
            {"detail": "Error Fetching RA Json"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def process_table(table):
    """
    Process rowwise table data
    """
    table_rows = table["children"]
    rows = []
    for row in table_rows:
        result_row = {}
        cells = row["children"]
        for cell in cells:
            result_row[cell["label"]] = cell["v"]
        rows.append(result_row)
    result = {
        "table_id": table["id"],
        "table_items": rows,
    }
    return result


def process_document(document):
    """
    Process a document and return keys, tables details
    """
    document_items = document["children"]
    tables = [i for i in document_items if i["type"] == "table"]
    table_data = [process_table(t) for t in tables]
    keys = [i for i in document_items if i["type"] == "key"]
    if keys:
        keys_data = {k["label"]: k["v"] for k in keys[0]["children"]}
    else:
        keys_data = {}
    return {"document_id": document["id"], "keys": keys_data, "tables": table_data}


@api_view(["GET"])
def simple_data_json(request):
    """Return specific batch data to json format"""
    batch_id = request.query_params.get("batch_id")
    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        batch = models.Batch.objects.get(id=batch_id)
        data_json = batch.data_json

        docs = data_json["nodes"]
        docs_data = [process_document(doc) for doc in docs]
        result = {
            "batch_id": batch_id,
            "definition_id": batch.definition_id,
            "type": batch.type,
            "vendor": batch.vendor,
            "documents": docs_data,
        }
        return Response({"data_json": result})
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


DOWNLOAD_FILE_TYPES = ["output", "automated_table_model", "definition_fields", "output_aidb_model"]


@api_view(["GET"])
def retrive_json(request):
    """This function handle to retribe necessary json files from batch path"""
    batch_id = request.query_params.get("batch_id")
    file_type = request.query_params.get("file_type")
    file_name = request.query_params.get("file_name", "")
    transaction_id = request.query_params.get("transaction_id", "")
    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    if file_type not in DOWNLOAD_FILE_TYPES:
        return Response(
            {
                "detail": "invalid file_type. it should be one of the following: {DOWNLOAD_FILE_TYPES}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        batch_instance = models.Batch.objects.get(id=batch_id)
        batch_path = os.path.join(BATCH_INPUT_PATH, batch_instance.sub_path, batch_id)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, batch_instance.sub_path, batch_id)

        if file_type == "output":
            output_file = os.path.join(batch_path, "output.json")
        elif file_type == "output_aidb_model":
            batch_type = models.Batch.objects.get(id=batch_id).mode
            # If batch mode is "train", the table to query is TrainToBatchLink else EmailToBatchLink Table
            if batch_type == "training":
                if not transaction_id:
                    transaction_id = list(
                        models.TrainToBatchLink.objects.filter(batch_id=batch_id).values_list(
                            "train_batch", flat=True
                        )
                    )
                linked_batches = list(
                    models.TrainToBatchLink.objects.filter(train_batch__in=transaction_id).values_list(
                        "batch_id", flat=True
                        )
                    )
            else:
                if not transaction_id:
                    transaction_id = list(
                        models.EmailToBatchLink.objects.filter(batch_id=batch_id).values_list(
                            "email", flat=True
                        )
                    )
                linked_batches = list(
                    models.EmailToBatchLink.objects.filter(email_id__in=transaction_id).values_list(
                        "batch_id", flat=True
                        )
                    )
         
            data = {}
            # Generate simplified data json for output-aidb-model
            for batch in linked_batches:
                simplified_data = simplify_data_json(batch)
                data[batch] = simplified_data
            
            return Response(data)
        elif file_type == "automated_table_model":
            output_file = os.path.join(batch_path, "automated_table_model.json")
        else:
            if file_name:
                assert file_name.startswith("definition_fields") is True
                assert file_name.endswith(".json") is True
            else:
                # Note: Erlier, definition fields were being saved to same file everytime.
                file_name = "definition_fields.json"
            output_file = os.path.join(batch_path, file_name)

        with open(output_file, "r") as f:
            data = json.loads(f.read())

        return Response(data)
    except Exception as error:
        import traceback
        print(traceback.print_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def download_djson_excel(request):
    """Download data json excel file from batch path using batch ID"""
    batch_id = request.query_params.get("batch_id")

    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        batch_instance = models.Batch.objects.get(id=batch_id)
        batch_path = os.path.join(BATCH_INPUT_PATH, batch_instance.sub_path, batch_id)

        if batch_instance.is_dataset_batch and ".U" not in batch_id:
            batch_path = os.path.join(DATASET_BATCH_INPUT_PATH, batch_instance.sub_path, batch_id)

        d_json_file = os.path.join(batch_path, "d_json.xlsx")

        with open(d_json_file, "rb") as f:
            excel_content = f.read()

        file_name = f"djson-{batch_id}"

        response = HttpResponse(
            excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename={file_name}.xlsx"
        return response

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET", "POST"])
def defined_keys(request):
    """Update defined keys for a specific profile ID (definition_id)"""
    try:
        if request.method == "GET":
            definition_id = request.query_params.get("definition_id")

            if not definition_id:
                return Response(
                    {"detail": "invalid definition_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            qs = models.DefinedKey.objects.filter(definition_id=definition_id)
            data = serializers.DefinedKeySerializer(qs, many=True).data
            return Response({"items": data})

        if request.method == "POST":
            definition_id = request.data.get("definition_id")
            if not definition_id:
                return Response(
                    {"detail": "invalid definition_id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            deleted_items = request.data.get("deleted_items", [])
            if deleted_items:
                models.DefinedKey.objects.filter(id__in=deleted_items).delete()

            items = request.data.get("items", [])

            # Handle each Definedkey Item separately
            for item in items:
                if item["id"]:
                    # Update item if it already exists
                    kwargs = {
                        "label": item["label"],
                        "data": item["data"],
                    }
                    instance = models.DefinedKey.objects.get(id=item["id"])
                    for attr, value in kwargs.items():
                        setattr(instance, attr, value)
                    instance.save()
                else:
                    # Create new Item
                    kwargs = {
                        "definition_id": definition_id,
                        "label": item["label"],
                        "data": item["data"],
                    }
                    models.DefinedKey.objects.create(**kwargs)

            return Response({"detail": "DefinedKeys Updated"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def copy_definition_data(request):
    """Copy definition data (table/key) from one version to another"""
    try:
        id = request.query_params.get("id")
        template = request.query_params.get("template", None)
        if not id and not template:
            return Response(
                {"detail": "invalid id"}, status=status.HTTP_400_BAD_REQUEST
            )

        key = request.query_params.get("key")
        if not key:
            return Response(
                {"detail": "invalid key"}, status=status.HTTP_400_BAD_REQUEST
            )

        table = request.query_params.get("table")
        if not table:
            return Response(
                {"detail": "invalid table"}, status=status.HTTP_400_BAD_REQUEST
            )

        from_version = request.query_params.get("from_version")
        if not table:
            return Response(
                {"detail": "invalid from_version"}, status=status.HTTP_400_BAD_REQUEST
            )

        to_version = request.query_params.get("to_version")
        if not table:
            return Response(
                {"detail": "invalid to_version"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if template:
                template = Template.objects.get(template_name=template)
                data = template.definition
            else:
                definition = models.Definition.objects.get(id=id)
                data = definition.data
        except models.Definition.DoesNotExist:
            return Response(
                {"detail": "Definition with provided id doesn't exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if from_version not in data.keys():
            return Response(
                {
                    "detail": f"Definition for from_version '{from_version}' doesn't exists"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if to_version not in data.keys():
            return Response(
                {
                    "detail": f"Definition for from_version '{to_version}' doesn't exists"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if key == "true":
            data[to_version]["key"] = data[from_version]["key"]
        if table == "true":
            data[to_version]["table"] = data[from_version]["table"]

        if template:
            template.definition = data
            template.save()
        else:
            definition.data = data
            definition.save()

        return Response({"detail": "Definition data copied"})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_definitions_by_profile(request):
    """
    Returns filtered definitions by profile id (definition_id) if prod definition is not empty.
    """
    try:
        definition_id = request.query_params.get("definition_id")
        if not definition_id:
            return Response(
                {"detail": "invalid definition_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get definitions by profile ID
        definitions_qs = models.Definition.objects.filter(
            definition_id__iexact=definition_id
        )
        if not definitions_qs.exists():
            return Response(
                {"detail": "Definition with provided definition_id doesn't exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            definition_objs = definitions_qs.all()

        definitions = []
        definitions_missing_prod = []

        # Check if prod definition exists in each definitions
        for definition_obj in definition_objs:
            def_data = serializers.DefinitionSerializer(definition_obj).data

            identifier = f"{def_data['definition_id']} - {def_data['type']}"
            if not ("prod" in def_data["data"].keys()):
                definitions_missing_prod.append(identifier)
                continue

            # Filter definition version by prod to check if its empty
            filtered_data = def_data["data"]["prod"]
            if filtered_data["table"] == {} and filtered_data["key"] == {}:
                definitions_missing_prod.append(identifier)
                continue

            definitions.append(def_data)

        if definitions_missing_prod:
            return Response(
                {
                    "detail": f"Following definitions are missing prod versions: {definitions_missing_prod}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response({"definitions": definitions})

    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def update_table_models_by_definition(request):
    """
    Update specific table's models of a specific definition.
    """
    print("Request received: update_table_models_by_definition")
    try:
        try:
            definition_id = request.data["definition_id"]
            vendor = request.data["vendor"]
            definition_version = request.data["definition_version"]
            table_unique_id = request.data["table_unique_id"]
            model = request.data["model"]
        except:
            print(f"{request=}")
            print(f"{request.data=}")
            traceback.print_exc()
            return Response(
                {
                    "detail": "invalid payload (definition_id, vendor, definition_version, table_unique_id, model)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not models.ApplicationSettings.objects.exists():
            return Response({"message": "Definition Settings Not Found."})

        application_settings = models.ApplicationSettings.objects.first().data
        table_settings = application_settings["tableSettings"]

        model_fields = [field["key"] for field in table_settings["model"]["fields"]]

        definition_qs = models.Definition.objects.filter(
            definition_id__iexact=definition_id
        ).filter(layout_id__iexact=layout_id)

        if definition_qs.exists():
            definition_obj = definition_qs.first()
            data = definition_obj.data

            tables = data[definition_version]["table"]

            missing_fields = []

            for index, table in enumerate(tables):
                if table["table_unique_id"] == table_unique_id:
                    for field in model.keys():
                        if field in model_fields:
                            tables[index]["table_definition_data"]["models"][field] = (
                                model[field]
                            )
                        else:
                            missing_fields.append(field)
                    break

            if len(missing_fields):
                return Response(
                    {
                        "message": "Definition Not Updated.",
                        "detail": f"{missing_fields} {'this field is' if len(missing_fields) == 1 else 'these fields are'} not found in table models.",
                    }
                )

            data[definition_version]["table"] = tables

            definition_obj.data = data
            definition_obj.save()

            definition = serializers.DefinitionSerializer(definition_obj).data

            return Response(
                {"message": "Definition Succesfully Updated.", "definition": definition}
            )
        else:
            return Response({"message": "Definition Not Found."})
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def all_definitions(request):
    """Returns all definitions without pagination"""
    try:
        project_countries = request.data.get("project_countries", None)

        queryset = models.Definition.objects.all()

        if project_countries:
            query = Q()
            for country_code, project_list in project_countries.items():
                if not project_list:
                    continue

                project_query = Q()
                for project in project_list:
                    project_query |= Q(definition_id__icontains=project)
                query |= project_query & Q(definition_id__startswith=country_code)
            if query:
                queryset = queryset.filter(query)
            else:
                queryset = queryset.none()

        if not project_countries:
            queryset = queryset.model.objects.none()

        serialize_data = serializers.DefinitionSerializer(queryset, many=True).data

        all_definitions = [dict(item)["definition_id"] for item in serialize_data]

        all_definitions = list(set(all_definitions))

        return Response(all_definitions)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_types_by_definition(request):
    """
    Returns all types without pagination by definition
    """
    try:
        definition_id = request.query_params.get("definition_id", None)

        if not definition_id:
            return Response(
                {"detail": "invalid definition_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        queryset = models.Definition.objects.filter(
            definition_id__iexact=definition_id
        ).order_by("created_at")

        serialize_data = serializers.DefinitionSerializer(queryset, many=True).data

        all_types = [dict(item)["type"] for item in serialize_data]

        definition_type_dict = {}

        for item in all_types:
            count = definition_type_dict.get(item, 0)
            definition_type_dict[item] = count + 1

        all_types = []

        for key, value in definition_type_dict.items():
            if value == 1:
                all_types.append(key)
                continue

            for i in range(value):
                all_types.append(f"{key} {i + 1}")

        return Response(all_types)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
def get_batches_by_definition_type(request):
    """
    Returns all batches without pagination by definition type
    """
    try:
        definition_id = request.query_params.get("definition_id", None)
        definition_type = request.query_params.get("definition_type", None)
        batch_type = request.query_params.get("batch_type", None)
        batch_id = request.query_params.get("batch_id", None)

        if not definition_id or not definition_type:
            return Response(
                {"detail": "invalid payload"}, status=status.HTTP_400_BAD_REQUEST
            )

        serial_no = definition_type.split(" ")[-1]

        try:
            serial_no = int(serial_no)
            type = " ".join(definition_type.split(" ")[:-1])
        except:
            serial_no = 1
            type = definition_type

        definition_qs = (
            models.Definition.objects.filter(definition_id__iexact=definition_id)
            .filter(type__iexact=type)
            .order_by("created_at")
        )

        if definition_qs.count() >= serial_no:
            definition_qs = definition_qs[serial_no - 1]

        name_matching_text = definition_qs.name_matching_text

        batches = list()
        latest_batches = list()
        all_batches_qs = models.Batch.objects.filter(
            definition_id__iexact=definition_id,
            type__iexact=type,
            name_matching_text__iexact=name_matching_text,
        ).order_by("-created_at")

        if batch_id:
            all_batches_qs = all_batches_qs.exclude(id=batch_id)
            latest_batches = list(
                all_batches_qs.only("id")[:49].values_list("id", flat=True)
            )
            latest_batches.append(batch_id)

        else:
            latest_batches = list(
                all_batches_qs.only("id")[:50].values_list("id", flat=True)
            )

        if not batch_type:
            # Check parent batch available in TrainToBatchLink
            link_batches = list(
                models.TrainToBatchLink.objects.filter(
                    batch_id__in=latest_batches
                ).values_list("batch_id", flat=True)
            )
            batches = link_batches

        else:
            if batch_type == "email":
                batches = latest_batches

        return Response(batches)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def latest_batch_info(request):
    """
    Returns latest batch id
    """
    project_countries = request.data.get("project_countries", None)
    definition_id = request.data.get("definition_id", None)

    try:
        queryset = models.Batch.objects.all()

        if project_countries:
            query = Q()
            for country_code, project_list in project_countries.items():
                if not project_list:
                    continue

                project_query = Q()
                for project in project_list:
                    project_query |= Q(definition_id__icontains=project)
                query |= project_query & Q(definition_id__startswith=country_code)
            if query:
                queryset = queryset.filter(query)
            else:
                queryset = queryset.none()

        if not project_countries:
            queryset = queryset.model.objects.none()

        if definition_id:
            queryset = queryset.filter(definition_id__iexact=definition_id)

        queryset = queryset.latest("created_at")

        return Response(
            {
                "batch_id": queryset.id,
                "definition_id": queryset.definition_id,
            }
        )
    except models.Batch.DoesNotExist:
        return Response({"batch_id": None})


@api_view(["GET"])
def check_batch_availability(request):
    """
    Returns true / false based on batch available on database
    """
    batch_id = request.query_params.get("batch_id", None)

    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        batch = models.Batch.objects.get(id=batch_id)

        return Response(
            {
                "available": True,
                "definition_id": batch.definition_id,
            }
        )
    except models.Batch.DoesNotExist:
        return Response({"available": False})


@api_view(["GET"])
def get_train_batch_ra_json(request):
    """Get train batch RA JSON by batch ID"""
    batch_id = request.query_params.get("batch_id")

    if not batch_id:
        return Response(
            {"detail": "invalid batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        ra_json = models.TrainBatch.objects.get(id=batch_id).ra_json

        return Response(ra_json)

    except:
        return Response(
            {"detail": "Error Fetching RA Json"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_assembled_results(request):
    """Get Transaction Assembled Results"""
    email_batch_id = request.query_params.get("email_batch_id")
    type = request.query_params.get("type", "assembled")

    if not email_batch_id:
        return Response(
            {"detail": "invalid email_batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        assembled_results = models.EmailBatch.objects.get(
            id=email_batch_id
        ).assembled_results

        if type == "payload":
            assembled_results = [i["data"] for i in assembled_results]

        return Response(assembled_results)
    except:
        return Response(
            {"detail": "Error Fetching Assembled Results"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_api_responses(request):
    """Get Transaction API responses"""
    email_batch_id = request.query_params.get("email_batch_id")
    type = request.query_params.get("type", "api")
    status = request.query_params.get("status", "success")

    if not email_batch_id:
        return Response(
            {"detail": "invalid email_batch_id"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        db_api_responses = models.EmailBatch.objects.get(id=email_batch_id).api_response

        api_responses = []
        response_json_key = "response_json"
        status_code_key = "status_code"

        if type == "doc":
            response_json_key = "uploaded_doc_response_json"
            status_code_key = "uploaded_doc_status_code"

        if type == "timestamp_api":
            for item in db_api_responses:
                timestamp_api_responses = item.get("timestamp_api_response", [])

                for i in timestamp_api_responses:
                    if status == "success" and i.get(status_code_key) != 200:
                        continue

                    if status == "failed" and i.get(status_code_key) == 200:
                        continue

                    api_responses.append(i)
        else:
            for item in db_api_responses:
                if status == "success" and item.get(status_code_key) != 200:
                    continue

                if status == "failed" and item.get(status_code_key) == 200:
                    continue

                if item.get(response_json_key):
                    api_responses.append(
                        {
                            **item[response_json_key],
                            "status_code": item[status_code_key],
                        }
                    )

        return Response(api_responses)
    except:
        return Response(
            {"detail": "Error Fetching API Responses"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ProfileTrainingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing profile training data with status information
    """

    lookup_value_regex = "[^/]+"
    queryset = (
        models.Batch.objects.filter(mode="training")
        .only("definition_id", "status")
        .order_by("id")
    )
    serializer_class = None  # Add your serializer if needed
    pagination_class = PaginationMeta

    @action(detail=False, methods=["post"], name="List with POST")
    def filter_list(self, request, *args, **kwargs):
        """
        Handle list retrieval with POST request
        """
        queryset = self.filter_queryset(self.get_queryset())
        processed_data = self.process_queryset_data(queryset)
        page = self.paginate_queryset(processed_data)

        if page is not None:
            return self.get_paginated_response(page)

        return Response(processed_data)

    def process_queryset_data(self, queryset):
        """
        Process queryset data to get profile statuses
        """
        profile_statuses = {}
        data = []
        status = self.request.query_params.get("status", None)
        # Group statuses by profile
        for item in queryset:
            profile = item.definition_id
            _status = item.status
            if profile not in profile_statuses:
                profile_statuses[profile] = set()
            profile_statuses[profile].add(_status)

        # Create final data structure maintaining priority order
        for profile, statuses in profile_statuses.items():
            if "failed" in statuses:
                data.append({"profile": profile, "status": "failed"})
            elif "inprogress" in statuses:
                data.append({"profile": profile, "status": "inprogress"})
            elif "completed" in statuses:
                data.append({"profile": profile, "status": "completed"})

        if status:
            #
            data = [
                profile
                for profile in data
                if profile["status"].startswith(status.lower())
            ]
            print(status, data)
        return data

    def get_queryset(self):
        """
        this fucntion does further filtering and sorting before returning the queryset
        """
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")
        definition_id = self.request.query_params.get("definition_id", None)
        extension = self.request.query_params.get("extension_type", None)
        linked_batch_id = self.request.query_params.get("linked_batch_id", None)

        queryset = self.queryset

        # filters the results with currently available profiles
        if linked_batch_id:
            print(linked_batch_id)
            queryset = queryset.filter(id__icontains=linked_batch_id)
        if extension and extension != "all":
            queryset = queryset.filter(extension=extension)

        queryset = queryset.filter(
            Q(definition_id__in=Profile.objects.values_list("name", flat=True))
        ).filter(
            Q(id__in=models.TrainToBatchLink.objects.values_list("batch_id", flat=True))
        )
        if definition_id:
            queryset = queryset.filter(definition_id__icontains=definition_id)

        project_countries = self.request.data.get("project_countries", None)

        if project_countries:
            query = Q()
            for country_code, project_list in project_countries.items():
                if not project_list:
                    continue

                project_query = Q()
                for project in project_list:
                    project_query |= Q(definition_id__icontains=project)
                query |= project_query & Q(definition_id__startswith=country_code)
            if query:
                queryset = queryset.filter(query)
            else:
                queryset = queryset.none()

        # Apply sorting
        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset


@api_view(["DELETE"])
def delete_from_profile_training(request):
    try:
        batch_ids = request.data.get("batch_ids", [])

        if not batch_ids:
            return Response(
                {"error": "No batch IDs provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Get parent batch IDs before deletion
            parent_batch_ids = set(
                models.TrainToBatchLink.objects.filter(
                    batch_id__in=batch_ids
                ).values_list("train_batch", flat=True)
            )
            # Create timeline log entries for each batch_id that gets deleted
            for batch_id in batch_ids:
                parent_batch_id = (
                    models.TrainToBatchLink.objects.filter(batch_id=batch_id)
                    .values_list("train_batch", flat=True)
                    .first()
                )
                write_parent_batch_log(
                    message=f"Batch {batch_id} was deleted successfully!",
                    batch_id=parent_batch_id,
                    status="incomplete",
                )
            # Delete the specified batches and train to batch links
            models.TrainToBatchLink.objects.filter(batch_id__in=batch_ids).delete()
            models.Batch.objects.filter(id__in=batch_ids).delete()[0]

            parents_deleted = 0
            if parent_batch_ids:
                # Find and delete parent batches that have no remaining children
                empty_parents = models.TrainBatch.objects.filter(
                    id__in=parent_batch_ids
                ).exclude(
                    id__in=models.TrainToBatchLink.objects.values_list(
                        "train_batch_id", flat=True
                    )
                )
                print(empty_parents)
                empty_parents.delete()[0]

        return Response({"details": "Batches deleted successfully!"})
    except Exception:
        print(traceback.format_exc())
        return Response(
            {"details": "Failed to delete batches"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_project_keys(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        project_key_items = (
            project.settings.get("options", {}).get("options-keys", {}).get("items", [])
        )
        profile_keys = [
            {
                "label": item.get("keyLabel"),
                "type": item.get("type"),
            }
            for item in project_key_items if item.get("type") != "compound"
        ]

        return Response(profile_keys)
    except Project.DoesNotExist:
        return Response(
            {"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["GET"])
def get_ai_agent_conversations(request, transaction_id):
    """Get latest 200 ai agent conversation messages for a specific batch ID"""
    queryset = models.AiAgentConversation.objects.filter(transaction_id=transaction_id).order_by(
        "event_time"
    )[:1000]
    serializer = serializers.AiAgentConversationSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def add_ai_agent_conversations(request, batch_id):
    try:
        ai_agent_conversations = request.data["ai_agent_conversations"]
    except KeyError:
        return Response(
            {"detail": "'ai_agent_conversations' is required fields"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    for item in ai_agent_conversations:
        message_type = item["type"]
        message = item["message"]
        models.AiAgentConversation.objects.create(
            batch_id=batch_id,
            type=message_type,
            message=message,
        )
    return Response({"detail": f"AI Agent conversations have been added successfully"})


@api_view(["DELETE"])
def clear_ai_agent_conversations(request, batch_id):
    """Get latest 200 ai agent conversation messages for a specific batch ID"""
    models.AiAgentConversation.objects.filter(batch_id=batch_id).delete()

    return Response(
        {
            "detail": f"AI Agent conversations have been cleared successfully for 'batch_id'"
        }
    )


@api_view(["GET"])
def get_profile_by_name(request, profile_name):
    try:
        profile = Profile.objects.get(name=profile_name)
        serialized_profile = ProfileSerializer(profile)
        project = Project.objects.get(name=profile.project)
        return Response(
            {"profile": {**serialized_profile.data, "project_id": project.id}}
        )
    except:
        return Response(
            {"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
def add_profile_key(request):
    """Add a key to a profile after validating it against its project."""
    profile_id = request.data.get("profile_id")
    key_label = request.data.get("key_label")

    if not profile_id or not key_label:
        return Response(
            {"detail": "'profile_id', 'key_label' and are required fields"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = Profile.objects.get(id=profile_id)
    project_name = profile.project

    project = Project.objects.get(name=project_name)

    # Check if key is already exist in profile
    profile_keys = profile.keys
    profile_key_labels = [i["label"] for i in profile_keys]

    if key_label in profile_key_labels:
        return Response(
            {
                "detail": f"key '{key_label}' is already exist in profile '{profile.name}'"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if key is part of project, then add it to profile
    project_key_items = (
        project.settings.get("options", {}).get("options-keys", {}).get("items", [])
    )
    project_key_labels = [i["keyLabel"] for i in project_key_items]

    final_key_label = None
    if key_label in project_key_labels:
        final_key_label = key_label

    # If key label is not available in project-keys,
    # Check mapped labels and add respective key
    else:
        project_mapped_key_items = (
            project.settings.get("options", {})
            .get("options-mapped-keys", {})
            .get("items", [])
        )
        project_mapped_key_labels = [i["mappedKey"] for i in project_mapped_key_items]

        if key_label in project_mapped_key_labels:
            # Update key_label to one (which is mapped) (for example, ship to to shipper)
            for i in project_mapped_key_items:
                if i["mappedKey"] == key_label:
                    final_key_label = i["keyLabel"]
                    break

        if final_key_label is None:
            return Response(
                {
                    "detail": f"Key '{key_label}' is not available for project '{project.name}'"
                },
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

    if final_key_label in profile_key_labels:
        return Response(
            {
                "detail": f"Key '{key_label}' ({final_key_label}) is already exist in profile '{profile.name}'"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    add_key_to_profile(profile, project_key_items, final_key_label)

    return Response({"detail": f"Key {final_key_label} added to profile"})


def add_key_to_profile(profile, project_key_items, key_label):
    try:
        profile_keys = profile.keys
        key_type = None
        for i in project_key_items:
            if i["keyLabel"] == key_label:
                key_type = i["type"]
                break

        profile_keys.append(
            {"type": key_type, "label": key_label, "keyValue": to_camel_case(key_label)}
        )
        profile.save()

    except Exception:
        print(traceback.format_exc())


@api_view(["POST"])
def add_mapped_key_to_project(request):
    """Add a key to the profile after mapping it to its project."""
    try:
        batch_id = request.data.get("batch_id")
        document_id = request.data.get("document_id")
        profile_id = request.data.get("profile_id")
        key_label = request.data.get("key_label")
        mapped_key = request.data.get("mapped_key")
        key_qualifier_value = request.data.get("key_qualifier_value")
        key_type= request.data.get("key_type", "key")
        is_table_key = request.data.get("is_table_key", False)
        template = request.data.get("template", None)
        table_unique_id = request.data.get("table_unique_id", None)
        skip_post_processor = request.data.get("skip_post_processor", False)
        skip_table_processing = request.data.get("skip_table_processing", False)
        skip_key_processing = request.data.get("skip_key_processing", False)
        definition_version = request.data.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )

        if profile_id is None or key_label is None or mapped_key is None:
            return Response(
                {
                    "detail": "'profile_id', 'key_label' and 'mapped_key' are required fields"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = Profile.objects.get(id=profile_id)
        project_name = profile.project

        project = Project.objects.get(name=project_name)

        project_key_items = (
            project.settings.get("options", {}).get("options-keys", {}).get("items", [])
        )

        project_mapped_key_items = (
            project.settings.get("options", {})
            .get("options-mapped-keys", {})
            .get("items", [])
        )

        profile_key_labels = [i["label"] for i in profile.keys]

        project_mapped_key_labels = [i["mappedKey"] for i in project_mapped_key_items]

        if mapped_key in project_mapped_key_labels:
            if key_label not in profile_key_labels:
                add_key_to_profile(profile, project_key_items, key_label)

            return Response(
                {
                    "detail": f"Mapped key ({key_label}, {mapped_key}) is already exist in project '{project_name}'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        project_mapped_key_items.append(
            {
                "keyLabel": key_label,
                "mappedKey": mapped_key,
                "qualifierValue": key_qualifier_value,
                "keyType": key_type,
                "isTableKey": is_table_key,
            }
        )
        project.save()

        if key_label not in profile_key_labels:
            add_key_to_profile(profile, project_key_items, key_label)

        request_data = {
            "batch_id": batch_id,
            "document_id": document_id,
            "template": template,
            "table_unique_id": table_unique_id,
            "skip_post_processor": skip_post_processor,
            "skip_table_processing": skip_table_processing,
            "skip_key_processing": skip_key_processing,
            "definition_version": definition_version,
        }
        publish("label_mapping", "to_pipeline", request_data)

        return Response(
            {"detail": f"Mapped key added successfully in project '{project_name}'"}
        )
    except Exception as error:
        print(traceback.format_exc())
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def get_vendors_by_profile(request):
    """Get Vendors list based on Profile name"""
    profile_name = request.GET.get("profile", None)
    if not profile_name:
        return Response(
            {"detail": "No 'profile' was provided in the request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        definition_obj = models.Definition.objects.filter(definition_id=profile_name)
        vendors = list(definition_obj.values_list("vendor", flat=True))
        return Response(vendors, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"detail": f"Error fetching vendors: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["POST"])
def delete_mapped_key(request):
    """Delete mapped key with project id and mapped key from project"""
    try:
        profile_name = request.data.get("profile_name")
        remove_key_value = request.data.get("remove_key_value")
        mapped_key = request.data.get("mapped_key")

        batch_id = request.data.get("batch_id")
        document_id = request.data.get("document_id")
        template = request.data.get("template", None)
        table_unique_id = request.data.get("table_unique_id", None)
        skip_post_processor = request.data.get("skip_post_processor", False)
        skip_table_processing = request.data.get("skip_table_processing", False)
        skip_key_processing = request.data.get("skip_key_processing", False)
        definition_version = request.data.get(
            "definition_version", settings.DEFAULT_DEFINITION_VERSION
        )

        if profile_name is None or remove_key_value is None or mapped_key is None:
            return Response(
                {
                    "detail": "'profile_name', 'remove_key_value' and 'mapped_key' are required fields"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = Profile.objects.get(name=profile_name)
        project_name = profile.project

        project = Project.objects.get(name=project_name)

        # Get the nested array safely
        project_settings = project.settings or {}
        options = project_settings.get("options", {})
        project_keys = options.get("options-keys", {})
        project_keys_items = project_keys.get("items", [])

        def normalize(value):
            return value.replace(" ", "").replace(".", "").lower()

        key_label = None
        for item in project_keys_items:
            project_key_value = normalize(item["keyValue"])
            project_key_label = normalize(item["keyLabel"])

            if project_key_value == normalize(remove_key_value):
                key_label = item["keyLabel"]
                break

            if project_key_label == normalize(remove_key_value):
                key_label = item["keyLabel"]
                break

        if not key_label:
            return Response(
                {"detail": f"Key Label '{key_label}' not found in project '{project_name}'."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        mapped_keys = options.get("options-mapped-keys", {})
        project_mapped_key_items = mapped_keys.get("items", [])

        def find_matching_item_index(project_mapped_key_items, key_label, mapped_key):
            """Find the index of item matching the given key_label and mapped_key."""

            mapped_key = normalize(mapped_key)  # camelCase + lower
            key_label = normalize(key_label)     # only lower (as per requirement)

            for index, item in enumerate(project_mapped_key_items):
                item_key_label = normalize(item.get("keyLabel", ""))
                item_mapped_key = normalize(item.get("mappedKey", ""))

                if item_key_label == key_label and item_mapped_key == mapped_key:
                    return index
            return None

        to_be_deleted_index = find_matching_item_index(
            project_mapped_key_items, 
            key_label, 
            mapped_key
        )

        if to_be_deleted_index is not None:
            project_mapped_key_items.pop(to_be_deleted_index)
            mapped_keys["items"] = project_mapped_key_items
            options["options-mapped-keys"] = mapped_keys
            project_settings["options"] = options
            project.settings = project_settings
            project.save(update_fields=["settings"])
        else:
            return Response(
                {"detail": f"Mapped key {mapped_key} and Key Label {key_label} not found in project '{project_name}'."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        request_data = {
            "batch_id": batch_id,
            "document_id": document_id,
            "template": template,
            "table_unique_id": table_unique_id,
            "skip_post_processor": skip_post_processor,
            "skip_table_processing": skip_table_processing,
            "skip_key_processing": skip_key_processing,
            "definition_version": definition_version,
        }
        publish("label_mapping", "to_pipeline", request_data)

        return Response(
            {"detail": f"Mapped key removed successfully in project '{project_name}'"}
        )
    except Exception as e:
        return Response(
                {"detail": f"Error when deleting mapped key: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
class ChangeLogViewSet(viewsets.ModelViewSet):
    queryset = models.ChangeLog.objects.all()
    serializer_class = serializers.ChangeLogSerializer
    pagination_class = PaginationMeta

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by", None)
        sort_desc = self.request.query_params.get("sort_desc", "false")
        queryset = self.queryset

        if self.action == "list":
            # Get all query parameters
            params = self.request.query_params
            module = params.get("module")
            module_id = params.get("module_id")
            change_category = params.get("change_category")
            action = params.get("action")
            username = params.get("username")

            if module:
                queryset = queryset.filter(module=module)

            if module_id:
                queryset = queryset.filter(module_id=module_id)

            if change_category:
                queryset = queryset.filter(change_category__icontains=change_category)
            
            if action:
                queryset = queryset.filter(action__icontains=action)

            if username:
                queryset = queryset.filter(user__username__iexact=username)

        if sort_by:
            sort_keyword = f"-{sort_by}" if sort_desc == "true" else sort_by
            queryset = queryset.order_by(sort_keyword)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Override to limit to 3 results regardless of pagination
        """
        queryset = self.filter_queryset(self.get_queryset())

        limited_queryset = queryset[:3]

        # Serialize the limited results
        page = self.paginate_queryset(limited_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(limited_queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def download(self, request, pk=None):
        """
        Download changes for a specific ChangeLog entry
        POST /api/changelogs/{id}/download/
        """
        try:
            change_log = self.get_object()
            if not change_log.old_data_path:
                return Response(
                    {
                        "status": "error",
                        "message": "No old data available for download",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            old_data = {}
            with open(change_log.old_data_path, "r") as f:
                old_data = json.load(f)

            return Response({"status": "success", "old_data": old_data})

        except Exception as e:
            return Response(
                {"status": "error", "message": f"Error downloading changes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def revert(self, request, pk=None):
        """
        Revert changes for a specific ChangeLog entry
        POST /api/changelogs/{id}/revert/
        """
        try:
            change_log = self.get_object()
            result = self._revert_changes(change_log)

            if result["success"]:
                return Response(
                    {
                        "status": "success",
                        "message": result["message"],
                        "reverted_to": result["reverted_data"],
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "error", "message": result["message"]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"status": "error", "message": f"Error reverting changes: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _revert_changes(self, change_log):
        """
        Core logic to revert changes based on ChangeLog entry
        """
        if not change_log.old_data_path:
            return {"success": False, "message": "No old data available for revert"}

        try:
            reverted_data = self._load_and_apply_old_data(change_log)
            return {
                "success": True,
                "message": "Changes reverted successfully",
                "reverted_data": reverted_data,
            }

        except Exception as e:
            return {"success": False, "message": f"Failed to revert changes: {str(e)}"}

    def _load_and_apply_old_data(self, change_log):
        """
        Load old data from storage and apply it
        """
        if not os.path.exists(change_log.old_data_path):
            raise FileNotFoundError("Old data file not found")

        with open(change_log.old_data_path, "r") as f:
            old_data = json.load(f)

        return self._apply_revert_data(change_log, old_data)

    def _apply_revert_data(self, change_log, old_data):
        """
        Apply the reverted data to the actual model
        """
        if change_log.module == "PROFILE":
            return self._revert_profile(change_log, old_data)
        elif change_log.module == "PROJECT":
            return self._revert_project(change_log, old_data)
        else:
            raise ValueError(f"Revert not supported for module: {change_log.module}")

    def _revert_profile(self, change_log, old_data):
        """
        Revert profile changes
        """
        from dashboard.views import import_profiles_handler
        from dashboard.serializers import ProfileSerializer

        try:
            profile = Profile.objects.get(id=change_log.module_id)

            # vendors should be empty
            old_data["vendors"] = []

            old_instance = profile
            old_instance_data = ProfileSerializer(old_instance).data

            if profile.name != old_data["name"]:
                profile.name = old_data["name"]
                profile.save()

            import_profiles_handler([old_data], ignore_fields=True)

            new_instance = Profile.objects.get(id=change_log.module_id)
            new_data = ProfileSerializer(new_instance).data

            ChangeLogger.log_model_changes(
                new_instance,
                old_instance,
                new_data,
                old_instance_data,
                self.request.user,
            )

            return {
                "id": profile.id,
                "module": "PROFILE",
            }

        except:
            print(traceback.format_exc())
            raise ValueError("Error found in core revert logic")

    def _revert_project(self, change_log, old_data):
        """
        Revert project changes
        """
        from dashboard.views import import_projects_handler
        from dashboard.serializers import ProjectSerializer

        try:
            project = Project.objects.get(id=change_log.module_id)

            old_instance = project
            old_instance_data = ProjectSerializer(old_instance).data

            # Remove project_id
            _ = old_data.pop("project_id", None)

            import_projects_handler([old_data], None, False)

            new_instance = Project.objects.get(id=change_log.module_id)
            new_data = ProjectSerializer(new_instance).data

            ChangeLogger.log_model_changes(
                new_instance,
                old_instance,
                new_data,
                old_instance_data,
                self.request.user,
            )

            return {
                "id": project.id,
                "module": "PROJECT",
            }

        except Exception as e:
            raise ValueError("Error found in core revert logic")
