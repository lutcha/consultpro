import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus } from 'lucide-react';
import { useTeamsStore } from '@/stores';

export function AddTeamMemberModal({ teamId: _teamId }: { teamId: string }) {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('consultant');
  const { isLoading } = useTeamsStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Placeholder: in production this would call an API to add member
    setOpen(false);
    setEmail('');
    setRole('consultant');
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline">
          <Plus className="h-4 w-4 mr-1" />
          Adicionar Membro
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Adicionar Membro à Equipa</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Email do Utilizador</Label>
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <Label>Função</Label>
            <select
              className="w-full h-10 rounded-md border border-input bg-background px-3"
              value={role}
              onChange={e => setRole(e.target.value)}
            >
              <option value="team_lead">Team Lead</option>
              <option value="technical_lead">Technical Lead</option>
              <option value="consultant">Consultor</option>
              <option value="specialist">Especialista</option>
              <option value="support">Suporte</option>
            </select>
          </div>
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'A adicionar...' : 'Adicionar Membro'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
