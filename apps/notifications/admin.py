from django.contrib import admin

from .models import ActivityLog, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'type', 'read', 'created_at']
    list_filter = ['type', 'read', 'created_at']
    search_fields = ['title', 'message']
    ordering = ['-created_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['type', 'user', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['description']
    ordering = ['-created_at']
