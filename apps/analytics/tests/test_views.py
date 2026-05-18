from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.opportunities.tests.factories import OpportunityFactory, UserFactory


class AnalyticsViewSetTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(user=UserFactory(role='manager'))

    def test_trends_endpoint_returns_contract(self):
        OpportunityFactory(sector='ict', country='cv', status='won')

        response = self.client.get(reverse('analytics-trends'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('win_rate_by_sector', response.data)
        self.assertIn('weighted_pipeline', response.data)
        self.assertIn('avg_stage_duration_days', response.data)
        self.assertIn('opportunity_status_counts', response.data)

    def test_trends_endpoint_accepts_predictive_query_params(self):
        OpportunityFactory(sector='ict', country='cv', status='go')

        response = self.client.get(
            reverse('analytics-trends'),
            {'country': 'cv', 'sector': 'ict', 'horizon': '6', 'include_forecast': 'true'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['meta']['country'], 'cv')
        self.assertEqual(response.data['meta']['sector'], 'ict')
        self.assertEqual(response.data['meta']['horizon_months'], 6)
        self.assertIn('descriptive', response.data)
        self.assertIn('demand_forecast', response.data['predictive'])
        self.assertIn('X-Analytics-Cache', response)
