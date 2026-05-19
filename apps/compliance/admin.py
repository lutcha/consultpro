from django.contrib import admin

from .models import ComplianceMatrix, ComplianceMatrixRow


class ComplianceMatrixRowInline(admin.TabularInline):
    model = ComplianceMatrixRow
    extra = 0
    fields = ['order', 'requirement_key', 'priority', 'status', 'proposal_section', 'human_override']
    readonly_fields = ['requirement_key']


@admin.register(ComplianceMatrix)
class ComplianceMatrixAdmin(admin.ModelAdmin):
    list_display = ['opportunity', 'status', 'confidence_score', 'human_override_count', 'updated_at']
    list_filter = ['status', 'generation_version']
    search_fields = ['opportunity__title', 'opportunity__client']
    inlines = [ComplianceMatrixRowInline]


@admin.register(ComplianceMatrixRow)
class ComplianceMatrixRowAdmin(admin.ModelAdmin):
    list_display = ['matrix', 'requirement_key', 'priority', 'status', 'human_override']
    list_filter = ['priority', 'status', 'human_override', 'source_type']
    search_fields = ['requirement_text', 'source_reference']
