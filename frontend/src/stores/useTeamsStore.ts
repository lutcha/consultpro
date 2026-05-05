import { create } from 'zustand';
import type {
  TeamStats,
  PipelinePhase,
  InternalTeamMember,
  Consultant,
  ProjectTeam,
} from '@/types/teams';
import {
  teamStats,
  pipelinePhases,
  internalTeamMembers,
  consultants,
  projectTeams,
} from '@/lib/mockTeamsData';

interface TeamsState {
  // Data
  stats: TeamStats;
  pipeline: PipelinePhase[];
  internalMembers: InternalTeamMember[];
  consultants: Consultant[];
  projectTeams: ProjectTeam[];

  // Loading / Error
  isLoading: boolean;
  error: string | null;

  // Filters
  searchQuery: string;
  selectedPhase: string | null;
  selectedSeniority: string | null;
  selectedSector: string | null;
  selectedAvailability: string | null;

  // Actions
  fetchAll: () => Promise<void>;
  setSearchQuery: (q: string) => void;
  setSelectedPhase: (phase: string | null) => void;
  setSelectedSeniority: (s: string | null) => void;
  setSelectedSector: (s: string | null) => void;
  setSelectedAvailability: (a: string | null) => void;
  clearFilters: () => void;
  clearError: () => void;

  // Getters (computed)
  getFilteredInternalMembers: () => InternalTeamMember[];
  getFilteredConsultants: () => Consultant[];
  getFilteredProjectTeams: () => ProjectTeam[];
  getAllSectors: () => string[];
  getAllPhases: () => string[];
}

export const useTeamsStore = create<TeamsState>((set, get) => ({
  stats: teamStats,
  pipeline: pipelinePhases,
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
      // Simulate API delay
      await new Promise((resolve) => setTimeout(resolve, 400));
      set({
        internalMembers: internalTeamMembers,
        consultants: consultants,
        projectTeams: projectTeams,
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
    set({
      searchQuery: '',
      selectedPhase: null,
      selectedSeniority: null,
      selectedSector: null,
      selectedAvailability: null,
    }),

  clearError: () => set({ error: null }),

  getFilteredInternalMembers: () => {
    const { internalMembers, searchQuery, selectedPhase } = get();
    return internalMembers.filter((m) => {
      const matchesSearch =
        !searchQuery ||
        m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesPhase = !selectedPhase || m.phase === selectedPhase;
      return matchesSearch && matchesPhase;
    });
  },

  getFilteredConsultants: () => {
    const { consultants, searchQuery, selectedSeniority, selectedSector, selectedAvailability } = get();
    return consultants.filter((c) => {
      const matchesSearch =
        !searchQuery ||
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.skills.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase())) ||
        c.sectors.some((s) => s.toLowerCase().includes(searchQuery.toLowerCase()));
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
    return projectTeams.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.client.toLowerCase().includes(q) ||
        p.internalMembers.some((m) => m.name.toLowerCase().includes(q))
    );
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
