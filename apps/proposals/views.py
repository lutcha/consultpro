from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsOwnerOrAdmin
from apps.users.models import User
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

        # Placeholder for AI service integration.
        generated_content = ''
        serializer = AISuggestionSerializer(
            data={
                'section': section.id,
                'action': action_type,
                'description': request.data.get('description', ''),
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
        team = proposal.proposalteammember_set.all()
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
