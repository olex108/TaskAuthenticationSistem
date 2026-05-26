from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings
from identity.models import User, RefreshToken


class JWTService:
    SECRET_KEY = getattr(settings, "SECRET_KEY", "your-super-secret-key")
    ALGORITHM = getattr(settings, "ALGORITHM", "HS256")
    ACCESS_EXP_MINS = getattr(settings, "ACCESS_EXP_MINS", 15)
    REFRESH_EXP_DAYS = getattr(settings, "REFRESH_EXP_DAYS", 7)

    @staticmethod
    def get_user_permissions(user: User) -> list[str]:
        """
        Method that returns a list of permissions that the user has permission to.
        Get permissions from all roles of user
        """

        permissions = (
            user.user_roles.prefetch_related("role__role_permissions__permission")
            .values_list("role__role_permissions__permission__code", flat=True)
            .distinct()
        )
        return [p for p in permissions if p]

    @staticmethod
    def create_refresh_token_in_db(user: User, refresh_token: str, expires_at: datetime, is_logout: bool = False) -> None:
        """
        Save refresh token in database
        """

        RefreshToken.objects.create(
            user=user,
            refresh_token=refresh_token,
            is_logout=is_logout,
            expires_at=expires_at
        )

    @classmethod
    def generate_token(cls, user: User) -> dict:
        """
        Method that generates a JWT token (Access and Refresh)
        """

        now = datetime.now(timezone.utc)

        user_permissions = cls.get_user_permissions(user)

        access_payload = {
            "token_type": "access",
            "user_id": user.id,
            "email": user.email,
            "permissions": user_permissions,
            "exp": now + timedelta(minutes=cls.ACCESS_EXP_MINS),
            "iat": now,
        }

        refresh_payload = {
            "token_type": "refresh",
            "user_id": user.id,
            "email": user.email,
            "permissions": user_permissions,
            "exp": now + timedelta(days=cls.REFRESH_EXP_DAYS),
            "iat": now,
        }

        access_token = jwt.encode(access_payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

        expires_datetime = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        JWTService.create_refresh_token_in_db(
            user=user,
            refresh_token=refresh_token,
            expires_at=expires_datetime,
            is_logout=False
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @classmethod
    def decode_token(cls, token: str, expected_type: str = "access") -> dict:
        """
        Method verifies token by expected_type

        :return payload if true or raise exception if false
        """

        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])

            if payload.get("token_type") != expected_type:
                raise jwt.InvalidTokenError("Invalid token type")

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Timestamp expired")
        except jwt.DecodeError:
            raise jwt.InvalidTokenError("Invalid token")
