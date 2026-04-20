from rest_framework import serializers

from apps.users.models import User

from .models import Team


class TeamMemberSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'name', 'role']

    def get_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}"


class TeamSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), source='members', write_only=True, required=False
    )

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'members', 'member_ids', 'created_at', 'updated_at']
