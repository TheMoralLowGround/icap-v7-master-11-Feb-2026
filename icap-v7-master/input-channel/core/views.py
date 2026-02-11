import imaplib
from core.models import ProcessLog
from core.service.common import CommonService
from core.utils.utils import normalized_error
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from utils.logger_config import get_logger

logger = get_logger(__name__)


PERMISSION_ID = {
    "Mail.ReadWrite": "e2a3a72e-5f79-4c64-b1b1-878b674786c9",
    "Sites.Manage.All": "0c0bf378-bf22-4481-8f81-9e89a9b4960a",
    "Files.ReadWrite.All": "75359482-378d-4052-8f01-80520e7db3cd"
}


@api_view(["POST"])
def get_sharepoint_sites(request):
    """List SharePoint sites accessible with application permissions"""
    try:
        logger.info("Fetching sharepoint sites")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        tenant_id = request.data.get("tenant_id")

        if not (client_id and client_secret and tenant_id):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = CommonService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        permissions = client.get_permissions(client_id)
        expected_permission = ["Sites.Manage.All", "Files.ReadWrite.All"]
        valid, missing = validate_permissions(permissions, expected_permission)

        if not valid:
            return Response(
                {
                    "error": "Invalid API Permission! Check your App's permission",
                    "missing_permissions": missing,
                    "expected_permissions": expected_permission
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        list_sites = client.list_sites()
        return Response(
            {"sites": list_sites}, 
            status=status.HTTP_200_OK
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_sharepoint_drive(request):
    """List document libraries (drives) in a SharePoint site"""
    try:
        logger.info("Fetching sharepoint drive")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        tenant_id = request.data.get("tenant_id")
        site_id = request.data.get("site_id")

        if not (client_id and client_secret and tenant_id and site_id):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = CommonService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        drive_list = client.list_site_drives(site_id)
        return Response(
            {"drives": drive_list}, 
            status=status.HTTP_200_OK
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_onedrive_folder(request):
    """List document libraries (drives) in a SharePoint site"""
    try:
        logger.info("Fetching onedrive folders")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        tenant_id = request.data.get("tenant_id")
        user_id = request.data.get("user_id")

        if not (client_id and client_secret and tenant_id and user_id):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = CommonService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        drive_id = client.get_drive_id(user_id)
        folder_list = client.list_drive_folder(drive_id, item_id="root")
        return Response(
            {"folders": folder_list}, 
            status=status.HTTP_200_OK
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def get_drive_folder(request):
    """List only folders inside a drive folder"""
    try:
        logger.info("Fetching driver folders")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        tenant_id = request.data.get("tenant_id")
        drive_id = request.data.get("drive_id")
        item_id = request.data.get("item_id", "root")

        if not (client_id and client_secret and tenant_id and drive_id and item_id):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = CommonService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        folder_list = client.list_drive_folder(drive_id, item_id)
        return Response(
            {"folders": folder_list}, 
            status=status.HTTP_200_OK
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def test_graph_config(request):
    """Validate user input correct data"""
    try:
        logger.info("Testing graph configuration")
        client_id = request.data.get("client_id")
        client_secret = request.data.get("client_secret")
        tenant_id = request.data.get("tenant_id")
        input_type = request.data.get("input_type")

        if not (client_id and client_secret and tenant_id and input_type):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        client = CommonService(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id
        )
        permissions = client.get_permissions(client_id)

        if input_type == "email":
            expected_permission = ["Mail.ReadWrite"]
        elif input_type == "sharepoint":
            expected_permission = ["Sites.Manage.All", "Files.ReadWrite.All"]
        elif input_type == "onedrive":
            expected_permission = ["Files.ReadWrite.All"]

        valid, missing = validate_permissions(permissions, expected_permission)

        if not valid:
            return Response(
                {
                    "error": "Invalid API Permission! Check your App's permission",
                    "missing_permissions": missing,
                    "expected_permissions": expected_permission
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {"success": True, "message": "Configured successfully"}, 
            status=status.HTTP_200_OK
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
def test_imap_config(request):
    try:
        logger.info("Testing basic email configuration")
        email = request.data.get("email")
        password = request.data.get("password")
        server = request.data.get("server")
        port = request.data.get("port")
        port = int(port)

        if not (email and password and port and server):
            return Response(
                {"error": "Some parameters may be missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(email, password)
        mail.logout()
        return Response(
            {"success": True, "message": "IMAP connection successful"},
            status=status.HTTP_200_OK,
        )
    except Exception as ex:
        error = normalized_error(ex)
        logger.error(error)
        return Response(
            {"error": error},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
def get_service_logs(request):
    project = request.data.get("project")
    service = request.data.get("service")

    if not project or not service:
        return Response(
            {"error": "'project' and 'service' are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    logs = ProcessLog.objects.filter(
        project=project, service=service
        ).order_by("-created_at")[:50].values()
    
    return Response(list(logs), status=status.HTTP_200_OK)


def validate_permissions(permissions, expected_permission):
    """Cross-check assigned app permissions with expected ones"""
    missing = []
    for name in expected_permission:
        perm_id = PERMISSION_ID.get(name)
        if perm_id not in permissions:
            missing.append(name)

    return (len(missing) == 0, missing)
