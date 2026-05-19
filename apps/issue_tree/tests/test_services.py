from django.test import TestCase

from apps.issue_tree.models import IssueTreeNode, IssueTreeSnapshot
from apps.issue_tree.services import create_issue_tree_snapshot, generate_issue_tree
from apps.opportunities.tests.factories import RequirementFactory
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory, UserFactory


class IssueTreeServiceTests(TestCase):
    def test_generate_issue_tree_creates_mece_nodes_from_sections_and_requirements(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, section_type='methodology', title='Methodology', order=2)
        ProposalSectionFactory(proposal=proposal, section_type='team', title='Team', order=3)
        RequirementFactory(opportunity=proposal.opportunity, description='Attach signed declaration')

        root = generate_issue_tree(proposal.id)

        self.assertEqual(root.proposal, proposal)
        self.assertEqual(root.node_type, 'root')
        self.assertTrue(IssueTreeNode.objects.filter(proposal=proposal, source_key='issue:technical_solution').exists())
        self.assertTrue(IssueTreeNode.objects.filter(proposal=proposal, source_key__startswith='section:').exists())
        self.assertTrue(IssueTreeNode.objects.filter(proposal=proposal, source_key__startswith='requirement:').exists())

    def test_generate_issue_tree_is_idempotent(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, section_type='budget')

        generate_issue_tree(proposal.id)
        first_count = IssueTreeNode.objects.count()
        generate_issue_tree(proposal.id)

        self.assertEqual(IssueTreeNode.objects.count(), first_count)

    def test_create_issue_tree_snapshot_versions_increment(self):
        user = UserFactory()
        proposal = ProposalFactory()
        generate_issue_tree(proposal.id, generated_by=user)

        first = create_issue_tree_snapshot(proposal.id, label='baseline', created_by=user)
        second = create_issue_tree_snapshot(proposal.id, label='review', created_by=user)

        self.assertEqual(first.version, 1)
        self.assertEqual(second.version, 2)
        self.assertEqual(IssueTreeSnapshot.objects.count(), 2)
        self.assertTrue(first.snapshot['nodes'])
