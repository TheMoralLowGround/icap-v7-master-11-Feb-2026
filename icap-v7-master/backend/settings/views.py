"""
Organization: AIDocBuilder Inc.
File: settings/views.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature updates

Last Updated By: Nayem
Last Updated At: 2024-11-30

Description:
    This file contains functions to configure data export settings. 
    Export definition by their unique IDs and receive definition from external system.

Dependencies:
    - status from rest_framework
    - api_view, permission_classes from rest_framework.decorators
    - AllowAny from rest_framework.permissions
    - Response from rest_framework.response
    - Definition from core.models
    - DefinitionSerializer from core.serializers
    - DataExportConfig, DataImportConfig from settings.models

Main Features:
    - Functionality to configure setting for exporting data
    - Support exporting specific definition to external system
    - Enables receiving and importing definitions from external system
"""
import requests
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.models import Definition
from core.serializers import DefinitionSerializer
from settings.models import DataExportConfig, DataImportConfig


@api_view(["GET"])
def data_export_config(request):
    """Return export config system name and url"""
    if DataExportConfig.objects.exists():
        config_obj = DataExportConfig.objects.first()
        response = {
            "export_system_name": config_obj.export_system_name,
            "export_system_url": config_obj.export_system_url,
        }
        return Response(response)
    else:
        return Response({})


@api_view(["POST"])
def export_definition(request, definition_id):
    """Export definition to external system"""
    if not DataExportConfig.objects.exists():
        return Response(
            {"detail": "Data export config is not defined, Please set it first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get Definition Object
    try:
        definition_obj = Definition.objects.get(id=definition_id)
        definition = DefinitionSerializer(definition_obj).data
    except Definition.DoesNotExist:
        return Response(
            {"detail": f"Definition with ID {definition_id} doesn't exist"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Export Definition to another system
    config = DataExportConfig.objects.first()
    url = f"{config.export_system_url}/api/settings/receive_definition/"

    request_data = {"definition": definition, "auth_key": config.export_system_auth_key}
    response = requests.post(url, json=request_data)

    if response.status_code != 200:
        error = f"Definition export to '{config.export_system_name}' failed: \n {response.text}"
        return Response({"detail": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"detail": "Definition sent successfully"})


@api_view(["POST"])
@permission_classes([AllowAny])
def receive_definition(request):
    """Receive definition from external system"""
    try:
        payload = request.data
        definition = payload["definition"]
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

        definition_data = {
            "definition_id": definition["definition_id"],
            "vendor": definition["vendor"],
            "type": definition["type"],
            "name_matching_text": definition["name_matching_text"],
            "data": definition["data"],
            "cw1": definition["cw1"],
        }

        # If definition exists, update it. otherwise create new one.
        qs = (
            Definition.objects.filter(
                definition_id__iexact=definition_data["definition_id"]
            )
            .filter(type__iexact=definition_data["type"])
            .filter(name_matching_text__iexact=definition_data["name_matching_text"])
        )
        if qs.exists():
            definition_instance = qs.first()
            for k, v in definition_data.items():
                setattr(definition_instance, k, v)
            definition_instance.save()

        else:
            Definition.objects.create(**definition_data)
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({"detail": "Definition imported successfully"})
