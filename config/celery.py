"""
Celery configuration for ConsultPro project.
"""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('config')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.update(
    # Per-task rate limits (1 req / 1.5s effective for scraping tasks)
    task_annotations={
        'apps.scraping.tasks.run_scraping_source': {
            'rate_limit': '40/m',      # ~1 per 1.5s
            'max_retries': 3,
            'default_retry_delay': 60,
        },
    },
    # Worker-level concurrency: 1 for scraping to respect domain rate limits
    worker_concurrency=2,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Persistent results for 24h
    result_expires=86400,
)
