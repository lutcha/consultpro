import uuid

from django.conf import settings
from django.db import models


class Tenant(models.Model):
    STATUS_CHOICES = [
        ('trialing', 'Trialing'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]
    PLAN_CHOICES = [
        ('beta', 'Beta'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    ORGANIZATION_TYPE_CHOICES = [
        ('consulting_firm', 'Consulting firm'),
        ('ngo', 'NGO'),
        ('donor', 'Donor'),
        ('government', 'Government'),
        ('startup', 'Startup'),
        ('university', 'University'),
        ('other', 'Other'),
    ]
    SIZE_CHOICES = [
        ('solo', 'Solo'),
        ('small', 'Small'),
        ('mid_market', 'Mid-market'),
        ('enterprise', 'Enterprise'),
    ]
    MATURITY_CHOICES = [
        ('early', 'Early'),
        ('growing', 'Growing'),
        ('mature', 'Mature'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trialing', db_index=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='beta', db_index=True)
    organization_type = models.CharField(
        max_length=40,
        choices=ORGANIZATION_TYPE_CHOICES,
        default='consulting_firm',
    )
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default='small')
    maturity_level = models.CharField(max_length=20, choices=MATURITY_CHOICES, default='growing')
    primary_country = models.CharField(max_length=100, blank=True)
    default_language = models.CharField(max_length=10, default='pt')
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['status', 'plan']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('consultant', 'Consultant'),
        ('viewer', 'Viewer'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('invited', 'Invited'),
        ('disabled', 'Disabled'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='consultant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tenant__name', 'user__email']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'user'], name='unique_tenant_membership_user'),
        ]
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user_id} @ {self.tenant_id} ({self.role})'


class TenantProfile(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='profile')
    legal_name = models.CharField(max_length=250, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    organization_description = models.TextField(blank=True)
    countries_of_operation = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True)
    core_capabilities = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    past_clients = models.JSONField(default=list, blank=True)
    donor_experience = models.JSONField(default=list, blank=True)
    sector_experience = models.JSONField(default=list, blank=True)
    team_size = models.PositiveIntegerField(default=0)
    annual_bid_capacity = models.PositiveIntegerField(default=0)
    average_contract_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    preferred_contract_size = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile: {self.tenant.name}'


class TenantStrategy(models.Model):
    RISK_APPETITE_CHOICES = [
        ('conservative', 'Conservative'),
        ('balanced', 'Balanced'),
        ('aggressive', 'Aggressive'),
    ]

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='strategy')
    strategic_objectives = models.JSONField(default=list, blank=True)
    target_markets = models.JSONField(default=list, blank=True)
    target_donors = models.JSONField(default=list, blank=True)
    target_sectors = models.JSONField(default=list, blank=True)
    target_countries = models.JSONField(default=list, blank=True)
    priority_project_types = models.JSONField(default=list, blank=True)
    growth_goals = models.JSONField(default=list, blank=True)
    positioning_statement = models.TextField(blank=True)
    risk_appetite = models.CharField(max_length=20, choices=RISK_APPETITE_CHOICES, default='balanced')
    partnership_strategy = models.TextField(blank=True)
    go_no_go_preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Strategy: {self.tenant.name}'


class TenantIntelligenceProfile(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name='intelligence_profile')
    opportunity_keywords = models.JSONField(default=list, blank=True)
    excluded_keywords = models.JSONField(default=list, blank=True)
    preferred_sources = models.JSONField(default=list, blank=True)
    excluded_sources = models.JSONField(default=list, blank=True)
    preferred_procurement_types = models.JSONField(default=list, blank=True)
    minimum_score_threshold = models.PositiveSmallIntegerField(default=50)
    deadline_min_days = models.PositiveSmallIntegerField(null=True, blank=True)
    deadline_max_days = models.PositiveSmallIntegerField(null=True, blank=True)
    minimum_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    maximum_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    requires_local_partner = models.BooleanField(default=False)
    eligible_languages = models.JSONField(default=list, blank=True)
    geographic_priority_weights = models.JSONField(default=dict, blank=True)
    sector_priority_weights = models.JSONField(default=dict, blank=True)
    donor_priority_weights = models.JSONField(default=dict, blank=True)
    scoring_weights = models.JSONField(default=dict, blank=True)
    ai_instructions = models.TextField(blank=True)
    partial_intelligence_rules = models.JSONField(default=dict, blank=True)
    created_from_onboarding = models.BooleanField(default=False)
    last_refined_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Intelligence profile: {self.tenant.name}'


class TenantOnboardingSnapshot(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='onboarding_snapshots')
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_onboarding_submissions',
    )
    responses = models.JSONField(default=dict, blank=True)
    derived_profile = models.JSONField(default=dict, blank=True)
    derived_strategy = models.JSONField(default=dict, blank=True)
    derived_intelligence_profile = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'created_at']),
        ]

    def __str__(self):
        return f'Onboarding {self.tenant.name} @ {self.created_at:%Y-%m-%d}'
