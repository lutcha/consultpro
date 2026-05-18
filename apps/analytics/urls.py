from django.urls import path

from .views import AnalyticsViewSet

urlpatterns = [
    path('trends/', AnalyticsViewSet.as_view({'get': 'trends'}), name='analytics-trends'),
]
