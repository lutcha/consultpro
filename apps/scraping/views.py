from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.scraping.filters import ScrapedOpportunityFilter
from apps.scraping.services.readiness import filter_ready_to_import, get_import_readiness
from apps.scraping.services.source_health import get_sources_health


class _LargePage(PageNumberPagination):
    page_size = 200
    max_page_size = 500
    page_size_query_param = 'page_size'


class _MediumPage(PageNumberPagination):
    page_size = 100
    max_page_size = 500
    page_size_query_param = 'page_size'
from .models import (
    ScrapingSource,
    ScrapedOpportunity,
    ScrapingJob,
    ScrapingAlert,
)
from .serializers import (
    ScrapingSourceListSerializer,
    ScrapingSourceDetailSerializer,
    ScrapedOpportunityListSerializer,
    ScrapedOpportunityDetailSerializer,
    ScrapingJobListSerializer,
    ScrapingJobDetailSerializer,
    ScrapingAlertListSerializer,
    ScrapingAlertDetailSerializer,
)


class ScrapingSourceViewSet(viewsets.ModelViewSet):
    queryset = ScrapingSource.objects.all()
    permission_classes = [IsConsultantOrManager]
    pagination_class = _LargePage
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'source_type']
    search_fields = ['name', 'organization']
    ordering_fields = ['name', 'last_scraped_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScrapingSourceListSerializer
        return ScrapingSourceDetailSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """Manually trigger scraping for this source"""
        source = self.get_object()
        
        from .tasks import run_scraping_source
        run_scraping_source.delay(
            source.id,
            executed_by='manual',
            user_id=request.user.id
        )
        
        return Response({'status': 'scraping started'})

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """Toggle source status (active/paused)"""
        source = self.get_object()
        if source.status == 'active':
            source.status = 'paused'
        elif source.status == 'paused':
            source.status = 'active'
        source.save()
        return Response({'status': source.get_status_display()})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get scraping statistics"""
        from django.db.models import Avg
        total_sources = ScrapingSource.objects.count()
        active_sources = ScrapingSource.objects.filter(status='active').count()
        total_opportunities = ScrapedOpportunity.objects.count()
        imported_opportunities = ScrapedOpportunity.objects.filter(status='imported').count()
        new_opportunities = ScrapedOpportunity.objects.filter(status='new').count()
        cv_eligible = ScrapedOpportunity.objects.filter(cv_eligible=True, status='new').count()
        ready_to_import = filter_ready_to_import(ScrapedOpportunity.objects.all()).count()
        
        avg_quality = ScrapedOpportunity.objects.aggregate(
            avg=Avg('data_quality_score')
        )['avg'] or 0
        
        terminal_jobs = ScrapingJob.objects.filter(status__in=['completed', 'failed'])
        terminal_count = terminal_jobs.count()
        if terminal_count:
            completed_count = terminal_jobs.filter(status='completed').count()
            avg_success_rate = int((completed_count / terminal_count) * 100)
        else:
            avg_success_rate = int(
                ScrapingSource.objects.aggregate(avg=Avg('success_rate'))['avg'] or 0
            )
        
        return Response({
            'total_sources': total_sources,
            'active_sources': active_sources,
            'total_opportunities': total_opportunities,
            'imported_opportunities': imported_opportunities,
            'new_opportunities': new_opportunities,
            'cv_eligible_new': cv_eligible,
            'ready_to_import': ready_to_import,
            'avg_quality_score': round(avg_quality, 2),
            'success_rate': avg_success_rate,
        })

    @action(detail=False, methods=['get'])
    def health(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        status_filter = request.query_params.get('health_status')
        data = get_sources_health(queryset)
        if status_filter:
            data = [item for item in data if item['health_status'] == status_filter]
        return Response({
            'count': len(data),
            'results': data,
        })


class ScrapedOpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScrapedOpportunity.objects.all()
    permission_classes = [IsConsultantOrManager]
    pagination_class = _MediumPage
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ScrapedOpportunityFilter
    search_fields = ['title', 'organization', 'client', 'external_id']
    ordering_fields = ['deadline', 'scraped_at', 'value', 'data_quality_score']
    ordering = ['-data_quality_score', 'deadline', '-scraped_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('ready_to_import') in ('1', 'true', 'yes'):
            queryset = filter_ready_to_import(queryset)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return ScrapedOpportunityListSerializer
        return ScrapedOpportunityDetailSerializer

    @action(detail=True, methods=['post'])
    def import_opportunity(self, request, pk=None):
        """Import a scraped opportunity to the internal system"""
        scraped_opp = self.get_object()

        from .services.opportunity_importer import import_scraped_opportunity

        return Response(import_scraped_opportunity(scraped_opp, request.user))

    @action(detail=False, methods=['post'])
    def import_ready(self, request):
        """Import ready scraped opportunities and explain any records skipped."""
        from .services.opportunity_importer import import_scraped_opportunity

        ids = request.data.get('ids') or []
        limit = int(request.data.get('limit') or 50)
        max_scan = int(request.data.get('max_scan') or 500)
        queryset = self.get_queryset().filter(
            status='new',
            imported_opportunity__isnull=True,
        )
        if ids:
            queryset = queryset.filter(pk__in=ids).order_by('deadline', '-data_quality_score', '-scraped_at')
        else:
            queryset = queryset.order_by('deadline', '-data_quality_score', '-scraped_at')[:max_scan]

        imported = []
        skipped = []
        failed = []
        for scraped_opp in queryset:
            readiness = get_import_readiness(scraped_opp)
            if not readiness['ready']:
                skipped.append({
                    'id': scraped_opp.id,
                    'title': scraped_opp.title,
                    'reasons': readiness['reasons'],
                })
                continue

            if len(imported) >= limit:
                skipped.append({
                    'id': scraped_opp.id,
                    'title': scraped_opp.title,
                    'reasons': ['import_limit_reached'],
                })
                continue

            try:
                result = import_scraped_opportunity(scraped_opp, request.user)
                imported.append({
                    'id': scraped_opp.id,
                    'title': scraped_opp.title,
                    **result,
                })
            except Exception as exc:
                failed.append({
                    'id': scraped_opp.id,
                    'title': scraped_opp.title,
                    'reason': str(exc)[:300],
                })

        return Response({
            'status': 'completed',
            'imported_count': len(imported),
            'skipped_count': len(skipped),
            'failed_count': len(failed),
            'processed_count': len(imported) + len(skipped) + len(failed),
            'imported': imported,
            'skipped': skipped,
            'failed': failed,
        })

    @action(detail=True, methods=['post'])
    def ignore(self, request, pk=None):
        """Mark a scraped opportunity as ignored"""
        scraped_opp = self.get_object()
        scraped_opp.status = 'ignored'
        scraped_opp.save()
        return Response({'status': 'ignored'})


class ScrapingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScrapingJob.objects.all()
    permission_classes = [IsManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['source', 'status']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScrapingJobListSerializer
        return ScrapingJobDetailSerializer


class ScrapingAlertViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'read']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScrapingAlertListSerializer
        return ScrapingAlertDetailSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ScrapingAlert.objects.filter(user=self.request.user)
        return ScrapingAlert.objects.none()

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark alert as read"""
        alert = self.get_object()
        alert.read = True
        alert.save()
        return Response({'status': 'marked as read'})
