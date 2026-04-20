from rest_framework import serializers

from apps.users.models import User
from .models import Project, ProjectTeamMember, ProjectMilestone, ProjectRisk, ProjectDeliverable


class UserMiniSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'name', 'role']

    def get_name(self, obj: User) -> str:
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class ProjectTeamMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = ProjectTeamMember
        fields = ['id', 'user', 'user_id', 'role', 'allocation_percentage', 'start_date', 'end_date']


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = '__all__'


class ProjectRiskSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='owner', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = ProjectRisk
        fields = '__all__'


class ProjectDeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDeliverable
        fields = '__all__'


class ProjectListSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    milestones_count = serializers.SerializerMethodField()
    milestones_completed = serializers.SerializerMethodField()
    days_remaining = serializers.IntegerField(read_only=True)
    budget_utilization = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'client', 'status', 'start_date', 'end_date',
            'budget_total', 'budget_currency', 'actual_cost', 'progress',
            'manager', 'manager_name', 'team_count', 'milestones_count',
            'milestones_completed', 'days_remaining', 'budget_utilization',
            'is_overdue', 'sector', 'country', 'risk_level',
            'created_at', 'updated_at',
        ]

    def get_manager_name(self, obj: Project) -> str:
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}".strip() or obj.manager.username
        return ''

    def get_team_count(self, obj: Project) -> int:
        return obj.project_team_members.count()

    def get_milestones_count(self, obj: Project) -> int:
        return obj.milestones.count()

    def get_milestones_completed(self, obj: Project) -> int:
        return obj.milestones.filter(status='completed').count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    team = ProjectTeamMemberSerializer(
        source='project_team_members', many=True, read_only=True
    )
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    risks = ProjectRiskSerializer(many=True, read_only=True)
    deliverables = ProjectDeliverableSerializer(many=True, read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    budget_utilization = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    proposal_id = serializers.PrimaryKeyRelatedField(
        source='proposal', read_only=True
    )

    class Meta:
        model = Project
        fields = '__all__'
