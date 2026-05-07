from django.contrib import admin

from .models import AIConfiguration


@admin.register(AIConfiguration)
class AIConfigurationAdmin(admin.ModelAdmin):
    list_display = ('provider', 'model', 'updated_at')
