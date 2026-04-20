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
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
  apiGetProjectStats,
} from '@/lib/api';
import {
  mapApiDashboardStats,
  mapApiPipelineItem,
  mapApiAlert,
  mapApiActivity,
} from '@/lib/apiMappers';
import type { DashboardStats, PipelineItem, Alert, Activity } from '@/types';

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { fetchOpportunities } = useOpportunityStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projectStats, setProjectStats] = useState({
    total_projects: 0,
    active_projects: 0,
    completed_projects: 0,
    overdue_projects: 0,
  });
  const [pipeline, setPipeline] = useState<PipelineItem[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchOpportunities();

    async function loadDashboard() {
      setIsLoading(true);
      try {
        const [statsData, pipelineData, alertsData, activityData, projStats] =
          await Promise.all([
            apiGetDashboardStats(),
            apiGetDashboardPipeline(),
            apiGetDashboardAlerts(),
            apiGetDashboardActivity(),
            apiGetProjectStats(),
          ]);
        setStats(mapApiDashboardStats(statsData));
        setProjectStats(projStats);
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

  const handleResolveAlert = (id: string) => {
    console.log('Resolve alert:', id);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-32 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded animate-pulse" />
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
          <Button variant="outline" onClick={() => navigate('/opportunities')}>
            <Calendar className="h-4 w-4 mr-2" />
            Relatório Semanal
          </Button>
          <Button onClick={() => navigate('/opportunities')}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Oportunidade
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Oportunidades Ativas"
          value={stats?.activeOpportunities ?? 0}
          icon={Briefcase}
          trend={{ value: 12, direction: 'up' }}
        />
        <KPICard
          title="Propostas em Curso"
          value={stats?.proposalsInProgress ?? 0}
          icon={FileText}
          trend={{ value: 8, direction: 'up' }}
        />
        <KPICard
          title="Taxa de Vitória"
          value={`${stats?.winRate ?? 0}%`}
          icon={TrendingUp}
          trend={{ value: 5, direction: 'up' }}
        />
        <KPICard
          title="Prazos Próximos (≤7 dias)"
          value={stats?.upcomingDeadlines ?? 0}
          icon={Clock}
          trend={{ value: 2, direction: 'down' }}
        />
        <KPICard
          title="Projetos Ativos"
          value={projectStats.active_projects}
          icon={FolderKanban}
          trend={{ value: projectStats.total_projects, direction: 'up' }}
        />
      </div>

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
