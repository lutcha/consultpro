// ============================================
// CURRICULUM PAGE — Complete with Mock Data
// ============================================

import { useState } from 'react';
import {
  FileText, Lightbulb, Download, Eye, Star, CheckCircle, AlertTriangle,
  ArrowRight, ChevronDown, ChevronUp, Award, BookOpen, Briefcase,
  GraduationCap, Languages, Wrench, User,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import type { Curriculum, CVTemplate, TemplateMatch, CVSuggestion, CVOpportunityMatch } from '@/types';

function getInitials(name: string) {
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

// ============================================================
// MOCK DATA (typed as any to avoid strict type mismatches)
// ============================================================
const mockCV: Curriculum = {
  id: 'cv-1',
  fileName: 'CV_Ana_Silva_2025.pdf',
  fileType: 'pdf' as any,
  status: 'analyzed' as any,
  analysisScore: 87,
  extractedData: {
    name: 'Ana Silva',
    email: 'ana.silva@email.com',
    phone: '+351 912345678',
    location: 'Lisboa, Portugal',
    summary: 'Consultora senior com 12 anos de experiencia em desenvolvimento internacional, focada em saude publica e governanca. Especialista em avaliacao de projetos e formulacao de propostas para organismos multilaterais.',
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
  } as any,
  templateMatches: [],
  suggestions: [],
  createdAt: new Date('2025-03-15'),
  updatedAt: new Date('2025-04-29'),
} as any;

const mockTemplates: CVTemplate[] = [
  {
    id: 'tpl-1', name: 'CV Curriculum Format', organization: 'world_bank' as any, organizationName: 'World Bank Group',
    description: 'Formato padrao para consultores do Banco Mundial. Enfase em experiencia tecnica, publicacoes e referencias.',
    requiredSections: [{ id: 'experience', name: 'Professional Experience', required: true }, { id: 'education', name: 'Education', required: true }, { id: 'publications', name: 'Publications', required: true }, { id: 'languages', name: 'Languages', required: true }, { id: 'references', name: 'References', required: true }],
    formatRules: [{ font: 'Times New Roman', size: 11, primary_color: '#1F4E79', accent_color: '#4472C4' }],
    isActive: true,
  } as any,
  {
    id: 'tpl-2', name: 'P11 / PHP Form', organization: 'un' as any, organizationName: 'United Nations',
    description: 'Formulario P11 para candidaturas a posicoes na ONU.',
    requiredSections: [{ id: 'experience', name: 'Work Experience', required: true }, { id: 'education', name: 'Education', required: true }, { id: 'languages', name: 'Languages', required: true }, { id: 'skills', name: 'Skills', required: true }],
    formatRules: [{ font: 'Arial', size: 10 }],
    isActive: true,
  } as any,
  {
    id: 'tpl-3', name: 'Europass CV', organization: 'eu' as any, organizationName: 'European Union',
    description: 'Formato Europass padrao para candidaturas a projetos financiados pela UE.',
    requiredSections: [{ id: 'experience', name: 'Work Experience', required: true }, { id: 'education', name: 'Education and Training', required: true }, { id: 'languages', name: 'Language Skills', required: true }, { id: 'digital', name: 'Digital Skills', required: false }],
    formatRules: [{ font: 'Calibri', size: 11 }],
    isActive: true,
  } as any,
  {
    id: 'tpl-4', name: 'Consultant CV Format', organization: 'afdb' as any, organizationName: 'African Development Bank',
    description: 'Formato especifico para consultores do BAD. Foco em experiencia em Africa.',
    requiredSections: [{ id: 'experience', name: 'Consulting Experience', required: true }, { id: 'education', name: 'Academic Qualifications', required: true }, { id: 'languages', name: 'Languages', required: true }, { id: 'africa', name: 'Africa Experience', required: true }],
    formatRules: [{ font: 'Arial', size: 11 }],
    isActive: true,
  } as any,
];

const mockTemplateMatches: TemplateMatch[] = [
  {
    id: 'tm-1', curriculumId: 'cv-1', template: mockTemplates[0], matchScore: 92,
    missingSections: ['references'], recommendations: ['Adicionar 3 referencias profissionais', 'Incluir lista completa de publicacoes'],
    createdAt: new Date('2025-03-15'),
  } as any,
  {
    id: 'tm-2', curriculumId: 'cv-1', template: mockTemplates[1], matchScore: 85,
    missingSections: [], recommendations: ['Verificar formato P11 especifico', 'Confirmar linguas ONU'],
    createdAt: new Date('2025-03-15'),
  } as any,
];

const mockSuggestions: CVSuggestion[] = [
  { id: 'sug-1', type: 'missing_section' as any, priority: 'high', message: 'Secao "Referencias" em falta para template World Bank', context: 'world_bank', autoFixable: false, fixed: false, createdAt: new Date('2025-03-15') },
  { id: 'sug-2', type: 'content' as any, priority: 'medium', message: 'Adicionar mais detalhes sobre experiencia em Africa (BAD requer minimo 5 anos)', context: 'afdb', autoFixable: false, fixed: false, createdAt: new Date('2025-03-15') },
  { id: 'sug-3', type: 'format' as any, priority: 'low', message: 'Publicacoes devem usar formato APA para UNICEF', context: 'un', autoFixable: true, fixed: false, createdAt: new Date('2025-03-15') },
];

const mockOpportunityMatches: CVOpportunityMatch[] = [
  {
    id: 'om-1', curriculumId: 'cv-1', opportunityId: 'opp-1', opportunityTitle: 'Consultoria em Saude Publica — Mocambique', opportunityClient: 'UNDP Mocambique',
    overallScore: 78, skillsMatchScore: 85, experienceMatchScore: 80, educationMatchScore: 90, languageMatchScore: 75,
    matchedSkills: ['Saude Publica', 'Gestao de Projetos', 'Avaliacao'], missingSkills: ['Epidemiologia', 'Sistemas de Informacao'],
    relevantExperiences: ['Banco Mundial - Saude Publica', 'UNDP - Governanca'] as any,
    recommendations: ['Destacar experiencia em Mocambique', 'Mencionar certificacao PMP'],
  } as any,
];

// ============================================================
// COMPONENTS
// ============================================================
function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? 'text-emerald-600' : score >= 60 ? 'text-amber-600' : 'text-red-600';
  return (
    <div className="relative w-20 h-20 flex items-center justify-center">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
        <path className="text-muted" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
        <path className={color} strokeDasharray={`${score}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="3" />
      </svg>
      <span className={`absolute text-lg font-bold ${color}`}>{score}</span>
    </div>
  );
}

function SuggestionCard({ suggestion }: { suggestion: CVSuggestion }) {
  const priorityColors: Record<string, string> = {
    high: 'border-l-4 border-l-red-500 bg-red-50/50',
    medium: 'border-l-4 border-l-amber-500 bg-amber-50/50',
    low: 'border-l-4 border-l-blue-500 bg-blue-50/50',
  };
  const priorityLabels: Record<string, string> = { high: 'Alta', medium: 'Media', low: 'Baixa' };

  return (
    <Card className={`${priorityColors[suggestion.priority]} hover:shadow-md transition-shadow`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {suggestion.priority === 'high' ? <AlertTriangle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" /> :
           suggestion.priority === 'medium' ? <Lightbulb className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" /> :
           <CheckCircle className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={suggestion.priority === 'high' ? 'destructive' : suggestion.priority === 'medium' ? 'default' : 'secondary'} className="text-xs">
                {priorityLabels[suggestion.priority]}
              </Badge>
              <span className="text-xs text-muted-foreground capitalize">{suggestion.type.replace('_', ' ')}</span>
            </div>
            <p className="text-sm">{suggestion.message}</p>
            {suggestion.autoFixable && (
              <Button size="sm" variant="outline" className="mt-2 h-7 text-xs">Aplicar Correcao Automatica</Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TemplateMatchCard({ match }: { match: TemplateMatch }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h4 className="font-semibold">{match.template.name}</h4>
              <Badge variant="outline" className="text-xs">{match.template.organizationName}</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{match.template.description}</p>
          </div>
          <ScoreRing score={match.matchScore} />
        </div>

        {match.missingSections.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium text-muted-foreground mb-1">Secoes em Falta:</p>
            <div className="flex flex-wrap gap-1">
              {match.missingSections.map((s) => <Badge key={s} variant="destructive" className="text-xs">{s}</Badge>)}
            </div>
          </div>
        )}

        <div className="mt-3 flex gap-2">
          <Button size="sm" variant="outline" className="h-8 text-xs flex-1"><Eye className="h-3.5 w-3.5 mr-1" />Ver Detalhes</Button>
          <Button size="sm" className="h-8 text-xs flex-1"><ArrowRight className="h-3.5 w-3.5 mr-1" />Adaptar CV</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function OpportunityMatchCard({ match }: { match: CVOpportunityMatch }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold">{match.opportunityTitle}</h4>
            <p className="text-sm text-muted-foreground">{match.opportunityClient}</p>
          </div>
          <div className="text-center">
            <ScoreRing score={match.overallScore} />
            <p className="text-xs text-muted-foreground mt-1">Compatibilidade</p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-2 mt-3">
          <div className="text-center p-2 bg-muted/50 rounded-lg">
            <p className="text-sm font-semibold text-blue-600">{match.skillsMatchScore}%</p>
            <p className="text-xs text-muted-foreground">Skills</p>
          </div>
          <div className="text-center p-2 bg-muted/50 rounded-lg">
            <p className="text-sm font-semibold text-emerald-600">{match.experienceMatchScore}%</p>
            <p className="text-xs text-muted-foreground">Experiencia</p>
          </div>
          <div className="text-center p-2 bg-muted/50 rounded-lg">
            <p className="text-sm font-semibold text-violet-600">{match.educationMatchScore}%</p>
            <p className="text-xs text-muted-foreground">Educacao</p>
          </div>
          <div className="text-center p-2 bg-muted/50 rounded-lg">
            <p className="text-sm font-semibold text-amber-600">{match.languageMatchScore}%</p>
            <p className="text-xs text-muted-foreground">Linguas</p>
          </div>
        </div>

        {expanded && (
          <div className="mt-3 pt-3 border-t space-y-2 text-sm">
            <div><p className="text-xs font-medium text-muted-foreground">Skills Correspondentes</p><div className="flex flex-wrap gap-1 mt-1">{match.matchedSkills.map((s) => <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>)}</div></div>
            <div><p className="text-xs font-medium text-muted-foreground">Skills em Falta</p><div className="flex flex-wrap gap-1 mt-1">{match.missingSkills.map((s) => <Badge key={s} variant="destructive" className="text-xs">{s}</Badge>)}</div></div>
            <div><p className="text-xs font-medium text-muted-foreground">Recomendacoes</p><ul className="list-disc list-inside text-xs text-muted-foreground mt-1">{match.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
          </div>
        )}

        <Button variant="ghost" size="sm" className="w-full mt-2 h-8 text-xs" onClick={() => setExpanded(!expanded)}>
          {expanded ? <><ChevronUp className="h-3 w-3 mr-1" /> Menos detalhes</> : <><ChevronDown className="h-3 w-3 mr-1" /> Mais detalhes</>}
        </Button>
      </CardContent>
    </Card>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================
export function CurriculumPage() {
  const [activeTab, setActiveTab] = useState('cv');
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const extracted = mockCV.extractedData || {};
  const score = mockCV.analysisScore || 0;

  const sectionCards = [
    { id: 'experience', label: 'Experiencia Profissional', icon: Briefcase, data: extracted.experience },
    { id: 'education', label: 'Educacao', icon: GraduationCap, data: extracted.education },
    { id: 'skills', label: 'Skills', icon: Wrench, data: extracted.skills },
    { id: 'languages', label: 'Linguas', icon: Languages, data: extracted.languages },
    { id: 'certifications', label: 'Certificacoes', icon: Award, data: extracted.certifications },
    { id: 'publications', label: 'Publicacoes', icon: BookOpen, data: extracted.publications },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analise Curricular</h1>
        <p className="text-muted-foreground text-sm">Gestao de CVs, analise com IA, matching com templates e oportunidades.</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 md:grid-cols-4">
          <TabsTrigger value="cv" className="flex items-center gap-1.5"><FileText className="h-4 w-4" />Meu CV</TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-1.5"><Download className="h-4 w-4" />Templates</TabsTrigger>
          <TabsTrigger value="matching" className="flex items-center gap-1.5"><ArrowRight className="h-4 w-4" />Matching</TabsTrigger>
          <TabsTrigger value="suggestions" className="flex items-center gap-1.5"><Lightbulb className="h-4 w-4" />Sugestoes</TabsTrigger>
        </TabsList>

        {/* TAB: CV */}
        <TabsContent value="cv" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><Star className="h-4 w-4 text-amber-500" />Score de Qualidade</CardTitle></CardHeader>
              <CardContent className="pt-0 flex flex-col items-center">
                <ScoreRing score={score} />
                <p className="text-sm text-muted-foreground mt-2 text-center">
                  {score >= 80 ? 'Excelente CV! Poucas melhorias necessarias.' : score >= 60 ? 'Bom CV. Algumas melhorias recomendadas.' : 'CV necessita de melhorias significativas.'}
                </p>
                <div className="w-full mt-3 space-y-2">
                  <div className="flex justify-between text-sm"><span>Completude</span><span className="font-medium">85%</span></div>
                  <Progress value={85} className="h-1.5" />
                  <div className="flex justify-between text-sm"><span>Formato</span><span className="font-medium">90%</span></div>
                  <Progress value={90} className="h-1.5" />
                  <div className="flex justify-between text-sm"><span>Conteudo</span><span className="font-medium">88%</span></div>
                  <Progress value={88} className="h-1.5" />
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4" />Dados Pessoais</CardTitle></CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center gap-4">
                  <Avatar className="h-14 w-14"><AvatarFallback className="bg-primary/10 text-primary text-lg font-bold">{getInitials((extracted as any).name || '')}</AvatarFallback></Avatar>
                  <div>
                    <p className="text-lg font-semibold">{(extracted as any).name}</p>
                    <p className="text-sm text-muted-foreground">{(extracted as any).location}</p>
                    <p className="text-sm text-muted-foreground">{(extracted as any).email}</p>
                  </div>
                </div>
                <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm">{(extracted as any).summary}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sectionCards.map((section) => {
              const isExpanded = expandedSection === section.id;
              const data = (section.data || []) as any[];
              return (
                <Card key={section.id} className="hover:shadow-md transition-shadow">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <section.icon className="h-4 w-4 text-muted-foreground" />
                      {section.label}
                      <Badge variant="secondary" className="text-xs ml-auto">{data.length}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    {!isExpanded ? (
                      <div className="space-y-1">
                        {data.slice(0, 2).map((item, i) => (
                          <p key={i} className="text-sm text-muted-foreground truncate">
                            {typeof item === 'string' ? item : item.title || JSON.stringify(item)}
                          </p>
                        ))}
                        {data.length > 2 && <p className="text-xs text-muted-foreground">+{data.length - 2} mais...</p>}
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {data.map((item, i) => (
                          <div key={i} className="text-sm">
                            {typeof item === 'string' ? (
                              <p>{item}</p>
                            ) : (
                              <div className="p-2 bg-muted/30 rounded">
                                <p className="font-medium">{item.title}</p>
                                {item.organization && <p className="text-muted-foreground text-xs">{item.organization} {item.dateRange && `(${item.dateRange})`}</p>}
                                {item.description && <p className="text-muted-foreground text-xs mt-1">{item.description}</p>}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                    <Button variant="ghost" size="sm" className="w-full mt-2 h-7 text-xs" onClick={() => setExpandedSection(isExpanded ? null : section.id)}>
                      {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" /> Recolher</> : <><ChevronDown className="h-3 w-3 mr-1" /> Expandir</>}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* TAB: TEMPLATES */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockTemplates.map((tpl) => (
              <Card key={tpl.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">{tpl.name}</h4>
                      <p className="text-xs text-muted-foreground">{tpl.organizationName}</p>
                    </div>
                    <Badge variant="outline" className="text-xs">{(tpl as any).maxLengthPages || 5} paginas max</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{tpl.description}</p>
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Secoes obrigatorias:</p>
                    <div className="flex flex-wrap gap-1">
                      {tpl.requiredSections?.map((s: any) => (
                        <Badge key={s.id} variant="secondary" className="text-xs font-normal">{s.name}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="h-8 text-xs flex-1"><Download className="h-3.5 w-3.5 mr-1" />Descarregar Template</Button>
                    <Button size="sm" className="h-8 text-xs flex-1"><ArrowRight className="h-3.5 w-3.5 mr-1" />Adaptar CV</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* TAB: MATCHING */}
        <TabsContent value="matching" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Download className="h-4 w-4" />Matching com Templates</h3>
              <div className="space-y-3">
                {mockTemplateMatches.map((m) => (
                  <TemplateMatchCard key={m.id} match={m} />
                ))}
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Briefcase className="h-4 w-4" />Matching com Oportunidades</h3>
              <div className="space-y-3">
                {mockOpportunityMatches.map((m) => (
                  <OpportunityMatchCard key={m.id} match={m} />
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        {/* TAB: SUGGESTIONS */}
        <TabsContent value="suggestions" className="space-y-4">
          <div className="space-y-3">
            {mockSuggestions.map((s) => (
              <SuggestionCard key={s.id} suggestion={s} />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
