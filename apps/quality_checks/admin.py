from django.contrib import admin

from .models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck


@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = ['id', 'proposal', 'overall_score', 'status', 'can_submit', 'created_at']


@admin.register(QCCheckCategory)
class QCCheckCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'quality_check', 'category', 'score', 'status']


@admin.register(QCItem)
class QCItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'description', 'status', 'section']


@admin.register(QCSuggestion)
class QCSuggestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'quality_check', 'action', 'target_section', 'applied', 'ignored']
