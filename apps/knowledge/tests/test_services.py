from django.test import TestCase

from apps.knowledge.models import KnowledgeAsset, KnowledgeIndexRun
from apps.knowledge.services import index_knowledge_assets, run_knowledge_reindex, search_knowledge
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

    def test_search_knowledge_boosts_country_sector_and_high_value_sources(self):
        weaker = KnowledgeAsset.objects.create(
            asset_type='template',
            title='WASH methodology template',
            summary='Water sanitation approach',
            content='Procurement and staffing plan',
            country='Ghana',
            sector='WASH',
            source_app='manual',
            source_model='Template',
        )
        stronger = KnowledgeAsset.objects.create(
            asset_type='proposal',
            title='WASH methodology proposal',
            summary='Water sanitation approach',
            content='Procurement and staffing plan',
            country='Senegal',
            sector='WASH',
            source_app='proposals',
            source_model='Proposal',
        )

        results = search_knowledge('wash methodology', country='Senegal', sector='WASH')

        self.assertEqual(results[0]['asset'], stronger)
        self.assertNotEqual(results[0]['asset'], weaker)
        self.assertIn('country_match', results[0]['reasoning_trace'])
        self.assertIn('sector_match', results[0]['reasoning_trace'])
        self.assertIn('high_value_source', results[0]['reasoning_trace'])

    def test_search_knowledge_filters_by_source_app(self):
        KnowledgeAsset.objects.create(
            asset_type='proposal',
            title='Energy sector proposal',
            content='Transmission planning',
            source_app='proposals',
            source_model='Proposal',
        )
        template = KnowledgeAsset.objects.create(
            asset_type='template',
            title='Energy sector template',
            content='Transmission planning',
            source_app='manual',
            source_model='Template',
        )

        results = search_knowledge('energy planning', source_app='manual')

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['asset'], template)
        self.assertIn('source_app_match', results[0]['reasoning_trace'])

    def test_index_knowledge_assets_is_idempotent_for_proposals(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Methodology', content='Climate adaptation methodology')

        index_knowledge_assets(source='proposals')
        first_count = KnowledgeAsset.objects.count()
        index_knowledge_assets(source='proposals')

        self.assertEqual(KnowledgeAsset.objects.count(), first_count)
        self.assertTrue(KnowledgeAsset.objects.filter(source_model='Proposal', source_id=str(proposal.id)).exists())
        self.assertTrue(KnowledgeAsset.objects.filter(source_model='ProposalSection').exists())

    def test_run_knowledge_reindex_records_counts_and_source_stats(self):
        proposal = ProposalFactory()
        ProposalSectionFactory(proposal=proposal, title='Staffing', content='Senior experts and CVs')

        run = run_knowledge_reindex(source='proposals')

        self.assertEqual(run.status, 'completed')
        self.assertEqual(run.error_count, 0)
        self.assertGreaterEqual(run.indexed_count, 2)
        self.assertEqual(run.stats['sources']['proposals']['indexed'], run.indexed_count)
        self.assertEqual(KnowledgeIndexRun.objects.get(id=run.id).source, 'proposals')
