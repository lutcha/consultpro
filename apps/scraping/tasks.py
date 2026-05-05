from celery import shared_task
from django.utils import timezone
from .models import ScrapingSource, ScrapedOpportunity, ScrapingJob


@shared_task
def run_scraping_source(source_id):
    """Execute web scraping for a specific source."""
    try:
        source = ScrapingSource.objects.get(id=source_id)
    except ScrapingSource.DoesNotExist:
        return {'status': 'error', 'message': 'Source not found'}

    job = ScrapingJob.objects.create(
        source=source,
        status='running',
        started_at=timezone.now(),
        executed_by='scheduler',
    )

    try:
        # Placeholder for actual scraping logic
        # In production, this would call the appropriate scraper class
        # based on source.scraper_class and source.scraper_config
        
        job.status = 'completed'
        job.completed_at = timezone.now()
        source.last_scraped_at = timezone.now()
        source.error_message = ''
        source.save()
        
    except Exception as e:
        job.status = 'failed'
        job.error_log = str(e)
        job.completed_at = timezone.now()
        source.error_message = str(e)
        source.status = 'error'
        source.save()
    
    job.save()
    return {'status': job.status, 'job_id': job.id}


@shared_task
def run_all_scraping_sources():
    """Run scraping for all active sources."""
    active_sources = ScrapingSource.objects.filter(status='active')
    for source in active_sources:
        run_scraping_source.delay(source.id)
    return {'status': 'queued', 'sources_count': active_sources.count()}
