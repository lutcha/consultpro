from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.users.tests.factories import UserFactory


class UserViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(role='consultant')
        self.manager = UserFactory(role='manager')
        self.admin = UserFactory(role='admin')

    def test_list_unauthenticated(self):
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_consultant(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-detail', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_me_endpoint_get(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_me_endpoint_put(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse('user-me'),
            {'first_name': 'Updated'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_skills_action(self):
        self.client.force_authenticate(user=self.user)
        self.user.skills = ['Python', 'Django']
        self.user.save()
        response = self.client.get(reverse('user-skills', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['skills'], ['Python', 'Django'])

    def test_availability_action(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('user-availability', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['availability'], 'available')
