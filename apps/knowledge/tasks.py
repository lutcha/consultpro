from celery import shared_task

from .services import index_knowledge_assets


@shared_task(bind=True, max_retries=2)
def index_knowledge_assets_task(self, source='all'):
    return len(index_knowledge_assets(source=source))
