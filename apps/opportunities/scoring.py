from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.ai_services.services import AIServiceFactory

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

    strategic_fit = 55
    strategic_reason = 'Base fit from structured opportunity data.'
    if opportunity.ai_summary:
        strategic_fit += 15
        strategic_reason = 'AI summary is available, improving strategic context.'
    if requirements:
        strategic_fit += 10
        strategic_reason += ' Requirements are available for qualification.'

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

    margin = 55
    margin_reason = 'Neutral margin baseline.'
    if opportunity.value and opportunity.value >= 100000:
        margin += 15
        margin_reason = 'Budget is material enough to support pursuit economics.'
    if opportunity.currency and opportunity.currency.upper() not in {'USD', 'EUR'}:
        margin -= 5
        margin_reason += ' Currency may require pricing attention.'

    risk_score = 70
    risk_reason = 'Risk score starts from a moderate-safe baseline.'
    if risks:
        risk_score -= min(35, len(risks) * 7)
        risk_reason = f'{len(risks)} risk item(s) identified.'
    if high_risk_count:
        risk_score -= min(20, high_risk_count * 10)
        risk_reason += f' {high_risk_count} high severity risk(s).'

    resource = 55
    resource_reason = 'Resource score uses available team requirement signals.'
    team_requirements = ai_criteria.get('team_requirements') if isinstance(ai_criteria, dict) else None
    if team_requirements:
        resource += 15
        resource_reason = 'Team requirements are extracted and can guide staffing.'
    if mandatory_count > 8:
        resource -= 10
        resource_reason += ' Many mandatory requirements increase delivery burden.'

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
        'ai_extracted_criteria': ai_criteria if isinstance(ai_criteria, dict) else {},
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
