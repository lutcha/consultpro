// ============================================
// OPPORTUNITY STORE - Zustand
// ============================================

import { create } from 'zustand';
import type { Opportunity, OpportunityStatus } from '@/types';
import {
  apiGetOpportunities,
  apiGetOpportunity,
  apiUpdateOpportunityStatus,
} from '@/lib/api';
import {
  mapApiOpportunity,
  mapApiOpportunityListItem,
} from '@/lib/apiMappers';

interface OpportunityState {
  opportunities: Opportunity[];
  selectedOpportunity: Opportunity | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setOpportunities: (opportunities: Opportunity[]) => void;
  selectOpportunity: (id: string) => Promise<void>;
  updateStatus: (id: string, status: OpportunityStatus) => Promise<void>;
  addOpportunity: (opportunity: Opportunity) => void;
  updateOpportunity: (id: string, updates: Partial<Opportunity>) => void;
  fetchOpportunities: () => Promise<void>;
}

export const useOpportunityStore = create<OpportunityState>((set, get) => ({
  opportunities: [],
  selectedOpportunity: null,
  isLoading: false,
  error: null,

  setOpportunities: (opportunities) => set({ opportunities }),

  selectOpportunity: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiGetOpportunity(id);
      const opportunity = mapApiOpportunity(data);
      set({ selectedOpportunity: opportunity, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch opportunity',
        isLoading: false,
      });
    }
  },

  updateStatus: async (id, status) => {
    try {
      const data = await apiUpdateOpportunityStatus(id, status);
      const updated = mapApiOpportunity(data);
      set((state) => ({
        opportunities: state.opportunities.map((opp) =>
          opp.id === id ? updated : opp
        ),
        selectedOpportunity:
          state.selectedOpportunity?.id === id
            ? updated
            : state.selectedOpportunity,
      }));
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : 'Failed to update status',
      });
    }
  },

  addOpportunity: (opportunity) => {
    set((state) => ({
      opportunities: [...state.opportunities, opportunity],
    }));
  },

  updateOpportunity: (id, updates) => {
    set((state) => ({
      opportunities: state.opportunities.map((opp) =>
        opp.id === id ? { ...opp, ...updates, updatedAt: new Date() } : opp
      ),
    }));
  },

  fetchOpportunities: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiGetOpportunities();
      const opportunities = response.results.map(mapApiOpportunityListItem);
      set({ opportunities, isLoading: false });
    } catch (error) {
      set({
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch opportunities',
        isLoading: false,
      });
    }
  },
}));
