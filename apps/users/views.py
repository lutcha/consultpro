from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.users.models import User, Certification
from apps.users.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    MeSerializer,
)


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = MeSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering_fields = ['created_at', 'email', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        if self.action == 'me':
            return MeSerializer
        return UserListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'skills', 'availability']:
            permission_classes = [permissions.IsAuthenticated, IsConsultantOrManager]
        elif self.action == 'me':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = MeSerializer(user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = MeSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def skills(self, request, pk=None):
        user = self.get_object()
        return Response({'skills': user.skills})

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        user = self.get_object()
        return Response({'availability': user.availability})
