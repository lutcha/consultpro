from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet, AcceptInvitationView, SelfSignupView, VerifyEmailView

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('accept-invitation/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('signup/', SelfSignupView.as_view(), name='self-signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('', include(router.urls)),
]
