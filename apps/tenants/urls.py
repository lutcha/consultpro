from rest_framework.routers import DefaultRouter

from .views import TenantViewSet


router = DefaultRouter()
router.register('', TenantViewSet, basename='tenant')

urlpatterns = router.urls
