import html
import re
import unicodedata

from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrAdmin
from apps.curriculum.matching import match_cv_to_opportunity
from apps.curriculum.models import Curriculum
from apps.projects.models import Project, ProjectArtifact, ProjectPhase
from apps.users.models import User
from .document_generator import generate_proposal_docx, generate_proposal_pdf
from .models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalEvent,
    ProposalSection,
    ProposalStatusHistory,
    ProposalTeamMember,
)
from .serializers import (
    AISuggestionSerializer,
    BudgetSerializer,
    BudgetItemSerializer,
    CommentSerializer,
    ProposalDetailSerializer,
    ProposalEventSerializer,
    ProposalListSerializer,
    ProposalSectionSerializer,
    ProposalTeamMemberSerializer,
)

DEFAULT_PROPOSAL_SECTIONS = [
    ('cover', 'Capa', 1),
    ('executive_summary', 'Resumo Executivo', 2),
    ('methodology', 'Metodologia', 3),
    ('team', 'Equipa Tecnica', 4),
    ('workplan', 'Plano de Trabalho', 5),
    ('budget', 'Orcamento', 6),
    ('annexes', 'Anexos', 7),
]

SECTION_COS_SOURCES = {
    'cover': ('submission_requirements',),
    'executive_summary': (
        'proposal_strategy',
        'strategic_opportunities',
        'tor_dissection_matrix',
    ),
    'methodology': (
        'methodology_blueprint',
        'tor_dissection_matrix',
        'qc_checklist',
    ),
    'team': ('team_requirements',),
    'workplan': ('workplan_requirements',),
    'budget': ('budget_requirements',),
    'annexes': ('submission_requirements', 'qc_checklist'),
    'custom': (
        'proposal_strategy',
        'methodology_blueprint',
        'submission_requirements',
        'qc_checklist',
    ),
}

GAP_STOPWORDS = {
    'a', 'ao', 'aos', 'as', 'com', 'como', 'da', 'das', 'de', 'do', 'dos',
    'e', 'em', 'na', 'nas', 'no', 'nos', 'o', 'os', 'ou', 'para', 'por',
    'que', 'se', 'sem', 'the', 'and', 'for', 'with', 'from', 'into', 'this',
    'that', 'shall', 'must', 'will', 'should',
}


def _extract_cos_value(opportunity, *keys):
    data = opportunity.ai_extraction or {}
    cos_analysis = data.get('cos_analysis') or {}
    current = cos_analysis
    for key in keys:
        if not isinstance(current, dict):
            return ''
        current = current.get(key)
    if isinstance(current, str):
        return current
    if isinstance(current, list):
        return '\n'.join(f"- {item}" for item in current if item)
    if isinstance(current, dict):
        return '\n'.join(f"{key}: {value}" for key, value in current.items() if value)
    return ''


def _format_context_value(value):
    if not value:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(f"- {_format_context_value(item)}" for item in value if item)
    if isinstance(value, dict):
        return '\n'.join(
            f"{key}: {_format_context_value(item)}" for key, item in value.items() if item
        )
    return str(value)


def _default_section_content(proposal, section_type):
    opportunity = proposal.opportunity
    if section_type == 'cover':
        return (
            f"<h1>{proposal.title}</h1>"
            f"<p><strong>Cliente:</strong> {opportunity.client}</p>"
            f"<p><strong>Setor:</strong> {opportunity.sector}</p>"
            f"<p><strong>País:</strong> {opportunity.country}</p>"
            f"<p><strong>Referência:</strong> {opportunity.reference_number or 'N/A'}</p>"
        )
    if section_type == 'executive_summary':
        summary = opportunity.ai_summary or opportunity.description
        return f"<p>{summary}</p>" if summary else ''
    if section_type == 'methodology':
        methodology = _extract_cos_value(opportunity, 'methodology_blueprint')
        return f"<p>{methodology}</p>" if methodology else ''
    if section_type == 'team':
        team_requirements = _extract_cos_value(opportunity, 'team_requirements')
        return f"<p>{team_requirements}</p>" if team_requirements else ''
    if section_type == 'workplan':
        workplan = _extract_cos_value(opportunity, 'workplan_requirements')
        return f"<p>{workplan}</p>" if workplan else ''
    if section_type == 'budget':
        budget = _extract_cos_value(opportunity, 'budget_requirements')
        return f"<p>{budget}</p>" if budget else ''
    return ''


def _build_proposal_ai_context(proposal):
    opportunity = proposal.opportunity
    context_parts = [
        f"Titulo da proposta: {proposal.title}",
        f"Secao/Oportunidade: {opportunity.title}",
        f"Cliente: {opportunity.client}",
        f"Pais: {opportunity.country}",
        f"Setor: {opportunity.sector}",
        f"Valor: {opportunity.value} {opportunity.currency}",
        f"Prazo: {opportunity.deadline.date() if opportunity.deadline else 'N/A'}",
        f"Resumo IA da oportunidade: {opportunity.ai_summary or ''}",
        f"Descricao/TdR: {opportunity.description or ''}",
    ]
    cos_analysis = (opportunity.ai_extraction or {}).get('cos_analysis') or {}
    for key in (
        'tor_dissection_matrix',
        'strategic_opportunities',
        'proposal_strategy',
        'methodology_blueprint',
        'team_requirements',
        'workplan_requirements',
        'budget_requirements',
        'submission_requirements',
        'qc_checklist',
    ):
        formatted_value = _format_context_value(cos_analysis.get(key))
        if formatted_value:
            context_parts.append(f"{key}:\n{formatted_value}")

    return '\n\n'.join(part for part in context_parts if part).strip()[:12000]


def _normalize_gap_text(value):
    text = html.unescape(str(value or ''))
    text = re.sub(r'<[^>]+>', ' ', text)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9]+', ' ', text).lower()
    return re.sub(r'\s+', ' ', text).strip()


def _gap_keywords(label):
    return [
        token
        for token in _normalize_gap_text(label).split()
        if len(token) > 3 and token not in GAP_STOPWORDS
    ]


def _clean_gap_label(value):
    label = re.sub(r'\s+', ' ', str(value or '')).strip()
    return label[:260]


def _gap_items_from_value(value, source, priority='context'):
    if not value:
        return []
    if isinstance(value, str):
        label = _clean_gap_label(value)
        return [{'label': label, 'source': source, 'priority': priority}] if label else []
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_gap_items_from_value(item, source, priority))
        return items
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            source_label = f"{source} - {str(key).replace('_', ' ')}"
            if isinstance(item, (list, dict)):
                items.extend(_gap_items_from_value(item, source_label, priority))
            else:
                items.extend(_gap_items_from_value(item, source_label, priority))
        return items
    label = _clean_gap_label(value)
    return [{'label': label, 'source': source, 'priority': priority}] if label else []


def _requirement_matches_section(section_type, requirement):
    if section_type == 'custom':
        return True
    category_map = {
        'financial': {'budget', 'executive_summary'},
        'institutional': {'team', 'annexes', 'executive_summary'},
        'technical': {'methodology', 'workplan', 'team', 'executive_summary'},
        'functional': {'methodology', 'workplan', 'executive_summary'},
    }
    return section_type in category_map.get(requirement.category, {'methodology'})


def _score_gap_item(label, section_content):
    content = _normalize_gap_text(section_content)
    normalized_label = _normalize_gap_text(label)
    if not content:
        return 'missing', ''
    if normalized_label and len(normalized_label) > 24 and normalized_label in content:
        return 'covered', label[:120]

    keywords = _gap_keywords(label)
    if not keywords:
        return ('covered', label[:120]) if normalized_label in content else ('missing', '')

    matched = [keyword for keyword in keywords if keyword in content]
    if not matched:
        return 'missing', ''

    ratio = len(matched) / len(set(keywords))
    if len(matched) >= min(3, len(set(keywords))) or ratio >= 0.45:
        return 'covered', ', '.join(matched[:5])
    return 'partial', ', '.join(matched[:5])


def _build_section_gap_analysis(proposal, section):
    opportunity = proposal.opportunity
    raw_items = []
    for requirement in opportunity.requirements.all():
        if _requirement_matches_section(section.section_type, requirement):
            raw_items.append(
                {
                    'label': _clean_gap_label(requirement.description),
                    'source': 'Requisito da oportunidade',
                    'priority': requirement.priority,
                }
            )

    cos_analysis = (opportunity.ai_extraction or {}).get('cos_analysis') or {}
    for key in SECTION_COS_SOURCES.get(section.section_type, SECTION_COS_SOURCES['custom']):
        raw_items.extend(
            _gap_items_from_value(
                cos_analysis.get(key),
                f"COS: {key.replace('_', ' ')}",
            )
        )

    seen = set()
    items = []
    for item in raw_items:
        normalized = _normalize_gap_text(item['label'])
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        item_status, evidence = _score_gap_item(item['label'], section.content or '')
        items.append({**item, 'status': item_status, 'evidence': evidence})

    status_order = {'missing': 0, 'partial': 1, 'covered': 2}
    items.sort(key=lambda item: (status_order[item['status']], item['source'], item['label']))

    total = len(items)
    covered = sum(1 for item in items if item['status'] == 'covered')
    partial = sum(1 for item in items if item['status'] == 'partial')
    score = round(((covered + partial * 0.5) / total) * 100) if total else 0
    suggestions = [
        f"Integrar na seccao: {item['label']}"
        for item in items
        if item['status'] in ('missing', 'partial')
    ][:5]

    return {
        'section': {
            'id': section.id,
            'title': section.title,
            'section_type': section.section_type,
        },
        'score': score,
        'covered_count': covered,
        'partial_count': partial,
        'total_count': total,
        'items': items,
        'suggestions': suggestions,
    }


def ensure_default_sections(proposal):
    for section_type, title, order in DEFAULT_PROPOSAL_SECTIONS:
        ProposalSection.objects.get_or_create(
            proposal=proposal,
            section_type=section_type,
            defaults={
                'title': title,
                'order': order,
                'content': _default_section_content(proposal, section_type),
            },
        )


def _validate_submission_readiness(proposal):
    ensure_default_sections(proposal)
    required_types = {item[0] for item in DEFAULT_PROPOSAL_SECTIONS if item[0] != 'annexes'}
    sections = proposal.sections.all()
    section_by_type = {section.section_type: section for section in sections}

    missing_required = sorted(required_types - set(section_by_type.keys()))
    incomplete_required = sorted(
        section_type
        for section_type in required_types
        if section_type in section_by_type and not section_by_type[section_type].is_complete
    )

    if proposal.status != 'ready_for_submission':
        return (
            False,
            {
                'detail': 'A proposta deve estar no estado ready_for_submission antes de submeter.',
                'missing_required_sections': missing_required,
                'incomplete_required_sections': incomplete_required,
            },
        )

    if missing_required or incomplete_required:
        return (
            False,
            {
                'detail': 'Existem secções obrigatórias em falta ou incompletas.',
                'missing_required_sections': missing_required,
                'incomplete_required_sections': incomplete_required,
            },
        )

    return True, None


def _ensure_project_for_proposal(proposal, manager=None):
    opportunity = proposal.opportunity
    budget = getattr(proposal, 'budget', None)
    project, _created = Project.objects.get_or_create(
        proposal=proposal,
        defaults={
            'title': proposal.title,
            'description': opportunity.description or '',
            'client': opportunity.client,
            'status': Project.Status.PLANNING,
            'start_date': None,
            'end_date': opportunity.deadline.date() if opportunity.deadline else None,
            'budget_total': budget.total if budget else opportunity.value,
            'budget_currency': budget.currency if budget else opportunity.currency,
            'manager': manager or proposal.created_by,
            'sector': opportunity.sector,
            'country': opportunity.country,
            'region': getattr(opportunity, 'region', ''),
        },
    )

    phases = [
        ('initiating', 0),
        ('planning', 1),
        ('executing', 2),
        ('monitoring', 3),
        ('closing', 4),
    ]
    for name, order in phases:
        ProjectPhase.objects.get_or_create(
            project=project,
            name=name,
            defaults={'order': order},
        )
    _sync_proposal_events_to_project_artifacts(proposal, project, created_by=manager)
    return project


PROPOSAL_EVENT_ARTIFACT_TYPES = {
    'submission': ProjectArtifact.ArtifactType.FINAL_PROPOSAL,
    'bafo': ProjectArtifact.ArtifactType.FINAL_PROPOSAL,
    'contracting': ProjectArtifact.ArtifactType.CONTRACT,
    'handover': ProjectArtifact.ArtifactType.HANDOVER,
}


def _event_artifact_type(event):
    if event.artifact_type:
        return event.artifact_type
    return PROPOSAL_EVENT_ARTIFACT_TYPES.get(event.event_type)


def _sync_proposal_events_to_project_artifacts(proposal, project, created_by=None):
    for event in proposal.events.all():
        artifact_type = _event_artifact_type(event)
        if not artifact_type:
            continue

        artifact, created = ProjectArtifact.objects.get_or_create(
            project=project,
            title=event.title,
            artifact_type=artifact_type,
            defaults={
                'status': ProjectArtifact.Status.ATTACHED
                if event.attachment or event.external_url
                else ProjectArtifact.Status.PENDING,
                'external_url': event.external_url,
                'notes': event.notes,
                'created_by': created_by or event.created_by,
            },
        )
        update_fields = []
        if event.attachment and artifact.file != event.attachment:
            artifact.file = event.attachment
            update_fields.append('file')
        if event.external_url and artifact.external_url != event.external_url:
            artifact.external_url = event.external_url
            update_fields.append('external_url')
        if event.notes and artifact.notes != event.notes:
            artifact.notes = event.notes
            update_fields.append('notes')
        if created:
            continue
        if update_fields:
            artifact.status = ProjectArtifact.Status.ATTACHED
            update_fields.append('status')
            artifact.save(update_fields=update_fields + ['updated_at'])


PROPOSAL_STATUS_EVENT_TYPES = {
    'submitted': 'submission',
    'under_evaluation': 'evaluation',
    'shortlisted': 'shortlist',
    'clarifications_requested': 'clarification',
    'bafo': 'bafo',
    'awarded': 'award',
    'contract_negotiation': 'contracting',
    'contract_signed': 'contracting',
    'project_initiation': 'handover',
    'lost': 'note',
    'rejected': 'note',
}

ALLOWED_PROPOSAL_TRANSITIONS = {
    'draft': {'in_review'},
    'in_review': {'qc_check', 'draft'},
    'qc_check': {'ready_for_submission', 'in_review'},
    'ready_for_submission': {'submitted'},
    'submitted': {'under_evaluation', 'rejected'},
    'under_evaluation': {'shortlisted', 'clarifications_requested', 'rejected'},
    'shortlisted': {'bafo', 'awarded', 'lost'},
    'clarifications_requested': {'under_evaluation', 'rejected'},
    'bafo': {'awarded', 'lost'},
    'awarded': {'contract_negotiation'},
    'contract_negotiation': {'contract_signed'},
    'contract_signed': {'project_initiation'},
    'project_initiation': {'won'},
}


def _qc_min_score_from_request(request):
    raw_value = request.data.get('qc_min_score')
    if raw_value in (None, ''):
        return None
    try:
        return max(0, min(100, int(raw_value)))
    except (TypeError, ValueError):
        raise ValueError('Invalid QC minimum score.')


def _proposal_has_passing_qc(proposal, min_score=None):
    quality_check = getattr(proposal, 'quality_check', None)
    if not quality_check or quality_check.status != 'completed':
        return False
    if min_score is not None:
        return quality_check.overall_score >= min_score
    return bool(
        quality_check.can_submit
    )


def _validate_proposal_transition(proposal, status_value, qc_min_score=None):
    valid_statuses = {choice[0] for choice in Proposal.STATUS_CHOICES}
    if status_value not in valid_statuses:
        raise ValueError('Invalid proposal status.')

    if status_value not in ALLOWED_PROPOSAL_TRANSITIONS.get(proposal.status, set()):
        raise ValueError('Invalid proposal status transition.')

    if status_value in {'ready_for_submission', 'submitted'} and not _proposal_has_passing_qc(
        proposal,
        min_score=qc_min_score,
    ):
        raise PermissionError('Proposal needs a completed passing QC before submission.')


def _event_artifact_type_from_status(status_value):
    event_type = PROPOSAL_STATUS_EVENT_TYPES.get(status_value)
    if not event_type:
        return ''
    return PROPOSAL_EVENT_ARTIFACT_TYPES.get(event_type, '')


def _set_proposal_status(
    proposal,
    status_value,
    user=None,
    note='',
    validate_transition=False,
    qc_min_score=None,
):
    if validate_transition:
        _validate_proposal_transition(proposal, status_value, qc_min_score=qc_min_score)

    valid_statuses = {choice[0] for choice in Proposal.STATUS_CHOICES}
    if status_value not in valid_statuses:
        raise ValueError('Invalid proposal status.')

    proposal.status = status_value
    update_fields = ['status', 'updated_at']
    if status_value == 'submitted' and not proposal.submitted_at:
        proposal.submitted_at = timezone.now()
        update_fields.append('submitted_at')
    proposal.save(update_fields=update_fields)
    ProposalStatusHistory.objects.create(
        proposal=proposal,
        status=status_value,
        changed_by=user,
        note=note,
    )
    event_type = PROPOSAL_STATUS_EVENT_TYPES.get(status_value)
    if event_type:
        status_label = dict(Proposal.STATUS_CHOICES).get(status_value, status_value)
        ProposalEvent.objects.create(
            proposal=proposal,
            event_type=event_type,
            artifact_type=_event_artifact_type_from_status(status_value),
            title=status_label,
            notes=note,
            created_by=user,
        )
    return proposal


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('manager', 'admin') or user.is_staff:
            return Proposal.objects.all()
        return Proposal.objects.filter(created_by=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return ProposalListSerializer
        return ProposalDetailSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            proposal = serializer.save(created_by=self.request.user)
            ensure_default_sections(proposal)
            proposal.opportunity.status = 'proposal_draft'
            proposal.opportunity.save(update_fields=['status', 'updated_at'])

    def retrieve(self, request, *args, **kwargs):
        proposal = self.get_object()
        ensure_default_sections(proposal)
        serializer = self.get_serializer(proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        proposal = self.get_object()
        ensure_default_sections(proposal)
        sections = proposal.sections.all()
        serializer = ProposalSectionSerializer(sections, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get', 'post'],
        parser_classes=[MultiPartParser, FormParser],
    )
    def events(self, request, pk=None):
        proposal = self.get_object()

        if request.method == 'GET':
            serializer = ProposalEventSerializer(
                proposal.events.all(),
                many=True,
                context={'request': request},
            )
            return Response(serializer.data)

        data = request.data.copy()
        data['proposal'] = proposal.id
        serializer = ProposalEventSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_section(self, request, pk=None):
        proposal = self.get_object()
        title = str(request.data.get('title') or '').strip()
        if not title:
            return Response(
                {'detail': 'title is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        section_type = request.data.get('section_type') or 'custom'
        valid_section_types = {choice[0] for choice in ProposalSection.SECTION_TYPE_CHOICES}
        if section_type not in valid_section_types:
            section_type = 'custom'

        next_order = (proposal.sections.aggregate(max_order=Max('order'))['max_order'] or 0) + 1
        section = ProposalSection.objects.create(
            proposal=proposal,
            section_type=section_type,
            title=title[:200],
            content=request.data.get('content') or '',
            order=next_order,
        )
        serializer = ProposalSectionSerializer(section)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['get', 'put', 'delete'],
        url_path='sections/(?P<section_id>[^/.]+)',
    )
    def section_detail(self, request, pk=None, section_id=None):
        proposal = self.get_object()
        try:
            section = proposal.sections.get(pk=section_id)
        except ProposalSection.DoesNotExist:
            return Response(
                {'detail': 'Section not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method == 'GET':
            serializer = ProposalSectionSerializer(section)
            return Response(serializer.data)

        if request.method == 'DELETE':
            if section.section_type != 'custom':
                return Response(
                    {'detail': 'Apenas secções custom podem ser removidas.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            section.delete()
            remaining = proposal.sections.all().order_by('order', 'id')
            for order, remaining_section in enumerate(remaining, start=1):
                if remaining_section.order != order:
                    remaining_section.order = order
                    remaining_section.save(update_fields=['order', 'updated_at'])
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ProposalSectionSerializer(section, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reorder_sections(self, request, pk=None):
        proposal = self.get_object()
        section_ids = request.data.get('section_ids')
        if not isinstance(section_ids, list) or not section_ids:
            return Response(
                {'detail': 'section_ids must be a non-empty list.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        existing_sections = list(proposal.sections.values_list('id', flat=True))
        try:
            normalized = [int(section_id) for section_id in section_ids]
        except (TypeError, ValueError):
            return Response(
                {'detail': 'section_ids must contain valid integer ids.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sorted(normalized) != sorted(existing_sections):
            return Response(
                {'detail': 'section_ids must match all proposal sections exactly.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for order, section_id in enumerate(normalized, start=1):
                ProposalSection.objects.filter(proposal=proposal, id=section_id).update(order=order)

        serializer = ProposalSectionSerializer(proposal.sections.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def section_gap(self, request, pk=None):
        proposal = self.get_object()
        section_id = request.query_params.get('section_id')
        if not section_id:
            return Response(
                {'detail': 'section_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            section = proposal.sections.get(pk=section_id)
        except ProposalSection.DoesNotExist:
            return Response(
                {'detail': 'Section not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_build_section_gap_analysis(proposal, section))

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        proposal = self.get_object()
        section_id = request.data.get('section_id')
        if not section_id:
            return Response(
                {'detail': 'section_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            section = proposal.sections.get(pk=section_id)
        except ProposalSection.DoesNotExist:
            return Response(
                {'detail': 'Section not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CommentSerializer(
            data={
                'section': section.id,
                'user_id': request.user.id,
                'text': request.data.get('text', ''),
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def ai_suggest(self, request, pk=None):
        proposal = self.get_object()
        section_id = request.data.get('section_id')
        action_type = str(request.data.get('action') or '').replace('-', '_')
        if not section_id or not action_type:
            return Response(
                {'detail': 'section_id and action are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        valid_actions = {choice[0] for choice in AISuggestion.ACTION_CHOICES}
        if action_type not in valid_actions:
            return Response(
                {'detail': 'Invalid AI action.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            section = proposal.sections.get(pk=section_id)
        except ProposalSection.DoesNotExist:
            return Response(
                {'detail': 'Section not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # AI service integration
        from apps.ai_services.services import AIServiceFactory
        service = AIServiceFactory.get_service()
        current_content = request.data.get('current_content', section.content or '')
        proposal_context = _build_proposal_ai_context(proposal)
        prompt_content = (
            f"Proposal context:\n{proposal_context}\n\n"
            f"Target section title: {section.title}\n"
            f"Target section type: {section.section_type}\n"
            f"Current section content:\n{current_content}\n\n"
            "Write in the proposal language. Return clean HTML for a rich text editor "
            "using paragraphs, headings, lists, and tables when useful. Do not return Markdown."
        )
        generated_content = service.generate_suggestion(
            section_type=section.title or section.section_type,
            content=prompt_content,
            action=action_type,
        )
        
        description = request.data.get('description', '')
        if not description and generated_content:
            description = generated_content[:200]
        
        serializer = AISuggestionSerializer(
            data={
                'section': section.id,
                'action': action_type,
                'description': description,
                'generated_content': generated_content,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        proposal = self.get_object()
        proposal.auto_save_status = 'saved'
        proposal.last_saved_at = timezone.now()
        proposal.save(update_fields=['auto_save_status', 'last_saved_at'])
        return Response(
            {'status': 'saved', 'last_saved_at': proposal.last_saved_at}
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        proposal = self.get_object()
        is_ready, error_payload = _validate_submission_readiness(proposal)
        if not is_ready:
            return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)
        try:
            qc_min_score = _qc_min_score_from_request(request)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            _set_proposal_status(
                proposal,
                'submitted',
                user=request.user,
                note=request.data.get('note', 'Proposta submetida ao cliente/concurso.'),
                validate_transition=True,
                qc_min_score=qc_min_score,
            )
        except PermissionError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
        except ValueError:
            return Response({'detail': 'Transicao de proposta invalida.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {'status': proposal.status, 'submitted_at': proposal.submitted_at}
        )

    @action(detail=True, methods=['post'])
    def approve_for_submission(self, request, pk=None):
        proposal = self.get_object()
        try:
            qc_min_score = _qc_min_score_from_request(request)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            try:
                _set_proposal_status(
                    proposal,
                    'ready_for_submission',
                    user=request.user,
                    note=request.data.get('note', 'QC aprovado. Proposta pronta para submissao.'),
                    validate_transition=True,
                    qc_min_score=qc_min_score,
                )
            except PermissionError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
            except ValueError:
                return Response({'detail': 'Transicao de proposta invalida.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': proposal.status,
            'proposal_id': proposal.id,
            'proposal_url': f'/proposals/{proposal.id}',
        })

    @action(detail=True, methods=['post'])
    def transition_status(self, request, pk=None):
        proposal = self.get_object()
        next_status = request.data.get('status')
        note = request.data.get('note', '')
        try:
            qc_min_score = _qc_min_score_from_request(request)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            try:
                _set_proposal_status(
                    proposal,
                    next_status,
                    user=request.user,
                    note=note,
                    validate_transition=True,
                    qc_min_score=qc_min_score,
                )
            except PermissionError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
            except ValueError:
                return Response(
                    {'detail': 'Transicao de proposta invalida.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = {
                'status': proposal.status,
                'proposal_id': proposal.id,
                'proposal_url': f'/proposals/{proposal.id}',
            }
            if proposal.status in ('contract_signed', 'project_initiation'):
                project = _ensure_project_for_proposal(proposal, manager=request.user)
                data['project_id'] = project.id
                data['project_url'] = f'/projects/{project.id}'

        return Response(data)

    @action(detail=True, methods=['get'])
    def team(self, request, pk=None):
        proposal = self.get_object()
        team = proposal.team_members_detail.all()
        serializer = ProposalTeamMemberSerializer(team, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def team_match(self, request, pk=None):
        proposal = self.get_object()
        members = proposal.team_members_detail.select_related('user').all()
        items = []
        total_score = 0
        scored_members = 0

        for member in members:
            curriculum = (
                Curriculum.objects.filter(user=member.user, status='analyzed')
                .order_by('-updated_at')
                .first()
            )
            if not curriculum:
                items.append({
                    'member_id': member.id,
                    'user_id': member.user_id,
                    'name': member.user.get_full_name() or member.user.email,
                    'role': member.role,
                    'has_analyzed_cv': False,
                    'overall_score': None,
                    'recommendations': ['Sem CV analisado para este membro.'],
                })
                continue

            match = match_cv_to_opportunity(curriculum, proposal.opportunity)
            total_score += match.overall_score
            scored_members += 1
            items.append({
                'member_id': member.id,
                'user_id': member.user_id,
                'name': member.user.get_full_name() or member.user.email,
                'role': member.role,
                'has_analyzed_cv': True,
                'overall_score': match.overall_score,
                'skills_match_score': match.skills_match_score,
                'experience_match_score': match.experience_match_score,
                'education_match_score': match.education_match_score,
                'language_match_score': match.language_match_score,
                'missing_skills': match.missing_skills,
                'recommendations': match.recommendations,
            })

        team_score = int(total_score / scored_members) if scored_members else 0
        return Response({
            'proposal_id': proposal.id,
            'opportunity_id': proposal.opportunity_id,
            'team_size': members.count(),
            'scored_members': scored_members,
            'team_score': team_score,
            'items': items,
        })

    @action(detail=True, methods=['post'])
    def add_team_member(self, request, pk=None):
        proposal = self.get_object()
        data = {**request.data, 'proposal': proposal.id}
        serializer = ProposalTeamMemberSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def budget(self, request, pk=None):
        proposal = self.get_object()

        if request.method == 'GET':
            try:
                budget = proposal.budget
            except Budget.DoesNotExist:
                return Response(
                    {'detail': 'Budget not found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = BudgetSerializer(budget)
            return Response(serializer.data)

        with transaction.atomic():
            budget, created = Budget.objects.get_or_create(
                proposal=proposal,
                defaults={
                    'total': request.data.get('total', 0),
                    'currency': request.data.get('currency', 'USD'),
                },
            )
            if not created:
                serializer = BudgetSerializer(
                    budget, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            else:
                serializer = BudgetSerializer(budget)

            items_data = request.data.get('items', [])
            for item_data in items_data:
                BudgetItem.objects.update_or_create(
                    budget=budget,
                    category=item_data.get('category'),
                    defaults={
                        'amount': item_data.get('amount', 0),
                        'description': item_data.get('description', ''),
                    },
                )

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='team/(?P<member_id>[^/.]+)/upload_cv',
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_cv(self, request, pk=None, member_id=None):
        proposal = self.get_object()
        try:
            member = proposal.team_members_detail.get(pk=member_id)
        except ProposalTeamMember.DoesNotExist:
            return Response(
                {'detail': 'Team member not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        file_obj = request.FILES.get('cv_document')
        if not file_obj:
            return Response(
                {'detail': 'Nenhum ficheiro fornecido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member.cv_document = file_obj
        member.cv_attached = True
        member.save(update_fields=['cv_document', 'cv_attached'])
        serializer = ProposalTeamMemberSerializer(member)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['delete'],
        url_path='team/(?P<member_id>[^/.]+)',
    )
    def remove_team_member(self, request, pk=None, member_id=None):
        proposal = self.get_object()
        try:
            member = proposal.team_members_detail.get(pk=member_id)
        except ProposalTeamMember.DoesNotExist:
            return Response(
                {'detail': 'Team member not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        member.delete()
        return Response({'detail': 'Membro removido com sucesso.'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def download_word(self, request, pk=None):
        """Download proposal as Word (.docx) document."""
        proposal = self.get_object()
        docx_bytes = generate_proposal_docx(proposal)
        filename = f"Proposta_{proposal.id}_{proposal.title.replace(' ', '_')}.docx"
        response = HttpResponse(
            docx_bytes,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download proposal as PDF document."""
        proposal = self.get_object()
        pdf_bytes = generate_proposal_pdf(proposal)
        filename = f"Proposta_{proposal.id}_{proposal.title.replace(' ', '_')}.pdf"
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_logo(self, request, pk=None):
        """Upload proponent or client logo for the proposal."""
        proposal = self.get_object()
        logo_type = request.data.get('logo_type', 'proponent')
        file_obj = request.FILES.get('logo')
        
        if not file_obj:
            return Response(
                {'detail': 'Nenhum ficheiro fornecido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if logo_type == 'client':
            proposal.client_logo = file_obj
            proposal.save(update_fields=['client_logo'])
            return Response({
                'detail': 'Logo do cliente atualizado.',
                'url': request.build_absolute_uri(proposal.client_logo.url),
            })
        else:
            proposal.proponent_logo = file_obj
            proposal.save(update_fields=['proponent_logo'])
            return Response({
                'detail': 'Logo da empresa proponente atualizado.',
                'url': request.build_absolute_uri(proposal.proponent_logo.url),
            })

    @action(detail=True, methods=['put', 'patch'])
    def update_consortium(self, request, pk=None):
        """Update consortium members list."""
        proposal = self.get_object()
        members = request.data.get('consortium_members', [])
        proposal.consortium_members = members
        proposal.save(update_fields=['consortium_members'])
        return Response({
            'detail': 'Membros do consórcio atualizados.',
            'consortium_members': proposal.consortium_members,
        })
