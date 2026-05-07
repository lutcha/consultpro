from django.db import models


class AIConfiguration(models.Model):
    provider = models.CharField(max_length=30, default='openai')
    model = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI Configuration'
        verbose_name_plural = 'AI Configuration'

    def __str__(self):
        return f'{self.provider} ({self.model or "default"})'

    @classmethod
    def current(cls):
        config, _created = cls.objects.get_or_create(pk=1)
        return config
