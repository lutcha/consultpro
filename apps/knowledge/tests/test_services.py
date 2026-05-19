from django.test import TestCase

from apps.knowledge.models import KnowledgeAsset
from apps.knowledge.services import index_knowledge_assets, search_knowledge
from apps.proposals.tests.factories import ProposalFactory, ProposalSectionFactory


class KnowledgeServiceTests(TestCase):
    def test_search_knowledge_ranks_title_and_content_matches(self):
        first = KnowledgeAsset.objects.create(
            asset_type='case',
            title='WASH governance reform',
            summary='Water sector institutional strengthening',
            content='Sanitation and procurement reform in West Africa',
            tags=['wash', 'governance'],
        )
        KnowledgeAsset.objects.create(
            asset_type='case',
            title='Energy market analysis',
            content='Power sector assessment',
        )

        results = search_knowledge('wash procurement')

        self.assertEqual(results[0]['asset'], first)
        self.assertIn('title_match', results[0]['reasoning_trace'])
        self.assertEqual(results[0]['search_mode'], 'textual_fallback')

    def test_index_knowledge_assets_is_idempotent_for_proposals(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Methodology', content='Climate adaptation methodology')

        index_knowledge_assets(source='proposals')
        first_count = KnowledgeAsset.objects.count()
        index_knowledge_assets(source='proposals')

        self.assertEqual(KnowledgeAsset.objects.count(), first_count)
        self.assertTrue(KnowledgeAsset.objects.filter(source_model='Proposal', source_id=str(proposal.id)).exists())
        self.assertTrue(KnowledgeAsset.objects.filter(source_model='ProposalSection').exists())
