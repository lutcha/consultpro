from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.users.models import User


class CreateAdminCommandTests(TestCase):
    @override_settings()
    def test_skips_creation_when_admin_password_not_set(self):
        import os
        os.environ.pop('ADMIN_PASSWORD', None)

        call_command('create_admin')

        self.assertFalse(User.objects.filter(email='admin@consultpro.cv').exists())

    def test_creates_admin_when_admin_password_set(self):
        import os
        os.environ['ADMIN_PASSWORD'] = 'Some-Strong-Test-Password-123!'
        try:
            call_command('create_admin')
        finally:
            os.environ.pop('ADMIN_PASSWORD', None)

        user = User.objects.get(email='admin@consultpro.cv')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.check_password('Some-Strong-Test-Password-123!'))

    def test_existing_admin_is_repaired_without_needing_password(self):
        import os
        os.environ.pop('ADMIN_PASSWORD', None)
        User.objects.create_user(
            username='platform_admin',
            email='admin@consultpro.cv',
            password='whatever',
            role='consultant',
            is_staff=False,
            is_superuser=False,
        )

        call_command('create_admin')

        user = User.objects.get(email='admin@consultpro.cv')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
