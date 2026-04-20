// ============================================
// TEAMS PAGE
// ============================================

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Users,
  Trash2,
  Edit,
  ArrowLeft,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiGetTeams, apiCreateTeam, apiUpdateTeam, apiDeleteTeam } from '@/lib/api';
import { apiGetUsers } from '@/lib/api';
import type { ApiTeam, ApiUser } from '@/lib/api';

export function Teams() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState<ApiTeam[]>([]);
  const [users, setUsers] = useState<ApiUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingTeam, setEditingTeam] = useState<ApiTeam | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    member_ids: [] as number[],
  });

  const loadTeams = async () => {
    try {
      const [teamsRes, usersRes] = await Promise.all([
        apiGetTeams(),
        apiGetUsers(),
      ]);
      setTeams(teamsRes.results);
      setUsers(usersRes.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar equipas');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTeams();
  }, []);

  const handleCreate = async () => {
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
    if (!editingTeam) return;
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
        <div className="h-64 bg-muted rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Equipas</h1>
            <p className="text-muted-foreground">
              Gerencie as equipas de consultores.
            </p>
          </div>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Nova Equipa
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {teams.map((team) => (
          <Card key={team.id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  {team.name}
                </CardTitle>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => openEdit(team)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(team.id)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">{team.description}</p>
              <div className="flex flex-wrap gap-2">
                {team.members.map((member) => (
                  <Badge key={member.id} variant="secondary">
                    {member.first_name} {member.last_name}
                  </Badge>
                ))}
                {team.members.length === 0 && (
                  <span className="text-sm text-muted-foreground">
                    Sem membros
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {teams.length === 0 && !isLoading && (
        <Card>
          <CardContent className="p-8 text-center">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium">Nenhuma equipa encontrada</h3>
            <p className="text-muted-foreground mt-1">
              Crie a sua primeira equipa de consultores.
            </p>
            <Button className="mt-4" onClick={openCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Nova Equipa
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingTeam ? 'Editar Equipa' : 'Nova Equipa'}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Nome *</Label>
              <Input
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Nome da equipa"
              />
            </div>
            <div className="space-y-2">
              <Label>Descrição</Label>
              <Textarea
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder="Descrição da equipa"
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Membros</Label>
              <div className="border rounded-lg p-3 space-y-2 max-h-48 overflow-y-auto">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-2 rounded hover:bg-muted cursor-pointer"
                    onClick={() => toggleMember(user.id)}
                  >
                    <span className="text-sm">
                      {user.name || `${user.first_name} ${user.last_name}`}
                    </span>
                    {formData.member_ids.includes(user.id) ? (
                      <Badge variant="default" className="text-xs">
                        Selecionado
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs">
                        Adicionar
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              <X className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
            <Button
              onClick={editingTeam ? handleUpdate : handleCreate}
            >
              {editingTeam ? 'Guardar' : 'Criar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
