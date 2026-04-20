from django.contrib import admin

from .models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalSection,
    ProposalTeamMember,
)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'version', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('title',)


@admin.register(ProposalTeamMember)
class ProposalTeamMemberAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'user', 'role', 'hours', 'hourly_rate')


@admin.register(ProposalSection)
class ProposalSectionAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'section_type', 'title', 'order', 'is_complete')
    list_filter = ('section_type', 'is_complete')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('section', 'user', 'resolved', 'created_at')
    list_filter = ('resolved',)


@admin.register(AISuggestion)
class AISuggestionAdmin(admin.ModelAdmin):
    list_display = ('section', 'action', 'applied', 'created_at')
    list_filter = ('action', 'applied')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('proposal', 'total', 'currency')


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'category', 'amount')
    list_filter = ('category',)
