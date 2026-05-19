from django.contrib import admin

from .models import KnowledgeAsset


@admin.register(KnowledgeAsset)
class KnowledgeAssetAdmin(admin.ModelAdmin):
    list_display = ['id', 'asset_type', 'title', 'country', 'sector', 'status', 'updated_at']
    list_filter = ['asset_type', 'status', 'country', 'sector']
    search_fields = ['title', 'summary', 'content', 'source_model', 'source_id']
    autocomplete_fields = ['created_by']
