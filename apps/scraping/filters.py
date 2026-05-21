import django_filters
from .models import ScrapedOpportunity
from .services.readiness import filter_ready_to_import


class ScrapedOpportunityFilter(django_filters.FilterSet):
    country = django_filters.CharFilter(lookup_expr='iexact')
    sector = django_filters.CharFilter(lookup_expr='iexact')
    ready_to_import = django_filters.BooleanFilter(method='filter_ready_to_import')

    class Meta:
        model = ScrapedOpportunity
        fields = ['source', 'status', 'cv_eligible', 'language', 'data_quality_score']

    def filter_ready_to_import(self, queryset, name, value):
        if value:
            return filter_ready_to_import(queryset)
        return queryset
