from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ComplianceMatrixRowViewSet, ComplianceMatrixViewSet

router = DefaultRouter()
router.register(r'matrices', ComplianceMatrixViewSet, basename='compliance-matrix')
router.register(r'rows', ComplianceMatrixRowViewSet, basename='compliance-row')

urlpatterns = [
    path('', include(router.urls)),
]
