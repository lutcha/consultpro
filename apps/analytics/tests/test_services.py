from django.test import TestCase
from django.utils import timezone

from apps.analytics.services import compute_procurement_trends
from apps.opportunities.models import OpportunityScore
from apps.opportunities.tests.factories import OpportunityFactory
from apps.proposals.models import ProposalStatusHistory
from apps.proposals.tests.factories import ProposalFactory


class AnalyticsServiceTests(TestCase):
    def test_compute_procurement_trends_returns_win_rates_and_weighted_pipeline(self):
        won = OpportunityFactory(sector='ict', country='cv', status='won', value=1000)
        OpportunityFactory(sector='ict', country='cv', status='lost', value=1000)
        active = OpportunityFactory(sector='health', country='sn', status='go', value=2000)
        OpportunityScore.objects.create(
            opportunity=active,
            overall_score=75,
            confidence_score=80,
            is_current=True,
        )

        data = compute_procurement_trends()

        self.assertEqual(data['win_rate_by_sector'][0]['sector'], 'ict')
        self.assertEqual(data['win_rate_by_sector'][0]['win_rate'], 50)
        self.assertEqual(data['win_rate_by_country'][0]['country'], 'cv')
        self.assertEqual(data['weighted_pipeline']['count'], 1)
        self.assertEqual(data['weighted_pipeline']['weighted_value'], 1500.0)
        self.assertEqual(data['opportunity_status_counts']['won'], 1)
        self.assertEqual(won.status, 'won')

    def test_compute_procurement_trends_returns_average_stage_duration(self):
        proposal = ProposalFactory(status='submitted')
        first = ProposalStatusHistory.objects.create(proposal=proposal, status='draft')
        second = ProposalStatusHistory.objects.create(proposal=proposal, status='submitted')
        ProposalStatusHistory.objects.filter(pk=first.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=3)
        )
        ProposalStatusHistory.objects.filter(pk=second.pk).update(
            created_at=timezone.now() - timezone.timedelta(days=1)
        )

        data = compute_procurement_trends()

        self.assertEqual(data['avg_stage_duration_days']['draft'], 2.0)

    def test_compute_procurement_trends_returns_proposal_outcomes(self):
        ProposalFactory(status='won')
        ProposalFactory(status='lost')
        ProposalFactory(status='submitted')

        data = compute_procurement_trends()

        self.assertEqual(data['proposal_outcomes']['won'], 1)
        self.assertEqual(data['proposal_outcomes']['lost'], 1)
        self.assertEqual(data['proposal_outcomes']['win_rate'], 50)
