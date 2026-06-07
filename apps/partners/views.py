from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.core.permissions import IsConsultantOrManager
from apps.tenants.utils import get_request_tenant, scope_queryset_to_request_tenant

from .models import PartnerProfile
from .serializers import PartnerProfileSerializer


class PartnerProfileViewSet(viewsets.ModelViewSet):
    queryset = PartnerProfile.objects.all()
    serializer_class = PartnerProfileSerializer
    permission_classes = [IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'notes']
    ordering_fields = ['trust_score', 'name', 'updated_at']
    ordering = ['-trust_score', 'name']

    def get_queryset(self):
        return scope_queryset_to_request_tenant(super().get_queryset(), self.request)

    def perform_create(self, serializer):
        tenant = get_request_tenant(self.request)
        if tenant:
            serializer.save(tenant=tenant)
        else:
            serializer.save()
