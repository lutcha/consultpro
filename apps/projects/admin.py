from django.contrib import admin

from .models import Project, ProjectTeamMember, ProjectMilestone, ProjectRisk, ProjectDeliverable


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client', 'status', 'progress', 'start_date', 'end_date', 'manager']
    list_filter = ['status', 'sector', 'country', 'risk_level']
    search_fields = ['title', 'client', 'description']
    date_hierarchy = 'created_at'


@admin.register(ProjectTeamMember)
class ProjectTeamMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'allocation_percentage']
    list_filter = ['role']


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'due_date', 'status']
    list_filter = ['status']


@admin.register(ProjectRisk)
class ProjectRiskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'severity', 'status']
    list_filter = ['severity', 'status']


@admin.register(ProjectDeliverable)
class ProjectDeliverableAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'due_date', 'status']
    list_filter = ['status']
