import re

from apps.opportunities.models import Requirement

from .models import CVOpportunityMatch


def _tokens(value):
    if not value:
        return set()
    if isinstance(value, list):
        value = ' '.join(str(item) for item in value)
    return {
        token
        for token in re.findall(r'[A-Za-z0-9]+', str(value).lower())
        if len(token) >= 4
    }


def _flatten_experience(items):
    parts = []
    for item in items or []:
        if isinstance(item, dict):
            parts.append(' '.join(str(value) for value in item.values()))
        else:
            parts.append(str(item))
    return ' '.join(parts)


def _score_overlap(candidate_tokens, required_tokens):
    if not required_tokens:
        return 0, [], []
    matched = sorted(candidate_tokens & required_tokens)
    missing = sorted(required_tokens - candidate_tokens)
    score = int((len(matched) / len(required_tokens)) * 100)
    return score, matched, missing


def match_cv_to_opportunity(curriculum, opportunity):
    data = curriculum.extracted_data or {}
    requirements = list(
        Requirement.objects.filter(opportunity=opportunity).values_list('description', flat=True)
    )
    requirement_text = ' '.join(requirements) or opportunity.description or ''
    requirement_tokens = _tokens(requirement_text)

    skill_tokens = _tokens(data.get('skills', []))
    experience_text = _flatten_experience(data.get('experience', []))
    education_text = _flatten_experience(data.get('education', []))
    language_tokens = _tokens(data.get('languages', []))

    skills_score, matched_skills, missing_skills = _score_overlap(skill_tokens, requirement_tokens)
    experience_score, _, _ = _score_overlap(_tokens(experience_text), requirement_tokens)
    education_score = min(100, len(data.get('education', []) or []) * 50)
    language_score = 100 if language_tokens else 0

    overall_score = int(
        (skills_score * 0.45)
        + (experience_score * 0.35)
        + (education_score * 0.10)
        + (language_score * 0.10)
    )

    recommendations = []
    if missing_skills:
        recommendations.append(
            'Reforcar evidencias para: ' + ', '.join(missing_skills[:8])
        )
    if curriculum.status != 'analyzed':
        recommendations.append('Analisar o CV antes de usar este score para staffing.')

    match, _created = CVOpportunityMatch.objects.update_or_create(
        curriculum=curriculum,
        opportunity=opportunity,
        defaults={
            'overall_score': overall_score,
            'skills_match_score': skills_score,
            'experience_match_score': experience_score,
            'education_match_score': education_score,
            'language_match_score': language_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'relevant_experiences': data.get('experience', [])[:3],
            'recommendations': recommendations,
        },
    )
    return match
