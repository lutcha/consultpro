// ============================================
// API DATA MAPPERS - snake_case → camelCase
// ============================================

import type {
  User,
  Opportunity,
  Requirement,
  Risk,
  Proposal,
  ProposalSection,
  TeamMember,
  Budget,
  BudgetItem,
  Comment,
  AISuggestion,
  DashboardStats,
  PipelineItem,
  Alert,
  Activity,
} from '@/types';
import type {
  ApiUser,
  ApiOpportunity,
  ApiOpportunityListItem,
  ApiRequirement,
  ApiRisk,
  ApiProposal,
  ApiProposalListItem,
  ApiProposalSection,
  ApiTeamMember,
  ApiBudget,
  ApiBudgetItem,
  ApiComment,
  ApiAISuggestion,
  ApiDashboardStats,
  ApiPipelineItem,
  ApiAlert,
  ApiActivity,
  MeResponse,
} from './api';

function toDate(value: string | null): Date {
  return value ? new Date(value) : new Date();
}

// ============================================
// USER
// ============================================

export function mapApiUser(user: ApiUser): User {
  return {
    id: String(user.id),
    name: user.name,
    email: user.email,
    avatar: user.avatar || undefined,
    role: user.role as User['role'],
    skills: user.skills || [],
    availability: user.availability as User['availability'],
    languages: user.languages || [],
  };
}

export function mapMeResponse(me: MeResponse): User {
  return {
    id: String(me.id),
    name: `${me.first_name} ${me.last_name}`.trim() || me.username,
    email: me.email,
    avatar: me.avatar || undefined,
    role: me.role as User['role'],
    skills: me.skills || [],
    availability: me.availability as User['availability'],
    languages: me.languages || [],
  };
}

// ============================================
// REQUIREMENT
// ============================================

export function mapApiRequirement(req: ApiRequirement): Requirement {
  return {
    id: String(req.id),
    category: req.category as Requirement['category'],
    description: req.description,
    priority: req.priority as Requirement['priority'],
    isCovered: req.is_covered,
    coveredIn: req.covered_in || undefined,
  };
}

// ============================================
// RISK
// ============================================

export function mapApiRisk(risk: ApiRisk): Risk {
  return {
    id: String(risk.id),
    description: risk.description,
    severity: risk.severity as Risk['severity'],
    mitigation: risk.mitigation || undefined,
  };
}

// ============================================
// OPPORTUNITY
// ============================================

export function mapApiOpportunity(opp: ApiOpportunity): Opportunity {
  return {
    id: String(opp.id),
    title: opp.title,
    client: opp.client,
    clientLogo: opp.client_logo || undefined,
    sector: opp.sector,
    country: opp.country,
    value: parseFloat(opp.value) || 0,
    currency: opp.currency,
    deadline: toDate(opp.deadline),
    status: opp.status as Opportunity['status'],
    description: opp.description,
    requirements: (opp.requirements || []).map(mapApiRequirement),
    risks: (opp.risks || []).map(mapApiRisk),
    createdAt: toDate(opp.created_at),
    updatedAt: toDate(opp.updated_at),
  };
}

export function mapApiOpportunityListItem(
  opp: ApiOpportunityListItem
): Opportunity {
  return {
    id: String(opp.id),
    title: opp.title,
    client: opp.client,
    sector: opp.sector,
    country: opp.country,
    value: parseFloat(opp.value) || 0,
    currency: opp.currency,
    deadline: toDate(opp.deadline),
    status: opp.status as Opportunity['status'],
    description: '',
    requirements: [],
    risks: [],
    createdAt: toDate(opp.created_at),
    updatedAt: toDate(opp.created_at),
  };
}

// ============================================
// COMMENT
// ============================================

export function mapApiComment(comment: ApiComment): Comment {
  return {
    id: String(comment.id),
    userId: String(comment.user?.id || comment.user_id),
    text: comment.text,
    createdAt: toDate(comment.created_at),
    resolved: comment.resolved,
  };
}

// ============================================
// AI SUGGESTION
// ============================================

export function mapApiAISuggestion(sugg: ApiAISuggestion): AISuggestion {
  return {
    id: String(sugg.id),
    type: sugg.action as AISuggestion['type'],
    description: sugg.description,
    applied: sugg.applied,
  };
}

// ============================================
// PROPOSAL SECTION
// ============================================

export function mapApiProposalSection(
  section: ApiProposalSection
): ProposalSection {
  return {
    id: String(section.id),
    type: section.type as ProposalSection['type'],
    title: section.title,
    content: section.content,
    order: section.order,
    isComplete: section.is_complete,
    comments: (section.comments || []).map(mapApiComment),
    aiSuggestions: (section.ai_suggestions || []).map(mapApiAISuggestion),
  };
}

// ============================================
// TEAM MEMBER
// ============================================

export function mapApiTeamMember(member: ApiTeamMember): TeamMember {
  return {
    userId: String(member.user?.id || member.user_id),
    role: member.role,
    hours: member.hours,
    cvAttached: member.cv_attached,
  };
}

// ============================================
// BUDGET
// ============================================

export function mapApiBudgetItem(item: ApiBudgetItem): BudgetItem {
  return {
    category: item.category,
    amount: parseFloat(item.amount) || 0,
    description: item.description,
  };
}

export function mapApiBudget(budget: ApiBudget | null): Budget | undefined {
  if (!budget) return undefined;
  return {
    total: parseFloat(budget.total) || 0,
    currency: budget.currency,
    breakdown: (budget.items || budget.breakdown || []).map(mapApiBudgetItem),
  };
}

// ============================================
// PROPOSAL
// ============================================

export function mapApiProposal(proposal: ApiProposal): Proposal {
  return {
    id: String(proposal.id),
    opportunityId: String(proposal.opportunity_id || proposal.opportunity),
    title: proposal.title,
    version: proposal.version,
    status: proposal.status as Proposal['status'],
    sections: (proposal.sections || []).map(mapApiProposalSection),
    team: (proposal.team || []).map(mapApiTeamMember),
    budget: mapApiBudget(proposal.budget) || { total: 0, currency: 'USD', breakdown: [] },
    qualityScore: proposal.quality_score || undefined,
    proponentLogoUrl: proposal.proponent_logo_url || undefined,
    clientLogoUrl: proposal.client_logo_url || undefined,
    consortiumMembers: proposal.consortium_members || [],
    createdAt: toDate(proposal.created_at),
    updatedAt: toDate(proposal.updated_at),
    submittedAt: proposal.submitted_at
      ? toDate(proposal.submitted_at)
      : undefined,
  };
}

export function mapApiProposalListItem(
  proposal: ApiProposalListItem
): Proposal {
  return {
    id: String(proposal.id),
    opportunityId: String(proposal.opportunity_id || proposal.opportunity),
    title: proposal.title,
    version: proposal.version,
    status: proposal.status as Proposal['status'],
    sections: [],
    team: [],
    budget: { total: 0, currency: 'USD', breakdown: [] },
    consortiumMembers: [],
    createdAt: toDate(proposal.created_at),
    updatedAt: toDate(proposal.updated_at),
  };
}

// ============================================
// DASHBOARD
// ============================================

export function mapApiDashboardStats(stats: ApiDashboardStats): DashboardStats {
  return {
    activeOpportunities: stats.active_opportunities,
    proposalsInProgress: stats.proposals_in_progress,
    winRate: stats.win_rate,
    upcomingDeadlines: stats.upcoming_deadlines,
  };
}

export function mapApiPipelineItem(item: ApiPipelineItem): PipelineItem {
  return {
    id: String(item.id),
    title: item.title,
    client: item.client,
    deadline: toDate(item.deadline),
    status: item.status as PipelineItem['status'],
    value: item.value,
    progress: item.progress,
  };
}

export function mapApiAlert(alert: ApiAlert): Alert {
  return {
    id: alert.id,
    type: alert.type as Alert['type'],
    message: alert.message,
    action: alert.action,
  };
}

export function mapApiActivity(activity: ApiActivity): Activity {
  return {
    id: activity.id,
    type: activity.type as Activity['type'],
    user: activity.user ? mapApiUser(activity.user as unknown as ApiUser) : ({
        id: '0',
        name: 'Sistema',
        email: '',
        role: 'admin',
        skills: [],
        availability: 'available',
        languages: [],
      } as User),
    description: activity.description,
    timestamp: toDate(activity.timestamp),
    metadata: activity.metadata || undefined,
  };
}
