// ============================================
// API CLIENT - ConsultPro Backend Integration
// ============================================

const API_BASE = '/api';

function getToken(): string | null {
  return localStorage.getItem('access_token');
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearTokens();
    window.location.href = '/';
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || errorData.message || `API Error: ${response.status}`
    );
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

// ============================================
// AUTH
// ============================================

export interface LoginResponse {
  access: string;
  refresh: string;
}

export interface MeResponse {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  avatar: string | null;
  availability: string;
  skills: string[];
  languages: string[];
}

export async function apiLogin(
  email: string,
  password: string
): Promise<LoginResponse> {
  const data = await apiRequest<LoginResponse>('/auth/token/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setTokens(data.access, data.refresh);
  return data;
}

export async function apiGetMe(): Promise<MeResponse> {
  return apiRequest<MeResponse>('/auth/me/');
}

// ============================================
// USERS
// ============================================

export interface ApiUser {
  id: number;
  email: string;
  username: string;
  name: string;
  role: string;
  avatar: string | null;
  availability: string;
  skills: string[];
  languages: string[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function apiGetUsers(): Promise<PaginatedResponse<ApiUser>> {
  return apiRequest<PaginatedResponse<ApiUser>>('/users/');
}

export async function apiGetUser(id: number): Promise<ApiUser> {
  return apiRequest<ApiUser>(`/users/${id}/`);
}

export async function apiUpdateMe(data: Partial<MeResponse>): Promise<MeResponse> {
  return apiRequest<MeResponse>('/auth/me/', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ============================================
// OPPORTUNITIES
// ============================================

export interface ApiRequirement {
  id: number;
  category: string;
  description: string;
  priority: string;
  is_covered: boolean;
  covered_in: string | null;
}

export interface ApiRisk {
  id: number;
  description: string;
  severity: string;
  mitigation: string | null;
}

export interface ApiOpportunity {
  id: number;
  title: string;
  client: string;
  client_logo: string | null;
  sector: string;
  country: string;
  region: string;
  value: string;
  currency: string;
  deadline: string | null;
  status: string;
  description: string;
  evaluation_criteria: string;
  technical_weight: number;
  financial_weight: number;
  tor_document: string | null;
  reference_number: string;
  url_source: string;
  ai_summary: string | null;
  ai_analysis_status: string;
  created_by: number | null;
  assigned_to: number | null;
  requirements: ApiRequirement[];
  risks: ApiRisk[];
  days_until_deadline: number;
  created_at: string;
  updated_at: string;
}

export interface ApiOpportunityListItem {
  id: number;
  title: string;
  client: string;
  sector: string;
  country: string;
  value: string;
  currency: string;
  deadline: string | null;
  status: string;
  days_until_deadline: number;
  created_at: string;
}

export async function apiGetOpportunities(): Promise<
  PaginatedResponse<ApiOpportunityListItem>
> {
  return apiRequest<PaginatedResponse<ApiOpportunityListItem>>(
    '/opportunities/opportunities/'
  );
}

export async function apiGetOpportunity(
  id: string
): Promise<ApiOpportunity> {
  return apiRequest<ApiOpportunity>(`/opportunities/opportunities/${id}/`);
}

export async function apiGetOpportunityRequirements(
  id: string
): Promise<ApiRequirement[]> {
  return apiRequest<ApiRequirement[]>(
    `/opportunities/opportunities/${id}/requirements/`
  );
}

export async function apiGetOpportunityRisks(
  id: string
): Promise<ApiRisk[]> {
  return apiRequest<ApiRisk[]>(`/opportunities/opportunities/${id}/risks/`);
}

export async function apiCreateOpportunity(
  data: Partial<ApiOpportunity>
): Promise<ApiOpportunity> {
  return apiRequest<ApiOpportunity>('/opportunities/opportunities/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiUploadToR(
  id: string,
  file: File
): Promise<{ detail: string }> {
  const formData = new FormData();
  formData.append('tor_document', file);
  return apiRequest<{ detail: string }>(
    `/opportunities/opportunities/${id}/upload_tor/`,
    {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type with boundary
    }
  );
}

export async function apiUpdateOpportunityStatus(
  id: string,
  status: string
): Promise<ApiOpportunity> {
  return apiRequest<ApiOpportunity>(`/opportunities/opportunities/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

// ============================================
// PROPOSALS
// ============================================

export interface ApiBudgetItem {
  id: number;
  category: string;
  amount: string;
  description: string;
}

export interface ApiBudget {
  id: number;
  proposal: number;
  total: string;
  currency: string;
  items: ApiBudgetItem[];
  breakdown: ApiBudgetItem[];
}

export interface ApiComment {
  id: number;
  user: { id: number; email: string; first_name: string; last_name: string };
  user_id: number;
  section: number;
  text: string;
  resolved: boolean;
  created_at: string;
}

export interface ApiAISuggestion {
  id: number;
  section: number;
  action: string;
  description: string;
  generated_content: string;
  applied: boolean;
  created_at: string;
}

export interface ApiProposalSection {
  id: number;
  proposal: number;
  type: string;
  title: string;
  content: string;
  order: number;
  is_complete: boolean;
  comments: ApiComment[];
  ai_suggestions: ApiAISuggestion[];
  created_at: string;
  updated_at: string;
}

export interface ApiTeamMember {
  id: number;
  user: { id: number; email: string; first_name: string; last_name: string };
  user_id: number;
  proposal: number;
  role: string;
  hours: number;
  hourly_rate: string;
  cv_attached: boolean;
  cv_document: string | null;
}

export interface ApiProposalListItem {
  id: number;
  title: string;
  version: number;
  status: string;
  opportunity: number;
  opportunity_id: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  progress: number;
}

export interface ApiProposal {
  id: number;
  title: string;
  version: number;
  status: string;
  opportunity: number;
  opportunity_id: number;
  sections: ApiProposalSection[];
  team: ApiTeamMember[];
  budget: ApiBudget | null;
  quality_score: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

export async function apiGetProposals(): Promise<
  PaginatedResponse<ApiProposalListItem>
> {
  return apiRequest<PaginatedResponse<ApiProposalListItem>>('/proposals/');
}

export async function apiGetProposal(id: string): Promise<ApiProposal> {
  return apiRequest<ApiProposal>(`/proposals/${id}/`);
}

export async function apiCreateProposal(
  data: Partial<ApiProposal>
): Promise<ApiProposal> {
  return apiRequest<ApiProposal>('/proposals/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiUpdateProposalSection(
  proposalId: string,
  sectionId: string,
  data: Partial<ApiProposalSection>
): Promise<ApiProposalSection> {
  return apiRequest<ApiProposalSection>(
    `/proposals/${proposalId}/sections/${sectionId}/`,
    {
      method: 'PUT',
      body: JSON.stringify(data),
    }
  );
}

// ============================================
// DASHBOARD
// ============================================

export interface ApiDashboardStats {
  active_opportunities: number;
  proposals_in_progress: number;
  win_rate: number;
  upcoming_deadlines: number;
}

export interface ApiPipelineItem {
  id: number;
  title: string;
  client: string;
  deadline: string | null;
  status: string;
  value: number;
  progress: number;
}

export interface ApiAlert {
  id: string;
  type: string;
  message: string;
  action?: {
    label: string;
    href: string;
  };
}

export interface ApiActivity {
  id: string;
  type: string;
  user: ApiUser | null;
  description: string;
  timestamp: string;
  metadata: Record<string, unknown> | null;
}

export async function apiGetDashboardStats(): Promise<ApiDashboardStats> {
  return apiRequest<ApiDashboardStats>('/dashboard/stats/');
}

export async function apiGetDashboardPipeline(): Promise<ApiPipelineItem[]> {
  return apiRequest<ApiPipelineItem[]>('/dashboard/pipeline/');
}

export async function apiGetDashboardAlerts(): Promise<ApiAlert[]> {
  return apiRequest<ApiAlert[]>('/dashboard/alerts/');
}

export async function apiGetDashboardActivity(): Promise<ApiActivity[]> {
  return apiRequest<ApiActivity[]>('/dashboard/activity/');
}

// ============================================
// PROJECTS
// ============================================

export interface ApiProject {
  id: number;
  title: string;
  description: string;
  client: string;
  client_contact_name: string;
  client_contact_email: string;
  status: string;
  start_date: string | null;
  end_date: string | null;
  actual_end_date: string | null;
  budget_total: string;
  budget_currency: string;
  actual_cost: string;
  progress: number;
  manager: number | null;
  manager_name: string;
  team_count: number;
  milestones_count: number;
  milestones_completed: number;
  days_remaining: number | null;
  budget_utilization: number;
  is_overdue: boolean;
  sector: string;
  country: string;
  risk_level: string;
  created_at: string;
  updated_at: string;
  proposal_id: number | null;
}

export interface ApiProjectPhase {
  id: number;
  name: string;
  name_display: string;
  description: string;
  start_date: string | null;
  end_date: string | null;
  is_completed: boolean;
  completion_percentage: number;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectDetail extends ApiProject {
  team: Array<{
    id: number;
    user: { id: number; email: string; first_name: string; last_name: string; name: string; role: string };
    role: string;
    allocation_percentage: number;
  }>;
  milestones: Array<{
    id: number;
    title: string;
    description: string;
    due_date: string;
    completed_date: string | null;
    status: string;
  }>;
  risks: Array<{
    id: number;
    title: string;
    description: string;
    severity: string;
    status: string;
    mitigation_plan: string;
  }>;
  deliverables: Array<{
    id: number;
    title: string;
    description: string;
    due_date: string | null;
    status: string;
  }>;
  phases: ApiProjectPhase[];
}

export async function apiGetProjects(): Promise<PaginatedResponse<ApiProject>> {
  return apiRequest<PaginatedResponse<ApiProject>>('/projects/projects/');
}

export async function apiGetProject(id: string): Promise<ApiProjectDetail> {
  return apiRequest<ApiProjectDetail>(`/projects/projects/${id}/`);
}

export async function apiCreateProject(
  data: Partial<ApiProject>
): Promise<ApiProject> {
  return apiRequest<ApiProject>('/projects/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiUpdateProjectStatus(
  id: string,
  action: 'activate' | 'complete' | 'close' | 'hold'
): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/projects/projects/${id}/${action}/`, {
    method: 'POST',
  });
}

export async function apiGetProjectStats(): Promise<{
  total_projects: number;
  active_projects: number;
  planning_projects: number;
  completed_projects: number;
  on_hold_projects: number;
  overdue_projects: number;
}> {
  return apiRequest('/projects/projects/stats/');
}

export async function apiGetProjectPhases(projectId: string): Promise<ApiProjectPhase[]> {
  return apiRequest<ApiProjectPhase[]>(`/projects/phases/?project=${projectId}`);
}

export async function apiUpdateProjectPhase(
  phaseId: number,
  data: Partial<ApiProjectPhase>
): Promise<ApiProjectPhase> {
  return apiRequest<ApiProjectPhase>(`/projects/phases/${phaseId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ============================================
// CONSULTANTS
// ============================================

export interface ApiConsultantProfile {
  id: number;
  user: number;
  hourly_rate: string;
  daily_rate: string;
  currency: string;
  specializations: string[];
  education: string;
  linkedin_url: string;
  portfolio_url: string;
  cv_document: string | null;
  is_available_for_hire: boolean;
  total_projects_completed: number;
  total_proposals_won: number;
  performance_rating: string;
  created_at: string;
  updated_at: string;
}

export interface ApiConsultant {
  id: number;
  email: string;
  username: string;
  name: string;
  role: string;
  avatar: string | null;
  availability: string;
  skills: string[];
  languages: string[];
  years_experience: number;
  consultant_profile: ApiConsultantProfile | null;
}

export async function apiGetConsultants(): Promise<PaginatedResponse<ApiConsultant>> {
  return apiRequest<PaginatedResponse<ApiConsultant>>('/users/?role=consultant');
}

export async function apiGetConsultant(id: number): Promise<ApiConsultant> {
  return apiRequest<ApiConsultant>(`/users/${id}/`);
}

// ============================================
// TEAMS
// ============================================

export interface ApiTeam {
  id: number;
  name: string;
  description: string;
  members: ApiUser[];
  member_ids: number[];
  created_at: string;
  updated_at: string;
}

export async function apiGetTeams(): Promise<PaginatedResponse<ApiTeam>> {
  return apiRequest<PaginatedResponse<ApiTeam>>('/teams/');
}

export async function apiCreateTeam(
  data: Partial<ApiTeam>
): Promise<ApiTeam> {
  return apiRequest<ApiTeam>('/teams/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiUpdateTeam(
  id: number,
  data: Partial<ApiTeam>
): Promise<ApiTeam> {
  return apiRequest<ApiTeam>(`/teams/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function apiDeleteTeam(id: number): Promise<void> {
  return apiRequest<void>(`/teams/${id}/`, {
    method: 'DELETE',
  });
}
