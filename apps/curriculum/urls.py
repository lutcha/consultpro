from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CurriculumViewSet,
    CVTemplateViewSet,
    TemplateMatchViewSet,
    CVOpportunityMatchViewSet,
)

app_name = 'curriculum'

router = DefaultRouter()
router.register(r'', CurriculumViewSet, basename='curriculum')
router.register(r'templates', CVTemplateViewSet, basename='cv-template')
router.register(r'template-matches', TemplateMatchViewSet, basename='template-match')
router.register(r'opportunity-matches', CVOpportunityMatchViewSet, basename='opportunity-match')

urlpatterns = [
    path('', include(router.urls)),
]
