from django.utils import timezone
from rest_framework import serializers

from .models import Opportunity, Requirement, Risk


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = ['id', 'category', 'description', 'priority', 'is_covered', 'covered_in']


class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = ['id', 'description', 'severity', 'mitigation']


class OpportunityListSerializer(serializers.ModelSerializer):
    days_until_deadline = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id',
            'title',
            'client',
            'sector',
            'country',
            'value',
            'currency',
            'deadline',
            'status',
            'days_until_deadline',
            'created_at',
        ]

    def get_days_until_deadline(self, obj: Opportunity) -> int:
        if obj.deadline:
            delta = obj.deadline - timezone.now()
            return delta.days
        return 0


class OpportunityDetailSerializer(serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True, read_only=True)
    risks = RiskSerializer(many=True, read_only=True)
    days_until_deadline = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            'id',
            'title',
            'client',
            'client_logo',
            'sector',
            'country',
            'region',
            'value',
            'currency',
            'deadline',
            'status',
            'description',
            'evaluation_criteria',
            'technical_weight',
            'financial_weight',
            'tor_document',
            'reference_number',
            'url_source',
            'ai_summary',
            'ai_analysis_status',
            'created_by',
            'assigned_to',
            'requirements',
            'risks',
            'days_until_deadline',
            'created_at',
            'updated_at',
        ]

    def get_days_until_deadline(self, obj: Opportunity) -> int:
        if obj.deadline:
            delta = obj.deadline - timezone.now()
            return delta.days
        return 0
