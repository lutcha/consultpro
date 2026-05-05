from django.db import models
from apps.users.models import User
from apps.proposals.models import Proposal


class QualityCheck(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'A executar'),
        ('completed', 'Completo'),
        ('failed', 'Falhou'),
    ]

    proposal = models.OneToOneField(Proposal, on_delete=models.CASCADE, related_name='quality_check')
    overall_score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    can_submit = models.BooleanField(default=False)
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Quality Checks'

    def __str__(self):
        return f"QC for {self.proposal.title} - {self.overall_score}"


class QCCheckCategory(models.Model):
    CATEGORY_CHOICES = [
        ('compliance', 'Conformidade com ToR'),
        ('coherence', 'Coerencia Narrativa'),
        ('budget', 'Orcamento'),
        ('attachments', 'Anexos'),
    ]
    STATUS_CHOICES = [
        ('pass', 'Aprovado'),
        ('warn', 'Atencao'),
        ('fail', 'Reprovado'),
    ]

    quality_check = models.ForeignKey(QualityCheck, on_delete=models.CASCADE, related_name='categories')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['quality_check', 'category']
        verbose_name_plural = 'QC Check Categories'

    def __str__(self):
        return f"{self.get_category_display()} - {self.get_status_display()}"


class QCItem(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Aprovado'),
        ('warn', 'Atencao'),
        ('fail', 'Reprovado'),
    ]

    category = models.ForeignKey(QCCheckCategory, on_delete=models.CASCADE, related_name='items')
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    section = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'QC Items'

    def __str__(self):
        return f"{self.get_status_display()} - {self.description[:50]}"


class QCSuggestion(models.Model):
    ACTION_CHOICES = [
        ('replace', 'Substituir'),
        ('add', 'Adicionar'),
        ('remove', 'Remover'),
    ]

    quality_check = models.ForeignKey(QualityCheck, on_delete=models.CASCADE, related_name='suggestions')
    text = models.TextField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    target_section = models.CharField(max_length=200)
    applied = models.BooleanField(default=False)
    ignored = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'QC Suggestions'

    def __str__(self):
        return f"{self.get_action_display()} - {self.target_section}"

