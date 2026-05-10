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
  const isFormData = options.body instanceof FormData;

  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (!isFormData && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearTokens();
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

export async function apiCreateUser(data: {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  role: string;
  skills?: string[];
  languages?: string[];
}): Promise<ApiUser> {
  return apiRequest<ApiUser>('/users/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
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
    '/opportunities/'
  );
}

export async function apiGetOpportunity(
  id: string
): Promise<ApiOpportunity> {
  return apiRequest<ApiOpportunity>(`/opportunities/${id}/`);
}

export async function apiGetOpportunityRequirements(
  id: string
): Promise<ApiRequirement[]> {
  return apiRequest<ApiRequirement[]>(
    `/opportunities/${id}/requirements/`
  );
}

export async function apiGetOpportunityRisks(
  id: string
): Promise<ApiRisk[]> {
  return apiRequest<ApiRisk[]>(`/opportunities/${id}/risks/`);
}

export async function apiCreateOpportunity(
  data: Partial<ApiOpportunity>
): Promise<ApiOpportunity> {
  return apiRequest<ApiOpportunity>('/opportunities/', {
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
    `/opportunities/${id}/upload_tor/`,
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
  return apiRequest<ApiOpportunity>(`/opportunities/${id}/`, {
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
  proponent_logo_url: string | null;
  client_logo_url: string | null;
  consortium_members: string[];
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

export async function apiDownloadProposalWord(proposalId: string): Promise<Blob> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/proposals/${proposalId}/download_word/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error('Erro ao gerar Word');
  return response.blob();
}

export async function apiDownloadProposalPdf(proposalId: string): Promise<Blob> {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/proposals/${proposalId}/download_pdf/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error('Erro ao gerar PDF');
  return response.blob();
}

export async function apiUploadProposalLogo(
  proposalId: string,
  file: File,
  logoType: 'proponent' | 'client'
): Promise<{ url: string; detail: string }> {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('logo', file);
  formData.append('logo_type', logoType);
  const response = await fetch(`/api/proposals/${proposalId}/upload_logo/`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!response.ok) throw new Error('Erro ao fazer upload do logo');
  return response.json();
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
  return apiRequest<PaginatedResponse<ApiProject>>('/projects/');
}

export async function apiGetProject(id: string): Promise<ApiProjectDetail> {
  return apiRequest<ApiProjectDetail>(`/projects/${id}/`);
}

export async function apiCreateProject(
  data: Partial<ApiProject>
): Promise<ApiProject> {
  return apiRequest<ApiProject>('/projects/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiUpdateProjectStatus(
  id: string,
  action: 'activate' | 'complete' | 'close' | 'hold'
): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/projects/${id}/${action}/`, {
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
  return apiRequest('/projects/stats/');
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

export async function apiAddTeamMember(teamId: number, userId: number): Promise<ApiTeam> {
  return apiRequest<ApiTeam>(`/teams/${teamId}/add_member/`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

export async function apiRemoveTeamMember(teamId: number, userId: number): Promise<ApiTeam> {
  return apiRequest<ApiTeam>(`/teams/${teamId}/remove_member/`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });
}

// ============================================
// CURRICULUM / CV
// ============================================

export interface ApiCurriculum {
  id: number;
  user: any;
  file_name: string;
  file_type: string;
  status: string;
  analysis_score: number | null;
  extracted_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ApiCVTemplate {
  id: number;
  name: string;
  organization: string;
  organization_name: string;
  description: string;
  required_sections: unknown[];
  format_rules: unknown[];
  max_length_pages: number | null;
  file_template: string | null;
  example_url: string;
  is_active: boolean;
  created_at: string;
}

export interface ApiCVSuggestion {
  id: number;
  type: string;
  priority: string;
  message: string;
  context: string;
  auto_fixable: boolean;
  fixed: boolean;
  created_at: string;
}

export async function apiGetCurricula(): Promise<PaginatedResponse<ApiCurriculum>> {
  return apiRequest<PaginatedResponse<ApiCurriculum>>('/curriculum/');
}

export async function apiGetCurriculum(id: number): Promise<ApiCurriculum> {
  return apiRequest<ApiCurriculum>(`/curriculum/${id}/`);
}

export async function apiUploadCV(file: File): Promise<ApiCurriculum> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('file_name', file.name);
  const ext = file.name.split('.').pop()?.toLowerCase();
  formData.append('file_type', ext === 'pdf' ? 'pdf' : 'docx');

  return apiRequest<ApiCurriculum>('/curriculum/', {
    method: 'POST',
    body: formData,
    headers: {},
  });
}

export async function apiAnalyzeCV(id: number): Promise<ApiCurriculum> {
  return apiRequest<ApiCurriculum>(`/curriculum/${id}/analyze/`, {
    method: 'POST',
  });
}

export async function apiGetCVExtracted(id: number): Promise<{ extracted_data: Record<string, unknown> }> {
  return apiRequest<{ extracted_data: Record<string, unknown> }>(`/curriculum/${id}/extracted/`);
}

export async function apiGetCVSuggestions(id: number): Promise<ApiCVSuggestion[]> {
  return apiRequest<ApiCVSuggestion[]>(`/curriculum/${id}/suggestions/`);
}

export async function apiApplyCVSuggestion(cvId: number, suggId: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/curriculum/${cvId}/suggestions/${suggId}/apply/`, {
    method: 'POST',
  });
}

export async function apiGetCVTemplates(): Promise<PaginatedResponse<ApiCVTemplate>> {
  return apiRequest<PaginatedResponse<ApiCVTemplate>>('/curriculum/templates/');
}

export async function apiCreateCVTemplate(data: Partial<ApiCVTemplate>): Promise<ApiCVTemplate> {
  return apiRequest<ApiCVTemplate>('/curriculum/templates/', { method: 'POST', body: JSON.stringify(data) });
}

export async function apiUpdateCVTemplate(id: number, data: Partial<ApiCVTemplate>): Promise<ApiCVTemplate> {
  return apiRequest<ApiCVTemplate>(`/curriculum/templates/${id}/`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function apiDeleteCVTemplate(id: number): Promise<void> {
  return apiRequest<void>(`/curriculum/templates/${id}/`, { method: 'DELETE' });
}

export async function apiDownloadCVTemplate(id: number): Promise<Blob> {
  const response = await fetch(`${API_BASE}/curriculum/templates/${id}/download/`, {
    headers: { Authorization: `Bearer ${getToken() || ''}` },
  });
  if (!response.ok) throw new Error('Download failed');
  return response.blob();
}

// ============================================
// SCRAPING
// ============================================

export interface ApiScrapingSource {
  id: number;
  name: string;
  organization: string;
  url: string;
  logo: string;
  source_type: string;
  status: string;
  scrape_frequency: string;
  last_scraped_at: string | null;
  next_scrape_at: string | null;
  filters: Record<string, unknown>;
  new_opportunities_count: number;
  total_opportunities_count: number;
  success_rate: number;
  error_message: string;
}

export interface ApiScrapedOpportunity {
  id: number;
  source: number;
  external_id: string;
  external_url: string;
  title: string;
  organization: string;
  client: string;
  sector: string;
  country: string;
  description: string;
  value: string;
  currency: string;
  deadline: string | null;
  status: string;
  published_at: string | null;
  deadline_alert: boolean;
  ai_summary: string;
}

export interface ApiScrapingJob {
  id: number;
  source: number;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  items_found: number;
  items_new: number;
  items_imported: number;
  error_log: string;
  executed_by: string;
}

export interface ApiScrapingAlert {
  id: number;
  type: string;
  title: string;
  message: string;
  scraped_opportunity: number | null;
  read: boolean;
  created_at: string;
}

export async function apiGetScrapingSources(): Promise<PaginatedResponse<ApiScrapingSource>> {
  return apiRequest<PaginatedResponse<ApiScrapingSource>>('/scraping/sources/');
}

export async function apiCreateScrapingSource(data: Partial<ApiScrapingSource>): Promise<ApiScrapingSource> {
  return apiRequest<ApiScrapingSource>('/scraping/sources/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function apiRunScrapingSource(id: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/scraping/sources/${id}/run/`, {
    method: 'POST',
  });
}

export async function apiToggleScrapingSource(id: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/scraping/sources/${id}/toggle/`, {
    method: 'POST',
  });
}

export async function apiGetScrapedOpportunities(): Promise<PaginatedResponse<ApiScrapedOpportunity>> {
  return apiRequest<PaginatedResponse<ApiScrapedOpportunity>>('/scraping/opportunities/');
}

export async function apiImportScrapedOpportunity(id: number): Promise<{ opportunity_id: number; status: string }> {
  return apiRequest<{ opportunity_id: number; status: string }>(`/scraping/opportunities/${id}/import_opportunity/`, {
    method: 'POST',
  });
}

export async function apiIgnoreScrapedOpportunity(id: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/scraping/opportunities/${id}/ignore/`, {
    method: 'POST',
  });
}

export async function apiGetScrapingJobs(): Promise<PaginatedResponse<ApiScrapingJob>> {
  return apiRequest<PaginatedResponse<ApiScrapingJob>>('/scraping/jobs/');
}

export async function apiUpdateScrapingSource(id: number, data: Partial<ApiScrapingSource>): Promise<ApiScrapingSource> {
  return apiRequest<ApiScrapingSource>(`/scraping/sources/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiGetScrapingStats(): Promise<{
  total_sources: number;
  active_sources: number;
  total_opportunities: number;
  imported_opportunities: number;
  new_opportunities: number;
  cv_eligible_new: number;
  avg_quality_score: number;
  success_rate: number;
}> {
  return apiRequest('/scraping/sources/stats/');
}

export async function apiGetScrapingAlerts(): Promise<PaginatedResponse<ApiScrapingAlert>> {
  return apiRequest<PaginatedResponse<ApiScrapingAlert>>('/scraping/alerts/');
}

export async function apiMarkScrapingAlertRead(id: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/scraping/alerts/${id}/mark_read/`, {
    method: 'POST',
  });
}
