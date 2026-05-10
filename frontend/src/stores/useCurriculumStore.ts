import { create } from 'zustand';
import type { Curriculum, CVTemplate, TemplateMatch, CVSuggestion } from '@/types';
import {
  apiGetCurricula,
  apiUploadCV,
  apiAnalyzeCV,
  apiGetCVSuggestions,
  apiApplyCVSuggestion,
  apiGetCVTemplates,
} from '@/lib/api';
import type { ApiCurriculum, ApiCVTemplate, ApiCVSuggestion } from '@/lib/api';

// ── Mappers ──────────────────────────────────────────────────────────────────

function mapCurriculum(c: ApiCurriculum): Curriculum {
  return {
    id: String(c.id),
    fileName: c.file_name,
    fileType: (c.file_type || 'pdf') as Curriculum['fileType'],
    status: (c.status || 'uploaded') as Curriculum['status'],
    analysisScore: c.analysis_score ?? 0,
    extractedData: (c.extracted_data || {}) as any,
    templateMatches: [],
    suggestions: [],
    createdAt: new Date(c.created_at),
    updatedAt: new Date(c.updated_at),
  };
}

function mapTemplate(t: ApiCVTemplate): CVTemplate {
  return {
    id: String(t.id),
    name: t.name,
    organization: (t.organization || 'generic') as CVTemplate['organization'],
    organizationName: t.organization_name,
    description: t.description,
    requiredSections: (t.required_sections || []) as CVTemplate['requiredSections'],
    formatRules: (t.format_rules || []) as CVTemplate['formatRules'],
    maxLengthPages: t.max_length_pages ?? undefined,
    isActive: t.is_active,
  };
}

function mapSuggestion(s: ApiCVSuggestion): CVSuggestion {
  return {
    id: String(s.id),
    type: (s.type || 'content') as CVSuggestion['type'],
    priority: (s.priority || 'medium') as CVSuggestion['priority'],
    message: s.message,
    context: s.context,
    autoFixable: s.auto_fixable,
    fixed: s.fixed,
    createdAt: new Date(s.created_at),
  };
}

// ── Store ────────────────────────────────────────────────────────────────────

interface CurriculumState {
  curricula: Curriculum[];
  selectedCV: Curriculum | null;
  templates: CVTemplate[];
  matches: TemplateMatch[];
  suggestions: CVSuggestion[];
  isLoading: boolean;
  isLoadingTemplates: boolean;
  isAnalyzing: boolean;
  uploadProgress: number;
  error: string | null;

  fetchCurricula: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
  fetchMatches: (curriculumId: string) => Promise<void>;
  fetchSuggestions: (curriculumId: string) => Promise<void>;
  selectCV: (cv: Curriculum | null) => void;
  uploadCV: (file: File) => Promise<Curriculum>;
  analyzeCV: (curriculumId: string) => Promise<void>;
  applySuggestion: (suggestionId: string) => Promise<void>;
  addCurriculum: (cv: Curriculum) => void;
  clearError: () => void;
}

export const useCurriculumStore = create<CurriculumState>((set, get) => ({
  curricula: [],
  selectedCV: null,
  templates: [],
  matches: [],
  suggestions: [],
  isLoading: false,
  isLoadingTemplates: false,
  isAnalyzing: false,
  uploadProgress: 0,
  error: null,

  fetchCurricula: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await apiGetCurricula();
      const curricula = res.results.map(mapCurriculum);
      const first = curricula[0] ?? null;
      set({ curricula, selectedCV: first, isLoading: false });

      if (first) {
        const rawSugs = await apiGetCVSuggestions(Number(first.id));
        set({ suggestions: rawSugs.map(mapSuggestion) });
      }
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  fetchTemplates: async () => {
    set({ isLoadingTemplates: true, error: null });
    try {
      const res = await apiGetCVTemplates();
      set({ templates: res.results.map(mapTemplate), isLoadingTemplates: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoadingTemplates: false });
    }
  },

  fetchMatches: async (curriculumId) => {
    const cv = get().curricula.find((c) => c.id === curriculumId);
    set({ matches: cv?.templateMatches ?? [] });
  },

  fetchSuggestions: async (curriculumId) => {
    set({ isLoading: true, error: null });
    try {
      const rawSugs = await apiGetCVSuggestions(Number(curriculumId));
      set({ suggestions: rawSugs.map(mapSuggestion), isLoading: false });
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false });
    }
  },

  selectCV: (cv) => set({ selectedCV: cv }),

  uploadCV: async (file: File) => {
    set({ isLoading: true, uploadProgress: 10, error: null });
    try {
      set({ uploadProgress: 40 });
      const apiCv = await apiUploadCV(file);
      const cv = mapCurriculum(apiCv);
      set((state) => ({
        curricula: [cv, ...state.curricula],
        selectedCV: cv,
        uploadProgress: 100,
        isLoading: false,
      }));
      return cv;
    } catch (err) {
      set({ error: (err as Error).message, isLoading: false, uploadProgress: 0 });
      throw err;
    }
  },

  analyzeCV: async (curriculumId: string) => {
    set({ isAnalyzing: true, error: null });
    try {
      const apiCv = await apiAnalyzeCV(Number(curriculumId));
      const cv = mapCurriculum(apiCv);
      const rawSugs = await apiGetCVSuggestions(Number(curriculumId));
      set((state) => ({
        curricula: state.curricula.map((c) => c.id === curriculumId ? cv : c),
        selectedCV: cv,
        suggestions: rawSugs.map(mapSuggestion),
        isAnalyzing: false,
      }));
    } catch (err) {
      set({ error: (err as Error).message, isAnalyzing: false });
    }
  },

  applySuggestion: async (suggestionId: string) => {
    const { selectedCV } = get();
    if (!selectedCV) return;
    try {
      await apiApplyCVSuggestion(Number(selectedCV.id), Number(suggestionId));
      set((state) => ({
        suggestions: state.suggestions.map((s) =>
          s.id === suggestionId ? { ...s, fixed: true } : s
        ),
      }));
    } catch (err) {
      set({ error: (err as Error).message });
    }
  },

  addCurriculum: (cv) => set((state) => ({ curricula: [...state.curricula, cv] })),
  clearError: () => set({ error: null }),
}));
