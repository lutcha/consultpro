from rest_framework import serializers

from .models import KnowledgeAsset


class KnowledgeAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeAsset
        fields = [
            'id',
            'asset_type',
            'title',
            'summary',
            'content',
            'source_app',
            'source_model',
            'source_id',
            'source_url',
            'metadata',
            'tags',
            'country',
            'sector',
            'status',
            'indexed_at',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['indexed_at', 'created_at', 'updated_at']


class KnowledgeSearchResultSerializer(serializers.Serializer):
    asset = KnowledgeAssetSerializer()
    score = serializers.FloatField()
    reasoning_trace = serializers.ListField(child=serializers.CharField())
    search_mode = serializers.CharField()
