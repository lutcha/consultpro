from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.permissions import IsConsultantOrManager

from apps.opportunities.models import FirmProfile, Opportunity, OpportunityScore, Requirement, Risk, SavedFilter
from apps.opportunities.scoring import score_opportunity
from apps.partners.tests.factories import PartnerProfileFactory
from apps.proposals.models import Proposal
from apps.opportunities.tests.factories import (
    OpportunityFactory,
    RequirementFactory,
    RiskFactory,
    UserFactory,
)


class OpportunityViewSetTests(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=UserFactory())

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
        url = reverse('opportunity-no-go', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, 'no_go')

    def test_create_proposal_action_creates_default_sections_and_is_idempotent(self):
        opportunity = OpportunityFactory(status='go', ai_summary='Resumo IA inicial')
        url = reverse('opportunity-create-proposal', kwargs={'pk': opportunity.pk})

        first = self.client.post(url)
        second = self.client.post(url)

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertTrue(first.data['created'])
        self.assertFalse(second.data['created'])
        self.assertEqual(first.data['proposal_id'], second.data['proposal_id'])
        self.assertEqual(Proposal.objects.filter(opportunity=opportunity).count(), 1)

        proposal = Proposal.objects.get(pk=first.data['proposal_id'])
        self.assertEqual(proposal.sections.count(), 7)
        self.assertTrue(proposal.sections.filter(section_type='executive_summary', content__contains='Resumo IA inicial').exists())

        opportunity.refresh_from_db()
        self.assertEqual(opportunity.status, 'proposal_draft')

    def test_analyze_tor_action(self):
        opportunity = OpportunityFactory(ai_analysis_status='pending')
        url = reverse('opportunity-analyze-tor', kwargs={'pk': opportunity.pk})
        with patch('apps.opportunities.tasks.analyze_tor_document.delay') as mock_delay:
            response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertEqual(opportunity.ai_analysis_status, 'queued')
        mock_delay.assert_called_once_with(opportunity.id)

    def test_upload_tor_requires_file(self):
        opportunity = OpportunityFactory()
        url = reverse('opportunity-upload-tor', kwargs={'pk': opportunity.pk})
        response = self.client.post(url, data={}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_tor_saves_file_and_queues_analysis(self):
        opportunity = OpportunityFactory(ai_analysis_status='pending')
        url = reverse('opportunity-upload-tor', kwargs={'pk': opportunity.pk})
        tor_file = SimpleUploadedFile(
            'tor.pdf',
            b'%PDF-1.4 test tor content',
            content_type='application/pdf',
        )

        with patch('apps.opportunities.tasks.analyze_tor_document.delay') as mock_delay:
            response = self.client.post(
                url,
                data={'tor_document': tor_file},
                format='multipart',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        opportunity.refresh_from_db()
        self.assertTrue(opportunity.tor_document.name.endswith('.pdf'))
        self.assertEqual(opportunity.ai_analysis_status, 'queued')
        mock_delay.assert_called_once_with(opportunity.id, '')

    def test_filter_by_status(self):
        OpportunityFactory(status='new')
        OpportunityFactory(status='analyzing')
        url = reverse('opportunity-list')
        response = self.client.get(url, {'status': 'new'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'new')

    def test_firm_profile_defaults_apply_when_no_explicit_geo_filters(self):
        matching = OpportunityFactory(sector='ict', country='cv')
        OpportunityFactory(sector='health', country='sn')
        FirmProfile.objects.create(
            name='CV ICT',
            target_sectors=['ict'],
            geographies=['cv'],
            is_default=True,
        )

        url = reverse('opportunity-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {matching.id})

    def test_explicit_filter_overrides_firm_profile_defaults(self):
        OpportunityFactory(sector='ict', country='cv')
        explicit = OpportunityFactory(sector='health', country='sn')
        FirmProfile.objects.create(
            name='CV ICT',
            target_sectors=['ict'],
            geographies=['cv'],
            is_default=True,
        )

        url = reverse('opportunity-list')
        response = self.client.get(url, {'sector': 'health'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {explicit.id})

    def test_search_by_title(self):
        OpportunityFactory(title='Unique Search Title')
        OpportunityFactory(title='Another Title')
        url = reverse('opportunity-list')
        response = self.client.get(url, {'search': 'Unique'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('Unique', response.data['results'][0]['title'])

    def test_ordering_by_deadline(self):
        opp1 = OpportunityFactory(deadline=timezone.now() + timezone.timedelta(days=1))
        opp2 = OpportunityFactory(deadline=timezone.now() + timezone.timedelta(days=5))
        url = reverse('opportunity-list')
        response = self.client.get(url, {'ordering': 'deadline'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['id'], opp1.id)
        self.assertEqual(response.data['results'][1]['id'], opp2.id)

    def test_score_action_creates_explainable_score(self):
        opportunity = OpportunityFactory(
            ai_summary='Resumo IA',
            ai_extraction={'cos_analysis': {'team_requirements': ['Especialista M&A']}},
            value=150000,
        )
        RequirementFactory(opportunity=opportunity, priority='mandatory')
        RiskFactory(opportunity=opportunity, severity='high')

        url = reverse('opportunity-score', kwargs={'pk': opportunity.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opportunity'], opportunity.id)
        self.assertIn('overall_score', response.data)
        self.assertIn('reasoning_trace', response.data)
        self.assertIn('confidence_score', response.data)
        self.assertEqual(len(response.data['reasoning_trace']), 5)
        self.assertTrue(OpportunityScore.objects.filter(opportunity=opportunity, is_current=True).exists())

    def test_score_action_returns_current_score_without_refresh(self):
        opportunity = OpportunityFactory()
        score = score_opportunity(opportunity)
        url = reverse('opportunity-score', kwargs={'pk': opportunity.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], score.id)
        self.assertEqual(OpportunityScore.objects.filter(opportunity=opportunity).count(), 1)

    def test_score_action_refresh_marks_previous_score_not_current(self):
        opportunity = OpportunityFactory()
        old_score = score_opportunity(opportunity)
        url = reverse('opportunity-score', kwargs={'pk': opportunity.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_score.refresh_from_db()
        self.assertFalse(old_score.is_current)
        self.assertEqual(OpportunityScore.objects.filter(opportunity=opportunity, is_current=True).count(), 1)

    def test_suggestions_action_returns_partner_and_consultant_matches(self):
        opportunity = OpportunityFactory(sector='ict', country='cv')
        partner = PartnerProfileFactory(
            name='ICT Delivery Partner',
            sectors=['ict'],
            geographies=['cv'],
            capabilities=['delivery'],
            trust_score=70,
        )
        consultant = UserFactory(
            first_name='Joana',
            last_name='Lopes',
            role='consultant',
            availability='available',
            skills=['ict'],
            languages=['pt'],
            location='cv',
            years_experience=6,
        )

        url = reverse('opportunity-suggestions', kwargs={'pk': opportunity.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opportunity'], opportunity.id)
        self.assertEqual(response.data['partners'][0]['id'], partner.id)
        self.assertEqual(response.data['consultants'][0]['id'], consultant.id)
        self.assertIn('reasoning_trace', response.data['partners'][0])
        self.assertIn('confidence_score', response.data['consultants'][0])


class FirmProfileViewSetTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)

    def test_current_returns_default_profile(self):
        profile = FirmProfile.objects.create(name='Default', target_sectors=['ict'])

        url = reverse('firm-profile-current')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], profile.id)
        self.assertEqual(response.data['target_sectors'], ['ict'])

    def test_create_sets_updated_by(self):
        url = reverse('firm-profile-list')
        response = self.client.post(
            url,
            {
                'name': 'West Africa',
                'target_sectors': ['ict'],
                'geographies': ['cv', 'sn'],
                'scoring_weights_override': {'strategic_fit': 30},
                'is_default': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile = FirmProfile.objects.get(pk=response.data['id'])
        self.assertEqual(profile.updated_by, self.user)


class SavedFilterViewSetTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='consultant')
        self.other = UserFactory(role='consultant')
        self.client.force_authenticate(user=self.user)

    def test_create_saved_filter_sets_owner(self):
        url = reverse('saved-filter-list')
        response = self.client.post(
            url,
            {
                'name': 'CV ICT',
                'view_type': 'opportunities',
                'payload': {'country': 'cv', 'sector': 'ict'},
                'is_shared': False,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        saved_filter = SavedFilter.objects.get(pk=response.data['id'])
        self.assertEqual(saved_filter.owner, self.user)

    def test_list_returns_owned_and_shared_filters_only(self):
        owned = SavedFilter.objects.create(owner=self.user, name='Mine', payload={'country': 'cv'})
        shared = SavedFilter.objects.create(owner=self.other, name='Shared', payload={}, is_shared=True)
        SavedFilter.objects.create(owner=self.other, name='Private', payload={}, is_shared=False)

        url = reverse('saved-filter-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {owned.id, shared.id})

    def test_shared_filter_is_read_only_for_non_owner(self):
        shared = SavedFilter.objects.create(owner=self.other, name='Shared', payload={}, is_shared=True)

        url = reverse('saved-filter-detail', kwargs={'pk': shared.pk})
        response = self.client.patch(url, {'name': 'Changed'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        shared.refresh_from_db()
        self.assertEqual(shared.name, 'Shared')
