from rest_framework import serializers

from apps.users.models import User
from .models import (
    AISuggestion,
    Budget,
    BudgetItem,
    Comment,
    Proposal,
    ProposalSection,
    ProposalTeamMember,
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


class ProposalTeamMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = ProposalTeamMember
        fields = [
            'id', 'user', 'user_id', 'proposal', 'role',
            'hours', 'hourly_rate', 'cv_attached', 'cv_document',
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
        source='proposalteammember_set', many=True, read_only=True
    )
    budget = BudgetSerializer(read_only=True)

    class Meta:
        model = Proposal
        fields = '__all__'
