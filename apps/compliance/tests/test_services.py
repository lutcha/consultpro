from django.test import TestCase

from apps.compliance.models import ComplianceMatrix, ComplianceMatrixRow
from apps.compliance.services import generate_compliance_matrix
from apps.opportunities.tests.factories import OpportunityFactory, RequirementFactory, UserFactory


class ComplianceMatrixServiceTests(TestCase):
    def test_generate_compliance_matrix_from_requirements_and_ai_extraction(self):
        opportunity = OpportunityFactory(
            ai_extraction={
                'cos_analysis': {
                    'submission_requirements': ['Signed declaration', 'Tax certificate'],
                    'team_requirements': ['Team leader with 10 years experience'],
                }
            }
        )
        RequirementFactory(
            opportunity=opportunity,
            category='technical',
            priority='mandatory',
            description='Methodology must include monitoring plan',
        )

        matrix = generate_compliance_matrix(opportunity.id)

        self.assertEqual(matrix.opportunity, opportunity)
        self.assertEqual(matrix.status, 'generated')
        self.assertEqual(matrix.rows.count(), 4)
        self.assertEqual(matrix.ai_metadata['provider'], 'deterministic')
        self.assertTrue(matrix.source_trace)
        self.assertTrue(
            matrix.rows.filter(requirement_text__icontains='monitoring plan').exists()
        )
        self.assertTrue(
            matrix.rows.filter(source_type='ai_extraction', source_reference__icontains='submission').exists()
        )

    def test_generate_compliance_matrix_is_idempotent_and_preserves_row_status(self):
        opportunity = OpportunityFactory()
        RequirementFactory(opportunity=opportunity, description='Submit workplan')
        matrix = generate_compliance_matrix(opportunity.id)
        row = matrix.rows.first()
        row.status = 'covered'
        row.human_override = True
        row.human_override_note = 'Covered in proposal section.'
        row.save(update_fields=['status', 'human_override', 'human_override_note'])

        refreshed = generate_compliance_matrix(opportunity.id)

        self.assertEqual(ComplianceMatrix.objects.count(), 1)
        self.assertEqual(ComplianceMatrixRow.objects.count(), 1)
        row.refresh_from_db()
        self.assertEqual(refreshed.id, matrix.id)
        self.assertEqual(row.status, 'covered')
        self.assertTrue(row.human_override)
        self.assertEqual(refreshed.human_override_count, 1)

    def test_generate_compliance_matrix_records_user(self):
        user = UserFactory()
        opportunity = OpportunityFactory()

        matrix = generate_compliance_matrix(opportunity.id, generated_by=user)

        self.assertEqual(matrix.generated_by, user)
