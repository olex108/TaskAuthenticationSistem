import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from identity.models import User
from identity.services.jwt import JWTService


class TokenUser:
    """
    A lightweight wrapper object representing the authenticated user.
    Stores vital information and claims fetched from the verified JWT access token.
    """

    def __init__(self, user_id: int, email: str, permissions: list[str]):
        self.id = user_id
        self.email = email
        self.permissions = permissions
        # Required property for Django REST Framework compatibility
        self.is_authenticated = True

    def __str__(self):
        return f"{self.email} (Authenticated)"


class CustomJWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication backend for Django REST Framework.
    Validates the 'Authorization: Bearer <token>' header against your custom configuration.
    Ensures active status checking to securely handle account soft-deletions.
    """

    def authenticate(self, request: Request) -> tuple[TokenUser, None] | None:
        # 1. Fetch the Authorization header from incoming HTTP request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None  # Pass evaluation to other handlers if configured, or trigger 401 later

        # 2. Parse and validate the structure of the Authorization header
        try:
            auth_type, token = auth_header.split(" ")
            if auth_type.lower() != "bearer":
                raise AuthenticationFailed("Authorization header must begin with 'Bearer'")
        except ValueError:
            raise AuthenticationFailed("Invalid Authorization header format. Use 'Bearer <token>'")

        # 3. Securely decode and verify the signature of the Access Token
        try:
            payload = JWTService.decode_token(token, expected_type="access")
        except jwt.InvalidTokenError as e:
            # DRF intercepts AuthenticationFailed and translates it into an HTTP 401 response
            raise AuthenticationFailed(str(e))

        # 4. Critical security check: Verify user existence and active status in PostgreSQL
        user_id = payload.get("user_id")
        email = payload.get("email")

        # We query the database specifically to honor soft-deletion instantly (is_active=True)
        user_exists = User.objects.filter(id=user_id, is_active=True).exists()
        if not user_exists:
            raise AuthenticationFailed("User account is inactive or does not exist.")

        # 5. Extract compiled atomic permissions from the validated token claims
        token_permissions = payload.get("permissions", [])

        # 6. Initialize our safe stateless TokenUser wrapper and attach it to DRF request lifecycle
        authenticated_user = TokenUser(user_id=user_id, email=email, permissions=token_permissions)

        return (authenticated_user, None)
