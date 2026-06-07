from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.proposals.export_execution import execute_export_request
from apps.proposals.models import Proposal, ProposalExportRequest
from apps.quality_checks.models import QualityCheck
from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.scraping.scrapers.worldbank_scraper import WorldBankScraper
from apps.scraping.services.opportunity_importer import import_scraped_opportunity
from apps.tenants.models import Tenant
from apps.users.models import User, UserInvitation


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='qa@consultpro.cv',
    FRONTEND_URL='https://consultpro.cv',
)
class BetaReleaseQASmokeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='beta_admin',
            email='beta.admin@example.com',
            password='StrongPass123!',
            role='manager',
            is_staff=True,
        )
        self.client.force_authenticate(self.admin)

    def test_controlled_beta_smoke_flow(self):
        tenant_response = self.client.post(
            '/api/tenants/',
            {
                'name': 'Beta QA Tenant',
                'slug': 'beta-qa-tenant',
                'organization_type': 'consulting_firm',
                'size': 'small',
                'primary_country': 'CV',
            },
            format='json',
        )
        self.assertEqual(tenant_response.status_code, 201, tenant_response.data)
        tenant = Tenant.objects.get(id=tenant_response.data['id'])
        tenant_header = {'HTTP_X_TENANT_ID': str(tenant.id)}

        invite_response = self.client.post(
            f'/api/tenants/{tenant.id}/invite/',
            {'email': 'beta.owner@example.com', 'role': 'owner'},
            format='json',
            **tenant_header,
        )
        self.assertEqual(invite_response.status_code, 201, invite_response.data)
        invitation = UserInvitation.objects.get(email='beta.owner@example.com')
        self.assertEqual(invitation.tenant, tenant)
        self.assertEqual(invitation.tenant_role, 'owner')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('https://consultpro.cv/accept-invitation/', mail.outbox[0].body)

        onboarding_response = self.client.post(
            f'/api/tenants/{tenant.id}/onboarding/',
            {
                'responses': {
                    'organization_description': 'Cape Verde consulting team focused on public-sector reform.',
                    'core_capabilities': ['technical assistance', 'digital government'],
                    'target_countries': ['Cabo Verde', 'Guinea-Bissau'],
                    'target_sectors': ['Consultant Services', 'Governance'],
                    'target_donors': ['World Bank'],
                    'opportunity_keywords': ['technical assistance', 'consulting services'],
                    'excluded_keywords': ['vehicles only'],
                    'deadline_min_days': 7,
                    'deadline_max_days': 180,
                    'ai_instructions': 'Position the firm as a senior Lusophone implementation partner.',
                },
            },
            format='json',
            **tenant_header,
        )
        self.assertEqual(onboarding_response.status_code, 201, onboarding_response.data)
        tenant.refresh_from_db()
        self.assertEqual(tenant.intelligence_profile.opportunity_keywords, ['technical assistance', 'consulting services'])

        source = ScrapingSource.objects.create(
            tenant=tenant,
            name='World Bank QA Source',
            organization='World Bank Group',
            url='https://projects.worldbank.org/en/projects-operations/procurement',
            source_type='api',
            scraper_class='WorldBankScraper',
            scraper_config={'api_url': WorldBankScraper.API_URL},
        )
        scraper = WorldBankScraper(source)
        parsed_items = scraper.parse(
            '{"procnotices":[{'
            '"id":"OP-BETA-QA-1",'
            '"project_name":"Cabo Verde Digital Governance Technical Assistance",'
            '"notice_type":"Request for Expression of Interest",'
            '"submission_deadline_date":"2026-09-30T23:59:59Z",'
            '"project_ctry_name":"Cabo Verde",'
            '"regionname":"Western And Central Africa",'
            '"procurement_group_desc":"Consultant Services",'
            '"procurement_method_name":"Quality And Cost-Based Selection",'
            '"notice_text":"Technical assistance for public digital services and institutional reform.",'
            '"url":"https://projects.worldbank.org/en/projects-operations/procurement-detail/OP-BETA-QA-1"'
            '}]}'
        )
        self.assertEqual(len(parsed_items), 1)
        parsed = parsed_items[0]

        scraped = ScrapedOpportunity.objects.create(
            tenant=tenant,
            source=source,
            external_id=parsed['external_id'],
            external_url=parsed['external_url'],
            title=parsed['title'],
            organization=parsed['organization'],
            client='World Bank',
            sector=parsed['sector'],
            country=parsed['country'],
            region=parsed['region'],
            description=parsed['description'],
            value=Decimal('250000.00'),
            currency='USD',
            deadline=timezone.now() + timezone.timedelta(days=60),
            status='new',
            cv_eligible=True,
            data_quality_score=Decimal('0.92'),
            ai_summary='World Bank technical assistance opportunity for Cabo Verde.',
            ai_extracted_requirements=[
                {'description': 'Demonstrated digital government experience', 'priority': 'mandatory'},
                {'description': 'Lusophone public-sector delivery experience', 'priority': 'important'},
            ],
            raw_payload=parsed,
        )

        import_result = import_scraped_opportunity(scraped, user=self.admin)
        self.assertTrue(import_result['created'])
        opportunity_id = import_result['opportunity_id']

        score_response = self.client.post(
            f'/api/opportunities/{opportunity_id}/score/',
            {},
            format='json',
            **tenant_header,
        )
        self.assertEqual(score_response.status_code, 200, score_response.data)
        self.assertIn('overall_score', score_response.data)

        proposal_response = self.client.post(
            f'/api/opportunities/{opportunity_id}/create_proposal/',
            {},
            format='json',
            **tenant_header,
        )
        self.assertEqual(proposal_response.status_code, 201, proposal_response.data)
        proposal = Proposal.objects.get(id=proposal_response.data['proposal_id'])
        self.assertEqual(proposal.tenant, tenant)
        self.assertGreater(proposal.sections.count(), 0)

        section = proposal.sections.order_by('order').first()
        section_response = self.client.put(
            f'/api/proposals/{proposal.id}/sections/{section.id}/',
            {
                'title': section.title,
                'content': 'Updated beta QA narrative aligned with World Bank requirements.',
                'is_complete': True,
            },
            format='json',
            **tenant_header,
        )
        self.assertEqual(section_response.status_code, 200, section_response.data)

        quality_check = QualityCheck.objects.create(proposal=proposal)
        qc_response = self.client.post(
            f'/api/quality-checks/{quality_check.id}/run/',
            {
                'categories': [
                    {'category': 'compliance', 'score': 90, 'status': 'pass', 'items': [{'description': 'Requirements covered.', 'status': 'pass'}]},
                    {'category': 'coherence', 'score': 88, 'status': 'pass', 'items': [{'description': 'Narrative coherent.', 'status': 'pass'}]},
                    {'category': 'budget', 'score': 86, 'status': 'pass', 'items': [{'description': 'Budget assumptions acceptable.', 'status': 'pass'}]},
                    {'category': 'attachments', 'score': 90, 'status': 'pass', 'items': [{'description': 'Annex list ready.', 'status': 'pass'}]},
                ],
            },
            format='json',
            **tenant_header,
        )
        self.assertEqual(qc_response.status_code, 200, qc_response.data)
        quality_check.refresh_from_db()
        self.assertTrue(quality_check.can_submit)

        export_request = ProposalExportRequest.objects.create(
            proposal=proposal,
            export_type='executive_summary',
            status='queued',
            requested_by=self.admin,
        )
        executed_export = execute_export_request(export_request.id)
        self.assertEqual(executed_export.status, 'completed')
        self.assertTrue(executed_export.executive_summary)

        Notification.objects.create(
            tenant=tenant,
            user=self.admin,
            type='success',
            title='Beta QA smoke completed',
            message='End-to-end controlled beta smoke reached export request.',
        )
        notifications_response = self.client.get('/api/notifications/', **tenant_header)
        self.assertEqual(notifications_response.status_code, 200, notifications_response.data)
        self.assertIn('Beta QA smoke completed', [item['title'] for item in notifications_response.data['results']])
