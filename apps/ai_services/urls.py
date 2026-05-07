from django.urls import path

from .views import AIProviderStatusAPIView


urlpatterns = [
    path('providers/status/', AIProviderStatusAPIView.as_view(), name='ai-provider-status'),
]
