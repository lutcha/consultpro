from django.db import models

from apps.proposals.models import Proposal
from apps.users.models import User


class QualityCheck(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('running', 'A executar'),
        ('completed', 'Completo'),
        ('failed', 'Falhou'),
    ]

    proposal = models.OneToOneField(
        Proposal,
        on_delete=models.CASCADE,
        related_name='quality_check',
    )
    overall_score = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    can_submit = models.BooleanField(default=False)
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


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

    quality_check = models.ForeignKey(
        QualityCheck,
        on_delete=models.CASCADE,
        related_name='categories',
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
    )
    score = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
    )


class QCItem(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Aprovado'),
        ('warn', 'Atencao'),
        ('fail', 'Reprovado'),
    ]

    category = models.ForeignKey(
        QCCheckCategory,
        on_delete=models.CASCADE,
        related_name='items',
    )
    description = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
    )
    section = models.CharField(max_length=200, blank=True)


class QCSuggestion(models.Model):
    ACTION_CHOICES = [
        ('replace', 'Substituir'),
        ('add', 'Adicionar'),
        ('remove', 'Remover'),
    ]

    quality_check = models.ForeignKey(
        QualityCheck,
        on_delete=models.CASCADE,
        related_name='suggestions',
    )
    text = models.TextField()
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
    )
    target_section = models.CharField(max_length=200)
    applied = models.BooleanField(default=False)
    ignored = models.BooleanField(default=False)
