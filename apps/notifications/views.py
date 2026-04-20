from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permissions import IsConsultantOrManager

from .models import ActivityLog, Notification
from .serializers import ActivityLogSerializer, NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['created_at', 'read']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(read=False).count()
        return Response({'unread_count': count})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all().order_by('-created_at')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, IsConsultantOrManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
