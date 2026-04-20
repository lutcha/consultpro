from rest_framework import serializers
from apps.users.models import User, Certification


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = '__all__'


class UserListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'name', 'role',
            'avatar', 'availability', 'skills',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class UserDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    certifications = CertificationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'name',
            'role', 'avatar', 'skills', 'languages', 'availability', 'bio',
            'phone', 'location', 'years_experience', 'created_at', 'updated_at',
            'certifications',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class MeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    certifications = CertificationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'name',
            'role', 'avatar', 'skills', 'languages', 'availability', 'bio',
            'phone', 'location', 'years_experience', 'created_at', 'updated_at',
            'certifications',
        ]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
