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


class PursuitGate(models.Model):
    GATE_TYPE_CHOICES = [
        ('strategic_fit', 'Strategic fit'),
        ('commercial_viability', 'Commercial viability'),
        ('delivery_capacity', 'Delivery capacity'),
        ('partner_approval', 'Partner approval'),
    ]
    REQUIRED_ROLE_CHOICES = [
        ('consultant', 'Consultant'),
        ('manager', 'Manager'),
        ('admin', 'Partner/Admin'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waived', 'Waived'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='pursuit_gates',
    )
    gate_type = models.CharField(max_length=40, choices=GATE_TYPE_CHOICES)
    required_role = models.CharField(max_length=20, choices=REQUIRED_ROLE_CHOICES)
    is_required = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rationale = models.TextField(blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_pursuit_gates',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['proposal', 'gate_type'],
                name='unique_pursuit_gate_per_proposal_type',
            )
        ]

    def __str__(self):
        return f'{self.proposal_id} {self.gate_type} {self.status}'


class GateAuditLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waived', 'Waived'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='gate_audit_logs',
    )
    gate = models.ForeignKey(
        PursuitGate,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pursuit_gate_audit_logs',
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def delete(self, *args, **kwargs):
        raise PermissionError('Gate audit logs are append-only.')

    def __str__(self):
        return f'{self.proposal_id} {self.gate.gate_type} {self.action}'


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
    ARTIFACT_TYPE_CHOICES = [
        ('', 'Sem artefacto'),
        ('final_proposal', 'Proposta Final'),
        ('contract', 'Contrato'),
        ('handover', 'Handover Package'),
        ('kickoff', 'Kickoff Pack'),
        ('checklist', 'Checklist de Arranque'),
        ('other', 'Outro'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='events',
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    artifact_type = models.CharField(
        max_length=30,
        choices=ARTIFACT_TYPE_CHOICES,
        blank=True,
    )
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


class ProposalPostMortem(models.Model):
    OUTCOME_CHOICES = [
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
        ('no_decision', 'No decision'),
    ]

    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        related_name='post_mortem',
    )
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES)
    outcome_reason = models.TextField(blank=True)
    client_feedback = models.TextField(blank=True)
    lessons_learned = models.JSONField(default=list, blank=True)
    scoring_adjustments = models.JSONField(default=dict, blank=True)
    sentiment = models.CharField(max_length=20, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_post_mortems',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.proposal_id} {self.outcome}'


class ProposalExportRequest(models.Model):
    EXPORT_TYPE_CHOICES = [
        ('executive_summary', 'Executive summary'),
        ('board_pack', 'Board pack'),
        ('pdf', 'PDF'),
        ('pptx', 'PPTX'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='export_requests',
    )
    export_type = models.CharField(max_length=30, choices=EXPORT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_export_requests',
    )
    parameters = models.JSONField(default=dict, blank=True)
    executive_summary = models.TextField(blank=True)
    output_metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    task_id = models.CharField(max_length=255, blank=True)
    execution_attempts = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['proposal', 'status'], name='proposals_p_proposa_9e1c4d_idx'),
            models.Index(fields=['export_type', 'created_at'], name='proposals_p_export_55ab97_idx'),
        ]

    def __str__(self):
        return f'{self.proposal_id} {self.export_type} {self.status}'


class ProposalTeamMember(models.Model):
    TEAM_MEMBER_STATUS_CHOICES = [
        ('suggested_profile', 'Perfil Sugerido'),
        ('consultant_in_negotiation', 'Consultor em Negociacao'),
        ('cv_pending', 'CV Pendente'),
        ('confirmed', 'Confirmado'),
    ]

    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='team_members_detail')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=200)
    hours = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cv_attached = models.BooleanField(default=False)
    cv_document = models.FileField(upload_to='cv_documents/', null=True, blank=True)
    team_member_status = models.CharField(
        max_length=30,
        choices=TEAM_MEMBER_STATUS_CHOICES,
        default='cv_pending',
    )
    curriculum = models.ForeignKey(
        'curriculum.Curriculum',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proposal_memberships',
    )
    suggested_profile = models.JSONField(
        default=dict,
        blank=True,
        help_text='Free-text profile description for suggested (non-user) slots.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['proposal', 'user'],
                condition=models.Q(user__isnull=False),
                name='unique_proposal_user_when_set',
            )
        ]

    def __str__(self):
        if self.user_id:
            return f"{self.user.get_full_name() or self.user.email} - {self.role}"
        label = (self.suggested_profile or {}).get('name') or 'Perfil Sugerido'
        return f"{label} - {self.role}"


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
