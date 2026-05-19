from django.db import models

from apps.proposals.models import Proposal, ProposalSection
from apps.users.models import User


class IssueTreeNode(models.Model):
    NODE_TYPE_CHOICES = [
        ('root', 'Root'),
        ('issue', 'Issue'),
        ('hypothesis', 'Hypothesis'),
        ('evidence', 'Evidence'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In progress'),
        ('validated', 'Validated'),
        ('rejected', 'Rejected'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='issue_tree_nodes',
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    source_key = models.CharField(max_length=160, null=True, blank=True)
    node_type = models.CharField(max_length=20, choices=NODE_TYPE_CHOICES, default='issue')
    title = models.CharField(max_length=255)
    hypothesis = models.TextField(blank=True)
    data_needed = models.JSONField(default=list, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_issue_tree_nodes',
    )
    proposal_section = models.ForeignKey(
        ProposalSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issue_tree_nodes',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    order = models.PositiveIntegerField(default=0)
    source_trace = models.JSONField(default=list, blank=True)
    ai_metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_issue_tree_nodes',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['proposal_id', 'parent_id', 'order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['proposal', 'source_key'],
                name='unique_issue_tree_node_source_key_per_proposal',
            )
        ]
        indexes = [
            models.Index(fields=['proposal', 'parent']),
            models.Index(fields=['proposal', 'status']),
            models.Index(fields=['proposal', 'node_type']),
        ]

    def __str__(self):
        return f'{self.proposal_id} {self.title}'


class IssueTreeSnapshot(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='issue_tree_snapshots',
    )
    version = models.PositiveIntegerField()
    label = models.CharField(max_length=120, blank=True)
    snapshot = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_issue_tree_snapshots',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version']
        constraints = [
            models.UniqueConstraint(
                fields=['proposal', 'version'],
                name='unique_issue_tree_snapshot_version_per_proposal',
            )
        ]

    def __str__(self):
        return f'{self.proposal_id} v{self.version}'
