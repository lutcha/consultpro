from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import IssueTreeNodeViewSet, IssueTreeSnapshotViewSet

router = DefaultRouter()
router.register(r'nodes', IssueTreeNodeViewSet, basename='issue-tree-node')
router.register(r'snapshots', IssueTreeSnapshotViewSet, basename='issue-tree-snapshot')

urlpatterns = [
    path('', include(router.urls)),
]
