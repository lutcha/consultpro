from rest_framework import serializers

from apps.proposals.models import ProposalSection

from .models import IssueTreeNode, IssueTreeSnapshot
from .services import validate_node_scope


class IssueTreeNodeSerializer(serializers.ModelSerializer):
    children_count = serializers.IntegerField(read_only=True)
    assigned_to_email = serializers.CharField(source='assigned_to.email', read_only=True)
    proposal_section_title = serializers.CharField(source='proposal_section.title', read_only=True)

    class Meta:
        model = IssueTreeNode
        fields = [
            'id',
            'proposal',
            'parent',
            'source_key',
            'node_type',
            'title',
            'hypothesis',
            'data_needed',
            'assigned_to',
            'assigned_to_email',
            'proposal_section',
            'proposal_section_title',
            'status',
            'order',
            'source_trace',
            'ai_metadata',
            'created_by',
            'created_at',
            'updated_at',
            'children_count',
        ]
        read_only_fields = [
            'id',
            'source_key',
            'source_trace',
            'ai_metadata',
            'created_by',
            'created_at',
            'updated_at',
            'children_count',
        ]

    def validate(self, attrs):
        proposal = attrs.get('proposal') or getattr(self.instance, 'proposal', None)
        parent = attrs.get('parent') or getattr(self.instance, 'parent', None)
        proposal_section = attrs.get('proposal_section') or getattr(self.instance, 'proposal_section', None)
        if proposal:
            try:
                validate_node_scope(proposal, parent=parent, proposal_section=proposal_section)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc)) from exc
        return attrs

    def validate_proposal_section(self, value):
        if value and not isinstance(value, ProposalSection):
            raise serializers.ValidationError('Invalid proposal section.')
        return value


class IssueTreeSnapshotSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = IssueTreeSnapshot
        fields = [
            'id',
            'proposal',
            'version',
            'label',
            'snapshot',
            'created_by',
            'created_by_email',
            'created_at',
        ]
        read_only_fields = ['id', 'version', 'snapshot', 'created_by', 'created_at']
