"""
Organization: AIDocBuilder Inc.
File: dashboard/views.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Feature updates

Last Updated By: Nayem
Last Updated At: 2024-11-30

Description:
    Handle theme settings

Dependencies:
    - api_view, permission_classes from rest_framework.decorators
    - AllowAny from rest_framework.permissions
    - Response from rest_framework.response
    - ThemeSetting from theme.models

Main Features:
    - Manage and configure theme settings
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from theme.models import ThemeSetting


@api_view(["GET"])
@permission_classes([AllowAny])
def theme_settings(request):
    """Manage and configure theme settings"""
    if ThemeSetting.objects.exists():
        theme_settings = ThemeSetting.objects.first()
        response = {
            "app_title": theme_settings.app_title,
            "app_title_color_light_mode": theme_settings.app_title_color_light_mode,
            "app_title_color_dark_mode": theme_settings.app_title_color_dark_mode,
            "logo_light_mode": theme_settings.logo_light_mode.url
            if theme_settings.logo_light_mode
            else "",
            "logo_dark_mode": theme_settings.logo_dark_mode.url
            if theme_settings.logo_dark_mode
            else "",
            "favicon": theme_settings.favicon.url if theme_settings.favicon else "",
            "header_color_light_mode": theme_settings.header_color_light_mode,
            "header_color_dark_mode": theme_settings.header_color_dark_mode,
            "header_text_color_light_mode": theme_settings.header_text_color_light_mode,
            "header_text_color_dark_mode": theme_settings.header_text_color_dark_mode,
        }
        return Response(response)
    else:
        return Response({})
