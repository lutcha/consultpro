from django.test import TestCase

from apps.opportunities.tests.factories import OpportunityFactory, UserFactory
from apps.partners.matching import suggest_consultants, suggest_partners
from apps.partners.tests.factories import PartnerProfileFactory


class PartnerMatchingTests(TestCase):
    def test_suggest_partners_prioritizes_sector_and_geography(self):
        opportunity = OpportunityFactory(sector='ict', country='cv', region='west_africa')
        strong = PartnerProfileFactory(
            name='Strong Partner',
            sectors=['ict'],
            geographies=['cv'],
            capabilities=['digital transformation'],
            trust_score=70,
        )
        PartnerProfileFactory(name='Weak Partner', sectors=['health'], geographies=['sn'], trust_score=80)

        results = suggest_partners(opportunity)

        self.assertEqual(results[0].id, strong.id)
        self.assertGreaterEqual(results[0].score, 90)
        self.assertTrue(any('Sector match' in item for item in results[0].reasoning_trace))
        self.assertTrue(any('Country match' in item for item in results[0].reasoning_trace))

    def test_suggest_partners_excludes_inactive_partners(self):
        opportunity = OpportunityFactory(sector='ict', country='cv')
        PartnerProfileFactory(sectors=['ict'], geographies=['cv'], is_active=False)

        self.assertEqual(suggest_partners(opportunity), [])


class ConsultantMatchingTests(TestCase):
    def test_suggest_consultants_uses_skills_availability_and_experience(self):
        opportunity = OpportunityFactory(sector='ict', country='cv')
        strong = UserFactory(
            first_name='Ana',
            last_name='Silva',
            role='consultant',
            availability='available',
            skills=['ict', 'procurement'],
            languages=['pt', 'en'],
            location='cv',
            years_experience=8,
        )
        UserFactory(role='consultant', availability='unavailable', skills=['health'])

        results = suggest_consultants(opportunity)

        self.assertEqual(results[0].id, strong.id)
        self.assertGreaterEqual(results[0].score, 80)
        self.assertTrue(any('Availability match' in item for item in results[0].reasoning_trace))
        self.assertTrue(any('Skill match' in item for item in results[0].reasoning_trace))
