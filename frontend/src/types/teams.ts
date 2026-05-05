// ============================================
// TEAMS MODULE TYPES
// ============================================

export interface TeamStats {
  internalMembers: number;
  externalConsultants: number;
  activeProjects: number;
  averageRating: number;
}

export interface PipelinePhase {
  phase: string;
  members: number;
}

export interface InternalTeamMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: string;
  phase: string;
  department: string;
  skills: string[];
  availability: 'available' | 'busy' | 'unavailable';
  projectsCount: number;
  joinedAt: string;
}

export interface Consultant {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  seniority: 'senior' | 'mid' | 'junior';
  seniorityLabel: string;
  availability: 'available' | 'busy' | 'unavailable';
  location: string;
  education: string;
  yearsExperience: number;
  projectsCompleted: number;
  dailyRate: number;
  currency: string;
  rating: number;
  skills: string[];
  languages: string[];
  sectors: string[];
  lastProject: {
    name: string;
    date: string;
  };
}

export interface ProjectTeamMember {
  id: string;
  name: string;
  avatar?: string;
  role: string;
  type: 'internal' | 'external';
}

export interface ProjectTeam {
  id: string;
  name: string;
  client: string;
  phase: string;
  status: 'in_proposal' | 'won' | 'lost';
  internalMembers: ProjectTeamMember[];
  externalMembers: ProjectTeamMember[];
  manager?: string;
  startDate?: string;
}
