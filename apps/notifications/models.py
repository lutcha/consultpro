from django.db import models

from apps.users.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('info', 'Informacao'),
        ('success', 'Sucesso'),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_label = models.CharField(max_length=100, blank=True)
    action_url = models.CharField(max_length=500, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.title}"


class ActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('proposal_created', 'Proposta Criada'),
        ('proposal_updated', 'Proposta Atualizada'),
        ('opportunity_added', 'Oportunidade Adicionada'),
        ('qc_completed', 'QC Completado'),
        ('comment_added', 'Comentario Adicionado'),
        ('status_changed', 'Estado Alterado'),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
    )
    type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.description[:50]}"
