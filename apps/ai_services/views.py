from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import AIServiceFactory, MockAIService


class AIProviderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AIServiceFactory.get_service()
        registry = {**AIServiceFactory.PROVIDER_REGISTRY, **AIServiceFactory.NATIVE_PROVIDERS}
        providers = []

        for name, config in registry.items():
            api_key_setting = config['api_key_setting']
            model_setting = config['model_setting']
            providers.append({
                'id': name,
                'model': getattr(settings, model_setting, '') or config['default_model'],
                'api_key_configured': bool(getattr(settings, api_key_setting, '')),
            })

        providers.append({
            'id': 'mock',
            'model': 'mock',
            'api_key_configured': True,
        })

        return Response({
            'active_provider': getattr(settings, 'AI_PROVIDER', 'openai'),
            'active_model': getattr(service, 'model', 'mock'),
            'is_mock': isinstance(service, MockAIService),
            'always_mock': getattr(settings, 'AI_ALWAYS_MOCK', False),
            'providers': providers,
        })
