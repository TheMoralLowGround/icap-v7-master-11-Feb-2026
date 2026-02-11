"""
Organization: AIDocbuilder Inc.
File: settings/urls.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file defines the URL routing for 'settings' app.

Dependencies:
    - path from django.urls
    - views from settings

Main Features:
    - URL patterns.
"""
from django.urls import path

from settings import views

urlpatterns = [
    path("data_export_config/", views.data_export_config),
    path("export_definition/<int:definition_id>/", views.export_definition),
    path("receive_definition/", views.receive_definition),
]
