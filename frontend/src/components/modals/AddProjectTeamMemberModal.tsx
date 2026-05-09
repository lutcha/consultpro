import { useState } from 'react';
import { UserPlus, Search } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { apiAddTeamMember } from '@/lib/api';
import { useTeamsStore } from '@/stores';

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: () => void;
  teamId: string | null;
  projectName?: string;
}

function getInitials(name: string) {
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

export function AddProjectTeamMemberModal({ open, onClose, onAdd, teamId, projectName }: Props) {
  const { internalMembers, consultants } = useTeamsStore();
  const [search, setSearch] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const allUsers = [
    ...internalMembers.map((m) => ({ id: m.id, name: m.name, email: m.email, type: 'internal' as const })),
    ...consultants.map((c) => ({ id: c.id, name: c.name, email: c.email, type: 'external' as const })),
  ];

  const filtered = search.trim()
    ? allUsers.filter((u) => u.name.toLowerCase().includes(search.toLowerCase()) || u.email.toLowerCase().includes(search.toLowerCase()))
    : allUsers;

  const reset = () => { setSearch(''); setSelectedId(null); setError(null); };

  const handleAdd = async () => {
    if (!teamId || !selectedId) return;
    setIsLoading(true);
    setError(null);
    try {
      await apiAddTeamMember(Number(teamId), Number(selectedId));
      reset();
      onAdd();
      onClose();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose(); } }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 flex-wrap">
            <UserPlus className="h-5 w-5" />
            Adicionar Membro ao Projeto
            {projectName && <span className="text-sm font-normal text-muted-foreground">— {projectName}</span>}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input className="pl-9" placeholder="Pesquisar utilizadores..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <div className="max-h-64 overflow-y-auto space-y-1 border rounded-md p-2">
            {filtered.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">Nenhum utilizador encontrado.</p>
            )}
            {filtered.map((u) => (
              <button
                key={u.id}
                onClick={() => setSelectedId(u.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-left transition-colors ${
                  selectedId === u.id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                }`}
              >
                <Avatar className="h-8 w-8 flex-shrink-0">
                  <AvatarFallback className={`text-xs font-semibold ${
                    selectedId === u.id ? 'bg-primary-foreground/20 text-primary-foreground' : 'bg-primary/10 text-primary'
                  }`}>
                    {getInitials(u.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{u.name}</p>
                  <p className={`text-xs truncate ${selectedId === u.id ? 'text-primary-foreground/70' : 'text-muted-foreground'}`}>
                    {u.email}
                  </p>
                </div>
                <Badge variant="outline" className={`text-xs flex-shrink-0 ${selectedId === u.id ? 'border-primary-foreground/30 text-primary-foreground' : ''}`}>
                  {u.type === 'internal' ? 'Interno' : 'Consultor'}
                </Badge>
              </button>
            ))}
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleAdd} disabled={!selectedId || isLoading}>
            {isLoading ? 'A adicionar...' : 'Adicionar Membro'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
