from rest_framework.routers import DefaultRouter

from .views import QualityCheckViewSet

router = DefaultRouter()
router.register(r'', QualityCheckViewSet, basename='quality-check')

urlpatterns = router.urls
