"""
Organization: AIDocBuilder Inc.
File: access_control/authentication.py
Version: 6.0

Authors:
    - Initial implementation for HttpOnly cookie-based authentication

Last Updated At: 2024-12-10

Description:
    Custom authentication class that reads Knox tokens from HttpOnly cookies
    instead of Authorization headers.

Dependencies:
    - knox.auth.TokenAuthentication

Main Features:
    - Read auth token from HttpOnly cookie
    - Fall back to header-based auth for API compatibility
    - Sliding expiry handled by SlidingSessionMiddleware
"""
from django.conf import settings
from knox.auth import TokenAuthentication as KnoxTokenAuthentication


class CookieTokenAuthentication(KnoxTokenAuthentication):
    """
    Custom authentication class that reads Knox tokens from HttpOnly cookies.
    Falls back to header-based authentication for backward compatibility.
    """
    
    COOKIE_NAME = settings.AUTH_COOKIE_NAME
    
    def authenticate(self, request):
        # First, try to get token from HttpOnly cookie
        token = request.COOKIES.get(self.COOKIE_NAME)
        
        if token:
            # Validate the token using Knox's built-in validation
            return self.authenticate_credentials(token.encode())
        
        # Fall back to header-based authentication for backward compatibility
        return super().authenticate(request)
