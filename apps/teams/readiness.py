"""
Team readiness service for proposals.

Purely informational - never blocks QC or submission.
Aggregates per-member CV/curriculum status and computes match scores
against opportunity requirements when a linked Curriculum is available.
"""
from apps.curriculum.matching import match_cv_to_opportunity
from apps.proposals.models import ProposalTeamMember


def compute_team_readiness(proposal):
    """
    Return a readiness dict for a proposal's technical team.

    Does not modify any state. Safe to call at any proposal status.
    """
    members_qs = ProposalTeamMember.objects.select_related(
        'user', 'curriculum'
    ).filter(proposal=proposal)

    members_data = []
    missing_cvs = []
    suggested_profiles = []
    warnings = []

    for member in members_qs:
        entry = _member_entry(member, proposal.opportunity)
        members_data.append(entry)

        if entry['team_member_status'] == 'suggested_profile':
            suggested_profiles.append(entry)

        if not entry['has_cv']:
            missing_cvs.append({
                'member_id': member.id,
                'role': member.role,
                'user_email': entry['user_email'],
                'team_member_status': entry['team_member_status'],
            })

    if missing_cvs:
        warnings.append(
            f"{len(missing_cvs)} membro(s) sem CV anexado ou curriculum ligado."
        )
    if suggested_profiles:
        warnings.append(
            f"{len(suggested_profiles)} perfil(is) sugerido(s) ainda não confirmado(s)."
        )

    total = len(members_data)
    confirmed_count = sum(
        1 for m in members_data if m['team_member_status'] == 'confirmed'
    )
    readiness = _overall_readiness(total, confirmed_count, missing_cvs, suggested_profiles)

    return {
        'readiness': readiness,
        'total_members': total,
        'confirmed_count': confirmed_count,
        'cv_missing_count': len(missing_cvs),
        'suggested_count': len(suggested_profiles),
        'members': members_data,
        'missing_cvs': missing_cvs,
        'suggested_profiles': suggested_profiles,
        'warnings': warnings,
    }


def _member_entry(member, opportunity):
    """Build a per-member readiness dict."""
    has_cv = bool(member.cv_attached or member.cv_document)
    curriculum_score = None
    matched_skills = []
    missing_skills = []
    match_reasons = []

    if member.curriculum_id and member.curriculum is not None:
        has_cv = True
        try:
            cv_match = match_cv_to_opportunity(member.curriculum, opportunity)
            curriculum_score = cv_match.overall_score
            matched_skills = cv_match.matched_skills or []
            missing_skills = cv_match.missing_skills or []
            match_reasons = cv_match.recommendations or []
        except Exception:
            match_reasons = ['Erro ao calcular score de curriculum.']

    if not has_cv and member.team_member_status not in ('suggested_profile',):
        match_reasons.append('CV em falta - score nao calculado.')

    user_email = None
    user_name = None
    if member.user_id:
        user_email = member.user.email
        user_name = member.user.get_full_name() or member.user.email
    elif member.suggested_profile:
        user_name = member.suggested_profile.get('name', 'Perfil Sugerido')

    return {
        'member_id': member.id,
        'user_email': user_email,
        'user_name': user_name,
        'role': member.role,
        'team_member_status': member.team_member_status,
        'has_cv': has_cv,
        'cv_attached': member.cv_attached,
        'has_cv_document': bool(member.cv_document),
        'curriculum_id': member.curriculum_id,
        'curriculum_score': curriculum_score,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'reasons': match_reasons,
        'suggested_profile': member.suggested_profile or {},
    }


def _overall_readiness(total, confirmed_count, missing_cvs, suggested_profiles):
    if total == 0:
        return 'not_started'
    if len(suggested_profiles) == total:
        return 'not_started'
    if missing_cvs or suggested_profiles:
        return 'in_progress'
    if confirmed_count == total:
        return 'ready'
    return 'in_progress'
