"""
Projects app - manages projects created from won proposals.
Follows project management best practices.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.users.models import User
from apps.proposals.models import Proposal


class Project(models.Model):
    """A project created from a won proposal."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Em Planeamento'
        ACTIVE = 'active', 'Em Execução'
        ON_HOLD = 'on_hold', 'Em Pausa'
        COMPLETED = 'completed', 'Concluído'
        CLOSED = 'closed', 'Fechado'

    # Core fields
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.PROTECT,
        related_name='project',
        null=True,
        blank=True,
    )

    # Client info
    client = models.CharField(max_length=200)
    client_contact_name = models.CharField(max_length=200, blank=True)
    client_contact_email = models.EmailField(blank=True)

    # Project lifecycle
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNING,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)

    # Financial tracking
    budget_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_currency = models.CharField(max_length=3, default='USD')
    actual_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Progress
    progress = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # Team
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects',
    )
    team_members = models.ManyToManyField(
        User,
        through='ProjectTeamMember',
        related_name='projects',
        blank=True,
    )

    # Metadata
    sector = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)

    # Deliverables tracking
    deliverables_count = models.PositiveIntegerField(default=0)
    deliverables_completed = models.PositiveIntegerField(default=0)

    # Risk & issues
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Baixo'),
            ('medium', 'Médio'),
            ('high', 'Alto'),
            ('critical', 'Crítico'),
        ],
        default='low',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.title

    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.end_date:
            return (self.end_date - timezone.now().date()).days
        return None

    @property
    def budget_utilization(self):
        if self.budget_total > 0:
            return int((self.actual_cost / self.budget_total) * 100)
        return 0

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.end_date and self.status not in (self.Status.COMPLETED, self.Status.CLOSED):
            return self.end_date < timezone.now().date()
        return False


class ProjectTeamMember(models.Model):
    """Team member assignment to a project with role and allocation."""

    class Role(models.TextChoices):
        TEAM_LEAD = 'team_lead', 'Team Lead'
        TECHNICAL_LEAD = 'technical_lead', 'Technical Lead'
        CONSULTANT = 'consultant', 'Consultor'
        SPECIALIST = 'specialist', 'Especialista'
        SUPPORT = 'support', 'Suporte'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_team_members',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_assignments',
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.CONSULTANT,
    )
    allocation_percentage = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.role} @ {self.project.title}"


class ProjectMilestone(models.Model):
    """Project milestones for tracking progress."""

    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Não Iniciado'
        IN_PROGRESS = 'in_progress', 'Em Curso'
        COMPLETED = 'completed', 'Concluído'
        DELAYED = 'delayed', 'Atrasado'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED,
    )
    deliverables = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} ({self.project.title})"


class ProjectRisk(models.Model):
    """Project risks and issues tracking."""

    class Severity(models.TextChoices):
        LOW = 'low', 'Baixo'
        MEDIUM = 'medium', 'Médio'
        HIGH = 'high', 'Alto'
        CRITICAL = 'critical', 'Crítico'

    class Status(models.TextChoices):
        OPEN = 'open', 'Aberto'
        MITIGATED = 'mitigated', 'Mitigado'
        CLOSED = 'closed', 'Fechado'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_risks',
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.LOW,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    mitigation_plan = models.TextField(blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_risks',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-severity', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.project.title})"


class ProjectDeliverable(models.Model):
    """Project deliverables tracking."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Rascunho'
        UNDER_REVIEW = 'under_review', 'Em Revisão'
        APPROVED = 'approved', 'Aprovado'
        SUBMITTED = 'submitted', 'Submetido'
        ACCEPTED = 'accepted', 'Aceite'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='project_deliverables',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    document = models.FileField(
        upload_to='projects/deliverables/%Y/%m/',
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return self.title
