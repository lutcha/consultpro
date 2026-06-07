from django.test import SimpleTestCase, TestCase

from apps.opportunities.scoring import build_opportunity_score_payload
from apps.opportunities.tests.factories import OpportunityFactory
from apps.scraping.requested_procurement_sources import REQUESTED_PROCUREMENT_SOURCES
from apps.scraping.services.cos_scope import classify_cos_scope_text, enrich_source_definition
from apps.scraping.services.cv_eligibility import CaboVerdeEligibilityValidator
from apps.scraping.services.enrichment import detect_sector, enrich_for_import


class COSScopeClassificationTests(SimpleTestCase):
    def test_classifies_strategic_consulting_opportunity(self):
        result = classify_cos_scope_text(
            'Technical assistance for GovTech digital transformation and '
            'capacity building in Cabo Verde and ECOWAS.'
        )

        self.assertTrue(result['is_consulting_relevant'])
        self.assertTrue(result['is_geographic_priority'])
        self.assertIn(result['relevance'], ['high', 'strategic'])

    def test_source_enrichment_is_additive(self):
        source = {
            'name': 'Example',
            'filters': {'countries': ['Existing'], 'keywords': ['custom']},
            'scraper_config': {'access': 'subscription'},
        }

        enriched = enrich_source_definition(source)

        self.assertIn('Existing', enriched['filters']['countries'])
        self.assertIn('custom', enriched['filters']['keywords'])
        self.assertIn('technical assistance', enriched['filters']['keywords'])
        self.assertEqual(enriched['scraper_config']['intelligence_mode'], 'partial_intelligence')

    def test_requested_subscription_sources_get_partial_intelligence_mode(self):
        sources = {src['name']: src for src in REQUESTED_PROCUREMENT_SOURCES}

        self.assertEqual(
            sources['TendersOnTime - Lead Discovery']['scraper_config']['intelligence_mode'],
            'partial_intelligence',
        )
        self.assertTrue(sources['GlobalTenders - Guinea-Bissau']['filters']['partial_intelligence'])


class COSScopePipelineTests(TestCase):
    def test_eligibility_accepts_regional_consulting_scope(self):
        result = CaboVerdeEligibilityValidator.evaluate({
            'title': 'Technical assistance for ECOWAS digital public infrastructure',
            'description': 'Capacity building, governance support, and implementation support in West Africa.',
            'language': 'en',
        })

        self.assertTrue(result['is_eligible'])
        self.assertIn('cos_consulting_scope_match', result['reasons'])
        self.assertIn('cos_scope', result['metadata'])

    def test_enrichment_detects_new_scope_sector_and_cos_metadata(self):
        self.assertEqual(
            detect_sector('AI governance and data analytics technical assistance'),
            'data_science',
        )

        opp = type('Opp', (), {
            'id': 1,
            'title': 'Framework contract for startup ecosystem acceleration in Cabo Verde',
            'description': 'Consulting assignment with capacity building and innovation ecosystem support.',
            'deep_content_text': '',
            'organization': 'Donor',
            'sector': '',
            'country': 'Cabo Verde',
            'region': '',
            'geographic_scope': {},
        })()
        result = enrich_for_import(opp)

        self.assertIn(result['sector'], ['private_sector', 'capacity_building'])
        self.assertEqual(result['country'], 'cv')
        self.assertIn('cos_scope', result)
        self.assertTrue(result['cos_scope']['is_consulting_relevant'])

    def test_scoring_includes_cos_scope(self):
        opportunity = OpportunityFactory(
            title='Technical assistance for GovTech reform in Cabo Verde',
            description='Digital transformation, capacity building, and public sector modernization.',
            country='cv',
            sector='digital_transformation',
        )

        payload = build_opportunity_score_payload(opportunity)

        self.assertIn('cos_scope', payload['ai_extracted_criteria'])
        self.assertGreaterEqual(payload['strategic_fit'], 70)
