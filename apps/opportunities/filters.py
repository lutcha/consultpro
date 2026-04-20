import django_filters
from django.utils.translation import gettext_lazy as _

from .models import Opportunity


class OpportunityFilter(django_filters.FilterSet):
    deadline_after = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='gte')
    deadline_before = django_filters.DateTimeFilter(field_name='deadline', lookup_expr='lte')

    class Meta:
        model = Opportunity
        fields = ['status', 'client', 'sector', 'country', 'deadline_after', 'deadline_before']
