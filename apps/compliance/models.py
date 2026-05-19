from django.db import models

from apps.opportunities.models import Opportunity
from apps.proposals.models import ProposalSection
from apps.users.models import User


class ComplianceMatrix(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('in_review', 'In review'),
        ('approved', 'Approved'),
    ]

    opportunity = models.OneToOneField(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='compliance_matrix',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    generation_version = models.CharField(max_length=40, default='compliance_matrix_v1')
    source_trace = models.JSONField(default=list, blank=True)
    ai_metadata = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    human_override_count = models.PositiveIntegerField(default=0)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_compliance_matrices',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Compliance matrix for opportunity {self.opportunity_id}'


class ComplianceMatrixRow(models.Model):
    PRIORITY_CHOICES = [
        ('mandatory', 'Mandatory'),
        ('desirable', 'Desirable'),
        ('optional', 'Optional'),
    ]
    STATUS_CHOICES = [
        ('missing', 'Missing'),
        ('partial', 'Partial'),
        ('covered', 'Covered'),
        ('waived', 'Waived'),
    ]

    matrix = models.ForeignKey(
        ComplianceMatrix,
        on_delete=models.CASCADE,
        related_name='rows',
    )
    requirement_key = models.CharField(max_length=120)
    requirement_text = models.TextField()
    requirement_category = models.CharField(max_length=40, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='mandatory')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='missing')
    proposal_section = models.ForeignKey(
        ProposalSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='compliance_rows',
    )
    evidence_text = models.TextField(blank=True)
    evidence_link = models.URLField(blank=True)
    source_type = models.CharField(max_length=40, default='requirement')
    source_reference = models.CharField(max_length=255, blank=True)
    source_trace = models.JSONField(default=dict, blank=True)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    ai_metadata = models.JSONField(default=dict, blank=True)
    human_override = models.BooleanField(default=False)
    human_override_note = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['matrix', 'requirement_key'],
                name='unique_compliance_row_per_matrix_key',
            )
        ]
        indexes = [
            models.Index(fields=['matrix', 'status']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return f'{self.matrix_id} {self.requirement_key} {self.status}'
