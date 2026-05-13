from django.core.management.base import BaseCommand
from apps.users.models import User

ADMIN_EMAIL = 'admin@consultpro.cv'
ADMIN_PASSWORD = 'Admin@ConsultPro2026!'
ADMIN_USERNAME = 'platform_admin'


class Command(BaseCommand):
    help = 'Create the platform admin user if it does not exist'

    def handle(self, *args, **options):
        user = User.objects.filter(email=ADMIN_EMAIL).first()
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
            if changed:
                user.save(update_fields=['role', 'is_staff', 'is_superuser', 'is_active'])
                self.stdout.write(self.style.SUCCESS(f'  updated  {ADMIN_EMAIL}'))
            else:
                self.stdout.write(f'  skip  {ADMIN_EMAIL} (already has platform admin access)')
            return

        username = ADMIN_USERNAME
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{ADMIN_USERNAME}_{suffix}'

        user = User(
            email=ADMIN_EMAIL,
            username=username,
            first_name='Admin',
            last_name='ConsultPro',
            role='admin',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        user.set_password(ADMIN_PASSWORD)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'  created  {ADMIN_EMAIL}'))
