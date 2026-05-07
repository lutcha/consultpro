from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import AIServiceFactory, MockAIService
from .models import AIConfiguration


class AIProviderStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AIServiceFactory.get_service()
        config = AIConfiguration.current()
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
            'active_provider': config.provider or getattr(settings, 'AI_PROVIDER', 'openai'),
            'active_model': getattr(service, 'model', 'mock'),
            'is_mock': isinstance(service, MockAIService),
            'always_mock': getattr(settings, 'AI_ALWAYS_MOCK', False),
            'selected_model': config.model,
            'providers': providers,
        })

    def patch(self, request):
        provider = str(request.data.get('provider', '')).lower().strip()
        model = str(request.data.get('model', '')).strip()
        valid_providers = AIServiceFactory.list_available_providers()

        if provider not in valid_providers:
            return Response(
                {'detail': f'Provider invalido. Opcoes: {", ".join(valid_providers)}'},
                status=400,
            )

        config = AIConfiguration.current()
        config.provider = provider
        config.model = model
        config.save(update_fields=['provider', 'model', 'updated_at'])
        AIServiceFactory.reset()

        return self.get(request)
