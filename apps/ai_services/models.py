from django.conf import settings
from django.db import models


class AIConfiguration(models.Model):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_configurations',
    )
    provider = models.CharField(max_length=30, default='openai')
    model = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI Configuration'
        verbose_name_plural = 'AI Configuration'

    def __str__(self):
        return f'{self.provider} ({self.model or "default"})'

    @classmethod
    def current(cls, tenant=None):
        if tenant is not None:
            config, _created = cls.objects.get_or_create(
                tenant=tenant,
                defaults={'provider': getattr(settings, 'AI_PROVIDER', 'openai')},
            )
            return config
        config, _created = cls.objects.get_or_create(
            pk=1,
            defaults={'provider': getattr(settings, 'AI_PROVIDER', 'openai')},
        )
        return config
