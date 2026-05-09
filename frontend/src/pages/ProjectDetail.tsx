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
  Layers,
  Circle,
  CheckCircle2,
  LayoutGrid,
  BarChart3,
  Save,
  FileText,
  ExternalLink,
  Upload,
} from 'lucide-react';
import { KanbanBoard, type KanbanTask } from '@/components/projects/KanbanBoard';
import { GanttChart, type GanttItem } from '@/components/projects/GanttChart';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  apiCreateProjectArtifact,
  apiCreateProjectMilestone,
  apiCreateProjectRisk,
  apiCreateProjectTeamMember,
  apiCreateProjectTask,
  apiGetUsers,
  apiGetProject,
  apiUpdateProject,
  apiUpdateProjectMilestone,
  apiUpdateProjectPhase,
  apiUpdateProjectRisk,
  apiUpdateProjectTeamMember,
  apiUpdateProjectStatus,
  apiUpdateProjectTask,
} from '@/lib/api';
import type { ApiProjectDetail, ApiProjectRisk, ApiProjectTask, ApiUser } from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/shared/StatusBadge';

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ApiProjectDetail | null>(null);
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [draft, setDraft] = useState({
    title: '',
    client: '',
    start_date: '',
    end_date: '',
    budget_total: '',
    actual_cost: '',
    progress: '0',
    description: '',
  });
  const [phaseDrafts, setPhaseDrafts] = useState<Record<number, {
    title: string;
    description: string;
    start_date: string;
    end_date: string;
    completion_percentage: string;
    is_completed: boolean;
  }>>({});
  const [artifactDraft, setArtifactDraft] = useState({
    artifact_type: 'handover',
    phase: '',
    title: '',
    status: 'pending',
    external_url: '',
    notes: '',
    file: null as File | null,
  });
  const [milestoneDraft, setMilestoneDraft] = useState({
    title: '',
    description: '',
    due_date: '',
    status: 'not_started',
    deliverables: '',
  });
  const [taskDraft, setTaskDraft] = useState({
    title: '',
    description: '',
    status: 'todo' as 'todo' | 'in_progress' | 'review' | 'done',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    due_date: '',
  });
  const [teamDraft, setTeamDraft] = useState({
    user_id: '',
    role: 'consultant',
    allocation_percentage: '100',
    start_date: '',
    end_date: '',
  });
  const [riskDraft, setRiskDraft] = useState({
    title: '',
    description: '',
    severity: 'medium' as ApiProjectRisk['severity'],
    status: 'open' as ApiProjectRisk['status'],
    mitigation_plan: '',
    owner_id: '',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savingPhaseId, setSavingPhaseId] = useState<number | null>(null);
  const [isSavingArtifact, setIsSavingArtifact] = useState(false);
  const [isSavingMilestone, setIsSavingMilestone] = useState(false);
  const [isSavingTask, setIsSavingTask] = useState(false);
  const [isSavingTeamMember, setIsSavingTeamMember] = useState(false);
  const [isSavingRisk, setIsSavingRisk] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadProject(id);
      loadUsers();
    }
  }, [id]);

  const loadUsers = async () => {
    try {
      const data = await apiGetUsers();
      setUsers(data.results || []);
    } catch {
      setUsers([]);
    }
  };

  const loadProject = async (projectId: string) => {
    setIsLoading(true);
    try {
      const data = await apiGetProject(projectId);
      setProject(data);
      setDraft({
        title: data.title || '',
        client: data.client || '',
        start_date: data.start_date || '',
        end_date: data.end_date || '',
        budget_total: data.budget_total || '0',
        actual_cost: data.actual_cost || '0',
        progress: String(data.progress ?? 0),
        description: data.description || '',
      });
      setPhaseDrafts(
        Object.fromEntries(
          (data.phases || []).map((phase) => [
            phase.id,
              {
                title: phase.title || phase.name_display || '',
                description: phase.description || '',
              start_date: phase.start_date || '',
              end_date: phase.end_date || '',
              completion_percentage: String(phase.completion_percentage ?? 0),
              is_completed: phase.is_completed,
            },
          ])
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar projeto');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProject = async () => {
    if (!id) return;
    setIsSaving(true);
    setError(null);
    setSaveMessage(null);

    const progress = Math.max(0, Math.min(100, Number(draft.progress) || 0));

    try {
      const updated = await apiUpdateProject(id, {
        title: draft.title,
        client: draft.client,
        start_date: draft.start_date || null,
        end_date: draft.end_date || null,
        budget_total: draft.budget_total,
        actual_cost: draft.actual_cost,
        progress,
        description: draft.description,
      });
      setProject(updated);
      setDraft({
        title: updated.title || '',
        client: updated.client || '',
        start_date: updated.start_date || '',
        end_date: updated.end_date || '',
        budget_total: updated.budget_total || '0',
        actual_cost: updated.actual_cost || '0',
        progress: String(updated.progress ?? 0),
        description: updated.description || '',
      });
      setSaveMessage('Projeto guardado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar projeto');
    } finally {
      setIsSaving(false);
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

  const updatePhaseDraft = (
    phaseId: number,
    patch: Partial<(typeof phaseDrafts)[number]>
  ) => {
    setPhaseDrafts((prev) => ({
      ...prev,
      [phaseId]: {
        ...prev[phaseId],
        ...patch,
      },
    }));
  };

  const handleSavePhase = async (phaseId: number) => {
    const phaseDraft = phaseDrafts[phaseId];
    if (!phaseDraft || !id) return;

    setSavingPhaseId(phaseId);
    setError(null);
    setSaveMessage(null);

    const completion = Math.max(
      0,
      Math.min(100, Number(phaseDraft.completion_percentage) || 0)
    );

    try {
      await apiUpdateProjectPhase(phaseId, {
        title: phaseDraft.title,
        description: phaseDraft.description,
        start_date: phaseDraft.start_date || null,
        end_date: phaseDraft.end_date || null,
        completion_percentage: phaseDraft.is_completed ? 100 : completion,
        is_completed: phaseDraft.is_completed,
      });
      await loadProject(id);
      setSaveMessage('Fase guardada.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar fase');
    } finally {
      setSavingPhaseId(null);
    }
  };

  const handleCreateArtifact = async () => {
    if (!project || !artifactDraft.title.trim()) return;
    setIsSavingArtifact(true);
    setError(null);
    setSaveMessage(null);

    try {
      await apiCreateProjectArtifact({
        project: project.id,
        artifact_type: artifactDraft.artifact_type,
        phase: artifactDraft.phase ? Number(artifactDraft.phase) : null,
        title: artifactDraft.title.trim(),
        status: artifactDraft.status,
        external_url: artifactDraft.external_url.trim(),
        notes: artifactDraft.notes.trim(),
        file: artifactDraft.file,
      });
      setArtifactDraft({
        artifact_type: 'handover',
        phase: '',
        title: '',
        status: 'pending',
        external_url: '',
        notes: '',
        file: null,
      });
      await loadProject(String(project.id));
      setSaveMessage('Artefacto guardado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar artefacto');
    } finally {
      setIsSavingArtifact(false);
    }
  };

  const handleCreateMilestone = async () => {
    if (!project || !milestoneDraft.title.trim() || !milestoneDraft.due_date) return;
    setIsSavingMilestone(true);
    setError(null);
    setSaveMessage(null);

    try {
      await apiCreateProjectMilestone({
        project: project.id,
        title: milestoneDraft.title.trim(),
        description: milestoneDraft.description.trim(),
        due_date: milestoneDraft.due_date,
        status: milestoneDraft.status,
        deliverables: milestoneDraft.deliverables.trim(),
      });
      setMilestoneDraft({
        title: '',
        description: '',
        due_date: '',
        status: 'not_started',
        deliverables: '',
      });
      await loadProject(String(project.id));
      setSaveMessage('Marco guardado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar marco');
    } finally {
      setIsSavingMilestone(false);
    }
  };

  const handleUpdateMilestoneStatus = async (milestoneId: number, status: string) => {
    if (!project) return;
    setError(null);
    setSaveMessage(null);

    try {
      await apiUpdateProjectMilestone(milestoneId, { status });
      await loadProject(String(project.id));
      setSaveMessage('Marco atualizado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar marco');
    }
  };

  const handleCreateTask = async () => {
    if (!project || !taskDraft.title.trim()) return;
    setIsSavingTask(true);
    setError(null);
    setSaveMessage(null);

    try {
      await apiCreateProjectTask({
        project: project.id,
        title: taskDraft.title.trim(),
        description: taskDraft.description.trim(),
        status: taskDraft.status,
        priority: taskDraft.priority,
        due_date: taskDraft.due_date || null,
      });
      setTaskDraft({
        title: '',
        description: '',
        status: 'todo',
        priority: 'medium',
        due_date: '',
      });
      await loadProject(String(project.id));
      setSaveMessage('Tarefa guardada.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar tarefa');
    } finally {
      setIsSavingTask(false);
    }
  };

  const handleUpdateTaskStatus = async (taskId: number, status: ApiProjectTask['status']) => {
    if (!project) return;
    setError(null);
    setSaveMessage(null);

    try {
      await apiUpdateProjectTask(taskId, { status });
      await loadProject(String(project.id));
      setSaveMessage('Tarefa atualizada.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar tarefa');
    }
  };

  const handleCreateTeamMember = async () => {
    if (!project || !teamDraft.user_id) return;
    setIsSavingTeamMember(true);
    setError(null);
    setSaveMessage(null);

    try {
      await apiCreateProjectTeamMember({
        project: project.id,
        user_id: Number(teamDraft.user_id),
        role: teamDraft.role,
        allocation_percentage: Math.max(0, Math.min(100, Number(teamDraft.allocation_percentage) || 0)),
        start_date: teamDraft.start_date || null,
        end_date: teamDraft.end_date || null,
      });
      setTeamDraft({
        user_id: '',
        role: 'consultant',
        allocation_percentage: '100',
        start_date: '',
        end_date: '',
      });
      await loadProject(String(project.id));
      setSaveMessage('Membro adicionado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao adicionar membro');
    } finally {
      setIsSavingTeamMember(false);
    }
  };

  const handleUpdateTeamMember = async (
    memberId: number,
    patch: { role?: string; allocation_percentage?: number; start_date?: string | null; end_date?: string | null }
  ) => {
    if (!project) return;
    setError(null);
    setSaveMessage(null);

    try {
      await apiUpdateProjectTeamMember(memberId, patch);
      await loadProject(String(project.id));
      setSaveMessage('Membro atualizado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar membro');
    }
  };

  const handleCreateRisk = async () => {
    if (!project || !riskDraft.title.trim() || !riskDraft.description.trim()) return;
    setIsSavingRisk(true);
    setError(null);
    setSaveMessage(null);

    try {
      await apiCreateProjectRisk({
        project: project.id,
        title: riskDraft.title.trim(),
        description: riskDraft.description.trim(),
        severity: riskDraft.severity,
        status: riskDraft.status,
        mitigation_plan: riskDraft.mitigation_plan.trim(),
        owner_id: riskDraft.owner_id ? Number(riskDraft.owner_id) : null,
      });
      setRiskDraft({
        title: '',
        description: '',
        severity: 'medium',
        status: 'open',
        mitigation_plan: '',
        owner_id: '',
      });
      await loadProject(String(project.id));
      setSaveMessage('Risco guardado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao guardar risco');
    } finally {
      setIsSavingRisk(false);
    }
  };

  const handleUpdateRisk = async (
    riskId: number,
    patch: Partial<ApiProjectRisk> & { owner_id?: number | null }
  ) => {
    if (!project) return;
    setError(null);
    setSaveMessage(null);

    try {
      await apiUpdateProjectRisk(riskId, patch);
      await loadProject(String(project.id));
      setSaveMessage('Risco atualizado.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar risco');
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
          <Button variant="outline" onClick={handleSaveProject} disabled={isSaving}>
            <Save className="h-4 w-4 mr-2" />
            {isSaving ? 'A guardar...' : 'Guardar'}
          </Button>
        </div>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}
      {saveMessage && <p className="text-sm text-green-700">{saveMessage}</p>}

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
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 lg:grid-cols-8 lg:w-auto">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="phases">Fases Projeto</TabsTrigger>
          <TabsTrigger value="kanban">Tarefas</TabsTrigger>
          <TabsTrigger value="gantt">Timeline</TabsTrigger>
          <TabsTrigger value="team">Equipa</TabsTrigger>
          <TabsTrigger value="milestones">Marcos</TabsTrigger>
          <TabsTrigger value="risks">Riscos</TabsTrigger>
          <TabsTrigger value="artifacts">Artefactos</TabsTrigger>
        </TabsList>

        <TabsContent value="phases">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Fases do Projeto
              </CardTitle>
            </CardHeader>
            <CardContent>
              {project.phases?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhuma fase definida.
                </p>
              ) : (
                <div className="space-y-4">
                  {project.phases?.map((phase, index) => (
                    <div key={phase.id} className="relative">
                      {/* Connector line */}
                      {index < (project.phases?.length || 0) - 1 && (
                        <div className="absolute left-5 top-10 w-0.5 h-full bg-muted" />
                      )}
                      <div className="flex items-start gap-4">
                        <div
                          className={`h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                            phase.is_completed
                              ? 'bg-green-600 text-white'
                              : phase.completion_percentage > 0
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted text-muted-foreground'
                          }`}
                        >
                          {phase.is_completed ? (
                            <CheckCircle2 className="h-5 w-5" />
                          ) : (
                            <Circle className="h-5 w-5" />
                          )}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-semibold">{phase.title || phase.name_display}</p>
                              <p className="text-sm text-muted-foreground">
                                {phase.description || 'Sem descrição'}
                              </p>
                            </div>
                            <Badge
                              variant={phase.is_completed ? 'default' : 'outline'}
                              className={phase.is_completed ? 'bg-green-600' : ''}
                            >
                              {phase.is_completed
                                ? 'Concluída'
                                : `${phase.completion_percentage}%`}
                            </Badge>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
                            {phase.start_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                Início: {formatDate(new Date(phase.start_date))}
                              </span>
                            )}
                            {phase.end_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                Fim: {formatDate(new Date(phase.end_date))}
                              </span>
                            )}
                          </div>
                          <div className="mt-3 space-y-3 rounded-md border bg-muted/20 p-3">
                            <div className="space-y-2">
                              <Label htmlFor={`phase-title-${phase.id}`}>Nome da fase</Label>
                              <Input
                                id={`phase-title-${phase.id}`}
                                value={phaseDrafts[phase.id]?.title ?? ''}
                                onChange={(e) =>
                                  updatePhaseDraft(phase.id, { title: e.target.value })
                                }
                                placeholder={phase.name_display}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`phase-description-${phase.id}`}>Descricao</Label>
                              <Textarea
                                id={`phase-description-${phase.id}`}
                                value={phaseDrafts[phase.id]?.description ?? ''}
                                onChange={(e) =>
                                  updatePhaseDraft(phase.id, { description: e.target.value })
                                }
                                rows={2}
                                placeholder="Descreva o escopo e os objetivos desta fase"
                              />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                              <div className="space-y-2">
                                <Label htmlFor={`phase-start-${phase.id}`}>Inicio</Label>
                                <Input
                                  id={`phase-start-${phase.id}`}
                                  type="date"
                                  value={phaseDrafts[phase.id]?.start_date ?? ''}
                                  onChange={(e) =>
                                    updatePhaseDraft(phase.id, { start_date: e.target.value })
                                  }
                                />
                              </div>
                              <div className="space-y-2">
                                <Label htmlFor={`phase-end-${phase.id}`}>Fim</Label>
                                <Input
                                  id={`phase-end-${phase.id}`}
                                  type="date"
                                  value={phaseDrafts[phase.id]?.end_date ?? ''}
                                  onChange={(e) =>
                                    updatePhaseDraft(phase.id, { end_date: e.target.value })
                                  }
                                />
                              </div>
                              <div className="space-y-2">
                                <Label htmlFor={`phase-progress-${phase.id}`}>Progresso (%)</Label>
                                <Input
                                  id={`phase-progress-${phase.id}`}
                                  type="number"
                                  min="0"
                                  max="100"
                                  value={phaseDrafts[phase.id]?.completion_percentage ?? '0'}
                                  onChange={(e) =>
                                    updatePhaseDraft(phase.id, {
                                      completion_percentage: e.target.value,
                                      is_completed: Number(e.target.value) >= 100,
                                    })
                                  }
                                />
                              </div>
                              <div className="flex items-end gap-2 pb-2">
                                <input
                                  id={`phase-complete-${phase.id}`}
                                  type="checkbox"
                                  className="h-4 w-4 rounded border-input"
                                  checked={phaseDrafts[phase.id]?.is_completed ?? false}
                                  onChange={(e) =>
                                    updatePhaseDraft(phase.id, {
                                      is_completed: e.target.checked,
                                      completion_percentage: e.target.checked
                                        ? '100'
                                        : phaseDrafts[phase.id]?.completion_percentage ?? '0',
                                    })
                                  }
                                />
                                <Label htmlFor={`phase-complete-${phase.id}`}>Concluida</Label>
                              </div>
                            </div>
                            <div className="flex justify-end">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleSavePhase(phase.id)}
                                disabled={savingPhaseId === phase.id}
                              >
                                <Save className="h-4 w-4 mr-2" />
                                {savingPhaseId === phase.id ? 'A guardar...' : 'Guardar fase'}
                              </Button>
                            </div>
                          </div>
                          {project.artifacts?.some((artifact) => artifact.phase === phase.id) && (
                            <div className="mt-3 rounded-md border p-3">
                              <p className="text-sm font-medium mb-2">Artefactos desta fase</p>
                              <div className="space-y-2">
                                {project.artifacts
                                  ?.filter((artifact) => artifact.phase === phase.id)
                                  .map((artifact) => (
                                    <div
                                      key={artifact.id}
                                      className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-md bg-muted/40 p-2"
                                    >
                                      <div>
                                        <p className="text-sm font-medium">{artifact.title}</p>
                                        <p className="text-xs text-muted-foreground">
                                          {artifact.artifact_type_display}
                                        </p>
                                      </div>
                                      <Badge variant="outline">{artifact.status_display}</Badge>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}
                          {!phase.is_completed && (
                            <div className="mt-2">
                              <div className="flex items-center justify-between text-sm mb-1">
                                <span className="text-muted-foreground">Progresso</span>
                                <span className="font-medium">{phase.completion_percentage}%</span>
                              </div>
                              <Progress value={phase.completion_percentage} className="h-2" />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Dados do Projeto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="project-title">Titulo</Label>
                  <Input
                    id="project-title"
                    value={draft.title}
                    onChange={(e) => setDraft((prev) => ({ ...prev, title: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-client">Cliente</Label>
                  <Input
                    id="project-client"
                    value={draft.client}
                    onChange={(e) => setDraft((prev) => ({ ...prev, client: e.target.value }))}
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="project-start">Inicio</Label>
                  <Input
                    id="project-start"
                    type="date"
                    value={draft.start_date}
                    onChange={(e) => setDraft((prev) => ({ ...prev, start_date: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-end">Fim previsto</Label>
                  <Input
                    id="project-end"
                    type="date"
                    value={draft.end_date}
                    onChange={(e) => setDraft((prev) => ({ ...prev, end_date: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-budget">Orcamento</Label>
                  <Input
                    id="project-budget"
                    type="number"
                    min="0"
                    value={draft.budget_total}
                    onChange={(e) => setDraft((prev) => ({ ...prev, budget_total: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-cost">Custo real</Label>
                  <Input
                    id="project-cost"
                    type="number"
                    min="0"
                    value={draft.actual_cost}
                    onChange={(e) => setDraft((prev) => ({ ...prev, actual_cost: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="project-progress">Progresso (%)</Label>
                  <Input
                    id="project-progress"
                    type="number"
                    min="0"
                    max="100"
                    value={draft.progress}
                    onChange={(e) => setDraft((prev) => ({ ...prev, progress: e.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-description">Descricao</Label>
                <Textarea
                  id="project-description"
                  value={draft.description}
                  onChange={(e) => setDraft((prev) => ({ ...prev, description: e.target.value }))}
                  rows={5}
                />
              </div>
              <div className="flex justify-end">
                <Button onClick={handleSaveProject} disabled={isSaving}>
                  <Save className="h-4 w-4 mr-2" />
                  {isSaving ? 'A guardar...' : 'Guardar projeto'}
                </Button>
              </div>
            </CardContent>
          </Card>

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
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-3 rounded-md border bg-muted/20 p-3">
                <div className="space-y-2 lg:col-span-2">
                  <Label>Consultor</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={teamDraft.user_id}
                    onChange={(e) =>
                      setTeamDraft((prev) => ({ ...prev, user_id: e.target.value }))
                    }
                  >
                    <option value="">Selecionar membro</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name || user.email} ({user.role})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Papel</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={teamDraft.role}
                    onChange={(e) =>
                      setTeamDraft((prev) => ({ ...prev, role: e.target.value }))
                    }
                  >
                    <option value="team_lead">Team Lead</option>
                    <option value="technical_lead">Technical Lead</option>
                    <option value="consultant">Consultor</option>
                    <option value="specialist">Especialista</option>
                    <option value="support">Suporte</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Alocacao (%)</Label>
                  <Input
                    type="number"
                    min="0"
                    max="100"
                    value={teamDraft.allocation_percentage}
                    onChange={(e) =>
                      setTeamDraft((prev) => ({ ...prev, allocation_percentage: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Inicio</Label>
                  <Input
                    type="date"
                    value={teamDraft.start_date}
                    onChange={(e) =>
                      setTeamDraft((prev) => ({ ...prev, start_date: e.target.value }))
                    }
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={handleCreateTeamMember}
                    disabled={isSavingTeamMember || !teamDraft.user_id}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isSavingTeamMember ? 'A guardar...' : 'Adicionar'}
                  </Button>
                </div>
              </div>
              {project.team?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum membro atribuído.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.team?.map((member) => (
                    <div
                      key={member.id}
                      className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 p-3 rounded-lg bg-muted/50"
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
                      <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
                        <select
                          className="h-8 rounded-md border bg-background px-2 text-sm"
                          value={member.role}
                          onChange={(e) =>
                            handleUpdateTeamMember(member.id, { role: e.target.value })
                          }
                        >
                          <option value="team_lead">Team Lead</option>
                          <option value="technical_lead">Technical Lead</option>
                          <option value="consultant">Consultor</option>
                          <option value="specialist">Especialista</option>
                          <option value="support">Suporte</option>
                        </select>
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

        <TabsContent value="artifacts">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Artefactos de Arranque
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-3 rounded-md border bg-muted/20 p-3">
                <div className="space-y-2">
                  <Label>Tipo</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={artifactDraft.artifact_type}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, artifact_type: e.target.value }))
                    }
                  >
                    <option value="final_proposal">Proposta Final</option>
                    <option value="contract">Contrato</option>
                    <option value="handover">Handover Package</option>
                    <option value="kickoff">Kickoff Pack</option>
                    <option value="checklist">Checklist de Arranque</option>
                    <option value="other">Outro</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Fase</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={artifactDraft.phase}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, phase: e.target.value }))
                    }
                  >
                    <option value="">Sem fase</option>
                    {project.phases?.map((phase) => (
                      <option key={phase.id} value={phase.id}>
                        {phase.title || phase.name_display}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label>Titulo</Label>
                  <Input
                    value={artifactDraft.title}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, title: e.target.value }))
                    }
                    placeholder="Ex: Contrato assinado"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={artifactDraft.status}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, status: e.target.value }))
                    }
                  >
                    <option value="pending">Pendente</option>
                    <option value="attached">Anexado</option>
                    <option value="approved">Aprovado</option>
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label>Link externo</Label>
                  <Input
                    value={artifactDraft.external_url}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, external_url: e.target.value }))
                    }
                    placeholder="https://..."
                  />
                </div>
                <div className="space-y-2 lg:col-span-4">
                  <Label>Notas</Label>
                  <Textarea
                    value={artifactDraft.notes}
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({ ...prev, notes: e.target.value }))
                    }
                    rows={2}
                    placeholder="Contexto, pendencias ou instrucoes para a equipa"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Ficheiro</Label>
                  <Input
                    type="file"
                    onChange={(e) =>
                      setArtifactDraft((prev) => ({
                        ...prev,
                        file: e.target.files?.[0] || null,
                      }))
                    }
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={handleCreateArtifact}
                    disabled={isSavingArtifact || !artifactDraft.title.trim()}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    {isSavingArtifact ? 'A guardar...' : 'Adicionar'}
                  </Button>
                </div>
              </div>

              {project.artifacts?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum artefacto anexado.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.artifacts?.map((artifact) => (
                    <div
                      key={artifact.id}
                      className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 rounded-lg border p-4"
                    >
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="font-medium">{artifact.title}</p>
                          <Badge variant="outline">{artifact.artifact_type_display}</Badge>
                          <Badge>{artifact.status_display}</Badge>
                          {artifact.phase && (
                            <Badge variant="secondary">
                              {project.phases?.find((phase) => phase.id === artifact.phase)?.title ||
                                project.phases?.find((phase) => phase.id === artifact.phase)?.name_display ||
                                'Fase'}
                            </Badge>
                          )}
                        </div>
                        {artifact.notes && (
                          <p className="text-sm text-muted-foreground mt-2 whitespace-pre-line">
                            {artifact.notes}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {artifact.file_url && (
                          <Button variant="outline" size="sm" asChild>
                            <a href={artifact.file_url} target="_blank" rel="noreferrer">
                              <FileText className="h-4 w-4 mr-2" />
                              Ficheiro
                            </a>
                          </Button>
                        )}
                        {artifact.external_url && (
                          <Button variant="outline" size="sm" asChild>
                            <a href={artifact.external_url} target="_blank" rel="noreferrer">
                              <ExternalLink className="h-4 w-4 mr-2" />
                              Link
                            </a>
                          </Button>
                        )}
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
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-3 rounded-md border bg-muted/20 p-3">
                <div className="space-y-2 lg:col-span-2">
                  <Label>Titulo</Label>
                  <Input
                    value={milestoneDraft.title}
                    onChange={(e) =>
                      setMilestoneDraft((prev) => ({ ...prev, title: e.target.value }))
                    }
                    placeholder="Ex: Kickoff com o cliente"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Prazo</Label>
                  <Input
                    type="date"
                    value={milestoneDraft.due_date}
                    onChange={(e) =>
                      setMilestoneDraft((prev) => ({ ...prev, due_date: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={milestoneDraft.status}
                    onChange={(e) =>
                      setMilestoneDraft((prev) => ({ ...prev, status: e.target.value }))
                    }
                  >
                    <option value="not_started">Nao iniciado</option>
                    <option value="in_progress">Em curso</option>
                    <option value="completed">Concluido</option>
                    <option value="delayed">Atrasado</option>
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label>Entregaveis associados</Label>
                  <Input
                    value={milestoneDraft.deliverables}
                    onChange={(e) =>
                      setMilestoneDraft((prev) => ({ ...prev, deliverables: e.target.value }))
                    }
                    placeholder="Relatorio, ata, plano aprovado..."
                  />
                </div>
                <div className="space-y-2 lg:col-span-5">
                  <Label>Descricao</Label>
                  <Textarea
                    value={milestoneDraft.description}
                    onChange={(e) =>
                      setMilestoneDraft((prev) => ({ ...prev, description: e.target.value }))
                    }
                    rows={2}
                    placeholder="Contexto do marco e criterio de aceitacao"
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={handleCreateMilestone}
                    disabled={isSavingMilestone || !milestoneDraft.title.trim() || !milestoneDraft.due_date}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isSavingMilestone ? 'A guardar...' : 'Adicionar'}
                  </Button>
                </div>
              </div>

              {project.milestones?.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Nenhum marco definido.
                </p>
              ) : (
                <div className="space-y-3">
                  {project.milestones?.map((m) => (
                    <div
                      key={m.id}
                      className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 p-3 rounded-lg bg-muted/50"
                    >
                      <div>
                        <p className="font-medium">{m.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {formatDate(new Date(m.due_date))}
                        </p>
                        {m.description && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {m.description}
                          </p>
                        )}
                        {m.deliverables && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Entregaveis: {m.deliverables}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={m.status} size="sm" />
                        <select
                          className="h-8 rounded-md border bg-background px-2 text-sm"
                          value={m.status}
                          onChange={(e) => handleUpdateMilestoneStatus(m.id, e.target.value)}
                        >
                          <option value="not_started">Nao iniciado</option>
                          <option value="in_progress">Em curso</option>
                          <option value="completed">Concluido</option>
                          <option value="delayed">Atrasado</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="kanban">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LayoutGrid className="h-5 w-5" />
                Quadro de Tarefas
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-3 rounded-md border bg-muted/20 p-3">
                <div className="space-y-2 lg:col-span-2">
                  <Label>Titulo</Label>
                  <Input
                    value={taskDraft.title}
                    onChange={(e) =>
                      setTaskDraft((prev) => ({ ...prev, title: e.target.value }))
                    }
                    placeholder="Ex: Preparar agenda de kickoff"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={taskDraft.status}
                    onChange={(e) =>
                      setTaskDraft((prev) => ({
                        ...prev,
                        status: e.target.value as typeof taskDraft.status,
                      }))
                    }
                  >
                    <option value="todo">Por fazer</option>
                    <option value="in_progress">Em curso</option>
                    <option value="review">Revisao</option>
                    <option value="done">Concluido</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Prioridade</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={taskDraft.priority}
                    onChange={(e) =>
                      setTaskDraft((prev) => ({
                        ...prev,
                        priority: e.target.value as typeof taskDraft.priority,
                      }))
                    }
                  >
                    <option value="low">Baixa</option>
                    <option value="medium">Media</option>
                    <option value="high">Alta</option>
                    <option value="critical">Critica</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Prazo</Label>
                  <Input
                    type="date"
                    value={taskDraft.due_date}
                    onChange={(e) =>
                      setTaskDraft((prev) => ({ ...prev, due_date: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2 lg:col-span-5">
                  <Label>Descricao</Label>
                  <Textarea
                    value={taskDraft.description}
                    onChange={(e) =>
                      setTaskDraft((prev) => ({ ...prev, description: e.target.value }))
                    }
                    rows={2}
                    placeholder="O que precisa ser feito, criterio de conclusao e dependencias"
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={handleCreateTask}
                    disabled={isSavingTask || !taskDraft.title.trim()}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isSavingTask ? 'A guardar...' : 'Adicionar'}
                  </Button>
                </div>
              </div>
              {(() => {
                const columns = [
                  { id: 'todo', title: 'Por Fazer' },
                  { id: 'in_progress', title: 'Em Curso' },
                  { id: 'review', title: 'Revisão' },
                  { id: 'done', title: 'Concluído' },
                ];

                const tasks: KanbanTask[] = [
                  ...(project.tasks?.map((task) => ({
                    id: String(task.id),
                    title: task.title,
                    description: task.description,
                    status: task.status,
                    priority: task.priority,
                    assignee: task.assignee?.name,
                    dueDate: task.due_date ? new Date(task.due_date).toLocaleDateString('pt-PT') : undefined,
                  })) || []),
                ];

                return tasks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Nenhuma tarefa disponível. Crie marcos e entregáveis para visualizar aqui.
                  </p>
                ) : (
                  <KanbanBoard
                    columns={columns}
                    tasks={tasks}
                    onTaskMove={(taskId, newStatus) => {
                      handleUpdateTaskStatus(Number(taskId), newStatus as ApiProjectTask['status']);
                    }}
                    onTaskClick={(task) => {
                      setTaskDraft((prev) => ({
                        ...prev,
                        title: task.title,
                        description: task.description || '',
                        status: task.status as typeof taskDraft.status,
                        priority: task.priority,
                      }));
                    }}
                    onAddTask={(columnId) =>
                      setTaskDraft((prev) => ({
                        ...prev,
                        status: columnId as typeof taskDraft.status,
                      }))
                    }
                  />
                );
              })()}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="gantt">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Cronograma do Projeto
              </CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                const items: GanttItem[] = [
                  ...(project.phases?.map((p) => ({
                    id: `phase-${p.id}`,
                    name: p.name_display,
                    startDate: p.start_date ? new Date(p.start_date) : new Date(project.start_date || Date.now()),
                    endDate: p.end_date ? new Date(p.end_date) : new Date(project.end_date || Date.now() + 30 * 24 * 60 * 60 * 1000),
                    progress: p.completion_percentage,
                    type: 'phase' as const,
                    status: p.is_completed ? 'completed' : p.completion_percentage > 0 ? 'in_progress' : 'not_started',
                  })) || []),
                  ...(project.milestones?.map((m) => ({
                    id: `milestone-${m.id}`,
                    name: m.title,
                    startDate: m.due_date ? new Date(m.due_date) : new Date(),
                    endDate: m.due_date ? new Date(new Date(m.due_date).getTime() + 24 * 60 * 60 * 1000) : new Date(),
                    progress: m.status === 'completed' ? 100 : 0,
                    type: 'milestone' as const,
                    status: m.status === 'completed' ? 'completed' : m.status === 'delayed' ? 'delayed' : 'not_started',
                  })) || []),
                ];

                return items.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Nenhum item para visualizar. Defina fases e marcos com datas.
                  </p>
                ) : (
                  <GanttChart
                    items={items}
                    onItemClick={(item) => {
                      console.log('Clicked item', item);
                    }}
                  />
                );
              })()}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="risks">
          <Card>
            <CardHeader>
              <CardTitle>Riscos e Issues</CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-6 gap-3 rounded-md border bg-muted/20 p-3">
                <div className="space-y-2 lg:col-span-2">
                  <Label>Titulo</Label>
                  <Input
                    value={riskDraft.title}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({ ...prev, title: e.target.value }))
                    }
                    placeholder="Ex: Atraso na aprovacao do plano"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Severidade</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={riskDraft.severity}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({
                        ...prev,
                        severity: e.target.value as ApiProjectRisk['severity'],
                      }))
                    }
                  >
                    <option value="low">Baixo</option>
                    <option value="medium">Medio</option>
                    <option value="high">Alto</option>
                    <option value="critical">Critico</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Estado</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={riskDraft.status}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({
                        ...prev,
                        status: e.target.value as ApiProjectRisk['status'],
                      }))
                    }
                  >
                    <option value="open">Aberto</option>
                    <option value="mitigated">Mitigado</option>
                    <option value="closed">Fechado</option>
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label>Responsavel</Label>
                  <select
                    className="h-9 w-full rounded-md border bg-background px-3 text-sm"
                    value={riskDraft.owner_id}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({ ...prev, owner_id: e.target.value }))
                    }
                  >
                    <option value="">Sem responsavel</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name || user.email}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2 lg:col-span-3">
                  <Label>Descricao</Label>
                  <Textarea
                    value={riskDraft.description}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({ ...prev, description: e.target.value }))
                    }
                    rows={2}
                    placeholder="O que pode acontecer e qual o impacto no projeto"
                  />
                </div>
                <div className="space-y-2 lg:col-span-2">
                  <Label>Plano de mitigacao</Label>
                  <Textarea
                    value={riskDraft.mitigation_plan}
                    onChange={(e) =>
                      setRiskDraft((prev) => ({ ...prev, mitigation_plan: e.target.value }))
                    }
                    rows={2}
                    placeholder="Acao preventiva, responsavel e trigger"
                  />
                </div>
                <div className="flex items-end">
                  <Button
                    className="w-full"
                    onClick={handleCreateRisk}
                    disabled={isSavingRisk || !riskDraft.title.trim() || !riskDraft.description.trim()}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isSavingRisk ? 'A guardar...' : 'Adicionar'}
                  </Button>
                </div>
              </div>
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
                        <div className="flex flex-col gap-2 min-w-40">
                          <Badge
                            variant={
                              r.severity === 'critical' || r.severity === 'high'
                                ? 'destructive'
                                : 'outline'
                            }
                          >
                            {r.severity}
                          </Badge>
                          <select
                            className="h-8 rounded-md border bg-background px-2 text-sm"
                            value={r.status}
                            onChange={(e) =>
                              handleUpdateRisk(r.id, { status: e.target.value as ApiProjectRisk['status'] })
                            }
                          >
                            <option value="open">Aberto</option>
                            <option value="mitigated">Mitigado</option>
                            <option value="closed">Fechado</option>
                          </select>
                          <select
                            className="h-8 rounded-md border bg-background px-2 text-sm"
                            value={r.severity}
                            onChange={(e) =>
                              handleUpdateRisk(r.id, { severity: e.target.value as ApiProjectRisk['severity'] })
                            }
                          >
                            <option value="low">Baixo</option>
                            <option value="medium">Medio</option>
                            <option value="high">Alto</option>
                            <option value="critical">Critico</option>
                          </select>
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
