from rest_framework import serializers

from apps.users.models import User, UserInvitation

from .models import (
    Tenant,
    TenantIntelligenceProfile,
    TenantMembership,
    TenantOnboardingSnapshot,
    TenantProfile,
    TenantStrategy,
)


class TenantMembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = TenantMembership
        fields = ['id', 'tenant', 'user', 'user_email', 'user_name', 'role', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email


class TenantSerializer(serializers.ModelSerializer):
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'status', 'plan', 'organization_type',
            'size', 'maturity_level', 'primary_country', 'default_language',
            'settings', 'current_user_role', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_user_role']

    def get_current_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return ''
        membership = obj.memberships.filter(user=request.user, status='active').first()
        return membership.role if membership else ''


class TenantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProfile
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class TenantStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantStrategy
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class TenantIntelligenceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantIntelligenceProfile
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at', 'last_refined_at']


class TenantOnboardingSnapshotSerializer(serializers.ModelSerializer):
    submitted_by_email = serializers.EmailField(source='submitted_by.email', read_only=True)

    class Meta:
        model = TenantOnboardingSnapshot
        fields = [
            'id', 'tenant', 'submitted_by', 'submitted_by_email', 'responses',
            'derived_profile', 'derived_strategy', 'derived_intelligence_profile',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'submitted_by', 'created_at']


class TenantOnboardingSubmitSerializer(serializers.Serializer):
    responses = serializers.JSONField()

    SECTION_KEYS = {
        'organization',
        'capabilities',
        'markets',
        'opportunity_preferences',
        'go_no_go_preferences',
        'ai_positioning',
    }

    def validate_responses(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('responses must be an object.')

        section_names = self.SECTION_KEYS.intersection(value.keys())
        if not section_names:
            return value

        flattened = {}
        for section_name in section_names:
            section = value.get(section_name) or {}
            if not isinstance(section, dict):
                raise serializers.ValidationError(f'{section_name} must be an object.')
            flattened.update(section)

        passthrough = {
            key: item
            for key, item in value.items()
            if key not in self.SECTION_KEYS
        }
        return {**flattened, **passthrough, '_raw_onboarding_responses': value}


class TenantInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=TenantMembership.ROLE_CHOICES, default='consultant')
    platform_role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)


class TenantInvitationResultSerializer(serializers.ModelSerializer):
    tenant_id = serializers.UUIDField(source='tenant.id', read_only=True)

    class Meta:
        model = UserInvitation
        fields = ['id', 'tenant_id', 'token', 'email', 'role', 'expires_at', 'is_used', 'accepted_at', 'created_at']
