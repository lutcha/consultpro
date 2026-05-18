from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PartnerProfileViewSet

router = DefaultRouter()
router.register(r'', PartnerProfileViewSet, basename='partner')

urlpatterns = [
    path('', include(router.urls)),
]
