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

    # AI service integration
    from apps.ai_services.services import AIServiceFactory
    service = AIServiceFactory.get_service()
    
    # Extract text from ToR document if available
    tor_text = ''
    if opportunity.tor_document:
        try:
            import io
            from docx import Document
            doc = Document(opportunity.tor_document.path)
            tor_text = '\n'.join([para.text for para in doc.paragraphs])
        except Exception:
            tor_text = opportunity.description or ''
    else:
        tor_text = opportunity.description or ''
    
    if tor_text:
        result = service.analyze_document(tor_text)
        opportunity.ai_summary = result.get('summary', '')
        opportunity.save(update_fields=['ai_analysis_status', 'ai_summary'])
    else:
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
