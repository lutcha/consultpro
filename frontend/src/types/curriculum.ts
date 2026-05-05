// Types for Curriculum module
export interface Curriculum {
  id: string;
  fileName: string;
  fileType: string;
  status: string;
  analysisScore?: number;
  extractedData?: ExtractedCVData;
  suggestions?: CVSuggestion[];
  templateMatches?: TemplateMatch[];
  opportunityMatches?: CVOpportunityMatch[];
  createdAt?: string;
  updatedAt?: string;
}

export interface ExtractedCVData {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  summary?: string;
  experience?: CVExperience[];
  education?: CVEducation[];
  skills?: string[];
  languages?: string[];
  certifications?: string[];
  publications?: string[];
}

export interface CVExperience {
  title: string;
  organization: string;
  dateRange: string;
  description?: string;
}

export interface CVEducation {
  title: string;
  organization: string;
  dateRange: string;
}

export interface CVTemplate {
  id: string;
  name: string;
  organization: string;
  organizationName: string;
  description: string;
  requiredSections?: TemplateSection[];
  formatRules?: any[];
  maxLengthPages: number;
  exampleUrl?: string;
  isActive: boolean;
  createdAt?: Date | string;
}

export interface TemplateSection {
  id: string;
  name: string;
  required: boolean;
}

export interface TemplateMatch {
  id: string;
  curriculumId: string;
  templateId: string;
  matchScore: number;
  missingSections: string[];
  recommendations: string[];
  adaptedContent?: any;
  generatedFileUrl?: string;
  createdAt?: Date | string;
}

export interface CVSuggestion {
  id: string;
  curriculumId: string;
  type: string;
  priority: string;
  message: string;
  context?: string;
  autoFixable: boolean;
  fixed: boolean;
  createdAt?: Date | string;
}

export interface CVOpportunityMatch {
  id: string;
  curriculumId: string;
  opportunityId: string;
  overallScore: number;
  skillsMatchScore: number;
  experienceMatchScore: number;
  educationMatchScore: number;
  languageMatchScore: number;
  matchedSkills: string[];
  missingSkills: string[];
  relevantExperiences: string[];
  recommendations: string[];
  createdAt?: Date | string;
}
