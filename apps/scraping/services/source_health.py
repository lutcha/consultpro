from django.db.models import Count, Max, Q

from apps.scraping.models import ScrapingJob, ScrapingSource


BLOCKED_ACCESS = {'restricted_login', 'subscription'}


def _source_access(source: ScrapingSource) -> str:
    config_access = source.scraper_config.get('access')
    filter_access = source.filters.get('access') or []
    if config_access in BLOCKED_ACCESS:
        return config_access
    if any(item in BLOCKED_ACCESS for item in filter_access):
        return next(item for item in filter_access if item in BLOCKED_ACCESS)
    return 'public'


def _health_reason(health_status: str, access: str, source: ScrapingSource, last_job: ScrapingJob | None) -> str:
    if health_status == 'blocked':
        return 'Fonte requer login ou subscricao; manter como lead discovery ate haver acesso.'
    if health_status == 'paused':
        return 'Fonte pausada manualmente; nao entra no scraping automatico.'
    if health_status == 'disabled':
        return 'Fonte desativada.'
    if health_status == 'failing':
        if last_job and last_job.error_log:
            return last_job.error_log[:300]
        return source.error_message[:300] or 'Ultima execucao falhou.'
    if health_status == 'empty':
        return 'Ultimas execucoes nao encontraram oportunidades novas.'
    if health_status == 'healthy':
        return 'Fonte a produzir resultados utilizaveis.'
    return 'Fonte ainda sem execucao suficiente para diagnostico.'


def _score_source(source: ScrapingSource, last_job: ScrapingJob | None, total_opportunities: int) -> int:
    access = _source_access(source)
    if source.status == 'disabled':
        return 0
    if access in BLOCKED_ACCESS:
        return 15
    if source.status == 'paused':
        return 25
    if source.status == 'error':
        return 20
    if last_job and last_job.status == 'failed':
        return 25
    if last_job and last_job.status == 'completed' and last_job.items_found == 0 and total_opportunities == 0:
        return 45

    score = int(source.success_rate or 0)
    if last_job and last_job.status == 'completed':
        score = max(score, 70)
        if last_job.items_new or last_job.items_imported:
            score += 15
    if total_opportunities:
        score = max(score, 75)

    return max(0, min(score, 100))


def get_source_health(source: ScrapingSource) -> dict:
    last_job = source.jobs.order_by('-created_at').first()
    access = _source_access(source)
    total_opportunities = getattr(source, 'health_total_opportunities', None)
    imported_opportunities = getattr(source, 'health_imported_opportunities', None)
    last_opportunity_at = getattr(source, 'health_last_opportunity_at', None)

    if total_opportunities is None:
        total_opportunities = source.scraped_opportunities.count()
    if imported_opportunities is None:
        imported_opportunities = source.scraped_opportunities.filter(status='imported').count()
    if last_opportunity_at is None:
        last_opportunity_at = source.scraped_opportunities.aggregate(last=Max('scraped_at'))['last']

    if access in BLOCKED_ACCESS:
        health_status = 'blocked'
    elif source.status == 'paused':
        health_status = 'paused'
    elif source.status == 'disabled':
        health_status = 'disabled'
    elif source.status == 'error' or (last_job and last_job.status == 'failed'):
        health_status = 'failing'
    elif last_job and last_job.status == 'completed' and last_job.items_found == 0 and total_opportunities == 0:
        health_status = 'empty'
    elif total_opportunities > 0 or (last_job and last_job.status == 'completed' and last_job.items_found > 0):
        health_status = 'healthy'
    else:
        health_status = 'unknown'

    return {
        'id': source.id,
        'name': source.name,
        'organization': source.organization,
        'url': source.url,
        'source_type': source.source_type,
        'status': source.status,
        'health_status': health_status,
        'health_score': _score_source(source, last_job, total_opportunities),
        'health_reason': _health_reason(health_status, access, source, last_job),
        'access': access,
        'scraper_class': source.scraper_class,
        'scrape_frequency': source.scrape_frequency,
        'last_scraped_at': source.last_scraped_at,
        'last_job_status': last_job.status if last_job else None,
        'last_job_at': last_job.created_at if last_job else None,
        'last_error': (last_job.error_log if last_job and last_job.error_log else source.error_message)[:300],
        'items_found_last_run': last_job.items_found if last_job else 0,
        'items_new_last_run': last_job.items_new if last_job else 0,
        'total_opportunities': total_opportunities,
        'imported_opportunities': imported_opportunities,
        'last_opportunity_at': last_opportunity_at,
        'production_ready': health_status == 'healthy' and access == 'public',
    }


def get_sources_health(queryset=None) -> list[dict]:
    queryset = queryset or ScrapingSource.objects.all()
    queryset = queryset.annotate(
        health_total_opportunities=Count('scraped_opportunities', distinct=True),
        health_imported_opportunities=Count(
            'scraped_opportunities',
            filter=Q(scraped_opportunities__status='imported'),
            distinct=True,
        ),
        health_last_opportunity_at=Max('scraped_opportunities__scraped_at'),
    ).prefetch_related('jobs')
    return [get_source_health(source) for source in queryset]
