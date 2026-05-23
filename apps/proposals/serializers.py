from rest_framework import serializers

from apps.users.models import User
from .models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalEvent,
    ProposalExportRequest,
    ProposalPostMortem,
    ProposalSection,
    ProposalTeamMember,
    GateAuditLog,
    PursuitGate,
)


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        fields = ['id', 'category', 'amount', 'description']


class BudgetSerializer(serializers.ModelSerializer):
    items = BudgetItemSerializer(many=True, read_only=True)
    breakdown = BudgetItemSerializer(source='items', many=True, read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'proposal', 'total', 'currency', 'items', 'breakdown']


class CommentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_id', 'section', 'text', 'resolved', 'created_at']


class AISuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AISuggestion
        fields = '__all__'


class ProposalEventSerializer(serializers.ModelSerializer):
    created_by_detail = UserMiniSerializer(source='created_by', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ProposalEvent
        fields = [
            'id',
            'proposal',
            'event_type',
            'event_type_display',
            'artifact_type',
            'title',
            'notes',
            'occurred_at',
            'external_url',
            'attachment',
            'attachment_url',
            'created_by',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.attachment.url)
        return obj.attachment.url


class ProposalPostMortemSerializer(serializers.ModelSerializer):
    created_by_detail = UserMiniSerializer(source='created_by', read_only=True)

    class Meta:
        model = ProposalPostMortem
        fields = [
            'id',
            'proposal',
            'outcome',
            'outcome_reason',
            'client_feedback',
            'lessons_learned',
            'scoring_adjustments',
            'sentiment',
            'evidence',
            'created_by',
            'created_by_detail',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'proposal', 'created_by', 'created_at', 'updated_at']


class ProposalExportRequestSerializer(serializers.ModelSerializer):
    requested_by_detail = UserMiniSerializer(source='requested_by', read_only=True)

    class Meta:
        model = ProposalExportRequest
        fields = [
            'id',
            'proposal',
            'export_type',
            'status',
            'requested_by',
            'requested_by_detail',
            'parameters',
            'executive_summary',
            'output_metadata',
            'error_message',
            'task_id',
            'execution_attempts',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'proposal',
            'status',
            'requested_by',
            'executive_summary',
            'output_metadata',
            'error_message',
            'task_id',
            'execution_attempts',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]


class GateAuditLogSerializer(serializers.ModelSerializer):
    actor_detail = UserMiniSerializer(source='actor', read_only=True)

    class Meta:
        model = GateAuditLog
        fields = [
            'id',
            'gate',
            'action',
            'actor',
            'actor_detail',
            'from_status',
            'to_status',
            'note',
            'snapshot',
            'created_at',
        ]
        read_only_fields = fields


class PursuitGateSerializer(serializers.ModelSerializer):
    approved_by_detail = UserMiniSerializer(source='approved_by', read_only=True)
    audit_logs = GateAuditLogSerializer(many=True, read_only=True)

    class Meta:
        model = PursuitGate
        fields = [
            'id',
            'proposal',
            'gate_type',
            'required_role',
            'is_required',
            'status',
            'rationale',
            'evidence',
            'approved_by',
            'approved_by_detail',
            'approved_at',
            'created_at',
            'updated_at',
            'audit_logs',
        ]
        read_only_fields = [
            'id',
            'proposal',
            'gate_type',
            'required_role',
            'is_required',
            'status',
            'approved_by',
            'approved_at',
            'created_at',
            'updated_at',
            'audit_logs',
        ]


class ProposalTeamMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True, required=False, allow_null=True,
    )

    class Meta:
        model = ProposalTeamMember
        fields = [
            'id', 'user', 'user_id', 'proposal', 'role',
            'hours', 'hourly_rate', 'cv_attached', 'cv_document',
            'team_member_status', 'curriculum', 'suggested_profile',
        ]


class ProposalSectionSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    ai_suggestions = AISuggestionSerializer(many=True, read_only=True)

    class Meta:
        model = ProposalSection
        fields = '__all__'


class ProposalListSerializer(serializers.ModelSerializer):
    opportunity_id = serializers.PrimaryKeyRelatedField(
        source='opportunity', read_only=True
    )
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = [
            'id', 'title', 'version', 'status', 'opportunity', 'opportunity_id',
            'created_by', 'created_at', 'updated_at', 'progress',
            'proponent_logo', 'client_logo', 'consortium_members',
        ]

    def get_progress(self, obj):
        total = obj.sections.count()
        if total == 0:
            return 0
        complete = obj.sections.filter(is_complete=True).count()
        return int((complete / total) * 100)


class ProposalDetailSerializer(serializers.ModelSerializer):
    sections = ProposalSectionSerializer(many=True, read_only=True)
    team = ProposalTeamMemberSerializer(
        source='team_members_detail', many=True, read_only=True
    )
    events = ProposalEventSerializer(many=True, read_only=True)
    budget = BudgetSerializer(read_only=True)
    proponent_logo_url = serializers.SerializerMethodField()
    client_logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = '__all__'

    def get_proponent_logo_url(self, obj):
        if obj.proponent_logo:
            return self.context['request'].build_absolute_uri(obj.proponent_logo.url)
        return None

    def get_client_logo_url(self, obj):
        if obj.client_logo:
            return self.context['request'].build_absolute_uri(obj.client_logo.url)
        return None
