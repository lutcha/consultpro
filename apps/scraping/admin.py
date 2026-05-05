from django.contrib import admin
from .models import ScrapingSource, ScrapedOpportunity, ScrapingJob, ScrapingAlert


@admin.register(ScrapingSource)
class ScrapingSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'status', 'scrape_frequency', 'last_scraped_at')
    list_filter = ('status', 'source_type', 'scrape_frequency')
    search_fields = ('name', 'organization')
    readonly_fields = ('created_at', 'updated_at', 'last_scraped_at')


@admin.register(ScrapedOpportunity)
class ScrapedOpportunityAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'status', 'deadline', 'scraped_at')
    list_filter = ('status', 'source', 'scraped_at')
    search_fields = ('title', 'organization', 'external_id')
    readonly_fields = ('scraped_at',)


@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = ('source', 'status', 'items_found', 'items_new', 'created_at')
    list_filter = ('status', 'source', 'created_at')
    readonly_fields = ('started_at', 'completed_at', 'created_at')


@admin.register(ScrapingAlert)
class ScrapingAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read', 'created_at')
    search_fields = ('user__email', 'title')
    readonly_fields = ('created_at',)
