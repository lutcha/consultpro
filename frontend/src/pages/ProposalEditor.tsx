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
  AlertCircle, GitBranch, Flag, SlidersHorizontal, BookOpen, Search,
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
import { useProposalStore, useQCStore } from '@/stores';
import {
  apiDownloadProposalWord, apiDownloadProposalPdf, apiUploadProposalLogo,
  apiGetProposalEvents, apiCreateProposalEvent, apiTransitionProposalStatus, apiGetProposalTeamMatch,
  apiGetProposalSectionGap, apiGetQualityChecks, type ApiProposalEvent, type ApiProposalSectionGap,
  apiGetComplianceMatrices, apiGenerateComplianceMatrix, apiUpdateComplianceMatrixRow,
  type ApiProposalTeamMatch, type ApiQualityCheck, type ApiComplianceMatrix,
  type ApiComplianceMatrixRow, apiSearchKnowledge, type ApiKnowledgeSearchResult,
} from '@/lib/api';
import { ExportRequestPanel } from '@/components/proposals/ExportRequestPanel';
import { PostMortemPanel } from '@/components/proposals/PostMortemPanel';
import type { ProposalStatus } from '@/types';
import { cn } from '@/lib/utils';
import { markdownToEditorHtml, shouldNormalizeMarkdown } from '@/lib/contentFormat';
import { readQCSettings, writeQCSettings } from '@/lib/qcSettings';

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

const EVENT_FILTER_OPTIONS = [
  { value: 'all', label: 'Todos' },
  ...EVENT_TYPE_OPTIONS,
];

const EVENT_PERIOD_OPTIONS = [
  { value: 'all', label: 'Todo período' },
  { value: '7', label: '7 dias' },
  { value: '30', label: '30 dias' },
  { value: '90', label: '90 dias' },
];

const CONTEXT_EVENT_BY_STATUS: Record<string, { event_type: string; artifact_type: string; title: string; notes: string }> = {
  submitted: {
    event_type: 'submission',
    artifact_type: 'final_proposal',
    title: 'Proposta submetida',
    notes: 'Registar comprovativo, canal de submissao e referencia do concurso.',
  },
  clarifications_requested: {
    event_type: 'clarification',
    artifact_type: 'other',
    title: 'Pedido de clarificacao recebido',
    notes: 'Registar perguntas do cliente, prazo de resposta e responsavel interno.',
  },
  bafo: {
    event_type: 'bafo',
    artifact_type: 'final_proposal',
    title: 'Pedido de BAFO recebido',
    notes: 'Registar alteracoes esperadas, prazo e impacto no orcamento.',
  },
  awarded: {
    event_type: 'award',
    artifact_type: 'other',
    title: 'Proposta adjudicada',
    notes: 'Registar decisao, proximos passos contratuais e documentos pendentes.',
  },
  contract_negotiation: {
    event_type: 'contracting',
    artifact_type: 'contract',
    title: 'Negociacao contratual',
    notes: 'Registar pontos negociados, riscos e decisoes pendentes.',
  },
  contract_signed: {
    event_type: 'contracting',
    artifact_type: 'contract',
    title: 'Contrato assinado',
    notes: 'Anexar contrato assinado e preparar handover para execucao.',
  },
  project_initiation: {
    event_type: 'handover',
    artifact_type: 'handover',
    title: 'Handover para projeto',
    notes: 'Registar pacote de arranque, equipa responsavel e proximas reunioes.',
  },
};

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

const GAP_STATUS_LABELS: Record<string, string> = {
  covered: 'Coberto',
  partial: 'Parcial',
  missing: 'Em falta',
};

const GAP_STATUS_STYLES: Record<string, string> = {
  covered: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300',
  partial: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300',
  missing: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300',
};

const COMPLIANCE_STATUS_LABELS: Record<ApiComplianceMatrixRow['status'], string> = {
  covered: 'Coberto',
  partial: 'Parcial',
  missing: 'Em falta',
  waived: 'Dispensado',
};

const COMPLIANCE_STATUS_STYLES: Record<ApiComplianceMatrixRow['status'], string> = {
  covered: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300',
  partial: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300',
  missing: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300',
  waived: 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-900/60 dark:text-slate-300',
};

const COMPLIANCE_PRIORITY_LABELS: Record<ApiComplianceMatrixRow['priority'], string> = {
  mandatory: 'Obrigatório',
  desirable: 'Desejável',
  optional: 'Opcional',
};

const escapeHtml = (value: string) =>
  value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

const cleanGapSuggestion = (suggestion: string) =>
  suggestion.replace(/^Integrar na seccao:\s*/i, '').trim();

// ── Main component ──────────────────────────────────────────────────────────

export function ProposalEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { selectedProposal, isLoading: proposalLoading, selectProposal, updateSection, addSection, removeSection, reorderSections, updateStatus, autoSaveStatus } =
    useProposalStore();
  const { qcState, isRunning: qcRunning, runQC } = useQCStore();
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
  const [sectionDialogOpen, setSectionDialogOpen] = useState(false);
  const [newSectionTitle, setNewSectionTitle] = useState('');
  const [newSectionError, setNewSectionError] = useState('');
  const [isAddingSection, setIsAddingSection] = useState(false);
  const [sectionGap, setSectionGap] = useState<ApiProposalSectionGap | null>(null);
  const [sectionGapLoading, setSectionGapLoading] = useState(false);
  const [sectionGapError, setSectionGapError] = useState('');

  // Mobile panel toggles
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobilePipelineOpen, setMobilePipelineOpen] = useState(false);

  // Right panel tab state (own state to avoid Radix Tabs flex issues)
  const [rightTab, setRightTab] = useState<'pipeline' | 'compliance' | 'knowledge' | 'events' | 'export' | 'postmortem'>('pipeline');

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
  const [teamMatch, setTeamMatch] = useState<ApiProposalTeamMatch | null>(null);
  const [teamMatchLoading, setTeamMatchLoading] = useState(false);
  const [teamMatchError, setTeamMatchError] = useState('');
  const [qualityCheck, setQualityCheck] = useState<ApiQualityCheck | null>(null);
  const [qualityCheckLoading, setQualityCheckLoading] = useState(false);
  const [qualityCheckError, setQualityCheckError] = useState('');
  const [complianceMatrix, setComplianceMatrix] = useState<ApiComplianceMatrix | null>(null);
  const [complianceLoading, setComplianceLoading] = useState(false);
  const [complianceError, setComplianceError] = useState('');
  const [complianceUpdatingRowId, setComplianceUpdatingRowId] = useState<number | null>(null);
  const [knowledgeResults, setKnowledgeResults] = useState<ApiKnowledgeSearchResult[]>([]);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [knowledgeError, setKnowledgeError] = useState('');
  const [knowledgeQuery, setKnowledgeQuery] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [eventPeriodFilter, setEventPeriodFilter] = useState('all');
  const [qcMinScore, setQcMinScore] = useState(() => readQCSettings().minScore);

  useEffect(() => {
    if (id) {
      selectProposal(id);
      loadEvents(id);
      loadTeamMatch(id);
      loadQualityCheck(id);
    }
  }, [id, selectProposal]);

  useEffect(() => {
    if (selectedProposal?.opportunityId) {
      loadComplianceMatrix(selectedProposal.opportunityId);
    }
  }, [selectedProposal?.opportunityId]);

  useEffect(() => {
    writeQCSettings({ minScore: qcMinScore });
  }, [qcMinScore]);

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
      if (section) {
        const shouldNormalize = shouldNormalizeMarkdown(section.content);
        const normalizedContent = shouldNormalize
          ? markdownToEditorHtml(section.content)
          : section.content || '';
        setEditorContent(normalizedContent);
        if (shouldNormalize) {
          updateSection(selectedProposal.id, activeSectionId, normalizedContent);
        }
      }
    }
  }, [selectedProposal, activeSectionId, updateSection]);

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

  const loadTeamMatch = async (proposalId: string) => {
    setTeamMatchLoading(true);
    setTeamMatchError('');
    try {
      const data = await apiGetProposalTeamMatch(proposalId);
      setTeamMatch(data);
    } catch (err) {
      setTeamMatchError(err instanceof Error ? err.message : 'Erro ao carregar score da equipa.');
    } finally {
      setTeamMatchLoading(false);
    }
  };

  const loadQualityCheck = async (proposalId: string) => {
    setQualityCheckLoading(true);
    setQualityCheckError('');
    try {
      const data = await apiGetQualityChecks(proposalId);
      setQualityCheck(data.results[0] || null);
    } catch (err) {
      setQualityCheck(null);
      setQualityCheckError(err instanceof Error ? err.message : 'Erro ao carregar QC.');
    } finally {
      setQualityCheckLoading(false);
    }
  };

  const loadComplianceMatrix = async (opportunityId: string | number) => {
    setComplianceLoading(true);
    setComplianceError('');
    try {
      const data = await apiGetComplianceMatrices(opportunityId);
      setComplianceMatrix(data.results[0] || null);
    } catch (err) {
      setComplianceMatrix(null);
      setComplianceError(err instanceof Error ? err.message : 'Erro ao carregar matriz de conformidade.');
    } finally {
      setComplianceLoading(false);
    }
  };

  const generateComplianceMatrix = async () => {
    if (!selectedProposal?.opportunityId) return;
    setComplianceLoading(true);
    setComplianceError('');
    try {
      const matrix = await apiGenerateComplianceMatrix(selectedProposal.opportunityId);
      setComplianceMatrix(matrix);
    } catch (err) {
      setComplianceError(err instanceof Error ? err.message : 'Erro ao gerar matriz de conformidade.');
    } finally {
      setComplianceLoading(false);
    }
  };

  const updateComplianceRow = async (
    row: ApiComplianceMatrixRow,
    data: Partial<Pick<ApiComplianceMatrixRow, 'status' | 'proposal_section' | 'evidence_text' | 'human_override_note'>>
  ) => {
    if (!complianceMatrix) return;
    setComplianceUpdatingRowId(row.id);
    setComplianceError('');
    try {
      const updated = await apiUpdateComplianceMatrixRow(row.id, data);
      const nextRows = complianceMatrix.rows.map((item) => (item.id === updated.id ? updated : item));
      setComplianceMatrix({
        ...complianceMatrix,
        human_override_count: nextRows.filter((item) => item.human_override).length,
        rows: nextRows,
      });
    } catch (err) {
      setComplianceError(err instanceof Error ? err.message : 'Erro ao atualizar requisito.');
    } finally {
      setComplianceUpdatingRowId(null);
    }
  };

  const buildKnowledgeQuery = useCallback(() => {
    const sectionTitle = selectedProposal?.sections.find((section) => section.id === activeSectionId)?.title || '';
    const proposalTitle = selectedProposal?.title || '';
    const plainContent = editorContent.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    return [sectionTitle, proposalTitle, plainContent.split(' ').slice(0, 12).join(' ')]
      .filter(Boolean)
      .join(' ')
      .trim();
  }, [activeSectionId, editorContent, selectedProposal]);

  const loadKnowledgeSuggestions = useCallback(async () => {
    const query = buildKnowledgeQuery();
    setKnowledgeQuery(query);
    setKnowledgeError('');
    if (!query) {
      setKnowledgeResults([]);
      return;
    }
    setKnowledgeLoading(true);
    try {
      const data = await apiSearchKnowledge({ q: query, limit: 6 });
      setKnowledgeResults(data.results || []);
    } catch (err) {
      setKnowledgeResults([]);
      setKnowledgeError(err instanceof Error ? err.message : 'Erro ao carregar sugestoes de conhecimento.');
    } finally {
      setKnowledgeLoading(false);
    }
  }, [buildKnowledgeQuery]);

  useEffect(() => {
    if (rightTab !== 'knowledge') return;
    loadKnowledgeSuggestions();
  }, [rightTab, activeSectionId, loadKnowledgeSuggestions]);

  const refreshQualityCheck = async () => {
    if (!id) return;
    setQualityCheckError('');
    try {
      if (activeSectionId) {
        await updateSection(id, activeSectionId, editorContent);
      }
      await runQC(id);
      await loadQualityCheck(id);
    } catch (err) {
      setQualityCheckError(err instanceof Error ? err.message : 'Erro ao atualizar QC.');
    }
  };

  const loadSectionGap = useCallback(async (proposalId: string, sectionId: string) => {
    setSectionGapLoading(true);
    setSectionGap(null);
    setSectionGapError('');
    try {
      const data = await apiGetProposalSectionGap(proposalId, sectionId);
      setSectionGap(data);
    } catch (err) {
      setSectionGap(null);
      setSectionGapError(err instanceof Error ? err.message : 'Erro ao analisar lacunas.');
    } finally {
      setSectionGapLoading(false);
    }
  }, []);

  useEffect(() => {
    if (id && activeSectionId) {
      loadSectionGap(id, activeSectionId);
    }
  }, [id, activeSectionId, loadSectionGap]);

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

  const handleAddSection = async () => {
    if (!selectedProposal) return;
    const title = newSectionTitle.trim();
    if (!title) {
      setNewSectionError('O titulo da seccao e obrigatorio.');
      return;
    }
    setNewSectionError('');
    setIsAddingSection(true);
    try {
      const sectionId = await addSection(selectedProposal.id, title);
      setActiveSectionId(sectionId);
      setEditorContent('');
      setNewSectionTitle('');
      setSectionDialogOpen(false);
    } catch (err) {
      setNewSectionError(err instanceof Error ? err.message : 'Erro ao criar seccao.');
    } finally {
      setIsAddingSection(false);
    }
  };

  const handleAISuggestion = (generatedContent: string) => {
    const normalizedContent = markdownToEditorHtml(generatedContent);
    setEditorContent(normalizedContent);
    handleContentChange(normalizedContent);
  };

  const applyGapSuggestion = (suggestion: string) => {
    const cleaned = cleanGapSuggestion(suggestion);
    if (!cleaned) return;
    const block = `<p><strong>Melhoria sugerida:</strong> ${escapeHtml(cleaned)}</p>`;
    const nextContent = editorContent.trim() ? `${editorContent}${block}` : block;
    setEditorContent(nextContent);
    saveSection(nextContent);
  };

  const formatTransitionError = (raw: string) => {
    const lowered = raw.toLowerCase();
    if (
      lowered.includes('qc ainda') ||
      lowered.includes('score') ||
      lowered.includes('limiar') ||
      lowered.includes('secoes incompletas') ||
      lowered.includes('secoes em falta')
    ) {
      return raw;
    }
    if (lowered.includes('completed passing qc') || lowered.includes('qc')) {
      return `A proposta precisa de QC completo com score minimo de ${qcMinScore}/100.`;
    }
    if (lowered.includes('obrigat') || lowered.includes('required section')) {
      return 'Existem secoes obrigatorias em falta ou incompletas.';
    }
    if (lowered.includes('invalid') || lowered.includes('invalida')) {
      return 'Transicao invalida para o estado selecionado.';
    }
    return raw;
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
      const result = await apiTransitionProposalStatus(
        id,
        transitionModal.targetStatus,
        transitionNote,
        { qc_min_score: qcMinScore }
      );
      updateStatus(id, result.status as ProposalStatus);
      setTransitionModal({ open: false, targetStatus: null, label: '' });
      if (result.project_id) {
        navigate(`/projects/${result.project_id}`);
        return;
      }
      selectProposal(id);
    } catch (err) {
      const raw = err instanceof Error ? err.message : 'Erro ao transitar estado.';
      setTransitionError(formatTransitionError(raw));
    } finally {
      setIsTransitioning(false);
    }
  };

  const moveSection = async (sectionId: string, direction: 'up' | 'down') => {
    if (!selectedProposal) return;
    const ordered = [...selectedProposal.sections].sort((a, b) => a.order - b.order);
    const idx = ordered.findIndex((section) => section.id === sectionId);
    const target = direction === 'up' ? idx - 1 : idx + 1;
    if (idx < 0 || target < 0 || target >= ordered.length) return;
    [ordered[idx], ordered[target]] = [ordered[target], ordered[idx]];
    await reorderSections(selectedProposal.id, ordered.map((section) => section.id));
  };

  const deleteCustomSection = async (sectionId: string) => {
    if (!selectedProposal) return;
    await removeSection(selectedProposal.id, sectionId);
    if (activeSectionId === sectionId) {
      const remaining = selectedProposal.sections.filter((section) => section.id !== sectionId);
      setActiveSectionId(remaining[0]?.id || '');
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

  const openEventSheet = (preset?: Partial<typeof newEvent>) => {
    setEventError('');
    setNewEvent((prev) => ({
      ...prev,
      ...preset,
      artifact_type: preset?.artifact_type || prev.artifact_type || 'none',
    }));
    setEventSheet(true);
  };

  const activeSection = selectedProposal?.sections.find((s) => s.id === activeSectionId);
  const currentStatus = selectedProposal?.status || 'draft';
  const liveQCState = qcState?.proposalId === id ? qcState : null;
  const qcScore = liveQCState?.overallScore ?? qualityCheck?.overall_score ?? 0;
  const qcStatus = liveQCState?.status ?? qualityCheck?.status ?? 'pending';
  const qcMeetsThreshold = qcStatus === 'completed' && qcScore >= qcMinScore;
  const hasPendingTeamValidation = Boolean(
    teamMatch && (teamMatch.team_size === 0 || teamMatch.scored_members < teamMatch.team_size)
  );
  const availableTransitions = PIPELINE_TRANSITIONS[currentStatus] || [];
  const currentStageIndex = STATUS_ORDER[currentStatus] ?? -1;
  const isTerminal = TERMINAL_STAGES.some((t) => t.status === currentStatus);
  const stageContext = STAGE_CONTEXT[currentStatus];
  const contextEvent = CONTEXT_EVENT_BY_STATUS[currentStatus];
  const filteredEvents = events.filter((ev) => {
    if (eventTypeFilter !== 'all' && ev.event_type !== eventTypeFilter) return false;
    if (eventPeriodFilter === 'all') return true;
    const days = Number(eventPeriodFilter);
    const since = Date.now() - days * 24 * 60 * 60 * 1000;
    return new Date(ev.occurred_at).getTime() >= since;
  });
  const complianceRows = complianceMatrix?.rows || [];
  const mandatoryComplianceRows = complianceRows.filter((row) => row.priority === 'mandatory');
  const coveredComplianceRows = complianceRows.filter((row) => row.status === 'covered' || row.status === 'waived');
  const complianceCoverage = complianceRows.length > 0
    ? Math.round((coveredComplianceRows.length / complianceRows.length) * 100)
    : 0;
  const mandatoryOpenCount = mandatoryComplianceRows.filter(
    (row) => row.status === 'missing' || row.status === 'partial'
  ).length;

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
    <div className="flex flex-col md:h-[calc(100vh-8rem)]">
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

      {/* Mobile toolbar — sections + pipeline quick access */}
      <div className="flex md:hidden gap-2 flex-shrink-0 py-2 border-b border-border">
        <Button variant="outline" size="sm" className="flex-1" onClick={() => setMobileSidebarOpen(true)}>
          <FileText className="h-4 w-4 mr-2" />
          Secções
        </Button>
        <Button variant="outline" size="sm" className="flex-1" onClick={() => setMobilePipelineOpen(true)}>
          <Flag className="h-4 w-4 mr-2" />
          Pipeline
        </Button>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden mt-4 min-h-0">
        {/* Left Sidebar — hidden on mobile, permanent on md+ */}
        <div className="hidden md:flex w-56 flex-shrink-0 flex-col border-r border-border overflow-auto">
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
            <Button
              variant="outline"
              size="sm"
              className="mb-2 h-7 w-full justify-start gap-1.5 text-xs"
              onClick={() => {
                setNewSectionError('');
                setSectionDialogOpen(true);
              }}
            >
              <Plus className="h-3.5 w-3.5" />
              Adicionar secção
            </Button>
            <div className="space-y-0.5">
              {selectedProposal.sections.map((section) => (
                <div key={section.id} className="group flex items-center gap-1">
                  <button
                    onClick={() => handleSectionChange(section.id)}
                    className={cn(
                      'flex-1 text-left px-2.5 py-2 rounded-lg text-xs transition-all',
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
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100" onClick={() => moveSection(section.id, 'up')}>
                    <ArrowLeft className="h-3 w-3 rotate-90" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100" onClick={() => moveSection(section.id, 'down')}>
                    <ArrowRight className="h-3 w-3 rotate-90" />
                  </Button>
                  {section.type === 'custom' && (
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0 text-destructive opacity-0 group-hover:opacity-100" onClick={() => deleteCustomSection(section.id)}>
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
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
            <div className="flex items-center gap-2 flex-shrink-0">
              <Button
                variant="outline"
                size="sm"
                className="h-8 text-xs"
                disabled={!id || !activeSectionId || sectionGapLoading}
                onClick={() => id && activeSectionId && loadSectionGap(id, activeSectionId)}
              >
                <RefreshCw className={cn('h-3.5 w-3.5 mr-1.5', sectionGapLoading && 'animate-spin')} />
                Gap {sectionGap ? `${sectionGap.score}%` : ''}
              </Button>
              <AIAssistButton
                section={activeSection?.title || ''}
                proposalId={id || ''}
                sectionId={activeSectionId}
                currentContent={editorContent}
                onApply={handleAISuggestion}
              />
            </div>
          </div>

          <div className="flex-1 overflow-auto p-4">
            {(sectionGap || sectionGapLoading || sectionGapError) && (
              <div className="mb-4 rounded-lg border border-border bg-muted/20 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4 text-primary" />
                      <h3 className="text-sm font-semibold">Gap analysis da secção</h3>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Cobertura dos requisitos da oportunidade e contexto COS.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {sectionGapLoading ? (
                      <Badge variant="outline">A analisar...</Badge>
                    ) : sectionGap ? (
                      <>
                        <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                          {sectionGap.score}/100
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {sectionGap.covered_count}/{sectionGap.total_count} cobertos
                        </span>
                      </>
                    ) : null}
                  </div>
                </div>

                {sectionGapError && (
                  <div className="flex items-center gap-2 text-xs text-destructive">
                    <AlertCircle className="h-3.5 w-3.5" />
                    {sectionGapError}
                  </div>
                )}

                {sectionGap && sectionGap.total_count === 0 && (
                  <p className="text-xs text-muted-foreground">
                    Ainda não há requisitos estruturados para avaliar esta secção.
                  </p>
                )}

                {sectionGap && sectionGap.total_count > 0 && (
                  <div className="grid gap-3 xl:grid-cols-[1fr_0.8fr]">
                    <div className="space-y-2 max-h-44 overflow-auto pr-1">
                      {sectionGap.items.slice(0, 6).map((item, idx) => {
                        const Icon = item.status === 'covered' ? CheckCircle2 : item.status === 'partial' ? Clock : AlertCircle;
                        return (
                          <div key={`${item.source}-${idx}`} className="rounded-md border border-border bg-background px-3 py-2">
                            <div className="flex items-start gap-2">
                              <Icon className={cn(
                                'h-4 w-4 mt-0.5 flex-shrink-0',
                                item.status === 'covered' && 'text-emerald-600',
                                item.status === 'partial' && 'text-amber-600',
                                item.status === 'missing' && 'text-red-600'
                              )} />
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-1.5">
                                  <Badge variant="outline" className={cn('text-[10px]', GAP_STATUS_STYLES[item.status])}>
                                    {GAP_STATUS_LABELS[item.status]}
                                  </Badge>
                                  <span className="text-[10px] text-muted-foreground truncate">{item.source}</span>
                                </div>
                                <p className="text-xs leading-snug mt-1">{item.label}</p>
                                {item.evidence && (
                                  <p className="text-[10px] text-muted-foreground mt-1">Evidência: {item.evidence}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div className="rounded-md border border-border bg-background px-3 py-2">
                      <h4 className="text-xs font-semibold mb-2">Próximas melhorias</h4>
                      {sectionGap.suggestions.length > 0 ? (
                        <ul className="space-y-1.5">
                          {sectionGap.suggestions.slice(0, 4).map((suggestion) => (
                            <li key={suggestion} className="rounded border border-border bg-muted/20 p-2">
                              <p className="text-xs text-muted-foreground leading-snug">
                                {suggestion}
                              </p>
                              <Button
                                variant="outline"
                                size="sm"
                                className="mt-2 h-7 text-[10px]"
                                onClick={() => applyGapSuggestion(suggestion)}
                              >
                                <Plus className="h-3 w-3 mr-1" />
                                Aplicar melhoria
                              </Button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          Esta secção cobre os pontos avaliados.
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
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

        {/* ── Right Panel — Pipeline + Events — hidden on mobile, permanent on lg+ ── */}
        <div className="hidden lg:flex w-80 xl:w-96 flex-shrink-0 flex-col border-l border-border overflow-hidden bg-background">

          {/* Tab headers — custom, no Radix Tabs */}
          <div className="flex flex-shrink-0 overflow-x-auto border-b border-border scrollbar-none">
            <button
              className={cn(
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2',
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
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2 flex items-center gap-1.5',
                rightTab === 'compliance'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('compliance')}
            >
              Compliance
              {mandatoryOpenCount > 0 && (
                <span className="bg-amber-100 text-amber-700 rounded-full text-[10px] px-1.5 py-0 leading-5 font-bold">
                  {mandatoryOpenCount}
                </span>
              )}
            </button>
            <button
              className={cn(
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2 flex items-center gap-1.5',
                rightTab === 'knowledge'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('knowledge')}
            >
              Sugestões
              {knowledgeResults.length > 0 && (
                <span className="bg-primary/15 text-primary rounded-full text-[10px] px-1.5 py-0 leading-5 font-bold">
                  {knowledgeResults.length}
                </span>
              )}
            </button>
            <button
              className={cn(
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2 flex items-center gap-1.5',
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
            <button
              className={cn(
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2',
                rightTab === 'export'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('export')}
            >
              Export
            </button>
            <button
              className={cn(
                'flex-none h-10 px-3 text-xs font-semibold tracking-wide whitespace-nowrap transition-all border-b-2',
                rightTab === 'postmortem'
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              )}
              onClick={() => setRightTab('postmortem')}
            >
              Post-Mortem
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

              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Quality Check
                    </p>
                    <Badge
                      variant="outline"
                      className={cn(
                        'text-[10px]',
                        qcMeetsThreshold
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      )}
                    >
                      {qcStatus === 'completed' ? 'Completo' : qcStatus === 'running' ? 'Em curso' : 'Pendente'}
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-[10px]"
                    onClick={refreshQualityCheck}
                    disabled={qcRunning || qualityCheckLoading}
                  >
                    <RefreshCw className={cn('h-3 w-3 mr-1', (qcRunning || qualityCheckLoading) && 'animate-spin')} />
                    Atualizar QC
                  </Button>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Score QC</span>
                    <span className="font-semibold">{qcScore}/100</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className={cn('h-full rounded-full', qcMeetsThreshold ? 'bg-emerald-500' : 'bg-amber-500')}
                      style={{ width: `${Math.max(0, Math.min(100, qcScore))}%` }}
                    />
                  </div>
                  {qualityCheckError && (
                    <p className="text-xs text-destructive">{qualityCheckError}</p>
                  )}
                  {!qualityCheckError && !qualityCheck && !liveQCState && (
                    <p className="text-[10px] text-muted-foreground leading-relaxed">
                      QC ainda nao executado. Clique em Atualizar QC para calcular a pontuacao a partir das secoes atuais.
                    </p>
                  )}
                  {!qualityCheckError && qcStatus === 'completed' && !qcMeetsThreshold && (
                    <p className="text-[10px] text-amber-700 leading-relaxed">
                      Score abaixo do limiar configurado de {qcMinScore}/100.
                    </p>
                  )}
                </div>
              </div>

              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Match da Equipa
                    </p>
                    <Badge variant="outline" className="text-[10px]">
                      Informativo
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-[10px]"
                    onClick={() => id && loadTeamMatch(id)}
                    disabled={teamMatchLoading}
                  >
                    Atualizar
                  </Button>
                </div>
                {teamMatchLoading && (
                  <p className="text-xs text-muted-foreground">A calcular score...</p>
                )}
                {!teamMatchLoading && teamMatchError && (
                  <p className="text-xs text-destructive">{teamMatchError}</p>
                )}
                {!teamMatchLoading && !teamMatchError && teamMatch && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Score global</span>
                      <span className="font-semibold">{teamMatch.team_score}/100</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Membros com CV analisado</span>
                      <span className="font-semibold">{teamMatch.scored_members}/{teamMatch.team_size}</span>
                    </div>
                    {hasPendingTeamValidation && (
                      <p className="rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-[10px] leading-relaxed text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                        A equipa ainda pode estar em negociacao. Este score orienta perfis e CVs, mas nao bloqueia o QC nesta fase.
                      </p>
                    )}
                    <div className="space-y-1.5 pt-1">
                      {teamMatch.items.slice(0, 3).map((item) => (
                        <div key={item.member_id} className="rounded border border-border p-2">
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-xs font-medium truncate">{item.name}</p>
                            <Badge variant={item.has_analyzed_cv ? 'outline' : 'destructive'} className="text-[10px]">
                              {item.has_analyzed_cv ? `${item.overall_score ?? 0}` : 'Sem CV'}
                            </Badge>
                          </div>
                          {item.missing_skills && item.missing_skills.length > 0 && (
                            <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                              Falhas: {item.missing_skills.slice(0, 4).join(', ')}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="p-4 border-b border-border bg-muted/20">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Limiar QC
                    </p>
                  </div>
                  <Badge variant="outline" className="text-[10px]">
                    {qcMinScore}/100
                  </Badge>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={qcMinScore}
                  onChange={(event) => setQcMinScore(Number(event.target.value))}
                  className="w-full accent-primary"
                />
                <div className="grid grid-cols-3 gap-1.5 mt-2">
                  {[50, 70, 85].map((score) => (
                    <Button
                      key={score}
                      variant={qcMinScore === score ? 'default' : 'outline'}
                      size="sm"
                      className="h-7 text-[10px]"
                      onClick={() => setQcMinScore(score)}
                    >
                      {score === 50 ? 'Teste' : score === 70 ? 'Piloto' : 'Padrão'}
                    </Button>
                  ))}
                </div>
                <p className="text-[10px] text-muted-foreground mt-2 leading-relaxed">
                  Para testes, baixa o limiar. A proposta só precisa de QC completo com score igual ou superior.
                </p>
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

              {contextEvent && (
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">
                    Ações Contextuais
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-full justify-start text-xs"
                    onClick={() => {
                      setRightTab('events');
                      openEventSheet(contextEvent);
                    }}
                  >
                    <Plus className="h-3.5 w-3.5 mr-1.5" />
                    Registar marco desta fase
                  </Button>
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
          {rightTab === 'compliance' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between gap-3 flex-shrink-0 bg-muted/20">
                <div className="min-w-0">
                  <p className="text-xs font-semibold">Matriz de Conformidade</p>
                  <p className="text-[10px] text-muted-foreground">
                    {complianceLoading
                      ? 'A carregar...'
                      : complianceMatrix
                        ? `${coveredComplianceRows.length}/${complianceRows.length} requisitos cobertos`
                        : 'Ainda sem matriz gerada'}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={complianceMatrix ? 'outline' : 'default'}
                  className="h-7 px-3 text-xs gap-1 flex-shrink-0"
                  onClick={generateComplianceMatrix}
                  disabled={complianceLoading || !selectedProposal?.opportunityId}
                >
                  <RefreshCw className={cn('h-3 w-3', complianceLoading && 'animate-spin')} />
                  {complianceMatrix ? 'Regenerar' : 'Gerar'}
                </Button>
              </div>

              {complianceMatrix && (
                <div className="px-4 py-3 border-b border-border">
                  <div className="flex items-center justify-between text-xs mb-2">
                    <span className="text-muted-foreground">Cobertura geral</span>
                    <span className="font-semibold">{complianceCoverage}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div
                      className={cn('h-full rounded-full', mandatoryOpenCount > 0 ? 'bg-amber-500' : 'bg-emerald-500')}
                      style={{ width: `${Math.max(0, Math.min(100, complianceCoverage))}%` }}
                    />
                  </div>
                  <div className="mt-2 flex flex-wrap items-center gap-1.5">
                    <Badge variant="outline" className="text-[10px]">
                      {complianceMatrix.generation_version}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {Number(complianceMatrix.confidence_score || 0).toFixed(2)} confiança
                    </Badge>
                    {complianceMatrix.human_override_count > 0 && (
                      <Badge variant="outline" className="text-[10px]">
                        {complianceMatrix.human_override_count} overrides
                      </Badge>
                    )}
                  </div>
                  {mandatoryOpenCount > 0 && (
                    <p className="mt-2 rounded border border-amber-200 bg-amber-50 px-2 py-1.5 text-[10px] leading-relaxed text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                      Existem {mandatoryOpenCount} requisitos obrigatórios ainda em falta/parciais. Isto orienta a proposta, mas não altera os gates de QC.
                    </p>
                  )}
                </div>
              )}

              {complianceError && (
                <div className="mx-4 mt-3 flex items-start gap-2 rounded border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{complianceError}</span>
                </div>
              )}

              <div className="flex-1 overflow-auto">
                {complianceLoading && !complianceMatrix && (
                  <div className="p-4 space-y-3">
                    {[1, 2, 3].map((item) => (
                      <div key={item} className="h-24 bg-muted rounded-lg animate-pulse" />
                    ))}
                  </div>
                )}

                {!complianceLoading && !complianceMatrix && (
                  <div className="flex flex-col items-center justify-center py-12 px-5 text-center">
                    <div className="h-12 w-12 rounded-2xl bg-muted flex items-center justify-center mb-4">
                      <FileCheck className="h-6 w-6 text-muted-foreground/60" />
                    </div>
                    <p className="text-sm font-medium text-foreground">Sem matriz ainda</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      Gere uma matriz a partir dos requisitos estruturados da oportunidade e depois ligue cada requisito às secções da proposta.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4 h-8 text-xs"
                      onClick={generateComplianceMatrix}
                      disabled={!selectedProposal?.opportunityId}
                    >
                      <FileCheck className="h-3.5 w-3.5 mr-1.5" />
                      Gerar Matriz
                    </Button>
                  </div>
                )}

                {complianceMatrix && complianceRows.length === 0 && (
                  <div className="px-5 py-10 text-center">
                    <p className="text-sm font-medium text-foreground">Sem requisitos estruturados</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      A oportunidade ainda não tem requisitos extraídos para montar a matriz.
                    </p>
                  </div>
                )}

                {complianceMatrix && complianceRows.length > 0 && (
                  <div className="p-4 space-y-3">
                    {complianceRows.map((row) => {
                      const isUpdating = complianceUpdatingRowId === row.id;
                      const linkedToActiveSection = row.proposal_section === Number(activeSectionId);
                      return (
                        <div key={row.id} className="rounded-lg border border-border bg-background p-3 shadow-sm">
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                                <Badge variant="outline" className={cn('text-[10px]', COMPLIANCE_STATUS_STYLES[row.status])}>
                                  {COMPLIANCE_STATUS_LABELS[row.status]}
                                </Badge>
                                <Badge variant="outline" className="text-[10px]">
                                  {COMPLIANCE_PRIORITY_LABELS[row.priority]}
                                </Badge>
                              </div>
                              <p className="text-xs font-medium leading-snug">{row.requirement_text}</p>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Select
                              value={row.status}
                              onValueChange={(value) =>
                                updateComplianceRow(row, {
                                  status: value as ApiComplianceMatrixRow['status'],
                                  human_override_note: 'Atualizado no editor da proposta.',
                                })
                              }
                              disabled={isUpdating}
                            >
                              <SelectTrigger className="h-8 text-xs">
                                <SelectValue placeholder="Estado" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="missing">Em falta</SelectItem>
                                <SelectItem value="partial">Parcial</SelectItem>
                                <SelectItem value="covered">Coberto</SelectItem>
                                <SelectItem value="waived">Dispensado</SelectItem>
                              </SelectContent>
                            </Select>

                            <div className="rounded border border-border bg-muted/20 px-2 py-1.5">
                              <p className="text-[10px] text-muted-foreground">
                                Secção ligada:{' '}
                                <span className="font-medium text-foreground">
                                  {row.proposal_section_title || 'Nenhuma'}
                                </span>
                              </p>
                              {row.evidence_text && (
                                <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                                  Evidência: {row.evidence_text}
                                </p>
                              )}
                            </div>

                            <Button
                              variant={linkedToActiveSection ? 'default' : 'outline'}
                              size="sm"
                              className="h-8 w-full justify-start text-xs"
                              disabled={!activeSectionId || isUpdating}
                              onClick={() =>
                                updateComplianceRow(row, {
                                  proposal_section: Number(activeSectionId),
                                  status: row.status === 'missing' ? 'partial' : row.status,
                                  evidence_text: activeSection?.title
                                    ? `Ligado à secção "${activeSection.title}".`
                                    : row.evidence_text,
                                  human_override_note: 'Ligado manualmente à secção ativa no editor.',
                                })
                              }
                            >
                              <Paperclip className="h-3.5 w-3.5 mr-1.5" />
                              {linkedToActiveSection ? 'Ligado à secção ativa' : 'Ligar à secção ativa'}
                            </Button>

                            <div className="flex flex-wrap gap-1.5 text-[10px] text-muted-foreground">
                              <span>{row.requirement_category}</span>
                              {row.source_reference && <span>• {row.source_reference}</span>}
                              {row.human_override && <span>• override humano</span>}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {rightTab === 'knowledge' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between gap-3 flex-shrink-0 bg-muted/20">
                <div className="min-w-0">
                  <p className="text-xs font-semibold">Smart Suggestions</p>
                  <p className="text-[10px] text-muted-foreground">
                    {knowledgeLoading
                      ? 'A pesquisar conhecimento...'
                      : `${knowledgeResults.length} referencia${knowledgeResults.length !== 1 ? 's' : ''} encontrada${knowledgeResults.length !== 1 ? 's' : ''}`}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-3 text-xs gap-1 flex-shrink-0"
                  onClick={loadKnowledgeSuggestions}
                  disabled={knowledgeLoading}
                >
                  <RefreshCw className={cn('h-3 w-3', knowledgeLoading && 'animate-spin')} />
                  Atualizar
                </Button>
              </div>

              <div className="px-4 py-3 border-b border-border">
                <div className="flex items-start gap-2 rounded border border-border bg-background p-2.5">
                  <Search className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Consulta contextual
                    </p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-3">
                      {knowledgeQuery || 'Abra uma seccao para pesquisar propostas, projetos, CVs e casos indexados.'}
                    </p>
                  </div>
                </div>
                <p className="mt-2 text-[10px] text-muted-foreground leading-relaxed">
                  Painel informativo. Estas sugestoes nao alteram QC, Compliance Matrix, Issue Tree ou o conteudo da proposta.
                </p>
              </div>

              {knowledgeError && (
                <div className="mx-4 mt-3 flex items-start gap-2 rounded border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{knowledgeError}</span>
                </div>
              )}

              <div className="flex-1 overflow-auto">
                {knowledgeLoading && knowledgeResults.length === 0 && (
                  <div className="p-4 space-y-3">
                    {[1, 2, 3].map((item) => (
                      <div key={item} className="h-24 bg-muted rounded-lg animate-pulse" />
                    ))}
                  </div>
                )}

                {!knowledgeLoading && !knowledgeError && knowledgeResults.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 px-5 text-center">
                    <div className="h-12 w-12 rounded-2xl bg-muted flex items-center justify-center mb-4">
                      <BookOpen className="h-6 w-6 text-muted-foreground/60" />
                    </div>
                    <p className="text-sm font-medium text-foreground">Sem sugestoes ainda</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      Indexe ativos de conhecimento ou ajuste a secao ativa para encontrar referencias relevantes.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4 h-8 text-xs"
                      onClick={loadKnowledgeSuggestions}
                    >
                      <Search className="h-3.5 w-3.5 mr-1.5" />
                      Pesquisar novamente
                    </Button>
                  </div>
                )}

                {knowledgeResults.length > 0 && (
                  <div className="p-4 space-y-3">
                    {knowledgeResults.map((result) => {
                      const asset = result.asset;
                      const trace = result.reasoning_trace || [];
                      return (
                        <div key={asset.id} className="rounded-lg border border-border bg-background p-3 shadow-sm">
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                                <Badge variant="outline" className="text-[10px]">
                                  {asset.asset_type.replace(/_/g, ' ')}
                                </Badge>
                                <Badge variant="outline" className="text-[10px]">
                                  {Math.round(result.score)} pts
                                </Badge>
                              </div>
                              <p className="text-xs font-semibold leading-snug">{asset.title}</p>
                            </div>
                          </div>

                          {(asset.summary || asset.content) && (
                            <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                              {asset.summary || asset.content.replace(/<[^>]*>/g, ' ')}
                            </p>
                          )}

                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {asset.country && (
                              <Badge variant="outline" className="text-[10px]">
                                {asset.country}
                              </Badge>
                            )}
                            {asset.sector && (
                              <Badge variant="outline" className="text-[10px]">
                                {asset.sector}
                              </Badge>
                            )}
                            {asset.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="outline" className="text-[10px]">
                                {tag}
                              </Badge>
                            ))}
                          </div>

                          {trace.length > 0 && (
                            <div className="mt-2 rounded border border-border bg-muted/20 px-2 py-1.5">
                              <p className="text-[10px] text-muted-foreground line-clamp-2">
                                Motivos: {trace.slice(0, 4).join(', ')}
                              </p>
                            </div>
                          )}

                          {asset.source_url && (
                            <a
                              href={asset.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-flex items-center gap-1 text-[10px] text-primary hover:underline"
                            >
                              <ExternalLink className="h-3 w-3" />
                              Abrir origem
                            </a>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {rightTab === 'events' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Events header */}
              <div className="px-4 py-3 border-b border-border flex items-center justify-between flex-shrink-0 bg-muted/20">
                <div>
                  <p className="text-xs font-semibold">Linha do Tempo</p>
                  <p className="text-[10px] text-muted-foreground">
                    {eventsLoading ? 'A carregar...' : `${filteredEvents.length} de ${events.length} evento${events.length !== 1 ? 's' : ''}`}
                  </p>
                </div>
                <Button
                  size="sm"
                  className="h-7 px-3 text-xs gap-1"
                  onClick={() => openEventSheet({ event_type: 'note', artifact_type: 'none', title: '', notes: '', external_url: '' })}
                >
                  <Plus className="h-3 w-3" />
                  Novo Evento
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2 border-b border-border px-4 py-3">
                <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue placeholder="Tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {EVENT_FILTER_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={eventPeriodFilter} onValueChange={setEventPeriodFilter}>
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue placeholder="Período" />
                  </SelectTrigger>
                  <SelectContent>
                    {EVENT_PERIOD_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                      onClick={() => openEventSheet({ event_type: 'note', artifact_type: 'none', title: '', notes: '', external_url: '' })}
                    >
                      <Plus className="h-3 w-3 mr-1.5" />
                      Registar Primeiro Evento
                    </Button>
                  </div>
                )}

                {!eventsLoading && events.length > 0 && filteredEvents.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-10 px-5 text-center">
                    <p className="text-sm font-medium text-foreground">Sem eventos neste filtro</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      Ajuste o tipo ou periodo para rever outros marcos da proposta.
                    </p>
                  </div>
                )}

                {!eventsLoading && filteredEvents.length > 0 && (
                  <div className="relative px-4 py-3">
                    {/* Vertical spine */}
                    <div className="absolute left-7 top-3 bottom-3 w-px bg-border" aria-hidden />

                    <div className="space-y-3">
                      {filteredEvents.map((ev) => {
                        const conf = EVENT_CONFIG[ev.event_type] ?? EVENT_CONFIG.note;
                        const Icon = conf.icon;
                        const eventDate = new Date(ev.occurred_at);
                        const eventAuthor = ev.created_by_detail?.first_name || ev.created_by_detail?.email || 'Sistema';
                        return (
                          <div key={ev.id} className="flex gap-3">
                            {/* Dot on spine */}
                            <div className={cn('h-7 w-7 rounded-full flex items-center justify-center flex-shrink-0 z-10 border-2 border-background', conf.dot)}>
                              <Icon className="h-3.5 w-3.5 text-white" />
                            </div>
                            {/* Card */}
                            <div className={cn('flex-1 rounded-lg border border-l-4 p-3.5 min-w-0 shadow-sm', conf.card)}>
                              <div className="flex items-start justify-between gap-2 mb-1.5">
                                <span className="text-sm font-semibold text-foreground leading-tight">{ev.title}</span>
                                <span className={cn('text-[10px] font-medium rounded px-1.5 py-0.5 flex-shrink-0 capitalize', conf.iconColor)}>
                                  {ev.event_type_display}
                                </span>
                              </div>
                              {ev.notes && (
                                <p className="text-xs text-muted-foreground leading-relaxed mb-2">{ev.notes}</p>
                              )}
                              <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground">
                                <span className="inline-flex items-center gap-1">
                                  <Calendar className="h-2.5 w-2.5 flex-shrink-0" />
                                  {eventDate.toLocaleDateString('pt-PT')} {eventDate.toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit' })}
                                </span>
                                <span className="truncate">por {eventAuthor}</span>
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

          {/* ── EXPORT PANEL ── */}
          {rightTab === 'export' && id && (
            <ExportRequestPanel proposalId={id} />
          )}

          {/* ── POST-MORTEM PANEL ── */}
          {rightTab === 'postmortem' && id && (
            <PostMortemPanel proposalId={id} />
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
      <Dialog open={sectionDialogOpen} onOpenChange={setSectionDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Adicionar secção</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Input
              value={newSectionTitle}
              onChange={(e) => setNewSectionTitle(e.target.value)}
              placeholder="Ex: Plano de Mobilizacao"
              onKeyDown={(e) => e.key === 'Enter' && handleAddSection()}
            />
            {newSectionError && (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {newSectionError}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSectionDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleAddSection} disabled={isAddingSection}>
              {isAddingSection ? 'A criar...' : 'Criar secção'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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
            {transitionModal.targetStatus === 'ready_for_submission' && hasPendingTeamValidation && (
              <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-relaxed text-amber-800 dark:border-amber-900/60 dark:bg-amber-950/30 dark:text-amber-300">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <span>
                  Equipa ainda pendente. Pode avancar com QC para teste; confirme perfis, CVs e disponibilidade antes da submissao final.
                </span>
              </div>
            )}
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

      {/* ── Mobile Sections Sheet ── */}
      <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
        <SheetContent side="left" className="w-72 flex flex-col p-0">
          <SheetHeader className="px-4 py-3 border-b border-border">
            <SheetTitle className="text-sm truncate">{selectedProposal?.title}</SheetTitle>
          </SheetHeader>
          <div className="flex-1 overflow-auto p-3 space-y-1">
            {selectedProposal?.sections.map((section) => (
              <button
                key={section.id}
                onClick={() => { handleSectionChange(section.id); setMobileSidebarOpen(false); }}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all',
                  activeSectionId === section.id
                    ? 'bg-primary/10 text-primary font-semibold'
                    : 'hover:bg-muted text-muted-foreground'
                )}
              >
                <div className="flex items-center gap-2">
                  {section.isComplete ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                  ) : (
                    <div className="h-4 w-4 rounded-full border border-muted-foreground/40 flex-shrink-0" />
                  )}
                  <span className="truncate">{section.title}</span>
                </div>
              </button>
            ))}
          </div>
        </SheetContent>
      </Sheet>

      {/* ── Mobile Pipeline Sheet ── */}
      <Sheet open={mobilePipelineOpen} onOpenChange={setMobilePipelineOpen}>
        <SheetContent side="right" className="w-80 flex flex-col p-0">
          <SheetHeader className="px-4 py-3 border-b border-border">
            <SheetTitle className="text-sm">Pipeline COS</SheetTitle>
          </SheetHeader>
          <div className="flex-1 overflow-auto">
            {/* Current status */}
            <div className={cn(
              'p-4 border-b border-border',
              isTerminal && currentStatus === 'won' ? 'bg-gradient-to-br from-emerald-50 to-transparent dark:from-emerald-950/30' :
              isTerminal ? 'bg-gradient-to-br from-red-50 to-transparent dark:from-red-950/30' :
              'bg-gradient-to-br from-primary/5 to-transparent'
            )}>
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">Estado Atual</p>
              <div className="flex items-center gap-2.5">
                <StatusBadge status={currentStatus} />
                <span className="text-sm font-semibold">{STATUS_LABELS[currentStatus] || currentStatus}</span>
              </div>
              {stageContext && (
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{stageContext.hint}</p>
              )}
            </div>

            {/* Transitions */}
            {availableTransitions.length > 0 && (
              <div className="p-4 border-b border-border space-y-2">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-2">Próxima Ação</p>
                {availableTransitions.map((t, i) => (
                  <button
                    key={t.status}
                    onClick={() => { openTransitionModal(t.status, t.label); setMobilePipelineOpen(false); }}
                    className={cn(
                      'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all',
                      i === 0
                        ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm'
                        : 'border border-border hover:border-primary/40 hover:bg-muted text-foreground'
                    )}
                  >
                    <span>{t.label}</span>
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                ))}
              </div>
            )}

            {/* Pipeline stepper (compact) */}
            <div className="p-4">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground mb-3">Estágios</p>
              <div className="space-y-1">
                {PIPELINE_STAGES.map((stage) => {
                  const isCurrent = stage.status === currentStatus;
                  const isPast = !isTerminal && currentStageIndex > (STATUS_ORDER[stage.status] ?? 999);
                  return (
                    <div key={stage.status} className="flex items-center gap-2.5 py-0.5">
                      <div className={cn(
                        'h-3 w-3 rounded-full flex-shrink-0',
                        isCurrent ? 'bg-primary ring-2 ring-primary/30' :
                        isPast ? 'bg-emerald-500' :
                        'bg-muted-foreground/20'
                      )} />
                      <span className={cn(
                        'text-xs',
                        isCurrent ? 'text-primary font-semibold' :
                        isPast ? 'text-muted-foreground/60' :
                        'text-muted-foreground/40'
                      )}>
                        {stage.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
