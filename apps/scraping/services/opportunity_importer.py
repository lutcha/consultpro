"""
Import helpers for moving scraped records into the Opportunities module.
"""
import logging

from django.db import transaction
from django.utils import timezone

from apps.opportunities.models import Opportunity
from apps.opportunities.tasks import _sync_ai_requirements, enrich_and_score_opportunity

from .enrichment import enrich_for_import

logger = logging.getLogger(__name__)


def _queue_post_import_scoring(opportunity: Opportunity) -> bool:
    if opportunity.scores.filter(is_current=True).exists():
        return False
    transaction.on_commit(lambda: enrich_and_score_opportunity.delay(opportunity.id))
    return True


def _build_description(scraped_opp) -> str:
    description = scraped_opp.description or ''
    if scraped_opp.deep_content_text:
        description = (
            f"{description}\n\n--- Conteudo extraido da fonte/TdR ---\n"
            f"{scraped_opp.deep_content_text}"
        ).strip()
    return description


def _build_ai_extraction(scraped_opp, enriched: dict) -> dict:
    return {
        'schema': 'scraped_opportunity_import_v1',
        'source': 'scraping',
        'scraped_opportunity_id': scraped_opp.id,
        'scraping_source_id': scraped_opp.source_id,
        'scraping_source_name': scraped_opp.source.name if scraped_opp.source_id else '',
        'external_id': scraped_opp.external_id,
        'external_url': scraped_opp.external_url,
        'deep_content_url': scraped_opp.deep_content_url,
        'deep_content_status': scraped_opp.deep_content_status,
        'deep_content_extracted_at': (
            scraped_opp.deep_content_extracted_at.isoformat()
            if scraped_opp.deep_content_extracted_at else ''
        ),
        'requirements': scraped_opp.ai_extracted_requirements or [],
        'transformation_flags': scraped_opp.transformation_flags or {},
        'c3_enrichment': enriched,
        'imported_at': timezone.now().isoformat(),
    }


@transaction.atomic
def import_scraped_opportunity(scraped_opp, user=None) -> dict:
    """
    Create or link an internal Opportunity from a ScrapedOpportunity.

    Returns a small API/task-safe result dict and is idempotent by relation
    and by Opportunity.url_source.
    """
    if scraped_opp.imported_opportunity_id:
        score_queued = _queue_post_import_scoring(scraped_opp.imported_opportunity)
        return {
            'opportunity_id': scraped_opp.imported_opportunity_id,
            'opportunity_url': f'/opportunities/{scraped_opp.imported_opportunity_id}',
            'status': 'imported',
            'created': False,
            'score_queued': score_queued,
        }

    existing = Opportunity.objects.filter(url_source=scraped_opp.external_url).first()
    if existing:
        scraped_opp.status = 'imported'
        scraped_opp.imported_opportunity = existing
        scraped_opp.imported_by = user
        scraped_opp.imported_at = timezone.now()
        scraped_opp.save(update_fields=['status', 'imported_opportunity', 'imported_by', 'imported_at'])
        score_queued = _queue_post_import_scoring(existing)
        return {
            'opportunity_id': existing.id,
            'opportunity_url': f'/opportunities/{existing.id}',
            'status': 'imported',
            'created': False,
            'score_queued': score_queued,
        }

    enriched = enrich_for_import(scraped_opp)
    description = _build_description(scraped_opp)
    ai_extraction = _build_ai_extraction(scraped_opp, enriched)

    opportunity = Opportunity.objects.create(
        title=scraped_opp.title,
        client=scraped_opp.client or scraped_opp.organization,
        sector=enriched['sector'],
        country=enriched['country'],
        region=enriched['region'],
        eligible_countries=enriched['eligible_countries'],
        consortium_type=enriched['consortium_type'],
        value=scraped_opp.value or 0,
        currency=scraped_opp.currency,
        deadline=scraped_opp.deadline or timezone.now(),
        description=description,
        url_source=scraped_opp.external_url,
        ai_summary=scraped_opp.ai_summary,
        ai_extraction=ai_extraction,
        created_by=user,
    )

    _sync_ai_requirements(opportunity, scraped_opp.ai_extracted_requirements or [])

    scraped_opp.status = 'imported'
    scraped_opp.imported_opportunity = opportunity
    scraped_opp.imported_by = user
    scraped_opp.imported_at = timezone.now()
    scraped_opp.save(update_fields=['status', 'imported_opportunity', 'imported_by', 'imported_at'])
    score_queued = _queue_post_import_scoring(opportunity)

    logger.info(
        "Imported scraped opportunity %s into Opportunity %s",
        scraped_opp.id,
        opportunity.id,
    )

    return {
        'opportunity_id': opportunity.id,
        'opportunity_url': f'/opportunities/{opportunity.id}',
        'status': 'imported',
        'created': True,
        'score_queued': score_queued,
    }
