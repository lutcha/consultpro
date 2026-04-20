from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.permissions import IsConsultantOrManager

from ..models import Opportunity, Requirement, Risk
from .factories import OpportunityFactory, RequirementFactory, RiskFactory, UserFactory


class OpportunityViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

        # Patch permission class to allow tests to run without full role setup
        self.permission_patcher = patch.object(
            IsConsultantOrManager, 'has_permission', return_value=True
        )
        self.permission_patcher.start()
        self.addCleanup(self.permission_patcher.stop)

    def test_list_opportunities(self):
        OpportunityFactory.create_batch(3)
        url = reverse('opportunity-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_retrieve_opportunity(self):
        opportunity = OpportunityFactory()
        RequirementFactory(opportunity=opportunity)
        RiskFactory(opportunity=opportunity)

        url = reverse('opportunity-detail', kwargs={'pk': opportunity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], opportunity.title)
        self.assertIn('requirements', response.data)
        self.assertIn('risks', response.data)
        self.assertEqual(len(response.data['requirements']), 1)
        self.assertEqual(len(response.data['risks']), 1)

    def test_days_until_deadline(self):
        opportunity = OpportunityFactory(
            deadline=timezone.now() + timezone.timedelta(days=5)
        )
        url = reverse('opportunity-detail', kwargs={'pk': opportunity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['days_until_deadline'], 5)

    def test_go_action(self):
        opportunity = OpportunityFactory(status='analyzing')
        url = reverse('opportunity-go', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, 'go')

    def test_no_go_action(self):
        opportunity = OpportunityFactory(status='analyzing')
        url = reverse('opportunity-no_go', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, 'no_go')

    def test_analyze_tor_action(self):
        opportunity = OpportunityFactory(ai_analysis_status='pending')
        url = reverse('opportunity-analyze-tor', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.ai_analysis_status, 'processing')

    def test_upload_tor_no_file(self):
        opportunity = OpportunityFactory()
        url = reverse('opportunity-upload-tor', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requirements_action(self):
        opportunity = OpportunityFactory()
        RequirementFactory.create_batch(2, opportunity=opportunity)
        url = reverse('opportunity-requirements', kwargs={'pk': opportunity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_risks_action(self):
        opportunity = OpportunityFactory()
        RiskFactory.create_batch(3, opportunity=opportunity)
        url = reverse('opportunity-risks', kwargs={'pk': opportunity.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_by_status(self):
        OpportunityFactory(status='new')
        OpportunityFactory(status='won')
        url = reverse('opportunity-list')
        response = self.client.get(url, {'status': 'new'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'new')

    def test_search_by_title(self):
        OpportunityFactory(title='Unique Search Title')
        OpportunityFactory(title='Another One')
        url = reverse('opportunity-list')
        response = self.client.get(url, {'search': 'Unique'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Unique Search Title')

    def test_ordering_by_deadline(self):
        opp1 = OpportunityFactory(deadline=timezone.now() + timezone.timedelta(days=10))
        opp2 = OpportunityFactory(deadline=timezone.now() + timezone.timedelta(days=1))
        url = reverse('opportunity-list')
        response = self.client.get(url, {'ordering': 'deadline'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], opp2.pk)
        self.assertEqual(response.data['results'][1]['id'], opp1.pk)
