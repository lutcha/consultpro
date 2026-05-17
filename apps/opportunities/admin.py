from django.contrib import admin

from .models import Opportunity, OpportunityScore, Requirement, Risk


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'client',
        'sector',
        'country',
        'value',
        'currency',
        'deadline',
        'status',
        'created_at',
    ]
    list_filter = ['status', 'sector', 'country', 'evaluation_criteria']
    search_fields = ['title', 'description', 'client']
    ordering = ['-created_at']


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ['opportunity', 'category', 'priority', 'is_covered', 'extracted_by_ai']
    list_filter = ['category', 'priority', 'is_covered', 'extracted_by_ai']
    search_fields = ['description', 'opportunity__title']


@admin.register(OpportunityScore)
class OpportunityScoreAdmin(admin.ModelAdmin):
    list_display = [
        'opportunity',
        'overall_score',
        'confidence_score',
        'provider',
        'scoring_version',
        'is_current',
        'created_at',
    ]
    list_filter = ['is_current', 'provider', 'scoring_version']
    search_fields = ['opportunity__title', 'opportunity__client']
    readonly_fields = [
        'opportunity',
        'strategic_fit',
        'win_probability',
        'margin',
        'risk',
        'resource',
        'overall_score',
        'confidence_score',
        'ai_extracted_criteria',
        'evaluation_weights',
        'reasoning_trace',
        'input_snapshot',
        'provider',
        'model',
        'scoring_version',
        'is_current',
        'created_at',
    ]
    ordering = ['-created_at']


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ['opportunity', 'severity', 'identified_by_ai']
    list_filter = ['severity', 'identified_by_ai']
    search_fields = ['description', 'mitigation', 'opportunity__title']
