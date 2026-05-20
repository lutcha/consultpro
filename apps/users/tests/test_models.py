from django.test import TestCase
from django.utils import timezone
from apps.users.models import UserInvitation
from apps.users.tests.factories import UserFactory, CertificationFactory


class UserModelTest(TestCase):
    def test_user_creation(self):
        user = UserFactory(email='test@example.com', username='testuser')
        self.assertEqual(str(user), 'test@example.com')

    def test_role_default(self):
        user = UserFactory()
        self.assertEqual(user.role, 'consultant')

    def test_availability_default(self):
        user = UserFactory()
        self.assertEqual(user.availability, 'available')

    def test_name_display(self):
        user = UserFactory(first_name='Jane', last_name='Doe')
        self.assertEqual(f"{user.first_name} {user.last_name}", 'Jane Doe')


class CertificationModelTest(TestCase):
    def test_certification_user_relation(self):
        user = UserFactory()
        cert = CertificationFactory(user=user)
        self.assertEqual(cert.user, user)
        self.assertIn(cert, user.certifications.all())


class UserInvitationModelTest(TestCase):
    def setUp(self):
        self.admin = UserFactory(role='admin')

    def test_create_for_helper(self):
        inv = UserInvitation.create_for(
            email='invited@example.com',
            role='consultant',
            invited_by=self.admin,
        )
        self.assertEqual(inv.email, 'invited@example.com')
        self.assertEqual(inv.role, 'consultant')
        self.assertFalse(inv.is_used)
        self.assertIsNotNone(inv.token)

    def test_is_valid_fresh(self):
        inv = UserInvitation.create_for('x@x.com', 'consultant', self.admin)
        self.assertTrue(inv.is_valid)

    def test_is_invalid_when_used(self):
        inv = UserInvitation.create_for('x@x.com', 'consultant', self.admin)
        inv.is_used = True
        inv.save()
        self.assertFalse(inv.is_valid)

    def test_is_invalid_when_expired(self):
        from datetime import timedelta
        inv = UserInvitation.create_for('x@x.com', 'consultant', self.admin, days_valid=0)
        inv.expires_at = timezone.now() - timedelta(seconds=1)
        inv.save()
        self.assertFalse(inv.is_valid)
