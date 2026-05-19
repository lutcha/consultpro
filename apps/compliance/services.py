from __future__ import annotations

import hashlib

from django.db import transaction

from apps.opportunities.models import Opportunity

from .models import ComplianceMatrix, ComplianceMatrixRow


COMPLIANCE_VERSION = 'compliance_matrix_v1'
COS_REQUIREMENT_SOURCES = [
    ('submission_requirements', 'mandatory'),
    ('qc_checklist', 'mandatory'),
    ('team_requirements', 'desirable'),
    ('workplan_requirements', 'desirable'),
    ('budget_requirements', 'desirable'),
]


def _flatten_items(value, source_reference, priority):
    if not value:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [{'text': text, 'source_reference': source_reference, 'priority': priority}] if text else []
    if isinstance(value, list):
        items = []
        for index, item in enumerate(value, start=1):
            items.extend(_flatten_items(item, f'{source_reference}[{index}]', priority))
        return items
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            items.extend(_flatten_items(item, f'{source_reference}.{key}', priority))
        return items
    text = str(value).strip()
    return [{'text': text, 'source_reference': source_reference, 'priority': priority}] if text else []


def _row_key(text, source_reference):
    raw = f'{source_reference}:{text}'.encode('utf-8')
    return hashlib.sha1(raw).hexdigest()[:16]


def _matrix_items(opportunity: Opportunity) -> list[dict]:
    items = []
    for requirement in opportunity.requirements.all().order_by('id'):
        items.append(
            {
                'requirement_key': f'requirement-{requirement.id}',
                'requirement_text': requirement.description,
                'requirement_category': requirement.category,
                'priority': requirement.priority,
                'source_type': 'requirement',
                'source_reference': f'opportunity.requirements.{requirement.id}',
                'source_trace': {
                    'model': 'Requirement',
                    'id': requirement.id,
                    'extracted_by_ai': requirement.extracted_by_ai,
                },
                'confidence_score': 0.9 if not requirement.extracted_by_ai else 0.75,
            }
        )

    cos_analysis = (opportunity.ai_extraction or {}).get('cos_analysis') or {}
    for source_key, priority in COS_REQUIREMENT_SOURCES:
        for item in _flatten_items(cos_analysis.get(source_key), f'cos_analysis.{source_key}', priority):
            text = item['text']
            items.append(
                {
                    'requirement_key': f"cos-{_row_key(text, item['source_reference'])}",
                    'requirement_text': text,
                    'requirement_category': source_key,
                    'priority': item['priority'],
                    'source_type': 'ai_extraction',
                    'source_reference': item['source_reference'],
                    'source_trace': {
                        'model': 'Opportunity',
                        'field': 'ai_extraction.cos_analysis',
                        'key': source_key,
                    },
                    'confidence_score': 0.65,
                }
            )
    return items


def generate_compliance_matrix(opportunity_id: int, generated_by=None) -> ComplianceMatrix:
    opportunity = Opportunity.objects.get(pk=opportunity_id)
    items = _matrix_items(opportunity)
    source_trace = [
        {
            'source_type': item['source_type'],
            'source_reference': item['source_reference'],
            'requirement_key': item['requirement_key'],
        }
        for item in items
    ]
    confidence = sum(float(item['confidence_score']) for item in items) / len(items) if items else 0

    with transaction.atomic():
        matrix, _created = ComplianceMatrix.objects.update_or_create(
            opportunity=opportunity,
            defaults={
                'status': 'generated',
                'generation_version': COMPLIANCE_VERSION,
                'source_trace': source_trace,
                'ai_metadata': {
                    'provider': 'deterministic',
                    'model': '',
                    'method': 'requirements_and_cos_extraction',
                    'item_count': len(items),
                },
                'confidence_score': round(confidence, 2),
                'generated_by': generated_by,
            },
        )
        existing_keys = set(matrix.rows.values_list('requirement_key', flat=True))
        incoming_keys = set()
        for order, item in enumerate(items, start=1):
            incoming_keys.add(item['requirement_key'])
            defaults = {
                'requirement_text': item['requirement_text'],
                'requirement_category': item['requirement_category'],
                'priority': item['priority'],
                'source_type': item['source_type'],
                'source_reference': item['source_reference'],
                'source_trace': item['source_trace'],
                'confidence_score': item['confidence_score'],
                'ai_metadata': matrix.ai_metadata,
                'order': order,
            }
            if item['requirement_key'] not in existing_keys:
                defaults['status'] = 'missing'
            matrix.rows.update_or_create(
                requirement_key=item['requirement_key'],
                defaults=defaults,
            )
        matrix.rows.exclude(requirement_key__in=incoming_keys).delete()
        matrix.human_override_count = matrix.rows.filter(human_override=True).count()
        matrix.save(update_fields=['human_override_count', 'updated_at'])
    return matrix
