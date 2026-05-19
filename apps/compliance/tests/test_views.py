from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.compliance.models import ComplianceMatrix
from apps.opportunities.tests.factories import OpportunityFactory, RequirementFactory, UserFactory
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory


class ComplianceMatrixViewTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)

    def test_generate_endpoint_returns_matrix_with_rows(self):
        opportunity = OpportunityFactory()
        RequirementFactory(
            opportunity=opportunity,
            category='functional',
            priority='mandatory',
            description='Provide implementation schedule',
        )
        url = reverse('compliance-matrix-generate')

        response = self.client.post(url, {'opportunity_id': opportunity.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['opportunity'], opportunity.id)
        self.assertEqual(len(response.data['rows']), 1)
        self.assertEqual(response.data['rows'][0]['status'], 'missing')
        self.assertEqual(ComplianceMatrix.objects.get().generated_by, self.user)

    def test_list_endpoint_filters_by_opportunity(self):
        first = OpportunityFactory()
        second = OpportunityFactory()
        RequirementFactory(opportunity=first, description='First requirement')
        RequirementFactory(opportunity=second, description='Second requirement')
        self.client.post(reverse('compliance-matrix-generate'), {'opportunity_id': first.id}, format='json')
        self.client.post(reverse('compliance-matrix-generate'), {'opportunity_id': second.id}, format='json')

        response = self.client.get(reverse('compliance-matrix-list'), {'opportunity': first.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['opportunity'], first.id)

    def test_patch_row_sets_human_override_and_validates_section_scope(self):
        opportunity = OpportunityFactory()
        RequirementFactory(opportunity=opportunity, description='Attach registration certificate')
        matrix_response = self.client.post(
            reverse('compliance-matrix-generate'),
            {'opportunity_id': opportunity.id},
            format='json',
        )
        row_id = matrix_response.data['rows'][0]['id']
        proposal = ProposalFactory(opportunity=opportunity)
        section = ProposalSectionFactory(proposal=proposal, section_type='annexes')

        response = self.client.patch(
            reverse('compliance-row-detail', kwargs={'pk': row_id}),
            {
                'status': 'covered',
                'proposal_section': section.id,
                'evidence_text': 'Included in annexes.',
                'human_override_note': 'Reviewed manually.',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['human_override'])
        self.assertEqual(response.data['status'], 'covered')
        matrix = ComplianceMatrix.objects.get()
        self.assertEqual(matrix.human_override_count, 1)

    def test_patch_row_rejects_section_from_different_opportunity(self):
        opportunity = OpportunityFactory()
        RequirementFactory(opportunity=opportunity, description='Attach registration certificate')
        matrix_response = self.client.post(
            reverse('compliance-matrix-generate'),
            {'opportunity_id': opportunity.id},
            format='json',
        )
        row_id = matrix_response.data['rows'][0]['id']
        other_proposal = ProposalFactory()
        other_section = ProposalSectionFactory(proposal=other_proposal)

        response = self.client.patch(
            reverse('compliance-row-detail', kwargs={'pk': row_id}),
            {'proposal_section': other_section.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('proposal_section', response.data)
