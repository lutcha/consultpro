from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FirmProfileViewSet, OpportunityViewSet, SavedFilterViewSet

router = DefaultRouter()
router.register(r'firm-profiles', FirmProfileViewSet, basename='firm-profile')
router.register(r'saved-filters', SavedFilterViewSet, basename='saved-filter')
router.register(r'', OpportunityViewSet, basename='opportunity')

urlpatterns = [
    path('', include(router.urls)),
]
