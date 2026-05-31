import re

from rest_framework import serializers

from .models import Permission, Role, RolePermission, User, UserRole
from .services.hasher import PasswordHasher


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer to handle user registration.
    Validates input data, enforces password complexity, and hashes passwords securely.
    """

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "password", "password_confirm", "first_name", "middle_name", "last_name"]

    def validate_email(self, value):
        """
        Check if the email is already registered in the system.
        """

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_password(self, value):
        """
        Enforce password complexity rules.
        """

        # 1. Length check
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")

        # 2. Character set check (only Latin letters, digits, and specific special characters)
        if not re.match(r"^[a-zA-Z0-9$%&!:]+$", value):
            raise serializers.ValidationError(
                "Password can only contain Latin letters, digits, and special characters ($%&!:)."
            )

        # 3. Uppercase check
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")

        return value

    def validate(self, attrs):
        """
        Cross-field validation to ensure password and confirmation match.
        """

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """
        Remove raw password fields from validated data,
        generate a secure password hash, and create the User instance.
        """

        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        # Generate password hash using the custom PasswordHasher class
        validated_data["password_hash"] = PasswordHasher.get_password_hash(password)

        return super().create(validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "middle_name", "last_name"]
        read_only_fields = ["id", "email"]


class LoginRequestSerializer(serializers.Serializer):

    email = serializers.EmailField(help_text="User email")
    password = serializers.CharField(
        style={'input_type': 'password'},
        help_text="Secure password"
    )


class LoginResponseSerializer(serializers.Serializer):

    access_token = serializers.CharField(help_text="JWT access token")
    refresh_token = serializers.CharField(help_text="refresh token")
    token_type = serializers.CharField(help_text="Token type 'bearer'")


class LogoutRequestSerializer(serializers.Serializer):

    refresh_token = serializers.CharField(
        help_text="refresh token"
    )


class TokenRefreshRequestSerializer(serializers.Serializer):

    refresh_token = serializers.CharField(
        help_text="JWT refresh token"
    )


    ########################
    ### AdminSerializers ###
    ########################


class AdminPermissionSerializer(serializers.ModelSerializer):
    """
    Serializer to list all permissions.
    """

    class Meta:
        model = Permission
        fields = ["id", "code", "description"]


class AdminRolesListSerializer(serializers.ModelSerializer):
    """
    Serializer to list roles along with their linked permission codes.
    Simplified using SlugRelatedField over the 'role_permissions' relationship.
    """

    permissions = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="permission__code", source="role_permissions"
    )

    class Meta:
        model = Role
        fields = ["id", "name", "permissions"]


class AdminRoleDetailOverviewSerializer(serializers.ModelSerializer):
    """
    Nested helper serializer to display structured role information inside the User overview.
    """

    role_name = serializers.CharField(source="role.name")
    permissions = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="permission__code", source="role.role_permissions"
    )

    class Meta:
        model = Role
        fields = ["role_name", "permissions"]


class AdminUserRolesSerializer(serializers.ModelSerializer):
    """
    Serializer to display user access overview.
    Completely refactored to eliminate custom MethodFields.
    """

    roles_overview = AdminRoleDetailOverviewSerializer(many=True, read_only=True, source="user_roles")
    all_effective_permissions = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="role__role_permissions__permission__code", source="user_roles"
    )

    class Meta:
        model = User
        fields = ["id", "email", "roles_overview", "all_effective_permissions"]


class AdminUserRoleManageSerializer(serializers.ModelSerializer):
    """
    Serializer to manage User <-> Role relationships.
    Accepts user email and role name to create or validate a connection.
    """

    email = serializers.EmailField(write_only=True)
    role_name = serializers.CharField(max_length=50, write_only=True)

    class Meta:
        model = UserRole
        fields = ["email", "role_name"]

    def validate(self, attrs):
        email = attrs.get("email")
        role_name = attrs.get("role_name")

        # 1. Fetch user and role instances
        user = User.objects.filter(email=email).first()
        role = Role.objects.filter(name=role_name).first()

        if not user:
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if not role:
            raise serializers.ValidationError({"role_name": f"Role '{role_name}' does not exist."})

        # Save instances in attributes for creation/deletion actions
        attrs["user"] = user
        attrs["role"] = role
        return attrs

    def create(self, validated_data):
        """Creates a relation if it doesn't already exist."""
        user = validated_data["user"]
        role = validated_data["role"]

        # Prevent duplicate database records
        user_role, created = UserRole.objects.get_or_create(user=user, role=role)
        return user_role


class AdminRolePermissionManageSerializer(serializers.ModelSerializer):
    """
    Serializer to manage Role <-> Permission relationships.
    Accepts role name and permission code to create or validate a connection.
    """

    role_name = serializers.CharField(max_length=50, write_only=True)
    permission_code = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = RolePermission
        fields = ["role_name", "permission_code"]

    def validate(self, attrs):
        role_name = attrs.get("role_name")
        permission_code = attrs.get("permission_code")

        # 1. Fetch role and permission instances
        role = Role.objects.filter(name=role_name).first()
        permission = Permission.objects.filter(code=permission_code).first()

        if not role:
            raise serializers.ValidationError({"role_name": f"Role '{role_name}' does not exist."})
        if not permission:
            raise serializers.ValidationError({"permission_code": f"Permission '{permission_code}' does not exist."})

        attrs["role"] = role
        attrs["permission"] = permission
        return attrs

    def create(self, validated_data):
        """Creates a relation if it doesn't already exist."""
        role = validated_data["role"]
        permission = validated_data["permission"]

        role_perm, created = RolePermission.objects.get_or_create(role=role, permission=permission)
        return role_perm
