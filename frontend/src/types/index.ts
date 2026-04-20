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
  requirements: Requirement[];
  risks: Risk[];
  createdAt: Date;
  updatedAt: Date;
}

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
  budget: Budget;
  qualityScore?: number;
  createdAt: Date;
  updatedAt: Date;
  submittedAt?: Date;
}

export type ProposalStatus = 
  | 'draft' 
  | 'in_review' 
  | 'qc_check' 
  | 'approved' 
  | 'submitted' 
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
  | 'annexes';

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
