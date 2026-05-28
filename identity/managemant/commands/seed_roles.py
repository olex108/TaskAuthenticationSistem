from django.core.management.base import BaseCommand
from django.db import transaction

from identity.models import Permission, Role, RolePermission


class Command(BaseCommand):
    """
    Management command to safely initialize default roles and atomic permissions.
    Runs idempotently inside Docker during containers startup.
    """

    help = "Seeds the database with default system roles and permissions if they do not exist"

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding process...")

        # Wrapping in a single transaction to ensure atomicity
        with transaction.atomic():

            # =====================================================================
            # 1. SEED PERMISSIONS
            # =====================================================================
            permissions_data = [
                {
                    "code": "admin:access",
                    "description": "Full administrative access to manage roles, permissions, and users",
                },
                {"code": "mock:view_analytics", "description": "Access to view business mock analytics endpoints"},
                {
                    "code": "mock:edit_data",
                    "description": "Access to modify or update business mock configuration data",
                },
            ]

            permissions_pool = {}
            for perm in permissions_data:
                # get_or_create ensures we don't throw an IntegrityError if rows exist
                obj, created = Permission.objects.get_or_create(
                    code=perm["code"], defaults={"description": perm["description"]}
                )
                permissions_pool[perm["code"]] = obj
                if created:
                    self.stdout.write(f"Permission created: [{perm['code']}]")

            # =====================================================================
            # 2. SEED ROLES
            # =====================================================================
            roles_data = [
                {"name": "administrator", "description": "System owner with unrestricted configuration access"},
                {"name": "moderator", "description": "Staff member responsible for inspecting data and analytics"},
                {"name": "user", "description": "Standard application client with restricted profile access"},
            ]

            roles_pool = {}
            for role in roles_data:
                obj, created = Role.objects.get_or_create(
                    name=role["name"], defaults={"description": role["description"]}
                )
                roles_pool[role["name"]] = obj
                if created:
                    self.stdout.write(f"Role created: [{role['name']}]")

            # =====================================================================
            # 3. BIND ROLE <-> PERMISSIONS (M2M)
            # =====================================================================
            self.stdout.write("Linking roles and permissions...")

            # Administrator gets ALL permissions
            RolePermission.objects.get_or_create(
                role=roles_pool["administrator"], permission=permissions_pool["admin:access"]
            )
            RolePermission.objects.get_or_create(
                role=roles_pool["administrator"], permission=permissions_pool["mock:view_analytics"]
            )
            RolePermission.objects.get_or_create(
                role=roles_pool["administrator"], permission=permissions_pool["mock:edit_data"]
            )

            # Moderator can view analytics and edit business data, but cannot touch admin panel
            RolePermission.objects.get_or_create(
                role=roles_pool["moderator"], permission=permissions_pool["mock:view_analytics"]
            )
            RolePermission.objects.get_or_create(
                role=roles_pool["moderator"], permission=permissions_pool["mock:edit_data"]
            )

            # Standard User gets NO special permissions (they can only view/update their own profile)

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
