from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.issue_tree.models import IssueTreeNode
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory, UserFactory


class IssueTreeViewTests(APITestCase):
    def setUp(self):
        self.user = UserFactory(role='manager')
        self.client.force_authenticate(user=self.user)

    def test_generate_endpoint_returns_root_and_list_filters_by_proposal(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, section_type='methodology')

        response = self.client.post(reverse('issue-tree-node-generate'), {'proposal_id': proposal.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['proposal'], proposal.id)
        self.assertEqual(response.data['node_type'], 'root')

        list_response = self.client.get(reverse('issue-tree-node-list'), {'proposal': proposal.id})
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(list_response.data['count'], 1)

    def test_create_node_validates_parent_scope(self):
        proposal = ProposalFactory()
        other = ProposalFactory()
        parent = IssueTreeNode.objects.create(proposal=other, title='Other root', node_type='root')

        response = self.client.post(
            reverse('issue-tree-node-list'),
            {
                'proposal': proposal.id,
                'parent': parent.id,
                'title': 'Invalid child',
                'node_type': 'issue',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Parent node must belong', str(response.data))

    def test_create_node_validates_section_scope(self):
        proposal = ProposalFactory()
        other = ProposalFactory()
        section = ProposalSectionFactory(proposal=other)

        response = self.client.post(
            reverse('issue-tree-node-list'),
            {
                'proposal': proposal.id,
                'proposal_section': section.id,
                'title': 'Invalid section link',
                'node_type': 'hypothesis',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Proposal section must belong', str(response.data))

    def test_snapshot_endpoint_creates_versioned_snapshot(self):
        proposal = ProposalFactory()
        IssueTreeNode.objects.create(proposal=proposal, title='Root', node_type='root')

        response = self.client.post(
            reverse('issue-tree-snapshot-create-snapshot'),
            {'proposal_id': proposal.id, 'label': 'review'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['version'], 1)
        self.assertEqual(response.data['created_by'], self.user.id)
