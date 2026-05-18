from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.opportunities.tests.factories import UserFactory
from apps.partners.tests.factories import PartnerProfileFactory


class PartnerProfileViewSetTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=UserFactory(role='manager'))

    def test_list_partners(self):
        PartnerProfileFactory(name='Regional Partner')

        response = self.client.get(reverse('partner-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['name'], 'Regional Partner')

    def test_create_partner(self):
        response = self.client.post(
            reverse('partner-list'),
            {
                'name': 'New Partner',
                'sectors': ['ict'],
                'geographies': ['cv'],
                'capabilities': ['delivery'],
                'trust_score': 75,
                'is_active': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['trust_score'], 75)
