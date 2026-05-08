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
