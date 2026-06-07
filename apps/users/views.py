from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.users.emails import EmailDeliveryError, send_invitation_email, send_welcome_email
from apps.users.models import User, Certification, ConsultantProfile, UserInvitation
from apps.users.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserAdminSerializer,
    UserInvitationSerializer,
    AcceptInvitationSerializer,
    MeSerializer,
    ConsultantProfileSerializer,
)
from apps.notifications.models import NotificationPreference
from apps.notifications.serializers import NotificationPreferenceSerializer


class AcceptInvitationView(APIView):
    """Public endpoint: accepts an invitation token, creates the user account."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invitation = data['invitation']

        username = invitation.email.split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        user = User.objects.create_user(
            email=invitation.email,
            username=username,
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=invitation.role,
            password=data['password'],
            is_active=True,
        )

        if invitation.tenant_id:
            from apps.tenants.models import TenantMembership
            from apps.tenants.services import ensure_tenant_context_records

            TenantMembership.objects.update_or_create(
                tenant=invitation.tenant,
                user=user,
                defaults={'role': invitation.tenant_role, 'status': 'active'},
            )
            ensure_tenant_context_records(invitation.tenant)

        invitation.is_used = True
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=['is_used', 'accepted_at'])

        try:
            send_welcome_email(user)
        except EmailDeliveryError:
            pass
        return Response(
            {'detail': 'Conta criada com sucesso. Podes agora iniciar sessão.'},
            status=status.HTTP_201_CREATED,
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
    filterset_fields = ['role', 'availability']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering_fields = ['created_at', 'email', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'admin_update':
            return UserAdminSerializer
        if self.action in ('retrieve', 'update', 'partial_update'):
            return UserDetailSerializer
        if self.action == 'me':
            return MeSerializer
        if self.action in ('invite', 'invitations'):
            return UserInvitationSerializer
        return UserListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'skills', 'availability', 'consultants']:
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

    @action(detail=True, methods=['patch'], url_path='admin-update')
    def admin_update(self, request, pk=None):
        """Allows managers/admins to change role, availability, and active state."""
        user = self.get_object()
        serializer = UserAdminSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserListSerializer(user).data)

    @action(detail=False, methods=['post'], url_path='invite')
    def invite(self, request):
        """Send an email invitation to a new platform user."""
        serializer = UserInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        role = serializer.validated_data.get('role', 'consultant')

        if User.objects.filter(email=email).exists():
            return Response(
                {'email': 'Já existe um utilizador com este email.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation = UserInvitation.create_for(email=email, role=role, invited_by=request.user)
        try:
            send_invitation_email(invitation)
        except EmailDeliveryError as exc:
            invitation.delete()
            return Response(
                {'detail': f'Convite nao enviado: falhou o envio do email ({exc}).'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(UserInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='invitations')
    def invitations(self, request):
        """List all pending invitations (managers/admins only)."""
        qs = UserInvitation.objects.select_related('invited_by').order_by('-created_at')
        serializer = UserInvitationSerializer(qs, many=True)
        return Response(serializer.data)
