// ============================================
// PROJECT DETAIL PAGE — COS Execution Module
// ============================================

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Play, CheckCircle, PauseCircle, XCircle, AlertTriangle,
  Calendar, DollarSign, Users, Layers, Circle, CheckCircle2,
  LayoutGrid, BarChart3, Plus, Pencil, Trash2, Upload, FileText,
  ExternalLink, Package, ChevronDown, ChevronRight,
} from 'lucide-react';
import { KanbanBoard, type KanbanTask } from '@/components/projects/KanbanBoard';
import { GanttChart, type GanttItem } from '@/components/projects/GanttChart';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  apiGetProject, apiUpdateProjectStatus, apiUpdateProjectPhase,
  apiCreateProjectMilestone, apiUpdateProjectMilestone, apiDeleteProjectMilestone,
  apiCreateProjectRisk, apiUpdateProjectRisk, apiDeleteProjectRisk,
  apiCreateProjectDeliverable, apiUpdateProjectDeliverable, apiDeleteProjectDeliverable,
  apiCreateProjectArtifact, apiUpdateProjectArtifact,
  apiAddProjectTeamMember, apiDeleteProjectTeamMember,
  apiGetConsultants,
} from '@/lib/api';
import type {
  ApiProjectDetail, ApiProjectMilestone, ApiProjectRisk,
  ApiProjectDeliverable, ApiProjectArtifact, ApiProjectPhase,
} from '@/lib/api';
import { formatDate, formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { cn } from '@/lib/utils';

// ── helpers ────────────────────────────────────────────────────────────────

const ARTIFACT_TYPES = [
  { value: 'final_proposal', label: 'Proposta Final' },
  { value: 'contract', label: 'Contrato' },
  { value: 'handover', label: 'Pacote de Handover' },
  { value: 'kickoff_pack', label: 'Kickoff Pack' },
  { value: 'checklist', label: 'Checklist de Fecho' },
] as const;

const ARTIFACT_STATUS = [
  { value: 'pending', label: 'Pendente' },
  { value: 'draft', label: 'Rascunho' },
  { value: 'under_review', label: 'Em Revisão' },
  { value: 'approved', label: 'Aprovado' },
  { value: 'signed', label: 'Assinado' },
  { value: 'archived', label: 'Arquivado' },
];

const DELIVERABLE_STATUS = [
  { value: 'pending', label: 'Pendente' },
  { value: 'in_progress', label: 'Em Progresso' },
  { value: 'submitted', label: 'Submetido' },
  { value: 'under_review', label: 'Em Revisão' },
  { value: 'approved', label: 'Aprovado' },
  { value: 'accepted', label: 'Aceite' },
  { value: 'rejected', label: 'Rejeitado' },
];

const RISK_SEVERITY = [
  { value: 'low', label: 'Baixo' },
  { value: 'medium', label: 'Médio' },
  { value: 'high', label: 'Alto' },
  { value: 'critical', label: 'Crítico' },
];

const RISK_STATUS = [
  { value: 'open', label: 'Aberto' },
  { value: 'mitigated', label: 'Mitigado' },
  { value: 'closed', label: 'Fechado' },
  { value: 'accepted', label: 'Aceite' },
];

const MILESTONE_STATUS = [
  { value: 'pending', label: 'Pendente' },
  { value: 'in_progress', label: 'Em Progresso' },
  { value: 'completed', label: 'Concluído' },
  { value: 'delayed', label: 'Atrasado' },
];

const MEMBER_ROLES = [
  'Project Manager', 'Team Leader', 'Senior Consultant', 'Consultant',
  'Junior Consultant', 'Analyst', 'Domain Expert', 'Advisor',
];

function artifactStatusColor(status: string) {
  switch (status) {
    case 'approved': case 'signed': return 'bg-success/10 text-success border-success/20';
    case 'under_review': return 'bg-warning/10 text-warning border-warning/20';
    case 'rejected': return 'bg-error/10 text-error border-error/20';
    default: return 'bg-muted/50 text-muted-foreground';
  }
}

function deliverableStatusColor(status: string) {
  switch (status) {
    case 'approved': case 'accepted': return 'text-success';
    case 'rejected': return 'text-error';
    case 'under_review': case 'submitted': return 'text-warning';
    default: return 'text-muted-foreground';
  }
}

// ── main component ─────────────────────────────────────────────────────────

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<ApiProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // phase inline edit
  const [editingPhaseId, setEditingPhaseId] = useState<number | null>(null);
  const [editingPhaseTitle, setEditingPhaseTitle] = useState('');
  const [savingPhaseId, setSavingPhaseId] = useState<number | null>(null);
  const [expandedPhases, setExpandedPhases] = useState<Set<number>>(new Set());

  // milestone modal
  const [milestoneModal, setMilestoneModal] = useState<{ open: boolean; item: Partial<ApiProjectMilestone> | null }>({ open: false, item: null });
  const [milestoneSaving, setMilestoneSaving] = useState(false);

  // risk modal
  const [riskModal, setRiskModal] = useState<{ open: boolean; item: Partial<ApiProjectRisk> | null }>({ open: false, item: null });
  const [riskSaving, setRiskSaving] = useState(false);

  // deliverable modal
  const [deliverableModal, setDeliverableModal] = useState<{ open: boolean; item: Partial<ApiProjectDeliverable> | null }>({ open: false, item: null });
  const [deliverableSaving, setDeliverableSaving] = useState(false);

  // artifact modal
  const [artifactModal, setArtifactModal] = useState<{ open: boolean; item: Partial<ApiProjectArtifact> | null; file?: File }>({ open: false, item: null });
  const [artifactSaving, setArtifactSaving] = useState(false);

  // team modal
  const [teamModal, setTeamModal] = useState(false);
  const [newMember, setNewMember] = useState({ userId: '', role: 'Consultant', allocation: '100' });
  const [consultants, setConsultants] = useState<{ id: number; name: string; email: string }[]>([]);
  const [teamSaving, setTeamSaving] = useState(false);

  const [modalError, setModalError] = useState('');

  useEffect(() => {
    if (id) loadProject(id);
  }, [id]);

  useEffect(() => {
    if (teamModal && consultants.length === 0) {
      apiGetConsultants().then(r => setConsultants(r.results.map(c => ({ id: c.id, name: c.name, email: c.email })))).catch(() => {});
    }
  }, [teamModal]);

  const loadProject = async (projectId: string) => {
    setIsLoading(true);
    try {
      const data = await apiGetProject(projectId);
      setProject(data);
      if (data.phases?.length) {
        setExpandedPhases(new Set(data.phases.map(p => p.id)));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar projeto');
    } finally {
      setIsLoading(false);
    }
  };

  const reload = () => id && loadProject(id);

  const handleStatusChange = async (action: 'activate' | 'complete' | 'close' | 'hold') => {
    if (!id) return;
    try {
      await apiUpdateProjectStatus(id, action);
      reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar estado');
    }
  };

  // ── phase title editing ──────────────────────────────────────────────────

  const startEditPhase = (phase: ApiProjectPhase) => {
    setEditingPhaseId(phase.id);
    setEditingPhaseTitle(phase.title || '');
  };

  const savePhaseTitle = async (phaseId: number) => {
    setSavingPhaseId(phaseId);
    try {
      await apiUpdateProjectPhase(phaseId, { title: editingPhaseTitle });
      setEditingPhaseId(null);
      reload();
    } catch {
    } finally {
      setSavingPhaseId(null);
    }
  };

  // ── milestone CRUD ───────────────────────────────────────────────────────

  const openMilestoneModal = (item: Partial<ApiProjectMilestone> | null = null) => {
    setModalError('');
    setMilestoneModal({ open: true, item: item ?? { title: '', description: '', due_date: '', status: 'pending', deliverables: '' } });
  };

  const saveMilestone = async () => {
    if (!id || !milestoneModal.item) return;
    setMilestoneSaving(true);
    setModalError('');
    try {
      if (milestoneModal.item.id) {
        await apiUpdateProjectMilestone(milestoneModal.item.id, milestoneModal.item);
      } else {
        await apiCreateProjectMilestone(id, milestoneModal.item);
      }
      setMilestoneModal({ open: false, item: null });
      reload();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Erro ao guardar marco');
    } finally {
      setMilestoneSaving(false);
    }
  };

  const deleteMilestone = async (milestoneId: number) => {
    if (!confirm('Eliminar este marco?')) return;
    try {
      await apiDeleteProjectMilestone(milestoneId);
      reload();
    } catch {}
  };

  // ── risk CRUD ────────────────────────────────────────────────────────────

  const openRiskModal = (item: Partial<ApiProjectRisk> | null = null) => {
    setModalError('');
    setRiskModal({ open: true, item: item ?? { title: '', description: '', severity: 'medium', status: 'open', mitigation_plan: '' } });
  };

  const saveRisk = async () => {
    if (!id || !riskModal.item) return;
    setRiskSaving(true);
    setModalError('');
    try {
      if (riskModal.item.id) {
        await apiUpdateProjectRisk(riskModal.item.id, riskModal.item);
      } else {
        await apiCreateProjectRisk(id, riskModal.item);
      }
      setRiskModal({ open: false, item: null });
      reload();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Erro ao guardar risco');
    } finally {
      setRiskSaving(false);
    }
  };

  const deleteRisk = async (riskId: number) => {
    if (!confirm('Eliminar este risco?')) return;
    try {
      await apiDeleteProjectRisk(riskId);
      reload();
    } catch {}
  };

  // ── deliverable CRUD ─────────────────────────────────────────────────────

  const openDeliverableModal = (item: Partial<ApiProjectDeliverable> | null = null, phaseId?: number) => {
    setModalError('');
    setDeliverableModal({
      open: true,
      item: item ?? { title: '', description: '', status: 'pending', phase: phaseId ?? null, due_date: '' },
    });
  };

  const saveDeliverable = async () => {
    if (!id || !deliverableModal.item) return;
    setDeliverableSaving(true);
    setModalError('');
    try {
      if (deliverableModal.item.id) {
        await apiUpdateProjectDeliverable(deliverableModal.item.id, deliverableModal.item);
      } else {
        await apiCreateProjectDeliverable(id, deliverableModal.item);
      }
      setDeliverableModal({ open: false, item: null });
      reload();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Erro ao guardar entregável');
    } finally {
      setDeliverableSaving(false);
    }
  };

  const deleteDeliverable = async (dId: number) => {
    if (!confirm('Eliminar este entregável?')) return;
    try {
      await apiDeleteProjectDeliverable(dId);
      reload();
    } catch {}
  };

  // ── artifact CRUD ────────────────────────────────────────────────────────

  const openArtifactModal = (item: Partial<ApiProjectArtifact> | null = null) => {
    setModalError('');
    setArtifactModal({ open: true, item: item ?? { artifact_type: 'final_proposal', title: '', status: 'pending', notes: '', external_url: '' } });
  };

  const saveArtifact = async () => {
    if (!id || !artifactModal.item) return;
    setArtifactSaving(true);
    setModalError('');
    try {
      if (artifactModal.item.id) {
        await apiUpdateProjectArtifact(artifactModal.item.id, { ...artifactModal.item, file: artifactModal.file });
      } else {
        await apiCreateProjectArtifact(id, { ...artifactModal.item, file: artifactModal.file });
      }
      setArtifactModal({ open: false, item: null });
      reload();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Erro ao guardar documento');
    } finally {
      setArtifactSaving(false);
    }
  };

  // ── team CRUD ────────────────────────────────────────────────────────────

  const addTeamMember = async () => {
    if (!id || !newMember.userId) return;
    setTeamSaving(true);
    setModalError('');
    try {
      await apiAddProjectTeamMember(id, {
        user: parseInt(newMember.userId),
        role: newMember.role,
        allocation_percentage: parseInt(newMember.allocation),
      });
      setTeamModal(false);
      setNewMember({ userId: '', role: 'Consultant', allocation: '100' });
      reload();
    } catch (err) {
      setModalError(err instanceof Error ? err.message : 'Erro ao adicionar membro');
    } finally {
      setTeamSaving(false);
    }
  };

  const removeTeamMember = async (memberId: number) => {
    if (!confirm('Remover este membro da equipa?')) return;
    try {
      await apiDeleteProjectTeamMember(memberId);
      reload();
    } catch {}
  };

  // ── render guards ────────────────────────────────────────────────────────

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

  // group deliverables by phase
  const deliverablesByPhase = (project.deliverables || []).reduce<Record<string, ApiProjectDeliverable[]>>((acc, d) => {
    const key = d.phase != null ? String(d.phase) : 'unassigned';
    if (!acc[key]) acc[key] = [];
    acc[key].push(d);
    return acc;
  }, {});

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
            <p className="text-sm text-muted-foreground">Orçamento Total</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/20 rounded text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Actions */}
      {actions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {actions.map((a) => (
            <Button key={a.action} variant={a.variant as 'default' | 'outline'} onClick={() => handleStatusChange(a.action)}>
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
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="phases">Fases PMI</TabsTrigger>
          <TabsTrigger value="deliverables">Entregáveis</TabsTrigger>
          <TabsTrigger value="artifacts">Documentos</TabsTrigger>
          <TabsTrigger value="kanban">Tarefas</TabsTrigger>
          <TabsTrigger value="gantt">Timeline</TabsTrigger>
          <TabsTrigger value="team">Equipa</TabsTrigger>
          <TabsTrigger value="milestones">Marcos</TabsTrigger>
          <TabsTrigger value="risks">Riscos</TabsTrigger>
        </TabsList>

        {/* ── OVERVIEW ── */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card><CardContent className="p-4">
              <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">Início</span></div>
              <p className="text-lg font-semibold mt-1">{project.start_date ? formatDate(new Date(project.start_date)) : '—'}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">Fim Previsto</span></div>
              <p className="text-lg font-semibold mt-1">{project.end_date ? formatDate(new Date(project.end_date)) : '—'}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center gap-2"><DollarSign className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">Custo Real</span></div>
              <p className="text-lg font-semibold mt-1">{formatCurrency(parseFloat(project.actual_cost), project.budget_currency)}</p>
            </CardContent></Card>
            <Card><CardContent className="p-4">
              <div className="flex items-center gap-2"><Users className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">Equipa</span></div>
              <p className="text-lg font-semibold mt-1">{project.team?.length || 0} membros</p>
            </CardContent></Card>
          </div>
          <Card>
            <CardHeader><CardTitle>Descrição</CardTitle></CardHeader>
            <CardContent>
              <p className="text-muted-foreground whitespace-pre-line">{project.description || 'Sem descrição.'}</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── PHASES ── */}
        <TabsContent value="phases">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="h-5 w-5" />
                Fases do Projeto (PMI)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!project.phases?.length ? (
                <p className="text-muted-foreground text-center py-8">Nenhuma fase definida.</p>
              ) : (
                <div className="space-y-4">
                  {project.phases.map((phase, index) => (
                    <div key={phase.id} className="relative">
                      {index < project.phases.length - 1 && (
                        <div className="absolute left-5 top-10 w-0.5 h-full bg-muted" />
                      )}
                      <div className="flex items-start gap-4">
                        <div className={cn(
                          'h-10 w-10 rounded-full flex items-center justify-center flex-shrink-0',
                          phase.is_completed ? 'bg-green-600 text-white' : phase.completion_percentage > 0 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
                        )}>
                          {phase.is_completed ? <CheckCircle2 className="h-5 w-5" /> : <Circle className="h-5 w-5" />}
                        </div>
                        <div className="flex-1 pb-6">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              {editingPhaseId === phase.id ? (
                                <div className="flex items-center gap-2">
                                  <Input
                                    value={editingPhaseTitle}
                                    onChange={e => setEditingPhaseTitle(e.target.value)}
                                    placeholder={phase.name_display}
                                    className="h-7 text-sm"
                                    onKeyDown={e => { if (e.key === 'Enter') savePhaseTitle(phase.id); if (e.key === 'Escape') setEditingPhaseId(null); }}
                                  />
                                  <Button size="sm" className="h-7 px-2" onClick={() => savePhaseTitle(phase.id)} disabled={savingPhaseId === phase.id}>
                                    {savingPhaseId === phase.id ? '...' : 'OK'}
                                  </Button>
                                  <Button size="sm" variant="ghost" className="h-7 px-2" onClick={() => setEditingPhaseId(null)}>✕</Button>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2">
                                  <p className="font-semibold">{phase.title || phase.name_display}</p>
                                  {phase.title && phase.title !== phase.name_display && (
                                    <span className="text-xs text-muted-foreground">({phase.name_display})</span>
                                  )}
                                  <Button size="sm" variant="ghost" className="h-6 w-6 p-0 opacity-50 hover:opacity-100" onClick={() => startEditPhase(phase)}>
                                    <Pencil className="h-3 w-3" />
                                  </Button>
                                </div>
                              )}
                              <p className="text-sm text-muted-foreground">{phase.description || 'Sem descrição'}</p>
                            </div>
                            <Badge variant={phase.is_completed ? 'default' : 'outline'} className={phase.is_completed ? 'bg-green-600' : ''}>
                              {phase.is_completed ? 'Concluída' : `${phase.completion_percentage}%`}
                            </Badge>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
                            {phase.start_date && (
                              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />Início: {formatDate(new Date(phase.start_date))}</span>
                            )}
                            {phase.end_date && (
                              <span className="flex items-center gap-1"><Calendar className="h-3 w-3" />Fim: {formatDate(new Date(phase.end_date))}</span>
                            )}
                          </div>
                          {!phase.is_completed && (
                            <div className="mt-2">
                              <div className="flex justify-between text-sm mb-1">
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

        {/* ── DELIVERABLES ── */}
        <TabsContent value="deliverables">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Package className="h-5 w-5" />
                  Entregáveis por Fase
                </CardTitle>
                <Button size="sm" onClick={() => openDeliverableModal()}>
                  <Plus className="h-4 w-4 mr-1" />
                  Novo Entregável
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* deliverables grouped by phase */}
              {project.phases?.map(phase => {
                const phaseDeliverables = deliverablesByPhase[String(phase.id)] || [];
                const isExpanded = expandedPhases.has(phase.id);
                return (
                  <div key={phase.id} className="border rounded-lg overflow-hidden">
                    <button
                      className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
                      onClick={() => setExpandedPhases(prev => {
                        const next = new Set(prev);
                        if (next.has(phase.id)) next.delete(phase.id); else next.add(phase.id);
                        return next;
                      })}
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                        <span className="font-medium">{phase.title || phase.name_display}</span>
                        <Badge variant="outline" className="text-xs">{phaseDeliverables.length}</Badge>
                      </div>
                      <Button size="sm" variant="ghost" className="h-6 px-2 text-xs" onClick={e => { e.stopPropagation(); openDeliverableModal(null, phase.id); }}>
                        <Plus className="h-3 w-3 mr-1" />Adicionar
                      </Button>
                    </button>
                    {isExpanded && (
                      <div className="divide-y">
                        {phaseDeliverables.length === 0 ? (
                          <p className="text-sm text-muted-foreground text-center py-4">Sem entregáveis nesta fase.</p>
                        ) : phaseDeliverables.map(d => (
                          <div key={d.id} className="flex items-center justify-between px-4 py-3">
                            <div className="flex-1">
                              <p className="text-sm font-medium">{d.title}</p>
                              <div className="flex items-center gap-2 mt-1">
                                {d.due_date && <span className="text-xs text-muted-foreground">{formatDate(new Date(d.due_date))}</span>}
                                <span className={cn('text-xs font-medium', deliverableStatusColor(d.status))}>{d.status_display || d.status}</span>
                              </div>
                            </div>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => openDeliverableModal(d)}>
                                <Pencil className="h-3 w-3" />
                              </Button>
                              <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-destructive hover:text-destructive" onClick={() => deleteDeliverable(d.id)}>
                                <Trash2 className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
              {/* unassigned deliverables */}
              {(deliverablesByPhase['unassigned'] || []).length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="p-3 bg-muted/30 font-medium flex items-center gap-2">
                    <Package className="h-4 w-4" />Sem fase atribuída
                    <Badge variant="outline" className="text-xs">{deliverablesByPhase['unassigned'].length}</Badge>
                  </div>
                  <div className="divide-y">
                    {deliverablesByPhase['unassigned'].map(d => (
                      <div key={d.id} className="flex items-center justify-between px-4 py-3">
                        <div className="flex-1">
                          <p className="text-sm font-medium">{d.title}</p>
                          <span className={cn('text-xs font-medium', deliverableStatusColor(d.status))}>{d.status_display || d.status}</span>
                        </div>
                        <div className="flex gap-1">
                          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => openDeliverableModal(d)}><Pencil className="h-3 w-3" /></Button>
                          <Button size="sm" variant="ghost" className="h-7 w-7 p-0 text-destructive" onClick={() => deleteDeliverable(d.id)}><Trash2 className="h-3 w-3" /></Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {!project.deliverables?.length && (
                <p className="text-muted-foreground text-center py-8">Nenhum entregável definido.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── ARTIFACTS / HANDOVER DOCS ── */}
        <TabsContent value="artifacts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Documentos de Handover
                </CardTitle>
                <Button size="sm" onClick={() => openArtifactModal()}>
                  <Plus className="h-4 w-4 mr-1" />
                  Novo Documento
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Fixed artifact type slots */}
              <div className="space-y-3">
                {ARTIFACT_TYPES.map(({ value: aType, label }) => {
                  const existing = (project.artifacts || []).filter(a => a.artifact_type === aType);
                  return (
                    <div key={aType} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{label}</h4>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-xs" onClick={() => openArtifactModal({ artifact_type: aType })}>
                          <Plus className="h-3 w-3 mr-1" />Adicionar
                        </Button>
                      </div>
                      {existing.length === 0 ? (
                        <p className="text-xs text-muted-foreground">Nenhum documento registado.</p>
                      ) : (
                        <div className="space-y-2">
                          {existing.map(a => (
                            <div key={a.id} className={cn('flex items-center justify-between p-2 rounded border text-sm', artifactStatusColor(a.status))}>
                              <div className="flex items-center gap-2 flex-1 min-w-0">
                                <FileText className="h-4 w-4 flex-shrink-0" />
                                <span className="truncate font-medium">{a.title}</span>
                                <Badge variant="outline" className="text-xs flex-shrink-0">{a.status_display || a.status}</Badge>
                              </div>
                              <div className="flex items-center gap-1 ml-2">
                                {a.file_url && (
                                  <a href={a.file_url} target="_blank" rel="noopener noreferrer">
                                    <Button size="sm" variant="ghost" className="h-7 w-7 p-0"><ExternalLink className="h-3 w-3" /></Button>
                                  </a>
                                )}
                                <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => openArtifactModal(a)}><Pencil className="h-3 w-3" /></Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── KANBAN ── */}
        <TabsContent value="kanban">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><LayoutGrid className="h-5 w-5" />Quadro de Tarefas</CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                const columns = [
                  { id: 'todo', title: 'Por Fazer' },
                  { id: 'in_progress', title: 'Em Curso' },
                  { id: 'review', title: 'Revisão' },
                  { id: 'done', title: 'Concluído' },
                ];
                const tasks: KanbanTask[] = [
                  ...(project.milestones?.map(m => ({
                    id: `milestone-${m.id}`, title: m.title, description: m.description,
                    status: m.status === 'completed' ? 'done' : m.status === 'in_progress' ? 'in_progress' : 'todo',
                    priority: 'medium' as const, dueDate: m.due_date ? new Date(m.due_date).toLocaleDateString('pt-PT') : undefined,
                  })) || []),
                  ...(project.deliverables?.map(d => ({
                    id: `deliverable-${d.id}`, title: d.title, description: d.description,
                    status: d.status === 'accepted' || d.status === 'approved' ? 'done' : d.status === 'under_review' || d.status === 'submitted' ? 'review' : d.status === 'in_progress' ? 'in_progress' : 'todo',
                    priority: 'medium' as const, dueDate: d.due_date ? new Date(d.due_date).toLocaleDateString('pt-PT') : undefined,
                  })) || []),
                ];
                return tasks.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">Crie marcos e entregáveis para visualizar aqui.</p>
                ) : (
                  <KanbanBoard columns={columns} tasks={tasks} onTaskMove={() => {}} onTaskClick={() => {}} />
                );
              })()}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── GANTT ── */}
        <TabsContent value="gantt">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" />Cronograma do Projeto</CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                const items: GanttItem[] = [
                  ...(project.phases?.map(p => ({
                    id: `phase-${p.id}`, name: p.title || p.name_display,
                    startDate: p.start_date ? new Date(p.start_date) : new Date(project.start_date || Date.now()),
                    endDate: p.end_date ? new Date(p.end_date) : new Date(project.end_date || Date.now() + 30 * 24 * 60 * 60 * 1000),
                    progress: p.completion_percentage, type: 'phase' as const,
                    status: p.is_completed ? 'completed' : p.completion_percentage > 0 ? 'in_progress' : 'not_started',
                  })) || []),
                  ...(project.milestones?.map(m => ({
                    id: `milestone-${m.id}`, name: m.title,
                    startDate: m.due_date ? new Date(m.due_date) : new Date(),
                    endDate: m.due_date ? new Date(new Date(m.due_date).getTime() + 24 * 60 * 60 * 1000) : new Date(),
                    progress: m.status === 'completed' ? 100 : 0, type: 'milestone' as const,
                    status: m.status === 'completed' ? 'completed' : m.status === 'delayed' ? 'delayed' : 'not_started',
                  })) || []),
                ];
                return items.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">Defina fases e marcos com datas.</p>
                ) : (
                  <GanttChart items={items} onItemClick={() => {}} />
                );
              })()}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── TEAM ── */}
        <TabsContent value="team">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Equipa do Projeto</CardTitle>
                <Button size="sm" onClick={() => { setModalError(''); setTeamModal(true); }}>
                  <Plus className="h-4 w-4 mr-1" />Adicionar Membro
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {!project.team?.length ? (
                <p className="text-muted-foreground text-center py-8">Nenhum membro atribuído.</p>
              ) : (
                <div className="space-y-3">
                  {project.team.map(member => (
                    <div key={member.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold">
                          {member.user.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <p className="font-medium">{member.user.name}</p>
                          <p className="text-sm text-muted-foreground">{member.user.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <Badge>{member.role}</Badge>
                          <p className="text-xs text-muted-foreground mt-1">{member.allocation_percentage}% alocação</p>
                        </div>
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-destructive hover:text-destructive" onClick={() => removeTeamMember(member.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── MILESTONES ── */}
        <TabsContent value="milestones">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Marcos</CardTitle>
                <Button size="sm" onClick={() => openMilestoneModal()}>
                  <Plus className="h-4 w-4 mr-1" />Novo Marco
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {!project.milestones?.length ? (
                <p className="text-muted-foreground text-center py-8">Nenhum marco definido.</p>
              ) : (
                <div className="space-y-3">
                  {project.milestones.map(m => (
                    <div key={m.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                      <div className="flex-1">
                        <p className="font-medium">{m.title}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-sm text-muted-foreground">{m.due_date ? formatDate(new Date(m.due_date)) : '—'}</span>
                          {m.deliverables && <span className="text-xs text-muted-foreground truncate max-w-xs">{m.deliverables}</span>}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={m.status} size="sm" />
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={() => openMilestoneModal(m)}><Pencil className="h-4 w-4" /></Button>
                        <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-destructive" onClick={() => deleteMilestone(m.id)}><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── RISKS ── */}
        <TabsContent value="risks">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Riscos e Issues</CardTitle>
                <Button size="sm" onClick={() => openRiskModal()}>
                  <Plus className="h-4 w-4 mr-1" />Novo Risco
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {!project.risks?.length ? (
                <p className="text-muted-foreground text-center py-8">Nenhum risco identificado.</p>
              ) : (
                <div className="space-y-3">
                  {project.risks.map(r => (
                    <div key={r.id} className={cn('p-4 rounded-lg border', r.severity === 'critical' ? 'bg-destructive/10 border-destructive/20' : r.severity === 'high' ? 'bg-error/10 border-error/20' : r.severity === 'medium' ? 'bg-warning/10 border-warning/20' : 'bg-success/10 border-success/20')}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{r.title}</p>
                          <p className="text-sm text-muted-foreground mt-1">{r.description}</p>
                          {r.mitigation_plan && (
                            <p className="text-sm mt-2"><strong>Mitigação:</strong> {r.mitigation_plan}</p>
                          )}
                        </div>
                        <div className="flex items-start gap-2 ml-3">
                          <div className="text-right">
                            <Badge variant={r.severity === 'critical' || r.severity === 'high' ? 'destructive' : 'outline'}>{r.severity}</Badge>
                            <p className="text-xs text-muted-foreground mt-1">{r.status}</p>
                          </div>
                          <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={() => openRiskModal(r)}><Pencil className="h-4 w-4" /></Button>
                          <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-destructive" onClick={() => deleteRisk(r.id)}><Trash2 className="h-4 w-4" /></Button>
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

      {/* ── MILESTONE MODAL ── */}
      <Dialog open={milestoneModal.open} onOpenChange={o => !o && setMilestoneModal({ open: false, item: null })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{milestoneModal.item?.id ? 'Editar Marco' : 'Novo Marco'}</DialogTitle>
          </DialogHeader>
          {milestoneModal.item && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Título *</label>
                <Input value={milestoneModal.item.title || ''} onChange={e => setMilestoneModal(s => ({ ...s, item: { ...s.item!, title: e.target.value } }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Descrição</label>
                <Textarea value={milestoneModal.item.description || ''} onChange={e => setMilestoneModal(s => ({ ...s, item: { ...s.item!, description: e.target.value } }))} rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium">Data Limite</label>
                  <Input type="date" value={milestoneModal.item.due_date || ''} onChange={e => setMilestoneModal(s => ({ ...s, item: { ...s.item!, due_date: e.target.value } }))} />
                </div>
                <div>
                  <label className="text-sm font-medium">Estado</label>
                  <Select value={milestoneModal.item.status || 'pending'} onValueChange={v => setMilestoneModal(s => ({ ...s, item: { ...s.item!, status: v } }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{MILESTONE_STATUS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Entregáveis associados</label>
                <Input value={milestoneModal.item.deliverables || ''} onChange={e => setMilestoneModal(s => ({ ...s, item: { ...s.item!, deliverables: e.target.value } }))} placeholder="Descrição dos entregáveis" />
              </div>
              {modalError && <p className="text-sm text-destructive">{modalError}</p>}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setMilestoneModal({ open: false, item: null })}>Cancelar</Button>
            <Button onClick={saveMilestone} disabled={milestoneSaving}>{milestoneSaving ? 'A guardar...' : 'Guardar'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── RISK MODAL ── */}
      <Dialog open={riskModal.open} onOpenChange={o => !o && setRiskModal({ open: false, item: null })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{riskModal.item?.id ? 'Editar Risco' : 'Novo Risco'}</DialogTitle>
          </DialogHeader>
          {riskModal.item && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Título *</label>
                <Input value={riskModal.item.title || ''} onChange={e => setRiskModal(s => ({ ...s, item: { ...s.item!, title: e.target.value } }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Descrição</label>
                <Textarea value={riskModal.item.description || ''} onChange={e => setRiskModal(s => ({ ...s, item: { ...s.item!, description: e.target.value } }))} rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium">Severidade</label>
                  <Select value={riskModal.item.severity || 'medium'} onValueChange={v => setRiskModal(s => ({ ...s, item: { ...s.item!, severity: v } }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{RISK_SEVERITY.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Estado</label>
                  <Select value={riskModal.item.status || 'open'} onValueChange={v => setRiskModal(s => ({ ...s, item: { ...s.item!, status: v } }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{RISK_STATUS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Plano de Mitigação</label>
                <Textarea value={riskModal.item.mitigation_plan || ''} onChange={e => setRiskModal(s => ({ ...s, item: { ...s.item!, mitigation_plan: e.target.value } }))} rows={2} />
              </div>
              {modalError && <p className="text-sm text-destructive">{modalError}</p>}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setRiskModal({ open: false, item: null })}>Cancelar</Button>
            <Button onClick={saveRisk} disabled={riskSaving}>{riskSaving ? 'A guardar...' : 'Guardar'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── DELIVERABLE MODAL ── */}
      <Dialog open={deliverableModal.open} onOpenChange={o => !o && setDeliverableModal({ open: false, item: null })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{deliverableModal.item?.id ? 'Editar Entregável' : 'Novo Entregável'}</DialogTitle>
          </DialogHeader>
          {deliverableModal.item && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Título *</label>
                <Input value={deliverableModal.item.title || ''} onChange={e => setDeliverableModal(s => ({ ...s, item: { ...s.item!, title: e.target.value } }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Descrição</label>
                <Textarea value={deliverableModal.item.description || ''} onChange={e => setDeliverableModal(s => ({ ...s, item: { ...s.item!, description: e.target.value } }))} rows={2} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium">Data Limite</label>
                  <Input type="date" value={deliverableModal.item.due_date || ''} onChange={e => setDeliverableModal(s => ({ ...s, item: { ...s.item!, due_date: e.target.value } }))} />
                </div>
                <div>
                  <label className="text-sm font-medium">Estado</label>
                  <Select value={deliverableModal.item.status || 'pending'} onValueChange={v => setDeliverableModal(s => ({ ...s, item: { ...s.item!, status: v } }))}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>{DELIVERABLE_STATUS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Fase</label>
                <Select
                  value={deliverableModal.item.phase != null ? String(deliverableModal.item.phase) : 'none'}
                  onValueChange={v => setDeliverableModal(s => ({ ...s, item: { ...s.item!, phase: v === 'none' ? null : parseInt(v) } }))}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sem fase</SelectItem>
                    {project.phases?.map(p => <SelectItem key={p.id} value={String(p.id)}>{p.title || p.name_display}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              {modalError && <p className="text-sm text-destructive">{modalError}</p>}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeliverableModal({ open: false, item: null })}>Cancelar</Button>
            <Button onClick={saveDeliverable} disabled={deliverableSaving}>{deliverableSaving ? 'A guardar...' : 'Guardar'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── ARTIFACT MODAL ── */}
      <Dialog open={artifactModal.open} onOpenChange={o => !o && setArtifactModal({ open: false, item: null })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{artifactModal.item?.id ? 'Editar Documento' : 'Novo Documento'}</DialogTitle>
          </DialogHeader>
          {artifactModal.item && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">Tipo de Documento</label>
                <Select value={artifactModal.item.artifact_type || 'final_proposal'} onValueChange={v => setArtifactModal(s => ({ ...s, item: { ...s.item!, artifact_type: v } }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{ARTIFACT_TYPES.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Título *</label>
                <Input value={artifactModal.item.title || ''} onChange={e => setArtifactModal(s => ({ ...s, item: { ...s.item!, title: e.target.value } }))} />
              </div>
              <div>
                <label className="text-sm font-medium">Estado</label>
                <Select value={artifactModal.item.status || 'pending'} onValueChange={v => setArtifactModal(s => ({ ...s, item: { ...s.item!, status: v } }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{ARTIFACT_STATUS.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Notas</label>
                <Textarea value={artifactModal.item.notes || ''} onChange={e => setArtifactModal(s => ({ ...s, item: { ...s.item!, notes: e.target.value } }))} rows={2} />
              </div>
              <div>
                <label className="text-sm font-medium">URL Externo</label>
                <Input value={artifactModal.item.external_url || ''} onChange={e => setArtifactModal(s => ({ ...s, item: { ...s.item!, external_url: e.target.value } }))} placeholder="https://..." />
              </div>
              <div>
                <label className="text-sm font-medium">Ficheiro</label>
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-2 cursor-pointer border rounded px-3 py-2 text-sm hover:bg-muted/50 transition-colors">
                    <Upload className="h-4 w-4" />
                    {artifactModal.file ? artifactModal.file.name : 'Selecionar ficheiro'}
                    <input type="file" className="hidden" onChange={e => setArtifactModal(s => ({ ...s, file: e.target.files?.[0] }))} />
                  </label>
                  {artifactModal.item.file_url && !artifactModal.file && (
                    <a href={artifactModal.item.file_url} target="_blank" rel="noopener noreferrer" className="text-xs text-primary flex items-center gap-1">
                      <ExternalLink className="h-3 w-3" />Ver atual
                    </a>
                  )}
                </div>
              </div>
              {modalError && <p className="text-sm text-destructive">{modalError}</p>}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setArtifactModal({ open: false, item: null })}>Cancelar</Button>
            <Button onClick={saveArtifact} disabled={artifactSaving}>{artifactSaving ? 'A guardar...' : 'Guardar'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── TEAM MEMBER MODAL ── */}
      <Dialog open={teamModal} onOpenChange={o => !o && setTeamModal(false)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Adicionar Membro à Equipa</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-sm font-medium">Consultor</label>
              <Select value={newMember.userId} onValueChange={v => setNewMember(s => ({ ...s, userId: v }))}>
                <SelectTrigger><SelectValue placeholder="Selecionar consultor..." /></SelectTrigger>
                <SelectContent>
                  {consultants.map(c => (
                    <SelectItem key={c.id} value={String(c.id)}>{c.name} — {c.email}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Função</label>
              <Select value={newMember.role} onValueChange={v => setNewMember(s => ({ ...s, role: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{MEMBER_ROLES.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">Alocação (%)</label>
              <Input type="number" min="1" max="100" value={newMember.allocation} onChange={e => setNewMember(s => ({ ...s, allocation: e.target.value }))} />
            </div>
            {modalError && <p className="text-sm text-destructive">{modalError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTeamModal(false)}>Cancelar</Button>
            <Button onClick={addTeamMember} disabled={teamSaving || !newMember.userId}>{teamSaving ? 'A adicionar...' : 'Adicionar'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
