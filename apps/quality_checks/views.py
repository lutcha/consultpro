from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager

from .models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck
from .serializers import QualityCheckListSerializer, QualityCheckSerializer


class QualityCheckViewSet(viewsets.ModelViewSet):
    queryset = QualityCheck.objects.all()
    permission_classes = [IsConsultantOrManager]

    def get_serializer_class(self):
        if self.action == 'list':
            return QualityCheckListSerializer
        return QualityCheckSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        quality_check = self.get_object()
        categories_data = request.data.get('categories', [])

        with transaction.atomic():
            quality_check.categories.all().delete()

            total_score = 0
            has_fail = False

            for cat_data in categories_data:
                category = cat_data.get('category')
                score = cat_data.get('score', 0)
                cat_status = cat_data.get('status', 'pass')
                items_data = cat_data.get('items', [])

                qc_category = QCCheckCategory.objects.create(
                    quality_check=quality_check,
                    category=category,
                    score=score,
                    status=cat_status,
                )

                for item_data in items_data:
                    QCItem.objects.create(
                        category=qc_category,
                        description=item_data.get('description', ''),
                        status=item_data.get('status', 'pass'),
                        section=item_data.get('section', ''),
                    )

                total_score += score
                if cat_status == 'fail':
                    has_fail = True

            category_count = len(categories_data)
            overall_score = total_score // category_count if category_count > 0 else 0

            quality_check.overall_score = overall_score
            quality_check.status = 'completed'
            quality_check.executed_by = request.user
            quality_check.executed_at = timezone.now()
            quality_check.can_submit = overall_score >= 85 and not has_fail
            quality_check.save()

        serializer = self.get_serializer(quality_check)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def apply_suggestion(self, request, pk=None):
        quality_check = self.get_object()
        suggestion_id = request.data.get('suggestion_id')

        if not suggestion_id:
            return Response(
                {'detail': 'suggestion_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            suggestion = quality_check.suggestions.get(pk=suggestion_id)
        except QCSuggestion.DoesNotExist:
            return Response(
                {'detail': 'Suggestion not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        suggestion.applied = True
        suggestion.save(update_fields=['applied'])

        return Response({'detail': 'Suggestion applied.'})

    @action(detail=True, methods=['post'])
    def ignore_suggestion(self, request, pk=None):
        quality_check = self.get_object()
        suggestion_id = request.data.get('suggestion_id')

        if not suggestion_id:
            return Response(
                {'detail': 'suggestion_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            suggestion = quality_check.suggestions.get(pk=suggestion_id)
        except QCSuggestion.DoesNotExist:
            return Response(
                {'detail': 'Suggestion not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        suggestion.ignored = True
        suggestion.save(update_fields=['ignored'])

        return Response({'detail': 'Suggestion ignored.'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        quality_check = self.get_object()
        proposal = quality_check.proposal
        proposal.status = 'approved'
        proposal.save(update_fields=['status'])

        serializer = self.get_serializer(quality_check)
        return Response(serializer.data)
