from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.users.models import User, Certification, ConsultantProfile
from apps.users.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    MeSerializer,
    ConsultantProfileSerializer,
)
from apps.notifications.models import NotificationPreference
from apps.notifications.serializers import NotificationPreferenceSerializer


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
    filterset_fields = ['role', 'availability']
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
        elif self.action in ['me', 'notification_preferences', 'change_password']:
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

    @action(detail=False, methods=['get'])
    def consultants(self, request):
        """List all users with consultant role."""
        consultants = User.objects.filter(role='consultant')
        serializer = UserListSerializer(consultants, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='me/notification-preferences',
    )
    def notification_preferences(self, request):
        preferences, _ = NotificationPreference.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        url_path='me/change-password',
    )
    def change_password(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        if not request.user.check_password(current_password):
            return Response(
                {'current_password': ['Password actual invalida.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(new_password, request.user)
        except DjangoValidationError as exc:
            return Response(
                {'new_password': list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        return Response({'status': 'password changed'})

    @action(detail=True, methods=['get', 'put', 'patch'])
    def consultant_profile(self, request, pk=None):
        user = self.get_object()
        profile, created = ConsultantProfile.objects.get_or_create(user=user)
        if request.method == 'GET':
            serializer = ConsultantProfileSerializer(profile)
            return Response(serializer.data)
        serializer = ConsultantProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
