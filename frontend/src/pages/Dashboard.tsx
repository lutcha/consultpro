// ============================================
// DASHBOARD PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  FileText,
  TrendingUp,
  Clock,
  Calendar,
  Plus,
  FolderKanban,
  Database,
  Target,
  DollarSign,
  AlertTriangle,
  ChevronRight,
  TrendingDown,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { KPICard } from '@/components/dashboard/KPICard';
import { ProposalTable } from '@/components/dashboard/ProposalTable';
import { AlertBanner } from '@/components/dashboard/AlertBanner';
import { ActivityTimeline } from '@/components/dashboard/ActivityTimeline';
import { useUserStore, useOpportunityStore } from '@/stores';
import {
  apiGetDashboardStats,
  apiGetDashboardPipeline,
  apiGetDashboardAlerts,
  apiGetDashboardActivity,
  apiGetDashboardFunnel,
} from '@/lib/api';
import {
  mapApiDashboardStats,
  mapApiPipelineItem,
  mapApiAlert,
  mapApiActivity,
  mapApiFunnel,
} from '@/lib/apiMappers';
import { formatCurrency } from '@/lib/utils';
import type { DashboardStats, PipelineItem, Alert, Activity, FunnelData } from '@/types';

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { fetchOpportunities } = useOpportunityStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pipeline, setPipeline] = useState<PipelineItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchOpportunities();

    async function loadDashboard() {
      setIsLoading(true);
      setError(null);
      try {
        const [statsData, pipelineData, alertsData, activityData, funnelData] =
          await Promise.all([
            apiGetDashboardStats(),
            apiGetDashboardPipeline(),
            apiGetDashboardAlerts(),
            apiGetDashboardActivity(),
            apiGetDashboardFunnel(),
          ]);
        setStats(mapApiDashboardStats(statsData));
        setPipeline(pipelineData.map(mapApiPipelineItem));
        setAlerts(alertsData.map(mapApiAlert));
        setActivities(activityData.map(mapApiActivity));
        setFunnel(mapApiFunnel(funnelData));
      } catch (error) {
        console.error('Failed to load dashboard:', error);
        setError('Não foi possível carregar o dashboard. Tente novamente.');
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, [fetchOpportunities]);

  const handleDismissAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const handleResolveAlert = (_id: string) => {
    // TODO: PATCH /api/notifications/{id}/read/ — wire when notifications endpoint is ready
  };

  // Computed metrics
  const pipelineTotalValue = pipeline.reduce(
    (sum, item) => sum + (item.value || 0),
    0
  );
  const proposalsInPipeline = pipeline.filter((p) =>
    p.id.startsWith('proposal-')
  ).length;
  const opportunitiesInPipeline = pipeline.filter((p) =>
    p.id.startsWith('opportunity-')
  ).length;
  const urgentDeadlines = (stats?.deadlineItems || []).filter(
    (d) => d.daysLeft <= 3
  );

  // Status labels
  const statusLabels: Record<string, string> = {
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="h-32 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-64 bg-muted rounded animate-pulse" />
          <div className="h-64 bg-muted rounded animate-pulse" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <AlertTriangle className="h-12 w-12 text-error mb-4" />
          <h2 className="text-xl font-semibold mb-2">
            Erro ao carregar dashboard
          </h2>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            Tentar Novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Bem-vindo, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-muted-foreground">
            Aqui está o resumo da sua atividade hoje.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate('/opportunities')}
          >
            <Calendar className="h-4 w-4 mr-2" />
            Ver Calendario
          </Button>
          <Button onClick={() => navigate('/opportunities')}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Oportunidade
          </Button>
        </div>
      </div>

      {/* KPI Cards Row 1 — Core Business */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Oportunidades Ativas"
          value={stats?.activeOpportunities ?? 0}
          icon={Briefcase}
        />
        <KPICard
          title="Propostas em Curso"
          value={stats?.proposalsInProgress ?? 0}
          icon={FileText}
        />
        <KPICard
          title="Taxa de Vitória"
          value={`${stats?.winRate ?? 0}%`}
          icon={TrendingUp}
        />
        <KPICard
          title="Prazos Próximos (≤7 dias)"
          value={stats?.upcomingDeadlines ?? 0}
          icon={Clock}
        />
      </div>

      {/* KPI Cards Row 2 — Operations & Pipeline */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Projetos Ativos"
          value={stats?.projectsActive ?? 0}
          icon={FolderKanban}
          trend={
            stats
              ? {
                  value: stats.projectsCompleted,
                  direction: 'up' as const,
                }
              : undefined
          }
        />
        <KPICard
          title="Novas Oportunidades"
          value={stats?.scrapingNew ?? 0}
          icon={Database}
          trend={
            stats && stats.scrapingWithAI > 0
              ? {
                  value: Math.round(
                    (stats.scrapingWithAI / (stats.scrapingNew || 1)) * 100
                  ),
                  direction: 'up' as const,
                }
              : undefined
          }
        />
        <KPICard
          title="Pipeline Total"
          value={formatCurrency(pipelineTotalValue, 'USD')}
          icon={Target}
        />
        <KPICard
          title="Propostas/Oportunidades"
          value={`${proposalsInPipeline}/${opportunitiesInPipeline + proposalsInPipeline}`}
          icon={DollarSign}
        />
      </div>

      {/* Deadline Urgent Alerts */}
      {urgentDeadlines.length > 0 && (
        <Card className="border-error/30 bg-error/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-error">
              <AlertTriangle className="h-4 w-4" />
              Prazos Urgentes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {urgentDeadlines.map((item) => (
                <div
                  key={`deadline-${item.id}`}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-error/10 cursor-pointer"
                  onClick={() => navigate(`/opportunities/${item.id}`)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {item.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.client}
                    </p>
                  </div>
                  <Badge
                    variant={
                      item.daysLeft <= 1 ? 'destructive' : 'default'
                    }
                  >
                    {item.daysLeft === 0
                      ? 'Hoje!'
                      : item.daysLeft === 1
                        ? 'Amanhã!'
                        : `${item.daysLeft} dias`}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Alertas Inteligentes</h2>
          <div className="grid gap-2">
            {alerts.map((alert) => (
              <AlertBanner
                key={alert.id}
                alert={alert}
                onDismiss={handleDismissAlert}
                onResolve={handleResolveAlert}
              />
            ))}
          </div>
        </div>
      )}

      {/* Opportunities by Status */}
      {stats?.opportunitiesByStatus &&
        Object.keys(stats.opportunitiesByStatus).length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">
                Oportunidades por Estado
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {Object.entries(stats.opportunitiesByStatus).map(
                  ([status, count]) => (
                    <div
                      key={status}
                      className="flex flex-col items-center p-3 rounded-lg bg-muted/50"
                    >
                      <span className="text-2xl font-bold">{count}</span>
                      <span className="text-xs text-muted-foreground capitalize">
                        {statusLabels[status] || status}
                      </span>
                    </div>
                  )
                )}
              </div>
            </CardContent>
          </Card>
        )}

      {/* Conversion Funnel + Financial */}
      {funnel && (
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Funnel stages */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Funil de Conversão</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {/* Stage 1 */}
                <div className="flex-1 text-center p-3 rounded-lg bg-primary/10">
                  <p className="text-2xl font-bold text-primary">
                    {funnel.funnel.opportunities.count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Oportunidades Ativas
                  </p>
                </div>
                {/* Arrow + rate */}
                <div className="flex flex-col items-center gap-1 shrink-0">
                  <span className="text-xs font-semibold text-muted-foreground">
                    {funnel.conversion.oppToProposal}%
                  </span>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
                {/* Stage 2 */}
                <div className="flex-1 text-center p-3 rounded-lg bg-warning/10">
                  <p className="text-2xl font-bold text-warning">
                    {funnel.funnel.proposals.count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Propostas Submetidas
                  </p>
                  {funnel.funnel.proposals.won > 0 && (
                    <p className="text-xs text-success mt-0.5">
                      {funnel.funnel.proposals.won} ganhas
                    </p>
                  )}
                </div>
                {/* Arrow + rate */}
                <div className="flex flex-col items-center gap-1 shrink-0">
                  <span className="text-xs font-semibold text-muted-foreground">
                    {funnel.conversion.proposalToProject}%
                  </span>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
                {/* Stage 3 */}
                <div className="flex-1 text-center p-3 rounded-lg bg-success/10">
                  <p className="text-2xl font-bold text-success">
                    {funnel.funnel.projects.count}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Projetos em Carteira
                  </p>
                  {funnel.funnel.projects.active > 0 && (
                    <p className="text-xs text-success mt-0.5">
                      {funnel.funnel.projects.active} ativos
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financial summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Resumo Financeiro</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Pipeline</p>
                  <p className="text-lg font-bold mt-0.5">
                    {formatCurrency(funnel.financial.pipelineValue, funnel.financial.currency)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Propostas Enviadas</p>
                  <p className="text-lg font-bold mt-0.5">
                    {formatCurrency(funnel.financial.proposalsValue, funnel.financial.currency)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50">
                  <p className="text-xs text-muted-foreground">Carteira em Execução</p>
                  <p className="text-lg font-bold mt-0.5">
                    {formatCurrency(funnel.financial.portfolioValue, funnel.financial.currency)}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${funnel.financial.estimatedMargin >= 0 ? 'bg-success/10' : 'bg-error/10'}`}>
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    Margem Estimada
                    {funnel.financial.estimatedMargin < 0 && (
                      <TrendingDown className="h-3 w-3 text-error" />
                    )}
                  </p>
                  <p className={`text-lg font-bold mt-0.5 ${funnel.financial.estimatedMargin >= 0 ? 'text-success' : 'text-error'}`}>
                    {formatCurrency(funnel.financial.estimatedMargin, funnel.financial.currency)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Pipeline Table */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Pipeline de Propostas</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/proposals')}
            >
              Ver todas
            </Button>
          </div>
          <ProposalTable proposals={pipeline} />
        </div>

        {/* Activity Timeline */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Atividade Recente</h2>
          <Card>
            <CardContent className="p-4">
              <ActivityTimeline activities={activities} />
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ações Rápidas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/opportunities')}
              >
                <Briefcase className="h-4 w-4 mr-2" />
                Ver Oportunidades
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/proposals')}
              >
                <FileText className="h-4 w-4 mr-2" />
                Continuar Proposta
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => navigate('/projects')}
              >
                <FolderKanban className="h-4 w-4 mr-2" />
                Ver Projetos
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
