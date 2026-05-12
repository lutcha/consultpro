import json
from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe
from django.utils.timezone import now
from django.db.models import Count, Q

from .models import ScrapingSource, ScrapedOpportunity, ScrapingJob, ScrapingAlert


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pretty_json(data) -> str:
    if not data:
        return "—"
    try:
        dumped = json.dumps(data, indent=2, ensure_ascii=False)
        return mark_safe(f'<pre style="margin:0;font-size:12px;max-height:300px;overflow:auto">{dumped}</pre>')
    except Exception:
        return str(data)


def _status_badge(status, choices_map):
    colors = {
        'active': '#28a745', 'paused': '#ffc107', 'error': '#dc3545',
        'disabled': '#6c757d', 'running': '#17a2b8', 'completed': '#28a745',
        'failed': '#dc3545', 'scheduled': '#6c757d',
        'new': '#17a2b8', 'imported': '#28a745', 'ignored': '#6c757d',
        'expired': '#fd7e14', 'rejected': '#dc3545',
    }
    label = choices_map.get(status, status)
    color = colors.get(status, '#adb5bd')
    return mark_safe(
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:11px;white-space:nowrap">{label}</span>'
    )


# ── Inlines ───────────────────────────────────────────────────────────────────

class RecentJobInline(admin.TabularInline):
    model = ScrapingJob
    extra = 0
    max_num = 5
    can_delete = False
    show_change_link = True
    fields = ('status', 'items_found', 'items_new', 'items_rejected', 'started_at', 'completed_at')
    readonly_fields = fields

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')


# ── ScrapingSource ────────────────────────────────────────────────────────────

@admin.register(ScrapingSource)
class ScrapingSourceAdmin(admin.ModelAdmin):
    list_display = (
        'name_link', 'organization', 'source_status_badge', 'scraper_class',
        'scrape_frequency', 'last_scraped_at', 'stats_cell', 'ssl_robots_flags',
    )
    list_filter = ('status', 'source_type', 'scrape_frequency', 'scraper_class', 'verify_ssl')
    search_fields = ('name', 'organization', 'url')
    readonly_fields = (
        'created_at', 'updated_at', 'last_scraped_at', 'next_scrape_at',
        'new_opportunities_count', 'total_opportunities_count', 'success_rate',
        'error_message', 'scraper_config_display', 'filters_display',
    )
    ordering = ('status', 'name')
    save_on_top = True
    inlines = [RecentJobInline]

    fieldsets = (
        ('Identification', {
            'fields': ('name', 'organization', 'url', 'logo', 'source_type'),
        }),
        ('Scraper', {
            'fields': ('scraper_class', 'scraper_config', 'scraper_config_display'),
        }),
        ('Schedule & Status', {
            'fields': ('status', 'scrape_frequency', 'last_scraped_at', 'next_scrape_at'),
        }),
        ('Security', {
            'fields': ('verify_ssl', 'respect_robots_txt'),
            'classes': ('collapse',),
        }),
        ('Filters', {
            'fields': ('filters', 'filters_display'),
            'classes': ('collapse',),
        }),
        ('Statistics', {
            'fields': (
                'new_opportunities_count', 'total_opportunities_count',
                'success_rate', 'error_message',
            ),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['action_run_scrape', 'action_enable', 'action_pause', 'action_disable']

    # ── Custom columns ────────────────────────────────────────────────────────

    @admin.display(description='Source')
    def name_link(self, obj):
        return format_html('<strong>{}</strong><br><small style="color:#666">{}</small>', obj.name, obj.url)

    @admin.display(description='Status')
    def source_status_badge(self, obj):
        return _status_badge(obj.status, dict(ScrapingSource.STATUS_CHOICES))

    @admin.display(description='Stats')
    def stats_cell(self, obj):
        return format_html(
            '<span title="New">{} new</span> / '
            '<span title="Total">{} total</span> / '
            '<span title="Success rate" style="color:{}">{} %</span>',
            obj.new_opportunities_count,
            obj.total_opportunities_count,
            '#28a745' if obj.success_rate >= 80 else '#dc3545',
            obj.success_rate,
        )

    @admin.display(description='SSL / Robots')
    def ssl_robots_flags(self, obj):
        ssl = '🔒' if obj.verify_ssl else '⚠️'
        robots = '🤖' if obj.respect_robots_txt else '–'
        return format_html('<span title="SSL verified">{}</span> <span title="Robots.txt">{}</span>', ssl, robots)

    @admin.display(description='Config (read-only)')
    def scraper_config_display(self, obj):
        return _pretty_json(obj.scraper_config)

    @admin.display(description='Filters (read-only)')
    def filters_display(self, obj):
        return _pretty_json(obj.filters)

    # ── Actions ───────────────────────────────────────────────────────────────

    @admin.action(description='▶ Run scrape now')
    def action_run_scrape(self, request, queryset):
        from apps.scraping.tasks import run_scraping_source
        triggered = 0
        skipped = 0
        for source in queryset:
            if source.status in ('active', 'paused', 'error'):
                run_scraping_source.delay(
                    source.id,
                    executed_by='user',
                    user_id=request.user.id,
                )
                triggered += 1
            else:
                skipped += 1
        if triggered:
            self.message_user(request, f'Scraping queued for {triggered} source(s).', messages.SUCCESS)
        if skipped:
            self.message_user(request, f'{skipped} source(s) skipped (disabled).', messages.WARNING)

    @admin.action(description='✓ Enable selected sources')
    def action_enable(self, request, queryset):
        n = queryset.update(status='active')
        self.message_user(request, f'{n} source(s) set to active.', messages.SUCCESS)

    @admin.action(description='⏸ Pause selected sources')
    def action_pause(self, request, queryset):
        n = queryset.update(status='paused')
        self.message_user(request, f'{n} source(s) paused.', messages.WARNING)

    @admin.action(description='✗ Disable selected sources')
    def action_disable(self, request, queryset):
        n = queryset.update(status='disabled')
        self.message_user(request, f'{n} source(s) disabled.', messages.WARNING)


# ── ScrapedOpportunity ────────────────────────────────────────────────────────

@admin.register(ScrapedOpportunity)
class ScrapedOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'source', 'opp_status_badge', 'country', 'cv_eligible_icon',
        'deadline_cell', 'quality_cell', 'deep_content_status', 'scraped_at',
    )
    list_filter = (
        'status', 'cv_eligible', 'source', 'language', 'deep_content_status',
        ('scraped_at', admin.DateFieldListFilter),
        ('deadline', admin.DateFieldListFilter),
    )
    search_fields = ('title', 'organization', 'external_id', 'country', 'sector')
    readonly_fields = (
        'scraped_at', 'raw_content_hash', 'ingestion_batch_id',
        'raw_payload_display', 'ai_extracted_requirements_display',
        'sector_tags_display', 'geographic_scope_display',
    )
    date_hierarchy = 'scraped_at'
    show_full_result_count = False
    list_per_page = 50
    save_on_top = True
    actions = ['action_mark_ignored', 'action_mark_rejected', 'action_enrich_ai']

    fieldsets = (
        ('Core', {
            'fields': (
                'source', 'title', 'organization', 'client',
                'external_url', 'external_id', 'status',
            ),
        }),
        ('Classification', {
            'fields': ('sector', 'country', 'region', 'language', 'sector_tags', 'sector_tags_display'),
        }),
        ('Financials & Dates', {
            'fields': ('value', 'currency', 'deadline', 'published_at'),
        }),
        ('Eligibility', {
            'fields': ('cv_eligible', 'eligibility_data'),
            'classes': ('collapse',),
        }),
        ('AI & Quality', {
            'fields': (
                'data_quality_score', 'ai_summary',
                'ai_extracted_requirements', 'ai_extracted_requirements_display',
            ),
            'classes': ('collapse',),
        }),
        ('Deep Content', {
            'fields': ('deep_content_status', 'deep_content_url', 'deep_content_extracted_at'),
            'classes': ('collapse',),
        }),
        ('Raw / Audit', {
            'fields': (
                'raw_payload_display', 'raw_content_hash',
                'ingestion_batch_id', 'scraped_at',
            ),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def opp_status_badge(self, obj):
        return _status_badge(obj.status, dict(ScrapedOpportunity.STATUS_CHOICES))

    @admin.display(description='CV', boolean=True)
    def cv_eligible_icon(self, obj):
        return obj.cv_eligible

    @admin.display(description='Deadline')
    def deadline_cell(self, obj):
        if not obj.deadline:
            return '—'
        delta = obj.deadline - now()
        color = '#dc3545' if delta.days < 7 else ('#ffc107' if delta.days < 30 else '#28a745')
        if delta.days < 0:
            color = '#6c757d'
        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            obj.deadline.strftime('%d %b %Y'),
        )

    @admin.display(description='Quality')
    def quality_cell(self, obj):
        score = float(obj.data_quality_score or 0)
        color = '#28a745' if score >= 0.8 else ('#ffc107' if score >= 0.5 else '#dc3545')
        return format_html('<span style="color:{}">{:.0%}</span>', color, score)

    @admin.display(description='Raw payload (read-only)')
    def raw_payload_display(self, obj):
        return _pretty_json(obj.raw_payload)

    @admin.display(description='AI requirements (read-only)')
    def ai_extracted_requirements_display(self, obj):
        return _pretty_json(obj.ai_extracted_requirements)

    @admin.display(description='Sector tags (read-only)')
    def sector_tags_display(self, obj):
        return _pretty_json(obj.sector_tags)

    @admin.display(description='Geographic scope (read-only)')
    def geographic_scope_display(self, obj):
        return _pretty_json(obj.geographic_scope)

    @admin.action(description='Ignore selected opportunities')
    def action_mark_ignored(self, request, queryset):
        n = queryset.update(status='ignored')
        self.message_user(request, f'{n} opportunity/ies marked ignored.', messages.SUCCESS)

    @admin.action(description='Reject selected opportunities')
    def action_mark_rejected(self, request, queryset):
        n = queryset.update(status='rejected')
        self.message_user(request, f'{n} opportunity/ies rejected.', messages.WARNING)

    @admin.action(description='🤖 Enrich with AI (queue)')
    def action_enrich_ai(self, request, queryset):
        from apps.scraping.tasks import enrich_scraped_opportunity_with_ai
        queued = 0
        for opp in queryset.filter(status__in=('new', 'ignored')):
            enrich_scraped_opportunity_with_ai.delay(opp.id)
            queued += 1
        self.message_user(request, f'AI enrichment queued for {queued} item(s).', messages.SUCCESS)


# ── ScrapingJob ───────────────────────────────────────────────────────────────

@admin.register(ScrapingJob)
class ScrapingJobAdmin(admin.ModelAdmin):
    list_display = (
        'source', 'job_status_badge', 'items_found', 'items_new',
        'items_duplicate', 'items_rejected', 'duration_cell', 'created_at',
    )
    list_filter = ('status', 'executed_by', 'source', ('created_at', admin.DateFieldListFilter))
    readonly_fields = (
        'started_at', 'completed_at', 'created_at',
        'batch_stats_display', 'duration_cell',
    )
    search_fields = ('source__name',)
    ordering = ('-created_at',)
    list_per_page = 50

    fieldsets = (
        ('Job', {
            'fields': ('source', 'status', 'executed_by', 'triggered_by'),
        }),
        ('Results', {
            'fields': (
                'items_found', 'items_new', 'items_imported',
                'items_duplicate', 'items_rejected',
            ),
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_cell', 'created_at'),
        }),
        ('Error log', {
            'fields': ('error_log',),
            'classes': ('collapse',),
        }),
        ('Batch stats', {
            'fields': ('batch_stats_display',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Status')
    def job_status_badge(self, obj):
        return _status_badge(obj.status, dict(ScrapingJob.STATUS_CHOICES))

    @admin.display(description='Duration')
    def duration_cell(self, obj):
        if obj.started_at and obj.completed_at:
            secs = int((obj.completed_at - obj.started_at).total_seconds())
            return f'{secs // 60}m {secs % 60}s' if secs >= 60 else f'{secs}s'
        return '—'

    @admin.display(description='Batch stats (read-only)')
    def batch_stats_display(self, obj):
        return _pretty_json(obj.batch_stats)


# ── ScrapingAlert ─────────────────────────────────────────────────────────────

@admin.register(ScrapingAlert)
class ScrapingAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'read', 'created_at')
    list_filter = ('type', 'read', ('created_at', admin.DateFieldListFilter))
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected as read')
    def mark_read(self, request, queryset):
        queryset.update(read=True)

    @admin.action(description='Mark selected as unread')
    def mark_unread(self, request, queryset):
        queryset.update(read=False)
