from django.db import models

from apps.users.models import User
from .constants import SECTOR_CHOICES, REGION_CHOICES, COUNTRY_CHOICES


class Opportunity(models.Model):
    STATUS_CHOICES = [
        ('new', 'Novo'),
        ('analyzing', 'Em Analise'),
        ('go', 'Go'),
        ('no_go', 'No-Go'),
        ('proposal_draft', 'Proposta em Rascunho'),
        ('proposal_review', 'Proposta em Revisao'),
        ('submitted', 'Submetida'),
        ('won', 'Ganha'),
        ('lost', 'Nao Aprovada'),
    ]
    EVALUATION_CRITERIA_CHOICES = [
        ('qcbs', 'QCBS (Qualidade e Custo)'),
        ('cqs', 'CQS (Qualidade apenas)'),
        ('lcs', 'LCS (Custo mais baixo)'),
        ('fbs', 'FBS (Baseado em Fixo)'),
    ]
    CONSORTIUM_TYPE_CHOICES = [
        ('solo', 'Solo'),
        ('lead', 'Líder de Consórcio'),
        ('partner', 'Parceiro de Consórcio'),
        ('open', 'Aberto a Consórcio'),
    ]

    title = models.CharField(max_length=500)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='opportunities',
    )
    client = models.CharField(max_length=200)
    client_logo = models.ImageField(upload_to='client_logos/', null=True, blank=True)
    sector = models.CharField(max_length=100, choices=SECTOR_CHOICES)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    region = models.CharField(max_length=100, blank=True, choices=REGION_CHOICES)
    eligible_countries = models.JSONField(
        default=list, blank=True,
        help_text='Lista de códigos de países elegíveis (ISO 2-letras)',
    )
    value = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    deadline = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    description = models.TextField()
    evaluation_criteria = models.CharField(
        max_length=10, choices=EVALUATION_CRITERIA_CHOICES, default='qcbs'
    )
    technical_weight = models.PositiveIntegerField(default=70)
    financial_weight = models.PositiveIntegerField(default=30)
    tor_document = models.FileField(upload_to='tor_documents/', null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    url_source = models.URLField(blank=True)
    consortium_type = models.CharField(
        max_length=20, choices=CONSORTIUM_TYPE_CHOICES, default='solo'
    )
    consortium_notes = models.TextField(blank=True)
    partner_profiles = models.JSONField(default=list, blank=True)
    ai_summary = models.TextField(blank=True)
    ai_extraction = models.JSONField(default=dict, blank=True)
    ai_analysis_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('queued', 'Em fila'),
            ('processing', 'A processar'),
            ('completed', 'Completo'),
            ('failed', 'Falhou'),
        ],
        default='pending',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_opportunities',
    )
    assigned_to = models.ManyToManyField(
        User,
        related_name='assigned_opportunities',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Opportunities'

    def __str__(self):
        return self.title


class OpportunityScore(models.Model):
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='scores',
    )
    strategic_fit = models.PositiveSmallIntegerField(default=0)
    win_probability = models.PositiveSmallIntegerField(default=0)
    margin = models.PositiveSmallIntegerField(default=0)
    risk = models.PositiveSmallIntegerField(default=0)
    resource = models.PositiveSmallIntegerField(default=0)
    overall_score = models.PositiveSmallIntegerField(default=0)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    ai_extracted_criteria = models.JSONField(default=dict, blank=True)
    evaluation_weights = models.JSONField(default=dict, blank=True)
    reasoning_trace = models.JSONField(default=list, blank=True)
    input_snapshot = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=50, default='deterministic')
    model = models.CharField(max_length=100, blank=True)
    scoring_version = models.CharField(max_length=40, default='opportunity_score_v1')
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['opportunity', 'is_current'], name='opportunity_score_current_idx'),
            models.Index(fields=['scoring_version'], name='opportunity_score_version_idx'),
        ]

    def __str__(self):
        return f'{self.opportunity_id} score {self.overall_score}'


class FirmProfile(models.Model):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='firm_profiles',
    )
    name = models.CharField(max_length=200, default='Default firm profile')
    target_sectors = models.JSONField(default=list, blank=True)
    geographies = models.JSONField(default=list, blank=True)
    scoring_weights_override = models.JSONField(default=dict, blank=True)
    is_default = models.BooleanField(default=True, db_index=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_firm_profiles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-updated_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            queryset = FirmProfile.objects.exclude(pk=self.pk).filter(is_default=True)
            if self.tenant_id:
                queryset = queryset.filter(tenant_id=self.tenant_id)
            else:
                queryset = queryset.filter(tenant__isnull=True)
            queryset.update(is_default=False)

    def __str__(self):
        return self.name


class SavedFilter(models.Model):
    VIEW_TYPE_CHOICES = [
        ('opportunities', 'Opportunities'),
        ('scraping', 'Scraping'),
        ('proposals', 'Proposals'),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_filters',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='saved_filters',
    )
    name = models.CharField(max_length=120)
    view_type = models.CharField(max_length=40, choices=VIEW_TYPE_CHOICES, default='opportunities')
    payload = models.JSONField(default=dict, blank=True)
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['view_type', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'view_type', 'name'],
                name='unique_saved_filter_per_owner_view_name',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.view_type})'


class Requirement(models.Model):
    CATEGORY_CHOICES = [
        ('functional', 'Funcionais'),
        ('technical', 'Tecnicos'),
        ('institutional', 'Institucionais'),
        ('financial', 'Financeiros'),
    ]
    PRIORITY_CHOICES = [
        ('mandatory', 'Obrigatorio'),
        ('preferred', 'Preferencial'),
        ('optional', 'Opcional'),
    ]

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='requirements',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default='mandatory'
    )
    is_covered = models.BooleanField(default=False)
    covered_in = models.CharField(max_length=200, blank=True)
    extracted_by_ai = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.category} - {self.description[:50]}"


class Risk(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baixo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
    ]

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='risks',
    )
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    mitigation = models.TextField(blank=True)
    identified_by_ai = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.severity} - {self.description[:50]}"
