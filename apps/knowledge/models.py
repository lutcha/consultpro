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
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='knowledge_assets',
    )
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


class KnowledgeIndexRun(models.Model):
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]
    SOURCE_CHOICES = [
        ('all', 'All'),
        ('proposals', 'Proposals'),
        ('projects', 'Projects'),
        ('curriculum', 'Curriculum'),
    ]

    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='all', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running', db_index=True)
    indexed_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    stats = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='knowledge_index_runs',
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f'{self.source} reindex {self.status} ({self.indexed_count})'

    def as_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'status': self.status,
            'indexed_count': self.indexed_count,
            'error_count': self.error_count,
            'stats': self.stats,
            'errors': self.errors,
            'celery_task_id': self.celery_task_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
