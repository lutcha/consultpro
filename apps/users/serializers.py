from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from apps.users.models import User, Certification, ConsultantProfile, UserInvitation


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class ConsultantProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultantProfile
        fields = [
            'id', 'hourly_rate', 'daily_rate', 'currency', 'specializations',
            'education', 'linkedin_url', 'portfolio_url', 'cv_document',
            'is_available_for_hire', 'total_projects_completed',
            'total_proposals_won', 'performance_rating',
            'created_at', 'updated_at',
        ]


class UserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    consultant_profile = ConsultantProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'name', 'role',
            'avatar', 'availability', 'skills', 'languages',
            'years_experience', 'consultant_profile',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    certifications = CertificationSerializer(many=True, read_only=True)
    consultant_profile = ConsultantProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'name',
            'role', 'avatar', 'skills', 'languages', 'availability', 'bio',
            'phone', 'location', 'years_experience', 'created_at', 'updated_at',
            'certifications', 'consultant_profile',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    """Used by managers/admins to create a new platform user directly."""
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'role', 'availability', 'skills', 'languages',
            'password', 'confirm_password',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'As passwords não coincidem.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserAdminSerializer(serializers.ModelSerializer):
    """Allows managers/admins to update role, availability, and active state."""
    class Meta:
        model = User
        fields = ['role', 'availability', 'is_active']


class UserInvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserInvitation
        fields = ['id', 'token', 'email', 'role', 'invited_by_name', 'expires_at', 'is_used', 'accepted_at', 'created_at']
        read_only_fields = ['id', 'token', 'invited_by_name', 'is_used', 'accepted_at', 'created_at']

    def get_invited_by_name(self, obj):
        if obj.invited_by:
            return f"{obj.invited_by.first_name} {obj.invited_by.last_name}".strip() or obj.invited_by.email
        return None


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'As passwords não coincidem.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        try:
            invitation = UserInvitation.objects.get(token=attrs['token'])
        except UserInvitation.DoesNotExist:
            raise serializers.ValidationError({'token': 'Convite inválido.'})
        if not invitation.is_valid:
            raise serializers.ValidationError({'token': 'Convite expirado ou já utilizado.'})
        attrs['invitation'] = invitation
        return attrs


class MeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    certifications = CertificationSerializer(many=True, read_only=True)
    consultant_profile = ConsultantProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'name',
            'role', 'avatar', 'skills', 'languages', 'availability', 'bio',
            'phone', 'location', 'years_experience', 'created_at', 'updated_at',
            'certifications', 'consultant_profile',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
