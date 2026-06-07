from __future__ import annotations

from decimal import Decimal, InvalidOperation


def normalize_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, (tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(',') if part.strip()]
    return [str(value).strip()] if str(value).strip() else []


def normalize_mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def normalize_decimal(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def weighted_codes(codes: list, default_weight: int = 80) -> dict:
    return {code: default_weight for code in normalize_list(codes)}


def text_matches_any(text: str, terms: list) -> list:
    lowered = (text or '').lower()
    return [term for term in normalize_list(terms) if term.lower() in lowered]


def tenant_intelligence_profile(tenant):
    if not tenant:
        return None
    try:
        from .models import TenantIntelligenceProfile

        return TenantIntelligenceProfile.objects.filter(tenant=tenant).first()
    except Exception:
        return None


def build_saved_filter_payload(intelligence_profile) -> dict:
    if not intelligence_profile:
        return {}
    payload = {}
    sectors = list(normalize_mapping(intelligence_profile.sector_priority_weights).keys())
    countries = list(normalize_mapping(intelligence_profile.geographic_priority_weights).keys())
    if sectors:
        payload['sector__in'] = sectors
    if countries:
        payload['country__in'] = countries
    if intelligence_profile.minimum_budget:
        payload['value__gte'] = str(intelligence_profile.minimum_budget)
    if intelligence_profile.maximum_budget:
        payload['value__lte'] = str(intelligence_profile.maximum_budget)
    if intelligence_profile.minimum_score_threshold:
        payload['minimum_score_threshold'] = intelligence_profile.minimum_score_threshold
    keywords = normalize_list(intelligence_profile.opportunity_keywords)
    if keywords:
        payload['search'] = ' '.join(keywords[:6])
    return payload
