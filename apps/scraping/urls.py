from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScrapingSourceViewSet,
    ScrapedOpportunityViewSet,
    ScrapingJobViewSet,
    ScrapingAlertViewSet,
)

app_name = 'scraping'

router = DefaultRouter()
router.register(r'sources', ScrapingSourceViewSet, basename='scraping-source')
router.register(r'opportunities', ScrapedOpportunityViewSet, basename='scraped-opportunity')
router.register(r'jobs', ScrapingJobViewSet, basename='scraping-job')
router.register(r'alerts', ScrapingAlertViewSet, basename='scraping-alert')

urlpatterns = [
    path('', include(router.urls)),
]
