from core import views
from django.urls import path


urlpatterns = [
    path("test_graph_config/", views.test_graph_config, name="test_graph_config"),
    path("test_imap_config/", views.test_imap_config, name="test_imap_config"),
    path("get_service_logs/", views.get_service_logs, name="get_service_logs"),
    path("get_sharepoint_sites/", views.get_sharepoint_sites, name="get_sharepoint_sites"),
    path("get_sharepoint_drive/", views.get_sharepoint_drive, name="get_sharepoint_drive"),
    path("get_onedrive_folder/", views.get_onedrive_folder, name="get_onedrive_folder"),
    path("get_drive_folder/", views.get_drive_folder, name="get_drive_folder"),
]
