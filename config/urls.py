"""
URL configuration for ConsultPro project.
"""
import json
import logging

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.http import JsonResponse

from apps.users.views import MeAPIView

logger = logging.getLogger(__name__)


def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'consultpro-api'})


@csrf_exempt
@require_POST
def beta_access_request(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'invalid payload'}, status=400)

    name = str(data.get('name') or '').strip()
    org = str(data.get('organization') or '').strip()
    email = str(data.get('email') or '').strip()
    plan = str(data.get('plan') or 'beta').strip()
    message = str(data.get('message') or '').strip()

    if not name or not email:
        return JsonResponse({'error': 'name and email are required'}, status=400)

    subject = f'[ConsultPro Beta] Pedido de acesso — {org or name}'
    body = (
        f'Nome: {name}\n'
        f'Organização: {org or "—"}\n'
        f'Email: {email}\n'
        f'Plano de interesse: {plan}\n\n'
        f'Mensagem:\n{message or "—"}'
    )
    try:
        from apps.users.emails import _send
        _send(subject, body, [settings.BETA_CONTACT_EMAIL])
    except Exception:
        logger.exception('beta_access_request: email delivery failed for %s', email)

    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health-check'),
    path('api/beta-access/', beta_access_request, name='beta-access'),

    # Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/', MeAPIView.as_view(), name='auth-me'),

    # API Endpoints
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/opportunities/', include('apps.opportunities.urls')),
    path('api/proposals/', include('apps.proposals.urls')),
    path('api/quality-checks/', include('apps.quality_checks.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/curriculum/', include('apps.curriculum.urls')),
    path('api/scraping/', include('apps.scraping.urls')),
    path('api/teams/', include('apps.teams.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/dashboard/', include('apps.core.urls')),
    path('api/ai/', include('apps.ai_services.urls')),
    path('api/partners/', include('apps.partners.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/compliance/', include('apps.compliance.urls')),
    path('api/issue-tree/', include('apps.issue_tree.urls')),
    path('api/knowledge/', include('apps.knowledge.urls')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
