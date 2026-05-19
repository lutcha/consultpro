import re
from collections import Counter
from decimal import Decimal

from django.db.models import Q

from apps.curriculum.models import Curriculum
from apps.projects.models import Project
from apps.proposals.models import Proposal, ProposalSection

from .models import KnowledgeAsset


STOPWORDS = {
    'a', 'an', 'and', 'as', 'at', 'by', 'de', 'da', 'das', 'do', 'dos', 'e', 'em',
    'for', 'from', 'in', 'no', 'na', 'of', 'on', 'or', 'para', 'por', 'the', 'to',
    'with', 'com', 'que',
}


def tokenize(value):
    text = re.sub(r'[^a-zA-Z0-9]+', ' ', str(value or '').lower())
    return [token for token in text.split() if len(token) > 2 and token not in STOPWORDS]


def _text_score(query_tokens, asset):
    if not query_tokens:
        return Decimal('0')
    title_tokens = Counter(tokenize(asset.title))
    summary_tokens = Counter(tokenize(asset.summary))
    content_tokens = Counter(tokenize(asset.content))
    tag_tokens = Counter(tokenize(' '.join(asset.tags or [])))
    score = Decimal('0')
    for token in query_tokens:
        score += Decimal(title_tokens[token] * 5)
        score += Decimal(summary_tokens[token] * 3)
        score += Decimal(content_tokens[token])
        score += Decimal(tag_tokens[token] * 2)
    return score


def _reasoning_trace(query_tokens, asset):
    tokens = set(query_tokens)
    trace = []
    if tokens.intersection(tokenize(asset.title)):
        trace.append('title_match')
    if tokens.intersection(tokenize(asset.summary)):
        trace.append('summary_match')
    if tokens.intersection(tokenize(asset.content)):
        trace.append('content_match')
    if tokens.intersection(tokenize(' '.join(asset.tags or []))):
        trace.append('tag_match')
    if asset.source_app:
        trace.append(f'source:{asset.source_app}.{asset.source_model}')
    return trace or ['fallback_rank']


def search_knowledge(query='', asset_type='', country='', sector='', limit=10):
    query_tokens = tokenize(query)
    queryset = KnowledgeAsset.objects.filter(status='active')
    if asset_type:
        queryset = queryset.filter(asset_type=asset_type)
    if country:
        queryset = queryset.filter(country__iexact=country)
    if sector:
        queryset = queryset.filter(sector__iexact=sector)
    if query_tokens:
        text_filter = Q()
        for token in query_tokens:
            text_filter |= (
                Q(title__icontains=token)
                | Q(summary__icontains=token)
                | Q(content__icontains=token)
                | Q(tags__icontains=token)
            )
        queryset = queryset.filter(text_filter)

    ranked = []
    for asset in queryset[:250]:
        score = _text_score(query_tokens, asset)
        if query_tokens and score <= 0:
            continue
        ranked.append(
            {
                'asset': asset,
                'score': float(score),
                'reasoning_trace': _reasoning_trace(query_tokens, asset),
                'search_mode': 'textual_fallback',
            }
        )
    ranked.sort(key=lambda item: (item['score'], item['asset'].updated_at), reverse=True)
    return ranked[:limit]


def upsert_asset_from_proposal(proposal):
    opportunity = proposal.opportunity
    content = '\n\n'.join(
        f'{section.title}\n{section.content}' for section in proposal.sections.all().order_by('order', 'id')
    )
    return KnowledgeAsset.objects.update_or_create(
        source_app='proposals',
        source_model='Proposal',
        source_id=str(proposal.id),
        defaults={
            'asset_type': 'proposal',
            'title': proposal.title,
            'summary': opportunity.ai_summary or opportunity.description[:500],
            'content': content,
            'metadata': {'proposal_status': proposal.status, 'opportunity_id': opportunity.id},
            'tags': [opportunity.client, opportunity.sector, opportunity.country],
            'country': opportunity.country or '',
            'sector': opportunity.sector or '',
            'status': 'active',
            'created_by': proposal.created_by,
        },
    )[0]


def upsert_asset_from_section(section):
    proposal = section.proposal
    opportunity = proposal.opportunity
    return KnowledgeAsset.objects.update_or_create(
        source_app='proposals',
        source_model='ProposalSection',
        source_id=str(section.id),
        defaults={
            'asset_type': 'proposal_section',
            'title': f'{proposal.title} - {section.title}',
            'summary': section.title,
            'content': section.content,
            'metadata': {
                'proposal_id': proposal.id,
                'section_type': section.section_type,
                'opportunity_id': opportunity.id,
            },
            'tags': [section.section_type, opportunity.sector, opportunity.country],
            'country': opportunity.country or '',
            'sector': opportunity.sector or '',
            'status': 'active',
            'created_by': proposal.created_by,
        },
    )[0]


def upsert_asset_from_project(project):
    return KnowledgeAsset.objects.update_or_create(
        source_app='projects',
        source_model='Project',
        source_id=str(project.id),
        defaults={
            'asset_type': 'project',
            'title': project.title,
            'summary': project.description,
            'content': project.description,
            'metadata': {'project_status': project.status, 'proposal_id': project.proposal_id},
            'tags': [project.client, project.sector, project.country],
            'country': project.country or '',
            'sector': project.sector or '',
            'status': 'active',
            'created_by': project.manager,
        },
    )[0]


def upsert_asset_from_curriculum(curriculum):
    extracted = curriculum.extracted_data or {}
    content = '\n'.join(str(value) for value in extracted.values() if value)
    return KnowledgeAsset.objects.update_or_create(
        source_app='curriculum',
        source_model='Curriculum',
        source_id=str(curriculum.id),
        defaults={
            'asset_type': 'cv',
            'title': curriculum.file_name,
            'summary': extracted.get('summary', ''),
            'content': content,
            'metadata': {'user_id': curriculum.user_id, 'analysis_score': curriculum.analysis_score},
            'tags': extracted.get('skills', []) if isinstance(extracted.get('skills', []), list) else [],
            'status': 'active',
            'created_by': curriculum.user,
        },
    )[0]


def index_knowledge_assets(source='all'):
    created = []
    if source in ('all', 'proposals'):
        for proposal in Proposal.objects.select_related('opportunity', 'created_by').prefetch_related('sections'):
            created.append(upsert_asset_from_proposal(proposal))
        for section in ProposalSection.objects.select_related('proposal__opportunity', 'proposal__created_by'):
            created.append(upsert_asset_from_section(section))
    if source in ('all', 'projects'):
        for project in Project.objects.select_related('proposal', 'manager'):
            created.append(upsert_asset_from_project(project))
    if source in ('all', 'curriculum'):
        for curriculum in Curriculum.objects.select_related('user'):
            created.append(upsert_asset_from_curriculum(curriculum))
    return created
