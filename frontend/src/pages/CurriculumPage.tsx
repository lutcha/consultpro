// ============================================
// CURRICULUM PAGE — real API, file upload
// ============================================

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  FileText, Lightbulb, Download, Eye, Star, CheckCircle, AlertTriangle,
  ArrowRight, ChevronDown, ChevronUp, Award, BookOpen, Briefcase,
  GraduationCap, Languages, Wrench, User, Upload, X, Loader2, RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useCurriculumStore } from '@/stores';
import type { Curriculum, CVSuggestion, TemplateMatch } from '@/types';

function getInitials(name: string) {
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

// ── Upload zone ──────────────────────────────────────────────────────────────

function UploadZone({ onUpload, isLoading, uploadProgress }: {
  onUpload: (file: File) => void;
  isLoading: boolean;
  uploadProgress: number;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'doc', 'docx'].includes(ext || '')) return;
    onUpload(file);
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  }, []);

  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);

  return (
    <Card>
      <CardContent className="p-6">
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            dragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/30'
          }`}
          onClick={() => !isLoading && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.doc,.docx"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          {isLoading ? (
            <div className="space-y-3">
              <Loader2 className="h-10 w-10 mx-auto text-primary animate-spin" />
              <p className="text-sm font-medium">A carregar CV...</p>
              <Progress value={uploadProgress} className="max-w-xs mx-auto h-2" />
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
              <p className="font-medium">Arrastar CV aqui ou clicar para selecionar</p>
              <p className="text-sm text-muted-foreground">PDF, DOC ou DOCX — max 10 MB</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Score ring ────────────────────────────────────────────────────────────────

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

// ── Suggestion card ───────────────────────────────────────────────────────────

function SuggestionCard({ suggestion, onApply }: { suggestion: CVSuggestion; onApply: (id: string) => void }) {
  const priorityColors: Record<string, string> = {
    high: 'border-l-4 border-l-red-500 bg-red-50/50 dark:bg-red-950/20',
    medium: 'border-l-4 border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20',
    low: 'border-l-4 border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20',
  };
  const priorityLabels: Record<string, string> = { high: 'Alta', medium: 'Media', low: 'Baixa' };

  if (suggestion.fixed) {
    return (
      <Card className="opacity-60">
        <CardContent className="p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" />
          <p className="text-sm line-through text-muted-foreground">{suggestion.message}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`${priorityColors[suggestion.priority] || ''} hover:shadow-md transition-shadow`}>
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
              <Button size="sm" variant="outline" className="mt-2 h-7 text-xs" onClick={() => onApply(suggestion.id)}>
                Aplicar Correcao Automatica
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Template match card ───────────────────────────────────────────────────────

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

// ── CV selector (if multiple) ─────────────────────────────────────────────────

function CVSelector({ curricula, selected, onSelect }: {
  curricula: Curriculum[];
  selected: Curriculum | null;
  onSelect: (cv: Curriculum) => void;
}) {
  if (curricula.length <= 1) return null;
  return (
    <div className="flex gap-2 flex-wrap">
      {curricula.map((cv) => (
        <button
          key={cv.id}
          onClick={() => onSelect(cv)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm transition-colors ${
            selected?.id === cv.id
              ? 'bg-primary text-primary-foreground border-primary'
              : 'bg-background hover:bg-muted border-border'
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          {cv.fileName}
          <Badge variant={cv.status === 'analyzed' ? 'default' : 'secondary'} className="text-xs ml-1">
            {cv.status}
          </Badge>
        </button>
      ))}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function CurriculumPage() {
  const {
    curricula, selectedCV, templates, suggestions,
    isLoading, isAnalyzing, uploadProgress, error,
    fetchCurricula, fetchTemplates, fetchSuggestions,
    selectCV, uploadCV, analyzeCV, applySuggestion, clearError,
  } = useCurriculumStore();

  const [activeTab, setActiveTab] = useState('cv');
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  useEffect(() => {
    fetchCurricula();
    fetchTemplates();
  }, [fetchCurricula, fetchTemplates]);

  const handleSelectCV = (cv: Curriculum) => {
    selectCV(cv);
    fetchSuggestions(cv.id);
  };

  const handleUpload = async (file: File) => {
    try {
      await uploadCV(file);
    } catch {
      // error shown from store
    }
  };

  const handleAnalyze = () => {
    if (selectedCV) analyzeCV(selectedCV.id);
  };

  const extracted = (selectedCV?.extractedData || {}) as any;
  const score = selectedCV?.analysisScore || 0;

  const sectionCards = [
    { id: 'experience', label: 'Experiencia Profissional', icon: Briefcase, data: extracted.experience },
    { id: 'education', label: 'Educacao', icon: GraduationCap, data: extracted.education },
    { id: 'skills', label: 'Skills', icon: Wrench, data: extracted.skills },
    { id: 'languages', label: 'Linguas', icon: Languages, data: extracted.languages },
    { id: 'certifications', label: 'Certificacoes', icon: Award, data: extracted.certifications },
    { id: 'publications', label: 'Publicacoes', icon: BookOpen, data: extracted.publications },
  ];

  // Pending suggestions (not fixed)
  const openSuggestions = suggestions.filter((s) => !s.fixed);
  const fixedSuggestions = suggestions.filter((s) => s.fixed);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analise Curricular</h1>
        <p className="text-muted-foreground text-sm">Gestao de CVs, analise com IA, matching com templates e oportunidades.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 flex items-center gap-3">
          <p className="text-sm text-destructive flex-1">{error}</p>
          <Button variant="ghost" size="sm" onClick={clearError}><X className="h-4 w-4" /></Button>
        </div>
      )}

      {/* Upload zone */}
      <UploadZone onUpload={handleUpload} isLoading={isLoading && uploadProgress > 0} uploadProgress={uploadProgress} />

      {/* CV selector when multiple */}
      {curricula.length > 1 && (
        <CVSelector curricula={curricula} selected={selectedCV} onSelect={handleSelectCV} />
      )}

      {/* No CV yet */}
      {!isLoading && curricula.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center space-y-2">
            <FileText className="h-12 w-12 mx-auto text-muted-foreground" />
            <p className="font-medium">Nenhum CV carregado</p>
            <p className="text-sm text-muted-foreground">Carregue um ficheiro PDF ou DOCX para comecar a analise.</p>
          </CardContent>
        </Card>
      )}

      {/* Main content when CV exists */}
      {selectedCV && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <TabsList className="grid grid-cols-2 md:grid-cols-4">
              <TabsTrigger value="cv" className="flex items-center gap-1.5"><FileText className="h-4 w-4" />Meu CV</TabsTrigger>
              <TabsTrigger value="templates" className="flex items-center gap-1.5"><Download className="h-4 w-4" />Templates</TabsTrigger>
              <TabsTrigger value="matching" className="flex items-center gap-1.5"><ArrowRight className="h-4 w-4" />Matching</TabsTrigger>
              <TabsTrigger value="suggestions" className="flex items-center gap-1.5">
                <Lightbulb className="h-4 w-4" />
                Sugestoes
                {openSuggestions.length > 0 && (
                  <Badge variant="destructive" className="ml-1 h-4 text-xs px-1">{openSuggestions.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{selectedCV.fileName}</span>
              {selectedCV.status !== 'analyzed' || isAnalyzing ? (
                <Button size="sm" onClick={handleAnalyze} disabled={isAnalyzing}>
                  {isAnalyzing ? <><Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />A analisar...</> : <><RefreshCw className="h-3.5 w-3.5 mr-1.5" />Analisar CV</>}
                </Button>
              ) : (
                <Button size="sm" variant="outline" onClick={handleAnalyze} disabled={isAnalyzing}>
                  <RefreshCw className="h-3.5 w-3.5 mr-1.5" />Re-analisar
                </Button>
              )}
            </div>
          </div>

          {/* TAB: CV */}
          <TabsContent value="cv" className="space-y-4">
            {isAnalyzing ? (
              <Card>
                <CardContent className="py-16 text-center space-y-3">
                  <Loader2 className="h-12 w-12 mx-auto text-primary animate-spin" />
                  <p className="font-medium">A analisar CV com IA...</p>
                  <p className="text-sm text-muted-foreground">Extração de texto e processamento estruturado. Aguarde.</p>
                </CardContent>
              </Card>
            ) : selectedCV.status === 'uploaded' ? (
              <Card>
                <CardContent className="py-12 text-center space-y-3">
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground" />
                  <p className="font-medium">CV carregado — aguarda analise</p>
                  <Button onClick={handleAnalyze}><RefreshCw className="h-4 w-4 mr-2" />Analisar Agora</Button>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2"><Star className="h-4 w-4 text-amber-500" />Score de Qualidade</CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0 flex flex-col items-center">
                      <ScoreRing score={score} />
                      <p className="text-sm text-muted-foreground mt-2 text-center">
                        {score >= 80 ? 'Excelente CV! Poucas melhorias necessarias.' : score >= 60 ? 'Bom CV. Algumas melhorias recomendadas.' : 'CV necessita de melhorias significativas.'}
                      </p>
                      <div className="w-full mt-3 space-y-2">
                        <div className="flex justify-between text-sm"><span>Completude</span><span className="font-medium">{Math.min(score + 5, 100)}%</span></div>
                        <Progress value={Math.min(score + 5, 100)} className="h-1.5" />
                        <div className="flex justify-between text-sm"><span>Conteudo</span><span className="font-medium">{score}%</span></div>
                        <Progress value={score} className="h-1.5" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="lg:col-span-2">
                    <CardHeader className="pb-3"><CardTitle className="text-base flex items-center gap-2"><User className="h-4 w-4" />Dados Pessoais</CardTitle></CardHeader>
                    <CardContent className="pt-0">
                      {extracted.name ? (
                        <>
                          <div className="flex items-center gap-4">
                            <Avatar className="h-14 w-14">
                              <AvatarFallback className="bg-primary/10 text-primary text-lg font-bold">{getInitials(extracted.name)}</AvatarFallback>
                            </Avatar>
                            <div>
                              <p className="text-lg font-semibold">{extracted.name}</p>
                              {extracted.location && <p className="text-sm text-muted-foreground">{extracted.location}</p>}
                              {extracted.email && <p className="text-sm text-muted-foreground">{extracted.email}</p>}
                            </div>
                          </div>
                          {extracted.summary && (
                            <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                              <p className="text-sm">{extracted.summary}</p>
                            </div>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-muted-foreground">Dados pessoais nao extraidos. Tente re-analisar.</p>
                      )}
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
                          {data.length === 0 ? (
                            <p className="text-xs text-muted-foreground italic">Nao encontrado no CV.</p>
                          ) : !isExpanded ? (
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
                                  {typeof item === 'string' ? <p>{item}</p> : (
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
                          {data.length > 0 && (
                            <Button variant="ghost" size="sm" className="w-full mt-2 h-7 text-xs" onClick={() => setExpandedSection(isExpanded ? null : section.id)}>
                              {isExpanded ? <><ChevronUp className="h-3 w-3 mr-1" />Recolher</> : <><ChevronDown className="h-3 w-3 mr-1" />Expandir</>}
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </>
            )}
          </TabsContent>

          {/* TAB: TEMPLATES */}
          <TabsContent value="templates" className="space-y-4">
            {templates.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">Sem templates configurados.</CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.map((tpl) => (
                  <Card key={tpl.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold">{tpl.name}</h4>
                          <p className="text-xs text-muted-foreground">{tpl.organizationName}</p>
                        </div>
                        {tpl.maxLengthPages && <Badge variant="outline" className="text-xs">{tpl.maxLengthPages} pag. max</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground">{tpl.description}</p>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Secoes obrigatorias:</p>
                        <div className="flex flex-wrap gap-1">
                          {(tpl.requiredSections || []).map((s: any) => (
                            <Badge key={s.id} variant="secondary" className="text-xs font-normal">{s.name}</Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="h-8 text-xs flex-1"><Download className="h-3.5 w-3.5 mr-1" />Descarregar</Button>
                        <Button size="sm" className="h-8 text-xs flex-1"><ArrowRight className="h-3.5 w-3.5 mr-1" />Adaptar CV</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>

          {/* TAB: MATCHING */}
          <TabsContent value="matching" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Download className="h-4 w-4" />Matching com Templates</h3>
                {selectedCV.templateMatches.length === 0 ? (
                  <Card><CardContent className="py-8 text-center text-sm text-muted-foreground">Sem resultados de matching. Use "Adaptar CV" num template para gerar scores.</CardContent></Card>
                ) : (
                  <div className="space-y-3">
                    {selectedCV.templateMatches.map((m) => <TemplateMatchCard key={m.id} match={m} />)}
                  </div>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Briefcase className="h-4 w-4" />Matching com Oportunidades</h3>
                <Card><CardContent className="py-8 text-center text-sm text-muted-foreground">Sem matches de oportunidades calculados ainda.</CardContent></Card>
              </div>
            </div>
          </TabsContent>

          {/* TAB: SUGGESTIONS */}
          <TabsContent value="suggestions" className="space-y-4">
            {suggestions.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center text-muted-foreground">
                  <CheckCircle className="h-10 w-10 mx-auto text-emerald-500 mb-2" />
                  <p>Nenhuma sugestao pendente.</p>
                </CardContent>
              </Card>
            ) : (
              <>
                {openSuggestions.length > 0 && (
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-muted-foreground">{openSuggestions.length} sugestao{openSuggestions.length !== 1 ? 'es' : ''} pendente{openSuggestions.length !== 1 ? 's' : ''}</p>
                    {openSuggestions.map((s) => (
                      <SuggestionCard key={s.id} suggestion={s} onApply={applySuggestion} />
                    ))}
                  </div>
                )}
                {fixedSuggestions.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <p className="text-sm font-medium text-muted-foreground">{fixedSuggestions.length} resolvida{fixedSuggestions.length !== 1 ? 's' : ''}</p>
                    {fixedSuggestions.map((s) => (
                      <SuggestionCard key={s.id} suggestion={s} onApply={applySuggestion} />
                    ))}
                  </div>
                )}
              </>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
