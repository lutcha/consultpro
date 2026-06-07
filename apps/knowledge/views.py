from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager
from apps.tenants.utils import get_request_tenant, scope_queryset_to_request_tenant

from .models import KnowledgeAsset
from .serializers import KnowledgeAssetSerializer, KnowledgeSearchResultSerializer
from .services import SUPPORTED_INDEX_SOURCE_CHOICES, run_knowledge_reindex, search_knowledge
from .tasks import index_knowledge_assets_task


class KnowledgeAssetViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeAssetSerializer
    permission_classes = [IsConsultantOrManager]

    def get_queryset(self):
        queryset = scope_queryset_to_request_tenant(KnowledgeAsset.objects.all(), self.request)
        asset_type = self.request.query_params.get('asset_type')
        country = self.request.query_params.get('country')
        sector = self.request.query_params.get('sector')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        if country:
            queryset = queryset.filter(country__iexact=country)
        if sector:
            queryset = queryset.filter(sector__iexact=sector)
        return queryset

    def perform_create(self, serializer):
        tenant = get_request_tenant(self.request)
        if tenant:
            serializer.save(created_by=self.request.user, tenant=tenant)
        else:
            serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        results = search_knowledge(
            query=request.query_params.get('q', ''),
            asset_type=request.query_params.get('asset_type', ''),
            country=request.query_params.get('country', ''),
            sector=request.query_params.get('sector', ''),
            limit=int(request.query_params.get('limit', 10)),
            tenant=get_request_tenant(request),
        )
        serializer = KnowledgeSearchResultSerializer(results, many=True)
        return Response(
            {
                'query': request.query_params.get('q', ''),
                'search_mode': 'textual_fallback',
                'count': len(results),
                'results': serializer.data,
            }
        )

    @action(detail=False, methods=['post'])
    def index(self, request):
        source = request.data.get('source', 'all')
        async_requested = bool(request.data.get('async', False))
        if source not in SUPPORTED_INDEX_SOURCE_CHOICES:
            return Response({'detail': 'Unsupported source.'}, status=status.HTTP_400_BAD_REQUEST)
        if async_requested:
            task = index_knowledge_assets_task.delay(source=source)
            return Response(
                {
                    'queued': True,
                    'task_id': task.id,
                    'source': source,
                },
                status=status.HTTP_202_ACCEPTED,
            )
        run = run_knowledge_reindex(source=source, triggered_by=request.user)
        return Response(
            {
                'indexed': run.indexed_count,
                'source': source,
                'run': run.as_dict(),
            },
            status=status.HTTP_200_OK,
        )
