import jwt
from rest_framework import generics, status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Permission, RefreshToken, Role, RolePermission, User, UserRole
from .permissions import HasPermission
from .serializers import (AdminPermissionSerializer, AdminRolePermissionManageSerializer, AdminRolesListSerializer,
                          AdminUserRoleManageSerializer, AdminUserRolesSerializer, UserProfileSerializer,
                          UserRegisterSerializer, LoginRequestSerializer, LoginResponseSerializer,
                          TokenRefreshRequestSerializer, LogoutRequestSerializer)
from .services.hasher import PasswordHasher
from .services.jwt import JWTService

from drf_spectacular.utils import extend_schema, inline_serializer


class UserRegisterAPIView(generics.CreateAPIView):
    """
    Register a new user. Accessible by any user
    """

    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    Endpoint for authenticated users to view and update their personal profile data.
    Automatically handles GET and PUT/PATCH requests using the serializer.
    """

    # Используем ваш существующий сериализатор
    serializer_class = UserProfileSerializer

    def get_object(self) -> User:
        """
        Fetch the actual database User record based on the stateless ID from the JWT.
        """
        return User.objects.get(id=self.request.user.id)


class UserSoftDeleteAPIView(APIView):
    """
    Endpoint for account soft-deletion initiated by the user.
    Deactivates the user profile (is_active=False) and forces a cascade logout
    by invalidating all their active refresh tokens.
    """

    def delete(self, request) -> Response:
        token_user = request.user

        # 1. Fetch the user from PostgreSQL and perform the soft-delete
        user = User.objects.get(id=token_user.id)
        user.is_active = False
        user.save()

        # 2. Force an immediate system-wide logout for this user
        RefreshToken.objects.filter(user=user, is_logout=False).update(is_logout=True)

        return Response({"message": "Account successfully deleted"}, status=status.HTTP_200_OK)


class LoginView(APIView):
    """
    API View to get tokens by valid email and password
    """

    permission_classes = [AllowAny]
    serializer_class = LoginRequestSerializer

    @extend_schema(
        request=LoginRequestSerializer,
        responses={200: LoginResponseSerializer}
    )
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


class LogoutAPIView(APIView):
    """
    Log out the user by refresh token.
    """

    serializer_class = LogoutRequestSerializer

    @extend_schema(
        request=LogoutRequestSerializer,
        responses={200: inline_serializer(
            name='LogoutSuccessResponse',
            fields={'message': serializers.CharField()}
        )}
    )
    def post(self, request) -> Response:
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required to logout"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token_entry = RefreshToken.objects.filter(refresh_token=refresh_token).first()
            if token_entry:
                token_entry.is_logout = True
                token_entry.save()

            return Response(
                {"message": "Logged out successfully. Token invalidated"},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"error": "Invalid token process"},
                status=status.HTTP_400_BAD_REQUEST
            )


class TokenRefreshView(APIView):
    """
    API View to refresh the access token using a valid refresh token.
    """

    permission_classes = [AllowAny]
    serializer_class = TokenRefreshRequestSerializer

    @extend_schema(
        request=TokenRefreshRequestSerializer,
        responses={200: LoginResponseSerializer}
    )
    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

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

            # 3. Get refresh token, chek status and del token from db
            token_entry = RefreshToken.objects.filter(refresh_token=refresh_token).first()
            if not token_entry or token_entry.is_logout:
                return Response(
                    {"error": "This token has been revoked (logged out)"}, status=status.HTTP_401_UNAUTHORIZED
                )
            else:
                del token_entry

            new_tokens = JWTService.generate_token(user)
            return Response(new_tokens, status=status.HTTP_200_OK)

        except jwt.InvalidTokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    ########################
    #####  AdminViews  #####
    ########################


class AdminPermissionListAPIView(generics.ListAPIView):
    """
    Admin-only endpoint to fetch a list of all system permissions.
    """

    queryset = Permission.objects.all()
    serializer_class = AdminPermissionSerializer
    permission_classes = [HasPermission("admin:access")]


class AdminRoleListAPIView(generics.ListAPIView):
    """
    Admin-only endpoint to fetch all roles along with their bundled permission codes.
    Uses prefetch_related to optimize DB queries (prevents N+1 problem).
    """

    serializer_class = AdminRolesListSerializer
    permission_classes = [HasPermission("admin:access")]

    def get_queryset(self):
        # Prefetching permissions linked to roles for optimal database performance
        return Role.objects.prefetch_related("role_permissions__permission").all()


class AdminUserDetailsAPIView(generics.RetrieveAPIView):
    """
    Admin-only endpoint to retrieve comprehensive role and permission breakdown
    for a specific user by their ID (/api/v1/admin/users/<int:pk>/access/).
    """

    serializer_class = AdminUserRolesSerializer
    permission_classes = [HasPermission("admin:access")]

    def get_queryset(self):
        # Deep prefetching across user roles, roles, and their permissions
        return User.objects.prefetch_related("user_roles__role__role_permissions__permission").all()


class AdminAssignUserRoleAPIView(generics.CreateAPIView):
    """
    Admin-only endpoint to assign a role to a user.
    Uses generic CreateAPIView and handles the logic via the serializer.
    """

    serializer_class = AdminUserRoleManageSerializer
    permission_classes = [HasPermission("admin:access")]


class AdminRevokeUserRoleAPIView(APIView):
    """
    Admin-only endpoint to revoke a role from a user.
    """

    permission_classes = [HasPermission("admin:access")]

    def post(self, request) -> Response:
        serializer = AdminUserRoleManageSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            role = serializer.validated_data["role"]

            # Find and delete the relation
            relation = UserRole.objects.filter(user=user, role=role).first()
            if not relation:
                return Response(
                    {"error": f"User does not hold the role '{role.name}'."}, status=status.HTTP_400_BAD_REQUEST
                )

            relation.delete()
            return Response({"message": "Role successfully revoked from the user."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================================
# 2. ROLE <-> PERMISSION MANAGEMENT
# =====================================================================


class AdminAddRolePermissionAPIView(generics.CreateAPIView):
    """
    Admin-only endpoint to add an atomic permission code to a role.
    """

    serializer_class = AdminRolePermissionManageSerializer
    permission_classes = [HasPermission("admin:access")]


class AdminRemoveRolePermissionAPIView(APIView):
    """
    Admin-only endpoint to remove a permission code from a role.
    """

    permission_classes = [HasPermission("admin:access")]

    def post(self, request) -> Response:
        serializer = AdminRolePermissionManageSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.validated_data["role"]
            permission = serializer.validated_data["permission"]

            # Find and delete the relation
            relation = RolePermission.objects.filter(role=role, permission=permission).first()
            if not relation:
                return Response(
                    {"error": f"Role '{role.name}' does not have permission '{permission.code}'."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            relation.delete()
            return Response({"message": "Permission successfully removed from the role."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
