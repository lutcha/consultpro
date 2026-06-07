from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.emails import EmailDeliveryError, send_invitation_email
from apps.users.models import UserInvitation

from .models import Tenant, TenantMembership
from .serializers import (
    TenantIntelligenceProfileSerializer,
    TenantInviteSerializer,
    TenantInvitationResultSerializer,
    TenantMembershipSerializer,
    TenantOnboardingSnapshotSerializer,
    TenantOnboardingSubmitSerializer,
    TenantProfileSerializer,
    TenantSerializer,
    TenantStrategySerializer,
)
from .services import (
    apply_onboarding_to_tenant,
    assert_user_in_tenant,
    create_tenant_with_owner,
    ensure_tenant_context_records,
    user_has_tenant_role,
)
from .utils import get_request_tenant


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_value_regex = '[0-9a-f-]{36}'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Tenant.objects.all()
        return Tenant.objects.filter(memberships__user=user, memberships__status='active').distinct()

    def perform_create(self, serializer):
        tenant = create_tenant_with_owner(
            name=serializer.validated_data.pop('name'),
            owner=self.request.user,
            **serializer.validated_data,
        )
        serializer.instance = tenant

    def _require_manager(self, tenant):
        assert_user_in_tenant(self.request.user, tenant)
        if not user_has_tenant_role(self.request.user, tenant, {'owner', 'admin', 'manager'}):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied('Tenant manager role required.')

    @action(detail=False, methods=['get'])
    def current(self, request):
        tenant = get_request_tenant(request)
        if not tenant:
            return Response({'detail': 'No active tenant.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(tenant)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def members(self, request, id=None):
        tenant = self.get_object()
        assert_user_in_tenant(request.user, tenant)
        serializer = TenantMembershipSerializer(tenant.memberships.select_related('user'), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def invite(self, request, id=None):
        tenant = self.get_object()
        self._require_manager(tenant)
        serializer = TenantInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        tenant_role = serializer.validated_data['role']
        platform_role = serializer.validated_data.get('platform_role') or (
            'manager' if tenant_role in {'owner', 'admin', 'manager'} else 'consultant'
        )
        invitation = UserInvitation.create_for(
            email=email,
            role=platform_role,
            invited_by=request.user,
            tenant=tenant,
            tenant_role=tenant_role,
        )
        try:
            send_invitation_email(invitation)
        except EmailDeliveryError as exc:
            invitation.delete()
            return Response(
                {'detail': f'Convite nao enviado: falhou o envio do email ({exc}).'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        result = TenantInvitationResultSerializer(invitation)
        return Response(result.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'patch'])
    def profile(self, request, id=None):
        tenant = self.get_object()
        assert_user_in_tenant(request.user, tenant)
        ensure_tenant_context_records(tenant)
        if request.method == 'GET':
            return Response(TenantProfileSerializer(tenant.profile).data)
        self._require_manager(tenant)
        serializer = TenantProfileSerializer(tenant.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'])
    def strategy(self, request, id=None):
        tenant = self.get_object()
        assert_user_in_tenant(request.user, tenant)
        ensure_tenant_context_records(tenant)
        if request.method == 'GET':
            return Response(TenantStrategySerializer(tenant.strategy).data)
        self._require_manager(tenant)
        serializer = TenantStrategySerializer(tenant.strategy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'patch'], url_path='intelligence-profile')
    def intelligence_profile(self, request, id=None):
        tenant = self.get_object()
        assert_user_in_tenant(request.user, tenant)
        ensure_tenant_context_records(tenant)
        if request.method == 'GET':
            return Response(TenantIntelligenceProfileSerializer(tenant.intelligence_profile).data)
        self._require_manager(tenant)
        serializer = TenantIntelligenceProfileSerializer(
            tenant.intelligence_profile,
            data={**request.data, 'last_refined_at': timezone.now()},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(last_refined_at=timezone.now())
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def onboarding(self, request, id=None):
        tenant = self.get_object()
        self._require_manager(tenant)
        serializer = TenantOnboardingSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snapshot = apply_onboarding_to_tenant(
            tenant,
            serializer.validated_data['responses'],
            submitted_by=request.user,
        )
        return Response(TenantOnboardingSnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)
