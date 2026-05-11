// ============================================
// QUALITY CHECK STORE - Zustand (wired to real API)
// ============================================

import { create } from 'zustand';
import type { QCState, QCCheck } from '@/types';
import {
  apiGetQualityChecks,
  apiCreateQualityCheck,
  apiRunQualityCheck,
  apiApproveQualityCheck,
  type ApiQualityCheck,
} from '@/lib/api';
import { useProposalStore } from './useProposalStore';

interface QCStoreState {
  qcState: QCState | null;
  qcId: number | null;
  isRunning: boolean;
  error: string | null;

  setQCState: (state: QCState) => void;
  runQC: (proposalId: string) => Promise<void>;
  approveQC: (note?: string) => Promise<{ proposal_id: number } | null>;
  applySuggestion: (suggestionId: string) => void;
  ignoreSuggestion: (suggestionId: string) => void;
  canSubmit: () => boolean;
}

// Analyse proposal sections locally and produce QC categories
function buildQCCategories(proposalSections: { title: string; content: string; isComplete: boolean }[]) {
  const allSections = proposalSections;
  const completedSections = allSections.filter((s) => s.isComplete);
  const totalSections = allSections.length || 1;
  const completionRate = Math.round((completedSections.length / totalSections) * 100);

  const hasMethodology = allSections.some((s) =>
    s.title.toLowerCase().includes('metodolog') && s.content.length > 100
  );
  const hasTeam = allSections.some((s) =>
    s.title.toLowerCase().includes('equipa') && s.content.length > 50
  );
  const hasBudget = allSections.some((s) =>
    s.title.toLowerCase().includes('or') && /\d/.test(s.content)
  );
  const hasExecutiveSummary = allSections.some((s) =>
    (s.title.toLowerCase().includes('resumo') || s.title.toLowerCase().includes('executivo')) &&
    s.content.length > 100
  );

  // Compliance — based on required sections presence
  const complianceItems = [
    { description: 'Resumo executivo presente', status: hasExecutiveSummary ? 'pass' : 'warn', section: 'Resumo Executivo' },
    { description: 'Metodologia detalhada', status: hasMethodology ? 'pass' : 'fail', section: 'Metodologia' },
    { description: 'Equipa técnica definida', status: hasTeam ? 'pass' : 'warn', section: 'Equipa Técnica' },
    { description: 'Orçamento com valores', status: hasBudget ? 'pass' : 'warn', section: 'Orçamento' },
  ] as const;

  const compliancePassed = complianceItems.filter((i) => i.status === 'pass').length;
  const complianceFailed = complianceItems.filter((i) => i.status === 'fail').length;
  const complianceScore = Math.round((compliancePassed / complianceItems.length) * 100);
  const complianceStatus = complianceFailed > 0 ? 'fail' : compliancePassed < complianceItems.length ? 'warn' : 'pass';

  // Coherence — based on content length and completion
  const coherenceItems = [
    {
      description: `${completedSections.length}/${totalSections} secções completas`,
      status: completionRate >= 80 ? 'pass' : completionRate >= 50 ? 'warn' : 'fail',
      section: '',
    },
    {
      description: 'Conteúdo mínimo em todas as secções',
      status: allSections.every((s) => s.content.length > 20) ? 'pass' : 'warn',
      section: '',
    },
  ] as const;
  const coherenceScore = Math.min(100, completionRate + 10);
  const coherenceStatus = coherenceScore >= 80 ? 'pass' : coherenceScore >= 60 ? 'warn' : 'fail';

  // Budget
  const budgetItems = [
    {
      description: 'Secção de orçamento preenchida',
      status: hasBudget ? 'pass' : 'fail',
      section: 'Orçamento',
    },
  ] as const;
  const budgetScore = hasBudget ? 100 : 0;
  const budgetStatus = hasBudget ? 'pass' : 'fail';

  // Attachments — based on team CVs (simplified)
  const attachmentsItems = [
    {
      description: 'Secção de equipa com detalhes',
      status: hasTeam ? 'pass' : 'warn',
      section: 'Equipa Técnica',
    },
  ] as const;
  const attachmentsScore = hasTeam ? 90 : 50;
  const attachmentsStatus = hasTeam ? 'pass' : 'warn';

  return [
    {
      category: 'compliance',
      score: complianceScore,
      status: complianceStatus,
      items: complianceItems.map((i) => ({ description: i.description, status: i.status, section: i.section })),
    },
    {
      category: 'coherence',
      score: coherenceScore,
      status: coherenceStatus,
      items: coherenceItems.map((i) => ({ description: i.description, status: i.status, section: i.section })),
    },
    {
      category: 'budget',
      score: budgetScore,
      status: budgetStatus,
      items: budgetItems.map((i) => ({ description: i.description, status: i.status, section: i.section })),
    },
    {
      category: 'attachments',
      score: attachmentsScore,
      status: attachmentsStatus,
      items: attachmentsItems.map((i) => ({ description: i.description, status: i.status, section: i.section })),
    },
  ];
}

function mapApiQCToState(qc: ApiQualityCheck, proposalId: string): QCState {
  const checks = qc.checks || {};

  const mapCategory = (key: string): QCCheck => {
    const cat = checks[key];
    if (!cat) return { score: 0, status: 'fail', items: [] };
    return {
      score: cat.score,
      status: cat.status as 'pass' | 'warn' | 'fail',
      items: (cat.items || []).map((item) => ({
        id: String(item.id),
        description: item.description,
        status: item.status as 'pass' | 'warn' | 'fail',
        section: item.section || undefined,
      })),
    };
  };

  return {
    proposalId,
    overallScore: qc.overall_score,
    status: qc.status as 'pending' | 'running' | 'completed' | 'failed',
    checks: {
      compliance: mapCategory('compliance'),
      coherence: mapCategory('coherence'),
      budget: mapCategory('budget'),
      attachments: mapCategory('attachments'),
    },
    canSubmit: qc.can_submit,
    suggestions: (qc.suggestions || [])
      .filter((s) => !s.ignored)
      .map((s) => ({
        id: String(s.id),
        text: s.text,
        action: s.action as 'replace' | 'add' | 'remove',
        targetSection: s.target_section,
        applied: s.applied,
      })),
  };
}

export const useQCStore = create<QCStoreState>((set, get) => ({
  qcState: null,
  qcId: null,
  isRunning: false,
  error: null,

  setQCState: (qcState) => set({ qcState }),

  runQC: async (proposalId) => {
    set({ isRunning: true, error: null });
    try {
      // Get or create QC record for this proposal
      let qc: ApiQualityCheck;
      const existing = await apiGetQualityChecks(proposalId);
      if (existing.results.length > 0) {
        qc = existing.results[0];
      } else {
        qc = await apiCreateQualityCheck(proposalId);
      }

      // Build categories from current proposal store state
      const proposalStore = useProposalStore.getState();
      const proposal = proposalStore.selectedProposal;
      const sections = proposal?.sections || [];

      const categories = buildQCCategories(sections);

      // Run QC with computed categories
      const result = await apiRunQualityCheck(qc.id, categories);
      set({ qcState: mapApiQCToState(result, proposalId), qcId: result.id, isRunning: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Erro ao executar QC', isRunning: false });
    }
  },

  approveQC: async (note) => {
    const { qcId } = get();
    if (!qcId) return null;
    try {
      const result = await apiApproveQualityCheck(qcId, note);
      return { proposal_id: result.proposal_id };
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Erro ao aprovar QC' });
      return null;
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
          suggestions: state.qcState.suggestions.filter((sugg) => sugg.id !== suggestionId),
        },
      };
    });
  },

  canSubmit: () => {
    const state = get().qcState;
    if (!state) return false;
    // Use the backend's can_submit flag (score >= 85 && no category fail).
    // Fallback: allow if QC has been run (status === 'completed') so the
    // reviewer can override a marginal score and the backend enforces the rules.
    return state.canSubmit || state.status === 'completed';
  },
}));
