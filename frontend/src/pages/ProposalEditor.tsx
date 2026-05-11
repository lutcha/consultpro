// ============================================
// PROPOSAL EDITOR PAGE - Rich Text + AI + Pipeline
// ============================================

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Save, CheckCircle, FileText, CheckSquare, FileType, FileDown,
  Upload, Building2, UserCircle, Plus, X, Eye, ChevronRight, Calendar,
  Paperclip, ExternalLink, ArrowRight, Send, Star, MessageSquare,
  RefreshCw, Trophy, CheckCircle2, Zap, Handshake, Clock, FileCheck,
  AlertCircle, GitBranch, Flag,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter } from '@/components/ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AIAssistButton } from '@/components/proposals/AIAssistButton';
import { RichTextEditor } from '@/components/proposals/RichTextEditor';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useProposalStore } from '@/stores';
import {
  apiDownloadProposalWord, apiDownloadProposalPdf, apiUploadProposalLogo,
  apiGetProposalEvents, apiCreateProposalEvent, apiTransitionProposalStatus,
  type ApiProposalEvent,
} from '@/lib/api';
import type { ProposalStatus } from '@/types';
import { cn } from '@/lib/utils';

// ── Pipeline config ────────────────────────────────────────────────────────

const PIPELINE_TRANSITIONS: Record<string, Array<{ status: ProposalStatus; label: string }>> = {
  draft: [{ status: 'in_review', label: 'Enviar para Revisão' }],
  in_review: [
    { status: 'qc_check', label: 'Enviar para QC' },
    { status: 'draft', label: 'Devolver ao Editor' },
  ],
  qc_check: [
    { status: 'ready_for_submission', label: 'Aprovar QC' },
    { status: 'in_review', label: 'Devolver à Revisão' },
  ],
  ready_for_submission: [{ status: 'submitted', label: 'Submeter ao Cliente' }],
  submitted: [
    { status: 'under_evaluation', label: 'Marcar Em Avaliação' },
    { status: 'rejected', label: 'Marcar Rejeitada' },
  ],
  under_evaluation: [
    { status: 'shortlisted', label: 'Marcar Shortlisted' },
    { status: 'clarifications_requested', label: 'Pedido de Clarificações' },
    { status: 'rejected', label: 'Marcar Rejeitada' },
  ],
  shortlisted: [
    { status: 'bafo', label: 'Recebeu Pedido de BAFO' },
    { status: 'awarded', label: 'Marcar Adjudicada' },
    { status: 'lost', label: 'Marcar Perdida' },
  ],
  clarifications_requested: [
    { status: 'under_evaluation', label: 'Resposta Enviada' },
    { status: 'rejected', label: 'Marcar Rejeitada' },
  ],
  bafo: [
    { status: 'awarded', label: 'Marcar Adjudicada' },
    { status: 'lost', label: 'Marcar Perdida' },
  ],
  awarded: [{ status: 'contract_negotiation', label: 'Iniciar Negociação' }],
  contract_negotiation: [{ status: 'contract_signed', label: 'Contrato Assinado' }],
  contract_signed: [{ status: 'project_initiation', label: 'Arrancar Projeto' }],
  project_initiation: [{ status: 'won', label: 'Marcar Ganha' }],
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Rascunho',
  in_review: 'Em Revisão',
  qc_check: 'QC em Curso',
  ready_for_submission: 'Pronta para Submissão',
  approved: 'Aprovada',
  submitted: 'Submetida',
  under_evaluation: 'Em Avaliação',
  rejected: 'Rejeitada',
  shortlisted: 'Shortlisted',
  clarifications_requested: 'Clarificações Pedidas',
  bafo: 'BAFO',
  awarded: 'Adjudicada',
  contract_negotiation: 'Negociação de Contrato',
  contract_signed: 'Contrato Assinado',
  project_initiation: 'Arranque de Projeto',
  won: 'Ganha',
  lost: 'Perdida',
};

// Main linear flow (excluding terminal branches)
const PIPELINE_STAGES = [
  { status: 'draft',                   label: 'Rascunho',               group: 'Preparação' },
  { status: 'in_review',               label: 'Em Revisão',             group: 'Preparação' },
  { status: 'qc_check',               label: 'Quality Check',           group: 'Preparação' },
  { status: 'ready_for_submission',    label: 'Pronta para Submissão',  group: 'Preparação' },
  { status: 'submitted',               label: 'Submetida',              group: 'Submissão' },
  { status: 'under_evaluation',        label: 'Em Avaliação',           group: 'Avaliação' },
  { status: 'shortlisted',            label: 'Shortlisted',            group: 'Avaliação' },
  { status: 'clarifications_requested',label: 'Clarificações',          group: 'Avaliação' },
  { status: 'bafo',                    label: 'BAFO',                   group: 'Avaliação' },
  { status: 'awarded',                 label: 'Adjudicada',             group: 'Decisão' },
  { status: 'contract_negotiation',    label: 'Negociação',             group: 'Contratação' },
  { status: 'contract_signed',         label: 'Contrato Assinado',      group: 'Contratação' },
  { status: 'project_initiation',      label: 'Arranque de Projeto',    group: 'Contratação' },
  { status: 'won',                     label: 'Ganha',                  group: 'Final' },
];

const TERMINAL_STAGES = [
  { status: 'rejected', label: 'Rejeitada' },
  { status: 'lost',     label: 'Perdida'   },
];

const STATUS_ORDER: Record<string, number> = Object.fromEntries(
  PIPELINE_STAGES.map((s, i) => [s.status, i])
);

// COS context: what should exist at each stage
const STAGE_CONTEXT: Record<string, { hint: string; artifacts: string[] }> = {
  submitted: {
    hint: 'A proposta está em avaliação pelo cliente.',
    artifacts: ['Comprovativo de submissão', 'Proposta final v' ],
  },
  clarifications_requested: {
    hint: 'O cliente pediu clarificações. Responda com rigor e brevidade.',
    artifacts: ['Documento de clarificações', 'Proposta ajustada (se necessário)'],
  },
  bafo: {
    hint: 'Best And Final Offer — prepare a versão definitiva com ajustes.',
    artifacts: ['BAFO Proposal', 'BAFO Budget', 'Summary of Changes'],
  },
  awarded: {
    hint: 'Parabéns! A proposta foi adjudicada. Inicie a negociação contratual.',
    artifacts: ['Pacote de negociação', 'Draft de contrato'],
  },
  contract_negotiation: {
    hint: 'Negoceie os termos. Documente todas as alterações e riscos.',
    artifacts: ['Draft de contrato', 'Matriz de riscos', 'Notas de negociação'],
  },
  contract_signed: {
    hint: 'Contrato assinado. Prepare o arranque formal do projeto.',
    artifacts: ['Contrato assinado', 'Resumo do contrato'],
  },
  project_initiation: {
    hint: 'Transfira para a equipa de execução com o handover completo.',
    artifacts: ['Kickoff Pack', 'Plano de trabalho', 'Mapa de stakeholders', 'RACI'],
  },
};

// ── Event config ────────────────────────────────────────────────────────────

const EVENT_TYPE_OPTIONS = [
  { value: 'submission',   label: 'Submissão' },
  { value: 'evaluation',   label: 'Avaliação' },
  { value: 'shortlist',    label: 'Shortlist' },
  { value: 'clarification',label: 'Clarificação' },
  { value: 'bafo',         label: 'BAFO' },
  { value: 'award',        label: 'Adjudicação' },
  { value: 'contracting',  label: 'Contratação' },
  { value: 'handover',     label: 'Handover' },
  { value: 'note',         label: 'Nota' },
];

type EventIconConfig = { icon: React.ElementType; dot: string; card: string; iconColor: string };
const EVENT_CONFIG: Record<string, EventIconConfig> = {
  submission:    { icon: Send,          dot: 'bg-blue-500',   card: 'border-l-blue-400 bg-blue-50/60 dark:bg-blue-950/30',   iconColor: 'text-blue-600' },
  evaluation:    { icon: Eye,           dot: 'bg-violet-500', card: 'border-l-violet-400 bg-violet-50/60 dark:bg-violet-950/30', iconColor: 'text-violet-600' },
  shortlist:     { icon: Star,          dot: 'bg-amber-500',  card: 'border-l-amber-400 bg-amber-50/60 dark:bg-amber-950/30',  iconColor: 'text-amber-600' },
  clarification: { icon: MessageSquare, dot: 'bg-orange-500', card: 'border-l-orange-400 bg-orange-50/60 dark:bg-orange-950/30', iconColor: 'text-orange-600' },
  bafo:          { icon: RefreshCw,     dot: 'bg-red-500',    card: 'border-l-red-400 bg-red-50/60 dark:bg-red-950/30',       iconColor: 'text-red-600' },
  award:         { icon: Trophy,        dot: 'bg-emerald-500',card: 'border-l-emerald-400 bg-emerald-50/60 dark:bg-emerald-950/30', iconColor: 'text-emerald-600' },
  contracting:   { icon: Handshake,     dot: 'bg-teal-500',   card: 'border-l-teal-400 bg-teal-50/60 dark:bg-teal-950/30',   iconColor: 'text-teal-600' },
  handover:      { icon: GitBranch,     dot: 'bg-indigo-500', card: 'border-l-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/30', iconColor: 'text-indigo-600' },
  note:          { icon: FileText,      dot: 'bg-slate-400',  card: 'border-l-slate-300 bg-slate-50/60 dark:bg-slate-900/30', iconColor: 'text-slate-500' },
};

// ── Main component ──────────────────────────────────────────────────────────

export function ProposalEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedProposal, isLoading: proposalLoading, selectProposal, updateSection, updateStatus, autoSaveStatus } =
    useProposalStore();
  const [activeSectionId, setActiveSectionId] = useState<string>('');
  const [editorContent, setEditorContent] = useState('');
  const [isExporting, setIsExporting] = useState<'word' | 'pdf' | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [consortiumMembers, setConsortiumMembers] = useState<string[]>([]);
  const [newMember, setNewMember] = useState('');
  const [logos, setLogos] = useState<{ proponent?: string; client?: string }>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadType, setUploadType] = useState<'proponent' | 'client'>('proponent');
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Right panel tab state (own state to avoid Radix Tabs flex issues)
  const [rightTab, setRightTab] = useState<'pipeline' | 'events'>('pipeline');

  // Pipeline state
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionModal, setTransitionModal] = useState<{
    open: boolean;
    targetStatus: ProposalStatus | null;
    label: string;
  }>({ open: false, targetStatus: null, label: '' });
  const [transitionNote, setTransitionNote] = useState('');
  const [transitionError, setTransitionError] = useState('');

  // Events state
  const [events, setEvents] = useState<ApiProposalEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventSheet, setEventSheet] = useState(false);
  const [newEvent, setNewEvent] = useState({
    event_type: 'note',
    artifact_type: 'none',
    title: '',
    notes: '',
    external_url: '',
  });
  const [eventError, setEventError] = useState('');
  const [eventSaving, setEventSaving] = useState(false);

  useEffect(() => {
    if (id) {
      selectProposal(id);
      loadEvents(id);
    }
  }, [id, selectProposal]);

  useEffect(() => {
    if (selectedProposal) {
      setConsortiumMembers(selectedProposal.consortiumMembers || []);
      setLogos({
        proponent: selectedProposal.proponentLogoUrl || undefined,
        client: selectedProposal.clientLogoUrl || undefined,
      });
      if (selectedProposal.sections.length > 0 && !activeSectionId) {
        setActiveSectionId(selectedProposal.sections[0].id);
      }
    }
  }, [selectedProposal]);

  useEffect(() => {
    if (selectedProposal && activeSectionId) {
      const section = selectedProposal.sections.find((s) => s.id === activeSectionId);
      if (section) setEditorContent(section.content || '');
    }
  }, [selectedProposal, activeSectionId]);

  const loadEvents = async (proposalId: string) => {
    setEventsLoading(true);
    try {
      const data = await apiGetProposalEvents(proposalId);
      setEvents(data);
    } catch {
      // ignore
    } finally {
      setEventsLoading(false);
    }
  };

  const saveSection = useCallback(
    (content: string) => {
      if (selectedProposal && activeSectionId) {
        updateSection(selectedProposal.id, activeSectionId, content);
      }
    },
    [selectedProposal, activeSectionId, updateSection]
  );

  const handleContentChange = (content: string) => {
    setEditorContent(content);
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => saveSection(content), 1500);
  };

  const handleSectionChange = (sectionId: string) => {
    if (activeSectionId && editorContent) saveSection(editorContent);
    setActiveSectionId(sectionId);
  };

  const handleAISuggestion = (generatedContent: string) => {
    setEditorContent(generatedContent);
    handleContentChange(generatedContent);
  };

  const handleExport = async (type: 'word' | 'pdf') => {
    if (!id) return;
    setIsExporting(type);
    try {
      const blob = type === 'word' ? await apiDownloadProposalWord(id) : await apiDownloadProposalPdf(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Proposta_${id}_${selectedProposal?.title?.replace(/\s+/g, '_') || 'document'}.${type === 'word' ? 'docx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao exportar');
    } finally {
      setIsExporting(null);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !id) return;
    try {
      const result = await apiUploadProposalLogo(id, file, uploadType);
      setLogos((prev) => ({ ...prev, [uploadType]: result.url }));
    } catch {
      alert('Erro ao fazer upload do logo');
    }
  };

  const triggerUpload = (type: 'proponent' | 'client') => {
    setUploadType(type);
    fileInputRef.current?.click();
  };

  const handleAddConsortiumMember = () => {
    if (newMember.trim()) {
      setConsortiumMembers((prev) => [...prev, newMember.trim()]);
      setNewMember('');
    }
  };

  const handleRemoveConsortiumMember = (index: number) => {
    setConsortiumMembers((prev) => prev.filter((_, i) => i !== index));
  };

  // Pipeline transition
  const openTransitionModal = (targetStatus: ProposalStatus, label: string) => {
    setTransitionNote('');
    setTransitionError('');
    setTransitionModal({ open: true, targetStatus, label });
  };

  const confirmTransition = async () => {
    if (!id || !transitionModal.targetStatus) return;
    setIsTransitioning(true);
    setTransitionError('');
    try {
      const result = await apiTransitionProposalStatus(id, transitionModal.targetStatus, transitionNote);
      updateStatus(id, result.status as ProposalStatus);
      setTransitionModal({ open: false, targetStatus: null, label: '' });
      if (result.project_id) {
        navigate(`/projects/${result.project_id}`);
        return;
      }
      selectProposal(id);
    } catch (err) {
      setTransitionError(err instanceof Error ? err.message : 'Erro ao transitar estado.');
    } finally {
      setIsTransitioning(false);
    }
  };

  // Create event
  const handleCreateEvent = async () => {
    if (!id || !newEvent.title.trim()) {
      setEventError('O título é obrigatório.');
      return;
    }
    setEventError('');
    setEventSaving(true);
    try {
      const payload = {
        ...newEvent,
        artifact_type: newEvent.artifact_type === 'none' ? '' : newEvent.artifact_type,
      };
      const created = await apiCreateProposalEvent(id, payload);
      setEvents((prev) => [created, ...prev]);
      setEventSheet(false);
      setNewEvent({ event_type: 'note', artifact_type: 'none', title: '', notes: '', external_url: '' });
    } catch (err) {
      setEventError(err instanceof Error ? err.message : 'Erro ao criar evento.');
    } finally {
      setEventSaving(false);
    }
  };

  const activeSection = selectedProposal?.sections.find((s) => s.id === activeSectionId);
  const currentStatus = selectedProposal?.status || 'draft';
  const availableTransitions = PIPELINE_TRANSITIONS[currentStatus] || [];
  const currentStageIndex = STATUS_ORDER[currentStatus] ?? -1;
  const isTerminal = TERMINAL_STAGES.some((t) => t.status === currentStatus);
  const stageContext = STAGE_CONTEXT[currentStatus];

  // Preview HTML
  const previewHtml = selectedProposal
    ? `<div style="font-family: Calibri, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 2px solid #1A365D; padding-bottom: 20px;">
          <div>${logos.proponent ? `<img src="${logos.proponent}" style="max-height: 60px; max-width: 150px;" />` : '<div style="color: #999; font-style: italic; font-size: 12px;">[LOGO EMPRESA PROPONENTE]</div>'}</div>
          <div>${logos.client ? `<img src="${logos.client}" style="max-height: 60px; max-width: 150px;" />` : '<div style="color: #999; font-style: italic; font-size: 12px;">[LOGO CLIENTE]</div>'}</div>
        </div>
        <h1 style="color: #1A365D; font-size: 24px; text-align: center; margin-bottom: 20px;">${selectedProposal.title}</h1>
        ${consortiumMembers.length > 0 ? `<div style="margin: 30px 0; padding: 15px; background: #F7FAFC; border-radius: 8px;"><h3 style="color: #1A365D; margin-bottom: 10px;">Membros do Consórcio</h3><ul style="margin: 0; padding-left: 20px;">${consortiumMembers.map((m) => `<li>${m}</li>`).join('')}</ul></div>` : ''}
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #E2E8F0;" />
        ${selectedProposal.sections.map((s) => `<div style="margin-bottom: 30px;"><h2 style="color: #1A365D; font-size: 18px; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px;">${s.title}</h2><div style="line-height: 1.6; color: #333;">${s.content || '<em style="color: #999;">[Conteúdo em desenvolvimento...]</em>'}</div></div>`).join('')}
        <div style="margin-top: 60px; text-align: center; color: #666; font-size: 10px; border-top: 1px solid #E2E8F0; padding-top: 20px;">Documento gerado automaticamente — ConsultPro ${new Date().getFullYear()}</div>
      </div>`
    : '';

  if (proposalLoading || !selectedProposal) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        {proposalLoading ? (
          <>
            <div className="h-8 w-48 bg-muted rounded animate-pulse" />
            <div className="h-64 w-full max-w-2xl bg-muted rounded animate-pulse" />
          </>
        ) : (
          <>
            <p className="text-muted-foreground">Proposta não encontrada.</p>
            <Button variant="outline" onClick={() => navigate('/proposals')}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Voltar
            </Button>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Hidden file input */}
      <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleLogoUpload} />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/proposals')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-xl font-bold">{selectedProposal.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">v{selectedProposal.version}</Badge>
              <StatusBadge status={currentStatus} size="sm" />
              <Badge
                variant={autoSaveStatus === 'saved' ? 'default' : 'secondary'}
                className="text-xs"
              >
                {autoSaveStatus === 'saving' && 'A guardar...'}
                {autoSaveStatus === 'saved' && 'Guardado'}
                {autoSaveStatus === 'idle' && 'Rascunho'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => setPreviewOpen(true)}>
            <Eye className="h-4 w-4 mr-2" />
            Pré-visualizar
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('word')} disabled={isExporting !== null}>
            <FileType className="h-4 w-4 mr-2" />
            {isExporting === 'word' ? 'A gerar...' : 'Word'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('pdf')} disabled={isExporting !== null}>
            <FileDown className="h-4 w-4 mr-2" />
            {isExporting === 'pdf' ? 'A gerar...' : 'PDF'}
          </Button>
          {currentStatus === 'draft' || currentStatus === 'in_review' ? (
            <Button size="sm" onClick={() => navigate(`/proposals/${id}/qc`)}>
              <CheckSquare className="h-4 w-4 mr-2" />
              Quality Check
            </Button>
          ) : availableTransitions.length > 0 ? (
            <Button
              size="sm"
              onClick={() => openTransitionModal(availableTransitions[0].status, availableTransitions[0].label)}
            >
              <ArrowRight className="h-4 w-4 mr-2" />
              {availableTransitions[0].label}
            </Button>
          ) : null}
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden mt-4">
        {/* Left Sidebar */}
        <div className="w-56 flex-shrink-0 flex flex-col border-r border-border overflow-auto">
          {/* Logos */}
          <div className="p-3 border-b border-border">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-2">
              Logos da Proposta
            </h3>
            <div className="space-y-2">
              {(['proponent', 'client'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => triggerUpload(type)}
                  className="w-full flex items-center gap-2 p-2 rounded-lg border border-dashed border-border hover:bg-muted/60 transition-colors text-left"
                >
                  {logos[type] ? (
                    <img src={logos[type]} alt={type} className="h-7 w-7 object-contain rounded" />
                  ) : type === 'proponent' ? (
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <UserCircle className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="text-xs text-muted-foreground truncate flex-1">
                    {type === 'proponent' ? 'Logo Proponente' : 'Logo Cliente'}
                  </span>
                  <Upload className="h-3 w-3 text-muted-foreground/50 flex-shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Consortium */}
          <div className="p-3 border-b border-border">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-2">
              Consórcio
            </h3>
            <div className="space-y-1">
              {consortiumMembers.map((member, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs bg-muted/50 rounded px-2 py-1">
                  <span className="flex-1 truncate">{member}</span>
                  <Button variant="ghost" size="sm" className="h-4 w-4 p-0 flex-shrink-0" onClick={() => handleRemoveConsortiumMember(idx)}>
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
              <div className="flex gap-1 mt-2">
                <Input
                  value={newMember}
                  onChange={(e) => setNewMember(e.target.value)}
                  placeholder="Nova empresa"
                  className="h-7 text-xs"
                  onKeyDown={(e) => e.key === 'Enter' && handleAddConsortiumMember()}
                />
                <Button size="sm" className="h-7 w-7 p-0 flex-shrink-0" onClick={handleAddConsortiumMember}>
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>

          {/* Sections */}
          <div className="flex-1 p-3">
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-2">
              Secções
            </h3>
            <div className="space-y-0.5">
              {selectedProposal.sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => handleSectionChange(section.id)}
                  className={cn(
                    'w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all',
                    activeSectionId === section.id
                      ? 'bg-primary/10 text-primary font-semibold'
                      : 'hover:bg-muted text-muted-foreground'
                  )}
                >
                  <div className="flex items-center gap-2">
                    {section.isComplete ? (
                      <CheckCircle2 className="h-3 w-3 text-emerald-500 flex-shrink-0" />
                    ) : (
                      <div className="h-3 w-3 rounded-full border border-muted-foreground/40 flex-shrink-0" />
                    )}
                    <span className="truncate">{section.title}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center - Editor */}
        <div className="flex-1 flex flex-col bg-card border-x border-border overflow-hidden min-w-0">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-2 min-w-0">
              <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="font-medium text-sm truncate">{activeSection?.title}</span>
              {activeSection?.isComplete && (
                <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200 flex-shrink-0 dark:bg-emerald-950/30 dark:text-emerald-400">
                  Completo
                </Badge>
              )}
            </div>
            <AIAssistButton
              section={activeSection?.title || ''}
              proposalId={id || ''}
              sectionId={activeSectionId}
              currentContent={editorContent}
              onApply={handleAISuggestion}
            />
          </div>

          <div className="flex-1 overflow-auto p-4">
            <RichTextEditor
              value={editorContent}
              onChange={handleContentChange}
              placeholder={`Escreva o conteúdo para ${activeSection?.title}...`}
              className="h-full"
            />
          </div>

          <div className="flex items-center justify-between px-4 py-2 border-t border-border bg-muted/20 flex-shrink-0">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span>{editorContent.replace(/<[^>]*>/g, '').length} car.</span>
              <span>{editorContent.replace(/<[^>]*>/g, '').split(/\s+/).filter(Boolean).length} pal.</span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="h-7 text-xs" onClick={() => saveSection(editorContent)}>
                <Save className="h-3.5 w-3.5 mr-1.5" />
                Guardar
              </Button>
              <Button size="sm" className="h-7 text-xs" onClick={() => {
                if (activeSection) updateSection(selectedProposal.id, activeSectionId, editorContent);
              }}>
                <CheckCircle className="h-3.5 w-3.5 mr-1.5" />
                Marcar Completo
              </Button>
            </div>
          </div>
        </div>

        {/* ── Right Panel — Pipeline + Events ── */}
        <div className="w-72 flex-shrink-0 flex flex-col border-l border-border overflow-hidden bg-background">

          {/* Tab headers — custom, no Radix Tabs */}
          <div className="flex flex-shrink-0 border-b border-border">
            <button
              className={cn(
                'flex-1 h-10 text-xs font-semibold tracking-wide transition-all border-b-2',
                rightTab === 'pipeline'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('pipeline')}
            >
              Pipeline
            </button>
            <button
              className={cn(
                'flex-1 h-10 text-xs font-semibold tracking-wide transition-all border-b-2 flex items-center justify-center gap-1.5',
                rightTab === 'events'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('events')}
            >
              Eventos
              {events.length > 0 && (
                <span className="bg-primary/15 text-primary rounded-full text-[10px] px-1.5 py-0 leading-5 font-bold">
                  {events.length}
                </span>
              )}
            </button>
          </div>

          {/* ── PIPELINE PANEL ── */}
          {rightTab === 'pipeline' && (
            <div className="flex-1 overflow-auto">

              {/* Current status hero */}
              <div className={cn(
                'p-4 border-b border-border',
                isTerminal && currentStatus === 'won' ? 'bg-gradient-to-br from-emerald-50 to-transparent dark:from-emerald-950/30' :
                isTerminal ? 'bg-gradient-to-br from-red-50 to-transparent dark:from-red-950/30' :
                'bg-gradient-to-br from-primary/5 to-transparent'
              )}>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                  Estado Atual
                </p>
                <div className="flex items-center gap-2.5">
                  <StatusBadge status={currentStatus} />
                  <span className="text-sm font-semibold">{STATUS_LABELS[currentStatus] || currentStatus}</span>
                </div>
                {stageContext && (
                  <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{stageContext.hint}</p>
                )}
              </div>

              {/* COS artifacts for current stage */}
              {stageContext?.artifacts && stageContext.artifacts.length > 0 && (
                <div className="px-4 py-3 border-b border-border bg-muted/20">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                    Artefactos COS desta Fase
                  </p>
                  <div className="space-y-1">
                    {stageContext.artifacts.map((a) => (
                      <div key={a} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <FileCheck className="h-3 w-3 text-muted-foreground/60 flex-shrink-0" />
                        <span>{a}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Available transitions */}
              {availableTransitions.length > 0 && (
                <div className="p-4 border-b border-border space-y-2">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                    Próxima Ação
                  </p>
                  {availableTransitions.map((t, i) => (
                    <button
                      key={t.status}
                      onClick={() => openTransitionModal(t.status, t.label)}
                      className={cn(
                        'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group',
                        i === 0
                          ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm'
                          : 'border border-border hover:border-primary/40 hover:bg-muted text-foreground'
                      )}
                    >
                      <span>{t.label}</span>
                      <ChevronRight className={cn('h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5', i === 0 ? 'opacity-80' : 'text-muted-foreground')} />
                    </button>
                  ))}
                </div>
              )}

              {/* Pipeline stepper */}
              <div className="p-4">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">
                  Pipeline COS
                </p>
                <div className="space-y-0">
                  {(() => {
                    let lastGroup = '';
                    return PIPELINE_STAGES.map((stage, idx) => {
                      const isCurrent = stage.status === currentStatus;
                      const isPast = !isTerminal && currentStageIndex > (STATUS_ORDER[stage.status] ?? 999);
                      const isLast = idx === PIPELINE_STAGES.length - 1;
                      const showGroupLabel = stage.group !== lastGroup;
                      lastGroup = stage.group;
                      return (
                        <div key={stage.status}>
                          {showGroupLabel && (
                            <div className={cn(
                              'text-[10px] font-semibold uppercase tracking-widest mt-3 mb-1.5 pl-7',
                              idx === 0 ? 'mt-0' : '',
                              'text-muted-foreground/60'
                            )}>
                              {stage.group}
                            </div>
                          )}
                          <div className="flex items-start gap-2.5">
                            <div className="flex flex-col items-center flex-shrink-0">
                              <div className={cn(
                                'h-4 w-4 rounded-full border-2 flex items-center justify-center mt-0.5 transition-all',
                                isCurrent
                                  ? 'border-primary bg-primary shadow-[0_0_0_3px] shadow-primary/20'
                                  : isPast
                                    ? 'border-emerald-500 bg-emerald-500'
                                    : 'border-muted-foreground/25 bg-background'
                              )}>
                                {isPast
                                  ? <CheckCircle2 className="h-2.5 w-2.5 text-white" />
                                  : isCurrent
                                    ? <div className="h-1.5 w-1.5 rounded-full bg-white" />
                                    : null}
                              </div>
                              {!isLast && (
                                <div className={cn(
                                  'w-0.5 flex-1 mt-0.5',
                                  isPast ? 'bg-emerald-400/60 h-4' : 'bg-muted-foreground/15 h-4'
                                )} />
                              )}
                            </div>
                            <div className={cn(
                              'pb-3 text-xs leading-none pt-0.5 transition-colors',
                              isCurrent ? 'text-primary font-semibold' :
                              isPast ? 'text-muted-foreground/60' :
                              'text-muted-foreground/40'
                            )}>
                              {stage.label}
                            </div>
                          </div>
                        </div>
                      );
                    });
                  })()}

                  {/* Terminal states */}
                  <div className="mt-3 pt-3 border-t border-border/50 space-y-1">
                    {TERMINAL_STAGES.map((t) => {
                      const isCurrent = t.status === currentStatus;
                      return (
                        <div key={t.status} className="flex items-center gap-2.5">
                          <div className={cn(
                            'h-4 w-4 rounded flex items-center justify-center flex-shrink-0',
                            isCurrent
                              ? t.status === 'won' ? 'bg-emerald-500' : 'bg-red-400'
                              : 'bg-muted-foreground/15'
                          )}>
                            {isCurrent
                              ? t.status === 'won'
                                ? <Flag className="h-2.5 w-2.5 text-white" />
                                : <X className="h-2.5 w-2.5 text-white" />
                              : null}
                          </div>
                          <span className={cn(
                            'text-xs',
                            isCurrent
                              ? t.status === 'won' ? 'text-emerald-600 font-semibold' : 'text-red-500 font-semibold'
                              : 'text-muted-foreground/40'
                          )}>
                            {t.label}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── EVENTS PANEL ── */}
          {rightTab === 'events' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Events header */}
              <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0 bg-muted/20">
                <div>
                  <p className="text-xs font-semibold">Linha do Tempo</p>
                  <p className="text-[10px] text-muted-foreground">
                    {eventsLoading ? 'A carregar...' : `${events.length} evento${events.length !== 1 ? 's' : ''}`}
                  </p>
                </div>
                <Button
                  size="sm"
                  className="h-7 px-3 text-xs gap-1"
                  onClick={() => {
                    setEventError('');
                    setEventSheet(true);
                  }}
                >
                  <Plus className="h-3 w-3" />
                  Novo Evento
                </Button>
              </div>

              {/* Timeline */}
              <div className="flex-1 overflow-auto">
                {eventsLoading && (
                  <div className="p-4 space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-16 bg-muted rounded-lg animate-pulse" />
                    ))}
                  </div>
                )}

                {!eventsLoading && events.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 px-5 text-center">
                    <div className="h-12 w-12 rounded-2xl bg-muted flex items-center justify-center mb-4">
                      <Clock className="h-6 w-6 text-muted-foreground/60" />
                    </div>
                    <p className="text-sm font-medium text-foreground">Sem eventos ainda</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      Registe submissões, clarificações, adjudicações e outros marcos do pipeline.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4 h-8 text-xs"
                      onClick={() => { setEventError(''); setEventSheet(true); }}
                    >
                      <Plus className="h-3 w-3 mr-1.5" />
                      Registar Primeiro Evento
                    </Button>
                  </div>
                )}

                {!eventsLoading && events.length > 0 && (
                  <div className="relative px-4 py-3">
                    {/* Vertical spine */}
                    <div className="absolute left-7 top-3 bottom-3 w-px bg-border" aria-hidden />

                    <div className="space-y-3">
                      {events.map((ev) => {
                        const conf = EVENT_CONFIG[ev.event_type] ?? EVENT_CONFIG.note;
                        const Icon = conf.icon;
                        return (
                          <div key={ev.id} className="flex gap-3">
                            {/* Dot on spine */}
                            <div className={cn('h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 z-10 border-2 border-background', conf.dot)}>
                              <Icon className="h-3.5 w-3.5 text-white" />
                            </div>
                            {/* Card */}
                            <div className={cn('flex-1 rounded-lg border border-l-4 p-2.5 min-w-0', conf.card)}>
                              <div className="flex items-start justify-between gap-1 mb-1">
                                <span className="text-xs font-semibold text-foreground leading-tight truncate">{ev.title}</span>
                                <span className={cn('text-[10px] font-medium rounded px-1.5 py-0.5 flex-shrink-0 capitalize', conf.iconColor)}>
                                  {ev.event_type_display}
                                </span>
                              </div>
                              {ev.notes && (
                                <p className="text-xs text-muted-foreground line-clamp-2 mb-1.5">{ev.notes}</p>
                              )}
                              <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                <Calendar className="h-2.5 w-2.5 flex-shrink-0" />
                                <span>{new Date(ev.occurred_at).toLocaleDateString('pt-PT')}</span>
                                {ev.created_by && (
                                  <span className="ml-auto truncate max-w-[70px]">
                                    {ev.created_by.firstName}
                                  </span>
                                )}
                                <div className="flex items-center gap-1 ml-auto">
                                  {ev.attachment_url && (
                                    <a href={ev.attachment_url} target="_blank" rel="noreferrer" className="hover:text-foreground transition-colors">
                                      <Paperclip className="h-2.5 w-2.5" />
                                    </a>
                                  )}
                                  {ev.external_url && (
                                    <a href={ev.external_url} target="_blank" rel="noreferrer" className="hover:text-foreground transition-colors">
                                      <ExternalLink className="h-2.5 w-2.5" />
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Preview Dialog ── */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Pré-visualização da Proposta</DialogTitle>
          </DialogHeader>
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </DialogContent>
      </Dialog>

      {/* ── Pipeline Transition Modal ── */}
      <Dialog
        open={transitionModal.open}
        onOpenChange={(open) => !open && setTransitionModal({ open: false, targetStatus: null, label: '' })}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              {transitionModal.label}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50 text-sm">
              <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <span className="text-muted-foreground">Novo estado:</span>
              <strong className="ml-1">{transitionModal.targetStatus ? STATUS_LABELS[transitionModal.targetStatus] : ''}</strong>
            </div>
            <Textarea
              placeholder="Nota sobre esta transição (opcional)..."
              value={transitionNote}
              onChange={(e) => setTransitionNote(e.target.value)}
              rows={3}
              className="resize-none"
            />
            {transitionError && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {transitionError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTransitionModal({ open: false, targetStatus: null, label: '' })}>
              Cancelar
            </Button>
            <Button onClick={confirmTransition} disabled={isTransitioning}>
              {isTransitioning ? 'A processar...' : 'Confirmar Transição'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── New Event Sheet (fixes blank page bug with Dialog + Select empty value) ── */}
      <Sheet open={eventSheet} onOpenChange={setEventSheet}>
        <SheetContent side="right" className="w-96 flex flex-col">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              Registar Evento
            </SheetTitle>
          </SheetHeader>

          <div className="flex-1 overflow-auto py-4 space-y-4">
            {/* Event type selector — visual grid */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">
                Tipo de Evento
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                {EVENT_TYPE_OPTIONS.map((opt) => {
                  const conf = EVENT_CONFIG[opt.value] ?? EVENT_CONFIG.note;
                  const Icon = conf.icon;
                  const isSelected = newEvent.event_type === opt.value;
                  return (
                    <button
                      key={opt.value}
                      onClick={() => setNewEvent((p) => ({ ...p, event_type: opt.value }))}
                      className={cn(
                        'flex flex-col items-center gap-1 p-2.5 rounded-lg border text-xs font-medium transition-all',
                        isSelected
                          ? `${conf.card} border-l-4 shadow-sm`
                          : 'border-border hover:bg-muted/60 text-muted-foreground'
                      )}
                    >
                      <Icon className={cn('h-4 w-4', isSelected ? conf.iconColor : '')} />
                      <span className="text-center leading-tight">{opt.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Artifact type */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                Artefacto Associado
              </label>
              <Select
                value={newEvent.artifact_type}
                onValueChange={(v) => setNewEvent((p) => ({ ...p, artifact_type: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Nenhum" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Nenhum</SelectItem>
                  <SelectItem value="final_proposal">Proposta Final</SelectItem>
                  <SelectItem value="contract">Contrato</SelectItem>
                  <SelectItem value="handover">Handover Package</SelectItem>
                  <SelectItem value="kickoff">Kickoff Pack</SelectItem>
                  <SelectItem value="checklist">Checklist de Arranque</SelectItem>
                  <SelectItem value="other">Outro</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Title */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                Título <span className="text-destructive">*</span>
              </label>
              <Input
                value={newEvent.title}
                onChange={(e) => setNewEvent((p) => ({ ...p, title: e.target.value }))}
                placeholder="Ex: Proposta submetida ao PNUD..."
                onKeyDown={(e) => e.key === 'Enter' && handleCreateEvent()}
              />
            </div>

            {/* Notes */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                Notas
              </label>
              <Textarea
                value={newEvent.notes}
                onChange={(e) => setNewEvent((p) => ({ ...p, notes: e.target.value }))}
                placeholder="Detalhes, contexto, decisões importantes..."
                rows={4}
                className="resize-none"
              />
            </div>

            {/* External URL */}
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-1.5">
                Link Externo
              </label>
              <Input
                value={newEvent.external_url}
                onChange={(e) => setNewEvent((p) => ({ ...p, external_url: e.target.value }))}
                placeholder="https://..."
                type="url"
              />
            </div>

            {eventError && (
              <div className="flex items-center gap-2 text-sm text-destructive p-3 bg-destructive/10 rounded-lg">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {eventError}
              </div>
            )}
          </div>

          <SheetFooter className="border-t border-border pt-4">
            <Button variant="outline" onClick={() => setEventSheet(false)} className="flex-1">
              Cancelar
            </Button>
            <Button onClick={handleCreateEvent} disabled={eventSaving} className="flex-1">
              {eventSaving ? 'A registar...' : 'Registar Evento'}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
