from django.contrib import admin

from .models import MarketSignal, PredictiveMetric


@admin.register(PredictiveMetric)
class PredictiveMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_key', 'country_iso', 'sector_code', 'forecast_horizon_months', 'valid_until']
    list_filter = ['metric_key', 'forecast_horizon_months']
    search_fields = ['metric_key', 'country_iso', 'sector_code']


@admin.register(MarketSignal)
class MarketSignalAdmin(admin.ModelAdmin):
    list_display = ['signal_type', 'country_iso', 'sector_code', 'severity', 'acknowledged', 'created_at']
    list_filter = ['signal_type', 'severity', 'acknowledged']
    search_fields = ['message', 'country_iso', 'sector_code']
