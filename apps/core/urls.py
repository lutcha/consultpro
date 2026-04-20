from django.urls import path
from apps.core.views import DashboardViewSet

urlpatterns = [
    path('stats/', DashboardViewSet.as_view({'get': 'stats'}), name='dashboard-stats'),
    path('pipeline/', DashboardViewSet.as_view({'get': 'pipeline'}), name='dashboard-pipeline'),
    path('alerts/', DashboardViewSet.as_view({'get': 'alerts'}), name='dashboard-alerts'),
    path('activity/', DashboardViewSet.as_view({'get': 'activity'}), name='dashboard-activity'),
]
