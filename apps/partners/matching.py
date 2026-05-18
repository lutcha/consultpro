from __future__ import annotations

from dataclasses import dataclass

from apps.opportunities.models import Opportunity
from apps.users.models import User

from .models import PartnerProfile


@dataclass(frozen=True)
class MatchResult:
    id: int
    name: str
    score: int
    confidence_score: int
    reasoning_trace: list[str]
    metadata: dict


def _normalize_list(values) -> set[str]:
    return {str(value).strip().lower() for value in values or [] if str(value).strip()}


def _contains_token(values, token: str) -> bool:
    normalized = _normalize_list(values)
    return token.lower() in normalized


def suggest_partners(opportunity: Opportunity, limit: int = 5) -> list[MatchResult]:
    results: list[MatchResult] = []
    sector = (opportunity.sector or '').lower()
    country = (opportunity.country or '').lower()
    region = (opportunity.region or '').lower()

    for partner in PartnerProfile.objects.filter(is_active=True):
        score = int(partner.trust_score or 0)
        trace = [f'Trust score base: {score}/100.']

        if sector and _contains_token(partner.sectors, sector):
            score += 25
            trace.append(f'Sector match: {opportunity.sector}.')
        if country and _contains_token(partner.geographies, country):
            score += 20
            trace.append(f'Country match: {opportunity.country}.')
        elif region and _contains_token(partner.geographies, region):
            score += 12
            trace.append(f'Region match: {opportunity.region}.')
        if partner.capabilities:
            score += min(10, len(partner.capabilities) * 2)
            trace.append(f'Capabilities available: {", ".join(partner.capabilities[:4])}.')

        if len(trace) == 1:
            trace.append('No direct sector/geography match; retained as low-priority option.')

        results.append(
            MatchResult(
                id=partner.id,
                name=partner.name,
                score=min(score, 100),
                confidence_score=70 if len(trace) > 2 else 45,
                reasoning_trace=trace,
                metadata={
                    'sectors': partner.sectors,
                    'geographies': partner.geographies,
                    'capabilities': partner.capabilities,
                    'linkedin_url': partner.linkedin_url,
                    'website_url': partner.website_url,
                    'trust_score': partner.trust_score,
                },
            )
        )

    return sorted(results, key=lambda item: (item.score, item.confidence_score), reverse=True)[:limit]


def suggest_consultants(opportunity: Opportunity, limit: int = 5) -> list[MatchResult]:
    results: list[MatchResult] = []
    sector = (opportunity.sector or '').lower()
    country = (opportunity.country or '').lower()
    region = (opportunity.region or '').lower()

    consultants = User.objects.filter(role='consultant', is_active=True)
    for consultant in consultants:
        score = 35
        trace = ['Consultant role and active account confirmed.']

        if consultant.availability == 'available':
            score += 20
            trace.append('Availability match: available.')
        elif consultant.availability == 'busy':
            score += 8
            trace.append('Availability is busy; possible with planning.')
        else:
            trace.append('Availability is unavailable; low-priority suggestion.')

        skills = _normalize_list(consultant.skills)
        languages = _normalize_list(consultant.languages)
        location = (consultant.location or '').lower()
        if sector and (sector in skills or sector.replace('_', ' ') in skills):
            score += 25
            trace.append(f'Skill match for sector: {opportunity.sector}.')
        if country and country in location:
            score += 10
            trace.append(f'Location mentions country: {opportunity.country}.')
        elif region and region in location:
            score += 6
            trace.append(f'Location mentions region: {opportunity.region}.')
        if languages:
            score += min(10, len(languages) * 3)
            trace.append(f'Languages available: {", ".join(sorted(languages)[:4])}.')
        if consultant.years_experience:
            score += min(10, consultant.years_experience)
            trace.append(f'Experience: {consultant.years_experience} years.')

        results.append(
            MatchResult(
                id=consultant.id,
                name=consultant.get_full_name() or consultant.username,
                score=min(score, 100),
                confidence_score=65 if score >= 70 else 50,
                reasoning_trace=trace,
                metadata={
                    'email': consultant.email,
                    'availability': consultant.availability,
                    'skills': consultant.skills,
                    'languages': consultant.languages,
                    'location': consultant.location,
                    'years_experience': consultant.years_experience,
                },
            )
        )

    return sorted(results, key=lambda item: (item.score, item.confidence_score), reverse=True)[:limit]


def build_opportunity_suggestions(opportunity: Opportunity, limit: int = 5) -> dict:
    return {
        'opportunity': opportunity.id,
        'partners': [result.__dict__ for result in suggest_partners(opportunity, limit=limit)],
        'consultants': [result.__dict__ for result in suggest_consultants(opportunity, limit=limit)],
    }
