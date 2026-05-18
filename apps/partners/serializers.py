from rest_framework import serializers

from .models import PartnerProfile


class PartnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerProfile
        fields = [
            'id',
            'name',
            'sectors',
            'geographies',
            'capabilities',
            'linkedin_url',
            'website_url',
            'trust_score',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
