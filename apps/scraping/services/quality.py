import hashlib
import html
import re
from dataclasses import dataclass, field

from .cos_scope import CONSULTING_SERVICE_TERMS, PROJECT_TYPE_TERMS, STRATEGIC_PRIORITY_TERMS


_NAVIGATION_TITLES = {
    'about',
    'apply',
    'back',
    'contact',
    'download',
    'home',
    'login',
    'log in',
    'menu',
    'more',
    'next',
    'previous',
    'procurement',
    'read more',
    'search',
    'sign in',
    'submit',
    'tenders',
    'view details',
}

_NAVIGATION_PATTERNS = [
    re.compile(r'^(click|read|learn|view)\s+(here|more|details)$', re.I),
    re.compile(r'^(page|p[aá]gina)\s+\d+$', re.I),
    re.compile(r'^\d+\s*(/|of|de)\s*\d+$', re.I),
    re.compile(r'^(previous|next|older|newer)\s+(page|notices|posts)$', re.I),
]

_TITLE_KEYWORDS = {
    'advisory',
    'assessment',
    'bid',
    'call',
    'capacity',
    'consultancy',
    'consultant',
    'contrato',
    'concurso',
    'evaluation',
    'expression',
    'framework',
    'interest',
    'pmo',
    'procurement',
    'proposal',
    'proposals',
    'quotation',
    'services',
    'study',
    'technical',
    'rfp',
    'tender',
    'tenders',
    'training',
}
_TITLE_KEYWORDS.update(
    term.replace('-', ' ').split()[0]
    for term in CONSULTING_SERVICE_TERMS + PROJECT_TYPE_TERMS + STRATEGIC_PRIORITY_TERMS
    if term
)


@dataclass(frozen=True)
class ScrapedItemQuality:
    title: str
    external_id: str
    valid: bool
    rejection_reason: str = ''
    warnings: list[str] = field(default_factory=list)


def normalize_title(value: str | None) -> str:
    text = html.unescape(value or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([,.;:!?])', r'\1', text)
    return text.strip(' -|–—\t\r\n')


def assess_scraped_item(raw_item: dict, source_name: str) -> ScrapedItemQuality:
    title = normalize_title(raw_item.get('title'))
    warnings: list[str] = []
    rejection_reason = _title_rejection_reason(title)

    external_id = str(raw_item.get('external_id') or '').strip()
    if not external_id:
        external_id = _fallback_external_id(raw_item, title, source_name)
        warnings.append('external_id_generated')

    if len(title) > 400:
        title = title[:400].rstrip()
        warnings.append('title_truncated')

    return ScrapedItemQuality(
        title=title,
        external_id=external_id,
        valid=not rejection_reason,
        rejection_reason=rejection_reason,
        warnings=warnings,
    )


def score_quality_adjustment(raw_item: dict, assessment: ScrapedItemQuality) -> float:
    adjustment = 0.0
    if assessment.warnings:
        adjustment -= min(0.10, len(assessment.warnings) * 0.05)
    if not raw_item.get('external_url'):
        adjustment -= 0.05
    if not raw_item.get('country'):
        adjustment -= 0.05
    if not raw_item.get('sector'):
        adjustment -= 0.05
    if raw_item.get('deep_content_text'):
        adjustment += 0.05
    return adjustment


def _title_rejection_reason(title: str) -> str:
    if not title:
        return 'missing_title'

    normalized = title.lower()
    words = re.findall(r'[\wÀ-ÿ]+', normalized)
    letters = re.findall(r'[A-Za-zÀ-ÿ]', title)

    if len(title) < 8:
        return 'title_too_short'
    if len(letters) < 5:
        return 'title_without_words'
    if normalized in _NAVIGATION_TITLES:
        return 'navigation_title'
    if any(pattern.match(title) for pattern in _NAVIGATION_PATTERNS):
        return 'navigation_title'
    if len(words) < 3 and not (_TITLE_KEYWORDS & set(words)):
        return 'title_too_generic'
    if _looks_like_url_or_script(title):
        return 'invalid_title_content'
    return ''


def _fallback_external_id(raw_item: dict, title: str, source_name: str) -> str:
    stable_value = raw_item.get('external_url') or f'{source_name}:{title}'
    digest = hashlib.sha1(str(stable_value).encode('utf-8')).hexdigest()[:16]
    return f'generated-{digest}'


def _looks_like_url_or_script(title: str) -> bool:
    lowered = title.lower()
    return lowered.startswith(('http://', 'https://', 'javascript:')) or 'function(' in lowered
