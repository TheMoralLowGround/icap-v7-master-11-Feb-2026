"""
Organization: AIDocBuilder Inc.
File: access_control/views.py
Version: 6.0

Authors:
    - Nayem - Initial implementation and feature update

Last Updated By: Nayem
Last Updated At: 2024-03-31

Description:
    This file define LoginView along with other access_control app functions such as
    ws_ticket, update_last_login

Dependencies:
    - uuid4 from uuid
    - cache from django.core.cache
    - login, get_user_model from django.contrib.auth
    - timezone from django.utils
    - LoginView from nox.views as KnoxLoginView
    - permissions, status from rest_framework
    - AuthTokenSerializer from rest_framework.authtoken.serializers
    - api_view from rest_framework.decorators
    - Response from rest_framework.response
    - UserSerializer from access_control.serializers

Main Features:
    - Generate and return unique ticket for websocket connections
    - Session control for refreshing user
    - Get necessary data for valid user
    - Update last login information
"""
import os
from uuid import uuid4
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import login, get_user_model
from django.utils import timezone
from knox.views import LoginView as KnoxLoginView, LogoutView as KnoxLogoutView, LogoutAllView as KnoxLogoutAllView
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response

from access_control.serializers import UserSerializer, LoginRequestSerializer
from access_control.authentication import CookieTokenAuthentication
from utils.presence_utils import unregister_user_presence_all

# Cookie configuration for HttpOnly secure cookies
COOKIE_NAME = settings.AUTH_COOKIE_NAME
COOKIE_SECURE = settings.AUTH_COOKIE_SECURE  # Use Secure flag in production (HTTPS only)
COOKIE_SAMESITE = settings.AUTH_COOKIE_SAMESITE  # 'Strict' for maximum security, 'Lax' for better UX
COOKIE_HTTPONLY = settings.AUTH_COOKIE_HTTPONLY  # Prevent JavaScript access
COOKIE_PATH = settings.AUTH_COOKIE_PATH  # Root path ensures consistent set/delete across all routes

# Get cookie max age from Knox token TTL setting
def get_cookie_max_age():
    """
    Get cookie max age from Knox TOKEN_TTL setting.
    For OpenShift-style persistent sessions, we always return a TTL value
    so the cookie persists across browser restarts.
    """
    token_ttl = settings.REST_KNOX.get('TOKEN_TTL')
    if token_ttl is None:
        # Default to 7 days for persistent cookie
        # This ensures the cookie survives browser restarts
        from datetime import timedelta
        return int(timedelta(days=7).total_seconds())
    return int(token_ttl.total_seconds())


class LoginView(KnoxLoginView):
    """
    API endpoint that allows users to obtain auth tokens.
    Sets the token in an HttpOnly cookie for security.
    """

    serializer_class = LoginRequestSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        
        # Get the response from Knox (contains token and user data)
        response = super(LoginView, self).post(request, format=None)
        
        # Set the token in an HttpOnly cookie
        if response.status_code == 200:
            token = response.data.get('token')
            if token:
                response.set_cookie(
                    key=COOKIE_NAME,
                    value=token,
                    max_age=get_cookie_max_age(),
                    secure=COOKIE_SECURE,
                    httponly=COOKIE_HTTPONLY,
                    samesite=COOKIE_SAMESITE,
                    path=COOKIE_PATH,
                )
                # Remove token from response body for security
                # The frontend doesn't need it since it's in the cookie
                del response.data['token']
        
        return response


def _delete_auth_cookie(response):
    """
    Helper to delete auth cookie from response.
    Uses set_cookie with max_age=0 instead of delete_cookie for more reliable deletion.
    This ensures the browser receives explicit instructions to remove the cookie.
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value='',  # Empty value
        max_age=0,  # Expire immediately
        expires='Thu, 01 Jan 1970 00:00:00 GMT',  # Explicit expiry in the past
        path=COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=COOKIE_HTTPONLY,
        samesite=COOKIE_SAMESITE,
    )
    return response


class LogoutView(KnoxLogoutView):
    """
    API endpoint to logout user and clear the auth cookie.
    Overrides Knox's permission check to allow logout even with invalid/expired tokens.
    """
    # Override to allow unauthenticated logout attempts
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, format=None):
        # Try to invalidate the Knox token if authenticated
        if request.user and request.user.is_authenticated:
            try:
                response = super().post(request, format=format)
                user_id_for_cleanup = getattr(request.user, 'id', None)
            except Exception:
                # If Knox logout fails, still return success
                response = Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
                user_id_for_cleanup = None
        else:
            # User not authenticated, just return success
            response = Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
            user_id_for_cleanup = None

        # Only cleanup if we had a valid authenticated user
        if user_id_for_cleanup:
            try:
                unregister_user_presence_all(user_id_for_cleanup)
            except Exception:
                pass

        # Always clear the auth cookie regardless of authentication status
        return _delete_auth_cookie(response)


class LogoutAllView(KnoxLogoutAllView):
    """
    API endpoint to logout user from all devices and clear the auth cookie.
    Overrides Knox's permission check to allow logout even with invalid/expired tokens.
    """
    # Override to allow unauthenticated logout attempts  
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, format=None):
        # Try to invalidate all Knox tokens (best-effort) and cleanup presence
        if request.user and request.user.is_authenticated:
            try:
                response = super().post(request, format=format)
                user_id_for_cleanup = getattr(request.user, 'id', None)
            except Exception:
                # If Knox logout fails, still return success
                response = Response({"detail": "Logged out from all devices"}, status=status.HTTP_200_OK)
                user_id_for_cleanup = None
        else:
            # User not authenticated, just return success
            response = Response({"detail": "Logged out from all devices"}, status=status.HTTP_200_OK)
            user_id_for_cleanup = None

        # Only cleanup if we had a valid authenticated user
        if user_id_for_cleanup:
            try:
                unregister_user_presence_all(user_id_for_cleanup)
            except Exception:
                pass
        
        # Always clear the auth cookie regardless of authentication status
        return _delete_auth_cookie(response)


@api_view(["GET"])
def ws_ticket(request):
    """Generate and return unique ticket for websocket connections"""
    ticket_uuid = str(uuid4())
    cache.set(ticket_uuid, True, 60 * 2)
    return Response({"ws_ticket": ticket_uuid})


@api_view(["GET"])
def me(request):
    """
    Get current authenticated user data from HttpOnly cookie.
    
    This is the primary endpoint for server-side session management.
    The frontend calls this on every page load to get user data.
    Authentication is validated via the HttpOnly cookie automatically.
    
    Returns:
        Response: User data if authenticated, 401 if not authenticated.
    
    Security:
        - No client-side storage needed
        - Server is the source of truth
    """
    # request.user is automatically populated by CookieTokenAuthentication
    # if the HttpOnly cookie contains a valid token
    if not request.user or not request.user.is_authenticated:
        return Response(
            {"detail": "Not authenticated"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    try:
        serialized_data = UserSerializer(request.user).data
        return Response({"user": serialized_data})
    except Exception as error:
        return Response(
            {"detail": str(error)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def update_last_login(request):
    """Update last login time for valid user"""
    username = request.query_params.get("username")

    if not username:
        return Response(
            {"detail": "invalid username"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        User = get_user_model()
        user = User.objects.get(username=username)

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return Response(
            data={"detail": "Last Login Updated Successfully"},
            status=status.HTTP_200_OK,
        )
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
