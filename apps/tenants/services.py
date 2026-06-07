from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from rest_framework.exceptions import PermissionDenied

from .intelligence import normalize_decimal, normalize_list, normalize_mapping, weighted_codes
from .models import (
    Tenant,
    TenantIntelligenceProfile,
    TenantMembership,
    TenantOnboardingSnapshot,
    TenantProfile,
    TenantStrategy,
)


DEFAULT_TENANT_SLUG = 'consultpro-internal'
DEFAULT_TENANT_NAME = 'ConsultPro Internal'


def _unique_slug(name: str) -> str:
    base = slugify(name)[:100] or 'tenant'
    slug = base
    counter = 2
    while Tenant.objects.filter(slug=slug).exists():
        suffix = f'-{counter}'
        slug = f'{base[:120 - len(suffix)]}{suffix}'
        counter += 1
    return slug


@transaction.atomic
def create_tenant_with_owner(name: str, owner, **tenant_fields) -> Tenant:
    tenant = Tenant.objects.create(
        name=name,
        slug=tenant_fields.pop('slug', '') or _unique_slug(name),
        **tenant_fields,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=owner,
        role='owner',
        status='active',
    )
    ensure_tenant_context_records(tenant)
    return tenant


def ensure_tenant_context_records(tenant: Tenant) -> None:
    TenantProfile.objects.get_or_create(tenant=tenant)
    TenantStrategy.objects.get_or_create(tenant=tenant)
    TenantIntelligenceProfile.objects.get_or_create(tenant=tenant)


def create_default_tenant_for_existing_data() -> Tenant:
    tenant, _created = Tenant.objects.get_or_create(
        slug=DEFAULT_TENANT_SLUG,
        defaults={
            'name': DEFAULT_TENANT_NAME,
            'status': 'active',
            'plan': 'beta',
            'organization_type': 'consulting_firm',
            'size': 'small',
            'maturity_level': 'growing',
            'primary_country': 'cv',
            'default_language': 'pt',
        },
    )
    ensure_tenant_context_records(tenant)
    return tenant


def assert_user_in_tenant(user, tenant: Tenant) -> TenantMembership:
    membership = TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        status='active',
    ).first()
    if not membership:
        raise PermissionDenied('User is not a member of this tenant.')
    return membership


def get_active_tenant_for_user(user, request=None):
    if not user or not user.is_authenticated:
        return None

    tenant_id = ''
    tenant_slug = ''
    if request is not None:
        tenant_id = request.headers.get('X-Tenant-ID') or request.META.get('HTTP_X_TENANT_ID') or ''
        tenant_slug = request.headers.get('X-Tenant-Slug') or request.META.get('HTTP_X_TENANT_SLUG') or ''

    queryset = Tenant.objects.filter(memberships__user=user, memberships__status='active').distinct()
    if tenant_id:
        tenant = queryset.filter(id=tenant_id).first()
        if not tenant:
            raise PermissionDenied('Invalid tenant for current user.')
        return tenant
    if tenant_slug:
        tenant = queryset.filter(slug=tenant_slug).first()
        if not tenant:
            raise PermissionDenied('Invalid tenant for current user.')
        return tenant
    return queryset.order_by('name').first()


def user_has_tenant_role(user, tenant: Tenant, roles: set[str]) -> bool:
    if user and user.is_staff:
        return True
    return TenantMembership.objects.filter(
        user=user,
        tenant=tenant,
        role__in=roles,
        status='active',
    ).exists()


def build_intelligence_profile_from_onboarding(responses: dict) -> dict:
    target_countries = normalize_list(responses.get('target_countries'))
    target_sectors = normalize_list(responses.get('target_sectors'))
    target_donors = normalize_list(responses.get('target_donors'))
    return {
        'opportunity_keywords': normalize_list(responses.get('opportunity_keywords') or responses.get('keywords')),
        'excluded_keywords': normalize_list(responses.get('excluded_keywords')),
        'preferred_sources': normalize_list(responses.get('preferred_sources')),
        'excluded_sources': normalize_list(responses.get('excluded_sources')),
        'preferred_procurement_types': normalize_list(
            responses.get('preferred_procurement_types') or responses.get('project_types')
        ),
        'minimum_score_threshold': responses.get('minimum_score_threshold') or 50,
        'deadline_min_days': responses.get('deadline_min_days'),
        'deadline_max_days': responses.get('deadline_max_days'),
        'minimum_budget': normalize_decimal(responses.get('minimum_budget')),
        'maximum_budget': normalize_decimal(responses.get('maximum_budget')),
        'requires_local_partner': bool(responses.get('requires_local_partner', False)),
        'eligible_languages': normalize_list(responses.get('eligible_languages') or responses.get('languages')),
        'geographic_priority_weights': normalize_mapping(responses.get('geographic_priority_weights')) or weighted_codes(target_countries),
        'sector_priority_weights': normalize_mapping(responses.get('sector_priority_weights')) or weighted_codes(target_sectors),
        'donor_priority_weights': normalize_mapping(responses.get('donor_priority_weights')) or weighted_codes(target_donors),
        'scoring_weights': normalize_mapping(responses.get('scoring_weights')),
        'ai_instructions': responses.get('ai_instructions') or responses.get('positioning_statement') or '',
        'partial_intelligence_rules': normalize_mapping(responses.get('partial_intelligence_rules')),
        'created_from_onboarding': True,
        'last_refined_at': timezone.now(),
    }


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _record_onboarding_overwrites(tenant: Tenant, model_name: str, instance, data: dict) -> list[dict]:
    overwrites = []
    for field, new_value in data.items():
        old_value = getattr(instance, field, None)
        comparable_old = _json_safe(old_value)
        comparable_new = _json_safe(new_value)
        old_is_empty = comparable_old in (None, '', [], {}, 0, '0.00')
        if not old_is_empty and comparable_old != comparable_new:
            overwrites.append({
                'model': model_name,
                'field': field,
                'previous_value': comparable_old,
                'new_value': comparable_new,
                'source': 'tenant_onboarding',
            })
    if not overwrites:
        return []

    tenant.settings = {
        **(tenant.settings or {}),
        'onboarding_overwrite_log': [
            *((tenant.settings or {}).get('onboarding_overwrite_log') or []),
            {
                'recorded_at': timezone.now().isoformat(),
                'items': overwrites,
            },
        ][-20:],
    }
    return overwrites


def sync_default_opportunity_context(tenant: Tenant, submitted_by=None) -> None:
    from apps.opportunities.models import FirmProfile, SavedFilter

    ensure_tenant_context_records(tenant)
    intelligence = tenant.intelligence_profile
    strategy = tenant.strategy
    profile_name = f'{tenant.name} default profile'
    sectors = list((intelligence.sector_priority_weights or {}).keys()) or strategy.target_sectors
    countries = list((intelligence.geographic_priority_weights or {}).keys()) or strategy.target_countries

    firm_profile, _created = FirmProfile.objects.update_or_create(
        tenant=tenant,
        is_default=True,
        defaults={
            'name': profile_name,
            'target_sectors': sectors,
            'geographies': countries,
            'scoring_weights_override': intelligence.scoring_weights or {},
            'updated_by': submitted_by if getattr(submitted_by, 'is_authenticated', False) else None,
        },
    )
    if firm_profile.is_default:
        FirmProfile.objects.filter(tenant=tenant, is_default=True).exclude(pk=firm_profile.pk).update(is_default=False)

    if submitted_by and getattr(submitted_by, 'is_authenticated', False):
        from .intelligence import build_saved_filter_payload

        payload = build_saved_filter_payload(intelligence)
        if payload:
            SavedFilter.objects.update_or_create(
                tenant=tenant,
                owner=submitted_by,
                view_type='opportunities',
                name='Tenant intelligence defaults',
                defaults={'payload': payload, 'is_shared': True},
            )


@transaction.atomic
def apply_onboarding_to_tenant(tenant: Tenant, responses: dict, submitted_by=None) -> TenantOnboardingSnapshot:
    raw_responses = responses.get('_raw_onboarding_responses') or responses
    responses = {key: value for key, value in responses.items() if key != '_raw_onboarding_responses'}
    tenant_data = {
        key: responses[key]
        for key in (
            'organization_type',
            'size',
            'maturity_level',
            'primary_country',
            'default_language',
        )
        if responses.get(key) not in (None, '')
    }
    profile_data = {
        'legal_name': responses.get('legal_name', ''),
        'brand_name': responses.get('brand_name', ''),
        'website': responses.get('website', ''),
        'organization_description': responses.get('organization_description', ''),
        'countries_of_operation': normalize_list(responses.get('countries_of_operation')),
        'languages': normalize_list(responses.get('languages')),
        'core_capabilities': normalize_list(responses.get('core_capabilities')),
        'certifications': normalize_list(responses.get('certifications')),
        'past_clients': normalize_list(responses.get('past_clients')),
        'donor_experience': normalize_list(responses.get('donor_experience')),
        'sector_experience': normalize_list(responses.get('sector_experience')),
        'team_size': responses.get('team_size') or 0,
        'annual_bid_capacity': responses.get('annual_bid_capacity') or 0,
        'average_contract_size': responses.get('average_contract_size'),
        'preferred_contract_size': responses.get('preferred_contract_size'),
    }
    strategy_data = {
        'strategic_objectives': normalize_list(responses.get('strategic_objectives')),
        'target_markets': normalize_list(responses.get('target_markets')),
        'target_donors': normalize_list(responses.get('target_donors')),
        'target_sectors': normalize_list(responses.get('target_sectors')),
        'target_countries': normalize_list(responses.get('target_countries')),
        'priority_project_types': normalize_list(responses.get('priority_project_types') or responses.get('project_types')),
        'growth_goals': normalize_list(responses.get('growth_goals')),
        'positioning_statement': responses.get('positioning_statement', ''),
        'risk_appetite': responses.get('risk_appetite') or 'balanced',
        'partnership_strategy': responses.get('partnership_strategy', ''),
        'go_no_go_preferences': normalize_mapping(responses.get('go_no_go_preferences')),
    }
    intelligence_data = build_intelligence_profile_from_onboarding(responses)

    ensure_tenant_context_records(tenant)
    overwrites = []
    if tenant_data:
        overwrites.extend(_record_onboarding_overwrites(tenant, 'Tenant', tenant, tenant_data))
        for field, value in tenant_data.items():
            setattr(tenant, field, value)
        tenant.save(update_fields=[*tenant_data.keys(), 'settings', 'updated_at'])
        tenant.refresh_from_db()

    profile = tenant.profile
    strategy = tenant.strategy
    intelligence = tenant.intelligence_profile
    overwrites.extend(_record_onboarding_overwrites(tenant, 'TenantProfile', profile, profile_data))
    overwrites.extend(_record_onboarding_overwrites(tenant, 'TenantStrategy', strategy, strategy_data))
    overwrites.extend(
        _record_onboarding_overwrites(
            tenant,
            'TenantIntelligenceProfile',
            intelligence,
            intelligence_data,
        )
    )
    TenantProfile.objects.filter(tenant=tenant).update(**profile_data)
    TenantStrategy.objects.filter(tenant=tenant).update(**strategy_data)
    TenantIntelligenceProfile.objects.filter(tenant=tenant).update(**intelligence_data)

    snapshot = TenantOnboardingSnapshot.objects.create(
        tenant=tenant,
        submitted_by=submitted_by,
        responses=raw_responses,
        derived_profile=_json_safe(profile_data),
        derived_strategy=_json_safe(strategy_data),
        derived_intelligence_profile=_json_safe({
            **intelligence_data,
            'last_refined_at': intelligence_data['last_refined_at'].isoformat(),
        }),
    )
    tenant.settings = {
        **(tenant.settings or {}),
        'last_onboarding_snapshot_id': snapshot.id,
        'last_onboarding_applied_at': timezone.now().isoformat(),
        'last_onboarding_overwrites': overwrites,
    }
    tenant.save(update_fields=['settings', 'updated_at'])
    sync_default_opportunity_context(tenant, submitted_by=submitted_by)
    return snapshot
