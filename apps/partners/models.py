from django.db import models


class PartnerProfile(models.Model):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='partner_profiles',
    )
    name = models.CharField(max_length=200)
    sectors = models.JSONField(default=list, blank=True)
    geographies = models.JSONField(default=list, blank=True)
    capabilities = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    trust_score = models.PositiveSmallIntegerField(default=50)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-trust_score', 'name']

    def __str__(self):
        return self.name
