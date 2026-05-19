from celery import shared_task

from .services import create_issue_tree_snapshot, generate_issue_tree


@shared_task(bind=True, max_retries=2)
def generate_issue_tree_task(self, proposal_id):
    return generate_issue_tree(proposal_id).id


@shared_task(bind=True, max_retries=2)
def create_issue_tree_snapshot_task(self, proposal_id, label=''):
    return create_issue_tree_snapshot(proposal_id, label=label).id
