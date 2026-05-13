from django.contrib import admin

from .models import ActivityLog, Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['title', 'message']
    ordering = ['-created_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'email_on_new_opportunity',
        'email_on_proposal_status',
        'email_on_scrape_complete',
        'updated_at',
    ]
    list_filter = [
        'email_on_new_opportunity',
        'email_on_proposal_status',
        'email_on_scrape_complete',
    ]
    search_fields = ['user__email', 'user__username']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['type', 'user', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['description']
    ordering = ['-created_at']
