// ============================================
// TYPES - ConsultPro Platform
// ============================================

// User Types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'consultant' | 'manager' | 'admin';
  skills: string[];
  availability: 'available' | 'busy' | 'unavailable';
  languages: string[];
}

// Opportunity Types
export interface Opportunity {
  id: string;
  title: string;
  client: string;
  clientLogo?: string;
  sector: string;
  country: string;
  value: number;
  currency: string;
  deadline: Date;
  status: OpportunityStatus;
  description: string;
  torDocument?: string;
  aiSummary?: string;
  aiExtraction?: Record<string, unknown>;
  aiAnalysisStatus?: AIAnalysisStatus;
  requirements: Requirement[];
  risks: Risk[];
  createdAt: Date;
  updatedAt: Date;
}

export type AIAnalysisStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed';

export type OpportunityStatus = 
  | 'new' 
  | 'analyzing' 
  | 'go' 
  | 'no_go' 
  | 'proposal_draft' 
  | 'proposal_review' 
  | 'submitted' 
  | 'won' 
  | 'lost';

export interface Requirement {
  id: string;
  category: 'functional' | 'technical' | 'institutional' | 'financial';
  description: string;
  priority: 'mandatory' | 'preferred' | 'optional';
  isCovered: boolean;
  coveredIn?: string;
}

export interface Risk {
  id: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  mitigation?: string;
}

// Proposal Types
export interface Proposal {
  id: string;
  opportunityId: string;
  title: string;
  version: number;
  status: ProposalStatus;
  sections: ProposalSection[];
  team: TeamMember[];
  budget?: Budget;
  qualityScore?: number;
  proponentLogoUrl?: string;
  clientLogoUrl?: string;
  consortiumMembers: string[];
  createdAt: Date;
  updatedAt: Date;
  submittedAt?: Date;
}

export type ProposalStatus = 
  | 'draft' 
  | 'in_review' 
  | 'qc_check' 
  | 'ready_for_submission'
  | 'approved' 
  | 'submitted' 
  | 'under_evaluation'
  | 'rejected'
  | 'shortlisted'
  | 'clarifications_requested'
  | 'bafo'
  | 'awarded'
  | 'contract_negotiation'
  | 'contract_signed'
  | 'project_initiation'
  | 'won' 
  | 'lost';

export interface ProposalSection {
  id: string;
  type: SectionType;
  title: string;
  content: string;
  order: number;
  isComplete: boolean;
  comments: Comment[];
  aiSuggestions?: AISuggestion[];
}

export type SectionType = 
  | 'cover' 
  | 'executive_summary' 
  | 'methodology' 
  | 'team' 
  | 'workplan' 
  | 'budget' 
  | 'annexes'
  | 'custom';

export interface TeamMember {
  userId: string;
  role: string;
  hours: number;
  cvAttached: boolean;
}

export interface Budget {
  total: number;
  currency: string;
  breakdown: BudgetItem[];
}

export interface BudgetItem {
  category: string;
  amount: number;
  description: string;
}

export interface Comment {
  id: string;
  userId: string;
  text: string;
  createdAt: Date;
  resolved: boolean;
}

export interface AISuggestion {
  id: string;
  type: 'expand' | 'summarize' | 'tone' | 'translate';
  description: string;
  applied: boolean;
}

// Quality Check Types
export interface QCState {
  proposalId: string;
  overallScore: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  checks: {
    compliance: QCCheck;
    coherence: QCCheck;
    budget: QCCheck;
    attachments: QCCheck;
  };
  canSubmit: boolean;
  suggestions: QCSuggestion[];
}

export interface QCCheck {
  score: number;
  status: 'pass' | 'warn' | 'fail';
  items: QCItem[];
}

export interface QCItem {
  id: string;
  description: string;
  status: 'pass' | 'warn' | 'fail';
  section?: string;
}

export interface QCSuggestion {
  id: string;
  text: string;
  action: 'replace' | 'add' | 'remove';
  targetSection: string;
  applied: boolean;
}

// Dashboard Types
export interface DashboardStats {
  activeOpportunities: number;
  proposalsInProgress: number;
  winRate: number;
  upcomingDeadlines: number;
}

export interface PipelineItem {
  id: string;
  title: string;
  client: string;
  deadline: Date;
  status: ProposalStatus;
  value: number;
  progress: number;
}

export interface Alert {
  id: string;
  type: 'warning' | 'error' | 'info';
  message: string;
  action?: {
    label: string;
    href: string;
  };
}

// Activity Types
export interface Activity {
  id: string;
  type: 'proposal_created' | 'proposal_updated' | 'opportunity_added' | 'qc_completed' | 'comment_added';
  user: User;
  description: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

// Curriculum / CV Types
export interface Curriculum {
  id: string;
  fileName: string;
  fileType: 'pdf' | 'docx' | 'doc';
  status: 'uploaded' | 'processing' | 'analyzed' | 'error';
  analysisScore?: number;
  extractedData: Record<string, unknown>;
  templateMatches: TemplateMatch[];
  suggestions: CVSuggestion[];
  createdAt: Date;
  updatedAt: Date;
}

export interface CVTemplate {
  id: string;
  name: string;
  organization: 'world_bank' | 'un' | 'eu' | 'afdb' | 'usaid' | 'giz' | 'other';
  organizationName: string;
  description: string;
  requiredSections: Array<{ id: string; name: string; required: boolean }>;
  formatRules: unknown[];
  maxLengthPages?: number;
  exampleUrl?: string;
  isActive: boolean;
}

export interface TemplateMatch {
  id: string;
  curriculumId: string;
  template: CVTemplate;
  matchScore: number;
  missingSections: string[];
  recommendations: string[];
  adaptedContent?: Record<string, unknown>;
  createdAt: Date;
}

export interface CVSuggestion {
  id: string;
  type: 'missing_section' | 'format' | 'content' | 'keyword' | 'length';
  priority: 'high' | 'medium' | 'low';
  message: string;
  context?: string;
  autoFixable: boolean;
  fixed: boolean;
  createdAt: Date;
}

export interface CVOpportunityMatch {
  id: string;
  curriculumId: string;
  opportunityId: string;
  opportunityTitle: string;
  opportunityClient: string;
  overallScore: number;
  skillsMatchScore: number;
  experienceMatchScore: number;
  educationMatchScore: number;
  languageMatchScore: number;
  matchedSkills: string[];
  missingSkills: string[];
  relevantExperiences: unknown[];
  recommendations: string[];
}

// Scraping Types
export interface ScrapingSource {
  id: string;
  name: string;
  organization: string;
  url: string;
  logo?: string;
  sourceType: 'portal' | 'rss' | 'api' | 'job_board';
  status: 'active' | 'paused' | 'error' | 'disabled';
  scrapeFrequency: 'hourly' | 'daily' | 'weekly';
  lastScrapedAt?: Date;
  nextScrapeAt?: Date;
  filters: Record<string, unknown>;
  newOpportunitiesCount: number;
  totalOpportunitiesCount: number;
  successRate: number;
  errorMessage?: string;
}

export interface ScrapedOpportunity {
  id: string;
  sourceId: string;
  externalId?: string;
  externalUrl: string;
  title: string;
  organization: string;
  client: string;
  sector?: string;
  country?: string;
  description: string;
  value?: number;
  currency: string;
  deadline?: Date;
  status: 'new' | 'imported' | 'ignored' | 'expired';
  publishedAt?: Date;
  deadlineAlert: boolean;
  aiSummary?: string;
  deepContentStatus?: string;
  importedOpportunityId?: string;
}

export interface ScrapingJob {
  id: string;
  sourceId: string;
  status: 'running' | 'completed' | 'failed' | 'scheduled';
  startedAt?: Date;
  completedAt?: Date;
  itemsFound: number;
  itemsNew: number;
  itemsImported: number;
  errorLog?: string;
  executedBy: string;
}

export interface ScrapingAlert {
  id: string;
  type: 'new_opportunity' | 'deadline_approaching' | 'status_change' | 'value_threshold';
  title: string;
  message: string;
  scrapedOpportunityId?: string;
  read: boolean;
  createdAt: Date;
}

// Team Types (extended)
export interface Team {
  id: string;
  name: string;
  description: string;
  members: TeamMemberExtended[];
  createdAt: Date;
  updatedAt: Date;
}

export interface TeamMemberExtended {
  id: string;
  userId: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  hoursAllocated?: number;
  joinedAt: Date;
}

// Translation Types
export interface TranslationKeys {
  navigation: {
    dashboard: string;
    opportunities: string;
    proposals: string;
    teams: string;
    settings: string;
  };
  actions: {
    save: string;
    submit: string;
    cancel: string;
    edit: string;
    delete: string;
  };
  status: {
    draft: string;
    review: string;
    submitted: string;
    won: string;
    lost: string;
  };
}
