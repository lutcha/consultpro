from django.core.management.base import BaseCommand
from apps.users.models import User

ADMIN_EMAIL = 'admin@consultpro.cv'
ADMIN_PASSWORD = 'Admin@ConsultPro2026!'


class Command(BaseCommand):
    help = 'Create the platform admin user if it does not exist'

    def handle(self, *args, **options):
        if User.objects.filter(email=ADMIN_EMAIL).exists():
            self.stdout.write(f'  skip  {ADMIN_EMAIL} (already exists)')
            return

        user = User(
            email=ADMIN_EMAIL,
            username='admin',
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
