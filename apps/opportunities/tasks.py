from celery import shared_task

from .models import Opportunity


@shared_task
def analyze_tor_document(opportunity_id: int):
    try:
        opportunity = Opportunity.objects.get(pk=opportunity_id)
    except Opportunity.DoesNotExist:
        return {'detail': 'Oportunidade nao encontrada.'}

    opportunity.ai_analysis_status = 'processing'
    opportunity.save(update_fields=['ai_analysis_status'])

    # TODO: Integrar com servico de AI para analisar o documento ToR
    # Simulacao de processamento bem-sucedido
    opportunity.ai_analysis_status = 'completed'
    opportunity.save(update_fields=['ai_analysis_status'])

    return {'detail': 'Analise concluida.', 'opportunity_id': opportunity_id}


@shared_task
def check_upcoming_deadlines():
    from django.utils import timezone

    upcoming = Opportunity.objects.filter(
        status__in=['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review'],
        deadline__gte=timezone.now(),
        deadline__lte=timezone.now() + timezone.timedelta(days=7),
    )

    # TODO: Enviar notificacoes por email/push para os utilizadores atribuidos
    count = upcoming.count()
    return {'upcoming_deadlines_count': count}
