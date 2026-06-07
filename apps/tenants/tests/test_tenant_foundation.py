from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APIClient
from django.test import TestCase
from django.utils import timezone

from apps.curriculum.models import Curriculum
from apps.knowledge.models import KnowledgeAsset
from apps.notifications.models import Notification
from apps.opportunities.models import FirmProfile, Opportunity, SavedFilter
from apps.opportunities.scoring import score_opportunity
from apps.proposals.models import Proposal
from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.tenants.models import (
    Tenant,
    TenantIntelligenceProfile,
    TenantMembership,
    TenantOnboardingSnapshot,
)
from apps.tenants.services import apply_onboarding_to_tenant, create_tenant_with_owner
from apps.users.models import User, UserInvitation


def make_user(email='user@example.com', role='manager'):
    return User.objects.create_user(
        username=email.split('@')[0],
        email=email,
        password='StrongPass123!',
        role=role,
    )


def auth_client(user, tenant):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_TENANT_ID=str(tenant.id))
    return client


def make_opportunity(tenant, title='Opportunity'):
    return Opportunity.objects.create(
        tenant=tenant,
        title=title,
        client='Client',
        sector='governance',
        country='cv',
        value=1000,
        currency='USD',
        deadline=timezone.now() + timezone.timedelta(days=20),
        description='Technical assistance opportunity.',
    )


class TenantServiceTests(TestCase):
    def test_create_tenant_with_owner_creates_context_records(self):
        owner = make_user('owner@example.com')

        tenant = create_tenant_with_owner('Beta Client', owner)

        self.assertEqual(tenant.memberships.get(user=owner).role, 'owner')
        self.assertTrue(hasattr(tenant, 'profile'))
        self.assertTrue(hasattr(tenant, 'strategy'))
        self.assertTrue(hasattr(tenant, 'intelligence_profile'))

    def test_onboarding_updates_intelligence_profile_and_snapshot(self):
        owner = make_user('owner2@example.com')
        tenant = create_tenant_with_owner('Strategy Client', owner)

        snapshot = apply_onboarding_to_tenant(
            tenant,
            {
                'strategic_objectives': ['Win GovTech work in West Africa'],
                'target_countries': ['cv', 'gw'],
                'target_sectors': ['digital_transformation'],
                'opportunity_keywords': ['technical assistance', 'govtech'],
                'excluded_keywords': ['vehicles only'],
                'minimum_score_threshold': 70,
                'ai_instructions': 'Prioritize institutional reform.',
            },
            submitted_by=owner,
        )

        profile = TenantIntelligenceProfile.objects.get(tenant=tenant)
        self.assertEqual(profile.minimum_score_threshold, 70)
        self.assertIn('technical assistance', profile.opportunity_keywords)
        self.assertEqual(profile.sector_priority_weights, {'digital_transformation': 80})
        self.assertEqual(profile.geographic_priority_weights, {'cv': 80, 'gw': 80})
        self.assertTrue(profile.created_from_onboarding)
        self.assertIsInstance(snapshot, TenantOnboardingSnapshot)
        self.assertTrue(FirmProfile.objects.filter(tenant=tenant, is_default=True).exists())
        self.assertTrue(
            SavedFilter.objects.filter(
                tenant=tenant,
                owner=owner,
                name='Tenant intelligence defaults',
            ).exists()
        )

    def test_onboarding_records_non_empty_overwrites(self):
        owner = make_user('overwrite-owner@example.com')
        tenant = create_tenant_with_owner('Overwrite Client', owner)
        tenant.profile.organization_description = 'Manual refinement'
        tenant.profile.save(update_fields=['organization_description'])
        tenant.intelligence_profile.ai_instructions = 'Manual AI guidance'
        tenant.intelligence_profile.save(update_fields=['ai_instructions'])

        apply_onboarding_to_tenant(
            tenant,
            {
                'organization_description': 'Assisted onboarding description',
                'ai_instructions': 'Assisted onboarding AI guidance',
            },
            submitted_by=owner,
        )

        tenant.refresh_from_db()
        overwritten_fields = {
            item['field']
            for entry in tenant.settings['onboarding_overwrite_log']
            for item in entry['items']
        }
        self.assertIn('organization_description', overwritten_fields)
        self.assertIn('ai_instructions', overwritten_fields)
        self.assertEqual(tenant.settings['last_onboarding_overwrites'][0]['source'], 'tenant_onboarding')

    def test_default_firm_profile_is_scoped_per_tenant(self):
        first_owner = make_user('first-owner@example.com')
        second_owner = make_user('second-owner@example.com')
        first = create_tenant_with_owner('First Client', first_owner)
        second = create_tenant_with_owner('Second Client', second_owner)

        FirmProfile.objects.create(tenant=first, name='First default', is_default=True)
        FirmProfile.objects.create(tenant=second, name='Second default', is_default=True)

        self.assertTrue(FirmProfile.objects.get(tenant=first).is_default)
        self.assertTrue(FirmProfile.objects.get(tenant=second).is_default)

    def test_opportunity_scoring_uses_tenant_intelligence_context(self):
        owner = make_user('score-owner@example.com')
        tenant = create_tenant_with_owner('Scoring Client', owner)
        apply_onboarding_to_tenant(
            tenant,
            {
                'target_countries': ['cv'],
                'target_sectors': ['digital_transformation'],
                'opportunity_keywords': ['govtech'],
                'excluded_keywords': ['vehicles only'],
            },
            submitted_by=owner,
        )
        opportunity = make_opportunity(tenant, 'GovTech technical assistance')
        opportunity.sector = 'digital_transformation'
        opportunity.description = 'GovTech advisory and institutional reform assignment.'
        opportunity.save()

        score = score_opportunity(opportunity)

        self.assertTrue(score.input_snapshot['tenant_profile_applied'])
        self.assertIn('govtech', score.input_snapshot['tenant_keyword_matches'])


class TenantAPITests(TestCase):
    def setUp(self):
        self.owner = make_user('api-owner@example.com', role='admin')
        self.tenant = create_tenant_with_owner('API Client', self.owner)
        self.other_tenant = Tenant.objects.create(name='Other Client', slug='other-client')
        self.client = auth_client(self.owner, self.tenant)

    def test_current_tenant_uses_header_context(self):
        response = self.client.get(reverse('tenant-current'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], str(self.tenant.id))

    def test_tenant_invite_creates_tenant_scoped_invitation(self):
        with patch('apps.tenants.views.send_invitation_email') as mocked_send:
            response = self.client.post(
                reverse('tenant-invite', kwargs={'id': self.tenant.id}),
                {'email': 'invitee@example.com', 'role': 'manager'},
                format='json',
            )

        self.assertEqual(response.status_code, 201)
        mocked_send.assert_called_once()
        invitation = UserInvitation.objects.get(email='invitee@example.com')
        self.assertEqual(invitation.tenant, self.tenant)
        self.assertEqual(invitation.tenant_role, 'manager')

    def test_tenant_invite_deletes_invitation_when_email_fails(self):
        from apps.users.emails import EmailDeliveryError

        with patch('apps.tenants.views.send_invitation_email', side_effect=EmailDeliveryError('SMTP down')):
            response = self.client.post(
                reverse('tenant-invite', kwargs={'id': self.tenant.id}),
                {'email': 'failed@example.com', 'role': 'manager'},
                format='json',
            )

        self.assertEqual(response.status_code, 502)
        self.assertFalse(UserInvitation.objects.filter(email='failed@example.com').exists())

    def test_onboarding_endpoint_accepts_sectioned_payload_and_preserves_raw_snapshot(self):
        response = self.client.post(
            reverse('tenant-onboarding', kwargs={'id': self.tenant.id}),
            {
                'responses': {
                    'organization': {
                        'legal_name': 'API Client Legal',
                        'primary_country': 'cv',
                    },
                    'capabilities': {
                        'core_capabilities': ['digital advisory'],
                    },
                    'markets': {
                        'target_countries': ['cv'],
                        'target_sectors': ['digital_transformation'],
                    },
                    'opportunity_preferences': {
                        'opportunity_keywords': ['govtech'],
                        'minimum_score_threshold': 75,
                    },
                    'go_no_go_preferences': {
                        'go_no_go_preferences': {
                            'must_have': ['clear ToR'],
                            'red_flags': ['unfunded'],
                        },
                    },
                    'ai_positioning': {
                        'ai_instructions': 'Use institutional reform positioning.',
                    },
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        snapshot = TenantOnboardingSnapshot.objects.get(pk=response.data['id'])
        self.assertIn('organization', snapshot.responses)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.primary_country, 'cv')
        self.assertEqual(self.tenant.profile.legal_name, 'API Client Legal')
        self.assertEqual(self.tenant.strategy.go_no_go_preferences['must_have'], ['clear ToR'])
        self.assertEqual(self.tenant.intelligence_profile.minimum_score_threshold, 75)

    def test_non_member_cannot_access_tenant_from_header(self):
        outsider = make_user('outsider@example.com')
        client = auth_client(outsider, self.tenant)

        response = client.get(reverse('tenant-current'))

        self.assertEqual(response.status_code, 403)

    def test_opportunities_are_scoped_by_tenant(self):
        visible = make_opportunity(self.tenant, 'Visible Opportunity')
        make_opportunity(self.other_tenant, 'Hidden Opportunity')

        response = self.client.get(reverse('opportunity-list'))

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(visible.id, ids)
        self.assertNotIn('Hidden Opportunity', [item['title'] for item in response.data['results']])

    def test_proposals_are_scoped_by_tenant(self):
        visible_opp = make_opportunity(self.tenant, 'Visible Opp')
        hidden_opp = make_opportunity(self.other_tenant, 'Hidden Opp')
        visible = Proposal.objects.create(
            tenant=self.tenant,
            opportunity=visible_opp,
            title='Visible Proposal',
            created_by=self.owner,
        )
        Proposal.objects.create(
            tenant=self.other_tenant,
            opportunity=hidden_opp,
            title='Hidden Proposal',
            created_by=self.owner,
        )

        response = self.client.get(reverse('proposal-list'))

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(visible.id, ids)
        self.assertNotIn('Hidden Proposal', [item['title'] for item in response.data['results']])

    def test_scraping_sources_and_opportunities_are_scoped_by_tenant(self):
        source = ScrapingSource.objects.create(
            tenant=self.tenant,
            name='Visible Source',
            organization='Org',
            url='https://example.org',
        )
        ScrapingSource.objects.create(
            tenant=self.other_tenant,
            name='Hidden Source',
            organization='Org',
            url='https://hidden.example.org',
        )
        scraped = ScrapedOpportunity.objects.create(
            tenant=self.tenant,
            source=source,
            external_id='visible',
            external_url='https://example.org/visible',
            title='Visible Scraped',
            organization='Org',
        )

        sources = self.client.get(reverse('scraping:scraping-source-list'))
        opportunities = self.client.get(reverse('scraping:scraped-opportunity-list'))

        self.assertEqual(sources.status_code, 200)
        self.assertNotIn('Hidden Source', [item['name'] for item in sources.data['results']])
        self.assertEqual(opportunities.status_code, 200)
        self.assertIn(scraped.id, [item['id'] for item in opportunities.data['results']])

    def test_scraped_opportunities_apply_tenant_intelligence_defaults(self):
        apply_onboarding_to_tenant(
            self.tenant,
            {
                'target_countries': ['cv'],
                'target_sectors': ['digital_transformation'],
                'opportunity_keywords': ['govtech'],
            },
            submitted_by=self.owner,
        )
        source = ScrapingSource.objects.create(
            tenant=self.tenant,
            name='World Bank',
            organization='World Bank',
            url='https://example.org/worldbank',
        )
        visible = ScrapedOpportunity.objects.create(
            tenant=self.tenant,
            source=source,
            external_id='visible-intel',
            external_url='https://example.org/visible-intel',
            title='GovTech advisory',
            organization='World Bank',
            sector='digital_transformation',
            country='cv',
        )
        ScrapedOpportunity.objects.create(
            tenant=self.tenant,
            source=source,
            external_id='hidden-intel',
            external_url='https://example.org/hidden-intel',
            title='Road works',
            organization='World Bank',
            sector='infrastructure',
            country='sn',
        )

        response = self.client.get(reverse('scraping:scraped-opportunity-list'))

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.data['results']]
        self.assertIn(visible.id, ids)
        self.assertNotIn('Road works', [item['title'] for item in response.data['results']])

    def test_curriculum_knowledge_and_notifications_are_scoped_by_tenant(self):
        Curriculum.objects.create(
            tenant=self.tenant,
            user=self.owner,
            file_name='visible.pdf',
            file='curricula/visible.pdf',
            file_type='pdf',
        )
        Curriculum.objects.create(
            tenant=self.other_tenant,
            user=self.owner,
            file_name='hidden.pdf',
            file='curricula/hidden.pdf',
            file_type='pdf',
        )
        KnowledgeAsset.objects.create(
            tenant=self.tenant,
            title='Visible Knowledge',
            asset_type='case',
            created_by=self.owner,
        )
        KnowledgeAsset.objects.create(
            tenant=self.other_tenant,
            title='Hidden Knowledge',
            asset_type='case',
            created_by=self.owner,
        )
        Notification.objects.create(
            tenant=self.tenant,
            user=self.owner,
            type='info',
            title='Visible Notification',
            message='Visible',
        )
        Notification.objects.create(
            tenant=self.other_tenant,
            user=self.owner,
            type='info',
            title='Hidden Notification',
            message='Hidden',
        )

        curricula = self.client.get(reverse('curriculum:curriculum-list'))
        knowledge = self.client.get(reverse('knowledge-asset-list'))
        notifications = self.client.get(reverse('notification-list'))

        self.assertEqual(curricula.status_code, 200)
        self.assertNotIn('hidden.pdf', [item['file_name'] for item in curricula.data['results']])
        self.assertEqual(knowledge.status_code, 200)
        self.assertNotIn('Hidden Knowledge', [item['title'] for item in knowledge.data['results']])
        self.assertEqual(notifications.status_code, 200)
        self.assertNotIn('Hidden Notification', [item['title'] for item in notifications.data['results']])
