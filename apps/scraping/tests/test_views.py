from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.opportunities.models import Opportunity, Requirement
from apps.opportunities.tests.factories import UserFactory
from apps.scraping.models import ScrapedOpportunity, ScrapingSource


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
