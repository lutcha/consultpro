from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db.models import Count, Q

from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal, ProposalStatusHistory


ACTIVE_PIPELINE_STATUSES = ['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review', 'submitted']
DECISION_STATUSES = ['won', 'lost']


def _pct(part: int, total: int) -> int:
    return round((part / total) * 100) if total else 0


def _float(value) -> float:
    return float(value or 0)


def _win_rate_rows(group_field: str) -> list[dict]:
    rows = (
        Opportunity.objects.values(group_field)
        .annotate(
            total=Count('id', filter=Q(status__in=DECISION_STATUSES)),
            won=Count('id', filter=Q(status='won')),
            lost=Count('id', filter=Q(status='lost')),
        )
        .filter(total__gt=0)
        .order_by(group_field)
    )
    return [
        {
            group_field: row[group_field] or 'unknown',
            'won': row['won'],
            'lost': row['lost'],
            'total_decided': row['total'],
            'win_rate': _pct(row['won'], row['total']),
        }
        for row in rows
    ]


def _status_counts() -> dict:
    return {
        row['status']: row['total']
        for row in Opportunity.objects.values('status').annotate(total=Count('id')).order_by('status')
    }


def _weighted_pipeline() -> dict:
    total_value = Decimal('0')
    weighted_value = Decimal('0')
    items = []
    opportunities = (
        Opportunity.objects.filter(status__in=ACTIVE_PIPELINE_STATUSES)
        .prefetch_related('scores')
        .order_by('-value')
    )

    for opportunity in opportunities:
        current_score = next((score for score in opportunity.scores.all() if score.is_current), None)
        probability = Decimal(current_score.overall_score if current_score else 50) / Decimal('100')
        value = opportunity.value or Decimal('0')
        weighted = value * probability
        total_value += value
        weighted_value += weighted
        items.append(
            {
                'id': opportunity.id,
                'title': opportunity.title,
                'status': opportunity.status,
                'value': _float(value),
                'currency': opportunity.currency,
                'probability': _float(probability),
                'weighted_value': _float(weighted),
                'score_source': 'opportunity_score' if current_score else 'default_probability',
            }
        )

    return {
        'total_value': _float(total_value),
        'weighted_value': _float(weighted_value),
        'currency': 'USD',
        'count': len(items),
        'items': items[:20],
    }


def _average_stage_duration_days() -> dict:
    durations = defaultdict(list)
    histories_by_proposal = defaultdict(list)
    histories = ProposalStatusHistory.objects.select_related('proposal').order_by('proposal_id', 'created_at')

    for history in histories:
        histories_by_proposal[history.proposal_id].append(history)

    for entries in histories_by_proposal.values():
        for index, entry in enumerate(entries):
            next_created_at = entries[index + 1].created_at if index + 1 < len(entries) else None
            if next_created_at is None:
                continue
            seconds = (next_created_at - entry.created_at).total_seconds()
            if seconds >= 0:
                durations[entry.status].append(seconds / 86400)

    return {
        status: round(sum(values) / len(values), 2)
        for status, values in sorted(durations.items())
        if values
    }


def _proposal_outcomes() -> dict:
    decided = Proposal.objects.filter(status__in=['won', 'lost'])
    won = decided.filter(status='won').count()
    total = decided.count()
    return {
        'won': won,
        'lost': decided.filter(status='lost').count(),
        'total_decided': total,
        'win_rate': _pct(won, total),
    }


def compute_procurement_trends() -> dict:
    return {
        'win_rate_by_sector': _win_rate_rows('sector'),
        'win_rate_by_country': _win_rate_rows('country'),
        'weighted_pipeline': _weighted_pipeline(),
        'avg_stage_duration_days': _average_stage_duration_days(),
        'opportunity_status_counts': _status_counts(),
        'proposal_outcomes': _proposal_outcomes(),
    }
