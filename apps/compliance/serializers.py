from rest_framework import serializers

from .models import ComplianceMatrix, ComplianceMatrixRow


class ComplianceMatrixRowSerializer(serializers.ModelSerializer):
    proposal_section_title = serializers.CharField(source='proposal_section.title', read_only=True)

    class Meta:
        model = ComplianceMatrixRow
        fields = [
            'id',
            'matrix',
            'requirement_key',
            'requirement_text',
            'requirement_category',
            'priority',
            'status',
            'proposal_section',
            'proposal_section_title',
            'evidence_text',
            'evidence_link',
            'source_type',
            'source_reference',
            'source_trace',
            'confidence_score',
            'ai_metadata',
            'human_override',
            'human_override_note',
            'order',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'matrix',
            'requirement_key',
            'source_type',
            'source_reference',
            'source_trace',
            'confidence_score',
            'ai_metadata',
            'order',
            'created_at',
            'updated_at',
        ]

    def validate_proposal_section(self, value):
        matrix = self.instance.matrix if self.instance else None
        if value and matrix and value.proposal.opportunity_id != matrix.opportunity_id:
            raise serializers.ValidationError('Section must belong to a proposal for the same opportunity.')
        return value


class ComplianceMatrixSerializer(serializers.ModelSerializer):
    rows = ComplianceMatrixRowSerializer(many=True, read_only=True)
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)

    class Meta:
        model = ComplianceMatrix
        fields = [
            'id',
            'opportunity',
            'opportunity_title',
            'status',
            'generation_version',
            'source_trace',
            'ai_metadata',
            'confidence_score',
            'human_override_count',
            'generated_by',
            'created_at',
            'updated_at',
            'rows',
        ]
        read_only_fields = [
            'id',
            'opportunity',
            'opportunity_title',
            'generation_version',
            'source_trace',
            'ai_metadata',
            'confidence_score',
            'human_override_count',
            'generated_by',
            'created_at',
            'updated_at',
            'rows',
        ]
