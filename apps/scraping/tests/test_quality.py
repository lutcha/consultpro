from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.scraping.services.quality import assess_scraped_item, normalize_title
from apps.scraping.tasks import _process_single_item


class ScrapedItemQualityServiceTests(SimpleTestCase):
    def test_normalize_title_removes_html_and_extra_spaces(self):
        title = normalize_title('  <b>Procurement&nbsp;of IT equipment</b>  ')

        self.assertEqual(title, 'Procurement of IT equipment')

    def test_rejects_navigation_titles(self):
        assessment = assess_scraped_item({'title': 'Read more'}, 'Source')

        self.assertFalse(assessment.valid)
        self.assertEqual(assessment.rejection_reason, 'navigation_title')

    def test_generates_stable_external_id_when_missing(self):
        first = assess_scraped_item(
            {'title': 'Consultancy for renewable energy policy', 'external_url': 'https://example.org/a'},
            'Source',
        )
        second = assess_scraped_item(
            {'title': 'Consultancy for renewable energy policy', 'external_url': 'https://example.org/a'},
            'Source',
        )

        self.assertTrue(first.valid)
        self.assertEqual(first.external_id, second.external_id)
        self.assertIn('external_id_generated', first.warnings)


class ScrapedItemQualityPipelineTests(TestCase):
    def setUp(self):
        self.source = ScrapingSource.objects.create(
            name='Quality Source',
            organization='Quality Org',
            url='https://example.org/tenders',
            scraper_config={'deep_extraction_enabled': False},
        )
        self.stats = {
            'validated': 0,
            'eligible_cv': 0,
            'duplicates_skipped': 0,
            'ingested': 0,
            'rejected': 0,
            'deep_extracted': 0,
            'deep_extraction_failed': 0,
            'errors': [],
        }

    def test_navigation_title_is_rejected_before_ingestion(self):
        outcome = _process_single_item(
            {
                'title': 'Read more',
                'description': 'Navigation link captured by a generic scraper',
                'external_url': 'https://example.org/read-more',
            },
            self.source,
            'batch-quality',
            self.stats,
        )

        self.assertEqual(outcome, 'rejected')
        rejected = ScrapedOpportunity.objects.get()
        self.assertEqual(rejected.status, 'rejected')
        self.assertEqual(rejected.transformation_flags['rejection_reason'], 'navigation_title')
        self.assertEqual(self.stats['ingested'], 0)

    def test_valid_item_uses_normalized_title_and_quality_flags(self):
        deadline = (timezone.now() + timezone.timedelta(days=30)).date().isoformat()

        outcome = _process_single_item(
            {
                'title': '  Consultancy   for Cabo Verde digital procurement  ',
                'description': 'Terms of reference for a public procurement advisory assignment in Cabo Verde.',
                'external_url': 'https://example.org/tenders/consultancy-cv',
                'deadline': deadline,
                'country': 'Cabo Verde',
                'sector': 'Governance',
            },
            self.source,
            'batch-quality',
            self.stats,
        )

        self.assertIsNone(outcome)
        scraped = ScrapedOpportunity.objects.get(status='new')
        self.assertEqual(scraped.title, 'Consultancy for Cabo Verde digital procurement')
        self.assertTrue(scraped.external_id.startswith('generated-'))
        self.assertTrue(scraped.transformation_flags['title_quality_valid'])
        self.assertIn('external_id_generated', scraped.transformation_flags['quality_warnings'])
        self.assertGreaterEqual(float(scraped.data_quality_score), 0.7)
