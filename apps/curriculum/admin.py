from django.contrib import admin
from .models import Curriculum, CVTemplate, TemplateMatch, CVSuggestion, CVOpportunityMatch


@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_name', 'file_type', 'status', 'analysis_score', 'created_at')
    list_filter = ('file_type', 'status', 'created_at')
    search_fields = ('user__email', 'file_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'is_active', 'created_at')
    list_filter = ('organization', 'is_active')
    search_fields = ('name', 'organization_name')


@admin.register(TemplateMatch)
class TemplateMatchAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'template', 'match_score', 'created_at')
    list_filter = ('match_score', 'created_at')
    search_fields = ('curriculum__user__email',)


@admin.register(CVSuggestion)
class CVSuggestionAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'type', 'priority', 'fixed', 'created_at')
    list_filter = ('type', 'priority', 'fixed', 'created_at')
    search_fields = ('curriculum__user__email', 'message')


@admin.register(CVOpportunityMatch)
class CVOpportunityMatchAdmin(admin.ModelAdmin):
    list_display = ('curriculum', 'opportunity', 'overall_score', 'created_at')
    list_filter = ('overall_score', 'created_at')
    search_fields = ('curriculum__user__email', 'opportunity__title')
