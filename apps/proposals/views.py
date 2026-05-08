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
from apps.users.models import User
from .document_generator import generate_proposal_docx, generate_proposal_pdf
from .models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalSection,
    ProposalTeamMember,
)
from .serializers import (
    AISuggestionSerializer,
    BudgetSerializer,
    BudgetItemSerializer,
    CommentSerializer,
    ProposalDetailSerializer,
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


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

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
        methods=['get', 'put'],
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

        serializer = ProposalSectionSerializer(
            section, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
            "Write in the proposal language and return only the suggested section text."
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
        proposal.status = 'qc_check'
        proposal.submitted_at = timezone.now()
        proposal.save(update_fields=['status', 'submitted_at'])
        return Response(
            {'status': proposal.status, 'submitted_at': proposal.submitted_at}
        )

    @action(detail=True, methods=['get'])
    def team(self, request, pk=None):
        proposal = self.get_object()
        team = proposal.team_members_detail.all()
        serializer = ProposalTeamMemberSerializer(team, many=True)
        return Response(serializer.data)

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
