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

function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token');
}

// Single in-flight refresh promise — prevents parallel refresh races
let _refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (_refreshPromise) return _refreshPromise;
  _refreshPromise = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) throw new Error('No refresh token');
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) throw new Error('Refresh failed');
    const data = await res.json();
    // Backend rotates refresh tokens — update both
    setTokens(data.access, data.refresh ?? refresh);
    return data.access as string;
  })().finally(() => { _refreshPromise = null; });
  return _refreshPromise;
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  _retry = true,
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

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && _retry) {
    try {
      const newToken = await refreshAccessToken();
      const retryHeaders = { ...headers, Authorization: `Bearer ${newToken}` };
      const retry = await fetch(url, { ...options, headers: retryHeaders });
      if (retry.status === 401) {
        clearTokens();
        window.location.href = '/login';
        throw new Error('Sessão expirada. Por favor inicia sessão novamente.');
      }
      if (!retry.ok) {
        const errData = await retry.json().catch(() => ({}));
        const fieldErrs = Object.entries(errData)
          .filter(([, v]) => Array.isArray(v))
          .map(([k, v]) => `${k}: ${(v as string[]).join(', ')}`)
          .join(' | ');
        throw new Error(errData.detail || errData.message || fieldErrs || `API Error: ${retry.status}`);
      }
      if (retry.status === 204) return {} as T;
      return retry.json() as Promise<T>;
    } catch (refreshErr) {
      clearTokens();
      window.location.href = '/login';
      throw new Error('Sessão expirada. Por favor inicia sessão novamente.');
    }
  }

  if (response.status === 401) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('Sessão expirada. Por favor inicia sessão novamente.');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    // DRF returns field-level errors as { field: ["msg", ...], ... }
    const fieldErrors = Object.entries(errorData)
      .filter(([, v]) => Array.isArray(v))
      .map(([k, v]) => `${k}: ${(v as string[]).join(', ')}`)
      .join(' | ');
    throw new Error(
      errorData.detail || errorData.message || fieldErrors || `API Error: ${response.status}`
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
  phone?: string;
  bio?: string;
  location?: string;
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

export async function apiPatchUser(id: number, data: { role?: string; availability?: string }): Promise<ApiUser> {
  return apiRequest<ApiUser>(`/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data) });
}

export interface ApiUserDetail extends ApiUser {
  first_name: string;
  last_name: string;
  bio: string;
  phone: string;
  location: string;
  years_experience: number;
}

export async function apiUpdateUser(
  id: number,
  data: Partial<{
    first_name: string;
    last_name: string;
    email: string;
    username: string;
    role: string;
    availability: string;
    skills: string[];
    languages: string[];
    bio: string;
    phone: string;
    location: string;
    years_experience: number;
  }>
): Promise<ApiUserDetail> {
  return apiRequest<ApiUserDetail>(`/users/${id}/`, { method: 'PATCH', body: JSON.stringify(data) });
}

export async function apiDeleteUser(id: number): Promise<void> {
  return apiRequest<void>(`/users/${id}/`, { method: 'DELETE' });
}

export async function apiUpdateMe(data: Partial<MeResponse>): Promise<MeResponse> {
  return apiRequest<MeResponse>('/auth/me/', {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function apiChangePassword(data: {
  current_password: string;
  new_password: string;
}): Promise<{ status: string }> {
  return apiRequest<{ status: string }>('/users/me/change-password/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export interface ApiNotificationPreference {
  email_on_new_opportunity: boolean;
  email_on_proposal_status: boolean;
  email_on_scrape_complete: boolean;
  created_at: string;
  updated_at: string;
}

export async function apiGetNotificationPreferences(): Promise<ApiNotificationPreference> {
  return apiRequest<ApiNotificationPreference>('/users/me/notification-preferences/');
}

export async function apiUpdateNotificationPreferences(
  data: Partial<ApiNotificationPreference>
): Promise<ApiNotificationPreference> {
  return apiRequest<ApiNotificationPreference>('/users/me/notification-preferences/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export interface ApiNotification {
  id: number;
  user: number;
  type: 'warning' | 'error' | 'info' | 'success';
  title: string;
  message: string;
  action_label: string;
  action_url: string;
  read: boolean;
  created_at: string;
}

export async function apiGetNotifications(): Promise<PaginatedResponse<ApiNotification>> {
  return apiRequest<PaginatedResponse<ApiNotification>>('/notifications/');
}

export async function apiGetUnreadNotificationCount(): Promise<{ unread_count: number }> {
  return apiRequest<{ unread_count: number }>('/notifications/unread_count/');
}

export async function apiMarkNotificationRead(id: number): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/notifications/${id}/read/`, {
    method: 'PATCH',
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
  eligible_countries: string[];
  consortium_type: string;
  consortium_notes: string;
  partner_profiles: Record<string, unknown>[];
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

export interface ApiOpportunityQueryParams {
  search?: string;
  status?: string;
  sector?: string;
  country?: string;
  region?: string;
  min_score?: string | number;
  apply_profile_defaults?: boolean;
}

export interface ApiFirmProfile {
  id: number;
  name: string;
  target_sectors: string[];
  geographies: string[];
  scoring_weights_override: Record<string, unknown>;
  is_default: boolean;
  updated_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApiSavedFilter {
  id: number;
  owner: number;
  name: string;
  view_type: string;
  payload: Record<string, unknown>;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

function buildQueryString(params: object): string {
  const query = new URLSearchParams();
  Object.entries(params as Record<string, unknown>).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : '';
}

export async function apiGetOpportunities(
  params: ApiOpportunityQueryParams = {}
): Promise<PaginatedResponse<ApiOpportunityListItem>> {
  return apiRequest<PaginatedResponse<ApiOpportunityListItem>>(
    `/opportunities/${buildQueryString(params)}`
  );
}

export async function apiGetCurrentFirmProfile(): Promise<ApiFirmProfile | null> {
  try {
    return await apiRequest<ApiFirmProfile>('/opportunities/firm-profiles/current/');
  } catch (error) {
    if (error instanceof Error && error.message.includes('404')) {
      return null;
    }
    throw error;
  }
}

export async function apiGetSavedFilters(
  viewType = 'opportunities'
): Promise<PaginatedResponse<ApiSavedFilter>> {
  return apiRequest<PaginatedResponse<ApiSavedFilter>>(
    `/opportunities/saved-filters/${buildQueryString({ view_type: viewType })}`
  );
}

export async function apiCreateSavedFilter(data: {
  name: string;
  view_type?: string;
  payload: Record<string, unknown>;
  is_shared?: boolean;
}): Promise<ApiSavedFilter> {
  return apiRequest<ApiSavedFilter>('/opportunities/saved-filters/', {
    method: 'POST',
    body: JSON.stringify({
      view_type: 'opportunities',
      is_shared: false,
      ...data,
    }),
  });
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
  section_type: string;
  title: string;
  content: string;
  order: number;
  is_complete: boolean;
  comments: ApiComment[];
  ai_suggestions: ApiAISuggestion[];
  created_at: string;
  updated_at: string;
}

export interface ApiProposalSectionGapItem {
  label: string;
  source: string;
  status: 'covered' | 'partial' | 'missing';
  evidence: string;
  priority: string;
}

export interface ApiProposalSectionGap {
  section: {
    id: number;
    title: string;
    section_type: string;
  };
  score: number;
  covered_count: number;
  total_count: number;
  items: ApiProposalSectionGapItem[];
  suggestions: string[];
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

export async function apiCreateProposalSection(
  proposalId: string,
  data: { title: string; content?: string; section_type?: string }
): Promise<ApiProposalSection> {
  return apiRequest<ApiProposalSection>(`/proposals/${proposalId}/add_section/`, {
    method: 'POST',
    body: JSON.stringify({
      title: data.title,
      content: data.content || '',
      section_type: data.section_type || 'custom',
    }),
  });
}

export async function apiGetProposalSectionGap(
  proposalId: string,
  sectionId: string
): Promise<ApiProposalSectionGap> {
  return apiRequest<ApiProposalSectionGap>(
    `/proposals/${proposalId}/section_gap/?section_id=${sectionId}`
  );
}

export async function apiDeleteProposalSection(
  proposalId: string,
  sectionId: string
): Promise<void> {
  return apiRequest<void>(`/proposals/${proposalId}/sections/${sectionId}/`, {
    method: 'DELETE',
  });
}

export async function apiReorderProposalSections(
  proposalId: string,
  sectionIds: string[]
): Promise<ApiProposalSection[]> {
  return apiRequest<ApiProposalSection[]>(`/proposals/${proposalId}/reorder_sections/`, {
    method: 'POST',
    body: JSON.stringify({ section_ids: sectionIds.map((id) => parseInt(id, 10)) }),
  });
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

export async function apiAISuggest(
  proposalId: string,
  sectionId: string,
  action: string,
  currentContent?: string
): Promise<{ id: number; section: number; action: string; description: string; generated_content: string; applied: boolean }> {
  return apiRequest(`/proposals/${proposalId}/ai_suggest/`, {
    method: 'POST',
    body: JSON.stringify({
      section_id: parseInt(sectionId),
      action,
      current_content: currentContent || '',
    }),
  });
}

export interface ApiTransitionResponse {
  status: string;
  proposal_id: number;
  proposal_url: string;
  project_id?: number;
  project_url?: string;
}

export async function apiTransitionProposalStatus(
  proposalId: string,
  newStatus: string,
  note?: string,
  options?: { qc_min_score?: number }
): Promise<ApiTransitionResponse> {
  return apiRequest<ApiTransitionResponse>(`/proposals/${proposalId}/transition_status/`, {
    method: 'POST',
    body: JSON.stringify({ status: newStatus, note: note || '', ...options }),
  });
}

export async function apiSubmitProposal(
  proposalId: string,
  note?: string,
  options?: { qc_min_score?: number }
): Promise<{ status: string; submitted_at: string }> {
  return apiRequest(`/proposals/${proposalId}/submit/`, {
    method: 'POST',
    body: JSON.stringify({ note: note || 'Proposta submetida.', ...options }),
  });
}

export async function apiApproveProposalForSubmission(
  proposalId: string,
  note?: string,
  options?: { qc_min_score?: number }
): Promise<ApiTransitionResponse> {
  return apiRequest<ApiTransitionResponse>(`/proposals/${proposalId}/approve_for_submission/`, {
    method: 'POST',
    body: JSON.stringify({ note: note || 'QC aprovado.', ...options }),
  });
}

export interface ApiProposalEvent {
  id: number;
  proposal: number;
  event_type: string;
  event_type_display: string;
  artifact_type: string;
  title: string;
  notes: string;
  occurred_at: string;
  external_url: string;
  attachment: string | null;
  attachment_url: string | null;
  created_by: number | null;
  created_by_detail: { id: number; email: string; first_name: string; last_name: string } | null;
  created_at: string;
  updated_at: string;
}

export interface ApiProposalTeamMatchItem {
  member_id: number;
  user_id: number;
  name: string;
  role: string;
  has_analyzed_cv: boolean;
  overall_score: number | null;
  skills_match_score?: number;
  experience_match_score?: number;
  education_match_score?: number;
  language_match_score?: number;
  missing_skills?: string[];
  recommendations: string[];
}

export interface ApiProposalTeamMatch {
  proposal_id: number;
  opportunity_id: number;
  team_size: number;
  scored_members: number;
  team_score: number;
  items: ApiProposalTeamMatchItem[];
}

export interface ApiComplianceMatrixRow {
  id: number;
  matrix: number;
  requirement_key: string;
  requirement_text: string;
  requirement_category: string;
  priority: 'mandatory' | 'desirable' | 'optional';
  status: 'missing' | 'partial' | 'covered' | 'waived';
  proposal_section: number | null;
  proposal_section_title: string | null;
  evidence_text: string;
  evidence_link: string;
  source_type: string;
  source_reference: string;
  source_trace: Array<Record<string, unknown>>;
  confidence_score: string;
  ai_metadata: Record<string, unknown>;
  human_override: boolean;
  human_override_note: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ApiComplianceMatrix {
  id: number;
  opportunity: number;
  opportunity_title: string;
  status: string;
  generation_version: string;
  source_trace: Array<Record<string, unknown>>;
  ai_metadata: Record<string, unknown>;
  confidence_score: string;
  human_override_count: number;
  generated_by: number | null;
  created_at: string;
  updated_at: string;
  rows: ApiComplianceMatrixRow[];
}

export async function apiGetProposalEvents(proposalId: string): Promise<ApiProposalEvent[]> {
  return apiRequest<ApiProposalEvent[]>(`/proposals/${proposalId}/events/`);
}

export async function apiGetProposalTeamMatch(proposalId: string): Promise<ApiProposalTeamMatch> {
  return apiRequest<ApiProposalTeamMatch>(`/proposals/${proposalId}/team_match/`);
}

export async function apiGetComplianceMatrices(
  opportunityId: string | number
): Promise<PaginatedResponse<ApiComplianceMatrix>> {
  return apiRequest<PaginatedResponse<ApiComplianceMatrix>>(
    `/compliance/matrices/${buildQueryString({ opportunity: opportunityId })}`
  );
}

export async function apiGenerateComplianceMatrix(
  opportunityId: string | number
): Promise<ApiComplianceMatrix> {
  return apiRequest<ApiComplianceMatrix>('/compliance/matrices/generate/', {
    method: 'POST',
    body: JSON.stringify({ opportunity_id: Number(opportunityId) }),
  });
}

export async function apiUpdateComplianceMatrixRow(
  rowId: number,
  data: Partial<Pick<
    ApiComplianceMatrixRow,
    'status' | 'proposal_section' | 'evidence_text' | 'evidence_link' | 'human_override_note'
  >>
): Promise<ApiComplianceMatrixRow> {
  return apiRequest<ApiComplianceMatrixRow>(`/compliance/rows/${rowId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export interface ApiKnowledgeAsset {
  id: number;
  asset_type: string;
  title: string;
  summary: string;
  content: string;
  source_app: string;
  source_model: string;
  source_id: string | null;
  source_url: string;
  metadata: Record<string, unknown>;
  tags: string[];
  country: string;
  sector: string;
  status: string;
  indexed_at: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApiKnowledgeSearchResult {
  asset: ApiKnowledgeAsset;
  score: number;
  reasoning_trace: string[];
  search_mode: string;
}

export interface ApiKnowledgeSearchResponse {
  query: string;
  search_mode: string;
  count: number;
  results: ApiKnowledgeSearchResult[];
}

export async function apiSearchKnowledge(params: {
  q?: string;
  asset_type?: string;
  country?: string;
  sector?: string;
  limit?: number;
}): Promise<ApiKnowledgeSearchResponse> {
  return apiRequest<ApiKnowledgeSearchResponse>(
    `/knowledge/assets/search/${buildQueryString(params)}`
  );
}

export async function apiCreateProposalEvent(
  proposalId: string,
  data: {
    event_type: string;
    artifact_type?: string;
    title: string;
    notes?: string;
    occurred_at?: string;
    external_url?: string;
    attachment?: File;
  }
): Promise<ApiProposalEvent> {
  const token = localStorage.getItem('access_token');
  const formData = new FormData();
  formData.append('event_type', data.event_type);
  if (data.artifact_type) formData.append('artifact_type', data.artifact_type);
  formData.append('title', data.title);
  if (data.notes) formData.append('notes', data.notes);
  if (data.occurred_at) formData.append('occurred_at', data.occurred_at);
  if (data.external_url) formData.append('external_url', data.external_url);
  if (data.attachment) formData.append('attachment', data.attachment);

  const response = await fetch(`/api/proposals/${proposalId}/events/`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || 'Erro ao criar evento');
  }
  return response.json() as Promise<ApiProposalEvent>;
}

export interface ApiQualityCheck {
  id: number;
  proposal: number;
  overall_score: number;
  status: string;
  can_submit: boolean;
  executed_by: number | null;
  executed_at: string | null;
  created_at: string;
  categories: Array<{
    id: number;
    category: string;
    score: number;
    status: string;
    items: Array<{ id: number; description: string; status: string; section: string }>;
  }>;
  suggestions: Array<{
    id: number;
    text: string;
    action: string;
    target_section: string;
    applied: boolean;
    ignored: boolean;
  }>;
  checks: Record<string, {
    score: number;
    status: string;
    items: Array<{ id: number; description: string; status: string; section: string }>;
  }>;
}

export async function apiGetQualityChecks(proposalId: string): Promise<PaginatedResponse<ApiQualityCheck>> {
  return apiRequest<PaginatedResponse<ApiQualityCheck>>(`/quality-checks/?proposal=${proposalId}`);
}

export async function apiCreateQualityCheck(proposalId: string): Promise<ApiQualityCheck> {
  return apiRequest<ApiQualityCheck>('/quality-checks/', {
    method: 'POST',
    body: JSON.stringify({ proposal: parseInt(proposalId) }),
  });
}

export async function apiRunQualityCheck(
  qcId: number,
  categories: Array<{
    category: string;
    score: number;
    status: string;
    items: Array<{ description: string; status: string; section?: string }>;
  }>
): Promise<ApiQualityCheck> {
  return apiRequest<ApiQualityCheck>(`/quality-checks/${qcId}/run/`, {
    method: 'POST',
    body: JSON.stringify({ categories }),
  });
}

export async function apiApproveQualityCheck(
  qcId: number,
  note?: string,
  options?: { qc_min_score?: number }
): Promise<ApiQualityCheck & { proposal_id: number }> {
  return apiRequest<ApiQualityCheck & { proposal_id: number }>(`/quality-checks/${qcId}/approve/`, {
    method: 'POST',
    body: JSON.stringify({ note: note || 'QC aprovado. Proposta pronta para submissão.', ...options }),
  });
}

// ============================================
// DASHBOARD
// ============================================

export interface ApiDashboardStats {
  active_opportunities: number;
  proposals_in_progress: number;
  win_rate: number;
  upcoming_deadlines: number;
  opportunities_by_status: Record<string, number>;
  projects_active: number;
  projects_completed: number;
  projects_on_hold: number;
  scraping_new: number;
  scraping_with_ai: number;
  deadline_items: ApiDeadlineItem[];
}

export interface ApiDeadlineItem {
  id: number;
  title: string;
  client: string;
  deadline: string;
  status: string;
  days_left: number;
}

export interface ApiPipelineItem {
  id: string;
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

export interface ApiFunnelResponse {
  funnel: {
    opportunities: { count: number; label: string };
    proposals: { count: number; label: string; won: number };
    projects: { count: number; label: string; active: number };
  };
  conversion: {
    opp_to_proposal: number;
    proposal_to_project: number;
  };
  financial: {
    pipeline_value: number;
    proposals_value: number;
    portfolio_value: number;
    personnel_costs: number;
    estimated_margin: number;
    currency: string;
  };
}

export async function apiGetDashboardFunnel(): Promise<ApiFunnelResponse> {
  return apiRequest<ApiFunnelResponse>('/dashboard/funnel/');
}

// ============================================
// ANALYTICS
// ============================================

export interface ApiAnalyticsWinRateRow {
  sector?: string;
  country?: string;
  won: number;
  lost: number;
  total_decided: number;
  win_rate: number;
}

export interface ApiAnalyticsPipelineItem {
  id: number;
  title: string;
  status: string;
  value: number;
  currency: string;
  probability: number;
  weighted_value: number;
  score_source: string;
}

export interface ApiAnalyticsForecastPoint {
  month: string;
  tenders: number;
}

export interface ApiAnalyticsForecastInterval {
  month: string;
  lower: number;
  upper: number;
}

export interface ApiAnalyticsTrends {
  meta: {
    country: string;
    sector: string;
    horizon_months: number;
    include_forecast: boolean;
    generated_at: string;
  };
  win_rate_by_sector: ApiAnalyticsWinRateRow[];
  win_rate_by_country: ApiAnalyticsWinRateRow[];
  weighted_pipeline: {
    total_value: number;
    weighted_value: number;
    currency: string;
    count: number;
    items: ApiAnalyticsPipelineItem[];
  };
  avg_stage_duration_days: Record<string, number>;
  opportunity_status_counts: Record<string, number>;
  proposal_outcomes: { won: number; lost: number; total_decided: number; win_rate: number };
  descriptive: {
    demand_velocity: number;
    budget_concentration_index: number;
    seasonality_score: number;
    competitive_density: number;
    avg_lead_time_days: number;
    median_lead_time_days: number;
  };
  predictive: {
    method: string;
    point_estimates: ApiAnalyticsForecastPoint[];
    confidence_intervals: ApiAnalyticsForecastInterval[];
    model_diagnostics: {
      confidence_score: number;
      history_months: number;
      non_zero_months: number;
      recent_3m_average: number;
      monthly_trend: number;
    };
    reasoning_trace: string[];
    warnings: string[];
    recommendations: string[];
  } | null;
  signals: Array<{ type: string; severity: string; message: string; created_at: string }>;
}

export async function apiGetAnalyticsTrends(params?: {
  country?: string;
  sector?: string;
  horizon?: number;
  include_forecast?: boolean;
}): Promise<ApiAnalyticsTrends> {
  const query = new URLSearchParams();
  if (params?.country) query.set('country', params.country);
  if (params?.sector) query.set('sector', params.sector);
  if (params?.horizon) query.set('horizon', String(params.horizon));
  if (params?.include_forecast) query.set('include_forecast', 'true');
  const qs = query.toString() ? `?${query.toString()}` : '';
  return apiRequest<ApiAnalyticsTrends>(`/analytics/trends/${qs}`);
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
  title: string;
  description: string;
  start_date: string | null;
  end_date: string | null;
  is_completed: boolean;
  completion_percentage: number;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectMilestone {
  id: number;
  project: number;
  title: string;
  description: string;
  due_date: string;
  completed_date: string | null;
  status: string;
  deliverables: string;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectRisk {
  id: number;
  project: number;
  title: string;
  description: string;
  severity: string;
  status: string;
  mitigation_plan: string;
  owner: { id: number; name: string; email: string } | null;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectDeliverable {
  id: number;
  project: number;
  phase: number | null;
  phase_name: string | null;
  title: string;
  description: string;
  due_date: string | null;
  submitted_date: string | null;
  status: string;
  status_display: string;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectArtifact {
  id: number;
  project: number;
  phase: number | null;
  artifact_type: string;
  artifact_type_display: string;
  title: string;
  status: string;
  status_display: string;
  file: string | null;
  file_url: string | null;
  external_url: string;
  notes: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectTask {
  id: number;
  project: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string | null;
  assignee: { id: number; name: string; email: string } | null;
  created_at: string;
  updated_at: string;
}

export interface ApiProjectDetail extends ApiProject {
  team: Array<{
    id: number;
    user: { id: number; email: string; first_name: string; last_name: string; name: string; role: string };
    role: string;
    allocation_percentage: number;
    start_date: string | null;
    end_date: string | null;
  }>;
  milestones: ApiProjectMilestone[];
  tasks: ApiProjectTask[];
  risks: ApiProjectRisk[];
  deliverables: ApiProjectDeliverable[];
  artifacts: ApiProjectArtifact[];
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

export async function apiCreateProjectPhase(
  projectId: string,
  data: Partial<ApiProjectPhase>
): Promise<ApiProjectPhase> {
  return apiRequest<ApiProjectPhase>('/projects/phases/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), name: 'custom', ...data }),
  });
}

export async function apiDeleteProjectPhase(phaseId: number): Promise<void> {
  return apiRequest<void>(`/projects/phases/${phaseId}/`, { method: 'DELETE' });
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

export async function apiUpdateProject(
  id: string,
  data: Partial<ApiProject>
): Promise<ApiProject> {
  return apiRequest<ApiProject>(`/projects/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiAddProjectTeamMember(
  projectId: string,
  data: { user: number; role: string; allocation_percentage?: number; start_date?: string; end_date?: string }
): Promise<{ id: number; user: { id: number; email: string; first_name: string; last_name: string; name: string; role: string }; role: string; allocation_percentage: number; start_date: string | null; end_date: string | null }> {
  return apiRequest(`/projects/team-members/`, {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...data }),
  });
}

export async function apiDeleteProjectTeamMember(memberId: number): Promise<void> {
  return apiRequest<void>(`/projects/team-members/${memberId}/`, { method: 'DELETE' });
}

export async function apiCreateProjectMilestone(
  projectId: string,
  data: Partial<ApiProjectMilestone>
): Promise<ApiProjectMilestone> {
  return apiRequest<ApiProjectMilestone>('/projects/milestones/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...data }),
  });
}

export async function apiUpdateProjectMilestone(
  milestoneId: number,
  data: Partial<ApiProjectMilestone>
): Promise<ApiProjectMilestone> {
  return apiRequest<ApiProjectMilestone>(`/projects/milestones/${milestoneId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiDeleteProjectMilestone(milestoneId: number): Promise<void> {
  return apiRequest<void>(`/projects/milestones/${milestoneId}/`, { method: 'DELETE' });
}

export async function apiCreateProjectRisk(
  projectId: string,
  data: Partial<ApiProjectRisk>
): Promise<ApiProjectRisk> {
  return apiRequest<ApiProjectRisk>('/projects/risks/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...data }),
  });
}

export async function apiUpdateProjectRisk(
  riskId: number,
  data: Partial<ApiProjectRisk>
): Promise<ApiProjectRisk> {
  return apiRequest<ApiProjectRisk>(`/projects/risks/${riskId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiDeleteProjectRisk(riskId: number): Promise<void> {
  return apiRequest<void>(`/projects/risks/${riskId}/`, { method: 'DELETE' });
}

export async function apiCreateProjectDeliverable(
  projectId: string,
  data: Partial<ApiProjectDeliverable>
): Promise<ApiProjectDeliverable> {
  return apiRequest<ApiProjectDeliverable>('/projects/deliverables/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...data }),
  });
}

export async function apiUpdateProjectDeliverable(
  deliverableId: number,
  data: Partial<ApiProjectDeliverable>
): Promise<ApiProjectDeliverable> {
  return apiRequest<ApiProjectDeliverable>(`/projects/deliverables/${deliverableId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiDeleteProjectDeliverable(deliverableId: number): Promise<void> {
  return apiRequest<void>(`/projects/deliverables/${deliverableId}/`, { method: 'DELETE' });
}

export async function apiGetProjectArtifacts(projectId: string): Promise<ApiProjectArtifact[]> {
  return apiRequest<ApiProjectArtifact[]>(`/projects/artifacts/?project=${projectId}`);
}

export async function apiCreateProjectArtifact(
  projectId: string,
  data: Omit<Partial<ApiProjectArtifact>, 'file'> & { file?: File }
): Promise<ApiProjectArtifact> {
  const { file, ...rest } = data;
  if (file) {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    formData.append('project', projectId);
    Object.entries(rest).forEach(([k, v]) => { if (v != null) formData.append(k, String(v)); });
    formData.append('file', file);
    const res = await fetch('/api/projects/artifacts/', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error((e as { detail?: string }).detail || 'Erro ao criar artefacto'); }
    return res.json() as Promise<ApiProjectArtifact>;
  }
  return apiRequest<ApiProjectArtifact>('/projects/artifacts/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...rest }),
  });
}

export async function apiUpdateProjectArtifact(
  artifactId: number,
  data: Omit<Partial<ApiProjectArtifact>, 'file'> & { file?: File }
): Promise<ApiProjectArtifact> {
  const { file, ...rest } = data;
  if (file) {
    const token = localStorage.getItem('access_token');
    const formData = new FormData();
    Object.entries(rest).forEach(([k, v]) => { if (v != null) formData.append(k, String(v)); });
    formData.append('file', file);
    const res = await fetch(`/api/projects/artifacts/${artifactId}/`, {
      method: 'PATCH',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error((e as { detail?: string }).detail || 'Erro ao atualizar artefacto'); }
    return res.json() as Promise<ApiProjectArtifact>;
  }
  return apiRequest<ApiProjectArtifact>(`/projects/artifacts/${artifactId}/`, {
    method: 'PATCH',
    body: JSON.stringify(rest),
  });
}

export async function apiCreateProjectTask(
  projectId: string,
  data: Partial<ApiProjectTask>
): Promise<ApiProjectTask> {
  return apiRequest<ApiProjectTask>('/projects/tasks/', {
    method: 'POST',
    body: JSON.stringify({ project: parseInt(projectId), ...data }),
  });
}

export async function apiUpdateProjectTask(
  taskId: number,
  data: Partial<ApiProjectTask>
): Promise<ApiProjectTask> {
  return apiRequest<ApiProjectTask>(`/projects/tasks/${taskId}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function apiDeleteProjectTask(taskId: number): Promise<void> {
  return apiRequest<void>(`/projects/tasks/${taskId}/`, { method: 'DELETE' });
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
  formData.append('file_type', ext === 'doc' ? 'doc' : ext === 'pdf' ? 'pdf' : 'docx');

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
  source_category: string;
  scraper_kind: string;
  scraper_class?: string;
}

export interface ApiScrapingSourceHealth {
  id: number;
  name: string;
  organization: string;
  url: string;
  source_type: string;
  status: string;
  health_status: string;
  health_score: number;
  health_reason: string;
  access: string;
  scraper_class: string;
  scrape_frequency: string;
  last_scraped_at: string | null;
  last_job_status: string | null;
  last_job_at: string | null;
  last_error: string;
  items_found_last_run: number;
  items_new_last_run: number;
  total_opportunities: number;
  imported_opportunities: number;
  last_opportunity_at: string | null;
  production_ready: boolean;
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
  cv_eligible: boolean;
  data_quality_score: string;
  ready_to_import?: boolean;
  import_readiness_reasons?: string[];
  imported_opportunity: number | null;
  source_name?: string;
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

export async function apiGetScrapingSourceHealth(params?: {
  health_status?: string;
  search?: string;
}): Promise<{ count: number; results: ApiScrapingSourceHealth[] }> {
  const query = new URLSearchParams();
  if (params?.health_status) query.set('health_status', params.health_status);
  if (params?.search) query.set('search', params.search);
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return apiRequest<{ count: number; results: ApiScrapingSourceHealth[] }>(`/scraping/sources/health/${suffix}`);
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

export async function apiImportReadyScrapedOpportunities(limit = 50, ids?: number[]): Promise<{
  status: string;
  imported_count: number;
  skipped_count: number;
  failed_count: number;
  processed_count: number;
  imported: Array<{
    id: number;
    title: string;
    opportunity_id: number;
    opportunity_url: string;
    status: string;
    created: boolean;
  }>;
  skipped: Array<{
    id: number;
    title: string;
    reasons: string[];
  }>;
  failed: Array<{
    id: number;
    title: string;
    reason: string;
  }>;
}> {
  return apiRequest<{
    status: string;
    imported_count: number;
    skipped_count: number;
    failed_count: number;
    processed_count: number;
    imported: Array<{
      id: number;
      title: string;
      opportunity_id: number;
      opportunity_url: string;
      status: string;
      created: boolean;
    }>;
    skipped: Array<{
      id: number;
      title: string;
      reasons: string[];
    }>;
    failed: Array<{
      id: number;
      title: string;
      reason: string;
    }>;
  }>('/scraping/opportunities/import_ready/', {
    method: 'POST',
    body: JSON.stringify({ limit, ids }),
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
  ready_to_import?: number;
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
