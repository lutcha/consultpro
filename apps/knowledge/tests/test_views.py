from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.knowledge.models import KnowledgeAsset
from apps.opportunities.tests.factories import UserFactory
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory


class KnowledgeViewTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)

    def test_search_endpoint_returns_explainable_results(self):
        KnowledgeAsset.objects.create(
            asset_type='template',
            title='AfDB WASH proposal template',
            content='Water sanitation methodology and staffing plan',
            country='Senegal',
            sector='WASH',
        )

        response = self.client.get(reverse('knowledge-asset-search'), {'q': 'wash methodology'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['search_mode'], 'textual_fallback')
        self.assertEqual(response.data['count'], 1)
        self.assertTrue(response.data['results'][0]['reasoning_trace'])

    def test_search_endpoint_filters_by_source_app(self):
        KnowledgeAsset.objects.create(
            asset_type='proposal',
            title='Education proposal',
            content='Teacher training delivery model',
            source_app='proposals',
            source_model='Proposal',
        )
        KnowledgeAsset.objects.create(
            asset_type='template',
            title='Education template',
            content='Teacher training delivery model',
            source_app='manual',
            source_model='Template',
        )

        response = self.client.get(
            reverse('knowledge-asset-search'),
            {'q': 'education training', 'source_app': 'manual'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['asset']['source_app'], 'manual')

    def test_index_endpoint_indexes_proposal_assets(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Workplan', content='Implementation plan')

        response = self.client.post(reverse('knowledge-asset-index'), {'source': 'proposals'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['indexed'], 2)
        self.assertEqual(response.data['run']['status'], 'completed')
        self.assertEqual(response.data['run']['source'], 'proposals')

    def test_index_endpoint_rejects_unknown_source(self):
        response = self.client.post(reverse('knowledge-asset-index'), {'source': 'unknown'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
