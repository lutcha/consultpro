from django.db import models


class Proposal(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('in_review', 'Em Revisao'),
        ('qc_check', 'QC em Curso'),
        ('approved', 'Aprovada'),
        ('submitted', 'Submetida'),
        ('won', 'Ganha'),
        ('lost', 'Perdida'),
    ]

    opportunity = models.ForeignKey(
        'opportunities.Opportunity',
        on_delete=models.CASCADE,
        related_name='proposals',
    )
    title = models.CharField(max_length=500)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    auto_save_status = models.CharField(
        max_length=20,
        choices=[
            ('idle', 'Idle'),
            ('saving', 'A guardar'),
            ('saved', 'Guardado'),
            ('error', 'Erro'),
        ],
        default='idle',
    )
    last_saved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_proposals',
    )
    team_members = models.ManyToManyField(
        'users.User',
        through='ProposalTeamMember',
        related_name='proposals',
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class ProposalTeamMember(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    role = models.CharField(max_length=200)
    hours = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cv_attached = models.BooleanField(default=False)
    cv_document = models.FileField(upload_to='cv_documents/', null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.role}"


class ProposalSection(models.Model):
    SECTION_TYPE_CHOICES = [
        ('cover', 'Capa'),
        ('executive_summary', 'Resumo Executivo'),
        ('methodology', 'Metodologia'),
        ('team', 'Equipa Tecnica'),
        ('workplan', 'Plano de Trabalho'),
        ('budget', 'Orcamento'),
        ('annexes', 'Anexos'),
    ]

    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    section_type = models.CharField(max_length=30, choices=SECTION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.proposal.title} - {self.title}"


class Comment(models.Model):
    section = models.ForeignKey(
        ProposalSection,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    text = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.section}"


class AISuggestion(models.Model):
    ACTION_CHOICES = [
        ('expand', 'Expandir'),
        ('summarize', 'Resumir'),
        ('tone_formal', 'Ajustar Tom'),
        ('translate_en', 'Traduzir EN'),
    ]

    section = models.ForeignKey(
        ProposalSection,
        on_delete=models.CASCADE,
        related_name='ai_suggestions',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    generated_content = models.TextField(blank=True)
    applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.section}"


class Budget(models.Model):
    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        related_name='budget',
    )
    total = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')

    def __str__(self):
        return f"Budget for {self.proposal.title}"


class BudgetItem(models.Model):
    CATEGORY_CHOICES = [
        ('personnel', 'Pessoal'),
        ('travel', 'Viagens'),
        ('equipment', 'Equipamentos'),
        ('materials', 'Materiais'),
        ('overhead', 'Overhead'),
        ('other', 'Outros'),
    ]

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name='items',
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.category} - {self.amount}"
