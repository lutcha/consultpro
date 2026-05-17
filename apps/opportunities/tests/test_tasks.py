from django.test import TestCase

from apps.opportunities.models import OpportunityScore
from apps.opportunities.tasks import enrich_and_score_opportunity

from .factories import OpportunityFactory


class OpportunityScoringTaskTests(TestCase):
    def test_enrich_and_score_opportunity_creates_current_score(self):
        opportunity = OpportunityFactory()

        result = enrich_and_score_opportunity(opportunity.id)

        score = OpportunityScore.objects.get(opportunity=opportunity, is_current=True)
        self.assertEqual(result['detail'], 'Scoring concluido.')
        self.assertEqual(result['opportunity_id'], opportunity.id)
        self.assertEqual(result['score_id'], score.id)
        self.assertEqual(result['overall_score'], score.overall_score)

    def test_enrich_and_score_opportunity_handles_missing_opportunity(self):
        result = enrich_and_score_opportunity(999999)

        self.assertEqual(result['detail'], 'Oportunidade nao encontrada.')
        self.assertEqual(result['opportunity_id'], 999999)
