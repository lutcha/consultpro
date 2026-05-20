from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.knowledge.models import KnowledgeIndexRun
from apps.knowledge.tasks import index_knowledge_assets_task
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory


class KnowledgeIndexOperationsTests(TestCase):
    def test_index_task_returns_run_summary(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Approach', content='Governance and implementation approach')

        result = index_knowledge_assets_task(source='proposals')

        self.assertEqual(result['source'], 'proposals')
        self.assertEqual(result['status'], 'completed')
        self.assertGreaterEqual(result['indexed_count'], 2)

    def test_reindex_command_prints_counts(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Workplan', content='Delivery schedule')
        output = StringIO()

        call_command('reindex_knowledge', '--source=proposals', stdout=output)

        self.assertIn('source=proposals', output.getvalue())
        self.assertIn('indexed=', output.getvalue())
        self.assertEqual(KnowledgeIndexRun.objects.last().status, 'completed')
