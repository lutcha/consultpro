import json
import logging

from celery import shared_task

from .models import Curriculum, CVSuggestion

logger = logging.getLogger(__name__)


# ── Text extraction ──────────────────────────────────────────────────────────

def _extract_text(curriculum) -> str:
    if not curriculum.file:
        return ''
    try:
        file_path = curriculum.file.path
        if curriculum.file_type == 'pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        if curriculum.file_type in ('docx', 'doc'):
            from docx import Document
            doc = Document(file_path)
            return '\n'.join(p.text for p in doc.paragraphs)
    except Exception as exc:
        logger.warning('Text extraction failed for CV %s: %s', curriculum.id, exc)
    return ''


# ── Scoring ──────────────────────────────────────────────────────────────────

def _compute_score(data: dict) -> int:
    score = 0
    if data.get('name'):    score += 10
    if data.get('email'):   score += 5
    if data.get('phone'):   score += 3
    if data.get('location'): score += 2
    if data.get('summary'): score += 15
    exp = data.get('experience', [])
    score += 20 if len(exp) >= 3 else (12 if len(exp) >= 1 else 0)
    edu = data.get('education', [])
    score += 15 if len(edu) >= 2 else (8 if len(edu) >= 1 else 0)
    skills = data.get('skills', [])
    score += 15 if len(skills) >= 10 else (8 if len(skills) >= 5 else 0)
    langs = data.get('languages', [])
    score += 10 if len(langs) >= 3 else (5 if len(langs) >= 1 else 0)
    if data.get('certifications'): score += 5
    if data.get('publications'):   score += 5
    return min(score, 100)


# ── Suggestions ──────────────────────────────────────────────────────────────

def _generate_suggestions(cv, data: dict):
    CVSuggestion.objects.filter(curriculum=cv).delete()
    items = []

    if not data.get('summary'):
        items.append(CVSuggestion(
            curriculum=cv, type='missing_section', priority='high',
            message='Adicionar sumario profissional no inicio do CV (2-3 frases sobre expertise e objetivos).',
            auto_fixable=False,
        ))

    skills = data.get('skills', [])
    if len(skills) < 5:
        items.append(CVSuggestion(
            curriculum=cv, type='content', priority='high',
            message=f'Identificadas apenas {len(skills)} skills. Expandir para 8-10 competencias tecnicas e transversais.',
            auto_fixable=False,
        ))

    langs = data.get('languages', [])
    if len(langs) < 2:
        items.append(CVSuggestion(
            curriculum=cv, type='missing_section', priority='medium',
            message='Adicionar secao de idiomas com nivel de proficiencia (nativo, fluente, intermedio, basico).',
            auto_fixable=False,
        ))

    if not data.get('certifications'):
        items.append(CVSuggestion(
            curriculum=cv, type='content', priority='medium',
            message='Adicionar certificacoes relevantes (PMP, M&E, formacoes especializadas).',
            auto_fixable=False,
        ))

    exp = data.get('experience', [])
    if len(exp) < 2:
        items.append(CVSuggestion(
            curriculum=cv, type='content', priority='high',
            message='Detalhar experiencia profissional com organizacao, periodo e descricao de responsabilidades.',
            auto_fixable=False,
        ))

    if not data.get('education'):
        items.append(CVSuggestion(
            curriculum=cv, type='missing_section', priority='medium',
            message='Adicionar formacao academica com instituicao e datas.',
            auto_fixable=False,
        ))

    if items:
        CVSuggestion.objects.bulk_create(items)


# ── AI extraction ─────────────────────────────────────────────────────────────

_CV_SYSTEM_PROMPT = (
    "You are an expert CV analyst for international development consultants. "
    "Extract structured information from the CV text. "
    "Return valid JSON (no markdown fences) with keys: "
    "name (string), email (string), phone (string), location (string), summary (string), "
    "experience (array of {title, organization, dateRange, description}), "
    "education (array of {title, organization, dateRange}), "
    "skills (array of strings), languages (array of strings with proficiency level), "
    "certifications (array of strings), publications (array of strings). "
    "Use empty string or empty array for missing fields."
)


def _ai_extract(text: str) -> dict:
    from apps.ai_services.services import AIServiceFactory
    service = AIServiceFactory.get_service()
    user_msg = f"Extract structured information from this CV:\n\n{text[:8000]}"

    try:
        if hasattr(service, '_chat_completion'):
            raw = service._chat_completion(
                messages=[
                    {'role': 'system', 'content': _CV_SYSTEM_PROMPT},
                    {'role': 'user', 'content': user_msg},
                ],
                temperature=0.1,
                json_mode=True,
            )
        elif hasattr(service, '_messages_create'):
            raw = service._messages_create(
                system_prompt=_CV_SYSTEM_PROMPT,
                user_prompt=user_msg,
                temperature=0.1,
            )
        else:
            return {}

        raw = service._clean_json_response(raw)
        return json.loads(raw)

    except Exception as exc:
        logger.warning('CV AI extraction failed: %s', exc)
        return {}


# ── Main task ─────────────────────────────────────────────────────────────────

@shared_task
def analyze_cv_with_ai(curriculum_id):
    try:
        cv = Curriculum.objects.get(id=curriculum_id)
    except Curriculum.DoesNotExist:
        return {'status': 'error', 'message': 'CV not found'}

    cv.status = 'processing'
    cv.save()

    try:
        text = _extract_text(cv)
        extracted = _ai_extract(text) if text.strip() else {}

        for key in ('skills', 'experience', 'education', 'languages', 'certifications', 'publications'):
            extracted.setdefault(key, [])

        cv.extracted_data = extracted
        cv.analysis_score = _compute_score(extracted)
        cv.status = 'analyzed'
        cv.save()

        _generate_suggestions(cv, extracted)
        return {'status': 'completed', 'cv_id': cv.id}

    except Exception as exc:
        logger.exception('analyze_cv_with_ai failed: %s', exc)
        cv.status = 'error'
        cv.save()
        return {'status': 'error', 'message': str(exc)}


@shared_task
def generate_cv_for_template(curriculum_id, template_id, output_format='docx'):
    from .models import CVTemplate, TemplateMatch

    try:
        cv = Curriculum.objects.get(id=curriculum_id)
        template = CVTemplate.objects.get(id=template_id)
    except (Curriculum.DoesNotExist, CVTemplate.DoesNotExist):
        return {'status': 'error', 'message': 'CV or Template not found'}

    try:
        match, _ = TemplateMatch.objects.get_or_create(
            curriculum=cv,
            template=template,
            defaults={'match_score': 0, 'missing_sections': [], 'recommendations': []},
        )

        extracted = cv.extracted_data or {}
        adapted_content = {
            'applicant': {'name': cv.user.get_full_name() or cv.user.email, 'email': cv.user.email},
            'summary': extracted.get('summary', ''),
            'sections': {
                'experience': extracted.get('experience', []),
                'education': extracted.get('education', []),
                'skills': extracted.get('skills', []),
                'languages': extracted.get('languages', []),
                'certifications': extracted.get('certifications', []),
            },
        }

        required = template.required_sections or []
        for sec_def in required:
            sec_id = sec_def.get('id', '')
            if sec_id not in adapted_content['sections']:
                adapted_content['sections'][sec_id] = sec_def.get('placeholder', '')

        from .generators import generate_cv_document
        generate_cv_document(adapted_content, template, output_format=output_format)

        match.adapted_content = adapted_content
        match.save()
        return {'status': 'completed', 'match_id': match.id}

    except Exception as exc:
        logger.exception('generate_cv_for_template failed: %s', exc)
        return {'status': 'error', 'message': str(exc)}
