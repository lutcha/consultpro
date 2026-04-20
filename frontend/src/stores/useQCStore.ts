// ============================================
// QUALITY CHECK STORE - Zustand
// ============================================

import { create } from 'zustand';
import type { QCState } from '@/types';
import { mockQCState } from '@/lib/mockData';

interface QCStoreState {
  qcState: QCState | null;
  isRunning: boolean;
  error: string | null;

  // Actions
  setQCState: (state: QCState) => void;
  runQC: (proposalId: string) => Promise<void>;
  applySuggestion: (suggestionId: string) => void;
  ignoreSuggestion: (suggestionId: string) => void;
  canSubmit: () => boolean;
}

export const useQCStore = create<QCStoreState>((set, get) => ({
  qcState: null,
  isRunning: false,
  error: null,

  setQCState: (qcState) => set({ qcState }),

  runQC: async (proposalId) => {
    set({ isRunning: true, error: null });
    try {
      // TODO: Connect to real QC API when available
      // const response = await apiRequest(`/quality-checks/${proposalId}/run/`, { method: 'POST' });

      // Simulate API call with mock data for now
      setTimeout(() => {
        set({
          qcState: { ...mockQCState, proposalId },
          isRunning: false,
        });
      }, 2000);
    } catch (error) {
      set({ error: 'Failed to run quality check', isRunning: false });
    }
  },

  applySuggestion: (suggestionId) => {
    set((state) => {
      if (!state.qcState) return state;

      return {
        qcState: {
          ...state.qcState,
          suggestions: state.qcState.suggestions.map((sugg) =>
            sugg.id === suggestionId ? { ...sugg, applied: true } : sugg
          ),
        },
      };
    });
  },

  ignoreSuggestion: (suggestionId) => {
    set((state) => {
      if (!state.qcState) return state;

      return {
        qcState: {
          ...state.qcState,
          suggestions: state.qcState.suggestions.filter(
            (sugg) => sugg.id !== suggestionId
          ),
        },
      };
    });
  },

  canSubmit: () => {
    const state = get().qcState;
    if (!state) return false;
    return state.overallScore >= 85 && state.checks.attachments.status !== 'fail';
  },
}));
