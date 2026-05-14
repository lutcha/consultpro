from decimal import Decimal

from django.db.models import Q
from django.utils import timezone


MIN_IMPORT_QUALITY_SCORE = Decimal('0.45')


def get_import_readiness(scraped_opp):
    reasons = []

    if scraped_opp.status != 'new':
        reasons.append('status_not_new')
    if not scraped_opp.cv_eligible:
        reasons.append('not_cv_eligible')
    if scraped_opp.imported_opportunity_id:
        reasons.append('already_imported')
    if scraped_opp.deadline and scraped_opp.deadline < timezone.now():
        reasons.append('deadline_expired')
    if scraped_opp.data_quality_score < MIN_IMPORT_QUALITY_SCORE:
        reasons.append('low_data_quality')

    return {
        'ready': not reasons,
        'reasons': reasons,
        'minimum_quality_score': str(MIN_IMPORT_QUALITY_SCORE),
    }


def filter_ready_to_import(queryset):
    return queryset.filter(
        status='new',
        cv_eligible=True,
        imported_opportunity__isnull=True,
        data_quality_score__gte=MIN_IMPORT_QUALITY_SCORE,
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gte=timezone.now())
    )
