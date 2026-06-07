from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.ai_services.services import AIServiceFactory
from apps.scraping.services.cos_scope import classify_cos_scope_text
from apps.tenants.intelligence import normalize_mapping, tenant_intelligence_profile, text_matches_any

from .models import Opportunity, OpportunityScore


SCORING_VERSION = 'opportunity_score_v1'


def _clamp(value: int) -> int:
    return max(0, min(100, int(value)))


def _trace(component: str, score: int, reason: str) -> dict:
    return {'component': component, 'score': _clamp(score), 'reason': reason}


def build_opportunity_score_payload(opportunity: Opportunity) -> dict:
    requirements = list(opportunity.requirements.all())
    risks = list(opportunity.risks.all())
    days_left = max(0, (opportunity.deadline - timezone.now()).days) if opportunity.deadline else 0
    mandatory_count = sum(1 for item in requirements if item.priority == 'mandatory')
    high_risk_count = sum(1 for item in risks if item.severity == 'high')
    ai_criteria = opportunity.ai_extraction.get('cos_analysis', {}) if opportunity.ai_extraction else {}
    imported_scope = {}
    if opportunity.ai_extraction:
        imported_scope = (
            opportunity.ai_extraction.get('c3_enrichment', {}).get('cos_scope', {})
            if isinstance(opportunity.ai_extraction.get('c3_enrichment'), dict)
            else {}
        )
    scope_text = ' '.join(filter(None, [
        opportunity.title,
        opportunity.description,
        opportunity.ai_summary,
        opportunity.sector,
        opportunity.country,
        opportunity.region,
    ]))[:12000]
    cos_scope = imported_scope or classify_cos_scope_text(scope_text)
    tenant_profile = tenant_intelligence_profile(opportunity.tenant)
    tenant_keywords = []
    tenant_exclusions = []
    tenant_sector_weight = 0
    tenant_geo_weight = 0
    tenant_donor_weight = 0
    tenant_deadline_fit = True
    tenant_budget_fit = True
    tenant_reason_bits = []

    if tenant_profile:
        tenant_keywords = text_matches_any(scope_text, tenant_profile.opportunity_keywords)
        tenant_exclusions = text_matches_any(scope_text, tenant_profile.excluded_keywords)
        sector_weights = normalize_mapping(tenant_profile.sector_priority_weights)
        geo_weights = normalize_mapping(tenant_profile.geographic_priority_weights)
        donor_weights = normalize_mapping(tenant_profile.donor_priority_weights)
        tenant_sector_weight = int(sector_weights.get(opportunity.sector, 0) or 0)
        tenant_geo_weight = int(geo_weights.get(opportunity.country, 0) or 0)
        tenant_donor_weight = max(
            [int(weight or 0) for donor, weight in donor_weights.items() if str(donor).lower() in scope_text.lower()]
            or [0]
        )
        if tenant_keywords:
            tenant_reason_bits.append(f'{len(tenant_keywords)} tenant keyword match(es).')
        if tenant_exclusions:
            tenant_reason_bits.append(f'{len(tenant_exclusions)} tenant exclusion keyword(s) detected.')
        if tenant_sector_weight:
            tenant_reason_bits.append('Sector matches tenant priorities.')
        if tenant_geo_weight:
            tenant_reason_bits.append('Geography matches tenant priorities.')
        if tenant_donor_weight:
            tenant_reason_bits.append('Donor/client matches tenant priorities.')
        if tenant_profile.deadline_min_days is not None and days_left < tenant_profile.deadline_min_days:
            tenant_deadline_fit = False
        if tenant_profile.deadline_max_days is not None and days_left > tenant_profile.deadline_max_days:
            tenant_deadline_fit = False
        if tenant_profile.minimum_budget is not None and opportunity.value < tenant_profile.minimum_budget:
            tenant_budget_fit = False
        if tenant_profile.maximum_budget is not None and opportunity.value > tenant_profile.maximum_budget:
            tenant_budget_fit = False

    strategic_fit = 55
    strategic_reason = 'Base fit from structured opportunity data.'
    if opportunity.ai_summary:
        strategic_fit += 15
        strategic_reason = 'AI summary is available, improving strategic context.'
    if requirements:
        strategic_fit += 10
        strategic_reason += ' Requirements are available for qualification.'
    if cos_scope.get('relevance') in ('high', 'strategic'):
        strategic_fit += 15
        strategic_reason += ' COS scope classifies the opportunity as high/strategic.'
    elif cos_scope.get('is_consulting_relevant'):
        strategic_fit += 8
        strategic_reason += ' COS scope detects consulting/technical assistance relevance.'
    if tenant_profile:
        strategic_fit += min(20, len(tenant_keywords) * 4)
        strategic_fit += min(12, tenant_sector_weight // 10)
        strategic_fit += min(12, tenant_geo_weight // 10)
        strategic_fit += min(8, tenant_donor_weight // 12)
        if tenant_exclusions:
            strategic_fit -= min(30, len(tenant_exclusions) * 10)
        if not tenant_budget_fit:
            strategic_fit -= 10
        if tenant_reason_bits:
            strategic_reason += ' Tenant context: ' + ' '.join(tenant_reason_bits)

    win_probability = 50
    win_reason = 'Neutral win probability baseline.'
    if mandatory_count:
        win_probability += min(20, mandatory_count * 4)
        win_reason = f'{mandatory_count} mandatory requirement(s) identified.'
    if days_left < 7:
        win_probability -= 15
        win_reason += ' Deadline pressure is high.'
    elif days_left >= 21:
        win_probability += 10
        win_reason += ' Deadline allows preparation time.'
    if cos_scope.get('is_geographic_priority'):
        win_probability += 5
        win_reason += ' Priority geography improves positioning potential.'
    if tenant_profile:
        if tenant_geo_weight:
            win_probability += min(10, tenant_geo_weight // 10)
        if not tenant_deadline_fit:
            win_probability -= 15
            win_reason += ' Deadline is outside tenant preference window.'

    margin = 55
    margin_reason = 'Neutral margin baseline.'
    if opportunity.value and opportunity.value >= 100000:
        margin += 15
        margin_reason = 'Budget is material enough to support pursuit economics.'
    if opportunity.currency and opportunity.currency.upper() not in {'USD', 'EUR'}:
        margin -= 5
        margin_reason += ' Currency may require pricing attention.'
    if cos_scope.get('project_type_matches'):
        margin += 5
        margin_reason += ' Project type fits consulting delivery economics.'
    if tenant_profile and not tenant_budget_fit:
        margin -= 15
        margin_reason += ' Budget is outside tenant preference window.'

    risk_score = 70
    risk_reason = 'Risk score starts from a moderate-safe baseline.'
    if risks:
        risk_score -= min(35, len(risks) * 7)
        risk_reason = f'{len(risks)} risk item(s) identified.'
    if high_risk_count:
        risk_score -= min(20, high_risk_count * 10)
        risk_reason += f' {high_risk_count} high severity risk(s).'
    if cos_scope.get('low_relevance_matches'):
        risk_score -= 15
        risk_reason += ' Low-relevance goods/works language detected.'
    if tenant_profile and tenant_exclusions:
        risk_score -= min(25, len(tenant_exclusions) * 8)
        risk_reason += ' Tenant exclusion terms increase no-go risk.'

    resource = 55
    resource_reason = 'Resource score uses available team requirement signals.'
    team_requirements = ai_criteria.get('team_requirements') if isinstance(ai_criteria, dict) else None
    if team_requirements:
        resource += 15
        resource_reason = 'Team requirements are extracted and can guide staffing.'
    if cos_scope.get('consulting_matches'):
        resource += 5
        resource_reason += ' Consulting scope is explicit enough to guide capture.'
    if mandatory_count > 8:
        resource -= 10
        resource_reason += ' Many mandatory requirements increase delivery burden.'
    if tenant_profile and tenant_profile.requires_local_partner and opportunity.consortium_type == 'solo':
        resource -= 8
        resource_reason += ' Tenant profile expects local partner support.'

    components = {
        'strategic_fit': _clamp(strategic_fit),
        'win_probability': _clamp(win_probability),
        'margin': _clamp(margin),
        'risk': _clamp(risk_score),
        'resource': _clamp(resource),
    }
    weights = {
        'strategic_fit': 25,
        'win_probability': 25,
        'margin': 15,
        'risk': 20,
        'resource': 15,
    }
    if tenant_profile and tenant_profile.scoring_weights:
        for key, value in tenant_profile.scoring_weights.items():
            if key in weights:
                try:
                    weights[key] = max(0, int(value))
                except (TypeError, ValueError):
                    continue
    if sum(weights.values()) <= 0:
        weights = {
            'strategic_fit': 25,
            'win_probability': 25,
            'margin': 15,
            'risk': 20,
            'resource': 15,
        }
    overall = round(
        sum(components[key] * weights[key] for key in components) / sum(weights.values())
    )
    confidence = Decimal('0.55')
    if requirements:
        confidence += Decimal('0.15')
    if risks:
        confidence += Decimal('0.10')
    if opportunity.ai_extraction:
        confidence += Decimal('0.10')
    confidence = min(confidence, Decimal('0.95'))

    service_info = AIServiceFactory.get_provider_info()
    return {
        **components,
        'overall_score': _clamp(overall),
        'confidence_score': confidence,
        'ai_extracted_criteria': {
            **(ai_criteria if isinstance(ai_criteria, dict) else {}),
            'cos_scope': cos_scope,
        },
        'evaluation_weights': weights,
        'reasoning_trace': [
            _trace('strategic_fit', components['strategic_fit'], strategic_reason),
            _trace('win_probability', components['win_probability'], win_reason),
            _trace('margin', components['margin'], margin_reason),
            _trace('risk', components['risk'], risk_reason),
            _trace('resource', components['resource'], resource_reason),
        ],
        'input_snapshot': {
            'opportunity_id': opportunity.id,
            'status': opportunity.status,
            'sector': opportunity.sector,
            'country': opportunity.country,
            'value': str(opportunity.value),
            'currency': opportunity.currency,
            'days_left': days_left,
            'requirements_count': len(requirements),
            'mandatory_requirements_count': mandatory_count,
            'risks_count': len(risks),
            'high_risks_count': high_risk_count,
            'has_ai_extraction': bool(opportunity.ai_extraction),
            'cos_scope_relevance': cos_scope.get('relevance', ''),
            'cos_scope_score': cos_scope.get('overall_score', 0),
            'tenant_id': str(opportunity.tenant_id) if opportunity.tenant_id else '',
            'tenant_profile_applied': bool(tenant_profile),
            'tenant_keyword_matches': tenant_keywords,
            'tenant_exclusion_matches': tenant_exclusions,
            'tenant_minimum_score_threshold': (
                tenant_profile.minimum_score_threshold if tenant_profile else None
            ),
        },
        'provider': service_info.get('provider', 'deterministic'),
        'model': service_info.get('model', ''),
        'scoring_version': SCORING_VERSION,
        'is_current': True,
    }


@transaction.atomic
def score_opportunity(opportunity: Opportunity) -> OpportunityScore:
    OpportunityScore.objects.filter(opportunity=opportunity, is_current=True).update(is_current=False)
    payload = build_opportunity_score_payload(opportunity)
    return OpportunityScore.objects.create(opportunity=opportunity, **payload)
