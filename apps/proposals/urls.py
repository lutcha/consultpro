from rest_framework.routers import DefaultRouter

from .views import ProposalViewSet

router = DefaultRouter()
router.register(r'', ProposalViewSet, basename='proposal')

urlpatterns = router.urls
