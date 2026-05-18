from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.core.permissions import IsConsultantOrManager

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
