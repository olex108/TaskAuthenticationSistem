import re

from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework import status
from .models import User
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


# class AuthFailedException(APIException):
#     status_code = status.HTTP_401_UNAUTHORIZED
#     default_detail = 'Invalid credentials or account is deactivated'
#     default_code = 'authentication_failed'

# class LoginSerializer(serializers.Serializer):
#     """
#     Serializer to handle user authentication.
#     Validates user credentials and mitigates timing attacks using dummy verification.
#     """
#
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True, style={'input_type': 'password'})
#
#     def validate(self, attrs):
#         email = attrs.get('email')
#         password = attrs.get('password')
#
#         if not email or not password:
#             raise serializers.ValidationError("Email or password are required")
#
#         user = User.objects.filter(email=email).first()
#
#         if not user or not user.is_active:
#             PasswordHasher.dummy_verify(password)
#             raise AuthFailedException()
#
#         if not PasswordHasher.verify_password(password, user.password_hash):
#             raise AuthFailedException()
#
#         attrs['user'] = user
#         return attrs
