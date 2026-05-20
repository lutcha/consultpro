from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, AcceptInvitationView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('', include(router.urls)),
]
