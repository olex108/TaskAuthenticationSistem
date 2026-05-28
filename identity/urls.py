from django.urls import path
from identity.views import (
    UserRegisterAPIView,
    LoginView,
    TokenRefreshView,
    LogoutAPIView,
    UserProfileAPIView,
    UserSoftDeleteAPIView,
    AdminPermissionListAPIView,
    AdminUserDetailsAPIView,
    AdminRoleListAPIView, AdminAssignUserRoleAPIView, AdminRevokeUserRoleAPIView, AdminAddRolePermissionAPIView,
    AdminRemoveRolePermissionAPIView
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

    path('admin/permissions/', AdminPermissionListAPIView.as_view(), name='admin_permissions_list'),
    path('admin/roles/', AdminRoleListAPIView.as_view(), name='admin_roles_list'),
    path('admin/users/<int:pk>/', AdminUserDetailsAPIView.as_view(), name='admin_user_access'),
    # Управление ролями пользователя
    path('admin/users/roles/assign/', AdminAssignUserRoleAPIView.as_view(), name='admin_user_role_assign'),
    path('admin/users/roles/revoke/', AdminRevokeUserRoleAPIView.as_view(), name='admin_user_role_revoke'),
    # Управление разрешениями ролей
    path('admin/roles/permissions/add/', AdminAddRolePermissionAPIView.as_view(), name='admin_role_permission_add'),
    path('admin/roles/permissions/remove/', AdminRemoveRolePermissionAPIView.as_view(),
         name='admin_role_permission_remove'),
]