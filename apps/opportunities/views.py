from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager

from .filters import OpportunityFilter
from .models import Opportunity, Requirement, Risk
from .serializers import (
    OpportunityDetailSerializer,
    OpportunityListSerializer,
    RequirementSerializer,
    RiskSerializer,
)


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['title', 'description', 'client']
    ordering_fields = ['deadline', 'created_at', 'value']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return OpportunityListSerializer
        return OpportunityDetailSerializer

    @action(detail=True, methods=['post'])
    def go(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.status = 'go'
        opportunity.save()
        return Response({'status': 'go'})

    @action(detail=True, methods=['post'])
    def no_go(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.status = 'no_go'
        opportunity.save()
        return Response({'status': 'no_go'})

    @action(detail=True, methods=['post'])
    def analyze_tor(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.ai_analysis_status = 'processing'
        opportunity.save()
        return Response({'ai_analysis_status': 'processing'})

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_tor(self, request, pk=None):
        opportunity = self.get_object()
        file_obj = request.FILES.get('tor_document')
        if not file_obj:
            return Response(
                {'detail': 'Nenhum ficheiro fornecido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        opportunity.tor_document = file_obj
        opportunity.save()
        return Response({'detail': 'Ficheiro enviado com sucesso.'})

    @action(detail=True, methods=['get'])
    def requirements(self, request, pk=None):
        opportunity = self.get_object()
        queryset = opportunity.requirements.all()
        serializer = RequirementSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def risks(self, request, pk=None):
        opportunity = self.get_object()
        queryset = opportunity.risks.all()
        serializer = RiskSerializer(queryset, many=True)
        return Response(serializer.data)
