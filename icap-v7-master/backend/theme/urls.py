"""
Organization: AIDocbuilder Inc.
File: theme/urls.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file defines the URL routing for 'theme' app.

Dependencies:
    - path from django.urls
    - views from theme

Main Features:
    - URL patterns.
"""
from django.urls import path

from theme import views

urlpatterns = [
    path("theme_settings/", views.theme_settings, name="theme_settings"),
]
