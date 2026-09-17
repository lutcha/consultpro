from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsConsultantOrManager, IsManager
from apps.users.emails import (
    EmailDeliveryError,
    send_invitation_email,
    send_self_signup_verification_email,
    send_welcome_email,
)
from apps.users.models import User, Certification, ConsultantProfile, UserInvitation
from apps.users.serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserAdminSerializer,
    UserInvitationSerializer,
    AcceptInvitationSerializer,
    SelfSignupSerializer,
    VerifyEmailSerializer,
    MeSerializer,
    ConsultantProfileSerializer,
)
from apps.users.throttles import SignupRateThrottle
from apps.users.turnstile import verify_turnstile_token
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


class SelfSignupView(APIView):
    """
    Public endpoint: self-service signup (Workstream T9).

    Does not create a usable account by itself — it creates a pending
    self-service UserInvitation and emails a confirmation link. The account
    and tenant only come into existence on SelfSignupView's counterpart,
    VerifyEmailView, once the email is confirmed. This mirrors the existing
    admin-invite pattern (invite now, account activates on accept) instead of
    introducing a second identity/activation model.
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SignupRateThrottle]

    def post(self, request):
        if not verify_turnstile_token(
            request.data.get('turnstile_token'),
            request.META.get('REMOTE_ADDR'),
        ):
            return Response(
                {'turnstile_token': 'Verificação anti-spam falhou. Tenta novamente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SelfSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data['email']

        existing_user = User.objects.filter(email=email).first()
        user = None
        created_user = False
        if existing_user and not existing_user.is_active:
            pending = UserInvitation.objects.filter(
                email=email,
                signup_source='self_service',
                is_used=False,
            ).order_by('-created_at').first()
            if pending and pending.is_valid:
                try:
                    send_self_signup_verification_email(pending)
                except EmailDeliveryError as exc:
                    return Response(
                        {'detail': f'Não foi possível reenviar o email de confirmação ({exc}).'},
                        status=status.HTTP_502_BAD_GATEWAY,
                    )
                return Response(
                    {'detail': 'Já existe um registo pendente. Reenviámos o email de confirmação.'},
                    status=status.HTTP_202_ACCEPTED,
                )

            if not pending:
                return Response(
                    {'email': 'Este email está associado a uma conta que não pode ser reativada por este fluxo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Restart an expired self-service attempt without deleting the user.
            # An inactive account with no self-service invitation belongs to a
            # different lifecycle and must never be removed here.
            UserInvitation.objects.filter(
                email=email,
                signup_source='self_service',
                is_used=False,
            ).delete()
            existing_user.set_password(data['password'])
            existing_user.save(update_fields=['password'])
            user = existing_user

        username = email.split('@')[0]
        base = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1

        if user is None:
            user = User.objects.create_user(
                email=email,
                username=username,
                password=data['password'],
                role='manager',
                is_active=False,
            )
            created_user = True
        invitation = UserInvitation.objects.create(
            email=email,
            role='manager',
            signup_source='self_service',
            organization_name=data['organization_name'],
            expires_at=timezone.now() + timedelta(hours=48),
        )

        try:
            send_self_signup_verification_email(invitation)
        except EmailDeliveryError as exc:
            if created_user:
                invitation.delete()
                user.delete()
            return Response(
                {'detail': f'Não foi possível enviar o email de confirmação ({exc}).'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {'detail': 'Confirma o teu email para ativar a conta. Enviámos um link de confirmação.'},
            status=status.HTTP_202_ACCEPTED,
        )


class VerifyEmailView(APIView):
    """Public endpoint: confirms a self-service signup and provisions the tenant."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.tenants.services import create_tenant_with_owner

        with transaction.atomic():
            invitation = UserInvitation.objects.select_for_update().get(
                token=serializer.validated_data['token'],
                signup_source='self_service',
            )
            if not invitation.is_valid:
                raise serializers.ValidationError(
                    {'token': 'Link de confirmação expirado ou já utilizado.'}
                )

            user = User.objects.select_for_update().get(
                email=invitation.email,
                is_active=False,
            )
            user.is_active = True
            user.save(update_fields=['is_active'])

            tenant = create_tenant_with_owner(
                name=invitation.organization_name,
                owner=user,
                trial_days=settings.SELF_SERVICE_TRIAL_DAYS,
            )

            invitation.is_used = True
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['is_used', 'accepted_at'])

        try:
            send_welcome_email(user)
        except EmailDeliveryError:
            pass

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'tenant_id': str(tenant.id),
            },
            status=status.HTTP_200_OK,
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
