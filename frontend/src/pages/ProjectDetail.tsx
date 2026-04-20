// ============================================
// PROJECT DETAIL PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  CheckCircle,
  PauseCircle,
  XCircle,
  AlertTriangle,
  Calendar,
  DollarSign,
  Users,
  Flag,
  FileText,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { apiGetProject, apiUpdateProjectStatus } from '@/lib/api';
import type { ApiProjectDetail } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ApiProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) loadProject(id);
  }, [id]);

  const loadProject = async (projectId: string) => {
    setIsLoading(true);
    try {
      const data = await apiGetProject(projectId);
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar projeto');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = async (action: 'activate' | 'complete' | 'close' | 'hold') => {
    if (!id) return;
    try {
      await apiUpdateProjectStatus(id, action);
      loadProject(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar estado');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-32 bg-muted rounded animate-pulse" />
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Projeto não encontrado.</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/projects')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar
        </Button>
      </div>
    );
  }

  const statusActions: Record<string, { label: string; action: 'activate' | 'complete' | 'close' | 'hold'; icon: React.ElementType; variant: string }[]> = {
    planning: [{ label: 'Iniciar', action: 'activate', icon: Play, variant: 'default' }],
    active: [
      { label: 'Concluir', action: 'complete', icon: CheckCircle, variant: 'default' },
      { label: 'Pausar', action: 'hold', icon: PauseCircle, variant: 'outline' },
    ],
    on_hold: [
      { label: 'Retomar', action: 'activate', icon: Play, variant: 'default' },
      { label: 'Concluir', action: 'complete', icon: CheckCircle, variant: 'outline' },
    ],
    completed: [{ label: 'Fechar', action: 'close', icon: XCircle, variant: 'default' }],
  };

  const actions = statusActions[project.status] || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/projects')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Voltar aos Projetos
        </Button>

        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">{project.title}</h1>
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline">{project.client}</Badge>
              <Badge variant="outline">{project.sector}</Badge>
              <Badge variant="outline">{project.country}</Badge>
              <StatusBadge status={project.status} size="sm" />
              {project.is_overdue && (
                <Badge variant="destructive">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Atrasado
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-primary">
              {formatCurrency(parseFloat(project.budget_total), project.budget_currency)}
            </p>
            <p className="text-sm text-muted-foreground">
              Orçamento Total
            </p>
          </div>
        </div>
      </div>

      {/* Actions */}
      {actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map((a) => (
            <Button
              key={a.action}
              variant={a.variant as 'default' | 'outline'}
              onClick={() => handleStatusChange(a.action)}
            >
              <a.icon className="h-4 w-4 mr-2" />
              {a.label}
            </Button>
          ))}
        </div>
      )}

      {/* Progress */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Progresso Geral</span>
            <span className="text-sm font-bold">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-3" />
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="grid w-full grid-cols-4 lg:w-auto">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="team">Equipa</TabsTrigger>
          <TabsTrigger value="milestones">Marcos</TabsTrigger>
          <TabsTrigger value="risks">Riscos</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Início</span>
                </div>
                <p className="text-lg font-semibold mt-1">
                  {project.start_date ? formatDate(new Date(project.start_date)) : '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Fim Previsto</span>
                </div>
                <p className="text-lg font-semibold mt-1">
                  {project.end_date ? formatDate(new Date(project.end_date)) : '—'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Custo Real</span>
                </div>
                <p className="text-lg font-semibold mt-1">
                  {formatCurrency(parseFloat(project.actual_cost), project.budget_currency)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">Equipa</span>
                </div>
                <p className="text-lg font-semibold mt-1">
                  {project.team?.length || 0} membros
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Descrição</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground whitespace-pre-line">
                {project.description || 'Sem descrição.'}
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="team">
          <Card>
            <CardHeader>
              <CardTitle>Equipa do Projeto</CardTitle>
            </CardHeader>
            <CardContent>
              {project.team?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum membro atribuído.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.team?.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold">
                          {member.user.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <p className="font-medium">{member.user.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {member.user.email}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge>{member.role}</Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          {member.allocation_percentage}% alocação
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="milestones">
          <Card>
            <CardHeader>
              <CardTitle>Marcos</CardTitle>
            </CardHeader>
            <CardContent>
              {project.milestones?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum marco definido.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.milestones?.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                    >
                      <div>
                        <p className="font-medium">{m.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(new Date(m.due_date))}
                        </p>
                      </div>
                      <StatusBadge status={m.status} size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risks">
          <Card>
            <CardHeader>
              <CardTitle>Riscos e Issues</CardTitle>
            </CardHeader>
            <CardContent>
              {project.risks?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum risco identificado.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.risks?.map((r) => (
                    <div
                      key={r.id}
                      className={`p-4 rounded-lg border ${
                        r.severity === 'critical'
                          ? 'bg-destructive/10 border-destructive/20'
                          : r.severity === 'high'
                          ? 'bg-error/10 border-error/20'
                          : r.severity === 'medium'
                          ? 'bg-warning/10 border-warning/20'
                          : 'bg-success/10 border-success/20'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{r.title}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            {r.description}
                          </p>
                          {r.mitigation_plan && (
                            <p className="text-sm mt-2">
                              <strong>Mitigação:</strong> {r.mitigation_plan}
                            </p>
                          )}
                        </div>
                        <div className="text-right">
                          <Badge
                            variant={
                              r.severity === 'critical' || r.severity === 'high'
                                ? 'destructive'
                                : 'outline'
                            }
                          >
                            {r.severity}
                          </Badge>
                          <p className="text-xs text-muted-foreground mt-1">
                            {r.status}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
