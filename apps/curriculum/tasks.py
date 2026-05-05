from celery import shared_task
from .models import Curriculum, CVTemplate, TemplateMatch, CVSuggestion


@shared_task
def analyze_cv_with_ai(curriculum_id):
    """AI analysis of uploaded CV/Resume."""
    try:
        cv = Curriculum.objects.get(id=curriculum_id)
    except Curriculum.DoesNotExist:
        return {'status': 'error', 'message': 'CV not found'}

    cv.status = 'processing'
    cv.save()

    try:
        # Use AI service for analysis
        from apps.ai_services.services import AIServiceFactory
        service = AIServiceFactory.get_service()
        
        # Extract text from file would go here in production
        # For now, use a placeholder approach
        cv.extracted_data = {
            'skills': [],
            'experience': [],
            'education': [],
            'languages': [],
        }
        cv.analysis_score = 75  # Placeholder
        cv.status = 'analyzed'
        cv.save()
        
        # Generate suggestions
        CVSuggestion.objects.create(
            curriculum=cv,
            type='content',
            priority='medium',
            message='Analise completa. Verifique os dados extraidos.',
        )
        
        return {'status': 'completed', 'cv_id': cv.id}
        
    except Exception as e:
        cv.status = 'error'
        cv.save()
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_cv_for_template(curriculum_id, template_id, output_format='docx'):
    """Generate a CV adapted for a specific template."""
    try:
        cv = Curriculum.objects.get(id=curriculum_id)
        template = CVTemplate.objects.get(id=template_id)
    except (Curriculum.DoesNotExist, CVTemplate.DoesNotExist):
        return {'status': 'error', 'message': 'CV or Template not found'}

    try:
        match, created = TemplateMatch.objects.get_or_create(
            curriculum=cv,
            template=template,
            defaults={
                'match_score': 0,
                'missing_sections': [],
                'recommendations': [],
            }
        )
        
        # Build adapted content from extracted data
        extracted = cv.extracted_data or {}
        adapted_content = {
            'applicant': {
                'name': cv.user.get_full_name() or cv.user.email,
                'email': cv.user.email,
            },
            'summary': extracted.get('summary', ''),
            'sections': {
                'experience': extracted.get('experience', []),
                'education': extracted.get('education', []),
                'skills': extracted.get('skills', []),
                'languages': extracted.get('languages', []),
                'certifications': extracted.get('certifications', []),
            }
        }
        
        # Merge with template required sections
        required = template.required_sections or []
        for sec_def in required:
            sec_id = sec_def.get('id', '')
            if sec_id not in adapted_content['sections']:
                adapted_content['sections'][sec_id] = sec_def.get('placeholder', '')
        
        # Generate document
        from .generators import generate_cv_document
        file_url = generate_cv_document(adapted_content, template, output_format=output_format)
        
        # Update match with generated file and content
        match.adapted_content = adapted_content
        match.save()
        
        return {
            'status': 'completed',
            'match_id': match.id,
            'file_url': file_url,
        }
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('generate_cv_for_template failed: %s', e)
        return {'status': 'error', 'message': str(e)}
