// ============================================
// PROPOSAL STORE - Zustand
// ============================================

import { create } from 'zustand';
import type { Proposal, ProposalStatus } from '@/types';
import {
  apiGetProposals,
  apiGetProposal,
  apiCreateProposalSection,
  apiUpdateProposalSection,
} from '@/lib/api';
import { mapApiProposal, mapApiProposalListItem, mapApiProposalSection } from '@/lib/apiMappers';

interface ProposalState {
  proposals: Proposal[];
  selectedProposal: Proposal | null;
  isLoading: boolean;
  error: string | null;
  autoSaveStatus: 'idle' | 'saving' | 'saved' | 'error';

  // Actions
  setProposals: (proposals: Proposal[]) => void;
  selectProposal: (id: string) => Promise<void>;
  fetchProposals: () => Promise<void>;
  updateSection: (
    proposalId: string,
    sectionId: string,
    content: string
  ) => Promise<void>;
  addSection: (proposalId: string, title: string, content?: string) => Promise<string>;
  updateStatus: (id: string, status: ProposalStatus) => void;
  addProposal: (proposal: Proposal) => void;
  saveProposal: (proposal: Proposal) => Promise<void>;
  applyAISuggestion: (
    proposalId: string,
    sectionId: string,
    suggestionId: string
  ) => void;
}

export const useProposalStore = create<ProposalState>((set, _get) => ({
  proposals: [],
  selectedProposal: null,
  isLoading: false,
  error: null,
  autoSaveStatus: 'idle',

  setProposals: (proposals) => set({ proposals }),

  selectProposal: async (id) => {
    // Always clear selectedProposal first so stale data from a previous proposal
    // is never shown while the new one loads (prevents "always shows One Health" bug)
    set({ isLoading: true, error: null, selectedProposal: null });
    try {
      const data = await apiGetProposal(id);
      const proposal = mapApiProposal(data);
      set({ selectedProposal: proposal, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch proposal',
        isLoading: false,
      });
    }
  },

  fetchProposals: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiGetProposals();
      const proposals = response.results.map(mapApiProposalListItem);
      set({ proposals, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch proposals',
        isLoading: false,
      });
    }
  },

  updateSection: async (proposalId, sectionId, content) => {
    set({ autoSaveStatus: 'saving' });
    try {
      await apiUpdateProposalSection(proposalId, sectionId, {
        content,
        is_complete: content.length > 50,
      });

      set((state) => ({
        proposals: state.proposals.map((prop) =>
          prop.id === proposalId
            ? {
                ...prop,
                sections: prop.sections.map((sec) =>
                  sec.id === sectionId
                    ? { ...sec, content, isComplete: content.length > 50 }
                    : sec
                ),
                updatedAt: new Date(),
              }
            : prop
        ),
        selectedProposal:
          state.selectedProposal?.id === proposalId
            ? {
                ...state.selectedProposal,
                sections: state.selectedProposal.sections.map((sec) =>
                  sec.id === sectionId
                    ? { ...sec, content, isComplete: content.length > 50 }
                    : sec
                ),
                updatedAt: new Date(),
              }
            : state.selectedProposal,
        autoSaveStatus: 'saved',
      }));
    } catch (error) {
      set({ autoSaveStatus: 'error' });
    }
  },

  addSection: async (proposalId, title, content = '') => {
    set({ autoSaveStatus: 'saving', error: null });
    try {
      const created = await apiCreateProposalSection(proposalId, {
        title,
        content,
        section_type: 'custom',
      });
      const section = mapApiProposalSection(created);
      set((state) => ({
        selectedProposal:
          state.selectedProposal?.id === proposalId
            ? {
                ...state.selectedProposal,
                sections: [...state.selectedProposal.sections, section],
                updatedAt: new Date(),
              }
            : state.selectedProposal,
        autoSaveStatus: 'saved',
      }));
      return section.id;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to add proposal section',
        autoSaveStatus: 'error',
      });
      throw error;
    }
  },

  updateStatus: (id, status) => {
    set((state) => ({
      proposals: state.proposals.map((prop) =>
        prop.id === id ? { ...prop, status, updatedAt: new Date() } : prop
      ),
      // Also update selectedProposal so the editor reflects the new status immediately
      selectedProposal:
        state.selectedProposal?.id === id
          ? { ...state.selectedProposal, status, updatedAt: new Date() }
          : state.selectedProposal,
    }));
  },

  addProposal: (proposal) => {
    set((state) => ({
      proposals: [...state.proposals, proposal],
    }));
  },

  saveProposal: async (proposal) => {
    set({ autoSaveStatus: 'saving' });
    try {
      // For full save, we would PUT the whole proposal
      // For now, just update local state
      setTimeout(() => {
        set((state) => ({
          proposals: state.proposals.map((p) =>
            p.id === proposal.id ? { ...proposal, updatedAt: new Date() } : p
          ),
          autoSaveStatus: 'saved',
        }));
      }, 800);
    } catch (error) {
      set({ autoSaveStatus: 'error' });
    }
  },

  applyAISuggestion: (proposalId, sectionId, suggestionId) => {
    set((state) => ({
      proposals: state.proposals.map((prop) =>
        prop.id === proposalId
          ? {
              ...prop,
              sections: prop.sections.map((sec) =>
                sec.id === sectionId
                  ? {
                      ...sec,
                      aiSuggestions: sec.aiSuggestions?.map((sugg) =>
                        sugg.id === suggestionId
                          ? { ...sugg, applied: true }
                          : sugg
                      ),
                    }
                  : sec
              ),
            }
          : prop
      ),
    }));
  },
}));
