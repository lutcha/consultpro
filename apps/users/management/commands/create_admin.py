import os

from django.core.management.base import BaseCommand, CommandError
from apps.users.models import User

DEFAULT_ADMIN_EMAIL = 'admin@consultpro.cv'
DEFAULT_ADMIN_USERNAME = 'platform_admin'


class Command(BaseCommand):
    help = 'Create the platform admin user if it does not exist'

    def handle(self, *args, **options):
        admin_email = os.getenv('ADMIN_EMAIL', DEFAULT_ADMIN_EMAIL).strip().lower()
        admin_password = os.getenv('ADMIN_PASSWORD', '')
        admin_username = os.getenv('ADMIN_USERNAME', DEFAULT_ADMIN_USERNAME).strip()

        if not admin_password:
            raise CommandError('ADMIN_PASSWORD must be configured as a secret.')

        user = User.objects.filter(email=admin_email).first()
        if user:
            changed = False
            for field, value in {
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }.items():
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    changed = True
            if not user.check_password(admin_password):
                user.set_password(admin_password)
                changed = True

            if changed:
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  updated  {admin_email}'))
            else:
                self.stdout.write(f'  skip  {admin_email} (already configured)')
            return

        username = admin_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{admin_username}_{suffix}'

        user = User(
            email=admin_email,
            username=username,
            first_name='Admin',
            last_name='ConsultPro',
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        user.set_password(admin_password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'  created  {admin_email}'))
