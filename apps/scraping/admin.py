from django.contrib import admin
from .models import ScrapingSource, ScrapedOpportunity, ScrapingJob, ScrapingAlert


@admin.register(ScrapingSource)
class ScrapingSourceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'organization', 'status', 'scrape_frequency',
        'last_scraped_at', 'success_rate'
    )
    list_filter = ('status', 'source_type', 'scrape_frequency')
    search_fields = ('name', 'organization')
    readonly_fields = ('created_at', 'updated_at', 'last_scraped_at')


@admin.register(ScrapedOpportunity)
class ScrapedOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'source', 'status', 'cv_eligible',
        'deadline', 'data_quality_score', 'scraped_at'
    )
    list_filter = ('status', 'cv_eligible', 'source', 'scraped_at', 'language')
    search_fields = ('title', 'organization', 'external_id', 'country')
    readonly_fields = ('scraped_at', 'raw_content_hash', 'ingestion_batch_id')
    date_hierarchy = 'scraped_at'


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = (
        'source', 'status', 'items_found', 'items_new',
        'items_duplicate', 'items_rejected', 'created_at'
    )
    list_filter = ('status', 'source', 'created_at')
    readonly_fields = ('started_at', 'completed_at', 'created_at', 'batch_stats')


@admin.register(ScrapingAlert)
class ScrapingAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read', 'created_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('created_at',)
