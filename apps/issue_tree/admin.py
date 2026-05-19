from django.contrib import admin

from .models import IssueTreeNode, IssueTreeSnapshot


@admin.register(IssueTreeNode)
class IssueTreeNodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'proposal', 'parent', 'node_type', 'title', 'status', 'order']
    list_filter = ['node_type', 'status', 'proposal']
    search_fields = ['title', 'hypothesis', 'source_key']
    autocomplete_fields = ['proposal', 'parent', 'assigned_to', 'created_by']


@admin.register(IssueTreeSnapshot)
class IssueTreeSnapshotAdmin(admin.ModelAdmin):
    list_display = ['id', 'proposal', 'version', 'label', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['proposal__title', 'label']
    autocomplete_fields = ['proposal', 'created_by']
