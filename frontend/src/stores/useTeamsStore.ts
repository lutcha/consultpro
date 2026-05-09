import { create } from 'zustand';
import type {
  TeamStats,
  PipelinePhase,
  InternalTeamMember,
  Consultant,
  ProjectTeam,
} from '@/types/teams';
import {
  apiGetUsers,
  apiGetConsultants,
  apiGetTeams,
} from '@/lib/api';
import type { ApiUser, ApiConsultant, ApiTeam } from '@/lib/api';

// ── Mappers ──────────────────────────────────────────────────────────────────

function mapUserToInternalMember(u: ApiUser): InternalTeamMember {
  return {
    id: String(u.id),
    name: u.name || u.email,
    email: u.email,
    avatar: u.avatar ?? undefined,
    role: u.role,
    phase: u.availability === 'available' ? 'Disponivel' : u.availability === 'busy' ? 'Em Projeto' : 'Indisponivel',
    department: u.role,
    skills: u.skills ?? [],
    availability: (u.availability as InternalTeamMember['availability']) ?? 'available',
    projectsCount: 0,
    joinedAt: new Date().toISOString(),
  };
}

function mapConsultantToConsultant(c: ApiConsultant): Consultant {
  const profile = c.consultant_profile;
  const years = c.years_experience ?? 0;
  const seniority: Consultant['seniority'] =
    years >= 10 ? 'senior' : years >= 4 ? 'mid' : 'junior';
  return {
    id: String(c.id),
    name: c.name || c.email,
    email: c.email,
    avatar: c.avatar ?? undefined,
    seniority,
    seniorityLabel: seniority === 'senior' ? 'Senior' : seniority === 'mid' ? 'Mid-Level' : 'Junior',
    availability: (c.availability as Consultant['availability']) ?? 'available',
    location: 'N/D',
    education: profile?.education ?? '',
    yearsExperience: years,
    projectsCompleted: profile?.total_projects_completed ?? 0,
    dailyRate: profile ? parseFloat(profile.daily_rate) || 0 : 0,
    currency: profile?.currency ?? 'EUR',
    rating: profile ? parseFloat(profile.performance_rating) || 0 : 0,
    skills: c.skills ?? [],
    languages: c.languages ?? [],
    sectors: profile?.specializations ?? [],
    lastProject: { name: '—', date: '—' },
  };
}

function mapTeamToProjectTeam(t: ApiTeam): ProjectTeam {
  const internal = t.members.filter((m) => m.role !== 'consultant');
  const external = t.members.filter((m) => m.role === 'consultant');
  return {
    id: String(t.id),
    name: t.name,
    client: t.description || '—',
    phase: 'Em Curso',
    status: 'in_proposal',
    internalMembers: internal.map((m) => ({
      id: String(m.id),
      name: m.name || m.email,
      role: m.role,
      type: 'internal' as const,
    })),
    externalMembers: external.map((m) => ({
      id: String(m.id),
      name: m.name || m.email,
      role: m.role,
      type: 'external' as const,
    })),
  };
}

// ── Store ─────────────────────────────────────────────────────────────────────

interface TeamsState {
  stats: TeamStats;
  pipeline: PipelinePhase[];
  internalMembers: InternalTeamMember[];
  consultants: Consultant[];
  projectTeams: ProjectTeam[];
  isLoading: boolean;
  error: string | null;
  searchQuery: string;
  selectedPhase: string | null;
  selectedSeniority: string | null;
  selectedSector: string | null;
  selectedAvailability: string | null;

  fetchAll: () => Promise<void>;
  setSearchQuery: (q: string) => void;
  setSelectedPhase: (phase: string | null) => void;
  setSelectedSeniority: (s: string | null) => void;
  setSelectedSector: (s: string | null) => void;
  setSelectedAvailability: (a: string | null) => void;
  clearFilters: () => void;
  clearError: () => void;
  getFilteredInternalMembers: () => InternalTeamMember[];
  getFilteredConsultants: () => Consultant[];
  getFilteredProjectTeams: () => ProjectTeam[];
  getAllSectors: () => string[];
  getAllPhases: () => string[];
}

export const useTeamsStore = create<TeamsState>((set, get) => ({
  stats: { internalMembers: 0, externalConsultants: 0, activeProjects: 0, averageRating: 0 },
  pipeline: [],
  internalMembers: [],
  consultants: [],
  projectTeams: [],
  isLoading: false,
  error: null,
  searchQuery: '',
  selectedPhase: null,
  selectedSeniority: null,
  selectedSector: null,
  selectedAvailability: null,

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const [usersRes, consultantsRes, teamsRes] = await Promise.all([
        apiGetUsers(),
        apiGetConsultants(),
        apiGetTeams(),
      ]);

      const internalMembers = usersRes.results.map(mapUserToInternalMember);
      const consultants = consultantsRes.results.map(mapConsultantToConsultant);
      const projectTeams = teamsRes.results.map(mapTeamToProjectTeam);

      const avgRating =
        consultants.length > 0
          ? Math.round((consultants.reduce((s, c) => s + c.rating, 0) / consultants.length) * 10) / 10
          : 0;

      const pipeline: PipelinePhase[] = [
        { phase: 'Disponivel', members: internalMembers.filter((m) => m.availability === 'available').length },
        { phase: 'Em Projeto', members: internalMembers.filter((m) => m.availability === 'busy').length },
        { phase: 'Indisponivel', members: internalMembers.filter((m) => m.availability === 'unavailable').length },
      ].filter((p) => p.members > 0);

      set({
        internalMembers,
        consultants,
        projectTeams,
        pipeline,
        stats: {
          internalMembers: internalMembers.length,
          externalConsultants: consultants.length,
          activeProjects: projectTeams.length,
          averageRating: avgRating,
        },
        isLoading: false,
      });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  setSearchQuery: (q) => set({ searchQuery: q }),
  setSelectedPhase: (phase) => set({ selectedPhase: phase }),
  setSelectedSeniority: (s) => set({ selectedSeniority: s }),
  setSelectedSector: (s) => set({ selectedSector: s }),
  setSelectedAvailability: (a) => set({ selectedAvailability: a }),
  clearFilters: () =>
    set({ searchQuery: '', selectedPhase: null, selectedSeniority: null, selectedSector: null, selectedAvailability: null }),
  clearError: () => set({ error: null }),

  getFilteredInternalMembers: () => {
    const { internalMembers, searchQuery, selectedPhase } = get();
    return internalMembers.filter((m) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch = !q || m.name.toLowerCase().includes(q) || m.role.toLowerCase().includes(q) || m.skills.some((s) => s.toLowerCase().includes(q));
      const matchesPhase = !selectedPhase || m.phase === selectedPhase;
      return matchesSearch && matchesPhase;
    });
  },

  getFilteredConsultants: () => {
    const { consultants, searchQuery, selectedSeniority, selectedSector, selectedAvailability } = get();
    return consultants.filter((c) => {
      const q = searchQuery.toLowerCase();
      const matchesSearch = !q || c.name.toLowerCase().includes(q) || c.skills.some((s) => s.toLowerCase().includes(q)) || c.sectors.some((s) => s.toLowerCase().includes(q));
      const matchesSeniority = !selectedSeniority || c.seniority === selectedSeniority;
      const matchesSector = !selectedSector || c.sectors.includes(selectedSector);
      const matchesAvailability = !selectedAvailability || c.availability === selectedAvailability;
      return matchesSearch && matchesSeniority && matchesSector && matchesAvailability;
    });
  },

  getFilteredProjectTeams: () => {
    const { projectTeams, searchQuery } = get();
    if (!searchQuery) return projectTeams;
    const q = searchQuery.toLowerCase();
    return projectTeams.filter((p) => p.name.toLowerCase().includes(q) || p.client.toLowerCase().includes(q) || p.internalMembers.some((m) => m.name.toLowerCase().includes(q)));
  },

  getAllSectors: () => {
    const sectors = new Set<string>();
    get().consultants.forEach((c) => c.sectors.forEach((s) => sectors.add(s)));
    return Array.from(sectors).sort();
  },

  getAllPhases: () => {
    const phases = new Set<string>();
    get().internalMembers.forEach((m) => phases.add(m.phase));
    return Array.from(phases).sort();
  },
}));
