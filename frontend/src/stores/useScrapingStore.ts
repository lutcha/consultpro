import { create } from 'zustand';
import type { ScrapingSource, ScrapedOpportunity, ScrapingJob } from '@/types';

// ── Mock seed data ──────────────────────────────────────────────────────────

const seedSources: ScrapingSource[] = [
  {
    id: 'src-1', name: 'Tenders Electronic Daily (TED)', organization: 'TED',
    url: 'https://ted.europa.eu', sourceType: 'portal', status: 'active',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-29T10:30:00Z'),
    nextScrapeAt: new Date('2025-04-29T18:00:00Z'),
    filters: { keywords: ['consultoria', 'desenvolvimento', 'saude', 'educacao'] },
    newOpportunitiesCount: 3, totalOpportunitiesCount: 1247, successRate: 94,
  } as ScrapingSource,
  {
    id: 'src-2', name: 'UNDP Procurement', organization: 'UNDP',
    url: 'https://procurement-notices.undp.org', sourceType: 'portal', status: 'active',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-29T09:15:00Z'),
    nextScrapeAt: new Date('2025-04-29T15:00:00Z'),
    filters: { keywords: ['health', 'governance', 'climate', 'gender'] },
    newOpportunitiesCount: 2, totalOpportunitiesCount: 892, successRate: 97,
  } as ScrapingSource,
  {
    id: 'src-3', name: 'World Bank Projects', organization: 'World Bank',
    url: 'https://projects.worldbank.org', sourceType: 'portal', status: 'active',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-29T08:00:00Z'),
    nextScrapeAt: new Date('2025-04-29T14:00:00Z'),
    filters: { keywords: ['consulting services', 'technical assistance'] },
    newOpportunitiesCount: 1, totalOpportunitiesCount: 534, successRate: 91,
  } as ScrapingSource,
  {
    id: 'src-4', name: 'DevBusiness (AfDB)', organization: 'AfDB',
    url: 'https://www.devbusiness.com', sourceType: 'portal', status: 'error',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-28T22:00:00Z'),
    nextScrapeAt: new Date('2025-04-29T20:00:00Z'),
    filters: { keywords: ['consultancy', 'feasibility', 'M&E'] },
    newOpportunitiesCount: 0, totalOpportunitiesCount: 312, successRate: 72,
    errorMessage: 'Rate limit exceeded at 22:15',
  } as ScrapingSource,
  {
    id: 'src-5', name: 'Portal BASE (Portugal)', organization: 'BASE',
    url: 'https://www.base.gov.pt', sourceType: 'portal', status: 'active',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-29T07:00:00Z'),
    nextScrapeAt: new Date('2025-04-29T13:00:00Z'),
    filters: { keywords: ['consultoria', 'formacao', 'avaliacao'] },
    newOpportunitiesCount: 2, totalOpportunitiesCount: 678, successRate: 96,
  } as ScrapingSource,
  {
    id: 'src-6', name: 'UNICEF Consultancies', organization: 'UNICEF',
    url: 'https://www.unicef.org/about/employment', sourceType: 'portal', status: 'paused',
    scrapeFrequency: 'daily', lastScrapedAt: new Date('2025-04-25T10:00:00Z'),
    filters: { keywords: ['consultant', 'advisor', 'specialist'] },
    newOpportunitiesCount: 0, totalOpportunitiesCount: 245, successRate: 88,
    errorMessage: 'Site structure changed - requires manual update',
  } as ScrapingSource,
];

const seedOpportunities: ScrapedOpportunity[] = [
  {
    id: 'opp-1', sourceId: 'src-1', externalUrl: 'https://ted.europa.eu/notice/12345',
    title: 'Servicos de Consultoria para Avaliacao de Programa de Saude Publica',
    organization: 'Ministerio da Saude de Mocambique', client: 'Ministerio da Saude de Mocambique',
    deadline: new Date('2025-05-15'), status: 'new', sector: 'Saude', country: 'MZ',
    currency: 'EUR', value: 625000,
    description: 'Avaliacao de impacto do Programa Nacional de Saude 2020-2024.',
    aiSummary: 'Oportunidade de consultoria em M&E de saude publica em Mocambique. Prazo apertado (15 dias).',
    deadlineAlert: true,
  } as ScrapedOpportunity,
  {
    id: 'opp-2', sourceId: 'src-2', externalUrl: 'https://procurement-notices.undp.org/notice/67890',
    title: 'Consultor(a) Senior em Governanca e Fortalecimento Institucional',
    organization: 'UNDP Angola', client: 'UNDP Angola',
    deadline: new Date('2025-05-20'), status: 'imported', sector: 'Governanca', country: 'AO',
    currency: 'USD', value: 150000,
    description: 'Apoio tecnico ao Ministerio da Administracao Territorial.',
    aiSummary: 'Consultoria UNDP em governanca para Angola. Foco em reforma administrativa.',
    deadlineAlert: false, importedOpportunityId: 'opp-imported-1',
  } as ScrapedOpportunity,
  {
    id: 'opp-3', sourceId: 'src-3', externalUrl: 'https://projects.worldbank.org/notice/11223',
    title: 'Especialista em Sistemas de Saude',
    organization: 'World Bank Group', client: 'World Bank Group',
    deadline: new Date('2025-06-01'), status: 'new', sector: 'Saude', country: 'ST',
    currency: 'USD', value: 100000,
    description: 'Consultor individual para fortalecimento do sistema de saude.',
    aiSummary: 'Consultoria Banco Mundial em Sao Tome e Principe. Prazo longo.',
    deadlineAlert: false,
  } as ScrapedOpportunity,
  {
    id: 'opp-4', sourceId: 'src-5', externalUrl: 'https://www.base.gov.pt/notice/33445',
    title: 'Servicos de Formacao em Avaliacao de Projetos',
    organization: 'Agencia para o Desenvolvimento e Coesao', client: 'ADCS',
    deadline: new Date('2025-05-10'), status: 'ignored', sector: 'Formacao', country: 'PT',
    currency: 'EUR', value: 55000,
    description: 'Formacao de 30 tecnicos em avaliacao de projetos.',
    aiSummary: 'Formacao em avaliacao de projetos. Menor alinhamento com foco atual.',
    deadlineAlert: false,
  } as ScrapedOpportunity,
  {
    id: 'opp-5', sourceId: 'src-1', externalUrl: 'https://ted.europa.eu/notice/55667',
    title: 'Consultoria em Desenvolvimento Rural e Seguranca Alimentar',
    organization: 'FAO Cabo Verde', client: 'FAO Cabo Verde',
    deadline: new Date('2025-05-30'), status: 'new', sector: 'Agricultura', country: 'CV',
    currency: 'EUR', value: 250000,
    description: 'Elaboracao de estudo de viabilidade para programa de desenvolvimento rural.',
    aiSummary: 'Consultoria FAO em Cabo Verde. Grande oportunidade com budget substancial.',
    deadlineAlert: false,
  } as ScrapedOpportunity,
];

const seedJobs: ScrapingJob[] = [
  {
    id: 'job-1', sourceId: 'src-1', status: 'completed',
    startedAt: new Date('2025-04-29T10:25:00Z'), completedAt: new Date('2025-04-29T10:32:00Z'),
    itemsFound: 18, itemsNew: 3, itemsImported: 0, executedBy: 'system',
  },
  {
    id: 'job-2', sourceId: 'src-2', status: 'completed',
    startedAt: new Date('2025-04-29T09:10:00Z'), completedAt: new Date('2025-04-29T09:17:00Z'),
    itemsFound: 22, itemsNew: 2, itemsImported: 1, executedBy: 'system',
  },
  {
    id: 'job-3', sourceId: 'src-4', status: 'failed',
    startedAt: new Date('2025-04-28T22:00:00Z'), completedAt: new Date('2025-04-28T22:01:00Z'),
    itemsFound: 0, itemsNew: 0, itemsImported: 0,
    errorLog: 'HTTP 429 — rate limit exceeded', executedBy: 'system',
  },
];

// ── Store ───────────────────────────────────────────────────────────────────

interface ScrapingState {
  sources: ScrapingSource[];
  opportunities: ScrapedOpportunity[];
  jobs: ScrapingJob[];
  isLoading: boolean;
  isScraping: boolean;
  error: string | null;
  statusFilter: string;
  sourceFilter: string;
  searchQuery: string;

  // Data fetchers (initialize from seed when backend is unavailable)
  fetchSources: () => Promise<void>;
  fetchOpportunities: () => Promise<void>;
  fetchJobs: () => Promise<void>;

  // Actions
  addSource: (source: Partial<ScrapingSource>) => void;
  toggleSourceStatus: (sourceId: string) => void;
  startScraping: (sourceId: string) => Promise<void>;
  runAllScrapes: () => Promise<void>;
  importOpportunity: (opportunityId: string) => void;
  ignoreOpportunity: (opportunityId: string) => void;

  // Filters
  updateFilters: (filters: { statusFilter?: string; sourceFilter?: string; searchQuery?: string }) => void;
  getFilteredOpportunities: () => ScrapedOpportunity[];
}

export const useScrapingStore = create<ScrapingState>((set, get) => ({
  sources: seedSources,
  opportunities: seedOpportunities,
  jobs: seedJobs,
  isLoading: false,
  isScraping: false,
  error: null,
  statusFilter: 'all',
  sourceFilter: 'all',
  searchQuery: '',

  fetchSources: async () => {
    set({ isLoading: true, error: null });
    try {
      // When backend is available, replace with real API call.
      // For now keep existing state (don't overwrite with empty).
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchOpportunities: async () => {
    set({ isLoading: true, error: null });
    try {
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchJobs: async () => {
    set({ isLoading: true, error: null });
    try {
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  addSource: (data) => {
    const newSource: ScrapingSource = {
      id: `src-${Date.now()}`,
      name: data.name || '',
      organization: data.organization || '',
      url: data.url || '',
      sourceType: (data.sourceType as any) || 'portal',
      status: 'active',
      scrapeFrequency: (data.scrapeFrequency as any) || 'daily',
      filters: {},
      newOpportunitiesCount: 0,
      totalOpportunitiesCount: 0,
      successRate: 0,
      ...data,
    } as ScrapingSource;
    set((state) => ({ sources: [...state.sources, newSource] }));
  },

  toggleSourceStatus: (sourceId) => {
    set((state) => ({
      sources: state.sources.map((s) =>
        s.id === sourceId
          ? { ...s, status: s.status === 'active' ? 'paused' : 'active' }
          : s
      ),
    }));
  },

  startScraping: async (sourceId) => {
    set({ isScraping: true });
    const job: ScrapingJob = {
      id: `job-${Date.now()}`, sourceId, status: 'running',
      startedAt: new Date(), itemsFound: 0, itemsNew: 0, itemsImported: 0,
      executedBy: 'user',
    };
    set((state) => ({ jobs: [job, ...state.jobs] }));
    await new Promise((r) => setTimeout(r, 1500));
    const completed = { ...job, status: 'completed' as const, completedAt: new Date(), itemsFound: 5, itemsNew: 1 };
    set((state) => ({
      isScraping: false,
      jobs: state.jobs.map((j) => (j.id === job.id ? completed : j)),
      sources: state.sources.map((s) =>
        s.id === sourceId ? { ...s, lastScrapedAt: new Date() } : s
      ),
    }));
  },

  runAllScrapes: async () => {
    set({ isScraping: true });
    await new Promise((r) => setTimeout(r, 2000));
    set((state) => ({
      isScraping: false,
      sources: state.sources.map((s) =>
        s.status === 'active' ? { ...s, lastScrapedAt: new Date() } : s
      ),
    }));
  },

  importOpportunity: (opportunityId) => {
    set((state) => ({
      opportunities: state.opportunities.map((o) =>
        o.id === opportunityId ? { ...o, status: 'imported' as const } : o
      ),
    }));
  },

  ignoreOpportunity: (opportunityId) => {
    set((state) => ({
      opportunities: state.opportunities.map((o) =>
        o.id === opportunityId ? { ...o, status: 'ignored' as const } : o
      ),
    }));
  },

  updateFilters: (filters) => {
    set((state) => ({ ...state, ...filters }));
  },

  getFilteredOpportunities: () => {
    const { opportunities, statusFilter, sourceFilter, searchQuery } = get();
    return opportunities.filter((o) => {
      if (statusFilter !== 'all' && o.status !== statusFilter) return false;
      if (sourceFilter !== 'all' && o.sourceId !== sourceFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!o.title.toLowerCase().includes(q) && !o.organization.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  },
}));
