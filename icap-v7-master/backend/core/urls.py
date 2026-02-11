"""
Organization: AIDocbuilder Inc.
File: core/urls.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Add API endpoints

Last Updated By: Nayem
Last Updated At: 2024-10-08

Description:
    This file defines the URL routing for 'core' app.

Dependencies:
    - include, path from django.urls
    - DefaultRouter from rest_framework.routers
    - views from core

Main Features:
    - Viewset and API endpoints.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r"definitions", views.DefinitionViewSet)
router.register(r"application-settings", views.ApplicationSettingsViewSet)
router.register(r"batches", views.BatchViewSet)
router.register(r"email-batches", views.EmailBatchViewSet)
router.register(r"train-batches", views.TrainBatchViewSet)
router.register(r"changelogs", views.ChangeLogViewSet)
# router.register(r"profile-training", views.ProfileTrainingViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path(
        "import_application_settings/",
        views.import_application_settings,
        name="import_application_settings",
    ),
    path(
        "get_definition_settings/",
        views.get_definition_settings,
        name="get_definition_settings",
    ),
    path(
        "update_definition_settings/",
        views.update_definition_settings,
        name="update_definition_settings",
    ),
    path(
        "import_definition_settings/",
        views.import_definition_settings,
        name="import_definition_settings",
    ),
    path("search_definition/", views.search_definition, name="search_definition"),
    path("update_definition_by_version/", views.update_definition_by_version),
    path("batch_status/<str:batch_id>", views.batch_status, name="batch_status"),
    path("ra_json/", views.get_ra_json, name="get_ra_json"),
    path(
        "get_ra_json_page_data/",
        views.get_ra_json_page_data,
        name="get_ra_json_page_data",
    ),
    path("simple_data_json/", views.simple_data_json, name="simple_data_json"),
    path("retrive_json/", views.retrive_json, name="retrive_json"),
    path("download_djson_excel/", views.download_djson_excel),
    path("defined_keys/", views.defined_keys, name="defined_keys"),
    path("all_batches/", views.all_batches, name="all_batches"),
    path("copy_definition_data/", views.copy_definition_data),
    path("get_definitions_by_profile/", views.get_definitions_by_profile),
    path("update_table_models_by_definition/", views.update_table_models_by_definition),
    path("all_definitions/", views.all_definitions, name="all_definitions"),
    path(
        "get_types_by_definition/",
        views.get_types_by_definition,
        name="get_types_by_definition",
    ),
    path(
        "get_batches_by_definition_type/",
        views.get_batches_by_definition_type,
        name="get_batches_by_definition_type",
    ),
    path("latest_batch_info/", views.latest_batch_info, name="latest_batch_info"),
    path(
        "check_batch_availability/",
        views.check_batch_availability,
        name="check_batch_availability",
    ),
    path(
        "get_train_batch_ra_json/",
        views.get_train_batch_ra_json,
        name="get_train_batch_ra_json",
    ),
    path(
        "get_assembled_results/",
        views.get_assembled_results,
        name="get_assembled_results",
    ),
    path(
        "get_api_responses/",
        views.get_api_responses,
        name="get_api_responses",
    ),
    path("get_excel_workbook/", views.get_excel_workbook, name="get_excel_workbook"),
    path(
        "delete_from_profile_training/",
        views.delete_from_profile_training,
        name="delete_from_profile_training",
    ),
    path("get-project-keys/<str:project_id>", views.get_project_keys),
    path("get_ai_agent_conversations/<str:transaction_id>", views.get_ai_agent_conversations, name="get_ai_agent_conversations"),
    path("add_ai_agent_conversations/<str:batch_id>", views.add_ai_agent_conversations, name="add_ai_agent_conversations"),
    path("clear_ai_agent_conversations/<str:batch_id>", views.clear_ai_agent_conversations, name="clear_ai_agent_conversations"),
    path("get_profile_by_name/<str:profile_name>", views.get_profile_by_name),
    path("add_key_to_profile/", views.add_profile_key),
    path("add_mapped_key_to_project/", views.add_mapped_key_to_project),
    path("get_vendors_by_profile/", views.get_vendors_by_profile),
    path("delete_mapped_key/", views.delete_mapped_key),
    path("", include(router.urls)),
]
