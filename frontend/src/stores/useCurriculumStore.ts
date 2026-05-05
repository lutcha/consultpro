import { create } from 'zustand';
import type { Curriculum, CVTemplate, TemplateMatch, CVSuggestion } from '@/types';

// ── Mock seed data ──────────────────────────────────────────────────────────

const seedTemplates: CVTemplate[] = [
  {
    id: 'tpl-1', name: 'CV Curriculum Format', organization: 'world_bank',
    organizationName: 'World Bank Group',
    description: 'Formato padrao para consultores do Banco Mundial. Enfase em experiencia tecnica, publicacoes e referencias.',
    requiredSections: [
      { id: 'experience', name: 'Professional Experience', required: true },
      { id: 'education', name: 'Education', required: true },
      { id: 'publications', name: 'Publications', required: true },
      { id: 'languages', name: 'Languages', required: true },
      { id: 'references', name: 'References', required: true },
    ],
    formatRules: [{ font: 'Times New Roman', size: 11 }],
    maxLengthPages: 5, isActive: true,
  },
  {
    id: 'tpl-2', name: 'P11 / PHP Form', organization: 'un',
    organizationName: 'United Nations',
    description: 'Formulario P11 para candidaturas a posicoes na ONU.',
    requiredSections: [
      { id: 'experience', name: 'Work Experience', required: true },
      { id: 'education', name: 'Education', required: true },
      { id: 'languages', name: 'Languages', required: true },
      { id: 'skills', name: 'Skills', required: true },
    ],
    formatRules: [{ font: 'Arial', size: 10 }],
    maxLengthPages: 8, isActive: true,
  },
  {
    id: 'tpl-3', name: 'Europass CV', organization: 'eu',
    organizationName: 'European Union',
    description: 'Formato Europass padrao para candidaturas a projetos financiados pela UE.',
    requiredSections: [
      { id: 'experience', name: 'Work Experience', required: true },
      { id: 'education', name: 'Education and Training', required: true },
      { id: 'languages', name: 'Language Skills', required: true },
      { id: 'digital', name: 'Digital Skills', required: false },
    ],
    formatRules: [{ font: 'Calibri', size: 11 }],
    maxLengthPages: 6, isActive: true,
  },
  {
    id: 'tpl-4', name: 'Consultant CV Format', organization: 'afdb',
    organizationName: 'African Development Bank',
    description: 'Formato especifico para consultores do BAD. Foco em experiencia em Africa.',
    requiredSections: [
      { id: 'experience', name: 'Consulting Experience', required: true },
      { id: 'education', name: 'Academic Qualifications', required: true },
      { id: 'languages', name: 'Languages', required: true },
      { id: 'africa', name: 'Africa Experience', required: true },
    ],
    formatRules: [{ font: 'Arial', size: 11 }],
    maxLengthPages: 5, isActive: true,
  },
];

const seedMatches: TemplateMatch[] = [
  {
    id: 'tm-1', curriculumId: 'cv-1', template: seedTemplates[0], matchScore: 92,
    missingSections: ['references'],
    recommendations: ['Adicionar 3 referencias profissionais', 'Incluir lista completa de publicacoes'],
    createdAt: new Date('2025-03-15'),
  },
  {
    id: 'tm-2', curriculumId: 'cv-1', template: seedTemplates[1], matchScore: 85,
    missingSections: [],
    recommendations: ['Verificar formato P11 especifico', 'Confirmar linguas ONU'],
    createdAt: new Date('2025-03-15'),
  },
  {
    id: 'tm-3', curriculumId: 'cv-1', template: seedTemplates[2], matchScore: 78,
    missingSections: ['digital'],
    recommendations: ['Adicionar secao de competencias digitais', 'Adaptar formato para Europass'],
    createdAt: new Date('2025-03-15'),
  },
];

const seedSuggestions: CVSuggestion[] = [
  {
    id: 'sug-1', type: 'missing_section', priority: 'high',
    message: 'Secao "Referencias" em falta para template World Bank',
    context: 'world_bank', autoFixable: false, fixed: false, createdAt: new Date('2025-03-15'),
  },
  {
    id: 'sug-2', type: 'content', priority: 'medium',
    message: 'Adicionar mais detalhes sobre experiencia em Africa (BAD requer minimo 5 anos)',
    context: 'afdb', autoFixable: false, fixed: false, createdAt: new Date('2025-03-15'),
  },
  {
    id: 'sug-3', type: 'format', priority: 'low',
    message: 'Publicacoes devem usar formato APA para UNICEF',
    context: 'un', autoFixable: true, fixed: false, createdAt: new Date('2025-03-15'),
  },
];

const seedCV: Curriculum = {
  id: 'cv-1',
  fileName: 'CV_Ana_Silva_2025.pdf',
  fileType: 'pdf',
  status: 'analyzed',
  analysisScore: 87,
  extractedData: {
    name: 'Ana Silva',
    email: 'ana.silva@email.com',
    phone: '+351 912345678',
    location: 'Lisboa, Portugal',
    summary: 'Consultora senior com 12 anos de experiencia em desenvolvimento internacional, focada em saude publica e governanca.',
    experience: [
      { title: 'Consultora Senior', organization: 'Banco Mundial', dateRange: '2019-2025', description: 'Lideranca tecnica em 8 projetos de saude publica em Africa subsaariana.' },
      { title: 'Especialista em Governanca', organization: 'UNDP', dateRange: '2014-2019', description: 'Apoio tecnico a ministerios da saude em 5 paises lusofonos.' },
      { title: 'Analista de Projetos', organization: 'GIZ', dateRange: '2012-2014', description: 'Coordenacao de projeto em Mocambique.' },
    ],
    education: [
      { title: 'PhD em Saude Publica', organization: 'Universidade de Lisboa', dateRange: '2008-2012' },
      { title: 'MSc em Desenvolvimento Internacional', organization: 'London School of Economics', dateRange: '2006-2008' },
    ],
    skills: ['Gestao de Projetos', 'Saude Publica', 'Governanca', 'Avaliacao', 'Formulacao de Propostas', 'Monitoramento e Avaliacao', 'Capacitacao', 'Pesquisa'],
    languages: ['Portugues (nativo)', 'Ingles (fluente)', 'Frances (intermedio)', 'Espanhol (basico)'],
    certifications: ['PMP Project Management', 'Monitoring & Evaluation Specialist (IPDET)', 'Gender Analysis (UN Women)'],
    publications: ['Silva, A. et al. (2023) "Strengthening Health Systems in Lusophone Africa"', 'Silva, A. (2021) "Proposal Writing for International Development"'],
  },
  templateMatches: seedMatches,
  suggestions: seedSuggestions,
  createdAt: new Date('2025-03-15'),
  updatedAt: new Date('2025-04-29'),
};

// ── Store ───────────────────────────────────────────────────────────────────

interface CurriculumState {
  curricula: Curriculum[];
  selectedCV: Curriculum | null;
  templates: CVTemplate[];
  matches: TemplateMatch[];
  suggestions: CVSuggestion[];
  isLoading: boolean;
  isAnalyzing: boolean;
  uploadProgress: number;
  error: string | null;

  fetchCurricula: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
  fetchMatches: (curriculumId: string) => Promise<void>;
  fetchSuggestions: (curriculumId: string) => Promise<void>;
  selectCV: (cv: Curriculum | null) => void;
  analyzeCV: (curriculumId: string) => Promise<void>;
  applySuggestion: (suggestionId: string) => void;
  addCurriculum: (cv: Curriculum) => void;
}

export const useCurriculumStore = create<CurriculumState>((set, get) => ({
  curricula: [seedCV],
  selectedCV: seedCV,
  templates: seedTemplates,
  matches: seedMatches,
  suggestions: seedSuggestions,
  isLoading: false,
  isAnalyzing: false,
  uploadProgress: 0,
  error: null,

  fetchCurricula: async () => {
    set({ isLoading: true, error: null });
    try {
      // Keep existing state; replace with real API when backend is available.
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchTemplates: async () => {
    set({ isLoading: true, error: null });
    try {
      set({ isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchMatches: async (curriculumId) => {
    set({ isLoading: true, error: null });
    try {
      const cv = get().curricula.find((c) => c.id === curriculumId);
      set({ matches: cv?.templateMatches ?? [], isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchSuggestions: async (curriculumId) => {
    set({ isLoading: true, error: null });
    try {
      const cv = get().curricula.find((c) => c.id === curriculumId);
      set({ suggestions: cv?.suggestions ?? [], isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  selectCV: (cv) => set({ selectedCV: cv }),

  analyzeCV: async (curriculumId) => {
    set({ isAnalyzing: true, uploadProgress: 0 });
    for (let p = 10; p <= 90; p += 20) {
      await new Promise((r) => setTimeout(r, 300));
      set({ uploadProgress: p });
    }
    set((state) => ({
      isAnalyzing: false,
      uploadProgress: 100,
      curricula: state.curricula.map((c) =>
        c.id === curriculumId ? { ...c, status: 'analyzed' as const } : c
      ),
    }));
  },

  applySuggestion: (suggestionId) => {
    set((state) => ({
      suggestions: state.suggestions.map((s) =>
        s.id === suggestionId ? { ...s, fixed: true } : s
      ),
    }));
  },

  addCurriculum: (cv) => {
    set((state) => ({ curricula: [...state.curricula, cv] }));
  },
}));
