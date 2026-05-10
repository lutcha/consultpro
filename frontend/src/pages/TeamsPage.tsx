// ============================================
// TEAMS PAGE — Complete Module (3 Tabs)
// ============================================

import { useEffect, useMemo, useState } from 'react';
import {
  Users, UserCheck, Briefcase, Search, Star, MapPin, GraduationCap,
  Calendar, DollarSign, Globe, Filter, X, TrendingUp,
  CheckCircle2, Clock, User, ChevronDown, ChevronUp, Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useTeamsStore } from '@/stores';
import { AddInternalMemberModal } from '@/components/modals/AddInternalMemberModal';
import { AddConsultantModal } from '@/components/modals/AddConsultantModal';
import { AddProjectTeamMemberModal } from '@/components/modals/AddProjectTeamMemberModal';
import { CreateProjectTeamModal } from '@/components/modals/CreateProjectTeamModal';
import type { ProjectTeam, InternalTeamMember, Consultant } from '@/types/teams';

function getInitials(name: string) {
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

function AvailabilityBadge({ status }: { status: string }) {
  const variants: Record<string, string> = {
    available: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    busy: 'bg-amber-100 text-amber-700 border-amber-200',
    unavailable: 'bg-slate-100 text-slate-700 border-slate-200',
  };
  const labels: Record<string, string> = {
    available: 'Disponivel', busy: 'Ocupado', unavailable: 'Indisponivel',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border ${variants[status] || variants.available}`}>
      {labels[status] || status}
    </span>
  );
}

// ============================================================
// TAB 1: STATS CARDS
// ============================================================
function StatsCards() {
  const { stats } = useTeamsStore();
  const cards = [
    { label: 'Membros Internos', value: stats.internalMembers, icon: Users, color: 'text-blue-600' },
    { label: 'Consultores Externos', value: stats.externalConsultants, icon: UserCheck, color: 'text-emerald-600' },
    { label: 'Projetos Ativos', value: stats.activeProjects, icon: Briefcase, color: 'text-violet-600' },
    { label: 'Rating Medio', value: `${stats.averageRating}/5`, icon: Star, color: 'text-amber-600' },
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <Card key={c.label}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className={`p-2.5 rounded-lg bg-muted ${c.color}`}>
              <c.icon className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{c.value}</p>
              <p className="text-xs text-muted-foreground">{c.label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================
// TAB 1: PIPELINE TABLE
// ============================================================
function PipelineTable() {
  const { pipeline } = useTeamsStore();
  const max = Math.max(...pipeline.map((p) => p.members));
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
          Pipeline por Fase
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-3">
          {pipeline.map((p) => (
            <div key={p.phase} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{p.phase}</span>
                <span className="text-muted-foreground">{p.members} membro{p.members !== 1 ? 's' : ''}</span>
              </div>
              <Progress value={(p.members / max) * 100} className="h-2" />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================
// TAB 1: INTERNAL TEAM
// ============================================================
function InternalTeamTab({ onAdd }: { onAdd: () => void }) {
  const store = useTeamsStore();
  const filtered = store.getFilteredInternalMembers();
  const phases = store.getAllPhases();

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar membros..." value={store.searchQuery} onChange={(e) => store.setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={store.selectedPhase || ''} onChange={(e) => store.setSelectedPhase(e.target.value || null)}>
            <option value="">Todas as Fases</option>
            {phases.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          {store.selectedPhase && (
            <Button variant="ghost" size="sm" onClick={() => store.setSelectedPhase(null)}><X className="h-3 w-3" /></Button>
          )}
          <Button size="sm" onClick={onAdd}><Plus className="h-4 w-4 mr-1" />Novo</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map((m) => <InternalMemberCard key={m.id} member={m} />)}
      </div>
      {filtered.length === 0 && <div className="text-center py-12 text-muted-foreground">Nenhum membro encontrado com os filtros aplicados.</div>}
    </div>
  );
}

function InternalMemberCard({ member }: { member: InternalTeamMember }) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-start gap-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-primary/10 text-primary text-sm font-semibold">{getInitials(member.name)}</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="font-semibold truncate">{member.name}</p>
            <p className="text-sm text-muted-foreground">{member.role}</p>
          </div>
          <AvailabilityBadge status={member.availability} />
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1"><Briefcase className="h-3.5 w-3.5" />{member.projectsCount} projetos</span>
          <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" />{new Date(member.joinedAt).getFullYear()}</span>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1.5">Fase: <span className="font-medium text-foreground">{member.phase}</span></p>
          <div className="flex flex-wrap gap-1">
            {member.skills.slice(0, 4).map((s) => <Badge key={s} variant="secondary" className="text-xs font-normal">{s}</Badge>)}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================================
// TAB 2: CONSULTANTS DATABASE
// ============================================================
function ConsultantsTab({ onAdd }: { onAdd: () => void }) {
  const store = useTeamsStore();
  const filtered = store.getFilteredConsultants();
  const sectors = store.getAllSectors();

  const seniorityCounts = useMemo(() => {
    const counts: Record<string, number> = { senior: 0, mid: 0, junior: 0 };
    store.consultants.forEach((c) => { counts[c.seniority] = (counts[c.seniority] || 0) + 1; });
    return counts;
  }, [store.consultants]);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold text-blue-600">{seniorityCounts.senior}</p><p className="text-xs text-muted-foreground">Senior</p></CardContent></Card>
        <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold text-emerald-600">{seniorityCounts.mid}</p><p className="text-xs text-muted-foreground">Mid-Level</p></CardContent></Card>
        <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold text-amber-600">{seniorityCounts.junior}</p><p className="text-xs text-muted-foreground">Junior</p></CardContent></Card>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar consultores, skills, setores..." value={store.searchQuery} onChange={(e) => store.setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <div className="flex gap-2 flex-wrap">
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={store.selectedSeniority || ''} onChange={(e) => store.setSelectedSeniority(e.target.value || null)}>
            <option value="">Todas Senioridades</option>
            <option value="senior">Senior</option>
            <option value="mid">Mid-Level</option>
            <option value="junior">Junior</option>
          </select>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={store.selectedSector || ''} onChange={(e) => store.setSelectedSector(e.target.value || null)}>
            <option value="">Todos Setores</option>
            {sectors.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={store.selectedAvailability || ''} onChange={(e) => store.setSelectedAvailability(e.target.value || null)}>
            <option value="">Todas Disponibilidades</option>
            <option value="available">Disponivel</option>
            <option value="busy">Ocupado</option>
          </select>
          {(store.selectedSeniority || store.selectedSector || store.selectedAvailability) && (
            <Button variant="ghost" size="sm" onClick={() => store.clearFilters()}><Filter className="h-3 w-3 mr-1" />Limpar</Button>
          )}
          <Button size="sm" onClick={onAdd}><Plus className="h-4 w-4 mr-1" />Novo</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filtered.map((c) => <ConsultantCard key={c.id} consultant={c} />)}
      </div>
      {filtered.length === 0 && <div className="text-center py-12 text-muted-foreground">Nenhum consultor encontrado com os filtros aplicados.</div>}
    </div>
  );
}

function ConsultantCard({ consultant }: { consultant: Consultant }) {
  const [expanded, setExpanded] = useState(false);
  const seniorityColors: Record<string, string> = {
    senior: 'bg-blue-100 text-blue-700 border-blue-200',
    mid: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    junior: 'bg-amber-100 text-amber-700 border-amber-200',
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Avatar className="h-12 w-12">
            <AvatarFallback className="bg-primary/10 text-primary font-bold">{getInitials(consultant.name)}</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-semibold">{consultant.name}</p>
              <span className={`text-xs px-2 py-0.5 rounded-full border ${seniorityColors[consultant.seniority]}`}>{consultant.seniorityLabel}</span>
              <AvailabilityBadge status={consultant.availability} />
            </div>
            <p className="text-sm text-muted-foreground flex items-center gap-1 mt-0.5"><MapPin className="h-3 w-3" />{consultant.location}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-1 text-amber-600"><Star className="h-4 w-4 fill-current" /><span className="font-semibold text-sm">{consultant.rating}</span></div>
            <p className="text-xs text-muted-foreground">{consultant.dailyRate} {consultant.currency}/dia</p>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1">
          {consultant.sectors.map((s) => <Badge key={s} variant="outline" className="text-xs font-normal">{s}</Badge>)}
        </div>

        {expanded && (
          <div className="mt-3 pt-3 border-t space-y-2 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <span className="flex items-center gap-1.5 text-muted-foreground"><GraduationCap className="h-3.5 w-3.5" />{consultant.education}</span>
              <span className="flex items-center gap-1.5 text-muted-foreground"><Calendar className="h-3.5 w-3.5" />{consultant.yearsExperience} anos exp.</span>
              <span className="flex items-center gap-1.5 text-muted-foreground"><CheckCircle2 className="h-3.5 w-3.5" />{consultant.projectsCompleted} projetos</span>
              <span className="flex items-center gap-1.5 text-muted-foreground"><DollarSign className="h-3.5 w-3.5" />{consultant.dailyRate} {consultant.currency}/dia</span>
            </div>
            <div><p className="text-xs text-muted-foreground mb-1">Skills</p><div className="flex flex-wrap gap-1">{consultant.skills.map((s) => <Badge key={s} variant="secondary" className="text-xs font-normal">{s}</Badge>)}</div></div>
            <div><p className="text-xs text-muted-foreground mb-1">Linguas</p><div className="flex flex-wrap gap-1">{consultant.languages.map((l) => <Badge key={l} variant="outline" className="text-xs font-normal"><Globe className="h-3 w-3 mr-1" />{l}</Badge>)}</div></div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground"><Clock className="h-3.5 w-3.5" />Ultimo projeto: <span className="font-medium text-foreground">{consultant.lastProject.name}</span> ({consultant.lastProject.date})</div>
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
// TAB 3: PROJECT TEAMS
// ============================================================
function ProjectTeamsTab({ onAdd, onCreateTeam }: { onAdd: (project: ProjectTeam) => void; onCreateTeam: () => void }) {
  const store = useTeamsStore();
  const filtered = store.getFilteredProjectTeams();

  const statusConfig: Record<string, { label: string; color: string; icon: typeof CheckCircle2 }> = {
    in_proposal: { label: 'Em Proposta', color: 'bg-blue-100 text-blue-700 border-blue-200', icon: Clock },
    won: { label: 'Ganho', color: 'bg-emerald-100 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
    lost: { label: 'Perdido', color: 'bg-red-100 text-red-700 border-red-200', icon: X },
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Pesquisar projetos..." value={store.searchQuery} onChange={(e) => store.setSearchQuery(e.target.value)} className="pl-9" />
        </div>
        <Button size="sm" onClick={onCreateTeam}><Plus className="h-4 w-4 mr-1" />Nova Equipa</Button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filtered.map((project) => {
          const cfg = statusConfig[project.status] || statusConfig.in_proposal;
          const StatusIcon = cfg.icon;
          return (
            <Card key={project.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-lg">{project.name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full border flex items-center gap-1 ${cfg.color}`}><StatusIcon className="h-3 w-3" />{cfg.label}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">Cliente: {project.client}</p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><TrendingUp className="h-3.5 w-3.5" />Fase: <span className="font-medium text-foreground">{project.phase}</span></span>
                    {project.startDate && <span className="flex items-center gap-1 mt-0.5"><Calendar className="h-3.5 w-3.5" />Inicio: {project.startDate}</span>}
                  </div>
                </div>

                {project.manager && (
                  <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-lg">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm"><span className="text-muted-foreground">Gestor de Projeto:</span> <span className="font-medium">{project.manager}</span></span>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Membros Internos ({project.internalMembers.length})</p>
                      <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => onAdd(project)}><Plus className="h-3 w-3 mr-1" />Adicionar</Button>
                    </div>
                    <div className="space-y-2">
                      {project.internalMembers.map((m) => (
                        <div key={m.id} className="flex items-center gap-2">
                          <Avatar className="h-7 w-7"><AvatarFallback className="bg-primary/10 text-primary text-xs">{getInitials(m.name)}</AvatarFallback></Avatar>
                          <div className="text-sm"><span className="font-medium">{m.name}</span><span className="text-muted-foreground"> — {m.role}</span></div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Consultores Externos ({project.externalMembers.length})</p>
                      <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => onAdd(project)}><Plus className="h-3 w-3 mr-1" />Adicionar</Button>
                    </div>
                    {project.externalMembers.length > 0 ? (
                      <div className="space-y-2">
                        {project.externalMembers.map((m) => (
                          <div key={m.id} className="flex items-center gap-2">
                            <Avatar className="h-7 w-7"><AvatarFallback className="bg-emerald-100 text-emerald-700 text-xs">{getInitials(m.name)}</AvatarFallback></Avatar>
                            <div className="text-sm"><span className="font-medium">{m.name}</span><span className="text-muted-foreground"> — {m.role}</span></div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">Ainda nenhum consultor externo atribuido. {project.status === 'in_proposal' && 'Atribuicao pos-ganho.'}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      {filtered.length === 0 && <div className="text-center py-12 text-muted-foreground">Nenhum projeto encontrado.</div>}
    </div>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================
export function TeamsPage() {
  const { fetchAll, isLoading, error, clearError } = useTeamsStore();
  const [showInternalModal, setShowInternalModal] = useState(false);
  const [showConsultantModal, setShowConsultantModal] = useState(false);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showCreateTeamModal, setShowCreateTeamModal] = useState(false);
  const [activeProject, setActiveProject] = useState<ProjectTeam | null>(null);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleAddInternal = () => { fetchAll(); };
  const handleAddConsultant = () => { fetchAll(); };
  const handleAddProjectMember = () => { fetchAll(); setActiveProject(null); };
  const handleCreateTeam = () => { fetchAll(); };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Card key={i} className="animate-pulse"><CardContent className="p-4 h-20 bg-muted" /></Card>)}
        </div>
        <div className="h-64 bg-muted rounded-lg animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Equipas</h1>
        <p className="text-muted-foreground text-sm">Gestao de equipas internas, consultores externos e equipas de projeto.</p>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 flex items-center gap-3">
          <p className="text-sm text-destructive">{error}</p>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={clearError}><X className="h-4 w-4" /></Button>
        </div>
      )}

      <StatsCards />

      <Tabs defaultValue="internal" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="internal" className="flex items-center gap-1.5"><Users className="h-4 w-4" /><span className="hidden sm:inline">Equipa Interna</span><span className="sm:hidden">Interna</span></TabsTrigger>
          <TabsTrigger value="consultants" className="flex items-center gap-1.5"><UserCheck className="h-4 w-4" /><span className="hidden sm:inline">Base de Consultores</span><span className="sm:hidden">Consultores</span></TabsTrigger>
          <TabsTrigger value="projects" className="flex items-center gap-1.5"><Briefcase className="h-4 w-4" /><span className="hidden sm:inline">Equipas de Projeto</span><span className="sm:hidden">Projetos</span></TabsTrigger>
        </TabsList>

        <TabsContent value="internal" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2"><InternalTeamTab onAdd={() => setShowInternalModal(true)} /></div>
            <div><PipelineTable /></div>
          </div>
        </TabsContent>

        <TabsContent value="consultants" className="space-y-4">
          <ConsultantsTab onAdd={() => setShowConsultantModal(true)} />
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <ProjectTeamsTab
            onAdd={(project) => { setActiveProject(project); setShowProjectModal(true); }}
            onCreateTeam={() => setShowCreateTeamModal(true)}
          />
        </TabsContent>
      </Tabs>

      <AddInternalMemberModal open={showInternalModal} onClose={() => setShowInternalModal(false)} onAdd={handleAddInternal} />
      <AddConsultantModal open={showConsultantModal} onClose={() => setShowConsultantModal(false)} onAdd={handleAddConsultant} />
      <AddProjectTeamMemberModal open={showProjectModal} onClose={() => setShowProjectModal(false)} onAdd={handleAddProjectMember} teamId={activeProject?.id ?? null} projectName={activeProject?.name} />
      <CreateProjectTeamModal open={showCreateTeamModal} onClose={() => setShowCreateTeamModal(false)} onAdd={handleCreateTeam} />
    </div>
  );
}
