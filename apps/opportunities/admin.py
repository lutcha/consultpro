from django.contrib import admin

from .models import Opportunity, Requirement, Risk


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


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ['opportunity', 'severity', 'identified_by_ai']
    list_filter = ['severity', 'identified_by_ai']
    search_fields = ['description', 'mitigation', 'opportunity__title']
