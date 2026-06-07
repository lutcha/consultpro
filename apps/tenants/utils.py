def get_request_tenant(request):
    tenant = getattr(request, 'tenant', None)
    if tenant is not None:
        return tenant
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        from .services import get_active_tenant_for_user

        tenant = get_active_tenant_for_user(user, request)
        request.tenant = tenant
        return tenant
    return None


def scope_queryset_to_request_tenant(queryset, request):
    tenant = get_request_tenant(request)
    if tenant is not None and hasattr(queryset.model, 'tenant_id'):
        return queryset.filter(tenant=tenant)
    return queryset


def save_with_request_tenant(serializer, request, **kwargs):
    tenant = get_request_tenant(request)
    if tenant is not None and hasattr(serializer.Meta.model, 'tenant'):
        kwargs.setdefault('tenant', tenant)
    return serializer.save(**kwargs)
