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
  Plus,
  FolderKanban,
  AlertTriangle,
  Zap,
  CheckCircle2,
  Circle,
  ArrowRight,
  Globe,
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
} from '@/lib/api';
import {
  mapApiDashboardStats,
  mapApiPipelineItem,
  mapApiAlert,
  mapApiActivity,
} from '@/lib/apiMappers';
import type { DashboardStats, PipelineItem, Alert, Activity } from '@/types';

const STATUS_LABELS: Record<string, string> = {
  new: 'Novo',
  analyzing: 'Em Análise',
  go: 'Go',
  no_go: 'No-Go',
  proposal_draft: 'Proposta',
  proposal_review: 'Em Revisão',
  submitted: 'Submetida',
  won: 'Ganha',
  lost: 'Não Aprovada',
};

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-gray-400',
  analyzing: 'bg-blue-400',
  go: 'bg-emerald-500',
  no_go: 'bg-red-400',
  proposal_draft: 'bg-amber-400',
  proposal_review: 'bg-orange-400',
  submitted: 'bg-purple-400',
  won: 'bg-green-600',
  lost: 'bg-red-600',
};

const PIPELINE_STATUSES = ['new', 'analyzing', 'go', 'proposal_draft', 'proposal_review'];

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { fetchOpportunities } = useOpportunityStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [pipeline, setPipeline] = useState<PipelineItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchOpportunities();

    async function loadDashboard() {
      setIsLoading(true);
      try {
        const [statsData, pipelineData, alertsData, activityData] =
          await Promise.all([
            apiGetDashboardStats(),
            apiGetDashboardPipeline(),
            apiGetDashboardAlerts(),
            apiGetDashboardActivity(),
          ]);
        setStats(mapApiDashboardStats(statsData));
        setPipeline(pipelineData.map(mapApiPipelineItem));
        setAlerts(alertsData.map(mapApiAlert));
        setActivities(activityData.map(mapApiActivity));
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, [fetchOpportunities]);

  const handleDismissAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-28 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const pipelineTotal = PIPELINE_STATUSES.reduce(
    (sum, s) => sum + (stats?.opportunitiesByStatus[s] ?? 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Bem-vindo, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-muted-foreground text-sm">
            {new Date().toLocaleDateString('pt-PT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/scraping')}>
            <Globe className="h-4 w-4 mr-2" />
            Scraping
            {(stats?.scrapingNew ?? 0) > 0 && (
              <Badge className="ml-2 h-5 px-1.5 text-xs bg-amber-500 text-white">{stats!.scrapingNew}</Badge>
            )}
          </Button>
          <Button onClick={() => navigate('/opportunities/new')}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Oportunidade
          </Button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
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
          title="Prazos ≤ 7 dias"
          value={stats?.upcomingDeadlines ?? 0}
          icon={Clock}
        />
        <KPICard
          title="Projetos Ativos"
          value={stats?.projectsActive ?? 0}
          icon={FolderKanban}
        />
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert) => (
            <AlertBanner
              key={alert.id}
              alert={alert}
              onDismiss={handleDismissAlert}
              onResolve={() => {}}
            />
          ))}
        </div>
      )}

      {/* Middle row: funnel + deadlines + scraping health */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Opportunity funnel */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center justify-between">
              Funil de Oportunidades
              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs px-2"
                onClick={() => navigate('/opportunities')}
              >
                Ver todas <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {PIPELINE_STATUSES.map((s) => {
              const count = stats?.opportunitiesByStatus[s] ?? 0;
              const pct = pipelineTotal > 0 ? Math.round((count / pipelineTotal) * 100) : 0;
              return (
                <div key={s} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">{STATUS_LABELS[s]}</span>
                    <span className="font-medium tabular-nums">{count}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${STATUS_COLORS[s]}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
            <div className="pt-2 mt-1 border-t flex justify-between text-xs">
              <span className="text-muted-foreground">Ganhas</span>
              <span className="font-semibold text-green-600">
                {stats?.opportunitiesByStatus['won'] ?? 0}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Upcoming deadline list */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Prazos Próximos (7 dias)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {(stats?.deadlineItems ?? []).length === 0 ? (
              <div className="flex flex-col items-center py-6 gap-2">
                <CheckCircle2 className="h-8 w-8 text-green-500" />
                <p className="text-xs text-muted-foreground text-center">
                  Nenhum prazo crítico nos próximos 7 dias
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {stats!.deadlineItems.slice(0, 6).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start justify-between gap-2 cursor-pointer hover:bg-muted/40 rounded px-1 py-0.5 -mx-1"
                    onClick={() => navigate(`/opportunities/${item.id}`)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{item.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{item.client}</p>
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-xs flex-shrink-0 ${
                        item.days_left <= 2
                          ? 'border-red-500 text-red-600'
                          : 'border-amber-500 text-amber-600'
                      }`}
                    >
                      {item.days_left === 0 ? 'Hoje' : `${item.days_left}d`}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Scraping health */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <Zap className="h-4 w-4 text-blue-500" />
              Radar de Scraping
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-amber-400 text-amber-400" />
                <span className="text-sm">Novas para avaliar</span>
              </div>
              <span className="text-2xl font-bold tabular-nums">{stats?.scrapingNew ?? 0}</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-blue-400 text-blue-400" />
                <span className="text-sm">Com análise IA pronta</span>
              </div>
              <span className="text-2xl font-bold tabular-nums text-blue-600">
                {stats?.scrapingWithAi ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between py-1">
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-green-500 text-green-500" />
                <span className="text-sm">Projetos concluídos</span>
              </div>
              <span className="text-2xl font-bold tabular-nums text-green-600">
                {stats?.projectsCompleted ?? 0}
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => navigate('/scraping')}
            >
              Avaliar oportunidades
              {(stats?.scrapingNew ?? 0) > 0 && (
                <Badge className="ml-2 h-4 px-1.5 text-xs bg-amber-500 text-white">
                  {stats!.scrapingNew}
                </Badge>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Bottom row: pipeline table + activity */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">Pipeline de Propostas</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/proposals')}>
              Ver todas
            </Button>
          </div>
          <ProposalTable proposals={pipeline} />
        </div>

        <div className="space-y-4">
          <h2 className="text-base font-semibold">Atividade Recente</h2>
          <Card>
            <CardContent className="p-4">
              <ActivityTimeline activities={activities} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Ações Rápidas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start text-sm"
                onClick={() => navigate('/opportunities')}
              >
                <Briefcase className="h-4 w-4 mr-2" />
                Ver Oportunidades
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start text-sm"
                onClick={() => navigate('/proposals')}
              >
                <FileText className="h-4 w-4 mr-2" />
                Continuar Proposta
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start text-sm"
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
