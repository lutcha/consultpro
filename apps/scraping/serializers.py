from rest_framework import serializers
from apps.users.models import User
from .models import (
    ScrapingSource,
    ScrapedOpportunity,
    ScrapingJob,
    ScrapingAlert,
)


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class ScrapingSourceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingSource
        fields = [
            'id',
            'name',
            'organization',
            'url',
            'source_type',
            'status',
            'scrape_frequency',
            'last_scraped_at',
            'new_opportunities_count',
            'total_opportunities_count',
            'success_rate',
        ]


class ScrapingSourceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingSource
        fields = [
            'id',
            'name',
            'organization',
            'url',
            'logo',
            'source_type',
            'status',
            'scrape_frequency',
            'last_scraped_at',
            'next_scrape_at',
            'filters',
            'scraper_class',
            'scraper_config',
            'new_opportunities_count',
            'total_opportunities_count',
            'success_rate',
            'error_message',
            'created_at',
            'updated_at',
        ]


class ScrapedOpportunityListSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)

    class Meta:
        model = ScrapedOpportunity
        fields = [
            'id',
            'source',
            'source_name',
            'title',
            'organization',
            'sector',
            'country',
            'value',
            'currency',
            'deadline',
            'status',
            'scraped_at',
        ]


class ScrapedOpportunityDetailSerializer(serializers.ModelSerializer):
    source = ScrapingSourceListSerializer(read_only=True)

    class Meta:
        model = ScrapedOpportunity
        fields = [
            'id',
            'source',
            'external_id',
            'external_url',
            'title',
            'organization',
            'client',
            'sector',
            'country',
            'description',
            'value',
            'currency',
            'deadline',
            'status',
            'published_at',
            'deadline_alert',
            'ai_summary',
            'ai_extracted_requirements',
            'imported_opportunity',
            'imported_by',
            'imported_at',
            'scraped_at',
        ]


class ScrapingJobListSerializer(serializers.ModelSerializer):
    source_name = serializers.CharField(source='source.name', read_only=True)

    class Meta:
        model = ScrapingJob
        fields = [
            'id',
            'source',
            'source_name',
            'status',
            'items_found',
            'items_new',
            'items_imported',
            'started_at',
            'completed_at',
            'created_at',
        ]


class ScrapingJobDetailSerializer(serializers.ModelSerializer):
    source = ScrapingSourceListSerializer(read_only=True)
    triggered_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = ScrapingJob
        fields = [
            'id',
            'source',
            'status',
            'items_found',
            'items_new',
            'items_imported',
            'error_log',
            'executed_by',
            'triggered_by',
            'started_at',
            'completed_at',
            'created_at',
        ]


class ScrapingAlertListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingAlert
        fields = [
            'id',
            'type',
            'title',
            'read',
            'created_at',
        ]


class ScrapingAlertDetailSerializer(serializers.ModelSerializer):
    scraped_opportunity = ScrapedOpportunityListSerializer(read_only=True)

    class Meta:
        model = ScrapingAlert
        fields = [
            'id',
            'user',
            'type',
            'title',
            'message',
            'scraped_opportunity',
            'read',
            'created_at',
        ]
