from django.urls import path
from identity.views import (
    UserRegisterAPIView,
    LoginView,
    TokenRefreshView,
    LogoutAPIView,
    UserProfileAPIView,
    UserSoftDeleteAPIView,
    AdminAssignRoleAPIView
)

# Явно задаем app_name для изоляции маршрутов приложения
app_name = 'identity'

urlpatterns = [
    path('auth/register/', UserRegisterAPIView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutAPIView.as_view(), name='logout'),

    path('users/profile/', UserProfileAPIView.as_view(), name='user_profile'),
    path('users/deactivate/', UserSoftDeleteAPIView.as_view(), name='user_deactivate'),
]