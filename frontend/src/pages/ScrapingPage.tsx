// ============================================
// SCRAPING PAGE - Web Scraping / Fontes
// ============================================

import { useCallback, useEffect, useState } from 'react';
import {
  Globe, Play, Pause, Settings, Plus, Search, RefreshCw,
  CheckCircle2, AlertTriangle, Clock, Download, ArrowRight,
  Activity, Zap, Bot, ChevronDown, ChevronUp,
  BarChart3, Layers, Eye, DollarSign, ExternalLink,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AddScrapingSourceModal } from '@/components/modals';
import {
  apiCreateScrapingSource,
  apiGetScrapedOpportunities,
  apiGetScrapingJobs,
  apiGetScrapingSources,
  apiGetScrapingStats,
  apiIgnoreScrapedOpportunity,
  apiImportScrapedOpportunity,
  apiImportReadyScrapedOpportunities,
  apiRunScrapingSource,
  apiToggleScrapingSource,
  apiUpdateScrapingSource,
  type ApiScrapedOpportunity,
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
  ready_to_import?: number;
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
    sourceCategory: source.source_category || source.source_type,
    scraperKind: source.scraper_kind as ScrapingSource['scraperKind'],
    scraperClass: source.scraper_class,
  };
}

function mapOpportunity(opp: ApiScrapedOpportunity): ScrapedOpportunity {
  const score = opp.data_quality_score ? Number(opp.data_quality_score) : undefined;
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
    importedOpportunityId: opp.imported_opportunity ? String(opp.imported_opportunity) : undefined,
    cvEligible: Boolean(opp.cv_eligible),
    dataQualityScore: score !== undefined && score <= 1 ? Math.round(score * 100) : score,
    sourceName: opp.source_name,
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

function formatSourceCategory(category: string): string {
  const labels: Record<string, string> = {
    multilateral: 'Multilaterais',
    bilateral: 'Bilaterais',
    grants: 'Grants',
    aggregator: 'Agregadores',
    national: 'Nacionais',
    eu_grants: 'UE / Grants',
    bilateral_procurement: 'Bilaterais / Procurement',
    development_bank: 'Bancos de Desenvolvimento',
    un_agency: 'Agencias ONU',
    portal: 'Portais',
    api: 'APIs',
    rss: 'RSS',
    other: 'Outras',
  };
  return labels[category] || category.replace(/_/g, ' ');
}

function formatScraperKind(kind: string): string {
  const labels: Record<string, string> = {
    dedicated: 'Scraper dedicado',
    generic: 'Scraper generico',
    api: 'API',
    rss: 'RSS',
    paused: 'Pausada',
  };
  return labels[kind] || kind;
}

function isReadyToImport(opp: ScrapedOpportunity): boolean {
  return opp.status === 'new' && Boolean(opp.cvEligible) && !opp.importedOpportunityId && dataQualityScore(opp) >= 45;
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
    rejected: { label: 'Rejeitada', class: 'bg-red-100 text-red-700 border-red-200' },
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
  const readyToImport = stats?.ready_to_import ?? 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
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
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-emerald-600"><CheckCircle2 className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{readyToImport}</p><p className="text-xs text-muted-foreground">Prontas a Importar</p></div>
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
  const [categoryFilter, setCategoryFilter] = useState('');
  const [kindFilter, setKindFilter] = useState('');
  const [editForm, setEditForm] = useState({
    name: '',
    url: '',
    scrape_frequency: 'daily',
    status: 'active',
  });
  const categories = Array.from(new Set(sources.map((s) => s.sourceCategory || s.sourceType).filter(Boolean))).sort();
  const kinds = Array.from(new Set(sources.map((s) => s.scraperKind || 'generic').filter(Boolean))).sort();
  const filtered = sources.filter((s) => {
    const matchesSearch = s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.organization.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !categoryFilter || (s.sourceCategory || s.sourceType) === categoryFilter;
    const matchesKind = !kindFilter || (s.scraperKind || 'generic') === kindFilter;
    return matchesSearch && matchesCategory && matchesKind;
  });
  const groupedSources = filtered.reduce<Record<string, ScrapingSource[]>>((acc, source) => {
    const key = source.sourceCategory || source.sourceType || 'other';
    acc[key] = acc[key] || [];
    acc[key].push(source);
    return acc;
  }, {});

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
        <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
          <option value="">Todas categorias</option>
          {categories.map((category) => <option key={category} value={category}>{formatSourceCategory(category)}</option>)}
        </select>
        <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={kindFilter} onChange={(e) => setKindFilter(e.target.value)}>
          <option value="">Todos tipos</option>
          {kinds.map((kind) => <option key={kind} value={kind}>{formatScraperKind(kind)}</option>)}
        </select>
        <Button size="sm" onClick={onAdd}><Plus className="h-4 w-4 mr-1" />Nova Fonte</Button>
      </div>

      {editingSource && (
        <Card>
          <CardContent className="p-4 space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Input value={editForm.name} onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))} placeholder="Nome" />
              <Input value={editForm.url} onChange={(e) => setEditForm((prev) => ({ ...prev, url: e.target.value }))} placeholder="URL" />
              <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={editForm.scrape_frequency} onChange={(e) => setEditForm((prev) => ({ ...prev, scrape_frequency: e.target.value }))}>
                <option value="hourly">Por Hora</option>
                <option value="daily">Diario</option>
                <option value="weekly">Semanal</option>
              </select>
              <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={editForm.status} onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))}>
                <option value="active">Ativo</option>
                <option value="paused">Pausado</option>
                <option value="error">Erro</option>
                <option value="disabled">Desativado</option>
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={onCancelEdit} disabled={savingSource}>Cancelar</Button>
              <Button size="sm" onClick={() => onSaveEdit(editingSource.id, editForm)} disabled={savingSource}>
                {savingSource ? 'A guardar...' : 'Guardar'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-5">
        {Object.entries(groupedSources).map(([category, group]) => (
          <div key={category} className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">{formatSourceCategory(category)}</h3>
              <span className="text-xs text-muted-foreground">{group.length} fontes</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {group.map((source) => (
                <Card key={source.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-sm">{source.name}</h4>
                    <SourceStatusBadge status={source.status} />
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded border bg-muted">{formatScraperKind(source.scraperKind || 'generic')}</span>
                    {source.scraperClass && <span className="text-xs text-muted-foreground">{source.scraperClass}</span>}
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
          </div>
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
// TAB: OPPORTUNITIES
// ============================================
interface OpportunitiesTabProps {
  opportunities: ScrapedOpportunity[];
  busyOpportunityIds: Set<string>;
  importingReady: boolean;
  onImport: (id: string) => void;
  onImportReady: () => void;
  onIgnore: (id: string) => void;
}

function dataQualityScore(opp: ScrapedOpportunity): number {
  if (opp.dataQualityScore !== undefined) {
    return Math.round(opp.dataQualityScore);
  }
  let score = 0;
  if (opp.title && opp.title.length > 10 && opp.title.length < 300) score += 30;
  if (opp.organization) score += 15;
  if (opp.country) score += 15;
  if (opp.sector) score += 15;
  if (opp.deadline) score += 15;
  if (opp.value) score += 10;
  return score;
}

function DataQualityBadge({ score }: { score: number }) {
  const cls = score >= 75 ? 'bg-emerald-100 text-emerald-700' : score >= 45 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700';
  const label = score >= 75 ? 'Alta' : score >= 45 ? 'Média' : 'Baixa';
  return <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${cls}`}>{label} ({score}%)</span>;
}

function OpportunitiesTab({ opportunities, busyOpportunityIds, importingReady, onImport, onImportReady, onIgnore }: OpportunitiesTabProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [sectorFilter, setSectorFilter] = useState<string>('');
  const [countryFilter, setCountryFilter] = useState<string>('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [qualityMin, setQualityMin] = useState<number>(0);

  const sectors = Array.from(new Set(opportunities.map((o) => o.sector).filter(Boolean))) as string[];
  const countries = Array.from(new Set(opportunities.map((o) => o.country).filter(Boolean))) as string[];

  const filtered = opportunities.filter((o) => {
    const title = o.title || '';
    const matchesSearch = title.toLowerCase().includes(search.toLowerCase()) ||
      (o.organization || '').toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || (statusFilter === 'ready' ? isReadyToImport(o) : o.status === statusFilter);
    const matchesSector = !sectorFilter || o.sector === sectorFilter;
    const matchesCountry = !countryFilter || o.country === countryFilter;
    const matchesQuality = qualityMin === 0 || dataQualityScore(o) >= qualityMin;
    // filter out navigation garbage (very short or very long titles that are not real opportunities)
    const titleOk = title.length >= 8 && title.length <= 400;
    return matchesSearch && matchesStatus && matchesSector && matchesCountry && matchesQuality && titleOk;
  });

  const newCount = filtered.filter((o) => o.status === 'new').length;
  const readyCount = opportunities.filter(isReadyToImport).length;

  return (
    <div className="space-y-4">
      {/* filters row */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Pesquisar oportunidades..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
          </div>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">Todos Status</option>
            <option value="ready">Prontas para importar</option>
            <option value="new">Novas</option>
            <option value="imported">Importadas</option>
            <option value="ignored">Ignoradas</option>
            <option value="expired">Expiradas</option>
            <option value="rejected">Rejeitadas</option>
          </select>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={sectorFilter} onChange={(e) => setSectorFilter(e.target.value)}>
            <option value="">Todos Sectores</option>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)}>
            <option value="">Todos Países</option>
            {countries.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={qualityMin} onChange={(e) => setQualityMin(Number(e.target.value))}>
            <option value={0}>Toda Qualidade</option>
            <option value={75}>Alta Qualidade</option>
            <option value={45}>Média+</option>
          </select>
          <Button size="sm" className="h-9" onClick={onImportReady} disabled={importingReady || readyCount === 0}>
            <ArrowRight className="h-4 w-4 mr-1" />
            {importingReady ? 'A importar...' : `Importar elegiveis (${readyCount})`}
          </Button>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{filtered.length} oportunidades {newCount > 0 && <span className="text-blue-600 font-medium">· {newCount} novas</span>}</span>
          {(statusFilter || sectorFilter || countryFilter || qualityMin > 0 || search) && (
            <button className="text-primary hover:underline" onClick={() => { setStatusFilter(''); setSectorFilter(''); setCountryFilter(''); setQualityMin(0); setSearch(''); }}>
              Limpar filtros
            </button>
          )}
        </div>
      </div>

      <div className="space-y-2">
        {filtered.map((opp) => {
          const isExpanded = expanded === opp.id;
          const isBusy = busyOpportunityIds.has(opp.id);
          const quality = dataQualityScore(opp);
          const titleTruncated = opp.title.length > 120 ? opp.title.slice(0, 120) + '…' : opp.title;
          return (
            <Card key={opp.id} className={`transition-shadow hover:shadow-md ${opp.status === 'imported' ? 'opacity-60' : ''}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start gap-2 flex-wrap">
                      <h4 className="font-semibold text-sm leading-snug flex-1">{titleTruncated}</h4>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <OpportunityStatusBadge status={opp.status} />
                        <DataQualityBadge score={quality} />
                        {isReadyToImport(opp) && <span className="text-xs px-1.5 py-0.5 rounded font-medium bg-emerald-100 text-emerald-700">Pronta</span>}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-xs text-muted-foreground">
                      {opp.organization && <span className="font-medium text-foreground">{opp.organization}</span>}
                      {opp.sourceName && <span>{opp.sourceName}</span>}
                      {opp.country && <span className="flex items-center gap-1">🌍 {opp.country}</span>}
                      {opp.sector && <span className="flex items-center gap-1"><BarChart3 className="h-3 w-3" />{opp.sector}</span>}
                      {opp.deadline && <span className="flex items-center gap-1"><Clock className="h-3 w-3" />Prazo: {opp.deadline.toLocaleDateString('pt-PT')}</span>}
                      {opp.value && opp.value > 0 && <span className="flex items-center gap-1 text-emerald-700 font-medium"><DollarSign className="h-3 w-3" />{opp.value.toLocaleString('pt-PT')} {opp.currency}</span>}
                    </div>
                  </div>

                  <div className="flex flex-col gap-1 shrink-0">
                    <div className="flex gap-1">
                      {/* Eye → open source URL */}
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" title="Ver fonte original" asChild>
                        <a href={opp.externalUrl} target="_blank" rel="noreferrer"><Eye className="h-3.5 w-3.5" /></a>
                      </Button>
                      {/* Download = external link */}
                      <Button size="sm" variant="outline" className="h-7 w-7 p-0" title="Abrir URL externo" asChild>
                        <a href={opp.externalUrl} target="_blank" rel="noreferrer"><Download className="h-3.5 w-3.5" /></a>
                      </Button>
                    </div>
                    {opp.status === 'new' && (
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          className="h-7 text-xs px-2 bg-primary"
                          onClick={() => onImport(opp.id)}
                          disabled={isBusy}
                          title="Importar para Oportunidades e iniciar Go/No-Go"
                        >
                          {isBusy ? '…' : <><ArrowRight className="h-3 w-3 mr-1" />Importar</>}
                        </Button>
                        <Button size="sm" variant="ghost" className="h-7 text-xs px-2" onClick={() => onIgnore(opp.id)} disabled={isBusy}>
                          Ignorar
                        </Button>
                      </div>
                    )}
                    {opp.status === 'imported' && (
                      <div className="flex flex-col items-end gap-1">
                        <span className="text-xs text-emerald-600 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" />Importada</span>
                        {opp.importedOpportunityId && (
                          <Button size="sm" variant="ghost" className="h-7 text-xs px-2" asChild>
                            <a href={`/opportunities/${opp.importedOpportunityId}`}>
                              <ExternalLink className="h-3 w-3 mr-1" />Ver oportunidade
                            </a>
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Expandable: description + AI summary */}
                {isExpanded && (
                  <div className="mt-3 pt-3 border-t space-y-2">
                    {opp.description && opp.description.length > 30 && (
                      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">{opp.description}</p>
                    )}
                    {opp.aiSummary && (
                      <div className="p-3 bg-blue-50/50 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <Bot className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-blue-900">Resumo AI</span>
                        </div>
                        <p className="text-sm text-blue-800">{opp.aiSummary}</p>
                      </div>
                    )}
                  </div>
                )}

                {(opp.aiSummary || (opp.description && opp.description.length > 30)) && (
                  <Button variant="ghost" size="sm" className="w-full mt-2 h-7 text-xs" onClick={() => setExpanded(isExpanded ? null : opp.id)}>
                    {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" />Recolher</> : <><ChevronDown className="h-3 w-3 mr-1" />Ver Detalhes</>}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      {filtered.length === 0 && (
        <div className="text-center py-16 text-muted-foreground space-y-2">
          <Layers className="h-10 w-10 mx-auto opacity-30" />
          <p className="font-medium">Nenhuma oportunidade encontrada</p>
          <p className="text-xs">Ajusta os filtros ou executa um scraping.</p>
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
export function ScrapingPage() {
  const [sources, setSources] = useState<ScrapingSource[]>([]);
  const [opportunities, setOpportunities] = useState<ScrapedOpportunity[]>([]);
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [stats, setStats] = useState<ScrapingStats | null>(null);
  const [showSourceModal, setShowSourceModal] = useState(false);
  const [editingSource, setEditingSource] = useState<ScrapingSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningSourceIds, setRunningSourceIds] = useState<Set<string>>(new Set());
  const [busyOpportunityIds, setBusyOpportunityIds] = useState<Set<string>>(new Set());
  const [savingSource, setSavingSource] = useState(false);
  const [importingReady, setImportingReady] = useState(false);

  const refreshSources = useCallback(async () => {
    const response = await apiGetScrapingSources();
    setSources(response.results.map(mapSource));
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sourcesResponse, opportunitiesResponse, jobsResponse, statsResponse] = await Promise.all([
        apiGetScrapingSources(),
        apiGetScrapedOpportunities(),
        apiGetScrapingJobs(),
        apiGetScrapingStats(),
      ]);
      setSources(sourcesResponse.results.map(mapSource));
      setOpportunities(opportunitiesResponse.results.map(mapOpportunity));
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
      await refreshSources();
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
      await refreshSources();
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

  const handleImportOpportunity = async (id: string) => {
    setBusyOpportunityIds((prev) => new Set(prev).add(id));
    setError(null);
    try {
      const response = await apiImportScrapedOpportunity(Number(id));
      setOpportunities((prev) =>
        prev.map((o) => (
          o.id === id
            ? { ...o, status: 'imported' as const, importedOpportunityId: String(response.opportunity_id) }
            : o
        ))
      );
      toast.success('Oportunidade importada');
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

  const handleImportReadyOpportunities = async () => {
    setImportingReady(true);
    setError(null);
    try {
      const response = await apiImportReadyScrapedOpportunities(50);
      toast.success(`${response.imported_count} oportunidades importadas`);
      await refreshAll();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao importar oportunidades elegiveis';
      setError(message);
      toast.error(message);
    } finally {
      setImportingReady(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Web Scraping</h1>
          <p className="text-muted-foreground text-sm">Monitorize fontes de oportunidades internacionais (UN, Banco Mundial, UE, etc.).</p>
        </div>
        <Button variant="outline" size="sm" onClick={refreshAll} disabled={loading}>
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
                importingReady={importingReady}
                onImport={handleImportOpportunity}
                onImportReady={handleImportReadyOpportunities}
                onIgnore={handleIgnoreOpportunity}
              />
            </TabsContent>
            <TabsContent value="jobs" className="space-y-4">
              <JobLogsTab jobs={jobs} sources={sources} />
            </TabsContent>
          </Tabs>
        </>
      )}

      <AddScrapingSourceModal open={showSourceModal} onClose={() => setShowSourceModal(false)} onAdd={handleAddSource} />
    </div>
  );
}
