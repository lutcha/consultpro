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
        from django.db.models import Count, Sum, Q, Avg
        total_sources = ScrapingSource.objects.count()
        active_sources = ScrapingSource.objects.filter(status='active').count()
        total_opportunities = ScrapedOpportunity.objects.count()
        imported_opportunities = ScrapedOpportunity.objects.filter(status='imported').count()
        new_opportunities = ScrapedOpportunity.objects.filter(status='new').count()
        cv_eligible = ScrapedOpportunity.objects.filter(cv_eligible=True, status='new').count()
        
        avg_quality = ScrapedOpportunity.objects.aggregate(
            avg=Avg('data_quality_score')
        )['avg'] or 0
        
        avg_success_rate = 0
        sources_with_rate = ScrapingSource.objects.filter(success_rate__gt=0)
        if sources_with_rate.exists():
            avg_success_rate = int(sources_with_rate.aggregate(avg=Avg('success_rate'))['avg'] or 0)
        
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
        
        opportunity = Opportunity.objects.create(
            title=scraped_opp.title,
            client=scraped_opp.client or scraped_opp.organization,
            sector=scraped_opp.sector or 'Consultoria',
            country=scraped_opp.country or 'Cabo Verde',
            value=scraped_opp.value or 0,
            currency=scraped_opp.currency,
            deadline=scraped_opp.deadline or timezone.now(),
            description=scraped_opp.description,
            url_source=scraped_opp.external_url,
            ai_summary=scraped_opp.ai_summary,
            created_by=request.user,
        )
        
        scraped_opp.status = 'imported'
        scraped_opp.imported_opportunity = opportunity
        scraped_opp.imported_by = request.user
        scraped_opp.imported_at = timezone.now()
        scraped_opp.save()
        
        return Response({'opportunity_id': opportunity.id, 'status': 'imported'})

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
