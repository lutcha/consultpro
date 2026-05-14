from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from apps.core.permissions import IsConsultantOrManager
from .models import (
    Curriculum,
    CVTemplate,
    TemplateMatch,
    CVSuggestion,
    CVOpportunityMatch,
)
from .serializers import (
    CurriculumListSerializer,
    CurriculumDetailSerializer,
    CVTemplateSerializer,
    TemplateMatchSerializer,
    CVSuggestionSerializer,
    CVOpportunityMatchSerializer,
)


class CurriculumViewSet(viewsets.ModelViewSet):
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'file_type']
    search_fields = ['file_name']
    ordering_fields = ['created_at', 'analysis_score']
    ordering = ['-created_at']
    parser_classes = (MultiPartParser, FormParser)
    # Restrict pk to integers so /templates/ is not matched as a pk
    lookup_value_regex = r'[0-9]+'

    def get_queryset(self):
        return Curriculum.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return CurriculumListSerializer
        return CurriculumDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Run CV analysis synchronously and return the updated CV."""
        curriculum = self.get_object()
        from .tasks import analyze_cv_with_ai
        analyze_cv_with_ai(curriculum.id)
        curriculum.refresh_from_db()
        serializer = CurriculumDetailSerializer(curriculum, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def extracted(self, request, pk=None):
        """Get extracted CV data"""
        curriculum = self.get_object()
        return Response({'extracted_data': curriculum.extracted_data})

    @action(detail=True, methods=['get'])
    def suggestions(self, request, pk=None):
        """Get CV improvement suggestions"""
        curriculum = self.get_object()
        suggestions = curriculum.suggestions.all()
        serializer = CVSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path=r'suggestions/(?P<sugg_id>[^/.]+)/apply')
    def apply_suggestion(self, request, pk=None, sugg_id=None):
        """Apply a CV suggestion"""
        try:
            suggestion = CVSuggestion.objects.get(id=sugg_id, curriculum_id=pk)
            suggestion.fixed = True
            suggestion.save()
            return Response({'status': 'suggestion applied'})
        except CVSuggestion.DoesNotExist:
            return Response({'error': 'Suggestion not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path=r'match-template/(?P<template_id>[^/.]+)')
    def match_template(self, request, pk=None, template_id=None):
        """Match CV against a specific template"""
        try:
            match = TemplateMatch.objects.get(curriculum_id=pk, template_id=template_id)
            serializer = TemplateMatchSerializer(match)
            return Response(serializer.data)
        except TemplateMatch.DoesNotExist:
            return Response({'error': 'Template match not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path=r'match-opportunity/(?P<opp_id>[^/.]+)')
    def match_opportunity(self, request, pk=None, opp_id=None):
        """Match CV against a specific opportunity"""
        from django.shortcuts import get_object_or_404
        from apps.opportunities.models import Opportunity
        from .matching import match_cv_to_opportunity

        curriculum = self.get_object()
        opportunity = get_object_or_404(Opportunity, id=opp_id)
        match = match_cv_to_opportunity(curriculum, opportunity)
        serializer = CVOpportunityMatchSerializer(match)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path=r'adapt/(?P<template_id>[^/.]+)')
    def adapt(self, request, pk=None, template_id=None):
        """Adapt CV for a specific template"""
        from django.shortcuts import get_object_or_404
        curriculum = self.get_object()
        template = get_object_or_404(CVTemplate, id=template_id, is_active=True)
        output_format = request.data.get('format', 'docx')
        
        # Get or create template match
        match, created = TemplateMatch.objects.get_or_create(
            curriculum=curriculum,
            template=template,
            defaults={
                'match_score': 0,
                'missing_sections': [],
                'recommendations': [],
            }
        )
        
        # Trigger async generation if Celery is available
        try:
            from .tasks import generate_cv_for_template
            generate_cv_for_template.delay(curriculum.id, template.id, output_format)
            return Response({
                'status': 'adaptation started',
                'match_id': match.id,
                'format': output_format,
            })
        except Exception:
            return Response({
                'status': 'adaptation queued (celery not available)',
                'match_id': match.id,
                'format': output_format,
            })

    @action(detail=True, methods=['get'], url_path=r'download-adapted/(?P<template_id>[^/.]+)')
    def download_adapted(self, request, pk=None, template_id=None):
        """Download the adapted CV for a specific template"""
        from django.shortcuts import get_object_or_404
        from django.http import FileResponse
        curriculum = self.get_object()
        template = get_object_or_404(CVTemplate, id=template_id, is_active=True)
        
        try:
            match = TemplateMatch.objects.get(curriculum=curriculum, template=template)
        except TemplateMatch.DoesNotExist:
            return Response(
                {'error': 'No adaptation found for this template'},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if match.generated_file:
            return FileResponse(
                match.generated_file.open(),
                as_attachment=True,
                filename=match.generated_file.name.split('/')[-1],
            )
        
        return Response(
            {'error': 'No generated file available. Run adapt first.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class CVTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = CVTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['organization']
    search_fields = ['name', 'organization_name']
    ordering = ['organization', 'name']

    def get_queryset(self):
        return CVTemplate.objects.filter(is_active=True)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download template file"""
        template = self.get_object()
        if template.file_template:
            from django.http import FileResponse
            return FileResponse(
                template.file_template.open(),
                as_attachment=True,
                filename=template.file_template.name.split('/')[-1]
            )
        return Response({'error': 'No file available'}, status=status.HTTP_404_NOT_FOUND)


class TemplateMatchViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['curriculum', 'template']
    ordering_fields = ['match_score']
    ordering = ['-match_score']
    serializer_class = TemplateMatchSerializer

    def get_queryset(self):
        return TemplateMatch.objects.filter(curriculum__user=self.request.user)


class CVOpportunityMatchViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['curriculum', 'opportunity']
    ordering_fields = ['overall_score']
    ordering = ['-overall_score']
    serializer_class = CVOpportunityMatchSerializer

    def get_queryset(self):
        return CVOpportunityMatch.objects.filter(curriculum__user=self.request.user)
