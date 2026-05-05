// ============================================
// TEAMS PAGE - Enhanced with stats, avatars, responsive
// ============================================

import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Users,
  Trash2,
  Edit,
  ArrowLeft,
  X,
  Search,
  UserCheck,
  Briefcase,
  Crown,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { apiGetTeams, apiCreateTeam, apiUpdateTeam, apiDeleteTeam, apiGetUsers } from '@/lib/api';
import type { ApiTeam, ApiUser } from '@/lib/api';

const availabilityConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  available: { label: 'Disponível', color: 'bg-green-500', icon: CheckCircle2 },
  busy: { label: 'Ocupado', color: 'bg-amber-500', icon: Clock },
  unavailable: { label: 'Indisponível', color: 'bg-red-500', icon: AlertCircle },
};

export function Teams() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<ApiTeam[]>([]);
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showDialog, setShowDialog] = useState(false);
  const [editingTeam, setEditingTeam] = useState<ApiTeam | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', member_ids: [] as number[] });
  const [detailTeam, setDetailTeam] = useState<ApiTeam | null>(null);

  const loadTeams = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [teamsRes, usersRes] = await Promise.all([apiGetTeams(), apiGetUsers()]);
      setTeams(teamsRes.results || []);
      setUsers(usersRes.results || []);
    } catch (err) {
      console.error('Teams load error:', err);
      setError(err instanceof Error ? err.message : 'Erro ao carregar equipas');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTeams();
  }, []);

  const filteredTeams = useMemo(() => {
    if (!search.trim()) return teams;
    const q = search.toLowerCase();
    return teams.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.members.some((m) => m.name?.toLowerCase().includes(q) || m.email.toLowerCase().includes(q))
    );
  }, [teams, search]);

  const stats = useMemo(() => {
    const totalMembers = new Set(teams.flatMap((t) => t.members.map((m) => m.id))).size;
    const availableCount = users.filter((u) => u.availability === 'available').length;
    const avgSize = teams.length > 0 ? Math.round(teams.reduce((sum, t) => sum + t.members.length, 0) / teams.length) : 0;
    return { total: teams.length, totalMembers, availableCount, avgSize };
  }, [teams, users]);

  const handleCreate = async () => {
    if (!formData.name.trim()) return;
    try {
      await apiCreateTeam(formData);
      setShowDialog(false);
      setFormData({ name: '', description: '', member_ids: [] });
      loadTeams();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar equipa');
    }
  };

  const handleUpdate = async () => {
    if (!editingTeam || !formData.name.trim()) return;
    try {
      await apiUpdateTeam(editingTeam.id, formData);
      setShowDialog(false);
      setEditingTeam(null);
      setFormData({ name: '', description: '', member_ids: [] });
      loadTeams();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar equipa');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja eliminar esta equipa?')) return;
    try {
      await apiDeleteTeam(id);
      loadTeams();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao eliminar equipa');
    }
  };

  const openCreate = () => {
    setEditingTeam(null);
    setFormData({ name: '', description: '', member_ids: [] });
    setShowDialog(true);
  };

  const openEdit = (team: ApiTeam) => {
    setEditingTeam(team);
    setFormData({
      name: team.name,
      description: team.description,
      member_ids: team.members.map((m) => m.id),
    });
    setShowDialog(true);
  };

  const toggleMember = (userId: number) => {
    setFormData((prev) => ({
      ...prev,
      member_ids: prev.member_ids.includes(userId)
        ? prev.member_ids.filter((id) => id !== userId)
        : [...prev.member_ids, userId],
    }));
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-muted rounded animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-muted rounded animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Equipas</h1>
            <p className="text-muted-foreground text-sm">Gerencie as equipas de consultores.</p>
          </div>
        </div>
        <Button onClick={openCreate} className="shrink-0">
          <Plus className="h-4 w-4 mr-2" />
          Nova Equipa
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total}</p>
                <p className="text-xs text-muted-foreground">Equipas</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Briefcase className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.totalMembers}</p>
                <p className="text-xs text-muted-foreground">Consultores</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <UserCheck className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.availableCount}</p>
                <p className="text-xs text-muted-foreground">Disponíveis</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <Crown className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.avgSize}</p>
                <p className="text-xs text-muted-foreground">Média/Equipa</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{error}</p>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={() => setError(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Pesquisar equipas, membros..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Teams Grid */}
      {filteredTeams.length === 0 ? (
        <Card>
          <CardContent className="p-8 md:p-12 text-center">
            <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium">
              {search.trim() ? 'Nenhuma equipa encontrada' : 'Nenhuma equipa criada'}
            </h3>
            <p className="text-muted-foreground mt-1 text-sm max-w-md mx-auto">
              {search.trim()
                ? 'Tente ajustar os critérios de pesquisa.'
                : 'Crie a sua primeira equipa de consultores para começar a organizar os seus projetos.'}
            </p>
            {!search.trim() && (
              <Button className="mt-4" onClick={openCreate}>
                <Plus className="h-4 w-4 mr-2" />
                Nova Equipa
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredTeams.map((team) => (
            <Card
              key={team.id}
              className="group hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setDetailTeam(team)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Users className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="font-semibold truncate">{team.name}</h3>
                      <p className="text-xs text-muted-foreground truncate">
                        {team.members.length} membros
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation();
                        openEdit(team);
                      }}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(team.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-2">{team.description}</p>

                {/* Members avatars */}
                <div className="flex items-center justify-between">
                  <div className="flex -space-x-2">
                    {team.members.slice(0, 5).map((member) => (
                      <div
                        key={member.id}
                        className="h-8 w-8 rounded-full border-2 border-background flex items-center justify-center text-xs font-bold text-white"
                        style={{
                          backgroundColor: `hsl(${(member.id * 137) % 360}, 60%, 45%)`,
                        }}
                        title={member.name || member.email}
                      >
                        {(member.name || member.email || '?').charAt(0).toUpperCase()}
                      </div>
                    ))}
                    {team.members.length > 5 && (
                      <div className="h-8 w-8 rounded-full border-2 border-background bg-muted flex items-center justify-center text-xs font-medium">
                        +{team.members.length - 5}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-1">
                    {team.members.filter((m) => m.availability === 'available').length > 0 && (
                      <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        {team.members.filter((m) => m.availability === 'available').length}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Capacity bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Capacidade</span>
                    <span className="font-medium">
                      {team.members.filter((m) => m.availability === 'available').length}/{team.members.length} disponíveis
                    </span>
                  </div>
                  <Progress
                    value={
                      team.members.length > 0
                        ? (team.members.filter((m) => m.availability === 'available').length /
                            team.members.length) *
                          100
                        : 0
                    }
                    className="h-1.5"
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{editingTeam ? 'Editar Equipa' : 'Nova Equipa'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="Nome da equipa"
              />
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Descrição da equipa"
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Membros ({formData.member_ids.length} selecionados)</Label>
              <div className="border rounded-lg p-2 space-y-1 max-h-56 overflow-y-auto">
                {users.map((user) => {
                  const selected = formData.member_ids.includes(user.id);
                  const avail = availabilityConfig[user.availability] || availabilityConfig.unavailable;
                  const AvailIcon = avail.icon;
                  return (
                    <div
                      key={user.id}
                      className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                        selected ? 'bg-primary/5 border border-primary/20' : 'hover:bg-muted border border-transparent'
                      }`}
                      onClick={() => toggleMember(user.id)}
                    >
                      <div
                        className="h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0"
                        style={{ backgroundColor: `hsl(${(user.id * 137) % 360}, 60%, 45%)` }}
                      >
                        {(user.name || user.email || '?').charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{user.name || user.email}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <AvailIcon className={`h-3.5 w-3.5 ${avail.color.replace('bg-', 'text-')}`} />
                        {selected ? (
                          <Badge variant="default" className="text-xs">Selecionado</Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">Adicionar</Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              <X className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
            <Button onClick={editingTeam ? handleUpdate : handleCreate} disabled={!formData.name.trim()}>
              {editingTeam ? 'Guardar Alterações' : 'Criar Equipa'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={!!detailTeam} onOpenChange={() => setDetailTeam(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-auto">
          {detailTeam && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p>{detailTeam.name}</p>
                    <p className="text-sm text-muted-foreground font-normal">
                      {detailTeam.members.length} membros
                    </p>
                  </div>
                </DialogTitle>
              </DialogHeader>

              <Tabs defaultValue="members">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="members">Membros</TabsTrigger>
                  <TabsTrigger value="info">Informação</TabsTrigger>
                </TabsList>

                <TabsContent value="members" className="space-y-3 mt-4">
                  {detailTeam.members.map((member) => {
                    const avail = availabilityConfig[member.availability] || availabilityConfig.unavailable;
                    const AvailIcon = avail.icon;
                    return (
                      <div
                        key={member.id}
                        className="flex items-center gap-4 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                      >
                        <div
                          className="h-10 w-10 rounded-full flex items-center justify-center text-sm font-bold text-white shrink-0"
                          style={{ backgroundColor: `hsl(${(member.id * 137) % 360}, 60%, 45%)` }}
                        >
                          {(member.name || member.email || '?').charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium">{member.name || member.email}</p>
                          <p className="text-sm text-muted-foreground">{member.email}</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {member.skills?.slice(0, 3).map((skill) => (
                              <Badge key={skill} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <Badge variant="outline" className="shrink-0 flex items-center gap-1">
                          <AvailIcon className={`h-3 w-3 ${avail.color.replace('bg-', 'text-')}`} />
                          {avail.label}
                        </Badge>
                      </div>
                    );
                  })}
                </TabsContent>

                <TabsContent value="info" className="space-y-4 mt-4">
                  <div>
                    <h4 className="font-medium mb-1">Descrição</h4>
                    <p className="text-sm text-muted-foreground">{detailTeam.description || 'Sem descrição.'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold">{detailTeam.members.length}</p>
                      <p className="text-xs text-muted-foreground">Total Membros</p>
                    </div>
                    <div className="p-3 bg-muted rounded-lg text-center">
                      <p className="text-2xl font-bold text-green-600">
                        {detailTeam.members.filter((m) => m.availability === 'available').length}
                      </p>
                      <p className="text-xs text-muted-foreground">Disponíveis</p>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button variant="outline" onClick={() => setDetailTeam(null)}>Fechar</Button>
                <Button
                  onClick={() => {
                    setDetailTeam(null);
                    openEdit(detailTeam);
                  }}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Editar Equipa
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
