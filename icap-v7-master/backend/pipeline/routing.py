"""
Organization: AIDocbuilder Inc.
File: pipeline/routing.py
Version: 6.0

Authors:
    - Vivek - Initial implementation

Last Updated By: Vivek
Last Updated At: 2023-11-01

Description:
    This file defines the Websocket URL routing for the pipeline app.

Dependencies:
    - re_path from django.urls
    - consumers

Main Features:
    - Websocket URL routing.
"""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/notifications/", consumers.StatusConsumer.as_asgi()),
]
