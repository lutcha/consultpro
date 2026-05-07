"""
Celery tasks for the scraping pipeline.

Pipeline:
  1. Fetch raw data via scraper class
  2. Parse into standardized items
  3. Validate deadlines
  4. Evaluate Cabo Verde eligibility
  5. Deduplicate against existing records
  6. Upsert ScrapedOpportunity with full provenance
  7. Update source statistics
"""
import logging
import uuid
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import ScrapingSource, ScrapedOpportunity, ScrapingJob
from .scrapers.registry import get_scraper_class
from .services.deadline_validator import DeadlineValidator
from .services.cv_eligibility import CaboVerdeEligibilityValidator
from .services.deduplication import SmartDeduplicator

logger = logging.getLogger(__name__)

# === AI Enrichment Settings ===
AI_ENRICHMENT_MIN_DESCRIPTION_LENGTH = 80  # Don't waste API calls on very short texts
AI_ENRICHMENT_MAX_TEXT_LENGTH = 12000       # Truncate very long descriptions


def _format_scraping_error(exc):
    message = str(exc).strip()
    if message:
        return message[:1000]
    return f'{exc.__class__.__name__}: no error detail provided'


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_scraping_source(self, source_id, executed_by='scheduler', user_id=None):
    """
    Execute web scraping for a specific source with full validation pipeline.
    """
    try:
        source = ScrapingSource.objects.get(id=source_id, status='active')
    except ScrapingSource.DoesNotExist:
        logger.warning(f"Source {source_id} not found or not active")
        return {'status': 'error', 'message': 'Source not found or inactive'}

    batch_id = str(uuid.uuid4())
    job = ScrapingJob.objects.create(
        source=source,
        status='running',
        started_at=timezone.now(),
        executed_by=executed_by,
        triggered_by_id=user_id,
        batch_stats={'batch_id': batch_id},
    )

    stats = {
        'batch_id': batch_id,
        'source_id': source_id,
        'total_received': 0,
        'processed': 0,
        'validated': 0,
        'eligible_cv': 0,
        'duplicates_skipped': 0,
        'ingested': 0,
        'rejected': 0,
        'errors': [],
    }

    try:
        scraper_class = get_scraper_class(source.scraper_class)
        scraper = scraper_class(source)
        result = scraper.execute()

        if result['status'] != 'success':
            detail = result.get('error') or result.get('message') or result
            raise RuntimeError(f'Scraper returned {result.get("status")}: {detail}')

        raw_items = result['items']
        stats['total_received'] = len(raw_items)
        logger.info(f"Source '{source.name}': fetched {len(raw_items)} raw items")

        for idx, raw_item in enumerate(raw_items):
            try:
                outcome = _process_single_item(raw_item, source, batch_id, stats)
                stats['processed'] += 1
                if outcome == 'rejected':
                    stats['rejected'] += 1
            except Exception as e:
                logger.error(f"Error processing item[{idx}] from {source.name}: {e}", exc_info=True)
                stats['errors'].append({'index': idx, 'error': str(e)})
                stats['rejected'] += 1

        # Update source stats
        source.last_scraped_at = timezone.now()
        source.total_opportunities_count = ScrapedOpportunity.objects.filter(source=source).count()
        source.new_opportunities_count = ScrapedOpportunity.objects.filter(
            source=source, status='new'
        ).count()
        if stats['total_received'] > 0:
            source.success_rate = int(
                ((stats['ingested'] + stats['duplicates_skipped']) / stats['total_received']) * 100
            )
        source.error_message = ''
        source.save()

        job.status = 'completed'
        job.completed_at = timezone.now()
        job.items_found = stats['total_received']
        job.items_new = stats['ingested']
        job.items_duplicate = stats['duplicates_skipped']
        job.items_rejected = stats['rejected']
        job.batch_stats = stats
        job.save()

        logger.info(f"Batch {batch_id} completed for {source.name}: {stats}")

        # Trigger notifications for CV-eligible opportunities from this batch
        if stats['eligible_cv'] > 0:
            notify_new_cv_eligible_opportunities.delay(batch_id=batch_id)

        return {'status': 'completed', 'job_id': job.id, 'stats': stats}

    except Exception as e:
        error_message = _format_scraping_error(e)
        logger.error(f"Scraping job failed for source {source_id}: {error_message}", exc_info=True)
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_log = error_message
        job.batch_stats = stats
        job.save()

        source.status = 'error'
        source.error_message = error_message[:500]
        source.success_rate = 0
        source.save()

        # Retry on transient errors
        if isinstance(e, (TimeoutError, ConnectionError)) and self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {'status': 'failed', 'job_id': job.id, 'error': error_message}


@shared_task
def run_all_scraping_sources():
    """Run scraping for all active sources."""
    active_sources = ScrapingSource.objects.filter(status='active')
    queued = 0
    for source in active_sources:
        # Respect next_scrape_at if set
        if source.next_scrape_at and source.next_scrape_at > timezone.now():
            logger.info(f"Skipping {source.name}: next scrape at {source.next_scrape_at}")
            continue
        run_scraping_source.delay(source.id)
        queued += 1

        # Update next scrape based on frequency
        if source.scrape_frequency == 'hourly':
            source.next_scrape_at = timezone.now() + timedelta(hours=1)
        elif source.scrape_frequency == 'daily':
            source.next_scrape_at = timezone.now() + timedelta(days=1)
        elif source.scrape_frequency == 'weekly':
            source.next_scrape_at = timezone.now() + timedelta(weeks=1)
        source.save(update_fields=['next_scrape_at'])

    return {'status': 'queued', 'sources_count': queued}


@shared_task
def check_expired_scraped_opportunities():
    """Mark scraped opportunities as expired if their deadline has passed."""
    now = timezone.now()
    expired = ScrapedOpportunity.objects.filter(
        status='new',
        deadline__lt=now,
    ).update(status='expired')

    logger.info(f"Marked {expired} scraped opportunities as expired")
    return {'expired_count': expired}


def _process_single_item(raw_item, source, batch_id, stats):
    """
    Process a single scraped item through the full validation pipeline.
    """
    title = raw_item.get('title', '')
    description = raw_item.get('description', '')
    external_id = raw_item.get('external_id', '')
    external_url = raw_item.get('external_url', source.url)

    # === Phase 1: Raw data hashing for quick duplicate check ===
    content_hash = SmartDeduplicator.compute_content_hash(raw_item)

    # Quick hash duplicate check
    existing_hash = ScrapedOpportunity.objects.filter(
        source=source,
        raw_content_hash=content_hash,
    ).first()
    if existing_hash:
        stats['duplicates_skipped'] += 1
        return

    # === Phase 2: Deadline validation ===
    deadline_str = raw_item.get('deadline')
    published_at = None
    if raw_item.get('published_at'):
        from dateutil import parser as date_parser
        try:
            published_at = date_parser.parse(raw_item['published_at'])
        except Exception:
            pass

    deadline_validation = DeadlineValidator.validate(
        raw_deadline=deadline_str,
        published_at=published_at,
    )

    normalized_deadline = None
    if deadline_validation.get('normalized_deadline'):
        from dateutil import parser as date_parser
        try:
            normalized_deadline = date_parser.parse(deadline_validation['normalized_deadline'])
        except Exception:
            normalized_deadline = None

    # Reject if deadline is fundamentally invalid (not just expired)
    if deadline_validation['errors'] and not normalized_deadline:
        _create_rejected_record(
            source, external_id, external_url, title, raw_item,
            content_hash, deadline_validation, batch_id,
            rejection_reason='invalid_deadline'
        )
        return 'rejected'

    # === Phase 3: Cabo Verde eligibility ===
    eligibility = CaboVerdeEligibilityValidator.evaluate(raw_item)

    # === Phase 4: Smart deduplication (title + description + deadline) ===
    is_duplicate, existing_id = SmartDeduplicator.check_duplicate(
        title=title,
        description=description,
        deadline=normalized_deadline,
        source_name=source.name,
        external_id=external_id,
    )

    if is_duplicate:
        stats['duplicates_skipped'] += 1
        return

    # === Phase 5: Build transformation flags ===
    transformation_flags = {
        'deadline_normalized': bool(normalized_deadline),
        'eligibility_evaluated': True,
        'content_hashed': True,
        'processed_at': timezone.now().isoformat(),
    }
    if deadline_validation.get('warnings'):
        transformation_flags['deadline_warnings'] = deadline_validation['warnings']

    # Compute data quality score
    quality_score = _compute_quality_score(raw_item, deadline_validation, eligibility)

    # === Phase 6: Unified Upsert ===
    with transaction.atomic():
        opportunity, created = ScrapedOpportunity.objects.update_or_create(
            source=source,
            external_id=external_id,
            defaults={
                'external_url': external_url,
                'title': title[:500],
                'organization': raw_item.get('organization', source.organization)[:200],
                'client': raw_item.get('client', '')[:200],
                'sector': raw_item.get('sector', '')[:100],
                'country': raw_item.get('country', '')[:100],
                'region': raw_item.get('region', '')[:100],
                'description': description,
                'value': raw_item.get('value'),
                'currency': raw_item.get('currency', 'USD')[:3],
                'deadline': normalized_deadline,
                'status': 'new',
                'published_at': published_at,
                'language': raw_item.get('language', '')[:10],
                'sector_tags': raw_item.get('sector_tags', []),
                'geographic_scope': raw_item.get('geographic_scope', {}),
                # Pipeline fields
                'raw_payload': raw_item,
                'raw_content_hash': content_hash,
                'deadline_validation': deadline_validation,
                'deadline_timezone': deadline_validation.get('metadata', {}).get('timezone', 'Atlantic/Cape_Verde'),
                'cv_eligible': eligibility['is_eligible'],
                'eligibility_data': eligibility,
                'data_quality_score': quality_score,
                'transformation_flags': transformation_flags,
                'ingestion_batch_id': batch_id,
            }
        )

    stats['validated'] += 1
    if eligibility['is_eligible']:
        stats['eligible_cv'] += 1
    stats['ingested'] += 1

    logger.info(
        f"Ingested opportunity: {opportunity.title[:80]}... "
        f"(CV eligible: {eligibility['is_eligible']}, quality: {quality_score})"
    )

    # === Phase 7: Trigger async AI enrichment ===
    if created or not opportunity.ai_summary:
        enrich_scraped_opportunity_with_ai.delay(opportunity.id)


@shared_task(bind=True, max_retries=2, default_retry_delay=120)
def enrich_scraped_opportunity_with_ai(self, scraped_opportunity_id: int):
    """
    Enrich a ScrapedOpportunity with AI-generated summary and extracted requirements.
    Called asynchronously after ingestion to avoid blocking the scraping pipeline.
    """
    try:
        opp = ScrapedOpportunity.objects.get(id=scraped_opportunity_id)
    except ScrapedOpportunity.DoesNotExist:
        logger.warning(f"AI enrichment: ScrapedOpportunity {scraped_opportunity_id} not found")
        return {'status': 'error', 'reason': 'not_found'}

    # Build text for analysis
    text_parts = [f"Title: {opp.title}"]
    if opp.organization:
        text_parts.append(f"Organization: {opp.organization}")
    if opp.client:
        text_parts.append(f"Client: {opp.client}")
    if opp.description:
        text_parts.append(f"Description: {opp.description}")
    if opp.sector:
        text_parts.append(f"Sector: {opp.sector}")
    if opp.country:
        text_parts.append(f"Country: {opp.country}")

    full_text = '\n\n'.join(text_parts)

    # Skip if text too short
    if len(full_text) < AI_ENRICHMENT_MIN_DESCRIPTION_LENGTH:
        logger.info(f"AI enrichment skipped for {scraped_opportunity_id}: text too short ({len(full_text)} chars)")
        opp.transformation_flags = {
            **opp.transformation_flags,
            'ai_enrichment_skipped': True,
            'ai_enrichment_reason': 'text_too_short',
        }
        opp.save(update_fields=['transformation_flags'])
        return {'status': 'skipped', 'reason': 'text_too_short'}

    # Truncate if too long
    if len(full_text) > AI_ENRICHMENT_MAX_TEXT_LENGTH:
        full_text = full_text[:AI_ENRICHMENT_MAX_TEXT_LENGTH] + '\n\n[Text truncated for analysis]'

    try:
        from apps.ai_services.services import AIServiceFactory
        service = AIServiceFactory.get_service()
        result = service.analyze_document(full_text)

        summary = result.get('summary', '')
        requirements = result.get('requirements', [])
        risks = result.get('risks', [])

        opp.ai_summary = summary
        opp.ai_extracted_requirements = requirements
        opp.transformation_flags = {
            **opp.transformation_flags,
            'ai_enriched': True,
            'ai_enriched_at': timezone.now().isoformat(),
            'ai_requirements_count': len(requirements),
            'ai_risks_count': len(risks),
        }
        opp.save(update_fields=['ai_summary', 'ai_extracted_requirements', 'transformation_flags'])

        logger.info(
            f"AI enrichment completed for {scraped_opportunity_id}: "
            f"summary_len={len(summary)}, reqs={len(requirements)}, risks={len(risks)}"
        )
        return {
            'status': 'completed',
            'requirements_count': len(requirements),
            'risks_count': len(risks),
        }

    except Exception as exc:
        logger.exception(f"AI enrichment failed for {scraped_opportunity_id}: {exc}")
        opp.transformation_flags = {
            **opp.transformation_flags,
            'ai_enrichment_failed': True,
            'ai_enrichment_error': str(exc)[:200],
        }
        opp.save(update_fields=['transformation_flags'])

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {'status': 'failed', 'error': str(exc)}


@shared_task
def notify_new_cv_eligible_opportunities(batch_id: str = None, hours_window: int = 24):
    """
    Create alerts and notifications for newly scraped opportunities that are
    eligible for Cabo Verde. Can be called after a scraping batch or on schedule.
    """
    from apps.users.models import User
    from apps.notifications.tasks import send_notification
    from apps.scraping.models import ScrapingAlert

    now = timezone.now()
    cutoff = now - timedelta(hours=hours_window)

    qs = ScrapedOpportunity.objects.filter(
        cv_eligible=True,
        status='new',
        scraped_at__gte=cutoff,
    )
    if batch_id:
        qs = qs.filter(ingestion_batch_id=batch_id)

    # Get managers to notify
    managers = User.objects.filter(role__in=['manager', 'admin'])
    if not managers.exists():
        managers = User.objects.filter(is_staff=True)

    alerts_created = 0
    notifications_created = 0

    for opp in qs:
        # Skip if already alerted for this opportunity in the last 7 days
        already_alerted = ScrapingAlert.objects.filter(
            scraped_opportunity=opp,
            type='new_opportunity',
            created_at__gte=now - timedelta(days=7),
        ).exists()
        if already_alerted:
            continue

        # Create ScrapingAlert for each manager
        for manager in managers:
            alert, created = ScrapingAlert.objects.get_or_create(
                user=manager,
                type='new_opportunity',
                scraped_opportunity=opp,
                defaults={
                    'title': f'Nova oportunidade elegivel para CV: {opp.title[:80]}',
                    'message': (
                        f'Fonte: {opp.source.name}\n'
                        f'Prazo: {opp.deadline.strftime("%d/%m/%Y") if opp.deadline else "N/A"}\n'
                        f'Pais: {opp.country or "N/A"}\n'
                        f'Setor: {opp.sector or "N/A"}\n'
                        f'Confianca de elegibilidade: {opp.eligibility_data.get("confidence", "N/A")}'
                    ),
                }
            )
            if created:
                alerts_created += 1

        # Create in-app Notification for each manager — deduplicated by title+user
        from apps.notifications.models import Notification
        notif_title = f'Nova oportunidade: {opp.title[:60]}'
        notif_message = (
            f'Oportunidade elegivel para Cabo Verde detectada em {opp.source.name}. '
            f'Prazo: {opp.deadline.strftime("%d/%m/%Y") if opp.deadline else "N/A"}.'
        )
        for manager in managers:
            already_notified = Notification.objects.filter(
                user=manager,
                title=notif_title,
                created_at__gte=now - timedelta(days=7),
            ).exists()
            if already_notified:
                continue
            try:
                send_notification.delay(
                    user_id=manager.id,
                    type='info',
                    title=notif_title,
                    message=notif_message,
                    action_label='Ver Oportunidade',
                    action_url=f'/scraping/opportunities/{opp.id}/',
                )
                notifications_created += 1
            except Exception as notify_exc:
                logger.warning(f"Could not queue notification for {manager.email}: {notify_exc}")
                try:
                    send_notification.apply(kwargs={
                        'user_id': manager.id,
                        'type': 'info',
                        'title': notif_title,
                        'message': notif_message,
                        'action_label': 'Ver Oportunidade',
                        'action_url': f'/scraping/opportunities/{opp.id}/',
                    })
                    notifications_created += 1
                except Exception:
                    pass

    logger.info(
        f"Notification task completed: {alerts_created} alerts, "
        f"{notifications_created} notifications for {qs.count()} CV-eligible opportunities"
    )
    return {
        'opportunities_found': qs.count(),
        'alerts_created': alerts_created,
        'notifications_created': notifications_created,
    }


def _create_rejected_record(source, external_id, external_url, title, raw_item,
                            content_hash, deadline_validation, batch_id, rejection_reason):
    """Create or update a rejected ScrapedOpportunity for audit trail."""
    ScrapedOpportunity.objects.update_or_create(
        source=source,
        external_id=external_id,
        defaults={
            'external_url': external_url,
            'title': title[:500] if title else 'Untitled',
            'organization': raw_item.get('organization', source.organization)[:200],
            'description': raw_item.get('description', '')[:1000],
            'status': 'rejected',
            'raw_payload': raw_item,
            'raw_content_hash': content_hash,
            'deadline_validation': deadline_validation,
            'transformation_flags': {
                'rejected': True,
                'rejection_reason': rejection_reason,
                'processed_at': timezone.now().isoformat(),
            },
            'ingestion_batch_id': batch_id,
            'data_quality_score': 0.0,
        }
    )


def _compute_quality_score(raw_item, deadline_validation, eligibility) -> float:
    """Compute a 0.00-1.00 data quality score."""
    score = 1.0

    # Deduct for missing critical fields
    if not raw_item.get('title'):
        score -= 0.3
    if not raw_item.get('description'):
        score -= 0.2
    if not raw_item.get('deadline'):
        score -= 0.2

    # Deduct for deadline warnings
    warnings = deadline_validation.get('warnings', [])
    score -= min(0.15, len(warnings) * 0.05)

    # Deduct for low confidence eligibility (unclear geography)
    confidence = eligibility.get('confidence', 1.0)
    if confidence < 0.3:
        score -= 0.1

    # Deduct for very short descriptions
    desc_len = len(raw_item.get('description', ''))
    if desc_len < 100:
        score -= 0.1
    elif desc_len < 300:
        score -= 0.05

    return round(max(0.0, min(1.0, score)), 2)
