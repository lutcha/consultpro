from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.services import compute_procurement_trends
from apps.core.permissions import IsConsultantOrManager


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsConsultantOrManager]

    @action(detail=False, methods=['get'], url_path='trends')
    def trends(self, request):
        return Response(compute_procurement_trends())
