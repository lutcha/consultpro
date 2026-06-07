from django.test import TestCase

from apps.scraping.models import ScrapingSource
from apps.scraping.tasks import _apply_tenant_intelligence_to_eligibility
from apps.tenants.services import apply_onboarding_to_tenant, create_tenant_with_owner
from apps.users.models import User


class TenantIntelligencePipelineTests(TestCase):
    def test_tenant_exclusion_keyword_blocks_scraped_opportunity_eligibility(self):
        owner = User.objects.create_user(
            username='source-owner',
            email='source-owner@example.com',
            password='StrongPass123!',
            role='manager',
        )
        tenant = create_tenant_with_owner('Reliable Source Tenant', owner)
        apply_onboarding_to_tenant(
            tenant,
            {
                'opportunity_keywords': ['technical assistance'],
                'excluded_keywords': ['vehicles only'],
            },
            submitted_by=owner,
        )
        source = ScrapingSource.objects.create(
            tenant=tenant,
            name='World Bank',
            organization='World Bank Group',
            url='https://search.worldbank.org/api/v2/procnotices',
        )

        result = _apply_tenant_intelligence_to_eligibility(
            source,
            {
                'title': 'Vehicles only procurement',
                'description': 'Technical assistance is not requested; vehicles only.',
                'organization': 'World Bank',
            },
            {
                'is_eligible': True,
                'confidence': 0.6,
                'reasons': ['regional_match'],
                'negative_reasons': [],
                'metadata': {},
            },
        )

        self.assertFalse(result['is_eligible'])
        self.assertIn('tenant_exclusion_keyword', result['negative_reasons'])
        self.assertEqual(result['metadata']['tenant_exclusion_matches'], ['vehicles only'])
