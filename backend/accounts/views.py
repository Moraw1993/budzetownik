from common.views import PrivateAPIView
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .exceptions import LoginRateLimitError, SetupClosedError
from .models import User
from .serializers import CredentialsSerializer, SetupSerializer, UserSerializer
from .services import authenticate_account, create_initial_account, security_log


@method_decorator(csrf_protect, name="dispatch")
class SetupView(PrivateAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {"setup_required": not User.objects.exists(), "csrf_token": get_token(request)}
        )

    def post(self, request):
        if User.objects.exists():
            return Response({"detail": "Konfiguracja początkowa została zakończona."}, status=409)

        serializer = SetupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = create_initial_account(**serializer.validated_data)
        except SetupClosedError:
            return Response({"detail": "Konfiguracja początkowa została zakończona."}, status=409)

        login(request, user)
        return Response(UserSerializer(user).data, status=201)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(PrivateAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CredentialsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = authenticate_account(request=request, **serializer.validated_data)
        except LoginRateLimitError:
            response = Response(
                {"detail": "Zbyt wiele prób. Spróbuj ponownie później."}, status=429
            )
            response["Retry-After"] = "900"
            return response

        if user is None:
            return Response({"detail": "Nieprawidłowy login lub hasło."}, status=401)

        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(PrivateAPIView):
    def post(self, request):
        user_id = request.user.pk
        logout(request)
        security_log.info("logout user_id=%s", user_id)
        return Response(status=204)


class CurrentUserView(PrivateAPIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
