from django.db import transaction
from django.utils import timezone

from .models import ProposalExportRequest


def build_board_ready_summary(proposal, export_type):
    opportunity = proposal.opportunity
    completed_sections = proposal.sections.filter(is_complete=True).count()
    total_sections = proposal.sections.count()
    budget = getattr(proposal, 'budget', None)
    budget_line = ''
    if budget:
        budget_line = f' Budget: {budget.total} {budget.currency}.'

    outcome_line = ''
    if hasattr(proposal, 'post_mortem'):
        post_mortem = proposal.post_mortem
        outcome_line = f' Outcome captured as {post_mortem.outcome}.'

    return (
        f'{export_type.replace("_", " ").title()} for {proposal.title}. '
        f'Client: {opportunity.client}. Sector: {opportunity.sector}. '
        f'Current pursuit status: {proposal.status}. '
        f'Proposal readiness: {completed_sections}/{total_sections} sections complete.'
        f'{budget_line}{outcome_line}'
    ).strip()


def execute_export_request(export_request_id, task_id='', force=False):
    with transaction.atomic():
        export_request = (
            ProposalExportRequest.objects
            .select_for_update()
            .select_related('proposal__opportunity')
            .get(pk=export_request_id)
        )
        if export_request.status == 'completed' and not force:
            return export_request

        now = timezone.now()
        export_request.status = 'processing'
        export_request.task_id = task_id or export_request.task_id
        export_request.execution_attempts += 1
        export_request.started_at = export_request.started_at or now
        export_request.completed_at = None
        export_request.error_message = ''
        export_request.output_metadata = {
            **(export_request.output_metadata or {}),
            'execution': {
                'attempt': export_request.execution_attempts,
                'task_id': export_request.task_id,
                'started_at': now.isoformat(),
                'mode': 'deterministic_light',
            },
        }
        export_request.save(
            update_fields=[
                'status',
                'task_id',
                'execution_attempts',
                'started_at',
                'completed_at',
                'error_message',
                'output_metadata',
                'updated_at',
            ]
        )

    try:
        export_request = (
            ProposalExportRequest.objects
            .select_related('proposal__opportunity')
            .get(pk=export_request_id)
        )
        summary = build_board_ready_summary(export_request.proposal, export_request.export_type)
        now = timezone.now()
        export_request.status = 'completed'
        export_request.executive_summary = summary
        export_request.completed_at = now
        export_request.error_message = ''
        export_request.output_metadata = {
            **(export_request.output_metadata or {}),
            'generator': 'deterministic_v1',
            'format_ready': export_request.export_type in ('executive_summary', 'board_pack'),
            'heavy_rendering_deferred': export_request.export_type in ('pdf', 'pptx'),
            'proposal_status': export_request.proposal.status,
            'execution': {
                **(export_request.output_metadata or {}).get('execution', {}),
                'completed_at': now.isoformat(),
                'status': 'completed',
            },
        }
        export_request.save(
            update_fields=[
                'status',
                'executive_summary',
                'completed_at',
                'error_message',
                'output_metadata',
                'updated_at',
            ]
        )
        return export_request
    except Exception as exc:
        ProposalExportRequest.objects.filter(pk=export_request_id).update(
            status='failed',
            error_message=str(exc),
            completed_at=timezone.now(),
            updated_at=timezone.now(),
        )
        raise
