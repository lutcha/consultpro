from rest_framework import serializers

from .models import QCCheckCategory, QCItem, QCSuggestion, QualityCheck


class QCItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCItem
        fields = ['id', 'description', 'status', 'section']


class QCCheckCategorySerializer(serializers.ModelSerializer):
    items = QCItemSerializer(many=True, read_only=True)

    class Meta:
        model = QCCheckCategory
        fields = ['id', 'category', 'score', 'status', 'items']


class QCSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCSuggestion
        fields = ['id', 'text', 'action', 'target_section', 'applied', 'ignored']


class QualityCheckSerializer(serializers.ModelSerializer):
    categories = QCCheckCategorySerializer(many=True, read_only=True)
    suggestions = QCSuggestionSerializer(many=True, read_only=True)
    checks = serializers.SerializerMethodField()
    proposal_id = serializers.PrimaryKeyRelatedField(
        source='proposal', read_only=True
    )

    class Meta:
        model = QualityCheck
        fields = [
            'id',
            'proposal',
            'proposal_id',
            'overall_score',
            'status',
            'can_submit',
            'executed_by',
            'executed_at',
            'created_at',
            'categories',
            'suggestions',
            'checks',
        ]

    def get_checks(self, obj):
        checks = {}
        for category in obj.categories.all():
            checks[category.category] = {
                'score': category.score,
                'status': category.status,
                'items': QCItemSerializer(category.items.all(), many=True).data,
            }
        return checks


class QualityCheckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = [
            'id',
            'proposal',
            'overall_score',
            'status',
            'can_submit',
            'created_at',
        ]
