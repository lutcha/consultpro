from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.scraping.tasks import enrich_scraped_opportunity_with_ai


class ScrapingAIEnrichmentTaskTests(TestCase):
    def setUp(self):
        self.source = ScrapingSource.objects.create(
            name='Task Source',
            organization='Task Org',
            url='https://example.org/tenders',
        )

    @override_settings(AI_PROVIDER='mock', AI_ALWAYS_MOCK=False)
    def test_enrichment_records_provider_governance_metadata(self):
        scraped = ScrapedOpportunity.objects.create(
            source=self.source,
            external_id='ai-meta-001',
            external_url='https://example.org/tenders/ai-meta-001',
            title='Consultoria para governanca digital',
            organization='Task Org',
            client='Task Client',
            sector='ICT',
            country='Cabo Verde',
            description='Descricao suficientemente longa para ativar enriquecimento por IA.',
            deep_content_text='Conteudo adicional do termo de referencia com requisitos tecnicos e prazos.',
            deadline=timezone.now() + timezone.timedelta(days=30),
        )

        result = enrich_scraped_opportunity_with_ai(scraped.id)

        scraped.refresh_from_db()
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['provider'], 'mock')
        self.assertEqual(scraped.transformation_flags['ai_provider'], 'mock')
        self.assertEqual(scraped.transformation_flags['ai_model'], 'n/a')
        self.assertTrue(scraped.transformation_flags['ai_is_mock'])
        self.assertEqual(len(scraped.transformation_flags['ai_prompt_hash']), 64)
        self.assertGreater(scraped.transformation_flags['ai_estimated_prompt_tokens'], 0)
        self.assertTrue(scraped.ai_summary)

    def test_enrichment_skips_short_text_without_provider_call(self):
        scraped = ScrapedOpportunity.objects.create(
            source=self.source,
            external_id='short-001',
            external_url='https://example.org/tenders/short-001',
            title='Short',
            organization='Task Org',
            description='Tiny',
        )

        with patch('apps.ai_services.services.AIServiceFactory.get_service') as mock_get_service:
            result = enrich_scraped_opportunity_with_ai(scraped.id)

        scraped.refresh_from_db()
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'text_too_short')
        self.assertEqual(scraped.transformation_flags['ai_enrichment_reason'], 'text_too_short')
        mock_get_service.assert_not_called()
