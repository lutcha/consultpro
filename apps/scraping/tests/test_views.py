from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from apps.opportunities.models import Opportunity, Requirement
from apps.opportunities.scoring import score_opportunity
from apps.opportunities.tests.factories import UserFactory
from apps.scraping.models import ScrapedOpportunity, ScrapingJob, ScrapingSource


class ScrapedOpportunityImportTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)
        self.source = ScrapingSource.objects.create(
            name='QA Source',
            organization='QA Org',
            url='https://example.org/tenders',
        )

    def _create_scraped_opportunity(self, **overrides):
        data = {
            'source': self.source,
            'external_id': 'qa-001',
            'external_url': 'https://example.org/tenders/qa-001',
            'title': 'Consultoria de Dados',
            'organization': 'ECREEE',
            'client': 'ECREEE',
            'sector': 'Tecnologia',
            'country': 'Cabo Verde',
            'description': 'Resumo curto da oportunidade.',
            'deep_content_text': 'Conteudo completo do TdR com requisitos.',
            'deep_content_status': 'completed',
            'value': 2500,
            'currency': 'USD',
            'deadline': timezone.now() + timezone.timedelta(days=20),
            'ai_summary': 'Resumo IA da oportunidade.',
            'ai_extracted_requirements': [
                {'description': 'Experiencia minima em gestao de dados', 'category': 'technical', 'priority': 'mandatory'},
                {'description': 'Disponibilidade para trabalho de campo', 'category': 'functional', 'priority': 'preferred'},
            ],
        }
        data.update(overrides)
        return ScrapedOpportunity.objects.create(**data)

    def test_import_scraped_opportunity_creates_internal_opportunity_with_ai_context(self):
        scraped = self._create_scraped_opportunity()
        url = reverse('scraping:scraped-opportunity-import-opportunity', kwargs={'pk': scraped.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['created'])

        scraped.refresh_from_db()
        opportunity = Opportunity.objects.get(pk=response.data['opportunity_id'])
        self.assertEqual(scraped.status, 'imported')
        self.assertEqual(scraped.imported_opportunity, opportunity)
        self.assertEqual(opportunity.title, scraped.title)
        self.assertEqual(opportunity.client, scraped.client)
        self.assertEqual(opportunity.url_source, scraped.external_url)
        self.assertIn('Conteudo completo do TdR', opportunity.description)
        self.assertEqual(opportunity.ai_summary, scraped.ai_summary)
        self.assertEqual(opportunity.ai_extraction['scraped_opportunity_id'], scraped.id)
        self.assertEqual(opportunity.ai_extraction['deep_content_status'], 'completed')
        self.assertEqual(Requirement.objects.filter(opportunity=opportunity, extracted_by_ai=True).count(), 2)
        self.assertTrue(response.data['score_queued'])

    def test_import_scraped_opportunity_queues_post_import_scoring(self):
        scraped = self._create_scraped_opportunity(external_id='score-001', external_url='https://example.org/tenders/score-001')
        url = reverse('scraping:scraped-opportunity-import-opportunity', kwargs={'pk': scraped.pk})

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity.delay') as mock_delay:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(callbacks), 1)
        mock_delay.assert_called_once_with(response.data['opportunity_id'])

    def test_import_scraped_opportunity_is_idempotent(self):
        scraped = self._create_scraped_opportunity()
        url = reverse('scraping:scraped-opportunity-import-opportunity', kwargs={'pk': scraped.pk})

        first = self.client.post(url)
        second = self.client.post(url)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(second.data['created'])
        self.assertEqual(first.data['opportunity_id'], second.data['opportunity_id'])
        self.assertEqual(Opportunity.objects.filter(url_source=scraped.external_url).count(), 1)

        opportunity = Opportunity.objects.get(pk=first.data['opportunity_id'])
        score_opportunity(opportunity)
        third = self.client.post(url)
        self.assertFalse(third.data['score_queued'])

    def test_ready_to_import_filter_uses_eligibility_deadline_and_quality(self):
        ready = self._create_scraped_opportunity(
            external_id='ready-001',
            external_url='https://example.org/tenders/ready-001',
            cv_eligible=True,
            data_quality_score='0.90',
        )
        self._create_scraped_opportunity(
            external_id='low-quality',
            external_url='https://example.org/tenders/low-quality',
            cv_eligible=True,
            data_quality_score='0.20',
        )
        self._create_scraped_opportunity(
            external_id='not-eligible',
            external_url='https://example.org/tenders/not-eligible',
            cv_eligible=False,
            data_quality_score='0.90',
        )
        self._create_scraped_opportunity(
            external_id='expired',
            external_url='https://example.org/tenders/expired',
            cv_eligible=True,
            data_quality_score='0.90',
            deadline=timezone.now() - timezone.timedelta(days=1),
        )

        url = reverse('scraping:scraped-opportunity-list')
        response = self.client.get(url, {'ready_to_import': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data['results']}
        self.assertEqual(ids, {ready.id})
        self.assertTrue(response.data['results'][0]['ready_to_import'])

    def test_import_ready_imports_only_ready_records(self):
        ready = self._create_scraped_opportunity(
            external_id='ready-import',
            external_url='https://example.org/tenders/ready-import',
            cv_eligible=True,
            data_quality_score='0.90',
        )
        low_quality = self._create_scraped_opportunity(
            external_id='low-quality-import',
            external_url='https://example.org/tenders/low-quality-import',
            cv_eligible=True,
            data_quality_score='0.20',
        )

        url = reverse('scraping:scraped-opportunity-import-ready')
        response = self.client.post(url, {'limit': 10}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(response.data['skipped_count'], 1)
        self.assertEqual(response.data['failed_count'], 0)
        self.assertEqual(response.data['processed_count'], 2)
        self.assertEqual(response.data['imported'][0]['id'], ready.id)
        self.assertEqual(response.data['skipped'][0]['id'], low_quality.id)
        self.assertIn('low_data_quality', response.data['skipped'][0]['reasons'])
        ready.refresh_from_db()
        low_quality.refresh_from_db()
        self.assertEqual(ready.status, 'imported')
        self.assertEqual(low_quality.status, 'new')

    def test_list_serializer_explains_import_readiness_reasons(self):
        scraped = self._create_scraped_opportunity(
            external_id='reason-001',
            external_url='https://example.org/tenders/reason-001',
            cv_eligible=False,
            data_quality_score='0.20',
        )

        url = reverse('scraping:scraped-opportunity-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next(row for row in response.data['results'] if row['id'] == scraped.id)
        self.assertFalse(item['ready_to_import'])
        self.assertIn('not_cv_eligible', item['import_readiness_reasons'])
        self.assertIn('low_data_quality', item['import_readiness_reasons'])


class ScrapingSourceHealthTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)

    def _create_source(self, **overrides):
        data = {
            'name': 'Health Source',
            'organization': 'Health Org',
            'url': 'https://example.org/health',
            'status': 'active',
            'success_rate': 80,
        }
        data.update(overrides)
        return ScrapingSource.objects.create(**data)

    def test_health_endpoint_marks_productive_source_as_healthy(self):
        source = self._create_source()
        ScrapingJob.objects.create(
            source=source,
            status='completed',
            items_found=3,
            items_new=2,
            completed_at=timezone.now(),
        )
        ScrapedOpportunity.objects.create(
            source=source,
            external_id='health-001',
            external_url='https://example.org/health/001',
            title='Consultancy opportunity',
            organization='Health Org',
            status='new',
        )

        response = self.client.get(reverse('scraping:scraping-source-health'), {'search': 'Health Source'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data['results'][0]
        self.assertEqual(item['health_status'], 'healthy')
        self.assertTrue(item['production_ready'])
        self.assertEqual(item['total_opportunities'], 1)
        self.assertGreaterEqual(item['health_score'], 75)

    def test_health_endpoint_explains_empty_and_failing_sources(self):
        empty = self._create_source(name='Empty Source', url='https://example.org/empty')
        failing = self._create_source(
            name='Failing Source',
            url='https://example.org/failing',
            error_message='SSL failure',
        )
        ScrapingJob.objects.create(source=empty, status='completed', items_found=0)
        ScrapingJob.objects.create(source=failing, status='failed', error_log='timeout')

        response = self.client.get(reverse('scraping:scraping-source-health'), {'search': 'Source'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_name = {item['name']: item for item in response.data['results']}
        self.assertEqual(by_name['Empty Source']['health_status'], 'empty')
        self.assertEqual(by_name['Failing Source']['health_status'], 'failing')
        self.assertIn('timeout', by_name['Failing Source']['health_reason'])

    def test_health_endpoint_marks_subscription_sources_as_blocked(self):
        self._create_source(
            name='Subscription Source',
            url='https://example.org/subscription',
            scraper_config={'access': 'subscription'},
            filters={'access': ['subscription']},
        )

        response = self.client.get(reverse('scraping:scraping-source-health'), {'search': 'Subscription Source'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data['results'][0]
        self.assertEqual(item['health_status'], 'blocked')
        self.assertFalse(item['production_ready'])
        self.assertEqual(item['access'], 'subscription')

    def test_health_endpoint_filters_by_health_status(self):
        self._create_source(name='Paused Source', url='https://example.org/paused', status='paused')
        self._create_source(name='Active Source', url='https://example.org/active')

        response = self.client.get(
            reverse('scraping:scraping-source-health'),
            {'health_status': 'paused', 'search': 'Paused Source'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Paused Source')
