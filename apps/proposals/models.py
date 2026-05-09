from django.db import models
from django.utils import timezone
from apps.users.models import User
from apps.opportunities.models import Opportunity


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('in_review', 'Em Revisao'),
        ('qc_check', 'QC em Curso'),
        ('ready_for_submission', 'Pronta para Submissao'),
        ('approved', 'Aprovada'),
        ('submitted', 'Submetida'),
        ('under_evaluation', 'Em Avaliacao'),
        ('rejected', 'Rejeitada'),
        ('shortlisted', 'Shortlisted'),
        ('clarifications_requested', 'Clarificacoes Pedidas'),
        ('bafo', 'BAFO'),
        ('awarded', 'Adjudicada'),
        ('contract_negotiation', 'Negociacao de Contrato'),
        ('contract_signed', 'Contrato Assinado'),
        ('project_initiation', 'Arranque de Projeto'),
        ('won', 'Ganha'),
        ('lost', 'Perdida'),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name='proposals')
    title = models.CharField(max_length=500)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')
    
    # Auto-save tracking
    auto_save_status = models.CharField(
        max_length=20,
        choices=[('idle', 'Idle'), ('saving', 'A guardar'), ('saved', 'Guardado'), ('error', 'Erro')],
        default='idle'
    )
    last_saved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_proposals')
    team_members = models.ManyToManyField(User, through='ProposalTeamMember', related_name='proposals')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Document branding
    proponent_logo = models.ImageField(
        upload_to='proposals/logos/proponent/',
        blank=True,
        null=True,
        help_text='Logo da empresa proponente ou consórcio',
    )
    client_logo = models.ImageField(
        upload_to='proposals/logos/client/',
        blank=True,
        null=True,
        help_text='Logo do cliente',
    )
    consortium_members = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de membros do consórcio (se aplicável)',
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} (v{self.version})"


class ProposalStatusHistory(models.Model):
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    status = models.CharField(max_length=30, choices=Proposal.STATUS_CHOICES)
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_status_changes',
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Proposal status history'
        verbose_name_plural = 'Proposal status histories'

    def __str__(self):
        return f"{self.proposal} -> {self.status}"


class ProposalEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('submission', 'Submissao'),
        ('evaluation', 'Avaliacao'),
        ('shortlist', 'Shortlist'),
        ('clarification', 'Clarificacao'),
        ('bafo', 'BAFO'),
        ('award', 'Adjudicacao'),
        ('contracting', 'Contratacao'),
        ('handover', 'Handover'),
        ('note', 'Nota'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    external_url = models.URLField(blank=True)
    attachment = models.FileField(
        upload_to='proposals/events/%Y/%m/',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-occurred_at', '-created_at']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.proposal}"


class ProposalTeamMember(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='team_members_detail')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=200)  # Team Leader, Especialista, etc.
    hours = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cv_attached = models.BooleanField(default=False)
    cv_document = models.FileField(upload_to='cv_documents/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['proposal', 'user']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email} - {self.role}"


class ProposalSection(models.Model):
    SECTION_TYPE_CHOICES = [
        ('cover', 'Capa'),
        ('executive_summary', 'Resumo Executivo'),
        ('methodology', 'Metodologia'),
        ('team', 'Equipa Tecnica'),
        ('workplan', 'Plano de Trabalho'),
        ('budget', 'Orcamento'),
        ('annexes', 'Anexos'),
        ('custom', 'Personalizada'),
    ]

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='sections')
    section_type = models.CharField(max_length=30, choices=SECTION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.title} - {self.proposal.title}"


class Comment(models.Model):
    section = models.ForeignKey(ProposalSection, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.email} on {self.section.title}"


class AISuggestion(models.Model):
    ACTION_CHOICES = [
        ('draft_from_context', 'Gerar Rascunho'),
        ('expand', 'Expandir'),
        ('improve', 'Melhorar'),
        ('summarize', 'Resumir'),
        ('tone_formal', 'Ajustar Tom'),
        ('translate_en', 'Traduzir EN'),
    ]

    section = models.ForeignKey(ProposalSection, on_delete=models.CASCADE, related_name='ai_suggestions')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    generated_content = models.TextField(blank=True)
    applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.section.title}"


class Budget(models.Model):
    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, related_name='budget')
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Budgets'

    def __str__(self):
        return f"Budget for {self.proposal.title} - {self.total} {self.currency}"


class BudgetItem(models.Model):
    CATEGORY_CHOICES = [
        ('personnel', 'Pessoal'),
        ('travel', 'Viagens'),
        ('equipment', 'Equipamentos'),
        ('materials', 'Materiais'),
        ('overhead', 'Overhead'),
        ('other', 'Outros'),
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category']

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} {self.budget.currency}"
