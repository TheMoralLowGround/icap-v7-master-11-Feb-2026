"""
Organization: AIDocbuilder Inc.
File: core/permissions.py
Version: 6.0

Authors:
    - Vivek - Initial implementation
    - Nayem - Code optimization
    - Sunny - Update user permission

Last Updated By: Sunny
Last Updated At: 2024-05-30

Description:
    This file define custom permission to access operations for users.

Dependencies:
    - permissions from rest_framework

Main Features:
    - Customize user access permission.
"""
from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class that only allows admin users (superuser or staff).
    Use this on admin-only endpoints to enforce server-side authorization.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class CustomPermission(permissions.BasePermission):
    """
    Custom permission class to restrict operations for regular users.
    Superuser will have full access to all APIs
    """
    safe_mehtods = permissions.SAFE_METHODS
    create_methods = ["POST"]
    edit_methods = ["PUT", "PATCH"]
    remove_mehtods = ["DELETE"]

    user_permissions = {
        "ws_ticket": safe_mehtods,
        "batch_list": safe_mehtods,
        "batch_instance": safe_mehtods,
        "delete_multiple": remove_mehtods,
        "definition_settings_list": safe_mehtods,
        "get_ra_json": safe_mehtods,
        "search_definition": safe_mehtods,
        "batch_status": safe_mehtods,
        "retrive_json": safe_mehtods,
        "chunk_data": create_methods,
        "test_models": create_methods,
        "process_batch": create_methods,
        "re_process_extraction": create_methods,
        "definition_instance": edit_methods,
        "update_definition_by_version": create_methods,
        "copy_definition_data": create_methods,
    }

    def has_permission(self, request, view):
        """Check user has permission"""
        if not request.user.is_authenticated:
            return False

        if request.user.is_active:
            return True

        # Check if regular user has permission for requested view.
        view_name = view.get_view_name().lower().replace(" ", "_")
        allowed_methods = self.user_permissions.get(view_name, [])

        if request.method in allowed_methods:
            return True

        return False
