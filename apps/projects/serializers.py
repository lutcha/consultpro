from rest_framework import serializers

from apps.proposals.models import Proposal
from apps.users.models import User
from .models import (
    Project,
    ProjectTeamMember,
    ProjectMilestone,
    ProjectTask,
    ProjectRisk,
    ProjectDeliverable,
    ProjectPhase,
    ProjectArtifact,
)


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
        fields = [
            'id', 'project', 'user', 'user_id', 'role',
            'allocation_percentage', 'start_date', 'end_date',
        ]


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = '__all__'


class ProjectTaskSerializer(serializers.ModelSerializer):
    assignee = UserMiniSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assignee',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ProjectTask
        fields = [
            'id', 'project', 'title', 'description', 'status', 'priority',
            'due_date', 'assignee', 'assignee_id', 'created_by',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by']


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


class ProjectArtifactSerializer(serializers.ModelSerializer):
    artifact_type_display = serializers.CharField(source='get_artifact_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectArtifact
        fields = [
            'id', 'project', 'phase', 'artifact_type', 'artifact_type_display',
            'title', 'status', 'status_display', 'file', 'file_url',
            'external_url', 'notes', 'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ProjectPhaseSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = ProjectPhase
        fields = [
            'id', 'name', 'name_display', 'title', 'description', 'start_date',
            'end_date', 'is_completed', 'completion_percentage', 'order',
            'created_at', 'updated_at',
        ]


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
    tasks = ProjectTaskSerializer(many=True, read_only=True)
    risks = ProjectRiskSerializer(
        source='project_risks', many=True, read_only=True
    )
    deliverables = ProjectDeliverableSerializer(
        source='project_deliverables', many=True, read_only=True
    )
    artifacts = ProjectArtifactSerializer(many=True, read_only=True)
    phases = ProjectPhaseSerializer(many=True, read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    budget_utilization = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    proposal_id = serializers.PrimaryKeyRelatedField(
        queryset=Proposal.objects.all(),
        source='proposal',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Project
        fields = '__all__'
