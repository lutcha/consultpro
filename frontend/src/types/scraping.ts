// Types for Scraping module
export interface ScrapingSource {
  id: string;
  name: string;
  url: string;
  type: string;
  status: 'active' | 'warning' | 'paused' | 'error';
  lastScraped: string | null;
  nextScrape: string | null;
  frequency: string;
  configuration: any;
  isAutomated: boolean;
  successRate: number;
  totalOpportunities: number;
  lastError: string | null;
  createdAt: string;
}

export interface ScrapedOpportunity {
  id: string;
  sourceId: string;
  sourceName: string;
  title: string;
  organization: string;
  deadline: string;
  status: string;
  location: string;
  budgetRange: string;
  sector: string;
  url: string;
  description: string;
  aiSummary: string;
  keywordsMatched: string[];
  isRelevant: boolean;
  relevanceScore: number;
  scrapedAt: string;
  importedAt: string | null;
  notes: string;
}

export interface ScrapingJob {
  id: string;
  sourceId: string;
  sourceName: string;
  status: string;
  startedAt: string | null;
  completedAt: string | null;
  opportunitiesFound: number;
  opportunitiesNew: number;
  errors: string[];
  duration: number;
}

export interface ScrapingStats {
  totalSources: number;
  activeSources: number;
  totalOpportunities: number;
  opportunitiesThisWeek: number;
  averageSuccessRate: number;
  importRate: number;
}
