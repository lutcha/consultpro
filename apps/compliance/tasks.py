from celery import shared_task

from .services import generate_compliance_matrix


@shared_task(bind=True, max_retries=2)
def generate_compliance_matrix_task(self, opportunity_id):
    try:
        matrix = generate_compliance_matrix(opportunity_id)
        return {'matrix_id': matrix.id, 'opportunity_id': matrix.opportunity_id, 'rows': matrix.rows.count()}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
