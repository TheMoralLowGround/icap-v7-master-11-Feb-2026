"""
Organization: AIDocbuilder Inc.
File: access_control/backends.py
Version: 6.0

Authors:
    - Nayem - Initial implementation

Last Updated By: Nayem
Last Updated At: 2024-03-06

Description:
    This file contain customized LDAP functionalities.

Dependencies:
    - LDAPBackend from django_auth_ldap.backend
    - get_user_model from django.contrib.auth

Main Features:
    - Implement customized LDAP functionalities for user management.
"""
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth import get_user_model


class CustomLDAPBackend(LDAPBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Check if the user also exists in the Django database
            User = get_user_model()
            user = User.objects.get(username=username)

            # Only the username `admin` can authenticate directly through the Django default backend
            if user and user.is_superuser and username == "admin":
                # Verify the password
                if user.check_password(password):
                    return user
                return None
        except User.DoesNotExist:
            # If the user does not exist in Django's database, authentication fails
            return None

        # Check if the user is disabled or not
        if user and not user.is_active:
            return None

        # If a user exists in Django's database, then authenticate against the LDAP directory
        try:
            ldap_user = super().authenticate(request, username, password, **kwargs)

            # Save the user to restrict LDAP overwrite permissions.
            user.save()

            if ldap_user and ldap_user.is_active:
                return user
            return None
        except:
            return None
