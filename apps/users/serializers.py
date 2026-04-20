from rest_framework import serializers
from apps.users.models import User, Certification, ConsultantProfile


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
