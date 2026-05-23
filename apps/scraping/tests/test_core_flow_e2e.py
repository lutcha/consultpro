"""
Core flow E2E / smoke tests.
Coverage: Scraping -> Import -> Opportunity -> Proposal -> QC guardrails -> Export

These are lightweight, in-process, database-backed smoke tests.
No new features are introduced. No QC logic is modified.
No Celery tasks run for real (mocked at transaction.on_commit level).
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.opportunities.models import Opportunity
from apps.proposals.models import (
    Proposal,
    ProposalExportRequest,
    ProposalSection,
)
from apps.proposals.export_execution import execute_export_request
from apps.proposals.views import (
    DEFAULT_PROPOSAL_SECTIONS,
    ensure_default_sections,
    _validate_proposal_transition,
)
from apps.quality_checks.models import QualityCheck
from apps.scraping.models import ScrapedOpportunity, ScrapingSource
from apps.scraping.services.readiness import (
    MIN_IMPORT_QUALITY_SCORE,
    get_import_readiness,
)
from apps.scraping.services.opportunity_importer import import_scraped_opportunity
from apps.users.models import User


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_source(name='E2E Source'):
    return ScrapingSource.objects.create(
        name=name,
        organization='E2E Org',
        url='https://example.org/e2e-tenders',
    )


def _make_scraped_opp(source, external_id='e2e-001', **overrides):
    """Return a ScrapedOpportunity that is ready_to_import by default."""
    defaults = {
        'source': source,
        'external_id': external_id,
        'external_url': f'https://example.org/e2e-tenders/{external_id}',
        'title': 'E2E Consultoria para Governacao Digital',
        'organization': 'E2E Org',
        'client': 'Ministerio das Financas',
        'sector': 'ict',
        'country': 'cv',
        'description': 'Prestacao de servicos de consultoria para transformacao digital do sector publico.',
        'value': Decimal('250000.00'),
        'currency': 'USD',
        'status': 'new',
        'cv_eligible': True,
        'data_quality_score': Decimal('0.85'),
        'deadline': timezone.now() + timezone.timedelta(days=30),
        'ai_summary': 'Servicos de consultoria TIC para o governo.',
        'ai_extracted_requirements': ['Experiencia em e-government', 'Capacidade em Python'],
    }
    defaults.update(overrides)
    return ScrapedOpportunity.objects.create(**defaults)


def _make_user(role='manager', suffix=''):
    username = f'e2euser_{role}{suffix}'
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password='testpassword123',
        role=role,
    )


# ---------------------------------------------------------------------------
# Test 1 — Scraping import happy path
# ---------------------------------------------------------------------------

class ScrapingImportHappyPathTests(TestCase):
    """
    A ScrapedOpportunity with quality_score >= 0.45 and all gates passing
    should produce an Opportunity when import_scraped_opportunity() is called.
    Import must be idempotent.
    ai_extraction metadata on the created Opportunity must be preserved.
    """

    def setUp(self):
        self.source = _make_source('Import Source')
        self.user = _make_user('manager', '_import')

    def test_import_creates_opportunity(self):
        scraped = _make_scraped_opp(self.source)

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity') as mock_score:
            result = import_scraped_opportunity(scraped, user=self.user)

        self.assertTrue(result['created'], "Expected a new Opportunity to be created on first import.")
        self.assertEqual(result['status'], 'imported')
        self.assertIsNotNone(result.get('opportunity_id'))

    def test_import_links_scraped_opportunity_to_opportunity(self):
        scraped = _make_scraped_opp(self.source, external_id='e2e-link')

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity'):
            import_scraped_opportunity(scraped, user=self.user)

        scraped.refresh_from_db()
        self.assertIsNotNone(
            scraped.imported_opportunity_id,
            "imported_opportunity FK must be populated after import.",
        )
        self.assertEqual(scraped.status, 'imported')
        self.assertIsNotNone(scraped.imported_at)

    def test_import_is_idempotent(self):
        """Calling import twice must NOT create a second Opportunity."""
        scraped = _make_scraped_opp(self.source, external_id='e2e-idem')

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity'):
            result1 = import_scraped_opportunity(scraped, user=self.user)
            result2 = import_scraped_opportunity(scraped, user=self.user)

        opp_count = Opportunity.objects.filter(id=result1['opportunity_id']).count()
        self.assertEqual(opp_count, 1, "No duplicate Opportunity should exist.")
        self.assertEqual(result1['opportunity_id'], result2['opportunity_id'])
        self.assertFalse(result2['created'], "Second call must not create a new record.")

    def test_import_preserves_ai_extraction_metadata(self):
        """The ai_extraction field on the created Opportunity must reference the scraped source."""
        scraped = _make_scraped_opp(self.source, external_id='e2e-meta')

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity'):
            result = import_scraped_opportunity(scraped, user=self.user)

        opp = Opportunity.objects.get(pk=result['opportunity_id'])
        self.assertIsInstance(opp.ai_extraction, dict)
        self.assertEqual(opp.ai_extraction.get('schema'), 'scraped_opportunity_import_v1')
        self.assertEqual(opp.ai_extraction.get('source'), 'scraping')
        self.assertEqual(opp.ai_extraction.get('scraped_opportunity_id'), scraped.id)
        self.assertEqual(opp.ai_extraction.get('external_url'), scraped.external_url)
        # Requirements list must be preserved (even if empty list is valid)
        self.assertIn('requirements', opp.ai_extraction)

    def test_import_does_not_duplicate_on_url_match(self):
        """
        If an Opportunity already exists for the same external_url,
        import must link to it rather than create a second one.
        """
        scraped = _make_scraped_opp(self.source, external_id='e2e-url-dup')
        # Pre-create an Opportunity with the same url_source
        existing_opp = Opportunity.objects.create(
            title='Pre-existing Opportunity',
            client='Client A',
            sector='governance',
            country='cv',
            value=Decimal('100000.00'),
            currency='USD',
            deadline=timezone.now() + timezone.timedelta(days=10),
            description='Pre-existing description.',
            url_source=scraped.external_url,
        )

        with patch('apps.scraping.services.opportunity_importer.enrich_and_score_opportunity'):
            result = import_scraped_opportunity(scraped, user=self.user)

        self.assertFalse(result['created'])
        self.assertEqual(result['opportunity_id'], existing_opp.id)
        scraped.refresh_from_db()
        self.assertEqual(scraped.imported_opportunity_id, existing_opp.id)


# ---------------------------------------------------------------------------
# Test 2 — Opportunity -> Proposal
# ---------------------------------------------------------------------------

class OpportunityToProposalTests(TestCase):
    """
    Creating a Proposal linked to an Opportunity must:
    - create the Proposal
    - trigger ensure_default_sections() to set up the standard section set
    - update the Opportunity status to 'proposal_draft'
    """

    def setUp(self):
        self.user = _make_user('manager', '_proposal')
        self.opportunity = Opportunity.objects.create(
            title='E2E Oportunidade para Proposta',
            client='Banco Central',
            sector='financial_services',
            country='cv',
            region='west_africa',
            value=Decimal('300000.00'),
            currency='USD',
            deadline=timezone.now() + timezone.timedelta(days=45),
            description='Consultoria para sistema de pagamentos.',
            url_source='https://example.org/opps/e2e-prop-001',
            created_by=self.user,
        )

    def test_proposal_created(self):
        proposal = Proposal.objects.create(
            opportunity=self.opportunity,
            title='Proposta de Consultoria para Pagamentos',
            created_by=self.user,
        )
        self.assertIsNotNone(proposal.pk)
        self.assertEqual(proposal.status, 'draft')
        self.assertEqual(proposal.opportunity, self.opportunity)

    def test_ensure_default_sections_creates_standard_set(self):
        proposal = Proposal.objects.create(
            opportunity=self.opportunity,
            title='Proposta para Secoes Default',
            created_by=self.user,
        )
        # Simulate what ProposalViewSet.perform_create does
        ensure_default_sections(proposal)

        section_types = set(proposal.sections.values_list('section_type', flat=True))
        expected_types = {s[0] for s in DEFAULT_PROPOSAL_SECTIONS}
        self.assertEqual(
            section_types,
            expected_types,
            f"Expected sections {expected_types}, got {section_types}",
        )

    def test_ensure_default_sections_is_idempotent(self):
        """Calling ensure_default_sections twice must not duplicate sections."""
        proposal = Proposal.objects.create(
            opportunity=self.opportunity,
            title='Proposta Idempotent Secoes',
            created_by=self.user,
        )
        ensure_default_sections(proposal)
        ensure_default_sections(proposal)

        total_sections = proposal.sections.count()
        expected_count = len(DEFAULT_PROPOSAL_SECTIONS)
        self.assertEqual(
            total_sections,
            expected_count,
            f"Expected {expected_count} sections, got {total_sections} after second call.",
        )

    def test_proposal_creation_updates_opportunity_status(self):
        """ProposalViewSet.perform_create sets Opportunity.status to 'proposal_draft'."""
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(
            '/api/proposals/',
            data={
                'opportunity': self.opportunity.id,
                'title': 'Proposta Status Test via API',
            },
            format='json',
        )
        self.assertEqual(
            response.status_code,
            201,
            f"Expected 201 Created, got {response.status_code}: {response.data}",
        )

        self.opportunity.refresh_from_db()
        self.assertEqual(
            self.opportunity.status,
            'proposal_draft',
            "Opportunity status must be 'proposal_draft' once a proposal is created via the API.",
        )


# ---------------------------------------------------------------------------
# Test 3 — Proposal guardrails (QC / submission transition)
# ---------------------------------------------------------------------------

class ProposalQCGuardrailTests(TestCase):
    """
    Transitioning a Proposal to 'submitted' must be blocked if:
    - QC has not been executed
    - QC is not completed
    - QC can_submit is False (default threshold)
    - Proposal is not in 'ready_for_submission' state

    None of the QC logic is modified here.
    """

    def setUp(self):
        self.user = _make_user('manager', '_qc')
        self.opportunity = Opportunity.objects.create(
            title='E2E Oportunidade QC',
            client='Ministerio Saude',
            sector='health',
            country='cv',
            value=Decimal('150000.00'),
            currency='USD',
            deadline=timezone.now() + timezone.timedelta(days=60),
            description='Consultoria para sistema de saude.',
            created_by=self.user,
        )
        self.proposal = Proposal.objects.create(
            opportunity=self.opportunity,
            title='Proposta QC Guardrail Test',
            created_by=self.user,
            status='draft',
        )
        ensure_default_sections(self.proposal)

    def test_transition_to_submitted_blocked_when_no_qc(self):
        """
        Without a QualityCheck record, transition to 'submitted' must raise PermissionError.
        We first put the proposal in 'ready_for_submission' without validation to set up the
        boundary condition, then attempt the guarded 'submitted' transition.
        """
        # Set up proposal status to 'ready_for_submission' bypassing validation
        self.proposal.status = 'ready_for_submission'
        self.proposal.save(update_fields=['status', 'updated_at'])
        # Mark all sections complete so section check passes
        self.proposal.sections.update(is_complete=True)

        with self.assertRaises(PermissionError) as ctx:
            _validate_proposal_transition(self.proposal, 'submitted')

        error_msg = str(ctx.exception)
        self.assertIn('QC', error_msg, f"Expected QC reference in error, got: {error_msg}")

    def test_transition_to_submitted_blocked_when_qc_pending(self):
        """QC exists but status='pending' must still block submission."""
        QualityCheck.objects.create(
            proposal=self.proposal,
            overall_score=0,
            status='pending',
            can_submit=False,
        )
        self.proposal.status = 'ready_for_submission'
        self.proposal.save(update_fields=['status', 'updated_at'])
        self.proposal.sections.update(is_complete=True)

        with self.assertRaises(PermissionError) as ctx:
            _validate_proposal_transition(self.proposal, 'submitted')

        self.assertIn('QC', str(ctx.exception))

    def test_transition_to_submitted_blocked_when_qc_cannot_submit(self):
        """QC completed but can_submit=False must block submission."""
        QualityCheck.objects.create(
            proposal=self.proposal,
            overall_score=40,
            status='completed',
            can_submit=False,
        )
        self.proposal.status = 'ready_for_submission'
        self.proposal.save(update_fields=['status', 'updated_at'])
        self.proposal.sections.update(is_complete=True)

        with self.assertRaises(PermissionError):
            _validate_proposal_transition(self.proposal, 'submitted')

    def test_transition_to_submitted_allowed_when_qc_completed_and_can_submit(self):
        """When QC completed and can_submit=True, the transition must NOT raise."""
        QualityCheck.objects.create(
            proposal=self.proposal,
            overall_score=85,
            status='completed',
            can_submit=True,
        )
        self.proposal.status = 'ready_for_submission'
        self.proposal.save(update_fields=['status', 'updated_at'])
        self.proposal.sections.update(is_complete=True)

        # Must not raise — if it does the test will fail with the exception
        try:
            _validate_proposal_transition(self.proposal, 'submitted')
        except PermissionError as exc:
            self.fail(f"Unexpected PermissionError with valid QC: {exc}")

    def test_transition_from_draft_to_in_review_blocked_by_pursuit_governance(self):
        """
        Going from 'draft' to 'in_review' requires pursuit gates to be ready.
        With no gates approved, transition must be blocked.
        """
        # Proposal is in draft — ensure_default_pursuit_gates has NOT been called.
        # Calling _validate_proposal_transition triggers gate creation.
        with self.assertRaises(PermissionError) as ctx:
            _validate_proposal_transition(self.proposal, 'in_review')

        self.assertIn('gate', str(ctx.exception).lower())

    def test_transition_to_wrong_status_raises_value_error(self):
        """Non-existent target status must raise ValueError (not PermissionError)."""
        with self.assertRaises(ValueError):
            _validate_proposal_transition(self.proposal, 'nonexistent_status')

    def test_invalid_transition_raises_value_error(self):
        """A valid status that is not reachable from current state must raise ValueError."""
        # From 'draft', 'submitted' is not a direct allowed transition
        with self.assertRaises(ValueError):
            _validate_proposal_transition(self.proposal, 'submitted')


# ---------------------------------------------------------------------------
# Test 4 — Export request light (lifecycle without real PDF/PPT)
# ---------------------------------------------------------------------------

class ExportRequestLightTests(TestCase):
    """
    ProposalExportRequest lifecycle test using execute_export_request() directly.
    No real PDF/PPTX is generated.
    Verifies: execution_attempts increment, output_metadata presence, final status.
    """

    def setUp(self):
        self.user = _make_user('manager', '_export')
        self.opportunity = Opportunity.objects.create(
            title='E2E Export Opportunity',
            client='Fundo Monetario',
            sector='financial_services',
            country='cv',
            value=Decimal('500000.00'),
            currency='USD',
            deadline=timezone.now() + timezone.timedelta(days=90),
            description='Assessoria ao sistema financeiro.',
            created_by=self.user,
        )
        self.proposal = Proposal.objects.create(
            opportunity=self.opportunity,
            title='Proposta Export Test',
            created_by=self.user,
            status='draft',
        )
        ensure_default_sections(self.proposal)

    def _create_export_request(self, export_type='executive_summary'):
        return ProposalExportRequest.objects.create(
            proposal=self.proposal,
            export_type=export_type,
            status='queued',
            requested_by=self.user,
        )

    def test_export_request_fields_exist(self):
        """execution_attempts and output_metadata fields must exist on the model."""
        export_request = self._create_export_request()
        self.assertTrue(
            hasattr(export_request, 'execution_attempts'),
            "execution_attempts field missing from ProposalExportRequest.",
        )
        self.assertTrue(
            hasattr(export_request, 'output_metadata'),
            "output_metadata field missing from ProposalExportRequest.",
        )
        self.assertEqual(export_request.execution_attempts, 0)
        self.assertIsInstance(export_request.output_metadata, dict)

    def test_execute_export_request_completes(self):
        """execute_export_request() must leave status='completed' for executive_summary."""
        export_request = self._create_export_request(export_type='executive_summary')
        result = execute_export_request(export_request.id)
        self.assertEqual(result.status, 'completed')

    def test_execute_export_request_increments_execution_attempts(self):
        export_request = self._create_export_request()
        result = execute_export_request(export_request.id)
        self.assertGreaterEqual(result.execution_attempts, 1)

    def test_execute_export_request_populates_output_metadata(self):
        export_request = self._create_export_request()
        result = execute_export_request(export_request.id)
        self.assertIsInstance(result.output_metadata, dict)
        self.assertIn('generator', result.output_metadata)

    def test_execute_export_request_populates_executive_summary(self):
        export_request = self._create_export_request(export_type='executive_summary')
        result = execute_export_request(export_request.id)
        self.assertTrue(
            result.executive_summary,
            "executive_summary must be populated after execution.",
        )

    def test_execute_export_request_idempotent_when_completed(self):
        """Calling execute_export_request on an already-completed request must return early."""
        export_request = self._create_export_request()
        result1 = execute_export_request(export_request.id)
        result2 = execute_export_request(export_request.id, force=False)
        # Both calls must return completed; the second should not re-increment attempts
        self.assertEqual(result1.status, 'completed')
        self.assertEqual(result2.status, 'completed')
        self.assertEqual(result1.execution_attempts, result2.execution_attempts)

    def test_execute_export_request_force_reruns(self):
        """force=True must re-execute even when already completed."""
        export_request = self._create_export_request()
        result1 = execute_export_request(export_request.id)
        result2 = execute_export_request(export_request.id, force=True)
        self.assertEqual(result2.status, 'completed')
        self.assertGreater(result2.execution_attempts, result1.execution_attempts)

    def test_export_request_board_pack_type(self):
        """board_pack export type must also complete."""
        export_request = self._create_export_request(export_type='board_pack')
        result = execute_export_request(export_request.id)
        self.assertEqual(result.status, 'completed')

    def test_export_request_pdf_type_deferred(self):
        """pdf export type must complete but be flagged as heavy_rendering_deferred."""
        export_request = self._create_export_request(export_type='pdf')
        result = execute_export_request(export_request.id)
        self.assertEqual(result.status, 'completed')
        self.assertTrue(result.output_metadata.get('heavy_rendering_deferred'))


# ---------------------------------------------------------------------------
# Test 5 — Readiness alignment (low quality case)
# ---------------------------------------------------------------------------

class ReadinessLowQualityTests(TestCase):
    """
    A ScrapedOpportunity below MIN_IMPORT_QUALITY_SCORE must be flagged as not ready.
    The blocker key must be 'low_data_quality' (the canonical key from readiness.py).
    """

    def setUp(self):
        self.source = _make_source('Readiness Source')

    def _create(self, **overrides):
        defaults = {
            'source': self.source,
            'external_id': 'r-001',
            'external_url': 'https://example.org/r-001',
            'title': 'Opp Baixa Qualidade',
            'organization': 'Org',
            'client': 'Client',
            'description': 'Desc',
            'value': Decimal('1000.00'),
            'currency': 'USD',
            'status': 'new',
            'cv_eligible': True,
            'deadline': timezone.now() + timezone.timedelta(days=20),
        }
        defaults.update(overrides)
        return ScrapedOpportunity.objects.create(**defaults)

    def test_below_threshold_is_not_ready(self):
        low_score = Decimal('0.44')
        self.assertLess(
            low_score,
            MIN_IMPORT_QUALITY_SCORE,
            "Test setup: score must be below threshold.",
        )
        opp = self._create(data_quality_score=low_score)
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])

    def test_below_threshold_includes_low_data_quality_reason(self):
        opp = self._create(data_quality_score=Decimal('0.20'))
        result = get_import_readiness(opp)
        self.assertIn('low_data_quality', result['reasons'])
        self.assertIn('low_data_quality', result['blockers'])

    def test_exactly_at_threshold_is_ready(self):
        """Quality score equal to MIN_IMPORT_QUALITY_SCORE must pass (boundary value)."""
        opp = self._create(
            external_id='r-boundary',
            data_quality_score=MIN_IMPORT_QUALITY_SCORE,
        )
        result = get_import_readiness(opp)
        self.assertNotIn('low_data_quality', result['reasons'])

    def test_zero_quality_score_reason_key(self):
        """Edge: zero score must produce exactly 'low_data_quality', not some other key."""
        opp = self._create(
            external_id='r-zero',
            data_quality_score=Decimal('0.00'),
        )
        result = get_import_readiness(opp)
        self.assertFalse(result['ready'])
        self.assertIn('low_data_quality', result['reasons'])

    def test_quality_score_reflected_in_result(self):
        """get_import_readiness must echo back the quality_score in the result dict."""
        score = Decimal('0.33')
        opp = self._create(external_id='r-echo', data_quality_score=score)
        result = get_import_readiness(opp)
        self.assertEqual(result['quality_score'], str(score))

    def test_threshold_value_in_result(self):
        """The threshold and minimum_quality_score keys must match MIN_IMPORT_QUALITY_SCORE."""
        opp = self._create(external_id='r-thresh', data_quality_score=Decimal('0.10'))
        result = get_import_readiness(opp)
        self.assertEqual(result['threshold'], str(MIN_IMPORT_QUALITY_SCORE))
        self.assertEqual(result['minimum_quality_score'], str(MIN_IMPORT_QUALITY_SCORE))

    def test_low_quality_does_not_block_import_when_above_threshold(self):
        """Score at 0.80 must not trigger low_data_quality."""
        opp = self._create(external_id='r-high', data_quality_score=Decimal('0.80'))
        result = get_import_readiness(opp)
        self.assertNotIn('low_data_quality', result['reasons'])
        self.assertTrue(result['ready'])


# ---------------------------------------------------------------------------
# Test 6 - import_ready endpoint - low quality path
# ---------------------------------------------------------------------------

class ImportReadyEndpointTests(TestCase):
    """
    POST /api/scraping/opportunities/import_ready/ must skip ScrapedOpportunity
    records that are below MIN_IMPORT_QUALITY_SCORE, reporting them in the
    'skipped' list with reason 'low_data_quality'.
    """

    def setUp(self):
        self.source = _make_source('ImportReady Source')
        self.user = _make_user('manager', '_importready')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _create_low_quality(self, external_id='ir-low-001'):
        low_score = Decimal('0.20')
        return ScrapedOpportunity.objects.create(
            source=self.source,
            external_id=external_id,
            external_url=f'https://example.org/ir/{external_id}',
            title='Oportunidade de baixa qualidade',
            organization='Low Q Org',
            client='Client IR',
            description='Descricao insuficiente.',
            value=Decimal('5000.00'),
            currency='USD',
            status='new',
            cv_eligible=True,
            data_quality_score=low_score,
            deadline=timezone.now() + timezone.timedelta(days=15),
        )

    def test_low_quality_opportunity_not_imported(self):
        """A ScrapedOpportunity below the quality threshold must be skipped, not imported."""
        self._create_low_quality()

        response = self.client.post(
            '/api/scraping/opportunities/import_ready/',
            data={},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Expected 200, got {response.status_code}: {response.data}",
        )
        data = response.data
        self.assertEqual(
            data['imported_count'],
            0,
            "Low quality opportunity must not be imported.",
        )
        skipped = data.get('skipped', [])
        self.assertGreater(len(skipped), 0, "Expected at least one entry in 'skipped'.")
        skipped_reasons = [
            reason
            for entry in skipped
            for reason in entry.get('reasons', [])
        ]
        self.assertIn(
            'low_data_quality',
            skipped_reasons,
            f"Expected 'low_data_quality' in skipped reasons, got: {skipped_reasons}",
        )
