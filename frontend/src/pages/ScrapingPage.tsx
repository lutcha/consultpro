// ============================================
// SCRAPING PAGE — Web Scraping / Fontes
// ============================================

import { useState } from 'react';
import {
  Globe, Play, Pause, Settings, Plus, Search, RefreshCw,
  CheckCircle2, AlertTriangle, Clock, Download, ArrowRight,
  Activity, Zap, Bot, ChevronDown, ChevronUp,
  BarChart3, Layers, Eye, DollarSign,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { AddScrapingSourceModal } from '@/components/modals';
import type { ScrapingSource, ScrapedOpportunity, ScrapingJob } from '@/types';

// ============================================================
// INITIAL MOCK DATA
// ============================================================
const initialSources: ScrapingSource[] = [
  {
    id: 'src-1', name: 'Tenders Electronic Daily (TED)', organization: 'TED', url: 'https://ted.europa.eu',
    sourceType: 'portal', status: 'active', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-29T10:30:00Z'), nextScrapeAt: new Date('2025-04-29T18:00:00Z'),
    filters: { keywords: ['consultoria', 'desenvolvimento', 'saude', 'educacao'], countries: ['PT', 'AO', 'MZ', 'CV'] } as any,
    newOpportunitiesCount: 3, totalOpportunitiesCount: 1247, successRate: 94,
  } as any,
  {
    id: 'src-2', name: 'UNDP Procurement', organization: 'UNDP', url: 'https://procurement-notices.undp.org',
    sourceType: 'portal', status: 'active', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-29T09:15:00Z'), nextScrapeAt: new Date('2025-04-29T15:00:00Z'),
    filters: { keywords: ['health', 'governance', 'climate', 'gender'] } as any,
    newOpportunitiesCount: 2, totalOpportunitiesCount: 892, successRate: 97,
  } as any,
  {
    id: 'src-3', name: 'World Bank Projects', organization: 'World Bank', url: 'https://projects.worldbank.org',
    sourceType: 'portal', status: 'active', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-29T08:00:00Z'), nextScrapeAt: new Date('2025-04-29T14:00:00Z'),
    filters: { keywords: ['consulting services', 'technical assistance'] } as any,
    newOpportunitiesCount: 1, totalOpportunitiesCount: 534, successRate: 91,
  } as any,
  {
    id: 'src-4', name: 'DevBusiness (AfDB)', organization: 'AfDB', url: 'https://www.devbusiness.com',
    sourceType: 'portal', status: 'error', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-28T22:00:00Z'), nextScrapeAt: new Date('2025-04-29T20:00:00Z'),
    filters: { keywords: ['consultancy', 'feasibility', 'M&E'] } as any,
    newOpportunitiesCount: 0, totalOpportunitiesCount: 312, successRate: 72,
    errorMessage: 'Rate limit exceeded at 22:15',
  } as any,
  {
    id: 'src-5', name: 'Portal BASE (Portugal)', organization: 'BASE', url: 'https://www.base.gov.pt',
    sourceType: 'portal', status: 'active', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-29T07:00:00Z'), nextScrapeAt: new Date('2025-04-29T13:00:00Z'),
    filters: { keywords: ['consultoria', 'formacao', 'avaliacao'] } as any,
    newOpportunitiesCount: 2, totalOpportunitiesCount: 678, successRate: 96,
  } as any,
  {
    id: 'src-6', name: 'UNICEF Consultancies', organization: 'UNICEF', url: 'https://www.unicef.org/about/employment',
    sourceType: 'portal', status: 'paused', scrapeFrequency: 'daily',
    lastScrapedAt: new Date('2025-04-25T10:00:00Z'), nextScrapeAt: undefined,
    filters: { keywords: ['consultant', 'advisor', 'specialist'] } as any,
    newOpportunitiesCount: 0, totalOpportunitiesCount: 245, successRate: 88,
    errorMessage: 'Site structure changed - requires manual update',
  } as any,
];

const initialOpportunities: ScrapedOpportunity[] = [
  {
    id: 'opp-1', sourceId: 'src-1', externalUrl: 'https://ted.europa.eu/notice/12345',
    title: 'Servicos de Consultoria para Avaliacao de Programa de Saude Publica',
    organization: 'Ministerio da Saude de Mocambique', client: 'Ministerio da Saude de Mocambique',
    deadline: new Date('2025-05-15'), status: 'new', location: 'Maputo, Mocambique',
    sector: 'Saude', country: 'MZ', currency: 'EUR', value: 625000,
    description: 'Avaliacao de impacto do Programa Nacional de Saude 2020-2024.',
    aiSummary: 'Oportunidade de consultoria em avaliacao de programa de saude publica em Mocambique. Requisitos principais: experiencia em M&E (min. 8 anos), conhecimento do contexto lusofono. Prazo apertado (15 dias).',
    deadlineAlert: true,
  } as any,
  {
    id: 'opp-2', sourceId: 'src-2', externalUrl: 'https://procurement-notices.undp.org/notice/67890',
    title: 'Consultor(a) Senior em Governanca e Fortalecimento Institucional',
    organization: 'UNDP Angola', client: 'UNDP Angola',
    deadline: new Date('2025-05-20'), status: 'imported', location: 'Luanda, Angola',
    sector: 'Governanca', country: 'AO', currency: 'USD', value: 150000,
    description: 'Apoio tecnico ao Ministerio da Administracao Territorial.',
    aiSummary: 'Consultoria UNDP em governanca para Angola. Foco em reforma administrativa. Compativel com expertise da consultora Ana Silva.',
    deadlineAlert: false,
    importedOpportunityId: 'opp-imported-1',
  } as any,
  {
    id: 'opp-3', sourceId: 'src-3', externalUrl: 'https://projects.worldbank.org/notice/11223',
    title: 'Especialista em Sistemas de Saude',
    organization: 'World Bank Group', client: 'World Bank Group',
    deadline: new Date('2025-06-01'), status: 'new', location: 'Sao Tome e Principe',
    sector: 'Saude', country: 'ST', currency: 'USD', value: 100000,
    description: 'Consultor individual para fortalecimento do sistema de saude.',
    aiSummary: 'Consultoria individual do Banco Mundial em Sao Tome e Principe. Oportunidade interessante mas prazo longo.',
    deadlineAlert: false,
  } as any,
  {
    id: 'opp-4', sourceId: 'src-5', externalUrl: 'https://www.base.gov.pt/notice/33445',
    title: 'Servicos de Formacao em Avaliacao de Projetos',
    organization: 'Agencia para o Desenvolvimento e Coesao', client: 'ADCS',
    deadline: new Date('2025-05-10'), status: 'ignored', location: 'Lisboa, Portugal',
    sector: 'Formacao', country: 'PT', currency: 'EUR', value: 55000,
    description: 'Formacao de 30 tecnicos em avaliacao de projetos.',
    aiSummary: 'Formacao em avaliacao de projetos. Menor alinhamento com foco atual da empresa.',
    deadlineAlert: false,
  } as any,
  {
    id: 'opp-5', sourceId: 'src-1', externalUrl: 'https://ted.europa.eu/notice/55667',
    title: 'Consultoria em Desenvolvimento Rural e Seguranca Alimentar',
    organization: 'FAO Cabo Verde', client: 'FAO Cabo Verde',
    deadline: new Date('2025-05-30'), status: 'new', location: 'Praia, Cabo Verde',
    sector: 'Agricultura', country: 'CV', currency: 'EUR', value: 250000,
    description: 'Elaboracao de estudo de viabilidade para programa de desenvolvimento rural.',
    aiSummary: 'Consultoria FAO em desenvolvimento rural em Cabo Verde. Grande oportunidade com budget substancial. Marcada para revisao pela equipa de negocios.',
    deadlineAlert: true,
  } as any,
];

const initialJobs: ScrapingJob[] = [
  {
    id: 'job-1', sourceId: 'src-1', status: 'completed',
    startedAt: new Date('2025-04-29T10:30:00Z'), completedAt: new Date('2025-04-29T10:45:00Z'),
    itemsFound: 12, itemsNew: 3, itemsImported: 1, errorLog: '', executedBy: 'system',
  } as any,
  {
    id: 'job-2', sourceId: 'src-2', status: 'completed',
    startedAt: new Date('2025-04-29T09:15:00Z'), completedAt: new Date('2025-04-29T09:28:00Z'),
    itemsFound: 8, itemsNew: 2, itemsImported: 1, errorLog: '', executedBy: 'system',
  } as any,
  {
    id: 'job-3', sourceId: 'src-4', status: 'failed',
    startedAt: new Date('2025-04-28T22:00:00Z'), completedAt: new Date('2025-04-28T22:15:00Z'),
    itemsFound: 0, itemsNew: 0, itemsImported: 0, errorLog: 'Rate limit exceeded after 15 requests. Retry scheduled.', executedBy: 'system',
  } as any,
  {
    id: 'job-4', sourceId: 'src-5', status: 'running',
    startedAt: new Date('2025-04-29T13:00:00Z'), completedAt: undefined,
    itemsFound: 0, itemsNew: 0, itemsImported: 0, errorLog: '', executedBy: 'system',
  } as any,
];

// ============================================================
// COMPONENTS
// ============================================================
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
}

function StatsCards({ sources }: StatsCardsProps) {
  const activeSources = sources.filter((s) => s.status === 'active').length;
  const totalOportunidades = sources.reduce((acc, s) => acc + s.totalOpportunitiesCount, 0);
  const avgSuccess = sources.length > 0
    ? Math.round(sources.reduce((acc, s) => acc + s.successRate, 0) / sources.length)
    : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4 flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-muted text-blue-600"><Globe className="h-5 w-5" /></div>
          <div><p className="text-2xl font-bold">{sources.length}</p><p className="text-xs text-muted-foreground">Fontes Totais</p></div>
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

// ============================================================
// TAB: SOURCES
// ============================================================
interface SourcesTabProps {
  sources: ScrapingSource[];
  onAdd: () => void;
  onToggle: (id: string) => void;
}

function SourcesTab({ sources, onAdd, onToggle }: SourcesTabProps) {
  const [search, setSearch] = useState('');
  const filtered = sources.filter((s) => s.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar fontes..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Button size="sm" onClick={onAdd}><Plus className="h-4 w-4 mr-1" />Nova Fonte</Button>
      </div>

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
                {(source as any).lastScrapedAt ? `Ultimo scrape: ${new Date((source as any).lastScrapedAt).toLocaleDateString('pt-PT')}` : 'Nunca scrapeado'}
              </div>

              {(source as any).errorMessage && (
                <div className="flex items-start gap-1.5 text-xs text-red-600 bg-red-50 p-2 rounded">
                  <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                  <span>{(source as any).errorMessage}</span>
                </div>
              )}

              <div className="flex gap-2">
                <Button size="sm" variant="outline" className="h-8 text-xs flex-1" onClick={() => onToggle(source.id)}>
                  {source.status === 'paused' ? <><Play className="h-3.5 w-3.5 mr-1" />Iniciar</> : <><Pause className="h-3.5 w-3.5 mr-1" />Pausar</>}
                </Button>
                <Button size="sm" variant="outline" className="h-8 text-xs flex-1"><RefreshCw className="h-3.5 w-3.5 mr-1" />Executar</Button>
                <Button size="sm" variant="outline" className="h-8 text-xs px-2"><Settings className="h-3.5 w-3.5" /></Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          Nenhuma fonte encontrada. Adicione uma nova fonte para começar.
        </div>
      )}
    </div>
  );
}

// ============================================================
// TAB: OPPORTUNITIES
// ============================================================
interface OpportunitiesTabProps {
  opportunities: ScrapedOpportunity[];
  onImport: (id: string) => void;
  onIgnore: (id: string) => void;
}

function OpportunitiesTab({ opportunities, onImport, onIgnore }: OpportunitiesTabProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = opportunities.filter((o) => {
    const matchesSearch = o.title.toLowerCase().includes(search.toLowerCase()) || o.organization.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = !statusFilter || o.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

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

      <div className="space-y-3">
        {filtered.map((opp) => {
          const isExpanded = expanded === opp.id;
          return (
            <Card key={opp.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-semibold text-sm">{opp.title}</h4>
                      <OpportunityStatusBadge status={opp.status} />
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{opp.organization} — {(opp as any).location}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" />Prazo: {opp.deadline ? new Date(opp.deadline).toLocaleDateString('pt-PT') : '-'}</span>
                      <span className="flex items-center gap-1"><BarChart3 className="h-3 w-3" />{opp.sector}</span>
                      {opp.value && <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />{opp.value.toLocaleString('pt-PT')} {opp.currency}</span>}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" className="h-7 text-xs"><Eye className="h-3.5 w-3.5" /></Button>
                    <Button size="sm" variant="outline" className="h-7 text-xs"><Download className="h-3.5 w-3.5" /></Button>
                    {opp.status === 'new' && (
                      <Button size="sm" className="h-7 text-xs" onClick={() => onImport(opp.id)}>
                        <ArrowRight className="h-3.5 w-3.5 mr-1" />Importar
                      </Button>
                    )}
                    {opp.status === 'new' && (
                      <Button size="sm" variant="ghost" className="h-7 text-xs" onClick={() => onIgnore(opp.id)}>
                        Ignorar
                      </Button>
                    )}
                  </div>
                </div>

                {isExpanded && opp.aiSummary && (
                  <div className="mt-3 pt-3 border-t space-y-3">
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
                    {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" /> Recolher</> : <><ChevronDown className="h-3 w-3 mr-1" /> Ver Resumo AI</>}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
      {filtered.length === 0 && <div className="text-center py-12 text-muted-foreground">Nenhuma oportunidade encontrada.</div>}
    </div>
  );
}

// ============================================================
// TAB: JOB LOGS
// ============================================================
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
                      {job.startedAt ? new Date(job.startedAt).toLocaleString('pt-PT') : '-'}
                      {job.completedAt && job.startedAt ? ` (${Math.floor((new Date(job.completedAt).getTime() - new Date(job.startedAt).getTime()) / 60000)}m)` : ''}
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

// ============================================================
// MAIN PAGE
// ============================================================
export function ScrapingPage() {
  const [sources, setSources] = useState<ScrapingSource[]>(initialSources);
  const [opportunities, setOpportunities] = useState<ScrapedOpportunity[]>(initialOpportunities);
  const [jobs] = useState<ScrapingJob[]>(initialJobs);
  const [showSourceModal, setShowSourceModal] = useState(false);

  const handleAddSource = (data: any) => {
    const newSource: ScrapingSource = {
      id: `src-${Date.now()}`,
      name: data.name,
      organization: data.organization,
      url: data.url,
      sourceType: (data.source_type || 'portal') as any,
      status: 'active',
      scrapeFrequency: (data.scrape_frequency || 'daily') as any,
      filters: {},
      newOpportunitiesCount: 0,
      totalOpportunitiesCount: 0,
      successRate: 100,
    };
    setSources((prev) => [...prev, newSource]);
  };

  const handleToggleSource = (id: string) => {
    setSources((prev) =>
      prev.map((s) => {
        if (s.id !== id) return s;
        const nextStatus = s.status === 'active' ? 'paused' : 'active';
        return { ...s, status: nextStatus };
      })
    );
  };

  const handleImportOpportunity = (id: string) => {
    setOpportunities((prev) =>
      prev.map((o) => (o.id === id ? { ...o, status: 'imported' as const } : o))
    );
  };

  const handleIgnoreOpportunity = (id: string) => {
    setOpportunities((prev) =>
      prev.map((o) => (o.id === id ? { ...o, status: 'ignored' as const } : o))
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Web Scraping</h1>
        <p className="text-muted-foreground text-sm">Monitorize fontes de oportunidades internacionais (UN, Banco Mundial, UE, etc.).</p>
      </div>

      <StatsCards sources={sources} />

      <Tabs defaultValue="sources" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-3">
          <TabsTrigger value="sources" className="flex items-center gap-1.5"><Globe className="h-4 w-4" />Fontes</TabsTrigger>
          <TabsTrigger value="opportunities" className="flex items-center gap-1.5"><Layers className="h-4 w-4" />Oportunidades</TabsTrigger>
          <TabsTrigger value="jobs" className="flex items-center gap-1.5"><Activity className="h-4 w-4" />Histórico de Jobs</TabsTrigger>
        </TabsList>

        <TabsContent value="sources" className="space-y-4">
          <SourcesTab sources={sources} onAdd={() => setShowSourceModal(true)} onToggle={handleToggleSource} />
        </TabsContent>
        <TabsContent value="opportunities" className="space-y-4">
          <OpportunitiesTab opportunities={opportunities} onImport={handleImportOpportunity} onIgnore={handleIgnoreOpportunity} />
        </TabsContent>
        <TabsContent value="jobs" className="space-y-4">
          <JobLogsTab jobs={jobs} sources={sources} />
        </TabsContent>
      </Tabs>

      <AddScrapingSourceModal open={showSourceModal} onClose={() => setShowSourceModal(false)} onAdd={handleAddSource} />
    </div>
  );
}
