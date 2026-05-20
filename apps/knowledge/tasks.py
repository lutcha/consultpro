from celery import shared_task

from .services import run_knowledge_reindex


@shared_task(bind=True, max_retries=2)
def index_knowledge_assets_task(self, source='all'):
    run = run_knowledge_reindex(source=source, celery_task_id=self.request.id or '')
    return run.as_dict()
