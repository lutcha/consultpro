from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import median

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.analytics.models import MarketSignal, PredictiveMetric
from apps.opportunities.models import Opportunity
from apps.proposals.models import Proposal, ProposalStatusHistory
from apps.scraping.models import ScrapedOpportunity
from apps.users.models import User


ACTIVE_PIPELINE_STATUSES = ['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review', 'submitted']
DECISION_STATUSES = ['won', 'lost']
DEFAULT_LOOKBACK_MONTHS = 6
FORECAST_CACHE_HOURS = 12


def _pct(part: int, total: int) -> int:
    return round((part / total) * 100) if total else 0


def _float(value) -> float:
    return float(value or 0)


def _normalize_scope(value: str | None) -> str:
    return (value or '').strip()


def _opportunity_queryset(country: str | None = None, sector: str | None = None):
    queryset = Opportunity.objects.all()
    if country:
        queryset = queryset.filter(country__iexact=country)
    if sector:
        queryset = queryset.filter(sector__iexact=sector)
    return queryset


def _scraped_queryset(country: str | None = None, sector: str | None = None):
    queryset = ScrapedOpportunity.objects.all()
    if country:
        queryset = queryset.filter(country__iexact=country)
    if sector:
        queryset = queryset.filter(sector__iexact=sector)
    return queryset


def _win_rate_rows(group_field: str, country: str | None = None, sector: str | None = None) -> list[dict]:
    rows = (
        _opportunity_queryset(country=country, sector=sector)
        .values(group_field)
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


def _status_counts(country: str | None = None, sector: str | None = None) -> dict:
    return {
        row['status']: row['total']
        for row in _opportunity_queryset(country=country, sector=sector)
        .values('status')
        .annotate(total=Count('id'))
        .order_by('status')
    }


def _weighted_pipeline(country: str | None = None, sector: str | None = None) -> dict:
    total_value = Decimal('0')
    weighted_value = Decimal('0')
    items = []
    opportunities = (
        _opportunity_queryset(country=country, sector=sector)
        .filter(status__in=ACTIVE_PIPELINE_STATUSES)
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


def _proposal_outcomes(country: str | None = None, sector: str | None = None) -> dict:
    decided = Proposal.objects.filter(status__in=['won', 'lost'])
    if country:
        decided = decided.filter(opportunity__country__iexact=country)
    if sector:
        decided = decided.filter(opportunity__sector__iexact=sector)
    won = decided.filter(status='won').count()
    total = decided.count()
    return {
        'won': won,
        'lost': decided.filter(status='lost').count(),
        'total_decided': total,
        'win_rate': _pct(won, total),
    }


def _monthly_counts(country: str | None = None, sector: str | None = None, months: int = 12) -> list[dict]:
    now = timezone.now()
    start = now - timezone.timedelta(days=30 * months)
    counts = defaultdict(int)
    opportunities = _opportunity_queryset(country=country, sector=sector).filter(created_at__gte=start)
    scraped = _scraped_queryset(country=country, sector=sector).filter(scraped_at__gte=start)

    for created_at in opportunities.values_list('created_at', flat=True):
        counts[created_at.strftime('%Y-%m')] += 1
    for scraped_at in scraped.values_list('scraped_at', flat=True):
        counts[scraped_at.strftime('%Y-%m')] += 1

    series = []
    for offset in range(months - 1, -1, -1):
        month_date = now - timezone.timedelta(days=30 * offset)
        key = month_date.strftime('%Y-%m')
        series.append({'month': key, 'tenders': counts[key]})
    return series


def _avg_lead_time_days(country: str | None = None, sector: str | None = None) -> float | None:
    lead_times = []
    opportunities = _opportunity_queryset(country=country, sector=sector).exclude(deadline=None)
    for created_at, deadline in opportunities.values_list('created_at', 'deadline'):
        days = (deadline - created_at).total_seconds() / 86400
        if days >= 0:
            lead_times.append(days)

    scraped = _scraped_queryset(country=country, sector=sector).exclude(deadline=None)
    for scraped_at, deadline in scraped.values_list('scraped_at', 'deadline'):
        days = (deadline - scraped_at).total_seconds() / 86400
        if days >= 0:
            lead_times.append(days)

    if not lead_times:
        return None
    return round(median(lead_times), 2)


def _budget_concentration_index(country: str | None = None, sector: str | None = None) -> float:
    rows = (
        _opportunity_queryset(country=country, sector=sector)
        .values('client')
        .annotate(total_value=Sum('value'))
        .order_by('-total_value')
    )
    values = [_float(row['total_value']) for row in rows if row['total_value']]
    total = sum(values)
    if total <= 0:
        return 0.0
    return round(sum(values[:3]) / total, 2)


def _competitive_density(country: str | None = None, sector: str | None = None) -> dict:
    active_count = _opportunity_queryset(country=country, sector=sector).filter(
        status__in=ACTIVE_PIPELINE_STATUSES
    ).count()
    consultants = User.objects.filter(role='consultant')
    if country:
        consultants = consultants.filter(location__icontains=country)
    consultant_count = consultants.count()
    if consultant_count == 0:
        return {'level': 'unknown', 'ratio': None, 'basis': 'no_consultant_location_data'}

    ratio = round(active_count / consultant_count, 2)
    if ratio < 1:
        level = 'low'
    elif ratio < 3:
        level = 'medium'
    else:
        level = 'high'
    return {'level': level, 'ratio': ratio, 'basis': 'active_opportunities_per_consultant'}


def compute_descriptive_metrics(
    country: str | None = None,
    sector: str | None = None,
    lookback_months: int = DEFAULT_LOOKBACK_MONTHS,
) -> dict:
    now = timezone.now()
    recent_since = now - timezone.timedelta(days=30)
    lookback_since = now - timezone.timedelta(days=30 * lookback_months)
    opportunities = _opportunity_queryset(country=country, sector=sector)
    scraped = _scraped_queryset(country=country, sector=sector)
    recent_count = opportunities.filter(created_at__gte=recent_since).count()
    recent_count += scraped.filter(scraped_at__gte=recent_since).count()
    lookback_count = opportunities.filter(created_at__gte=lookback_since).count()
    lookback_count += scraped.filter(scraped_at__gte=lookback_since).count()
    monthly_average = lookback_count / lookback_months if lookback_months else 0
    demand_velocity = recent_count / monthly_average if monthly_average else 0

    monthly = _monthly_counts(country=country, sector=sector, months=12)
    monthly_values = [row['tenders'] for row in monthly]
    monthly_avg = sum(monthly_values) / len(monthly_values) if monthly_values else 0
    seasonality_score = 0
    if monthly_avg and max(monthly_values) > 0:
        seasonality_score = round((max(monthly_values) - monthly_avg) / max(monthly_values), 2)

    return {
        'demand_velocity': round(demand_velocity, 2),
        'recent_30d_tenders': recent_count,
        'lookback_months': lookback_months,
        'lookback_tenders': lookback_count,
        'monthly_average_tenders': round(monthly_average, 2),
        'budget_concentration_index': _budget_concentration_index(country=country, sector=sector),
        'seasonality_score': seasonality_score,
        'competitive_density': _competitive_density(country=country, sector=sector),
        'avg_lead_time_days': _avg_lead_time_days(country=country, sector=sector),
        'monthly_distribution': monthly,
    }


def _forecast_recommendations(descriptive: dict, forecast: list[dict]) -> list[str]:
    recommendations = []
    demand_velocity = descriptive.get('demand_velocity') or 0
    concentration = descriptive.get('budget_concentration_index') or 0
    peak = max((row['tenders'] for row in forecast), default=0)

    if demand_velocity >= 1.4:
        recommendations.append(
            'Demand velocity is above baseline; increase monitoring and reserve proposal capacity.'
        )
    if concentration >= 0.65:
        recommendations.append(
            'Budget is concentrated in the top clients; diversify source monitoring and partner coverage.'
        )
    if peak >= 3:
        recommendations.append(
            'Forecast indicates a measurable tender window; prepare reusable sector credentials early.'
        )
    if not recommendations:
        recommendations.append('Maintain current monitoring cadence; no strong demand anomaly detected.')
    return recommendations


def generate_demand_forecast(country: str | None = None, sector: str | None = None, horizon: int = 3) -> dict:
    horizon = max(1, min(int(horizon or 3), 12))
    history = _monthly_counts(country=country, sector=sector, months=12)
    counts = [row['tenders'] for row in history]
    non_zero_months = len([value for value in counts if value > 0])
    recent_avg = sum(counts[-3:]) / 3 if len(counts) >= 3 else 0
    previous_avg = sum(counts[-6:-3]) / 3 if len(counts) >= 6 else recent_avg
    baseline = recent_avg if recent_avg > 0 else (sum(counts) / len(counts) if counts else 0)
    monthly_trend = (recent_avg - previous_avg) / 3 if len(counts) >= 6 else 0
    warnings = []
    if non_zero_months < 3:
        warnings.append('insufficient_history_using_moving_average_fallback')
        monthly_trend = 0

    point_estimates = []
    confidence_intervals = []
    for month_index in range(1, horizon + 1):
        target_month = timezone.now() + timezone.timedelta(days=30 * month_index)
        point = max(0, round(baseline + (monthly_trend * month_index)))
        spread = max(1, round(point * 0.3))
        month = target_month.strftime('%Y-%m')
        point_estimates.append({'month': month, 'tenders': point})
        confidence_intervals.append({'month': month, 'lower': max(0, point - spread), 'upper': point + spread})

    confidence = min(0.8, round(0.35 + (non_zero_months / 24), 2))
    descriptive = compute_descriptive_metrics(country=country, sector=sector)
    return {
        'method': 'heuristic_moving_average_trend_v1',
        'point_estimates': point_estimates,
        'confidence_intervals': confidence_intervals,
        'model_diagnostics': {
            'confidence_score': confidence,
            'history_months': len(history),
            'non_zero_months': non_zero_months,
            'recent_3m_average': round(recent_avg, 2),
            'previous_3m_average': round(previous_avg, 2),
            'monthly_trend': round(monthly_trend, 2),
        },
        'reasoning_trace': [
            'Uses Opportunity.created_at and ScrapedOpportunity.scraped_at monthly counts.',
            'Forecast is recent 3-month moving average adjusted by the prior 3-month trend.',
            'Confidence is capped and reduced when historical coverage is sparse.',
        ],
        'warnings': warnings,
        'recommendations': _forecast_recommendations(descriptive, point_estimates),
    }


def _persist_signal(
    signal_type: str,
    country: str,
    sector: str,
    severity: str,
    message: str,
    data_snapshot: dict,
) -> None:
    recent_since = timezone.now() - timezone.timedelta(days=7)
    exists = MarketSignal.objects.filter(
        signal_type=signal_type,
        country_iso=country,
        sector_code=sector,
        acknowledged=False,
        created_at__gte=recent_since,
    ).exists()
    if not exists:
        MarketSignal.objects.create(
            signal_type=signal_type,
            country_iso=country,
            sector_code=sector,
            severity=severity,
            message=message,
            data_snapshot=data_snapshot,
        )


def detect_market_signals(country: str | None = None, sector: str | None = None, descriptive: dict | None = None) -> list:
    country_scope = _normalize_scope(country)
    sector_scope = _normalize_scope(sector)
    descriptive = descriptive or compute_descriptive_metrics(country=country, sector=sector)

    if descriptive['demand_velocity'] >= 1.4:
        _persist_signal(
            'demand_spike',
            country_scope,
            sector_scope,
            'high' if descriptive['demand_velocity'] >= 2 else 'medium',
            (
                f"Demand velocity is {descriptive['demand_velocity']}x baseline "
                f"for {country_scope or 'all countries'}/{sector_scope or 'all sectors'}."
            ),
            descriptive,
        )
    if descriptive['budget_concentration_index'] >= 0.65:
        _persist_signal(
            'budget_shift',
            country_scope,
            sector_scope,
            'medium',
            'Budget is concentrated in the top three clients for the selected market.',
            descriptive,
        )
    if descriptive['seasonality_score'] >= 0.6:
        _persist_signal(
            'seasonal_onset',
            country_scope,
            sector_scope,
            'low',
            'Monthly tender distribution shows a visible seasonal pattern.',
            descriptive,
        )

    recent_since = timezone.now() - timezone.timedelta(days=7)
    signals = MarketSignal.objects.filter(
        country_iso=country_scope,
        sector_code=sector_scope,
        acknowledged=False,
        created_at__gte=recent_since,
    ).order_by('-created_at')
    return [
        {
            'type': signal.signal_type,
            'severity': signal.severity,
            'message': signal.message,
            'created_at': signal.created_at.isoformat(),
        }
        for signal in signals
    ]


def get_or_compute_predictive_metric(
    country: str | None = None,
    sector: str | None = None,
    horizon: int = 3,
    force_refresh: bool = False,
) -> dict:
    country_scope = _normalize_scope(country)
    sector_scope = _normalize_scope(sector)
    horizon = max(1, min(int(horizon or 3), 12))
    now = timezone.now()

    cached = PredictiveMetric.objects.filter(
        metric_key='demand_forecast',
        country_iso=country_scope,
        sector_code=sector_scope,
        forecast_horizon_months=horizon,
        valid_until__gte=now,
    ).first()
    if cached and not force_refresh:
        value = dict(cached.value)
        value['cache_status'] = 'hit'
        return value

    forecast = generate_demand_forecast(country=country_scope, sector=sector_scope, horizon=horizon)
    value = {'demand_forecast': forecast}
    PredictiveMetric.objects.update_or_create(
        metric_key='demand_forecast',
        country_iso=country_scope,
        sector_code=sector_scope,
        forecast_horizon_months=horizon,
        defaults={
            'value': value,
            'valid_until': now + timezone.timedelta(hours=FORECAST_CACHE_HOURS),
        },
    )
    value['cache_status'] = 'refresh'
    return value


def compute_procurement_trends(
    country: str | None = None,
    sector: str | None = None,
    horizon: int = 3,
    include_forecast: bool = False,
) -> dict:
    descriptive = compute_descriptive_metrics(country=country, sector=sector)
    signals = detect_market_signals(country=country, sector=sector, descriptive=descriptive)
    predictive = None
    if include_forecast:
        predictive = get_or_compute_predictive_metric(country=country, sector=sector, horizon=horizon)

    return {
        'meta': {
            'country': _normalize_scope(country),
            'sector': _normalize_scope(sector),
            'horizon_months': max(1, min(int(horizon or 3), 12)),
            'include_forecast': include_forecast,
            'generated_at': timezone.now().isoformat(),
        },
        'win_rate_by_sector': _win_rate_rows('sector', country=country, sector=sector),
        'win_rate_by_country': _win_rate_rows('country', country=country, sector=sector),
        'weighted_pipeline': _weighted_pipeline(country=country, sector=sector),
        'avg_stage_duration_days': _average_stage_duration_days(),
        'opportunity_status_counts': _status_counts(country=country, sector=sector),
        'proposal_outcomes': _proposal_outcomes(country=country, sector=sector),
        'descriptive': descriptive,
        'predictive': predictive,
        'signals': signals,
    }
