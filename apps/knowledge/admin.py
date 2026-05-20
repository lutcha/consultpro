from django.contrib import admin
from django.contrib import messages

from .models import KnowledgeAsset, KnowledgeIndexRun
from .tasks import index_knowledge_assets_task


@admin.register(KnowledgeAsset)
class KnowledgeAssetAdmin(admin.ModelAdmin):
    list_display = ['id', 'asset_type', 'title', 'country', 'sector', 'status', 'updated_at']
    list_filter = ['asset_type', 'status', 'country', 'sector']
    search_fields = ['title', 'summary', 'content', 'source_model', 'source_id']
    autocomplete_fields = ['created_by']
    actions = ['queue_full_reindex']

    @admin.action(description='Queue full Knowledge reindex')
    def queue_full_reindex(self, request, queryset):
        task = index_knowledge_assets_task.delay(source='all')
        self.message_user(
            request,
            f'Knowledge reindex queued for all sources. Task: {task.id}',
            level=messages.INFO,
        )


@admin.register(KnowledgeIndexRun)
class KnowledgeIndexRunAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'source',
        'status',
        'indexed_count',
        'error_count',
        'celery_task_id',
        'started_at',
        'completed_at',
    ]
    list_filter = ['source', 'status', 'started_at']
    search_fields = ['celery_task_id', 'errors']
    readonly_fields = [
        'source',
        'status',
        'indexed_count',
        'error_count',
        'stats',
        'errors',
        'celery_task_id',
        'triggered_by',
        'started_at',
        'completed_at',
    ]
    actions = ['queue_same_source_reindex']

    @admin.action(description='Queue reindex for selected run sources')
    def queue_same_source_reindex(self, request, queryset):
        queued = []
        for source in sorted(set(queryset.values_list('source', flat=True))):
            task = index_knowledge_assets_task.delay(source=source)
            queued.append(f'{source}:{task.id}')
        self.message_user(
            request,
            f'Knowledge reindex queued: {", ".join(queued)}',
            level=messages.INFO,
        )
