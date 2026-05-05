from rest_framework import serializers
from apps.users.models import User
from apps.opportunities.models import Opportunity
from .models import (
    Curriculum,
    CVTemplate,
    TemplateMatch,
    CVSuggestion,
    CVOpportunityMatch,
)


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar']


class CurriculumListSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = Curriculum
        fields = [
            'id',
            'user',
            'file_name',
            'file_type',
            'status',
            'analysis_score',
            'created_at',
            'updated_at',
        ]


class CurriculumDetailSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    template_matches = serializers.SerializerMethodField()
    suggestions = serializers.SerializerMethodField()

    class Meta:
        model = Curriculum
        fields = [
            'id',
            'user',
            'file_name',
            'file_type',
            'status',
            'analysis_score',
            'extracted_data',
            'template_matches',
            'suggestions',
            'created_at',
            'updated_at',
        ]

    def get_template_matches(self, obj):
        matches = obj.template_matches.all()
        return TemplateMatchSerializer(matches, many=True).data

    def get_suggestions(self, obj):
        suggestions = obj.suggestions.all()
        return CVSuggestionSerializer(suggestions, many=True).data


class CVSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVSuggestion
        fields = [
            'id',
            'type',
            'priority',
            'message',
            'context',
            'auto_fixable',
            'fixed',
            'created_at',
        ]


class CVTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVTemplate
        fields = [
            'id',
            'name',
            'organization',
            'organization_name',
            'description',
            'required_sections',
            'format_rules',
            'max_length_pages',
            'file_template',
            'example_url',
            'is_active',
            'created_at',
        ]


class TemplateMatchSerializer(serializers.ModelSerializer):
    template = CVTemplateSerializer(read_only=True)
    generated_file_url = serializers.SerializerMethodField()

    class Meta:
        model = TemplateMatch
        fields = [
            'id',
            'curriculum',
            'template',
            'match_score',
            'missing_sections',
            'recommendations',
            'adapted_content',
            'generated_file',
            'generated_file_url',
            'created_at',
        ]

    def get_generated_file_url(self, obj):
        if obj.generated_file:
            return obj.generated_file.url
        return None


class CVOpportunityMatchSerializer(serializers.ModelSerializer):
    opportunity_title = serializers.CharField(source='opportunity.title', read_only=True)
    opportunity_client = serializers.CharField(source='opportunity.client', read_only=True)

    class Meta:
        model = CVOpportunityMatch
        fields = [
            'id',
            'curriculum',
            'opportunity',
            'opportunity_title',
            'opportunity_client',
            'overall_score',
            'skills_match_score',
            'experience_match_score',
            'education_match_score',
            'language_match_score',
            'matched_skills',
            'missing_skills',
            'relevant_experiences',
            'recommendations',
            'created_at',
        ]
