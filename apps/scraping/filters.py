import django_filters
from .models import ScrapedOpportunity


class ScrapedOpportunityFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr='iexact')
    sector = django_filters.CharFilter(lookup_expr='iexact')

    class Meta:
        model = ScrapedOpportunity
        fields = ['source', 'status', 'cv_eligible', 'language', 'data_quality_score']
