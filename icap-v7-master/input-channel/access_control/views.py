from uuid import uuid4
from django.contrib.auth import login, get_user_model
from knox.views import LoginView as KnoxLoginView
from rest_framework import permissions, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response

from access_control.serializers import LoginRequestSerializer, UserSerializer


class LoginView(KnoxLoginView):
    """
    API endpoint that allows users to obtain auth tokens.
    """

    serializer_class = LoginRequestSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        serializer = AuthTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return super(LoginView, self).post(request, format=None)


@api_view(["GET"])
def get_user_data(request):
    try:
        User = get_user_model()
        user = User.objects.get(username=request.user.username)

        serialized_data = UserSerializer(user).data

        return Response({"user": serialized_data})
    except Exception as error:
        return Response(
            {"detail": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

