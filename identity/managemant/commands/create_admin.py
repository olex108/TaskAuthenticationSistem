from django.core.management.base import BaseCommand
from identity.models import User, Role, UserRole
from identity.services.hasher import PasswordHasher


class Command(BaseCommand):
    """
    Management command to safely create a default administrator account.
    Runs idempotently inside Docker after the database seeding process.
    """

    help = 'Creates a default administrator user if it does not exist in the database'

    def handle(self, *args, **options):
        email = 'admin@admin.com'
        password = 'admin'
        role_name = 'administrator'

        self.stdout.write(f"Checking if administrator account '{email}' exists...")

        # 1. Check if the user already exists to ensure idempotency
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User '{email}' already exists. Skipping creation."))
            return

        # 2. Securely hash the password using your custom PasswordHasher (pwdlib)
        hashed_password = PasswordHasher.get_password_hash(password)

        # 3. Create the user record in PostgreSQL
        user = User.objects.create(
            email=email,
            password_hash=hashed_password,
            first_name='System',
            last_name='Admin',
            is_active=True
        )
        self.stdout.write(f"User account '{email}' created successfully.")

        # 4. Fetch the default 'administrator' role and link it via UserRole (M2M)
        admin_role = Role.objects.filter(name=role_name).first()
        if not admin_role:
            self.stdout.write(self.style.ERROR(
                f"Critical Error: Role '{role_name}' not found. "
                "Please run 'seed_roles' command first."
            ))
            return

        # Safely link user and role
        UserRole.objects.get_or_create(user=user, role=admin_role)

        self.stdout.write(self.style.SUCCESS(
            f"Successfully configured default admin!\n"
            f"Email: {email}\n"
            f"Password: {password}\n"
            f"Assigned Role: {role_name}"
        ))