from django.db import models


class User(models.Model):
    """
    Custom model of user with pk - id.
    """

    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.email}|{self.is_active}"


class Role(models.Model):
    """
    Role of user (for example: admin, manager, user).
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "roles"
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Permissions (for example: view_mock_data, edit_rules).
    """

    code = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "permissions"
        verbose_name = "Разрешение"
        verbose_name_plural = "Разрешения"

    def __str__(self):
        return self.code


class UserRole(models.Model):
    """
    Table M2M: bind User - Role.
    If Pole or User deleted - del record.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_users")

    class Meta:
        db_table = "user_roles"
        unique_together = ("user", "role")
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"


class RolePermission(models.Model):
    """
    Table M2M: bind Role - Permission.
    """

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="permission_roles")

    class Meta:
        db_table = "role_permissions"
        # Уникальный индекс, чтобы нельзя было привязать право к роли дважды
        unique_together = ("role", "permission")
        verbose_name = "Разрешение роли"
        verbose_name_plural = "Разрешения ролей"


class RefreshToken(models.Model):
    """
    Таблица для отслеживания активных/отозванных refresh-токенов.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_token")
    refresh_token = models.CharField(max_length=255, unique=True, db_index=True)
    is_logout = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "refresh_tokens"
