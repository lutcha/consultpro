from django.test import TestCase
from django.utils import timezone

from ..models import Opportunity, Requirement, Risk
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
        expected = f"{requirement.category} - A very long description that exceeds fifty char"
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
