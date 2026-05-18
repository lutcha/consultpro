from django.test import TestCase
from django.utils import timezone

from ..models import FirmProfile, Opportunity, OpportunityScore, Requirement, Risk, SavedFilter
from .factories import OpportunityFactory, RequirementFactory, RiskFactory, UserFactory


class OpportunityModelTests(TestCase):
    def test_str_representation(self):
        opportunity = OpportunityFactory(title='Test Opportunity')
        self.assertEqual(str(opportunity), 'Test Opportunity')

    def test_default_status(self):
        opportunity = OpportunityFactory()
        self.assertEqual(opportunity.status, 'new')

    def test_default_evaluation_criteria(self):
        opportunity = OpportunityFactory()
        self.assertEqual(opportunity.evaluation_criteria, 'qcbs')

    def test_ordering(self):
        older = OpportunityFactory()
        older.created_at = timezone.now() - timezone.timedelta(days=1)
        older.save()

        newer = OpportunityFactory()
        newer.created_at = timezone.now()
        newer.save()

        opportunities = list(Opportunity.objects.all())
        self.assertEqual(opportunities[0], newer)
        self.assertEqual(opportunities[1], older)

    def test_created_by_null(self):
        opportunity = OpportunityFactory(created_by=None)
        self.assertIsNone(opportunity.created_by)

    def test_assigned_to_many_to_many(self):
        user1 = UserFactory()
        user2 = UserFactory()
        opportunity = OpportunityFactory(assigned_to=[user1, user2])
        self.assertEqual(opportunity.assigned_to.count(), 2)


class RequirementModelTests(TestCase):
    def test_str_representation(self):
        requirement = RequirementFactory(description='A very long description that exceeds fifty characters easily')
        expected = f"{requirement.category} - A very long description that exceeds fifty charact"
        self.assertEqual(str(requirement), expected)

    def test_default_priority(self):
        requirement = RequirementFactory()
        self.assertEqual(requirement.priority, 'mandatory')

    def test_is_covered_default(self):
        requirement = RequirementFactory()
        self.assertFalse(requirement.is_covered)

    def test_related_opportunity(self):
        opportunity = OpportunityFactory()
        requirement = RequirementFactory(opportunity=opportunity)
        self.assertEqual(requirement.opportunity, opportunity)
        self.assertIn(requirement, opportunity.requirements.all())


class RiskModelTests(TestCase):
    def test_str_representation(self):
        risk = RiskFactory(description='A critical risk that we must address immediately')
        expected = f"{risk.severity} - A critical risk that we must address immediately"
        self.assertEqual(str(risk), expected)

    def test_related_opportunity(self):
        opportunity = OpportunityFactory()
        risk = RiskFactory(opportunity=opportunity)
        self.assertEqual(risk.opportunity, opportunity)
        self.assertIn(risk, opportunity.risks.all())

    def test_mitigation_blank(self):
        risk = RiskFactory(mitigation='')
        self.assertEqual(risk.mitigation, '')


class OpportunityScoreModelTests(TestCase):
    def test_str_representation(self):
        opportunity = OpportunityFactory()
        score = OpportunityScore.objects.create(
            opportunity=opportunity,
            overall_score=72,
            reasoning_trace=[{'component': 'risk', 'score': 72, 'reason': 'Test'}],
        )
        self.assertEqual(str(score), f'{opportunity.id} score 72')

    def test_related_opportunity(self):
        opportunity = OpportunityFactory()
        score = OpportunityScore.objects.create(opportunity=opportunity, overall_score=65)
        self.assertIn(score, opportunity.scores.all())
        self.assertTrue(score.is_current)


class FirmProfileModelTests(TestCase):
    def test_default_profile_is_singleton_by_flag(self):
        first = FirmProfile.objects.create(name='First', is_default=True)
        second = FirmProfile.objects.create(name='Second', is_default=True)

        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_str_representation(self):
        profile = FirmProfile.objects.create(name='West Africa')
        self.assertEqual(str(profile), 'West Africa')


class SavedFilterModelTests(TestCase):
    def test_str_representation(self):
        owner = UserFactory()
        saved_filter = SavedFilter.objects.create(
            owner=owner,
            name='Pipeline CV',
            view_type='opportunities',
            payload={'country': 'cv'},
        )

        self.assertEqual(str(saved_filter), 'Pipeline CV (opportunities)')
