from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.services import compute_procurement_trends
from apps.core.permissions import IsConsultantOrManager


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsConsultantOrManager]

    @action(detail=False, methods=['get'], url_path='trends')
    def trends(self, request):
        horizon = request.query_params.get('horizon', 3)
        try:
            horizon = int(horizon)
        except (TypeError, ValueError):
            horizon = 3
        horizon = max(1, min(horizon, 12))
        include_forecast = request.query_params.get('include_forecast', '').lower() == 'true'

        data = compute_procurement_trends(
            country=request.query_params.get('country'),
            sector=request.query_params.get('sector'),
            horizon=horizon,
            include_forecast=include_forecast,
        )
        response = Response(data)
        if include_forecast:
            response['X-Analytics-Cache'] = data.get('predictive', {}).get('cache_status', 'none')
        return response
