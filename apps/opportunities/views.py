import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from apps.core.permissions import IsConsultantOrManager

from .filters import OpportunityFilter
from .models import FirmProfile, Opportunity, Requirement, Risk, SavedFilter
from .scoring import score_opportunity
from .serializers import (
    OpportunityDetailSerializer,
    FirmProfileSerializer,
    OpportunityListSerializer,
    OpportunityScoreSerializer,
    RequirementSerializer,
    RiskSerializer,
    SavedFilterSerializer,
)


logger = logging.getLogger(__name__)


class OpportunityViewSet(viewsets.ModelViewSet):
    queryset = Opportunity.objects.all()
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = OpportunityFilter
    search_fields = ['title', 'description', 'client']
    ordering_fields = ['deadline', 'created_at', 'value']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        return self._apply_profile_defaults(queryset)

    def _apply_profile_defaults(self, queryset):
        if self.action != 'list':
            return queryset
        params = self.request.query_params
        if str(params.get('apply_profile_defaults', 'true')).lower() in {'false', '0', 'no'}:
            return queryset
        if any(params.get(key) for key in ['sector', 'country', 'region']):
            return queryset

        profile = FirmProfile.objects.filter(is_default=True).first()
        if not profile:
            return queryset
        if profile.target_sectors:
            queryset = queryset.filter(sector__in=profile.target_sectors)
        if profile.geographies:
            queryset = queryset.filter(country__in=profile.geographies)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return OpportunityListSerializer
        return OpportunityDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
    def create_proposal(self, request, pk=None):
        opportunity = self.get_object()

        from apps.proposals.models import Proposal
        from apps.proposals.views import ensure_default_sections

        existing = opportunity.proposals.order_by('-updated_at').first()
        if existing:
            ensure_default_sections(existing)
            return Response({
                'proposal_id': existing.id,
                'proposal_url': f'/proposals/{existing.id}',
                'status': existing.status,
                'created': False,
            })

        proposal = Proposal.objects.create(
            opportunity=opportunity,
            title=f'Proposta Tecnica - {opportunity.title}',
            version=1,
            status='draft',
            created_by=request.user,
        )
        ensure_default_sections(proposal)
        opportunity.status = 'proposal_draft'
        opportunity.save(update_fields=['status', 'updated_at'])

        return Response({
            'proposal_id': proposal.id,
            'proposal_url': f'/proposals/{proposal.id}',
            'status': proposal.status,
            'created': True,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def analyze_tor(self, request, pk=None):
        opportunity = self.get_object()
        opportunity.ai_analysis_status = 'queued'
        opportunity.save(update_fields=['ai_analysis_status'])
        # Trigger Celery task for AI analysis
        from .tasks import analyze_tor_document
        analyze_tor_document.delay(opportunity.id)
        return Response({'ai_analysis_status': 'queued', 'task': 'analyze_tor_document triggered'})

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_tor(self, request, pk=None):
        opportunity = self.get_object()
        file_obj = request.FILES.get('tor_document')
        if not file_obj:
            return Response(
                {'detail': 'Nenhum ficheiro fornecido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .tasks import analyze_tor_document, extract_text_from_uploaded_tor

        uploaded_tor_text = extract_text_from_uploaded_tor(file_obj)
        opportunity.tor_document = file_obj
        opportunity.ai_analysis_status = 'queued'
        try:
            opportunity.save(update_fields=['tor_document', 'ai_analysis_status', 'updated_at'])
        except Exception as exc:
            logger.exception('Failed to upload ToR for opportunity %s', opportunity.id)
            return Response(
                {
                    'detail': (
                        'Upload do ToR indisponivel. A oportunidade foi mantida sem documento; '
                        'verifique a configuracao de storage.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        # Auto-trigger AI analysis after upload
        analyze_tor_document.delay(opportunity.id, uploaded_tor_text)
        return Response({
            'detail': 'Ficheiro enviado com sucesso. Analise IA iniciada em background.',
            'ai_analysis_status': 'queued',
        })

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

    @action(detail=True, methods=['get', 'post'])
    def score(self, request, pk=None):
        opportunity = self.get_object()
        refresh = request.method == 'POST' or str(request.query_params.get('refresh', '')).lower() == 'true'

        current_score = opportunity.scores.filter(is_current=True).first()
        if refresh or current_score is None:
            current_score = score_opportunity(opportunity)

        serializer = OpportunityScoreSerializer(current_score)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def suggestions(self, request, pk=None):
        from apps.partners.matching import build_opportunity_suggestions

        opportunity = self.get_object()
        try:
            limit = max(1, min(int(request.query_params.get('limit', 5)), 20))
        except (TypeError, ValueError):
            limit = 5
        return Response(build_opportunity_suggestions(opportunity, limit=limit))


class FirmProfileViewSet(viewsets.ModelViewSet):
    queryset = FirmProfile.objects.all()
    serializer_class = FirmProfileSerializer
    permission_classes = [IsConsultantOrManager]

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        profile = FirmProfile.objects.filter(is_default=True).first()
        if profile is None:
            return Response({'detail': 'Nenhum perfil configurado.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class SavedFilterViewSet(viewsets.ModelViewSet):
    serializer_class = SavedFilterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['view_type', 'is_shared']
    search_fields = ['name']
    ordering_fields = ['name', 'updated_at', 'created_at']
    ordering = ['view_type', 'name']

    def get_queryset(self):
        user = self.request.user
        return SavedFilter.objects.filter(owner=user) | SavedFilter.objects.filter(is_shared=True)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.owner_id != self.request.user.id:
            raise PermissionDenied('Apenas o owner pode alterar este filtro.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.owner_id != self.request.user.id:
            raise PermissionDenied('Apenas o owner pode apagar este filtro.')
        instance.delete()
