from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.users.models import User


class CreateAdminCommandTests(TestCase):
    def test_requires_password_secret(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesMessage(CommandError, 'ADMIN_PASSWORD must be configured'):
                call_command('create_admin')

    def test_creates_active_platform_admin_from_environment(self):
        env = {
            'ADMIN_EMAIL': 'owner@example.com',
            'ADMIN_PASSWORD': 'StrongBootstrapPass123!',
            'ADMIN_USERNAME': 'owner_admin',
        }

        with patch.dict('os.environ', env, clear=True):
            call_command('create_admin', stdout=StringIO())

        user = User.objects.get(email='owner@example.com')
        self.assertEqual(user.username, 'owner_admin')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('StrongBootstrapPass123!'))

    def test_updates_existing_admin_and_rotates_password(self):
        user = User.objects.create_user(
            email='admin@consultpro.cv',
            username='platform_admin',
            password='OldPassword123!',
            role='viewer',
            is_active=False,
        )

        with patch.dict(
            'os.environ',
            {'ADMIN_PASSWORD': 'RotatedPassword456!'},
            clear=True,
        ):
            call_command('create_admin', stdout=StringIO())

        user.refresh_from_db()
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('RotatedPassword456!'))
