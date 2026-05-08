// ============================================
// SCRAPING PAGE - Web Scraping / Fontes
// ============================================

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Globe, Play, Pause, Settings, Plus, Search, RefreshCw,
  CheckCircle2, AlertTriangle, Clock, ArrowRight,
  Activity, Zap, Bot, ChevronDown, ChevronUp,
  BarChart3, Layers, Eye, DollarSign, ExternalLink, Star,
  ChevronLeft, ChevronRight,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AddScrapingSourceModal } from '@/components/modals';
import {
  apiCreateScrapingSource,
  apiGetScrapedOpportunities,
  apiGetScrapedOpportunity,
  apiGetScrapingJobs,
  apiGetScrapingSources,
  apiGetScrapingStats,
  apiIgnoreScrapedOpportunity,
  apiImportScrapedOpportunity,
  apiRunScrapingSource,
  apiToggleScrapingSource,
  apiUpdateScrapingSource,
  type ApiScrapedOpportunity,
  type ApiScrapedOpportunityDetail,
  type ApiScrapingJob,
  type ApiScrapingSource,
} from '@/lib/api';
import type { ScrapingSource, ScrapedOpportunity, ScrapingJob } from '@/types';

type ScrapingStats = {
  total_sources: number;
  active_sources: number;
  total_opportunities: number;
  imported_opportunities: number;
  new_opportunities: number;
  cv_eligible_new: number;
  avg_quality_score: number;
  success_rate: number;
};

function toDate(value: string | null | undefined): Date | undefined {
  return value ? new Date(value) : undefined;
}

function mapSource(source: ApiScrapingSource): ScrapingSource {
  return {
    id: String(source.id),
    name: source.name,
    organization: source.organization,
    url: source.url,
    sourceType: source.source_type as ScrapingSource['sourceType'],
    status: source.status as ScrapingSource['status'],
    scrapeFrequency: source.scrape_frequency as ScrapingSource['scrapeFrequency'],
    lastScrapedAt: toDate(source.last_scraped_at),
    nextScrapeAt: toDate(source.next_scrape_at),
    filters: {},
    newOpportunitiesCount: source.new_opportunities_count || 0,
    totalOpportunitiesCount: source.total_opportunities_count || 0,
    successRate: source.success_rate || 0,
    errorMessage: source.error_message || undefined,
  };
}

function mapOpportunity(opp: ApiScrapedOpportunity): ScrapedOpportunity {
  return {
    id: String(opp.id),
    sourceId: String(opp.source),
    externalId: opp.external_id || undefined,
    externalUrl: opp.external_url,
    title: opp.title,
    organization: opp.organization,
    client: opp.client,
    sector: opp.sector || undefined,
    country: opp.country || undefined,
    description: opp.description || '',
    value: opp.value ? Number(opp.value) : undefined,
    currency: opp.currency || 'USD',
    deadline: toDate(opp.deadline),
    status: opp.status as ScrapedOpportunity['status'],
    publishedAt: toDate(opp.published_at),
    deadlineAlert: Boolean(opp.deadline_alert),
    aiSummary: opp.ai_summary || undefined,
    deepContentStatus: opp.deep_content_status || undefined,
    importedOpportunityId: opp.imported_opportunity ? String(opp.imported_opportunity) : undefined,
  };
}

function mapJob(job: ApiScrapingJob): ScrapingJob {
  return {
    id: String(job.id),
    sourceId: String(job.source),
    status: job.status as ScrapingJob['status'],
    startedAt: toDate(job.started_at),
    completedAt: toDate(job.completed_at),
    itemsFound: job.items_found || 0,
    itemsNew: job.items_new || 0,
    itemsImported: job.items_imported || 0,
    errorLog: job.error_log || undefined,
    executedBy: job.executed_by || 'system',
  };
}

function deepContentLabel(status?: string): string | null {
  if (!status) return null;

  const labels: Record<string, string> = {
    extracted: 'Fonte lida',
    completed: 'Fonte lida',
    failed: 'Fonte nao lida',
    skipped: 'Sem texto extraido',
    pending: 'Leitura pendente',
  };

  return labels[status] || `Fonte: ${status}`;
}

function isImportableScrapedOpportunity(status?: string, importedOpportunityId?: string | number | null): boolean {
  const normalized = (status || '').toLowerCase().trim();
  return !importedOpportunityId && normalized !== 'imported' && normalized !== 'ignored' && normalized !== 'expired';
}

// ============================================
// COMPONENTS
// ============================================
function SourceStatusBadge({ status }: { status: string }) {
  const configs: Record<string, { label: string; class: string; icon: typeof CheckCircle2 }> = {
    active: { label: 'Ativo', class: 'bg-emerald-100 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
    paused: { label: 'Pausado', class: 'bg-slate-100 text-slate-700 border-slate-200', icon: Pause },
    error: { label: 'Erro', class: 'bg-red-100 text-red-700 border-red-200', icon: AlertTriangle },
    disabled: { label: 'Desativado', class: 'bg-slate-100 text-slate-500 border-slate-200', icon: AlertTriangle },
  };
  const cfg = configs[status] || configs.error;
  const Icon = cfg.icon;
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${cfg.class}`}>
      <Icon className="h-3 w-3" />{cfg.label}
    </span>
  );
}

function OpportunityStatusBadge({ status }: { status: string }) {
  const configs: Record<string, { label: string; class: string }> = {
    new: { label: 'Nova', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    imported: { label: 'Importada', class: 'bg-violet-100 text-violet-700 border-violet-200' },
    ignored: { label: 'Ignorada', class: 'bg-slate-100 text-slate-700 border-slate-200' },
    expired: { label: 'Expirada', class: 'bg-red-100 text-red-700 border-red-200' },
  };
  const cfg = configs[status] || configs.new;
  return <span className={`text-xs px-2 py-0.5 rounded-full border ${cfg.class}`}>{cfg.label}</span>;
}

function JobStatusBadge({ status }: { status: string }) {
  const configs: Record<string, { label: string; class: string }> = {
    running: { label: 'Em Progresso', class: 'bg-blue-100 text-blue-700 border-blue-200' },
    completed: { label: 'Concluido', class: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    failed: { label: 'Falhou', class: 'bg-red-100 text-red-700 border-red-200' },
    scheduled: { label: 'Agendado', class: 'bg-amber-100 text-amber-700 border-amber-200' },
  };
  const cfg = configs[status] || configs.failed;
  return <span className={`text-xs px-2 py-0.5 rounded-full border ${cfg.class}`}>{cfg.label}</span>;
}

interface StatsCardsProps {
  sources: ScrapingSource[];
  stats: ScrapingStats | null;
}

function StatsCards({ sources, stats }: StatsCardsProps) {
  const activeSources = stats?.active_sources ?? sources.filter((s) => s.status === 'active').length;
  const totalOportunidades = stats?.total_opportunities ?? sources.reduce((acc, s) => acc + s.totalOpportunitiesCount, 0);
  const avgSuccess = stats?.success_rate ?? (
    sources.length > 0
      ? Math.round(sources.reduce((acc, s) => acc + s.successRate, 0) / sources.length)
      : 0
  );
  const totalSources = stats?.total_sources ?? sources.length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-blue-600"><Globe className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{totalSources}</p><p className="text-xs text-muted-foreground">Fontes Totais</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-emerald-600"><Activity className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{activeSources}</p><p className="text-xs text-muted-foreground">Fontes Ativas</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-violet-600"><Layers className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{totalOportunidades.toLocaleString('pt-PT')}</p><p className="text-xs text-muted-foreground">Oportunidades Encontradas</p></div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-amber-600"><Zap className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{avgSuccess}%</p><p className="text-xs text-muted-foreground">Taxa de Sucesso</p></div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================
// TAB: SOURCES
// ============================================
interface SourcesTabProps {
  sources: ScrapingSource[];
  editingSource: ScrapingSource | null;
  runningSourceIds: Set<string>;
  savingSource: boolean;
  onAdd: () => void;
  onToggle: (id: string) => void;
  onRun: (id: string) => void;
  onEdit: (source: ScrapingSource) => void;
  onCancelEdit: () => void;
  onSaveEdit: (id: string, data: Partial<ApiScrapingSource>) => void;
}

function SourcesTab({
  sources,
  editingSource,
  runningSourceIds,
  savingSource,
  onAdd,
  onToggle,
  onRun,
  onEdit,
  onCancelEdit,
  onSaveEdit,
}: SourcesTabProps) {
  const [search, setSearch] = useState('');
  const [editForm, setEditForm] = useState({
    name: '',
    url: '',
    scrape_frequency: 'daily',
    status: 'active',
  });
  const filtered = sources.filter((s) => s.name.toLowerCase().includes(search.toLowerCase()));

  useEffect(() => {
    if (editingSource) {
      setEditForm({
        name: editingSource.name,
        url: editingSource.url,
        scrape_frequency: editingSource.scrapeFrequency,
        status: editingSource.status,
      });
    }
  }, [editingSource]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar fontes..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Button size="sm" onClick={onAdd}><Plus className="h-4 w-4 mr-1" />Nova Fonte</Button>
      </div>

      <Dialog open={!!editingSource} onOpenChange={(open) => !open && onCancelEdit()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Definicoes da Fonte</DialogTitle>
          </DialogHeader>
          {editingSource && (
            <div className="space-y-3">
              <Input value={editForm.name} onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Nome" />
              <Input value={editForm.url} onChange={(e) => setEditForm((prev) => ({ ...prev, url: e.target.value }))} placeholder="URL" />
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={editForm.scrape_frequency} onChange={(e) => setEditForm((prev) => ({ ...prev, scrape_frequency: e.target.value }))}>
                <option value="hourly">Por Hora</option>
                <option value="daily">Diario</option>
                <option value="weekly">Semanal</option>
              </select>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={editForm.status} onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))}>
                <option value="active">Ativo</option>
                <option value="paused">Pausado</option>
                <option value="error">Erro</option>
                <option value="disabled">Desativado</option>
              </select>
              <div className="flex justify-end gap-2 pt-2">
                <Button size="sm" variant="outline" onClick={onCancelEdit} disabled={savingSource}>Cancelar</Button>
                <Button size="sm" onClick={() => onSaveEdit(editingSource.id, editForm)} disabled={savingSource}>
                  {savingSource ? 'A guardar...' : 'Guardar'}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((source) => (
          <Card key={source.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm">{source.name}</h4>
                    <SourceStatusBadge status={source.status} />
                  </div>
                  <a href={source.url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 flex items-center gap-0.5 mt-0.5 hover:underline">
                    <Globe className="h-3 w-3" />{source.url}
                  </a>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-muted-foreground">{source.totalOpportunitiesCount}</p>
                  <p className="text-xs text-muted-foreground">oportunidades</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Taxa de sucesso:</span>
                <span className={`font-medium ${source.successRate >= 90 ? 'text-emerald-600' : source.successRate >= 70 ? 'text-amber-600' : 'text-red-600'}`}>{source.successRate}%</span>
              </div>
              <Progress value={source.successRate} className="h-1.5" />

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {source.lastScrapedAt ? `Ultimo scrape: ${source.lastScrapedAt.toLocaleDateString('pt-PT')}` : 'Nunca scrapeado'}
              </div>

              {source.errorMessage && (
                <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 p-2 rounded">
                  <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                  <span>{source.errorMessage}</span>
                </div>
              )}

              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="h-8 text-xs flex-1" onClick={() => onToggle(source.id)}>
                  {source.status === 'paused' ? <><Play className="h-3.5 w-3.5 mr-1" />Iniciar</> : <><Pause className="h-3.5 w-3.5 mr-1" />Pausar</>}
                </Button>
                <Button size="sm" variant="outline" className="h-8 text-xs flex-1" onClick={() => onRun(source.id)} disabled={runningSourceIds.has(source.id)}>
                  <RefreshCw className="h-3.5 w-3.5 mr-1" />{runningSourceIds.has(source.id) ? 'A executar' : 'Executar'}
                </Button>
                <Button size="sm" variant="outline" className="h-8 text-xs px-2" onClick={() => onEdit(source)}><Settings className="h-3.5 w-3.5" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          Nenhuma fonte encontrada. Adicione uma nova fonte para comecar.
        </div>
      )}
    </div>
  );
}

// ============================================
// DETAIL MODAL
// ============================================
interface OpportunityDetailModalProps {
  detail: ApiScrapedOpportunityDetail | null;
  loading: boolean;
  onClose: () => void;
  onImport: (id: string) => void;
  isBusy: boolean;
}

function OpportunityDetailModal({ detail, loading, onClose, onImport, isBusy }: OpportunityDetailModalProps) {
  const navigate = useNavigate();
  const open = loading || !!detail;
  const qualityColor = (score: number) =>
    score >= 0.7 ? 'text-emerald-600' : score >= 0.4 ? 'text-amber-600' : 'text-red-600';

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{loading ? 'A carregar…' : detail?.title}</DialogTitle>
        </DialogHeader>
        {loading && <div className="py-12 text-center text-muted-foreground">A carregar detalhe…</div>}
        {!loading && detail && (
          <div className="space-y-4 text-sm">
            {/* Meta row */}
            <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
              {detail.source?.name && <span className="flex items-center gap-1"><Globe className="h-3 w-3" />{detail.source.name}</span>}
              {detail.country && <span>{detail.country}</span>}
              {detail.sector && <span>{detail.sector}</span>}
              {detail.language && <span className="uppercase">{detail.language}</span>}
              {detail.cv_eligible && (
                <span className="flex items-center gap-1 text-emerald-600 font-medium">
                  <Star className="h-3 w-3" />CV Elegível
                </span>
              )}
              {detail.data_quality_score != null && (
                <span className={`font-medium ${qualityColor(detail.data_quality_score)}`}>
                  Qualidade {Math.round(detail.data_quality_score * 100)}%
                </span>
              )}
            </div>

            {/* Key fields */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-muted/40 rounded-lg text-xs">
              <div>
                <p className="text-muted-foreground mb-0.5">Prazo</p>
                <p className="font-medium">{detail.deadline ? new Date(detail.deadline).toLocaleDateString('pt-PT') : '—'}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Valor</p>
                <p className="font-medium">{detail.value ? `${Number(detail.value).toLocaleString('pt-PT')} ${detail.currency}` : '—'}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Organização</p>
                <p className="font-medium">{detail.organization || detail.client || '—'}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Publicado</p>
                <p className="font-medium">{detail.published_at ? new Date(detail.published_at).toLocaleDateString('pt-PT') : '—'}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3 bg-muted/40 rounded-lg text-xs">
              <div>
                <p className="text-muted-foreground mb-0.5">Leitura da fonte</p>
                <p className="font-medium">{deepContentLabel(detail.deep_content_status || undefined) || '-'}</p>
              </div>
              {detail.imported_opportunity && (
                <div>
                  <p className="text-muted-foreground mb-0.5">Oportunidade criada</p>
                  <p className="font-medium">#{detail.imported_opportunity}</p>
                </div>
              )}
            </div>

            {/* External link */}
            <a
              href={detail.external_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 text-blue-600 hover:underline text-xs"
            >
              <ExternalLink className="h-3.5 w-3.5" />Ver fonte original
            </a>

            {/* AI Summary */}
            {detail.ai_summary && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-1.5">
                  <Bot className="h-4 w-4 text-blue-600" />
                  <span className="font-medium text-blue-900">Resumo AI</span>
                </div>
                <p className="text-blue-800 leading-relaxed">{detail.ai_summary}</p>
              </div>
            )}

            {/* AI Requirements */}
            {detail.ai_extracted_requirements && detail.ai_extracted_requirements.length > 0 && (
              <div>
                <p className="font-medium mb-2">Requisitos extraídos pela AI</p>
                <ul className="space-y-1">
                  {detail.ai_extracted_requirements.map((req, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs">
                      <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                      {typeof req === 'string' ? req : req.description}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Description */}
            {detail.description && (
              <div>
                <p className="font-medium mb-1">Descrição</p>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-6">{detail.description}</p>
              </div>
            )}

            {/* Deep content */}
            {detail.deep_content_text && (
              <div>
                <p className="font-medium mb-1">Conteúdo extraído da fonte</p>
                <p className="text-muted-foreground leading-relaxed whitespace-pre-line line-clamp-6 text-xs bg-muted/40 p-3 rounded">{detail.deep_content_text}</p>
              </div>
            )}

            {/* Actions */}
            {isImportableScrapedOpportunity(detail.status, detail.imported_opportunity) && (
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button size="sm" variant="outline" onClick={onClose}>Fechar</Button>
                <Button size="sm" onClick={() => { onImport(String(detail.id)); onClose(); }} disabled={isBusy}>
                  <ArrowRight className="h-3.5 w-3.5 mr-1" />Importar para Oportunidades
                </Button>
              </div>
            )}
            {!isImportableScrapedOpportunity(detail.status, detail.imported_opportunity) && (
              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button size="sm" variant="outline" onClick={onClose}>Fechar</Button>
                {detail.imported_opportunity && (
                  <Button size="sm" onClick={() => navigate(`/opportunities/${detail.imported_opportunity}`)}>
                    Abrir em Oportunidades
                  </Button>
                )}
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ============================================
// TAB: OPPORTUNITIES
// ============================================
interface OpportunitiesTabProps {
  opportunities: ScrapedOpportunity[];
  busyOpportunityIds: Set<string>;
  page: number;
  totalCount: number;
  pageSize: number;
  onImport: (id: string) => void;
  onIgnore: (id: string) => void;
  onView: (id: string) => void;
  onPageChange: (page: number) => void;
}

function OpportunitiesTab({
  opportunities, busyOpportunityIds, page, totalCount, pageSize,
  onImport, onIgnore, onView, onPageChange,
}: OpportunitiesTabProps) {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = opportunities.filter((o) => {
    const matchesSearch = o.title.toLowerCase().includes(search.toLowerCase()) || o.organization.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || o.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, totalCount);

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar oportunidades..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Todos Status</option>
          <option value="new">Novas</option>
          <option value="imported">Importadas</option>
          <option value="ignored">Ignoradas</option>
          <option value="expired">Expiradas</option>
        </select>
      </div>

      <p className="text-xs text-muted-foreground">
        Fluxo: ver detalhes da oportunidade, confirmar a fonte e clicar em Importar para Oportunidades. Depois ela fica disponivel no modulo Oportunidades para criar proposta.
      </p>

      <div className="space-y-3">
        {filtered.map((opp) => {
          const isExpanded = expanded === opp.id;
          const isBusy = busyOpportunityIds.has(opp.id);
          const canImport = isImportableScrapedOpportunity(opp.status, opp.importedOpportunityId);
          return (
            <Card key={opp.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-semibold text-sm">{opp.title}</h4>
                      <OpportunityStatusBadge status={opp.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{opp.organization} – {opp.country || '–'}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Prazo: {opp.deadline ? opp.deadline.toLocaleDateString('pt-PT') : '–'}
                      </span>
                      {opp.sector && <span className="flex items-center gap-1"><BarChart3 className="h-3 w-3" />{opp.sector}</span>}
                      {opp.value && <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{opp.value.toLocaleString('pt-PT')} {opp.currency}</span>}
                      {deepContentLabel(opp.deepContentStatus) && (
                        <span>{deepContentLabel(opp.deepContentStatus)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-wrap justify-end gap-1 shrink-0">
                    <Button size="sm" variant="outline" className="h-7 text-xs px-2" title="Ver detalhe" onClick={() => onView(opp.id)}>
                      <Eye className="h-3.5 w-3.5 mr-1" />Ver
                    </Button>
                    {opp.externalUrl && (
                      <Button size="sm" variant="outline" className="h-7 text-xs px-2" title="Abrir fonte" asChild>
                        <a href={opp.externalUrl} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-3.5 w-3.5 mr-1" />Fonte
                        </a>
                      </Button>
                    )}
                    {canImport && (
                      <Button size="sm" className="h-7 text-xs px-2" onClick={() => onImport(opp.id)} disabled={isBusy}>
                        <ArrowRight className="h-3.5 w-3.5 mr-1" />Importar
                      </Button>
                    )}
                    {opp.importedOpportunityId && (
                      <Button size="sm" className="h-7 text-xs px-2" onClick={() => navigate(`/opportunities/${opp.importedOpportunityId}`)}>
                        Abrir em Oportunidades
                      </Button>
                    )}
                    {canImport && (
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => onIgnore(opp.id)} disabled={isBusy}>
                        Ignorar
                      </Button>
                    )}
                  </div>
                </div>

                {isExpanded && opp.aiSummary && (
                  <div className="mt-3 pt-3 border-t">
                    <div className="p-3 bg-blue-50/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <Bot className="h-4 w-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">Resumo AI</span>
                      </div>
                      <p className="text-sm text-blue-800">{opp.aiSummary}</p>
                    </div>
                  </div>
                )}

                {opp.aiSummary && (
                  <Button variant="ghost" size="sm" className="w-full mt-2 h-7 text-xs" onClick={() => setExpanded(isExpanded ? null : opp.id)}>
                    {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" />Recolher</> : <><ChevronDown className="h-3 w-3 mr-1" />Ver Resumo AI</>}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <p>Nenhuma oportunidade encontrada.</p>
          <p className="text-sm mt-1">Execute uma fonte ativa e consulte o Histórico de Jobs.</p>
        </div>
      )}

      {totalCount > pageSize && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-muted-foreground">{start}–{end} de {totalCount} oportunidades</p>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" className="h-8 w-8 p-0" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-xs text-muted-foreground">Pág. {page} / {totalPages}</span>
            <Button size="sm" variant="outline" className="h-8 w-8 p-0" disabled={page >= totalPages} onClick={() => onPageChange(page + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// TAB: JOB LOGS
// ============================================
interface JobLogsTabProps {
  jobs: ScrapingJob[];
  sources: ScrapingSource[];
}

function JobLogsTab({ jobs, sources }: JobLogsTabProps) {
  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {jobs.map((job) => (
          <Card key={job.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <JobStatusBadge status={job.status} />
                  <div>
                    <p className="font-semibold text-sm">{sources.find((s) => s.id === job.sourceId)?.name || job.sourceId}</p>
                    <p className="text-xs text-muted-foreground">
                      {job.startedAt ? job.startedAt.toLocaleString('pt-PT') : '-'}
                      {job.completedAt && job.startedAt ? ` (${Math.floor((job.completedAt.getTime() - job.startedAt.getTime()) / 60000)}m)` : ''}
                    </p>
                  </div>
                </div>
                <div className="text-right text-sm">
                  {job.itemsNew > 0 ? (
                    <p className="text-emerald-600 font-medium">+{job.itemsNew} novas oportunidades</p>
                  ) : job.status === 'failed' ? (
                    <p className="text-red-600 font-medium">Falhou</p>
                  ) : (
                    <p className="text-muted-foreground">Nenhuma nova</p>
                  )}
                  <p className="text-xs text-muted-foreground">{job.itemsFound} total encontradas</p>
                </div>
              </div>

              {job.errorLog && (
                <div className="mt-3 p-2 bg-red-50 rounded text-xs text-red-700">
                  <p className="flex items-center gap-1"><AlertTriangle className="h-3 w-3" />{job.errorLog}</p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ============================================
// MAIN PAGE
// ============================================
const PAGE_SIZE = 20;

export function ScrapingPage() {
  const navigate = useNavigate();
  const [sources, setSources] = useState<ScrapingSource[]>([]);
  const [opportunities, setOpportunities] = useState<ScrapedOpportunity[]>([]);
  const [opportunitiesTotalCount, setOpportunitiesTotalCount] = useState(0);
  const [opportunitiesPage, setOpportunitiesPage] = useState(1);
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [stats, setStats] = useState<ScrapingStats | null>(null);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [editingSource, setEditingSource] = useState<ScrapingSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningSourceIds, setRunningSourceIds] = useState<Set<string>>(new Set());
  const [busyOpportunityIds, setBusyOpportunityIds] = useState<Set<string>>(new Set());
  const [savingSource, setSavingSource] = useState(false);
  const [viewingDetail, setViewingDetail] = useState<ApiScrapedOpportunityDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const refreshSources = useCallback(async () => {
    const response = await apiGetScrapingSources();
    setSources(response.results.map(mapSource));
  }, []);

  const refreshOpportunities = useCallback(async (page: number) => {
    const response = await apiGetScrapedOpportunities(page);
    setOpportunities(response.results.map(mapOpportunity));
    setOpportunitiesTotalCount(response.count);
  }, []);

  const refreshAll = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const [sourcesResponse, opportunitiesResponse, jobsResponse, statsResponse] = await Promise.all([
        apiGetScrapingSources(),
        apiGetScrapedOpportunities(page),
        apiGetScrapingJobs(),
        apiGetScrapingStats(),
      ]);
      setSources(sourcesResponse.results.map(mapSource));
      setOpportunities(opportunitiesResponse.results.map(mapOpportunity));
      setOpportunitiesTotalCount(opportunitiesResponse.count);
      setJobs(jobsResponse.results.map(mapJob));
      setStats(statsResponse);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao carregar dados de scraping';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshAll();
  }, [refreshAll]);

  const handleAddSource = async (data: any) => {
    setError(null);
    try {
      await apiCreateScrapingSource({
        name: data.name,
        organization: data.organization,
        url: data.url,
        source_type: data.source_type || data.sourceType || 'portal',
        scrape_frequency: data.scrape_frequency || data.scrapeFrequency || 'daily',
      });
      toast.success('Fonte criada');
      setShowSourceModal(false);
      await refreshAll();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao criar fonte';
      setError(message);
      toast.error(message);
    }
  };

  const handleToggleSource = async (id: string) => {
    const previous = sources;
    setError(null);
    setSources((prev) =>
      prev.map((s) => {
        if (s.id !== id) return s;
        const nextStatus = s.status === 'active' ? 'paused' : 'active';
        return { ...s, status: nextStatus };
      })
    );
    try {
      await apiToggleScrapingSource(Number(id));
      await refreshSources();
      toast.success('Estado da fonte atualizado');
    } catch (err) {
      setSources(previous);
      const message = err instanceof Error ? err.message : 'Erro ao atualizar fonte';
      setError(message);
      toast.error(message);
    }
  };

  const handleRunSource = async (id: string) => {
    setError(null);
    setRunningSourceIds((prev) => new Set(prev).add(id));
    try {
      await apiRunScrapingSource(Number(id));
      toast.success('Scraping iniciado');
      await refreshAll();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao executar scraping';
      setError(message);
      toast.error(message);
    } finally {
      setRunningSourceIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleSaveSource = async (id: string, data: Partial<ApiScrapingSource>) => {
    setSavingSource(true);
    setError(null);
    try {
      const updated = await apiUpdateScrapingSource(Number(id), data);
      setSources((prev) => prev.map((source) => (source.id === id ? mapSource(updated) : source)));
      setEditingSource(null);
      toast.success('Fonte atualizada');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao guardar fonte';
      setError(message);
      toast.error(message);
    } finally {
      setSavingSource(false);
    }
  };

  const handleViewOpportunity = async (id: string) => {
    setLoadingDetail(true);
    setViewingDetail(null);
    try {
      const detail = await apiGetScrapedOpportunity(Number(id));
      setViewingDetail(detail);
    } catch (err) {
      toast.error('Erro ao carregar detalhe');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handlePageChange = async (page: number) => {
    setOpportunitiesPage(page);
    await refreshOpportunities(page);
  };

  const handleImportOpportunity = async (id: string) => {
    setBusyOpportunityIds((prev) => new Set(prev).add(id));
    setError(null);
    try {
      const result = await apiImportScrapedOpportunity(Number(id));
      setOpportunities((prev) =>
        prev.map((o) => (
          o.id === id
            ? { ...o, status: 'imported' as const, importedOpportunityId: String(result.opportunity_id) }
            : o
        ))
      );
      toast.success('Oportunidade importada', {
        action: {
          label: 'Ver Oportunidade →',
          onClick: () => navigate(`/opportunities/${result.opportunity_id}`),
        },
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao importar oportunidade';
      setError(message);
      toast.error(message);
    } finally {
      setBusyOpportunityIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleIgnoreOpportunity = async (id: string) => {
    setBusyOpportunityIds((prev) => new Set(prev).add(id));
    setError(null);
    try {
      await apiIgnoreScrapedOpportunity(Number(id));
      setOpportunities((prev) =>
        prev.map((o) => (o.id === id ? { ...o, status: 'ignored' as const } : o))
      );
      toast.success('Oportunidade ignorada');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao ignorar oportunidade';
      setError(message);
      toast.error(message);
    } finally {
      setBusyOpportunityIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Web Scraping</h1>
          <p className="text-muted-foreground text-sm">Monitorize fontes de oportunidades internacionais (UN, Banco Mundial, UE, etc.).</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refreshAll()} disabled={loading}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Atualizar
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading ? (
        <div className="py-12 text-center text-muted-foreground">Carregando...</div>
      ) : (
        <>
          <StatsCards sources={sources} stats={stats} />

          <Tabs defaultValue="sources" className="space-y-4">
            <TabsList className="grid w-full grid-cols-2 md:grid-cols-3">
              <TabsTrigger value="sources" className="flex items-center gap-1.5"><Globe className="h-4 w-4" />Fontes</TabsTrigger>
              <TabsTrigger value="opportunities" className="flex items-center gap-1.5"><Layers className="h-4 w-4" />Oportunidades</TabsTrigger>
              <TabsTrigger value="jobs" className="flex items-center gap-1.5"><Activity className="h-4 w-4" />Historico de Jobs</TabsTrigger>
            </TabsList>

            <TabsContent value="sources" className="space-y-4">
              <SourcesTab
                sources={sources}
                editingSource={editingSource}
                runningSourceIds={runningSourceIds}
                savingSource={savingSource}
                onAdd={() => setShowSourceModal(true)}
                onToggle={handleToggleSource}
                onRun={handleRunSource}
                onEdit={setEditingSource}
                onCancelEdit={() => setEditingSource(null)}
                onSaveEdit={handleSaveSource}
              />
            </TabsContent>
            <TabsContent value="opportunities" className="space-y-4">
              <OpportunitiesTab
                opportunities={opportunities}
                busyOpportunityIds={busyOpportunityIds}
                page={opportunitiesPage}
                totalCount={opportunitiesTotalCount}
                pageSize={PAGE_SIZE}
                onImport={handleImportOpportunity}
                onIgnore={handleIgnoreOpportunity}
                onView={handleViewOpportunity}
                onPageChange={handlePageChange}
              />
            </TabsContent>
            <TabsContent value="jobs" className="space-y-4">
              <JobLogsTab jobs={jobs} sources={sources} />
            </TabsContent>
          </Tabs>
        </>
      )}

      <AddScrapingSourceModal open={showSourceModal} onClose={() => setShowSourceModal(false)} onAdd={handleAddSource} />
      <OpportunityDetailModal
        detail={viewingDetail}
        loading={loadingDetail}
        onClose={() => { setViewingDetail(null); setLoadingDetail(false); }}
        onImport={handleImportOpportunity}
        isBusy={viewingDetail ? busyOpportunityIds.has(String(viewingDetail.id)) : false}
      />
    </div>
  );
}
