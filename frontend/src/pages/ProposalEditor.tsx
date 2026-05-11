// ============================================
// PROPOSAL EDITOR PAGE - Rich Text + AI + Pipeline
// ============================================

import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Save,
  CheckCircle,
  FileText,
  CheckSquare,
  FileType,
  FileDown,
  Upload,
  Building2,
  UserCircle,
  Plus,
  X,
  Eye,
  ChevronRight,
  Calendar,
  Paperclip,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AIAssistButton } from '@/components/proposals/AIAssistButton';
import { RichTextEditor } from '@/components/proposals/RichTextEditor';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useProposalStore } from '@/stores';
import {
  apiDownloadProposalWord,
  apiDownloadProposalPdf,
  apiUploadProposalLogo,
  apiGetProposalEvents,
  apiCreateProposalEvent,
  apiTransitionProposalStatus,
  type ApiProposalEvent,
} from '@/lib/api';
import type { ProposalStatus } from '@/types';

// Pipeline transitions map: current status → available next statuses
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
    { status: 'bafo', label: 'Recebeu BAFO' },
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

const EVENT_TYPE_OPTIONS = [
  { value: 'submission', label: 'Submissão' },
  { value: 'evaluation', label: 'Avaliação' },
  { value: 'shortlist', label: 'Shortlist' },
  { value: 'clarification', label: 'Clarificação' },
  { value: 'bafo', label: 'BAFO' },
  { value: 'award', label: 'Adjudicação' },
  { value: 'contracting', label: 'Contratação' },
  { value: 'handover', label: 'Handover' },
  { value: 'note', label: 'Nota' },
];

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
  const [eventModal, setEventModal] = useState(false);
  const [newEvent, setNewEvent] = useState({
    event_type: 'note',
    artifact_type: '',
    title: '',
    notes: '',
    external_url: '',
  });
  const [eventError, setEventError] = useState('');

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

  // AI applies real generated content directly
  const handleAISuggestion = (generatedContent: string) => {
    setEditorContent(generatedContent);
    handleContentChange(generatedContent);
  };

  const handleExport = async (type: 'word' | 'pdf') => {
    if (!id) return;
    setIsExporting(type);
    try {
      const blob =
        type === 'word' ? await apiDownloadProposalWord(id) : await apiDownloadProposalPdf(id);
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
      // If a project was created, navigate there
      if (result.project_id) {
        navigate(`/projects/${result.project_id}`);
        return;
      }
      // Reload proposal to get updated status
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
    try {
      const created = await apiCreateProposalEvent(id, newEvent);
      setEvents((prev) => [created, ...prev]);
      setEventModal(false);
      setNewEvent({ event_type: 'note', artifact_type: '', title: '', notes: '', external_url: '' });
    } catch (err) {
      setEventError(err instanceof Error ? err.message : 'Erro ao criar evento.');
    }
  };

  const activeSection = selectedProposal?.sections.find((s) => s.id === activeSectionId);
  const currentStatus = selectedProposal?.status || 'draft';
  const availableTransitions = PIPELINE_TRANSITIONS[currentStatus] || [];

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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-border">
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
        <div className="w-64 flex-shrink-0 flex flex-col border-r border-border overflow-auto">
          {/* Logos */}
          <div className="p-3 border-b border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Logos da Proposta
            </h3>
            <div className="space-y-2">
              {(['proponent', 'client'] as const).map((type) => (
                <button
                  key={type}
                  onClick={() => triggerUpload(type)}
                  className="w-full flex items-center gap-2 p-2 rounded-lg border border-dashed border-border hover:bg-muted transition-colors text-left"
                >
                  {logos[type] ? (
                    <img src={logos[type]} alt={type} className="h-8 w-8 object-contain" />
                  ) : type === 'proponent' ? (
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <UserCircle className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="text-xs text-muted-foreground truncate">
                    {type === 'proponent' ? 'Logo Proponente' : 'Logo Cliente'}
                  </span>
                  <Upload className="h-3 w-3 ml-auto text-muted-foreground" />
                </button>
              ))}
            </div>
          </div>

          {/* Consortium */}
          <div className="p-3 border-b border-border">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Consórcio
            </h3>
            <div className="space-y-1">
              {consortiumMembers.map((member, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs">
                  <span className="flex-1 truncate">{member}</span>
                  <Button variant="ghost" size="sm" className="h-5 w-5 p-0" onClick={() => handleRemoveConsortiumMember(idx)}>
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
                <Button size="sm" className="h-7 px-2" onClick={handleAddConsortiumMember}>
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>

          {/* Sections */}
          <div className="flex-1 p-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              Secções
            </h3>
            <div className="space-y-1">
              {selectedProposal.sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => handleSectionChange(section.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    activeSectionId === section.id
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'hover:bg-muted text-muted-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {section.isComplete ? (
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-muted-foreground" />
                    )}
                    <span className="truncate">{section.title}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Center - Editor */}
        <div className="flex-1 flex flex-col bg-card border-x border-border overflow-hidden">
          <div className="flex items-center justify-between p-3 border-b border-border">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium">{activeSection?.title}</span>
              {activeSection?.isComplete && (
                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
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

          <div className="flex items-center justify-between p-3 border-t border-border bg-muted/30">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>{editorContent.replace(/<[^>]*>/g, '').length} caracteres</span>
              <span>
                {editorContent.replace(/<[^>]*>/g, '').split(/\s+/).filter(Boolean).length} palavras
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => saveSection(editorContent)}>
                <Save className="h-4 w-4 mr-2" />
                Guardar
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  if (activeSection) updateSection(selectedProposal.id, activeSectionId, editorContent);
                }}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Marcar Completo
              </Button>
            </div>
          </div>
        </div>

        {/* Right Sidebar - Pipeline + Events */}
        <div className="w-80 flex-shrink-0 bg-card flex flex-col overflow-hidden border-l border-border">
          <Tabs defaultValue="pipeline" className="flex flex-col flex-1 overflow-hidden">
            <TabsList className="grid grid-cols-2 rounded-none border-b border-border h-10">
              <TabsTrigger value="pipeline" className="text-xs rounded-none">Pipeline</TabsTrigger>
              <TabsTrigger value="events" className="text-xs rounded-none">Eventos</TabsTrigger>
            </TabsList>

            {/* Pipeline Tab */}
            <TabsContent value="pipeline" className="flex-1 overflow-auto m-0 p-4 space-y-4">
              {/* Current Status */}
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Estado Atual
                </p>
                <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                  <StatusBadge status={currentStatus} />
                  <span className="text-sm font-medium">{STATUS_LABELS[currentStatus] || currentStatus}</span>
                </div>
              </div>

              {/* Available Transitions */}
              {availableTransitions.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                    Próximos Passos
                  </p>
                  <div className="space-y-2">
                    {availableTransitions.map((t) => (
                      <Button
                        key={t.status}
                        variant="outline"
                        size="sm"
                        className="w-full justify-between"
                        onClick={() => openTransitionModal(t.status, t.label)}
                      >
                        <span className="text-xs">{t.label}</span>
                        <ChevronRight className="h-3 w-3" />
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Pipeline Stages */}
              <div>
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  Pipeline Completo
                </p>
                <div className="space-y-1">
                  {Object.keys(STATUS_LABELS).map((status) => {
                    const isCurrent = status === currentStatus;
                    return (
                      <div
                        key={status}
                        className={`flex items-center gap-2 px-2 py-1 rounded text-xs ${
                          isCurrent
                            ? 'bg-primary/10 text-primary font-semibold'
                            : 'text-muted-foreground'
                        }`}
                      >
                        <div
                          className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${
                            isCurrent ? 'bg-primary' : 'bg-muted-foreground/40'
                          }`}
                        />
                        {STATUS_LABELS[status]}
                      </div>
                    );
                  })}
                </div>
              </div>
            </TabsContent>

            {/* Events Tab */}
            <TabsContent value="events" className="flex-1 overflow-auto m-0 flex flex-col">
              <div className="p-3 border-b border-border flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Linha do Tempo
                </p>
                <Button size="sm" variant="outline" className="h-7 text-xs px-2" onClick={() => setEventModal(true)}>
                  <Plus className="h-3 w-3 mr-1" />
                  Novo
                </Button>
              </div>
              <div className="flex-1 overflow-auto p-3 space-y-3">
                {eventsLoading && (
                  <p className="text-xs text-muted-foreground text-center py-4">A carregar...</p>
                )}
                {!eventsLoading && events.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    Nenhum evento registado.
                  </p>
                )}
                {events.map((ev) => (
                  <div key={ev.id} className="p-3 bg-muted/50 rounded-lg border border-border">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="text-xs font-semibold truncate">{ev.title}</span>
                      <Badge variant="outline" className="text-xs flex-shrink-0">
                        {ev.event_type_display}
                      </Badge>
                    </div>
                    {ev.notes && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{ev.notes}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      <Calendar className="h-3 w-3" />
                      <span>{new Date(ev.occurred_at).toLocaleDateString('pt-PT')}</span>
                      {ev.attachment_url && (
                        <a href={ev.attachment_url} target="_blank" rel="noreferrer" className="ml-auto">
                          <Paperclip className="h-3 w-3" />
                        </a>
                      )}
                      {ev.external_url && (
                        <a href={ev.external_url} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>Pré-visualização da Proposta</DialogTitle>
          </DialogHeader>
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </DialogContent>
      </Dialog>

      {/* Pipeline Transition Modal */}
      <Dialog open={transitionModal.open} onOpenChange={(open) => !open && setTransitionModal({ open: false, targetStatus: null, label: '' })}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{transitionModal.label}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Transitar proposta para:{' '}
              <strong>{transitionModal.targetStatus ? STATUS_LABELS[transitionModal.targetStatus] : ''}</strong>
            </p>
            <Textarea
              placeholder="Nota (opcional)..."
              value={transitionNote}
              onChange={(e) => setTransitionNote(e.target.value)}
              rows={3}
            />
            {transitionError && <p className="text-sm text-destructive">{transitionError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTransitionModal({ open: false, targetStatus: null, label: '' })}>
              Cancelar
            </Button>
            <Button onClick={confirmTransition} disabled={isTransitioning}>
              {isTransitioning ? 'A processar...' : 'Confirmar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Event Modal */}
      <Dialog open={eventModal} onOpenChange={setEventModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Registar Evento</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1 block">Tipo de evento</label>
                <Select
                  value={newEvent.event_type}
                  onValueChange={(v) => setNewEvent((p) => ({ ...p, event_type: v }))}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {EVENT_TYPE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-medium mb-1 block">Artefacto</label>
                <Select
                  value={newEvent.artifact_type || ''}
                  onValueChange={(v) => setNewEvent((p) => ({ ...p, artifact_type: v }))}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="Nenhum" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Nenhum</SelectItem>
                    <SelectItem value="final_proposal">Proposta Final</SelectItem>
                    <SelectItem value="contract">Contrato</SelectItem>
                    <SelectItem value="handover">Handover Package</SelectItem>
                    <SelectItem value="kickoff">Kickoff Pack</SelectItem>
                    <SelectItem value="checklist">Checklist de Arranque</SelectItem>
                    <SelectItem value="other">Outro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">Título *</label>
              <Input
                value={newEvent.title}
                onChange={(e) => setNewEvent((p) => ({ ...p, title: e.target.value }))}
                placeholder="Título do evento"
              />
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">Notas</label>
              <Textarea
                value={newEvent.notes}
                onChange={(e) => setNewEvent((p) => ({ ...p, notes: e.target.value }))}
                placeholder="Detalhes adicionais..."
                rows={3}
              />
            </div>
            <div>
              <label className="text-xs font-medium mb-1 block">URL externo</label>
              <Input
                value={newEvent.external_url}
                onChange={(e) => setNewEvent((p) => ({ ...p, external_url: e.target.value }))}
                placeholder="https://..."
              />
            </div>
            {eventError && <p className="text-sm text-destructive">{eventError}</p>}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEventModal(false)}>
              Cancelar
            </Button>
            <Button onClick={handleCreateEvent}>Registar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
