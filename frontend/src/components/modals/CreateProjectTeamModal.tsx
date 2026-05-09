import { useState } from 'react';
import { Briefcase } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiCreateTeam } from '@/lib/api';

interface Props {
  open: boolean;
  onClose: () => void;
  onAdd: () => void;
}

export function CreateProjectTeamModal({ open, onClose, onAdd }: Props) {
  const [name, setName] = useState('');
  const [client, setClient] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => { setName(''); setClient(''); setError(null); };

  const handleSubmit = async () => {
    if (!name.trim() || !client.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      await apiCreateTeam({ name: name.trim(), description: client.trim() });
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
          <DialogTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            Nova Equipa de Projeto
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label>Nome do Projeto / Proposta</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Ex: Proposta UNDP Mocambique 2025" />
          </div>
          <div>
            <Label>Cliente / Doador</Label>
            <Input value={client} onChange={(e) => setClient(e.target.value)} placeholder="Ex: UNDP, FAO, Banco Mundial" />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || !client.trim() || isLoading}>
            {isLoading ? 'A criar...' : 'Criar Equipa'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
