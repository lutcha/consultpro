from django.test import TestCase
from django.utils import timezone

from apps.analytics.models import MarketSignal, PredictiveMetric
from apps.analytics.services import compute_descriptive_metrics, compute_procurement_trends
from apps.opportunities.models import OpportunityScore
from apps.opportunities.tests.factories import OpportunityFactory
from apps.proposals.models import ProposalStatusHistory
from apps.proposals.tests.factories import ProposalFactory
from apps.scraping.models import ScrapedOpportunity, ScrapingSource


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

    def test_compute_descriptive_metrics_returns_layer_one_metrics(self):
        now = timezone.now()
        older = OpportunityFactory(sector='wash', country='mz', client='Donor A', value=1000)
        recent = OpportunityFactory(sector='wash', country='mz', client='Donor A', value=3000)
        OpportunityFactory(sector='wash', country='mz', client='Donor B', value=1000)
        older.created_at = now - timezone.timedelta(days=120)
        older.save(update_fields=['created_at'])
        recent.created_at = now - timezone.timedelta(days=5)
        recent.save(update_fields=['created_at'])
        source = ScrapingSource.objects.create(
            name='MZ Portal',
            organization='Gov',
            url='https://example.com',
        )
        scraped = ScrapedOpportunity.objects.create(
            source=source,
            external_id='mz-1',
            external_url='https://example.com/t/1',
            title='Water tender',
            organization='Gov',
            sector='wash',
            country='mz',
            deadline=now + timezone.timedelta(days=45),
        )
        ScrapedOpportunity.objects.filter(pk=scraped.pk).update(
            scraped_at=now - timezone.timedelta(days=3)
        )

        data = compute_descriptive_metrics(country='mz', sector='wash')

        self.assertGreater(data['demand_velocity'], 0)
        self.assertEqual(data['recent_30d_tenders'], 3)
        self.assertEqual(data['budget_concentration_index'], 1.0)
        self.assertIn('competitive_density', data)
        self.assertEqual(len(data['monthly_distribution']), 12)

    def test_procurement_trends_returns_cached_heuristic_forecast(self):
        now = timezone.now()
        for index in range(6):
            opportunity = OpportunityFactory(sector='health', country='cv', status='go')
            opportunity.created_at = now - timezone.timedelta(days=30 * index)
            opportunity.save(update_fields=['created_at'])

        first = compute_procurement_trends(
            country='cv',
            sector='health',
            horizon=3,
            include_forecast=True,
        )
        second = compute_procurement_trends(
            country='cv',
            sector='health',
            horizon=3,
            include_forecast=True,
        )

        self.assertIn('descriptive', first)
        self.assertIn('demand_forecast', first['predictive'])
        self.assertEqual(first['predictive']['cache_status'], 'refresh')
        self.assertEqual(second['predictive']['cache_status'], 'hit')
        self.assertEqual(PredictiveMetric.objects.count(), 1)

    def test_procurement_trends_persists_market_signals(self):
        now = timezone.now()
        old = OpportunityFactory(sector='ict', country='cv', status='go')
        old.created_at = now - timezone.timedelta(days=150)
        old.save(update_fields=['created_at'])
        for _ in range(5):
            recent = OpportunityFactory(sector='ict', country='cv', status='go')
            recent.created_at = now - timezone.timedelta(days=2)
            recent.save(update_fields=['created_at'])

        data = compute_procurement_trends(country='cv', sector='ict', include_forecast=True)

        self.assertTrue(MarketSignal.objects.filter(signal_type='demand_spike').exists())
        self.assertTrue(any(signal['type'] == 'demand_spike' for signal in data['signals']))
