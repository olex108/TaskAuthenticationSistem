from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class HasPermission(BasePermission):
    """
    Custom DRF permission class that checks if a user has the required permission code.
    Read data from TokenUser attached to the request.
    """

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self):
        # This allows us to instantiate the class with arguments inside views
        return self

    def has_permission(self, request: Request, view) -> bool:
        """
        Check if the user is authenticated and possesses the required permission.
        """
        # 1. If the authentication class didn't run or failed, deny access (401 handled by DRF)
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Extract permissions from Token
        user_permissions = getattr(request.user, 'permissions', [])

        # 3. Grant access if the required code exists in user's token claims
        return self.required_permission in user_permissions
