from django.db import transaction
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


class ProposalViewSet(viewsets.ModelViewSet):
    queryset = Proposal.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return ProposalListSerializer
        return ProposalDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        proposal = self.get_object()
        sections = proposal.sections.all()
        serializer = ProposalSectionSerializer(sections, many=True)
        return Response(serializer.data)

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
        action_type = request.data.get('action')
        if not section_id or not action_type:
            return Response(
                {'detail': 'section_id and action are required.'},
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
        generated_content = service.generate_suggestion(
            section_type=section.section_type,
            content=section.content or '',
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
            member = proposal.proposalteammember_set.get(pk=member_id)
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
            member = proposal.proposalteammember_set.get(pk=member_id)
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
