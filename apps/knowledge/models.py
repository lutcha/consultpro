from django.db import models

from apps.users.models import User


class KnowledgeAsset(models.Model):
    ASSET_TYPE_CHOICES = [
        ('proposal', 'Proposal'),
        ('proposal_section', 'Proposal section'),
        ('project', 'Project'),
        ('case', 'Case'),
        ('consultant_profile', 'Consultant profile'),
        ('cv', 'CV'),
        ('template', 'Template'),
        ('pricing', 'Pricing'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    asset_type = models.CharField(max_length=40, choices=ASSET_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=300)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    source_app = models.CharField(max_length=80, blank=True)
    source_model = models.CharField(max_length=120, blank=True)
    source_id = models.CharField(max_length=80, null=True, blank=True)
    source_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    country = models.CharField(max_length=100, blank=True, db_index=True)
    sector = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    indexed_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_knowledge_assets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['source_app', 'source_model', 'source_id'],
                name='unique_knowledge_asset_source',
            )
        ]
        indexes = [
            models.Index(fields=['asset_type', 'status']),
            models.Index(fields=['country', 'sector']),
            models.Index(fields=['source_app', 'source_model']),
        ]

    def __str__(self):
        return f'{self.asset_type}: {self.title}'
