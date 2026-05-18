from django.contrib import admin

from .models import PartnerProfile


@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'trust_score', 'is_active', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'notes']
    ordering = ['-trust_score', 'name']
