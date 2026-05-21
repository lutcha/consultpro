from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.opportunities.tests.factories import UserFactory
from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.scraping.services.readiness import (
    MIN_IMPORT_QUALITY_SCORE,
    filter_ready_to_import,
    get_import_readiness,
)


class ImportReadinessServiceTests(TestCase):
    """Unit tests for the single source of truth: get_import_readiness()."""

    def setUp(self):
        self.source = ScrapingSource.objects.create(
            name='Test Source',
            organization='Test Org',
            url='https://example.org/tenders',
        )

    def _create(self, **overrides):
        defaults = {
            'source': self.source,
            'external_id': 'test-001',
            'external_url': 'https://example.org/tenders/test-001',
            'title': 'Test Opportunity',
            'organization': 'Test Org',
            'client': 'Test Client',
            'description': 'A test description.',
            'value': 1000,
            'currency': 'USD',
            'status': 'new',
            'cv_eligible': True,
            'data_quality_score': Decimal('0.90'),
            'deadline': timezone.now() + timezone.timedelta(days=20),
        }
        defaults.update(overrides)
        return ScrapedOpportunity.objects.create(**defaults)

    def test_ready_when_all_criteria_met(self):
        opp = self._create()
        result = get_import_readiness(opp)
        self.assertTrue(result['ready'])
        self.assertEqual(result['reasons'], [])
        self.assertEqual(result['blockers'], [])
        self.assertEqual(result['quality_score'], '0.90')
        self.assertEqual(result['threshold'], str(MIN_IMPORT_QUALITY_SCORE))
        self.assertEqual(result['minimum_quality_score'], str(MIN_IMPORT_QUALITY_SCORE))

    def test_blocks_when_status_not_new(self):
        for idx, bad_status in enumerate(('imported', 'ignored', 'expired', 'rejected')):
            opp = self._create(status=bad_status, external_id=f'status-{idx}')
            result = get_import_readiness(opp)
            self.assertFalse(result['ready'])
            self.assertIn('status_not_new', result['reasons'])
            self.assertIn('status_not_new', result['blockers'])

    def test_blocks_when_not_cv_eligible(self):
        opp = self._create(cv_eligible=False)
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertIn('not_cv_eligible', result['reasons'])
        self.assertIn('not_cv_eligible', result['blockers'])

    def test_blocks_when_already_imported(self):
        from apps.opportunities.models import Opportunity
        opportunity = Opportunity.objects.create(
            title='Imported Opp',
            client='Client',
            description='Desc',
            value=1000,
            deadline=timezone.now() + timezone.timedelta(days=20),
        )
        opp = self._create()
        opp.imported_opportunity = opportunity
        opp.save(update_fields=['imported_opportunity'])
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertIn('already_imported', result['reasons'])
        self.assertIn('already_imported', result['blockers'])

    def test_blocks_when_deadline_expired(self):
        opp = self._create(deadline=timezone.now() - timezone.timedelta(days=1))
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertIn('deadline_expired', result['reasons'])
        self.assertIn('deadline_expired', result['blockers'])

    def test_allows_null_deadline(self):
        opp = self._create(deadline=None)
        result = get_import_readiness(opp)
        self.assertTrue(result['ready'])

    def test_blocks_when_quality_below_threshold(self):
        opp = self._create(data_quality_score=Decimal('0.20'))
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertIn('low_data_quality', result['reasons'])
        self.assertIn('low_data_quality', result['blockers'])
        self.assertEqual(result['quality_score'], '0.20')

    def test_multiple_blockers_accumulate(self):
        opp = self._create(
            status='ignored',
            cv_eligible=False,
            data_quality_score=Decimal('0.10'),
            deadline=timezone.now() - timezone.timedelta(days=5),
        )
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertEqual(
            set(result['reasons']),
            {'status_not_new', 'not_cv_eligible', 'deadline_expired', 'low_data_quality'},
        )
        self.assertEqual(result['reasons'], result['blockers'])


class FilterReadyToImportTests(TestCase):
    """ORM-level filter must mirror every gate in get_import_readiness()."""

    def setUp(self):
        self.source = ScrapingSource.objects.create(
            name='Filter Source',
            organization='Filter Org',
            url='https://example.org/tenders',
        )

    def _create(self, **overrides):
        defaults = {
            'source': self.source,
            'external_id': 'f-001',
            'external_url': 'https://example.org/tenders/f-001',
            'title': 'Filter Opp',
            'organization': 'Org',
            'client': 'Client',
            'description': 'Desc',
            'value': 1000,
            'currency': 'USD',
            'status': 'new',
            'cv_eligible': True,
            'data_quality_score': Decimal('0.90'),
            'deadline': timezone.now() + timezone.timedelta(days=20),
        }
        defaults.update(overrides)
        return ScrapedOpportunity.objects.create(**defaults)

    def test_filter_returns_only_ready_records(self):
        ready = self._create(external_id='ready')
        self._create(external_id='lowq', data_quality_score=Decimal('0.20'))
        self._create(external_id='notcv', cv_eligible=False)
        self._create(external_id='expired', deadline=timezone.now() - timezone.timedelta(days=1))
        self._create(external_id='imported', status='imported')

        qs = filter_ready_to_import(ScrapedOpportunity.objects.all())
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().id, ready.id)

    def test_filter_allows_null_deadline(self):
        ready = self._create(external_id='null-dl', deadline=None)
        qs = filter_ready_to_import(ScrapedOpportunity.objects.all())
        self.assertIn(ready, qs)

    def test_filter_excludes_already_imported(self):
        from apps.opportunities.models import Opportunity
        opportunity = Opportunity.objects.create(
            title='Opp', client='C', description='D', value=1000,
            deadline=timezone.now() + timezone.timedelta(days=20),
        )
        self._create(external_id='imported-opp', imported_opportunity=opportunity)
        qs = filter_ready_to_import(ScrapedOpportunity.objects.all())
        self.assertEqual(qs.count(), 0)


class ImportReadinessStatsTests(TestCase):
    """Stats endpoint must use the same filter as the rest of the system."""

    def setUp(self):
        from rest_framework.test import APIClient
        self.user = UserFactory(role='manager')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.source = ScrapingSource.objects.create(
            name='Stats Source',
            organization='Stats Org',
            url='https://example.org/tenders',
        )

    def _create(self, **overrides):
        defaults = {
            'source': self.source,
            'external_id': 's-001',
            'external_url': 'https://example.org/tenders/s-001',
            'title': 'Stats Opp',
            'organization': 'Org',
            'client': 'Client',
            'description': 'Desc',
            'value': 1000,
            'currency': 'USD',
            'status': 'new',
            'cv_eligible': True,
            'data_quality_score': Decimal('0.90'),
            'deadline': timezone.now() + timezone.timedelta(days=20),
        }
        defaults.update(overrides)
        return ScrapedOpportunity.objects.create(**defaults)

    def test_stats_ready_to_import_matches_filter(self):
        from django.urls import reverse

        ready1 = self._create(external_id='r1')
        ready2 = self._create(external_id='r2')
        self._create(external_id='lowq', data_quality_score=Decimal('0.20'))
        self._create(external_id='expired', deadline=timezone.now() - timezone.timedelta(days=1))

        response = self.client.get(reverse('scraping:scraping-source-stats'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['ready_to_import'], 2)

        # Ensure the count matches the ORM filter directly
        self.assertEqual(
            response.data['ready_to_import'],
            filter_ready_to_import(ScrapedOpportunity.objects.all()).count(),
        )
