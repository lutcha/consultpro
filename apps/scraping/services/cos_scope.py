"""
COS opportunity capture scope.

Centralizes the additive consulting/business-development intelligence rules used
by scraping, import enrichment, source setup, and opportunity scoring.
"""
from __future__ import annotations

from collections.abc import Iterable
import copy


GEOGRAPHIC_PRIORITY_TERMS = [
    'cabo verde', 'cape verde', 'cap verde', 'praia', 'mindelo',
    'guinea-bissau', 'guinea bissau', 'guine-bissau', 'guine bissau',
    'senegal', 'ghana', 'gana', 'ecowas', 'cedeao', 'west africa',
    'western africa', 'africa ocidental', 'lusophone africa', 'africa lusofona',
    'lusofono', 'palop', 'cplp', 'small island developing states', 'sids',
    'island states', 'africa-wide', 'regional africa',
]

GEOGRAPHIC_PRIORITY_FILTERS = [
    'CPV', 'Cabo Verde', 'Cape Verde', 'GNB', 'Guinea-Bissau', 'SEN', 'Senegal',
    'GHA', 'Ghana', 'ECOWAS', 'West Africa', 'Lusophone Africa', 'PALOP',
    'SIDS', 'Africa',
]

CONSULTING_SERVICE_TERMS = [
    'consulting services', 'consultancy', 'consultant', 'advisory services',
    'technical assistance', 'institutional support', 'policy support',
    'implementation support', 'project implementation support',
    'capacity building', 'capacity development', 'training services',
    'coaching', 'mentoring', 'facilitation', 'knowledge management',
    'research', 'study', 'studies', 'diagnostic', 'assessment',
    'feasibility study', 'baseline study', 'evaluation', 'impact assessment',
    'monitoring and evaluation', 'monitoring & evaluation', 'm&e',
    'project management', 'pmo', 'xmo', 'governance support',
    'framework contract', 'long-term service contract',
]

STRATEGIC_PRIORITY_TERMS = [
    'digital transformation', 'govtech', 'ai', 'artificial intelligence',
    'data project', 'data analytics', 'smart government',
    'digital public infrastructure', 'ict policy', 'digital literacy',
    'digital skills', 'innovation ecosystem', 'automation', 'ai governance',
    'cybersecurity', 'interoperability', 'digital services',
    'entrepreneurship', 'startup ecosystem', 'incubation', 'acceleration',
    'sme development', 'msme development', 'private sector development',
    'investment promotion', 'export promotion', 'trade facilitation',
    'competitiveness', 'industrial development', 'value chain',
    'local economic development', 'tourism development', 'blue economy',
    'creative economy', 'financial inclusion',
    'public sector reform', 'public administration modernization',
    'e-government', 'public financial management', 'macroeconomic reform',
    'statistics system', 'institutional strengthening', 'anti-corruption',
    'transparency', 'accountability', 'procurement reform',
    'regulatory reform', 'justice sector reform', 'security sector',
    'education', 'tvet', 'vocational training', 'employment',
    'youth empowerment', 'youth employment', 'gender equality',
    'social protection', 'health systems strengthening', 'inclusion',
    'migration', 'human development', 'community development',
    'climate resilience', 'green economy', 'renewable energy',
    'energy transition', 'sustainability', 'environmental governance',
    'biodiversity', 'circular economy', 'waste management',
    'climate finance', 'carbon reduction', 'resilience program',
    'rural development', 'agri-business', 'agribusiness', 'food security',
    'fisheries', 'livestock', 'irrigation', 'agricultural value chain',
    'climate-smart agriculture', 'rural entrepreneurship',
    'transport system', 'logistics', 'mobility', 'urban planning',
    'infrastructure governance', 'ports', 'maritime', 'aviation',
    'smart cities', 'donor-funded', 'eu-funded', 'world bank',
    'afdb', 'un-funded', 'gcf-funded', 'blended finance',
    'development finance', 'grants management', 'investment readiness',
    'public-private partnership', 'ppp',
]

PROJECT_TYPE_TERMS = [
    'technical assistance project', 'framework contract',
    'long-term service contract', 'institutional support project',
    'reform program', 'policy implementation', 'capacity building program',
    'consulting assignment', 'study', 'assessment', 'implementation support',
    'donor program management', 'request for proposal',
    'expression of interest', 'request for expressions of interest',
    'call for proposals', 'terms of reference',
]

LOW_RELEVANCE_PROCUREMENT_TERMS = [
    'supply of goods', 'goods procurement', 'office supplies',
    'vehicles', 'vehicle supply', 'construction works only',
    'civil works only', 'equipment supply only',
]

SOURCE_SCOPE_KEYWORDS = sorted(set(
    CONSULTING_SERVICE_TERMS + STRATEGIC_PRIORITY_TERMS + PROJECT_TYPE_TERMS
))

SOURCE_SCOPE_SECTORS = [
    'governance', 'public sector reform', 'digital transformation', 'govtech',
    'ai and data', 'innovation', 'private sector development', 'msme',
    'entrepreneurship', 'climate resilience', 'renewable energy',
    'blue economy', 'education', 'tvet', 'youth employment', 'gender',
    'monitoring and evaluation', 'capacity building', 'research',
    'agriculture', 'rural development', 'transport', 'logistics',
    'development finance', 'ppp',
]

LIMITED_ACCESS_ACTIONS = [
    'Classify visible title and metadata as Partial Intelligence.',
    'Estimate country, sector, donor, and strategic relevance from visible text.',
    'Capture intelligence gaps before any GO recommendation.',
    'Recommend local partner/contact follow-up to obtain documents and eligibility details.',
]


def _contains_any(text: str, terms: Iterable[str]) -> list[str]:
    low = (text or '').lower()
    return [term for term in terms if term in low]


def classify_cos_scope_text(text: str) -> dict:
    """Return COS scope matches and simple 0-100 relevance signals."""
    consulting_hits = _contains_any(text, CONSULTING_SERVICE_TERMS)
    strategic_hits = _contains_any(text, STRATEGIC_PRIORITY_TERMS)
    project_hits = _contains_any(text, PROJECT_TYPE_TERMS)
    geographic_hits = _contains_any(text, GEOGRAPHIC_PRIORITY_TERMS)
    low_relevance_hits = _contains_any(text, LOW_RELEVANCE_PROCUREMENT_TERMS)

    consulting_score = min(100, len(consulting_hits) * 25 + len(project_hits) * 15)
    strategic_score = min(100, len(strategic_hits) * 18)
    geographic_score = min(100, len(geographic_hits) * 25)
    penalty = min(50, len(low_relevance_hits) * 20)
    overall = max(0, min(100, round(
        (20 if consulting_hits or project_hits else 0)
        + min(35, len(consulting_hits) * 15 + len(project_hits) * 10)
        + min(25, len(strategic_hits) * 8)
        + min(30, len(geographic_hits) * 15)
        - penalty
    )))

    if overall >= 75:
        relevance = 'strategic'
    elif overall >= 55:
        relevance = 'high'
    elif overall >= 30:
        relevance = 'medium'
    else:
        relevance = 'low'

    return {
        'overall_score': overall,
        'relevance': relevance,
        'consulting_score': consulting_score,
        'strategic_score': strategic_score,
        'geographic_score': geographic_score,
        'consulting_matches': consulting_hits[:12],
        'strategic_matches': strategic_hits[:12],
        'project_type_matches': project_hits[:12],
        'geographic_matches': geographic_hits[:12],
        'low_relevance_matches': low_relevance_hits[:8],
        'is_consulting_relevant': bool(consulting_hits or project_hits),
        'is_geographic_priority': bool(geographic_hits),
    }


def enrich_source_definition(source: dict) -> dict:
    """
    Add COS scope filters/config to a source without deleting existing values.
    """
    enriched = copy.deepcopy(source)
    filters = dict(enriched.get('filters') or {})
    config = dict(enriched.get('scraper_config') or {})

    filters['countries'] = sorted(set(filters.get('countries', []) + GEOGRAPHIC_PRIORITY_FILTERS))
    filters['keywords'] = sorted(set(filters.get('keywords', []) + SOURCE_SCOPE_KEYWORDS))
    filters['sectors'] = sorted(set(filters.get('sectors', []) + SOURCE_SCOPE_SECTORS))
    filters['opportunity_scope'] = 'cos_international_consulting_technical_assistance'
    filters['strategic_filtering'] = {
        'prioritize_consulting_services': True,
        'prioritize_geographies': GEOGRAPHIC_PRIORITY_FILTERS,
        'ignore_low_relevance_goods_where_detected': True,
    }

    access = config.get('access') or next(iter(filters.get('access', []) or []), '')
    if access in {'subscription', 'restricted_login', 'limited', 'bot_challenge', 'robots_disallowed'}:
        config['intelligence_mode'] = 'partial_intelligence'
        config['limited_access_actions'] = LIMITED_ACCESS_ACTIONS
        filters['partial_intelligence'] = True

    enriched['filters'] = filters
    enriched['scraper_config'] = config
    return enriched


def enrich_source_definitions(sources: list[dict]) -> list[dict]:
    return [enrich_source_definition(source) for source in sources]
