"""
Middleware for sliding session expiry.
Refreshes the auth cookie on each authenticated request.
"""
from datetime import timedelta
from django.conf import settings

COOKIE_NAME = settings.AUTH_COOKIE_NAME
COOKIE_SECURE = settings.AUTH_COOKIE_SECURE
COOKIE_SAMESITE = settings.AUTH_COOKIE_SAMESITE
COOKIE_HTTPONLY = settings.AUTH_COOKIE_HTTPONLY
COOKIE_PATH = settings.AUTH_COOKIE_PATH


def get_cookie_max_age():
    token_ttl = settings.REST_KNOX.get('TOKEN_TTL')
    if token_ttl is None:
        return int(timedelta(days=7).total_seconds())
    return int(token_ttl.total_seconds())


class SlidingSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check user exists and is authenticated
        user = getattr(request, 'user', None)
        if (user is not None
            and getattr(user, 'is_authenticated', False)
            and COOKIE_NAME in request.COOKIES):

            # Don't override login/logout cookie setting
            if not (hasattr(response, 'cookies') and COOKIE_NAME in response.cookies):
                response.set_cookie(
                    key=COOKIE_NAME,
                    value=request.COOKIES[COOKIE_NAME],
                    max_age=get_cookie_max_age(),
                    secure=COOKIE_SECURE,
                    httponly=COOKIE_HTTPONLY,
                    samesite=COOKIE_SAMESITE,
                    path=COOKIE_PATH,
                )

        return response
