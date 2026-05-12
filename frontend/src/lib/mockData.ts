// ============================================
// MOCK DATA - ConsultPro Platform
// ============================================

import type { 
  User, 
  Opportunity, 
  Proposal, 
  DashboardStats, 
  PipelineItem, 
  Alert, 
  Activity,
  QCState 
} from '@/types';

// Mock Users
export const mockUsers: User[] = [
  {
    id: '1',
    name: 'Ana Silva',
    email: 'ana.silva@consultpro.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ana',
    role: 'consultant',
    skills: ['Educação', 'Género', 'Monitoria', 'Avaliação'],
    availability: 'available',
    languages: ['PT', 'EN', 'FR'],
  },
  {
    id: '2',
    name: 'Carlos Mendes',
    email: 'carlos.mendes@consultpro.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Carlos',
    role: 'manager',
    skills: ['Gestão de Projetos', 'Orçamentos', 'Negociação'],
    availability: 'busy',
    languages: ['PT', 'EN', 'ES'],
  },
  {
    id: '3',
    name: 'Maria Santos',
    email: 'maria.santos@consultpro.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Maria',
    role: 'consultant',
    skills: ['Saúde Pública', 'Sistemas de Saúde', 'Formação'],
    availability: 'available',
    languages: ['PT', 'EN'],
  },
];

// Mock Current User
export const currentUser = mockUsers[0];

// Mock Opportunities
export const mockOpportunities: Opportunity[] = [
  {
    id: 'opp-1',
    title: 'Formação de Professores Rurais - Moçambique',
    client: 'UNICEF',
    sector: 'Educação',
    country: 'Moçambique',
    value: 450000,
    currency: 'USD',
    deadline: new Date('2024-05-15'),
    status: 'analyzing',
    description: 'Consultoria para desenvolvimento de programa de formação de professores em áreas rurais, com ênfase em género e inclusão.',
    requirements: [
      {
        id: 'req-1',
        category: 'functional',
        description: 'Experiência mínima de 10 anos em projetos de educação',
        priority: 'mandatory',
        isCovered: true,
      },
      {
        id: 'req-2',
        category: 'technical',
        description: 'Especialista em género e inclusão social',
        priority: 'mandatory',
        isCovered: false,
      },
      {
        id: 'req-3',
        category: 'institutional',
        description: 'Registro ativo como consultora',
        priority: 'mandatory',
        isCovered: true,
      },
    ],
    risks: [
      {
        id: 'risk-1',
        description: 'Prazo curto para mobilização de equipa',
        severity: 'high',
        mitigation: 'Identificar consultores com disponibilidade imediata',
      },
    ],
    eligibleCountries: ['mz'],
    consortiumType: 'solo',
    partnerProfiles: [],
    createdAt: new Date('2024-04-01'),
    updatedAt: new Date('2024-04-10'),
  },
  {
    id: 'opp-2',
    title: 'Fortalecimento dos Sistemas de Saúde - Angola',
    client: 'Banco Mundial',
    sector: 'Saúde',
    country: 'Angola',
    value: 890000,
    currency: 'USD',
    deadline: new Date('2024-06-20'),
    status: 'go',
    description: 'Apoio técnico ao Ministério da Saúde de Angola para fortalecimento dos sistemas de saúde ao nível provincial.',
    requirements: [
      {
        id: 'req-4',
        category: 'functional',
        description: 'Experiência em sistemas de saúde em África',
        priority: 'mandatory',
        isCovered: true,
      },
      {
        id: 'req-5',
        category: 'technical',
        description: 'Conhecimento de PHC e UHC',
        priority: 'preferred',
        isCovered: true,
      },
    ],
    risks: [
      {
        id: 'risk-2',
        description: 'Concorrência forte de empresas internacionais',
        severity: 'medium',
      },
    ],
    eligibleCountries: ['ao'],
    consortiumType: 'solo',
    partnerProfiles: [],
    createdAt: new Date('2024-03-15'),
    updatedAt: new Date('2024-04-08'),
  },
  {
    id: 'opp-3',
    title: 'Avaliação de Impacto - Programa de Agricultura',
    client: 'FAO',
    sector: 'Agricultura',
    country: 'Cabo Verde',
    value: 180000,
    currency: 'USD',
    deadline: new Date('2024-04-25'),
    status: 'proposal_draft',
    description: 'Avaliação de impacto do programa de desenvolvimento agrícola sustentável em Cabo Verde.',
    requirements: [
      {
        id: 'req-6',
        category: 'functional',
        description: 'Metodologias de avaliação de impacto',
        priority: 'mandatory',
        isCovered: true,
      },
      {
        id: 'req-7',
        category: 'technical',
        description: 'Econometria aplicada',
        priority: 'preferred',
        isCovered: true,
      },
    ],
    risks: [],
    eligibleCountries: ['cv'],
    consortiumType: 'solo',
    partnerProfiles: [],
    createdAt: new Date('2024-03-20'),
    updatedAt: new Date('2024-04-05'),
  },
  {
    id: 'opp-4',
    title: 'Desenvolvimento de Infraestruturas Rurais - Senegal',
    client: 'AfDB',
    sector: 'Infraestruturas',
    country: 'Senegal',
    value: 1200000,
    currency: 'USD',
    deadline: new Date('2024-07-10'),
    status: 'new',
    description: 'Consultoria para planeamento e supervisão de infraestruturas rurais no vale do Senegal.',
    requirements: [
      {
        id: 'req-8',
        category: 'functional',
        description: 'Engenheiro civil com experiência em projetos rurais',
        priority: 'mandatory',
        isCovered: false,
      },
    ],
    risks: [
      {
        id: 'risk-3',
        description: 'Requisito de certificação PPM não disponível',
        severity: 'high',
      },
    ],
    eligibleCountries: ['sn'],
    consortiumType: 'open',
    partnerProfiles: [],
    createdAt: new Date('2024-04-08'),
    updatedAt: new Date('2024-04-08'),
  },
];

// Mock Proposals
export const mockProposals: Proposal[] = [
  {
    id: 'prop-1',
    opportunityId: 'opp-3',
    title: 'Proposta - Avaliação de Impacto FAO Cabo Verde',
    version: 2,
    status: 'draft',
    consortiumMembers: [],
    sections: [
      {
        id: 'sec-1',
        type: 'cover',
        title: 'Capa',
        content: '',
        order: 1,
        isComplete: true,
        comments: [],
      },
      {
        id: 'sec-2',
        type: 'executive_summary',
        title: 'Resumo Executivo',
        content: 'Esta proposta apresenta uma abordagem abrangente para a avaliação de impacto...',
        order: 2,
        isComplete: true,
        comments: [],
      },
      {
        id: 'sec-3',
        type: 'methodology',
        title: 'Metodologia',
        content: 'A metodologia proposta baseia-se em uma combinação de métodos quantitativos e qualitativos...',
        order: 3,
        isComplete: false,
        comments: [],
      },
      {
        id: 'sec-4',
        type: 'team',
        title: 'Equipa Técnica',
        content: '',
        order: 4,
        isComplete: false,
        comments: [],
      },
      {
        id: 'sec-5',
        type: 'workplan',
        title: 'Plano de Trabalho',
        content: '',
        order: 5,
        isComplete: false,
        comments: [],
      },
      {
        id: 'sec-6',
        type: 'budget',
        title: 'Orçamento',
        content: '',
        order: 6,
        isComplete: false,
        comments: [],
      },
    ],
    team: [
      { userId: '1', role: 'Team Leader', hours: 240, cvAttached: true },
      { userId: '3', role: 'Especialista em Saúde', hours: 120, cvAttached: false },
    ],
    budget: {
      total: 175000,
      currency: 'USD',
      breakdown: [
        { category: 'Pessoal', amount: 120000, description: 'Honorários da equipa' },
        { category: 'Viagens', amount: 25000, description: 'Deslocações e estadias' },
        { category: 'Outros', amount: 30000, description: 'Materiais e equipamentos' },
      ],
    },
    createdAt: new Date('2024-03-25'),
    updatedAt: new Date('2024-04-09'),
  },
];

// Mock Dashboard Stats
export const mockDashboardStats: DashboardStats = {
  activeOpportunities: 12,
  proposalsInProgress: 5,
  winRate: 68,
  upcomingDeadlines: 3,
  opportunitiesByStatus: {},
  projectsActive: 0,
  projectsCompleted: 0,
  projectsOnHold: 0,
  scrapingNew: 0,
  scrapingWithAI: 0,
  deadlineItems: [],
};

// Mock Pipeline
export const mockPipeline: PipelineItem[] = [
  {
    id: 'pipe-1',
    title: 'Educação Moçambique - Formação de Professores',
    client: 'UNICEF',
    deadline: new Date('2024-05-15'),
    status: 'draft',
    value: 450000,
    progress: 35,
  },
  {
    id: 'pipe-2',
    title: 'Saúde Angola - Fortalecimento de Sistemas',
    client: 'Banco Mundial',
    deadline: new Date('2024-06-20'),
    status: 'in_review',
    value: 890000,
    progress: 75,
  },
  {
    id: 'pipe-3',
    title: 'Agricultura Cabo Verde - Avaliação',
    client: 'FAO',
    deadline: new Date('2024-04-25'),
    status: 'qc_check',
    value: 180000,
    progress: 90,
  },
  {
    id: 'pipe-4',
    title: 'Infraestruturas Senegal - Vale do Senegal',
    client: 'AfDB',
    deadline: new Date('2024-07-10'),
    status: 'draft',
    value: 1200000,
    progress: 15,
  },
];

// Mock Alerts
export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    type: 'warning',
    message: 'ToR #234 exige certificação PPM — nenhum CV disponível',
    action: {
      label: 'Resolver',
      href: '/opportunities/opp-4',
    },
  },
  {
    id: 'alert-2',
    type: 'error',
    message: 'Prazo da proposta FAO termina em 3 dias',
    action: {
      label: 'Ver Proposta',
      href: '/proposals/prop-1',
    },
  },
  {
    id: 'alert-3',
    type: 'info',
    message: 'Nova oportunidade disponível: Avaliação UE-Timor Leste',
  },
];

// Mock Activities
export const mockActivities: Activity[] = [
  {
    id: 'act-1',
    type: 'proposal_updated',
    user: mockUsers[0],
    description: 'atualizou a secção de Metodologia na proposta FAO',
    timestamp: new Date('2024-04-09T14:30:00'),
  },
  {
    id: 'act-2',
    type: 'opportunity_added',
    user: mockUsers[1],
    description: 'adicionou nova oportunidade: Infraestruturas Senegal',
    timestamp: new Date('2024-04-09T10:15:00'),
  },
  {
    id: 'act-3',
    type: 'qc_completed',
    user: mockUsers[2],
    description: 'completou Quality Check da proposta Banco Mundial',
    timestamp: new Date('2024-04-08T16:45:00'),
  },
  {
    id: 'act-4',
    type: 'comment_added',
    user: mockUsers[0],
    description: 'adicionou comentário na proposta FAO',
    timestamp: new Date('2024-04-08T11:20:00'),
  },
];

// Mock QC State
export const mockQCState: QCState = {
  proposalId: 'prop-1',
  overallScore: 86,
  status: 'completed',
  checks: {
    compliance: {
      score: 100,
      status: 'pass',
      items: [
        { id: 'qc-1', description: 'Todos os requisitos obrigatórios cobertos', status: 'pass' },
        { id: 'qc-2', description: 'Formato de submissão correto', status: 'pass' },
      ],
    },
    coherence: {
      score: 72,
      status: 'warn',
      items: [
        { id: 'qc-3', description: 'Secção "Sustentabilidade" muito genérica', status: 'warn', section: 'methodology' },
        { id: 'qc-4', description: 'Objetivos alinhados com resultados esperados', status: 'pass' },
      ],
    },
    budget: {
      score: 95,
      status: 'pass',
      items: [
        { id: 'qc-5', description: 'Orçamento dentro dos limites', status: 'pass' },
        { id: 'qc-6', description: 'Justificação adequada dos custos', status: 'pass' },
      ],
    },
    attachments: {
      score: 85,
      status: 'warn',
      items: [
        { id: 'qc-7', description: 'CV do Especialista sem assinatura', status: 'warn' },
        { id: 'qc-8', description: 'Certificações anexadas', status: 'pass' },
      ],
    },
  },
  canSubmit: true,
  suggestions: [
    {
      id: 'sugg-1',
      text: 'Incluir indicador de impacto a 5 anos na secção de Sustentabilidade',
      action: 'add',
      targetSection: 'methodology',
      applied: false,
    },
  ],
};

// Helper function to get opportunity by ID
export function getOpportunityById(id: string): Opportunity | undefined {
  return mockOpportunities.find(opp => opp.id === id);
}

// Helper function to get proposal by ID
export function getProposalById(id: string): Proposal | undefined {
  return mockProposals.find(prop => prop.id === id);
}

// Helper function to get proposals by opportunity ID
export function getProposalsByOpportunityId(oppId: string): Proposal[] {
  return mockProposals.filter(prop => prop.opportunityId === oppId);
}
