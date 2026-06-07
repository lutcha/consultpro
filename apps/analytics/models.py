from django.db import models


class PredictiveMetric(models.Model):
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='predictive_metrics',
    )
    metric_key = models.CharField(max_length=100, db_index=True)
    country_iso = models.CharField(max_length=20, blank=True, db_index=True)
    sector_code = models.CharField(max_length=100, blank=True, db_index=True)
    forecast_horizon_months = models.PositiveSmallIntegerField(default=3)
    value = models.JSONField(default=dict, blank=True)
    computed_at = models.DateTimeField(auto_now=True)
    valid_until = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-computed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['metric_key', 'country_iso', 'sector_code', 'forecast_horizon_months'],
                name='unique_predictive_metric_scope_horizon',
            )
        ]
        indexes = [
            models.Index(fields=['valid_until', 'metric_key'], name='predictive_metric_valid_idx'),
        ]

    def __str__(self):
        scope = '/'.join(filter(None, [self.country_iso, self.sector_code])) or 'global'
        return f'{self.metric_key} {scope} {self.forecast_horizon_months}m'


class MarketSignal(models.Model):
    SIGNAL_TYPES = [
        ('demand_spike', 'Demand spike detected'),
        ('budget_shift', 'Budget concentration shift'),
        ('seasonal_onset', 'Seasonal demand onset'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    signal_type = models.CharField(max_length=30, choices=SIGNAL_TYPES)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='market_signals',
    )
    country_iso = models.CharField(max_length=20, blank=True, db_index=True)
    sector_code = models.CharField(max_length=100, blank=True, db_index=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    message = models.TextField()
    data_snapshot = models.JSONField(default=dict, blank=True)
    acknowledged = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['signal_type', 'country_iso', 'sector_code']),
            models.Index(fields=['acknowledged', 'created_at']),
        ]

    def __str__(self):
        scope = '/'.join(filter(None, [self.country_iso, self.sector_code])) or 'global'
        return f'{self.signal_type} {scope}'
