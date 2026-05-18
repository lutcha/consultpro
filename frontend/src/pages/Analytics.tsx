// ============================================
// ANALYTICS PAGE
// ============================================

import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import { TrendingUp, Target, Clock, Zap, AlertTriangle, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/utils';
import { apiGetAnalyticsTrends } from '@/lib/api';
import type { ApiAnalyticsTrends } from '@/lib/api';

const SIGNAL_SEVERITY: Record<string, string> = {
  high: 'destructive',
  medium: 'default',
  low: 'secondary',
};

const STATUS_LABELS: Record<string, string> = {
  new: 'Novas',
  analyzing: 'Em Análise',
  go: 'Go',
  no_go: 'No-Go',
  proposal_draft: 'Proposta',
  proposal_review: 'Revisão',
  submitted: 'Submetidas',
  won: 'Ganhas',
  lost: 'Perdidas',
};

function KPITile({ label, value, icon: Icon, sub }: { label: string; value: string | number; icon: React.ElementType; sub?: string }) {
  return (
    <Card>
      <CardContent className="pt-5 pb-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
            {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
          </div>
          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
            <Icon className="h-4 w-4 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function Analytics() {
  const [data, setData] = useState<ApiAnalyticsTrends | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [includeForecast, setIncludeForecast] = useState(false);

  useEffect(() => {
    async function load() {
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiGetAnalyticsTrends({ include_forecast: includeForecast, horizon: 3 });
        setData(result);
      } catch {
        setError('Não foi possível carregar os dados de analytics.');
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [includeForecast]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-28 bg-muted rounded animate-pulse" />)}
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          {[1, 2].map((i) => <div key={i} className="h-64 bg-muted rounded animate-pulse" />)}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <AlertTriangle className="h-10 w-10 text-destructive mb-3" />
        <p className="text-lg font-semibold mb-1">Erro ao carregar analytics</p>
        <p className="text-sm text-muted-foreground mb-4">{error}</p>
        <Button onClick={() => setIsLoading(true)}>Tentar Novamente</Button>
      </div>
    );
  }

  if (!data) return null;

  const { descriptive, weighted_pipeline, proposal_outcomes, win_rate_by_sector, win_rate_by_country, avg_stage_duration_days, signals, predictive, opportunity_status_counts } = data;

  const stageDurationRows = Object.entries(avg_stage_duration_days)
    .map(([status, days]) => ({ status: STATUS_LABELS[status] || status, days }))
    .sort((a, b) => b.days - a.days);

  const forecastChartData = predictive
    ? predictive.point_estimates.map((pt, i) => ({
        month: pt.month,
        tenders: pt.tenders,
        lower: predictive.confidence_intervals[i]?.lower ?? pt.tenders,
        upper: predictive.confidence_intervals[i]?.upper ?? pt.tenders,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
          <p className="text-sm text-muted-foreground">
            Métricas de mercado e desempenho do pipeline
          </p>
        </div>
        <Button
          variant={includeForecast ? 'default' : 'outline'}
          size="sm"
          onClick={() => setIncludeForecast((v) => !v)}
        >
          <Zap className="h-4 w-4 mr-1.5" />
          {includeForecast ? 'Forecast activo' : 'Activar Forecast'}
        </Button>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPITile
          label="Taxa de Vitória"
          value={`${proposal_outcomes.win_rate}%`}
          icon={TrendingUp}
          sub={`${proposal_outcomes.won} ganhas / ${proposal_outcomes.total_decided} decididas`}
        />
        <KPITile
          label="Pipeline Ponderado"
          value={formatCurrency(weighted_pipeline.weighted_value, weighted_pipeline.currency)}
          icon={Target}
          sub={`Total: ${formatCurrency(weighted_pipeline.total_value, weighted_pipeline.currency)}`}
        />
        <KPITile
          label="Lead Time Médio"
          value={`${descriptive.avg_lead_time_days ?? 0}d`}
          icon={Clock}
          sub={`Mediana: ${descriptive.median_lead_time_days ?? 0}d`}
        />
        <KPITile
          label="Velocidade de Procura"
          value={`${descriptive.demand_velocity ?? 0}×`}
          icon={Zap}
          sub={descriptive.demand_velocity >= 1.4 ? 'Acima do baseline' : 'Normal'}
        />
      </div>

      {/* Signals */}
      {signals.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Sinais de Mercado</h2>
          <div className="grid gap-2 sm:grid-cols-2">
            {signals.map((s, i) => (
              <div key={i} className="flex items-start gap-2 p-3 rounded-lg border bg-muted/30">
                <Badge variant={SIGNAL_SEVERITY[s.severity] as 'default' | 'secondary' | 'destructive'} className="shrink-0 mt-0.5">
                  {s.severity}
                </Badge>
                <p className="text-xs">{s.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Win rate charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {win_rate_by_sector.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Taxa de Vitória por Sector</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={win_rate_by_sector} layout="vertical" margin={{ left: 10, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="sector" tick={{ fontSize: 11 }} width={90} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Bar dataKey="win_rate" name="Win Rate" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {win_rate_by_country.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Taxa de Vitória por País</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={win_rate_by_country} layout="vertical" margin={{ left: 10, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="country" tick={{ fontSize: 11 }} width={90} />
                  <Tooltip formatter={(v) => `${v}%`} />
                  <Bar dataKey="win_rate" name="Win Rate" fill="hsl(var(--primary) / 0.7)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Stage duration + Status counts */}
      <div className="grid lg:grid-cols-2 gap-6">
        {stageDurationRows.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Duração Média por Fase (dias)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={stageDurationRows} layout="vertical" margin={{ left: 10, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="status" tick={{ fontSize: 11 }} width={90} />
                  <Tooltip />
                  <Bar dataKey="days" name="Dias" fill="hsl(var(--primary) / 0.5)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {Object.keys(opportunity_status_counts).length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Oportunidades por Estado</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2 pt-1">
                {Object.entries(opportunity_status_counts).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
                    <span className="text-xs text-muted-foreground">{STATUS_LABELS[status] || status}</span>
                    <span className="text-sm font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Forecast */}
      {includeForecast && predictive && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">Forecast de Procura ({data.meta.horizon_months} meses)</CardTitle>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Info className="h-3 w-3" />
                Confiança: {Math.round((predictive.model_diagnostics.confidence_score ?? 0) * 100)}%
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={forecastChartData} margin={{ left: 0, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="upper" name="Limite Superior" stroke="transparent" fill="hsl(var(--primary) / 0.1)" />
                <Area type="monotone" dataKey="tenders" name="Estimativa" stroke="hsl(var(--primary))" fill="hsl(var(--primary) / 0.2)" strokeWidth={2} />
                <Area type="monotone" dataKey="lower" name="Limite Inferior" stroke="transparent" fill="white" />
              </AreaChart>
            </ResponsiveContainer>
            {predictive.recommendations.length > 0 && (
              <div className="mt-3 space-y-1">
                {predictive.recommendations.map((rec, i) => (
                  <p key={i} className="text-xs text-muted-foreground flex items-start gap-1.5">
                    <span className="text-primary mt-0.5">→</span> {rec}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {includeForecast && !predictive && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Dados insuficientes para gerar forecast. Adicione mais oportunidades ao sistema.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
