from django.test import TestCase
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
