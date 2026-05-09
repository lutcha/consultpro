from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    ProjectTeamMemberViewSet,
    ProjectMilestoneViewSet,
    ProjectTaskViewSet,
    ProjectRiskViewSet,
    ProjectDeliverableViewSet,
    ProjectPhaseViewSet,
    ProjectArtifactViewSet,
)

router = DefaultRouter()
router.register(r'', ProjectViewSet, basename='project')
router.register(r'team-members', ProjectTeamMemberViewSet, basename='project-team-member')
router.register(r'milestones', ProjectMilestoneViewSet, basename='project-milestone')
router.register(r'tasks', ProjectTaskViewSet, basename='project-task')
router.register(r'risks', ProjectRiskViewSet, basename='project-risk')
router.register(r'deliverables', ProjectDeliverableViewSet, basename='project-deliverable')
router.register(r'phases', ProjectPhaseViewSet, basename='project-phase')
router.register(r'artifacts', ProjectArtifactViewSet, basename='project-artifact')

urlpatterns = [
    path('', include(router.urls)),
]
