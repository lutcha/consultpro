from celery import shared_task

from .export_execution import execute_export_request


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def execute_proposal_export_request(self, export_request_id, force=False):
    try:
        execute_export_request(export_request_id, task_id=self.request.id or '', force=force)
    except Exception as exc:
        raise self.retry(exc=exc)
