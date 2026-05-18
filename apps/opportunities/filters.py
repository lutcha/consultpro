import django_filters
from django.utils.translation import gettext_lazy as _

from .models import Opportunity


class OpportunityFilter(django_filters.FilterSet):
    deadline_after = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    deadline_before = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')
    region = django_filters.CharFilter(field_name='region')
    min_score = django_filters.NumberFilter(method='filter_min_score')

    def filter_min_score(self, queryset, name, value):
        return queryset.filter(scores__is_current=True, scores__overall_score__gte=value).distinct()

    class Meta:
        model = Opportunity
        fields = [
            'status',
            'client',
            'sector',
            'country',
            'region',
            'deadline_after',
            'deadline_before',
            'min_score',
        ]
