from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.permissions import IsManager
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
    permission_classes = [IsManager]
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
            'avg_quality_score': round(avg_quality, 2),
            'success_rate': avg_success_rate,
        })


class ScrapedOpportunityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ScrapedOpportunity.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'source', 'status', 'country', 'sector',
        'cv_eligible', 'language', 'data_quality_score'
    ]
    search_fields = ['title', 'organization', 'client', 'external_id']
    ordering_fields = ['deadline', 'scraped_at', 'value', 'data_quality_score']
    ordering = ['-scraped_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ScrapedOpportunityListSerializer
        return ScrapedOpportunityDetailSerializer

    @action(detail=True, methods=['post'])
    def import_opportunity(self, request, pk=None):
        """Import a scraped opportunity to the internal system"""
        scraped_opp = self.get_object()
        
        from apps.opportunities.models import Opportunity
        from apps.opportunities.tasks import _sync_ai_requirements

        description = scraped_opp.description
        if scraped_opp.deep_content_text:
            description = (
                f"{description}\n\n--- Conteudo extraido da fonte/TdR ---\n"
                f"{scraped_opp.deep_content_text}"
            ).strip()

        if scraped_opp.imported_opportunity_id:
            return Response({
                'opportunity_id': scraped_opp.imported_opportunity_id,
                'opportunity_url': f'/opportunities/{scraped_opp.imported_opportunity_id}',
                'status': 'imported',
                'created': False,
            })

        existing = Opportunity.objects.filter(url_source=scraped_opp.external_url).first()
        if existing:
            scraped_opp.status = 'imported'
            scraped_opp.imported_opportunity = existing
            scraped_opp.imported_by = request.user
            scraped_opp.imported_at = timezone.now()
            scraped_opp.save(update_fields=['status', 'imported_opportunity', 'imported_by', 'imported_at'])
            return Response({
                'opportunity_id': existing.id,
                'opportunity_url': f'/opportunities/{existing.id}',
                'status': 'imported',
                'created': False,
            })

        ai_extraction = {
            'schema': 'scraped_opportunity_import_v1',
            'source': 'scraping',
            'scraped_opportunity_id': scraped_opp.id,
            'scraping_source_id': scraped_opp.source_id,
            'scraping_source_name': scraped_opp.source.name if scraped_opp.source_id else '',
            'external_id': scraped_opp.external_id,
            'external_url': scraped_opp.external_url,
            'deep_content_url': scraped_opp.deep_content_url,
            'deep_content_status': scraped_opp.deep_content_status,
            'deep_content_extracted_at': scraped_opp.deep_content_extracted_at.isoformat() if scraped_opp.deep_content_extracted_at else '',
            'requirements': scraped_opp.ai_extracted_requirements or [],
            'transformation_flags': scraped_opp.transformation_flags or {},
            'imported_at': timezone.now().isoformat(),
        }
        
        opportunity = Opportunity.objects.create(
            title=scraped_opp.title,
            client=scraped_opp.client or scraped_opp.organization,
            sector=scraped_opp.sector or 'Consultoria',
            country=scraped_opp.country or 'Cabo Verde',
            value=scraped_opp.value or 0,
            currency=scraped_opp.currency,
            deadline=scraped_opp.deadline or timezone.now(),
            description=description,
            url_source=scraped_opp.external_url,
            ai_summary=scraped_opp.ai_summary,
            ai_extraction=ai_extraction,
            created_by=request.user,
        )

        _sync_ai_requirements(opportunity, scraped_opp.ai_extracted_requirements or [])
        
        scraped_opp.status = 'imported'
        scraped_opp.imported_opportunity = opportunity
        scraped_opp.imported_by = request.user
        scraped_opp.imported_at = timezone.now()
        scraped_opp.save(update_fields=['status', 'imported_opportunity', 'imported_by', 'imported_at'])
        
        return Response({
            'opportunity_id': opportunity.id,
            'opportunity_url': f'/opportunities/{opportunity.id}',
            'status': 'imported',
            'created': True,
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
