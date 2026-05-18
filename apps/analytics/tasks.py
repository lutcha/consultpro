from celery import shared_task

from .services import get_or_compute_predictive_metric


@shared_task(bind=True, max_retries=2)
def compute_predictive_metrics_task(self, country=None, sector=None, horizon=3):
    try:
        result = get_or_compute_predictive_metric(
            country=country,
            sector=sector,
            horizon=horizon,
            force_refresh=True,
        )
        return {
            'country': country or '',
            'sector': sector or '',
            'horizon': horizon,
            'cache_status': result.get('cache_status'),
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
