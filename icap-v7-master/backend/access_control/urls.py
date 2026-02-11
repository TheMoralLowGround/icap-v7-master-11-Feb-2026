"""
Organization: AIDocbuilder Inc.
File: access_control/urls.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-03-12

Description:
    This file defines the URL routing for access_control app.

Dependencies:
    - path from django.urls
    - views as knox_views from knox
    - views from access_control

Main Features:
    - URL patterns.
"""
from django.urls import path
from access_control import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="knox_login"),
    path("logout/", views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", views.LogoutAllView.as_view(), name="knox_logoutall"),
    path("me/", views.me, name="me"),  # Get current user from HttpOnly cookie
    path("ws_ticket/", views.ws_ticket, name="ws_ticket"),
    path("update_last_login/", views.update_last_login, name="update_last_login"),
]
