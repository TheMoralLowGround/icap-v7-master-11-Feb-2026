"""
Organization: AIDocbuilder Inc.
File: dashboard/urls.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add API endpoints

Last Updated By: Nayem
Last Updated At: 2024-07-04

Description:
    This file defines the URL routing for 'dashboard' app.

Dependencies:
    - include, path from django.urls
    - DefaultRouter from rest_framework.routers
    - views from dashboard

Main Features:
    - Viewset and API endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dashboard import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"profiles", views.ProfileViewSet)
router.register(r"projects", views.ProjectViewSet)
router.register(r"admin/projects", views.AdminProjectViewSet, basename="admin-projects")  # Admin-only projects endpoint
router.register(r"template", views.TemplateViewSet)
router.register(r"developer-settings", views.DeveloperSettingsViewSet)
router.register(r"output-channels", views.OutputChannelViewSet)

urlpatterns = [
    path("profile_fields_options/", views.profile_fields_options),
    path("export_templates/", views.export_templates),
    path("import_templates/", views.import_templates),
    path("clone_template/", views.clone_template),
    path("timeline/<str:timeline_id>", views.timeline),
    path("get_template_definition/", views.get_template_definition),
    path(
        "update_template_definition_by_version/",
        views.update_template_definition_by_version,
    ),
    path("template_upload_document/", views.template_upload_document),
    path(
        "send_profile_to_remote_system/<int:profile_id>/",
        views.send_profile_to_remote_system,
    ),
    path(
        "receive_profile_from_remote_system/", views.receive_profile_from_remote_system
    ),
    path("clone_profile/", views.clone_profile),
    path(
        "send_template_to_remote_system/<int:template_id>/",
        views.send_template_to_remote_system,
    ),
    path(
        "receive_template_from_remote_system/",
        views.receive_template_from_remote_system,
    ),
    path("create_default_dev_settings/", views.create_default_dev_settings),
    path("import_developer_settings/", views.import_developer_settings),
    path("", include(router.urls)),
    path("upload_yaml_file/<str:project_id>", views.upload_yaml_file),
    path("parse_yaml_json_keys/", views.parse_yaml_json_keys),
    path("get_all_processes/", views.get_all_processes),
    # Editor presence endpoints
    path("presence/join/", views.join_editor),
    path("presence/leave/", views.leave_editor),
    path("presence/heartbeat/", views.heartbeat_editor),
    path("presence/status/", views.editor_status),
    path("presence/cleanup_reloaded/", views.cleanup_reloaded_presence),
]
