from django.http import JsonResponse
from rest_framework.exceptions import PermissionDenied

from .services import get_active_tenant_for_user


class TenantContextMiddleware:
    """
    Lightweight beta tenant context.

    Uses X-Tenant-ID or X-Tenant-Slug when supplied. If neither is supplied,
    attaches the user's first active tenant, preserving compatibility for
    single-tenant local/test flows where no membership exists yet.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        request.tenant_membership = None
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            try:
                request.tenant = get_active_tenant_for_user(user, request)
                if request.tenant:
                    request.tenant_membership = (
                        user.tenant_memberships
                        .filter(tenant=request.tenant, status='active')
                        .first()
                    )
            except PermissionDenied:
                return JsonResponse({'detail': 'Invalid tenant for current user.'}, status=403)
        return self.get_response(request)
