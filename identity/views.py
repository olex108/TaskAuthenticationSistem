from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import jwt

from .models import User
from .serializers import UserRegisterSerializer
from .services.hasher import PasswordHasher
from .services.jwt import JWTService


class UserRegisterAPIView(generics.CreateAPIView):
    """
    Register a new user. Accessible by any user.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    """
    API View to get tokens by valid email and password.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email or password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()

        if not user or not user.is_active:
            PasswordHasher.dummy_verify(password)
            return Response(
                {"error": "Invalid credentials or account is deactivated."}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not PasswordHasher.verify_password(password, user.password_hash):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = JWTService.generate_token(user)

        return Response(tokens, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """
    API View to refresh the access token using a valid refresh token.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Decode and validate the refresh token
            payload = JWTService.decode_token(refresh_token, expected_type="refresh")
            user_id = payload.get("user_id")

            # 2. Fetch the user and verify they are still active
            user = User.objects.filter(id=user_id, is_active=True).first()
            if not user:
                return Response(
                    {"error": "User not found or account is deactivated"}, status=status.HTTP_401_UNAUTHORIZED
                )

            new_tokens = JWTService.generate_token(user)
            return Response(new_tokens, status=status.HTTP_200_OK)

        except jwt.InvalidTokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
