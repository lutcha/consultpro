import math

from django.utils import timezone
from rest_framework import serializers

from .constants import COUNTRY_CHOICES, SECTOR_CHOICES
from .models import Opportunity, OpportunityScore, Requirement, Risk


_SECTOR_ALIASES = {
    'ambiental': 'environment',
    'ambiente': 'environment',
    'tecnologia': 'ict',
    'finanças': 'financial_services',
    'financas': 'financial_services',
    'infraestruturas': 'infrastructure',
    'educação': 'education',
    'educacao': 'education',
    'saúde': 'health',
    'saude': 'health',
    'agricultura': 'agriculture',
    'governação': 'governance',
    'governacao': 'governance',
}

_COUNTRY_ALIASES = {
    'cabo verde': 'cv',
    'moçambique': 'mz',
    'mocambique': 'mz',
    'angola': 'ao',
    'senegal': 'sn',
    'guiné-bissau': 'gw',
    'guine-bissau': 'gw',
    'timor-leste': 'tl',
    'são tomé e príncipe': 'st',
    'sao tome e principe': 'st',
    'outro': 'int',
    'other': 'int',
    'international': 'int',
    'internacional': 'int',
}


class _FlexChoiceField(serializers.ChoiceField):
    def __init__(self, choices, aliases=None, **kwargs):
        super().__init__(choices, **kwargs)
        self._label_map = {label.lower(): code for code, label in choices}
        self._aliases = aliases or {}

    def to_internal_value(self, data):
        if data in self._choices:
            return data
        key = str(data).lower()
        return (
            self._label_map.get(key)
            or self._aliases.get(key)
            or self.fail('invalid_choice', input=data)
        )


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = ['id', 'category', 'description', 'priority', 'is_covered', 'covered_in']


class RiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Risk
        fields = ['id', 'description', 'severity', 'mitigation']


class OpportunityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpportunityScore
        fields = [
            'id',
            'opportunity',
            'strategic_fit',
            'win_probability',
            'margin',
            'risk',
            'resource',
            'overall_score',
            'confidence_score',
            'ai_extracted_criteria',
            'evaluation_weights',
            'reasoning_trace',
            'input_snapshot',
            'provider',
            'model',
            'scoring_version',
            'is_current',
            'created_at',
        ]
        read_only_fields = fields


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
            return max(0, int(delta.total_seconds() // 86400))
        return 0


class OpportunityDetailSerializer(serializers.ModelSerializer):
    requirements = RequirementSerializer(many=True, read_only=True)
    risks = RiskSerializer(many=True, read_only=True)
    days_until_deadline = serializers.SerializerMethodField()
    sector = _FlexChoiceField(choices=SECTOR_CHOICES, aliases=_SECTOR_ALIASES)
    country = _FlexChoiceField(choices=COUNTRY_CHOICES, aliases=_COUNTRY_ALIASES)
    description = serializers.CharField(required=False, allow_blank=True, default='')

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
            'eligible_countries',
            'consortium_type',
            'consortium_notes',
            'partner_profiles',
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
            'ai_extraction',
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
            return math.ceil(delta.total_seconds() / 86400)
        return 0
